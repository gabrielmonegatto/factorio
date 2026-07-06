#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import json

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TASKS_TABLE = f'"{SCHEMA}"."tblVzN1Eo8tfk7GX2CJ"'

def get_pending():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Busca apenas tarefas ativas e pendentes utilizando as colunas estruturadas
    cur.execute(f"""
        SELECT __id, "brand", "area", "project_slug", "task"
        FROM {TASKS_TABLE} 
        WHERE "Status" = 'Pendente'
        ORDER BY __created_time ASC
        LIMIT 50
    """)
    rows = cur.fetchall()
    
    tasks = []
    for r in rows:
        tasks.append({
            "id": r['__id'],
            "project": r['project_slug'] or "unknown",
            "area": r['area'] or "unknown",
            "task": r['task'] or "unknown"
        })
        
    print(json.dumps(tasks))
    conn.close()

if __name__ == "__main__":
    get_pending()
