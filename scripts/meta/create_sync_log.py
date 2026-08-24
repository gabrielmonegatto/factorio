"""Cria `sync_log`: o registro de cada execucao de sincronizacao.

Existe pela mesma razao do db-watch: no apagao de 09-12/08/2026 a falha foi
silenciosa por tres dias. Um cron que quebra sem deixar rastro repete isso.
Aqui cada rodada grava uma linha, entao "faz dois dias que nao sincroniza"
vira uma consulta, nao uma descoberta tardia.

  python create_sync_log.py
"""
from __future__ import annotations

from _common import D1, log

DDL = """
CREATE TABLE IF NOT EXISTS sync_log (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  rodou_em  TEXT NOT NULL DEFAULT (datetime('now')),
  fonte     TEXT NOT NULL,     -- 'meta' | 'flow' | ...
  modo      TEXT,              -- 'diario' | 'horario' | 'backfill'
  linhas    INTEGER DEFAULT 0,
  segundos  INTEGER,
  status    TEXT,              -- 'ok' | 'erro'
  detalhe   TEXT               -- JSON: linhas por conta, ou a mensagem de erro
)
"""
IDX = ("CREATE INDEX IF NOT EXISTS idx_sync_log_fonte "
       "ON sync_log(fonte, rodou_em DESC)")


def main() -> None:
    db = D1()
    db.query(DDL)
    db.query(IDX)
    n = db.query("SELECT COUNT(*) n FROM sync_log")[0]["n"]
    log(f"sync_log pronta ({n} linhas)")


if __name__ == "__main__":
    main()
