"""Confere o que esta no D1 contra o que a API do Meta diz, conta por conta.

Roda depois de qualquer backfill. Divergencia acima de 1% aponta buraco de
carga; abaixo disso costuma ser reatribuicao em andamento (o Meta mexe nos
numeros por ate ~72h).

  python verify_coverage.py --since 2026-01-01
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

from _common import ACCOUNTS, CURRENCY, D1, Graph, lit, log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-01-01")
    ap.add_argument("--until", default=str(dt.date.today()))
    args = ap.parse_args()

    db, g = D1(), Graph()
    janela = json.dumps({"since": args.since, "until": args.until})
    log(f"janela {args.since} -> {args.until}")
    print(f"\n{'conta':26} {'moeda':5} {'API':>13} {'D1':>13} {'diff':>8}")

    pior = 0.0
    for acct_id, acct_name, _brand in ACCOUNTS:
        rows = list(g.paginate(f"{acct_id}/insights", level="account",
                               time_range=janela, fields="spend"))
        api = sum(float(r.get("spend") or 0) for r in rows)
        got = db.query(
            "SELECT COALESCE(SUM(spend),0) s FROM meta_insights "
            f"WHERE account_id = {lit(acct_id)} "
            f"AND date BETWEEN {lit(args.since)} AND {lit(args.until)}"
        )[0]["s"]
        diff = (got - api) / api * 100 if api else 0.0
        pior = max(pior, abs(diff))
        print(f"{acct_name:26} {CURRENCY.get(acct_id, '?'):5} {api:>13,.0f} "
              f"{got:>13,.0f} {diff:>7.1f}%")

    print()
    log(f"maior divergencia: {pior:.1f}%")
    if pior > 1:
        log("ATENCAO: acima de 1% — provavel buraco de carga, rodar o backfill de novo")


if __name__ == "__main__":
    main()
