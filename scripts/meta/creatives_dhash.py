"""Calcula o dHash dos nossos PNGs e grava em creatives.dhash.

Fonte das imagens: a pasta de staging local (rapido) ou, com --from-r2, o
proprio bucket via rclone. Roda uma vez; reexecucao so processa o que falta.

  python creatives_dhash.py --src "<caminho>/upload"
  python creatives_dhash.py --all      # recalcula tudo, inclusive ja preenchidos
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from PIL import Image

from _common import D1, dhash, lit, log

# Staging default (sessao de download original do Drive).
DEFAULT_SRC = pathlib.Path(
    r"C:\Users\MONEGA~1\AppData\Local\Temp\claude"
    r"\C--Users-Monegatto-Desktop-EternalL"
    r"\19f9fca5-fe81-4845-952f-054352f943b7\scratchpad\upload"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="pasta com a arvore bluue/ads/*.png")
    ap.add_argument("--all", action="store_true", help="recalcula mesmo quem ja tem dhash")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.exists():
        sys.exit(f"pasta de origem nao existe: {src}")

    db = D1()
    cond = "r2_key IS NOT NULL" + ("" if args.all else " AND dhash IS NULL")
    rows = db.query(f"SELECT id, r2_key FROM creatives WHERE {cond}")
    log(f"{len(rows)} criativos a processar")

    updates: list[str] = []
    faltando = 0
    for i, r in enumerate(rows, 1):
        p = src / r["r2_key"]
        if not p.exists():
            faltando += 1
            continue
        try:
            with Image.open(p) as im:
                im.load()
                h = dhash(im)
        except Exception as e:
            log(f"  erro em {r['r2_key']}: {e}")
            continue
        updates.append(f"UPDATE creatives SET dhash={lit(h)} WHERE id={lit(r['id'])}")
        if i % 250 == 0:
            log(f"  hasheados {i}/{len(rows)}")

    log(f"{len(updates)} hashes calculados; {faltando} arquivos ausentes no disco")
    if updates:
        db.exec_batch(updates, chunk=120, label="gravando ")

    n = db.query("SELECT COUNT(*) n FROM creatives WHERE dhash IS NOT NULL")[0]["n"]
    dup = db.query(
        "SELECT COUNT(*) n FROM (SELECT dhash FROM creatives WHERE dhash IS NOT NULL "
        "GROUP BY dhash HAVING COUNT(*) > 1)"
    )[0]["n"]
    log(f"pronto: {n} criativos com dhash ({dup} hashes repetidos = artes identicas)")


if __name__ == "__main__":
    main()
