"""Aplica arquivos .sql no D1 remoto em lote (bem mais rapido que wrangler
arquivo a arquivo, que abre uma conexao por chamada).

  python apply_sql.py "<pasta>/mig_*.sql"
  python apply_sql.py a.sql b.sql --chunk 200
"""
from __future__ import annotations

import argparse
import glob
import pathlib

from _common import D1, log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="+", help="arquivos ou globs")
    ap.add_argument("--chunk", type=int, default=150)
    args = ap.parse_args()

    files: list[pathlib.Path] = []
    for pat in args.patterns:
        hits = sorted(glob.glob(pat))
        if not hits:
            log(f"aviso: nada casou com {pat}")
        files.extend(pathlib.Path(h) for h in hits)
    if not files:
        raise SystemExit("nenhum arquivo para aplicar")

    db = D1()
    total = 0
    for f in files:
        stmts = []
        for raw in f.read_text(encoding="utf-8").split(";\n"):
            body = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("--")).strip()
            if body:
                stmts.append(body)
        log(f"{f.name}: {len(stmts)} statements")
        db.exec_batch(stmts, chunk=args.chunk, label=f"{f.name} ")
        total += len(stmts)
    log(f"pronto: {total} statements aplicados")


if __name__ == "__main__":
    main()
