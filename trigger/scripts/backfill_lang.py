#!/usr/bin/env python3
"""
backfill_lang.py — preenche o campo `lang` da tabela tasks a partir do nome da etapa.

Na estrutura antiga o idioma vivia embutido no nome da task (`narrate-audio` = ES,
`narrate-audio-en` = EN). Isso não escala pra 7 idiomas. Este script extrai o idioma
para a coluna `lang`, deixando o nome da etapa agnóstico.

Mapa (derivado de reconcile_factory.py → ETAPAS_CONFIG):
  published_en    → publish-books-en    → en
  narration_en    → narrate-audio-en    → en
  transcript_en   → transcribe-audio    → en
  translation_es  → translate-content   → es
  narration_es    → narrate-audio       → es

Uso:  python3 backfill_lang.py [--dry-run]
Só usa API REST do Teable (nunca SQL) — regra da constituição.
"""
import os
import sys
import json
import argparse
import urllib.request

TABLE = "tblVzN1Eo8tfk7GX2CJ"          # tasks
HERE = os.path.dirname(os.path.abspath(__file__))

LANG_POR_ETAPA = {
    "publish-books-en": "en",
    "narrate-audio-en": "en",
    "transcribe-audio": "en",
    "translate-content": "es",
    "narrate-audio": "es",
}


def load_env():
    env = dict(os.environ)
    for p in (os.path.join(HERE, "..", "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def api(env, method, path, body=None):
    url = env["TEABLE_URL"].rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + env["TEABLE_TOKEN"],
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    env = load_env()

    # pagina todos os registros
    recs, skip = [], 0
    while True:
        r = api(env, "GET", f"/api/table/{TABLE}/record?take=1000&skip={skip}")
        page = r.get("records", [])
        recs += page
        if len(page) < 1000:
            break
        skip += 1000
    print(f"📋 {len(recs)} tasks no total")

    pend = []
    for rec in recs:
        f = rec.get("fields", {})
        if f.get("lang"):
            continue
        lang = LANG_POR_ETAPA.get(f.get("task"))
        if lang:
            pend.append((rec["id"], lang))

    from collections import Counter
    print(f"🔤 a preencher: {len(pend)} | distribuição: {dict(Counter(l for _, l in pend))}")
    if args.dry_run:
        print("(dry-run, nada gravado)")
        return

    ok = 0
    for rid, lang in pend:
        try:
            api(env, "PATCH", f"/api/table/{TABLE}/record/{rid}",
                {"record": {"fields": {"lang": lang}}, "fieldKeyType": "name"})
            ok += 1
            if ok % 50 == 0:
                print(f"   ... {ok}/{len(pend)}")
        except Exception as e:
            print(f"   ❌ {rid}: {str(e)[:90]}")
    print(f"✅ preenchidos: {ok}/{len(pend)}")


if __name__ == "__main__":
    main()
