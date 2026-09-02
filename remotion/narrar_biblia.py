#!/usr/bin/env python3
"""
narrar_biblia.py — narra os blocos da Bíblia que o preparar_corpus deixou no R2.

## Por que um narrador próprio

O `narrar_sermao.py` puxa a fila da MINERAÇÃO (D1): capítulo de obra vira
sermão. A Bíblia não passa pela mineração: o `biblia_preparar_corpus.py` já
fatiou a KJV em 140 blocos de ~1h e deixou cada um como pasta no R2
(`NNNN_-_slug/text.txt` + `meta.json`), no MESMO contrato de pastas que o
build_job espera. O que falta é só a ponte texto → áudio + transcrição, e ela
REUSA as peças do narrar_sermao (Kokoro, faster-whisper, vaga de CPU, contrato
do transcript). Nada de pipeline novo: é o mesmo motor com outra entrada.

## O que produz (mesmo contrato do narrar_sermao)

    <prefix>/NNNN_-_slug/sermon_NNNN.mp3
    <prefix>/NNNN_-_slug/transcript.json   (words[] em ms, endireitadas)

## Custo e ritmo

Bloco de ~1h a RTF ~0.5 numa vaga de 5 CPUs ≈ 2h de máquina por bloco.
Os 140 blocos ≈ 12 dias de UMA vaga; o cron de 4h com orçamento divide a
máquina com os pregadores sem briga (o vaga_cpu arbitra).

Uso:
  python3 narrar_biblia.py --canal biblia_kjv --status
  python3 narrar_biblia.py --canal biblia_kjv --limite 2 --minutos 200
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import canais
import vaga_cpu
import narrar_sermao as N


def pastas_do_canal(s3, prefixo):
    """Mapa NNNN -> (nome_da_pasta, arquivos)."""
    tok, ks = None, []
    while True:
        kw = {"Bucket": "mananciall", "Prefix": prefixo + "/", "MaxKeys": 1000}
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        ks += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            break
        tok = r.get("NextContinuationToken")
    pastas = {}
    for k in ks:
        m = re.match(rf"{re.escape(prefixo)}/(\d{{4}})(_-_[^/]+)/(.+)$", k)
        if m:
            pastas.setdefault(m.group(1), [m.group(1) + m.group(2), set()])[1].add(m.group(3))
    return pastas


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--limite", type=int, default=1)
    ap.add_argument("--minutos", type=int, default=0)
    ap.add_argument("--so", help="só este bloco (NNNN)")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    c = canais.get(a.canal)
    N.CANAL_ATUAL = c["slug"]
    env = N.load_env()
    s3 = N.s3c(env)
    pastas = pastas_do_canal(s3, c["prefix"])

    fila = [n for n, (_, fs) in sorted(pastas.items())
            if "text.txt" in fs and not any(f.startswith("sermon_") for f in fs)]
    print(f"📖 {c['nome']}: {len(pastas)} blocos · {len(pastas) - len(fila)} narrados · "
          f"{len(fila)} na fila")
    if a.status:
        return
    if a.so:
        fila = [a.so.zfill(4)]

    # Fôlego local (mesma lógica do narrar_sermao, com o estoque contado do R2):
    # cada esteira se auto-regula, sem orquestrador. Canal sem estreia = fome.
    narrados = len(pastas) - len(fila)
    try:
        est = json.loads(s3.get_object(Bucket="mananciall",
                                       Key=c["state_key"])["Body"].read())
        publicados = len(est.get("scheduled", {}))
    except Exception:
        publicados = 0
    folego = max(0.0, (narrados - publicados) / float(c.get("videos_por_dia") or 1.0))
    a.limite, a.minutos, regime = N.regime_do_folego(folego, a.limite, a.minutos)
    print(f"🌡️  fôlego: {folego:.0f} dias → {regime}")

    t0 = time.monotonic()
    feitos = 0
    for nnnn in fila[: a.limite]:
        gasto = (time.monotonic() - t0) / 60
        media = gasto / feitos if feitos else 0
        if a.minutos and (gasto >= a.minutos or (media and gasto + media > a.minutos)):
            print(f"⏳ orçamento de {a.minutos} min: parando ({gasto:.0f} gastos)")
            break

        pasta, _fs = pastas[nnnn]
        corpo = s3.get_object(Bucket="mananciall",
                              Key=f"{c['prefix']}/{pasta}/text.txt")["Body"].read()
        texto = corpo.decode("utf-8")
        print(f"\n  📖 {pasta} · {len(texto)//1000}k chars (~{len(texto.split())//140}min)")

        work = os.path.join(N.WORK, c["slug"], nnnn)
        os.makedirs(work, exist_ok=True)
        wav = os.path.join(work, "s.wav")
        mp3 = os.path.join(work, f"sermon_{nnnn}.mp3")
        try:
            with vaga_cpu.vaga(f"narrar {c['slug']} {nnnn}", espera_max_s=1800):
                N.narrar(c, texto, wav)
                N.para_mp3(wav, mp3)
                tr = N.transcrever(mp3, env, c)
        except TimeoutError as e:
            print(f"⏸️  {e}; encerrando o run")
            break

        s3.upload_file(mp3, "mananciall", f"{c['prefix']}/{pasta}/sermon_{nnnn}.mp3")
        s3.put_object(Bucket="mananciall", Key=f"{c['prefix']}/{pasta}/transcript.json",
                      Body=json.dumps(tr).encode(), ContentType="application/json")
        for p in (wav, mp3):
            if os.path.exists(p):
                os.remove(p)
        feitos += 1
        print(f"  ✅ {pasta} no R2")

    print(f"\n🏁 narrados neste run: {feitos}")


if __name__ == "__main__":
    main()
