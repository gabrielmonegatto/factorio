import os
import sys
import argparse
import json
import psycopg2
from psycopg2.extras import RealDictCursor

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TASKS_TABLE = f'"{SCHEMA}"."tblVzN1Eo8tfk7GX2CJ"'
USER_ID = "usrCe4LHiMshx2Cw3C0"

def main():
    parser = argparse.ArgumentParser(description="Cria a próxima task da esteira no Postgres local")
    parser.add_argument("--parent-id", required=True, help="ID da task pai/anterior")
    parser.add_argument("--next-task", required=True, help="Nome do próximo passo (ex: 'transcribe-audio')")
    parser.add_argument("--area", required=True, help="Área da próxima task (ex: 'channels')")
    parser.add_argument("--instruction", required=True, help="Insumo/Caminho físico gerado para o próximo passo")
    args = parser.parse_args()
    
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Busca os metadados da task pai (para herdar o título e o projeto vinculado)
        cur.execute(f'SELECT * FROM {TASKS_TABLE} WHERE __id = %s', (args.parent_id,))
        parent = cur.fetchone()
        
        if not parent:
            raise Exception(f"Task pai {args.parent_id} não encontrada no banco.")
            
        title = parent.get("Task_ID") or "Sem Título"
        project_link = parent.get("Projeto")
        
        # ID único para a nova task (ex: task_transcricao_{parent_id})
        clean_parent_id = args.parent_id.replace("task_spurgeon_", "").replace("task_transcribe_", "")
        is_transcribe = "transcribe" in args.next_task.lower()
        next_task_id = f"task_transcribe_{clean_parent_id}" if is_transcribe else f"task_render_{clean_parent_id}"
        
        # 2. Insere a nova task com status Pendente
        cur.execute(f'SELECT __id FROM {TASKS_TABLE} WHERE __id = %s', (next_task_id,))
        if not cur.fetchone():
            print(f"➕ Criando próxima task '{args.next_task}' para o sermão '{title}'...")
            cur.execute(f"""
                INSERT INTO {TASKS_TABLE} (__id, "Task_ID", "Instruction", "Status", "Projeto", "Task", "Area", __version, __created_time, __created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW(), %s)
            """, (next_task_id, title, args.instruction, "Pendente", project_link, args.next_task, args.area, USER_ID))
        else:
            print(f"🔄 Task '{args.next_task}' já existe no banco. Resetando para Pendente...")
            cur.execute(f"""
                UPDATE {TASKS_TABLE}
                SET "Instruction" = %s, "Status" = 'Pendente', "Projeto" = %s, "Task_ID" = %s, "Area" = %s
                WHERE __id = %s
            """, (args.instruction, project_link, title, args.area, next_task_id))
            
        conn.commit()
        print("✅ Próxima task enfileirada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar próxima task no banco: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
