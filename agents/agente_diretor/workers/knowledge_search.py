#!/usr/bin/env python3
"""
knowledge_search.py — Busca na tabela knowledge do Postgres.
Uso: python knowledge_search.py --query "..." [--category pattern]

Exemplos:
  python knowledge_search.py --query "pipeline de traducao"
  python knowledge_search.py --query "elevenlabs" --category api
  python knowledge_search.py --query "gargalo" --category lesson
"""
import argparse
import json
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://teable:teable_secret_password@localhost:42345/teable")

SCHEMA = "bseWeczeNfCSaMlu2EC"
TBL_KNOWLEDGE = f'"{SCHEMA}"."tblFactoryKnowledge"'

def search_knowledge(query: str, category: str = None, limit: int = 10):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if category:
        cur.execute(f"""
            SELECT __id, title, category, tags, content, source, confidence, __created_time
            FROM {TBL_KNOWLEDGE}
            WHERE (
                title ILIKE %s OR content ILIKE %s OR tags ILIKE %s
            ) AND category = %s
            ORDER BY confidence DESC, __created_time DESC
            LIMIT %s;
        """, (f'%{query}%', f'%{query}%', f'%{query}%', category, limit))
    else:
        cur.execute(f"""
            SELECT __id, title, category, tags, content, source, confidence, __created_time
            FROM {TBL_KNOWLEDGE}
            WHERE title ILIKE %s OR content ILIKE %s OR tags ILIKE %s
            ORDER BY confidence DESC, __created_time DESC
            LIMIT %s;
        """, (f'%{query}%', f'%{query}%', f'%{query}%', limit))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    print(json.dumps({
        "query": query,
        "category_filter": category,
        "count": len(rows),
        "results": rows
    }, indent=2, default=str))

def main():
    parser = argparse.ArgumentParser(description="Busca na base de knowledge")
    parser.add_argument("--query", required=True, help="Texto para buscar")
    parser.add_argument("--category", default=None, help="Filtrar por categoria: pattern|lesson|procedure|context|api")
    parser.add_argument("--limit", type=int, default=10, help="Limite de resultados (default: 10)")
    args = parser.parse_args()
    search_knowledge(args.query, args.category, args.limit)

if __name__ == "__main__":
    main()
