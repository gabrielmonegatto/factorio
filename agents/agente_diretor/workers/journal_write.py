#!/usr/bin/env python3
"""
journal_write.py — Registra uma entrada no agent_journal no Postgres.
Uso: python journal_write.py --agent diretor --type decision --summary "..." [--context '{"key":"val"}']

Tipos válidos: decision | milestone | alert | suggestion | error | observation
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://teable:teable_secret_password@localhost:42345/teable")

SCHEMA = "bseWeczeNfCSaMlu2EC"
TBL_JOURNAL = f'"{SCHEMA}"."tblAgentJournal001"'
USER_MAP = {
    "diretor":   "usrCe4LHiMshx2Cw3C0",
    "minerador": "usrCe4LHiMshx2Cw3C0",
    "builder":   "usrCe4LHiMshx2Cw3C0",
    "analisador":"usrCe4LHiMshx2Cw3C0",
}

VALID_TYPES = {"decision", "milestone", "alert", "suggestion", "error", "observation"}

def write_journal(agent: str, entry_type: str, summary: str, context: dict = None):
    if entry_type not in VALID_TYPES:
        print(json.dumps({"error": f"Tipo inválido '{entry_type}'. Use: {', '.join(VALID_TYPES)}"}))
        sys.exit(1)

    entry_id = f"jnl_{agent[:3]}_{uuid.uuid4().hex[:12]}"
    user_id = USER_MAP.get(agent, "usrCe4LHiMshx2Cw3C0")
    context_str = json.dumps(context) if context else None

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {TBL_JOURNAL} (
            __id, __created_by, __version,
            agent, type, summary, context
        ) VALUES (%s, %s, 1, %s, %s, %s, %s);
    """, (entry_id, user_id, agent, entry_type, summary, context_str))
    conn.commit()
    conn.close()

    print(json.dumps({
        "status": "saved",
        "id": entry_id,
        "agent": agent,
        "type": entry_type,
        "summary": summary[:100] + "..." if len(summary) > 100 else summary
    }))

def main():
    parser = argparse.ArgumentParser(description="Escreve no agent_journal")
    parser.add_argument("--agent", required=True, help="Nome do agente (diretor, minerador, etc.)")
    parser.add_argument("--type", dest="entry_type", required=True, help="Tipo: decision|milestone|alert|suggestion|error|observation")
    parser.add_argument("--summary", required=True, help="Resumo da entrada (texto)")
    parser.add_argument("--context", default=None, help="JSON com contexto adicional (opcional)")
    args = parser.parse_args()

    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Context JSON inválido: {e}"}))
            sys.exit(1)

    write_journal(args.agent, args.entry_type, args.summary, context)

if __name__ == "__main__":
    main()
