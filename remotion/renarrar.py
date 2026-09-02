#!/usr/bin/env python3
"""
renarrar.py — manda de volta pra fila o que foi narrado com texto ruim.

## Por que existe

O Gabriel OUVIU o Moody (01/09): "D. L. Moody" robótico, passagens bíblicas
lidas torto. Causa: o texto ia pro Kokoro sem a camada de normalização
(construída agora em `normalizar_narracao`). O Spurgeon escapou porque o CCEL
entrega tipografia limpa; o Moody vem do Gutenberg, que entrega a página de
1880 como impressa. Ordem dele: "refazer o que estiver ruim nos já narrados".

## O que faz (e o que NUNCA toca)

Para cada sermão `narrado` do canal que NÃO está agendado/publicado:
  1. apaga do R2 o `sermon_*.mp3` e o `transcript.json` (artefatos derivados,
     regeneráveis; copy e hook ficam, o texto deles não mudou);
  2. apaga o render `NNNN.mp4` (derivado do áudio apagado: ficaria órfão);
  3. volta o status no D1 pra `fila`.

Vídeo AGENDADO OU PUBLICADO é intocável: trocar áudio de vídeo no ar não
existe, e mexer no que o público já viu é reescrever história.

Depois disto o resto é o sistema normal: o fôlego do canal despenca, a esteira
entra em FOME sozinha e re-narra com a normalização nova; o produtor vê o mp4
sumido e re-renderiza. A refação não tem orquestração própria DE PROPÓSITO.

Uso:
  python3 renarrar.py --canal moody            # prévia
  python3 renarrar.py --canal moody --aplicar
"""
import argparse
import json
import re
import sys

sys.path.insert(0, ".")
import canais
import narrar_sermao as N


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()

    c = canais.get(a.canal)
    env = N.load_env()
    s3 = N.s3c(env)

    try:
        est = json.loads(s3.get_object(Bucket=c["bucket"],
                                       Key=c["state_key"])["Body"].read())
        protegidos = set(est.get("scheduled", {}).keys())
    except Exception:
        protegidos = set()

    narrados = N.d1(env, "SELECT numero FROM sermons WHERE canal=? AND status='narrado' "
                         "ORDER BY numero", [c["slug"]])
    alvos = [f"{r['numero']:04d}" for r in narrados
             if f"{r['numero']:04d}" not in protegidos]
    print(f"🔁 {c['nome']}: {len(narrados)} narrados · {len(protegidos)} protegidos "
          f"(agendados/publicados) · {len(alvos)} voltam pra fila")
    if not a.aplicar:
        print("   (prévia — rode com --aplicar)")
        return

    # mapa pasta por número (o slug da pasta pode diferir do slug atual no D1)
    tok, ks = None, []
    while True:
        kw = {"Bucket": c["bucket"], "Prefix": c["prefix"] + "/", "MaxKeys": 1000}
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        ks += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            break
        tok = r.get("NextContinuationToken")

    apagar = []
    for k in ks:
        m = re.match(rf"{re.escape(c['prefix'])}/(\d{{4}})_-_[^/]+/(sermon_\d+\.(?:mp3|wav)|transcript\.json)$", k)
        if m and m.group(1) in alvos:
            apagar.append(k)
    for nnnn in alvos:
        apagar.append(f"{c['renders_prefix']}/{nnnn}.mp4")

    apagados = 0
    for k in apagar:
        try:
            s3.delete_object(Bucket=c["bucket"], Key=k)
            apagados += 1
        except Exception:
            pass
    for nnnn in alvos:
        N.d1(env, "UPDATE sermons SET status='fila', updated_at=datetime('now') "
                  "WHERE canal=? AND numero=?", [c["slug"], int(nnnn)])

    print(f"🏁 {len(alvos)} sermões de volta à fila · {apagados} artefatos derivados "
          f"removidos. A esteira re-narra sozinha (fôlego caiu, vira FOME).")


if __name__ == "__main__":
    main()
