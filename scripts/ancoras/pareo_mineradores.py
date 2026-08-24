#!/usr/bin/env python3
"""
pareo_mineradores.py — compara modelos de LLM no trabalho de minerar clipes.

## Por que medir e não escolher pelo preço

A tarefa é ler um sermão inteiro e apontar QUAIS frases viram um short de 30 a
60s que se sustenta sozinho. Modelo barato que devolve índice fora da faixa, ou
que corta no meio do argumento, custa mais caro do que economiza: o erro só
aparece no vídeo pronto.

## O que dá pra conferir sozinho (e entra na nota)

  json_ok       devolveu JSON válido no formato pedido
  indices_ok    índices existem, a<=b, e os clipes não se sobrepõem
  duracao_ok    o trecho escolhido já cai em 28-62s SEM o conserto automático
  hook_fiel     as palavras do hook aparecem MESMO no trecho escolhido
                (é a checagem anti-invenção: hook bonito que mente é pior
                 que hook sem graça)
  aproveitados  quantos dos clipes pedidos sobreviveram a tudo isso

## O que NÃO dá pra medir e por isso vai pro Gabriel

Se o trecho é BOM. A régua pega o mecânico; escolher entre dois candidatos que
passam em tudo é ouvido, não número. Por isso o script imprime o texto escolhido.

Uso:
  python scripts/ancoras/pareo_mineradores.py --sermoes 1 2 3
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "remotion"))
import mine_clips as mc  # noqa: E402

MODELOS = [
    "inclusionai/ling-3.0-flash",
    "qwen/qwen3.7-flash",
    "openai/gpt-oss-120b",
    "deepseek/deepseek-v4-flash",
    "openai/gpt-5-nano",
    "google/gemini-2.5-flash",      # o atual, é a linha de base
]


def chamar(modelo, key, system, titulo, frases, tentativas=2):
    linhas = [f'[{s["i"]}] ({s["start"]/1000:.1f}s) {s["text"]}' for s in frases]
    corpo = json.dumps({
        "model": modelo,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": f"Sermon: {titulo}\n\n" + "\n".join(linhas)}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }).encode()
    for t in range(tentativas):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions", data=corpo, method="POST",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                         "User-Agent": "factorio-pareo/1.0"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read())
            txt = d["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.S)
            return json.loads(m.group(0) if m else txt), time.time() - t0, None
        except Exception as e:
            erro = str(e)[:160]
            if t + 1 < tentativas:
                time.sleep(4)
    return None, 0, erro


def avaliar(saida, frases):
    """Devolve (metricas, clipes_validos). Só conta o que dá pra conferir."""
    n = len(frases)
    clips = (saida or {}).get("clips") or []
    ok_idx = ok_dur = ok_hook = 0
    validos, ocupado = [], []
    for c in clips:
        try:
            a, b = int(c["start_sentence"]), int(c["end_sentence"])
        except Exception:
            continue
        if not (0 <= a <= b < n):
            continue
        if any(a <= fim and ini <= b for ini, fim in ocupado):   # sobreposição
            continue
        ocupado.append((a, b))
        ok_idx += 1
        dur = (frases[b]["end"] - frases[a]["start"]) / 1000.0
        if mc.MIN_S <= dur <= mc.MAX_S:
            ok_dur += 1
        texto = " ".join(f["text"] for f in frases[a:b + 1]).lower()
        hook = (c.get("hook_text") or "").lower()
        palavras = [p for p in re.findall(r"[a-z']{4,}", hook)]
        fiel = bool(palavras) and sum(p in texto for p in palavras) >= max(1, len(palavras) // 2)
        ok_hook += fiel
        validos.append({"a": a, "b": b, "dur": dur, "hook": c.get("hook_text", ""),
                        "fiel": fiel, "texto": texto})
    return {"pedidos": len(clips), "indices_ok": ok_idx, "duracao_ok": ok_dur,
            "hook_fiel": ok_hook}, validos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sermoes", nargs="+", default=["1", "2", "3"])
    ap.add_argument("--modelos", nargs="+", default=MODELOS)
    ap.add_argument("--amostras", action="store_true", help="imprime o texto escolhido")
    args = ap.parse_args()

    import canais
    C = canais.get("spurgeon")
    mc.CHANNEL_PREFIX = C["prefix"]
    env = mc.load_env()
    key = env["OPENROUTER_API_KEY"]
    s3 = mc.s3c(env)
    # mesma armadilha do mine_clips: o molde é JSON, .format() estoura nas chaves
    system = mc.SYSTEM_MOLDE
    for campo, valor in (("canal", C["nome"]), ("pregador", C["pregador"])):
        system = system.replace("{" + campo + "}", valor)

    provas = []
    for s in args.sermoes:
        nnnn = f"{int(s):04d}"
        pasta = mc.find_folder(s3, nnnn)
        tr = json.loads(s3.get_object(Bucket=mc.BUCKET, Key=f"{pasta}/transcript.json")["Body"].read())
        frases = mc.build_sentences(tr["words"])
        provas.append((nnnn, tr.get("title", nnnn), frases))
        print(f"📖 {nnnn} · {len(frases)} frases")

    print(f"\n🥊 {len(args.modelos)} modelos × {len(provas)} sermões\n")
    placar = {}
    for modelo in args.modelos:
        tot = {"pedidos": 0, "indices_ok": 0, "duracao_ok": 0, "hook_fiel": 0}
        segs, falhas, amostra = 0.0, 0, None
        for nnnn, titulo, frases in provas:
            saida, dt, erro = chamar(modelo, key, system, titulo, frases)
            segs += dt
            if saida is None:
                falhas += 1
                continue
            m, validos = avaliar(saida, frases)
            for k in tot:
                tot[k] += m[k]
            if amostra is None and validos:
                amostra = validos[0]
        placar[modelo] = (tot, segs, falhas, amostra)
        marca = "❌" if falhas == len(provas) else "  "
        print(f"{marca} {modelo:44} pedidos {tot['pedidos']:2} · "
              f"índice ok {tot['indices_ok']:2} · duração ok {tot['duracao_ok']:2} · "
              f"hook fiel {tot['hook_fiel']:2} · {segs:5.0f}s"
              + (f" · {falhas} falha(s)" if falhas else ""))

    if args.amostras:
        print("\n" + "=" * 78 + "\nO PRIMEIRO CLIPE QUE CADA UM ESCOLHEU\n" + "=" * 78)
        for modelo, (_, _, _, am) in placar.items():
            if not am:
                print(f"\n{modelo}\n  (nada válido)")
                continue
            print(f"\n{modelo}\n  hook: \"{am['hook']}\""
                  f"{'' if am['fiel'] else '   ⚠️ hook não aparece no trecho'}"
                  f"  ({am['dur']:.0f}s)")
            print(f"  \"{am['texto'][:300]}...\"")


if __name__ == "__main__":
    main()
