import os
import sys
import json
import argparse
import re
import psycopg2
from psycopg2.extras import RealDictCursor

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TASKS_TABLE = "tblVzN1Eo8tfk7GX2CJ"
PROJECTS_TABLE = "tblalvN0Db5K9S7Hrb6"

PROJECTS_FULL = f'"{SCHEMA}"."{PROJECTS_TABLE}"'
TASKS_FULL = f'"{SCHEMA}"."{TASKS_TABLE}"'

def slugify(text):
    text = text.lower().strip()
    import unicodedata
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '_', text)
    text = re.sub(r'-+', '-', text)
    return text

def ensure_columns_exist(cur, conn):
    # Garante coluna spec na tabela de projetos
    cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = '{SCHEMA}' AND table_name = '{PROJECTS_TABLE}' AND column_name = 'spec'
    """)
    if not cur.fetchone():
        print("🔧 Criando coluna 'spec' em projects...")
        cur.execute(f'ALTER TABLE {PROJECTS_FULL} ADD COLUMN spec TEXT;')
        conn.commit()

    # Garante colunas na tabela de tasks
    cols_to_check = {
        'resultado': 'TEXT',
        'background_image': 'TEXT',
        'preacher_image': 'TEXT',
        'bgm_audio': 'TEXT'
    }
    for col_name, col_type in cols_to_check.items():
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA}' AND table_name = '{TASKS_TABLE}' AND column_name = '{col_name}'
        """)
        if not cur.fetchone():
            print(f"🔧 Criando coluna '{col_name}' em tasks...")
            cur.execute(f'ALTER TABLE {TASKS_FULL} ADD COLUMN "{col_name}" {col_type};')
            conn.commit()

def get_task_info(record_id):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(f'SELECT * FROM {TASKS_FULL} WHERE __id = %s', (record_id,))
        task = cur.fetchone()
        if not task:
            raise Exception(f"Task {record_id} não encontrada na tabela.")
            
        title = task.get("Task_ID") or "sermon_sem_titulo"
        clean_slug = slugify(title)
        
        # O caminho base de saída é tirado das especificações do projeto
        project_link = task.get("Projeto")
        project_id = None
        if project_link:
            try:
                p_ids = json.loads(project_link)
                if isinstance(p_ids, list) and len(p_ids) > 0:
                    project_id = p_ids[0]
            except Exception:
                project_id = project_link.strip('[]"\'')
                
        output_base = "apps/channels/channels_youtube/treasures_charlesspurgeon/"
        if project_id:
            cur.execute(f'SELECT * FROM {PROJECTS_FULL} WHERE __id = %s', (project_id,))
            project = cur.fetchone()
            if project and project.get("spec"):
                try:
                    spec = json.loads(project["spec"])
                    output_base = spec.get("paths", {}).get("output_base", output_base)
                except Exception:
                    pass
                    
        sermon_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", output_base, clean_slug))
        transcript_path = os.path.join(sermon_dir, "transcript.json")
        
        # Extrai o número do sermão do título (ex: '0011 - The People\'s Christ' -> '0011')
        sermon_number = "0001"
        num_match = re.match(r'^(\d+)', title)
        if num_match:
            sermon_number = num_match.group(1).zfill(4)
            
        # Extrai o título limpo do sermão (removendo número e hífen)
        sermon_title = title
        title_match = re.match(r'^\d+\s*-\s*(.*)', title)
        if title_match:
            sermon_title = title_match.group(1).strip()
            
        info = {
            "recordId": record_id,
            "title": title,
            "sermonTitle": sermon_title,
            "sermonNumber": sermon_number,
            "sermonDir": sermon_dir,
            "transcriptPath": transcript_path,
        }
        print(json.dumps(info, indent=2))
    finally:
        cur.close()
        conn.close()

def update_task_status(record_id, status, logs=None, resultado=None, background_image=None, preacher_image=None, bgm_audio=None):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        # Garante as colunas necessárias antes da alteração
        ensure_columns_exist(cur, conn)
        
        fields = ['"Status" = %s', '__last_modified_time = NOW()']
        params = [status]
        
        if logs is not None:
            fields.append('"Logs" = COALESCE("Logs", \'\') || %s')
            params.append(logs)
            
        if resultado is not None:
            fields.append('"resultado" = %s')
            params.append(resultado)
            
        if background_image is not None:
            fields.append('"background_image" = %s')
            params.append(background_image)
            
        if preacher_image is not None:
            fields.append('"preacher_image" = %s')
            params.append(preacher_image)
            
        if bgm_audio is not None:
            fields.append('"bgm_audio" = %s')
            params.append(bgm_audio)
            
        params.append(record_id)
        
        query = f"""
            UPDATE {TASKS_FULL}
            SET {", ".join(fields)}
            WHERE __id = %s
        """
        cur.execute(query, tuple(params))
        conn.commit()
        print(f"✅ Status da task {record_id} atualizado para: {status}")
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Helper de banco de dados para renderização de vídeo")
    parser.add_argument("--record-id", required=True, help="ID da task no Teable")
    parser.add_argument("--get-info", action="store_true", help="Obtém informações estruturadas do sermão")
    parser.add_argument("--update-status", choices=["Pendente", "Em Processamento", "Concluído", "Erro"], help="Atualiza o status da task")
    parser.add_argument("--logs", help="Mensagem de log para concatenar")
    parser.add_argument("--resultado", help="Resultado final da task (caminho do arquivo mp4)")
    parser.add_argument("--background-image", help="Catedral utilizada de fundo")
    parser.add_argument("--preacher-image", help="Busto do pregador utilizado")
    parser.add_argument("--bgm-audio", help="Música de fundo utilizada")
    
    args = parser.parse_args()
    
    try:
        if args.get_info:
            get_task_info(args.record_id)
        elif args.update_status:
            update_task_status(
                args.record_id, 
                args.update_status, 
                args.logs, 
                args.resultado, 
                args.background_image, 
                args.preacher_image, 
                args.bgm_audio
            )
        else:
            parser.print_help()
    except Exception as e:
        print(f"❌ ERRO: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
