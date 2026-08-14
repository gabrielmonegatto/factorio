"""Puxa quebras de hora e regiao dos insights do Meta -> D1.

Grao = conta (nao ad): padrao de hora/regiao nao precisa do grao de criativo
e assim o volume fica pequeno. Upsert idempotente.

  python meta_pull_breakdowns.py --dim hourly --since 2026-01-01
  python meta_pull_breakdowns.py --dim region --since 2026-01-01

GOTCHAS que este script trata:
- Contas tem timezone diferente (LF1 = Sao_Paulo; CA1/CA2/Tonaface = Los
  Angeles). A hora e gravada como o Meta reporta (timezone da conta) +
  colunas tz/currency para normalizar na analise.
- A "hora" do Meta e a hora do CLIQUE/impressao atribuida, nao da compra.
- Janela longa com time_increment=1 estoura a API -> fatiar (--chunk-days).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time

from _common import ACCOUNTS, D1, Graph, lit, log
from meta_pull_insights import (CUSTOM_PURCHASE, PURCHASE_KEYS, _sum)

FIELDS = "spend,impressions,clicks,actions,action_values,conversions,conversion_values,date_start"

DDL = {
    "hourly": """CREATE TABLE IF NOT EXISTS meta_breakdown_hourly (
        account_id TEXT NOT NULL, date TEXT NOT NULL, hour INTEGER NOT NULL,
        tz TEXT, currency TEXT,
        spend REAL DEFAULT 0, impressions INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
        purchases INTEGER DEFAULT 0, revenue REAL DEFAULT 0, updated_at TEXT,
        PRIMARY KEY (account_id, date, hour))""",
    "region": """CREATE TABLE IF NOT EXISTS meta_breakdown_region (
        account_id TEXT NOT NULL, date TEXT NOT NULL, region TEXT NOT NULL,
        tz TEXT, currency TEXT,
        spend REAL DEFAULT 0, impressions INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
        purchases INTEGER DEFAULT 0, revenue REAL DEFAULT 0, updated_at TEXT,
        PRIMARY KEY (account_id, date, region))""",
}
BREAKDOWN = {
    "hourly": "hourly_stats_aggregated_by_advertiser_time_zone",
    "region": "region",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", choices=("hourly", "region"), required=True)
    ap.add_argument("--since", default="2026-01-01")
    ap.add_argument("--until")
    ap.add_argument("--chunk-days", type=int, default=10)
    ap.add_argument("--account")
    args = ap.parse_args()

    since = dt.date.fromisoformat(args.since)
    until = dt.date.fromisoformat(args.until) if args.until else dt.date.today()
    table = f"meta_breakdown_{args.dim}"
    bkey = BREAKDOWN[args.dim]

    db = D1()
    db.query(DDL[args.dim])
    g = Graph()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    accounts = [a for a in ACCOUNTS if not args.account or a[0] == args.account]
    blocks = []
    cur = since
    while cur <= until:
        end = min(cur + dt.timedelta(days=args.chunk_days - 1), until)
        blocks.append((cur, end))
        cur = end + dt.timedelta(days=1)

    grand = 0
    for acct_id, acct_name, _brand in accounts:
        meta = g.get(acct_id, fields="timezone_name,currency")
        tz, curr = meta.get("timezone_name"), meta.get("currency")
        log(f"=== {acct_name} ({acct_id}) tz={tz} {curr} — {len(blocks)} blocos")
        acct_rows = 0
        for bi, (b0, b1) in enumerate(blocks, 1):
            try:
                rows = list(g.paginate(
                    f"{acct_id}/insights", level="account", time_increment=1,
                    time_range=json.dumps({"since": str(b0), "until": str(b1)}),
                    breakdowns=bkey, fields=FIELDS, limit=500))
            except Exception as e:
                log(f"  bloco {b0}..{b1} falhou ({str(e)[:80]}); segue")
                continue
            stmts = []
            for row in rows:
                if args.dim == "hourly":
                    # formato "13:00:00 - 13:59:59" -> 13
                    key_val = int((row.get(bkey) or "0")[:2])
                else:
                    key_val = row.get(bkey) or "(unknown)"
                cols = {
                    "account_id": acct_id,
                    "date": row.get("date_start"),
                    ("hour" if args.dim == "hourly" else "region"): key_val,
                    "tz": tz, "currency": curr,
                    "spend": float(row.get("spend") or 0),
                    "impressions": int(row.get("impressions") or 0),
                    "clicks": int(row.get("clicks") or 0),
                    "purchases": int(max(_sum(row.get("actions"), PURCHASE_KEYS),
                                         _sum(row.get("conversions"), CUSTOM_PURCHASE))),
                    "revenue": max(_sum(row.get("action_values"), PURCHASE_KEYS),
                                   _sum(row.get("conversion_values"), CUSTOM_PURCHASE)),
                    "updated_at": now,
                }
                if not cols["date"]:
                    continue
                keys = ",".join(f'"{k}"' for k in cols)
                vals = ",".join(lit(v) for v in cols.values())
                pk = "account_id,date," + ("hour" if args.dim == "hourly" else "region")
                sets = ",".join(f'"{k}"=excluded."{k}"' for k in cols
                                if k not in ("account_id", "date", "hour", "region"))
                stmts.append(f"INSERT INTO {table} ({keys}) VALUES ({vals}) "
                             f"ON CONFLICT({pk}) DO UPDATE SET {sets}")
            if stmts:
                db.exec_batch(stmts, chunk=200)
            acct_rows += len(stmts)
            if bi % 5 == 0 or bi == len(blocks):
                log(f"  bloco {bi}/{len(blocks)}: acumulado {acct_rows}")
        grand += acct_rows
    tot = db.query(f"SELECT COUNT(*) n, ROUND(SUM(spend),2) s FROM {table}")[0]
    log(f"pronto: {grand} linhas gravadas | tabela {table}: {tot['n']} linhas, spend {tot['s']}")


if __name__ == "__main__":
    main()
