#!/usr/bin/env python3
"""
knowledge_save.py — Salva uma entrada na tabela knowledge do Postgres.
Uso: python knowledge_save.py --title "..." --category pattern --content "..." [--tags "tag1,tag2"] [--source diretor] [--confidence 90]

Categorias válidas: pattern | lesson | procedure | context | api | observation
"""
import argparse
import json
import os
import sys
import uuid
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://teable:teable_secret_password@localhost:42345/teable")

SCHEMA = "bseWeczeNfCSaMlu2EC"
TBL_KNOWLEDGE = f'"{SCHEMA}"."tblFactoryKnowledge"'

VALID_CATEGORIES = {"pattern", "lesson", "procedure", "context", "api", "observation"}

def save_knowledge(title: str, category: str, content: str, tags: str = "", source: str = "diretor", confidence: int = 80):
    if category not in VALID_CATEGORIES:
        print(json.dumps({"error": f"Categoria inválida '{category}'. Use: {', '.join(VALID_CATEGORIES)}"}))
        sys.exit(1)

    entry_id = f"knw_{category[:3]}_{uuid.uuid4().hex[:12]}"

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {TBL_KNOWLEDGE} (
            __id, __created_by, __version,
            title, category, tags, content, source, confidence
        ) VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s);
    """, (entry_id, "usrCe4LHiMshx2Cw3C0", title, category, tags, content, source, confidence))
    conn.commit()
    conn.close()

    print(json.dumps({
        "status": "saved",
        "id": entry_id,
        "title": title,
        "category": category,
        "source": source,
        "confidence": confidence
    }))

def main():
    parser = argparse.ArgumentParser(description="Salva conhecimento na base")
    parser.add_argument("--title", required=True, help="Título da entrada")
    parser.add_argument("--category", required=True, help="Categoria: pattern|lesson|procedure|context|api|observation")
    parser.add_argument("--content", required=True, help="Conteúdo em markdown/texto")
    parser.add_argument("--tags", default="", help="Tags separadas por vírgula")
    parser.add_argument("--source", default="diretor", help="Agente que está salvando (default: diretor)")
    parser.add_argument("--confidence", type=int, default=80, help="Confiança 0-100 (default: 80)")
    args = parser.parse_args()
    save_knowledge(args.title, args.category, args.content, args.tags, args.source, args.confidence)

if __name__ == "__main__":
    main()
