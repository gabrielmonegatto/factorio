"""Migracao: coluna `currency` em meta_insights e reforco do meta_insights_hourly.

Duas contas faturam em dolar (CA1 e CA2). Sem moeda na linha, qualquer SUM(spend)
que cruze contas mistura BRL com USD. A conversao fica na leitura, nao na carga.

Idempotente: pode rodar de novo sem quebrar.

  python migrate_currency.py
"""
from __future__ import annotations

from _common import CURRENCY, D1, lit, log

ALTERS = [
    "ALTER TABLE meta_insights ADD COLUMN currency TEXT",
    "ALTER TABLE meta_insights_hourly ADD COLUMN currency TEXT",
    "ALTER TABLE meta_insights_hourly ADD COLUMN purchases INTEGER DEFAULT 0",
    "ALTER TABLE meta_insights_hourly ADD COLUMN revenue REAL DEFAULT 0",
]
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_meta_insights_acct_date "
    "ON meta_insights(account_id, date)",
    "CREATE INDEX IF NOT EXISTS idx_meta_hourly_date "
    "ON meta_insights_hourly(date, hora)",
]


def main() -> None:
    db = D1()

    for sql in ALTERS:
        try:
            db.query(sql)
            log(f"ok: {sql}")
        except Exception as e:
            # "duplicate column name" = ja aplicada numa execucao anterior
            if "duplicate column" in str(e).lower():
                log(f"ja existia: {sql}")
            else:
                raise

    for sql in INDEXES:
        db.query(sql)
        log(f"ok: {sql[:60]}...")

    # preenche a moeda das linhas que ja estavam gravadas
    for acct, cur in CURRENCY.items():
        db.query(
            f"UPDATE meta_insights SET currency = {lit(cur)} "
            f"WHERE account_id = {lit(acct)} AND (currency IS NULL OR currency = '')"
        )

    faltando = db.query(
        "SELECT COUNT(*) n FROM meta_insights WHERE currency IS NULL OR currency = ''"
    )[0]["n"]
    log(f"linhas sem moeda apos o backfill: {faltando}")
    for r in db.query(
        "SELECT currency, COUNT(*) n, ROUND(SUM(spend),2) spend "
        "FROM meta_insights GROUP BY 1 ORDER BY 3 DESC"
    ):
        log(f"  {r['currency']}: {r['n']} linhas, spend {r['spend']}")


if __name__ == "__main__":
    main()
