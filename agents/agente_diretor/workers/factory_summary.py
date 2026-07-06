#!/usr/bin/env python3
"""
factory_summary.py — Resumo do estado atual da fábrica EternalL.
Usado pelo agente diretor para pulsar o estado e identificar gargalos.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://teable:teable_secret_password@localhost:42345/teable")

SCHEMA = "bseWeczeNfCSaMlu2EC"
TBL_TASKS = f'"{SCHEMA}"."tblVzN1Eo8tfk7GX2CJ"'

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Totais por status
    cur.execute(f"""
        SELECT "Status", COUNT(*) as total
        FROM {TBL_TASKS}
        GROUP BY "Status"
        ORDER BY "Status";
    """)
    by_status = {r['Status']: r['total'] for r in cur.fetchall()}

    # 2. Totais por área
    cur.execute(f"""
        SELECT area, "Status", COUNT(*) as total
        FROM {TBL_TASKS}
        GROUP BY area, "Status"
        ORDER BY area, "Status";
    """)
    by_area = {}
    for r in cur.fetchall():
        a = r['area'] or 'unknown'
        s = r['Status']
        if a not in by_area:
            by_area[a] = {}
        by_area[a][s] = r['total']

    # 3. Top projetos com mais pendências
    cur.execute(f"""
        SELECT project_slug, area, COUNT(*) as pendentes
        FROM {TBL_TASKS}
        WHERE "Status" = 'Pendente'
        GROUP BY project_slug, area
        ORDER BY pendentes DESC
        LIMIT 10;
    """)
    top_pendentes = [dict(r) for r in cur.fetchall()]

    # 4. Projetos Em Processamento (podem estar travados)
    cur.execute(f"""
        SELECT project_slug, area, task, "progresso",
               __last_modified_time
        FROM {TBL_TASKS}
        WHERE "Status" = 'Em Processamento'
        ORDER BY __last_modified_time ASC
        LIMIT 20;
    """)
    em_processamento = [dict(r) for r in cur.fetchall()]

    # 5. Totais por task type
    cur.execute(f"""
        SELECT task, COUNT(*) as total,
               SUM(CASE WHEN "Status" = 'Concluído' THEN 1 ELSE 0 END) as concluidos,
               SUM(CASE WHEN "Status" = 'Pendente' THEN 1 ELSE 0 END) as pendentes
        FROM {TBL_TASKS}
        GROUP BY task
        ORDER BY task;
    """)
    by_task = [dict(r) for r in cur.fetchall()]

    result = {
        "summary": {
            "total_tasks": sum(by_status.values()),
            "by_status": by_status,
            "by_area": by_area,
        },
        "top_pending_projects": top_pendentes,
        "in_progress": em_processamento,
        "by_task_type": by_task,
    }

    print(json.dumps(result, indent=2, default=str))
    conn.close()

if __name__ == "__main__":
    main()
