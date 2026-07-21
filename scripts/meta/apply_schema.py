"""Aplica schema.sql no D1 remoto + adiciona creatives.dhash se faltar.

Idempotente: pode rodar quantas vezes quiser.
"""
import pathlib
import re

from _common import D1, log

HERE = pathlib.Path(__file__).resolve().parent


def main() -> None:
    db = D1()
    sql = (HERE / "schema.sql").read_text(encoding="utf-8")
    stmts = []
    for raw in re.split(r";\s*\n", sql):
        # tira as linhas de comentario, senao um bloco comentado no topo
        # engole o CREATE TABLE que vem logo abaixo dele
        body = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("--")).strip()
        if body:
            stmts.append(body)
    for st in stmts:
        head = " ".join(st.split())[:70]
        db.query(st)
        log("ok: " + head)

    # Colunas adicionadas depois da criacao das tabelas. SQLite nao tem
    # ADD COLUMN IF NOT EXISTS, entao conferimos no PRAGMA.
    extras = [
        ("creatives", "dhash", "TEXT"),
        ("meta_insights", "atc", "INTEGER DEFAULT 0"),
        ("meta_insights", "checkouts", "INTEGER DEFAULT 0"),
    ]
    for table, col, decl in extras:
        have = {c["name"] for c in db.query(f"PRAGMA table_info({table})")}
        if col in have:
            log(f"{table}.{col} ja existe")
            continue
        db.query(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        log(f"ok: {table}.{col} criada")
    db.query("CREATE INDEX IF NOT EXISTS idx_creatives_dhash ON creatives(dhash)")

    tables = {t["name"] for t in db.query("SELECT name FROM sqlite_master WHERE type='table'")}
    log("tabelas meta_*: " + ", ".join(sorted(t for t in tables if t.startswith("meta_"))))


if __name__ == "__main__":
    main()
