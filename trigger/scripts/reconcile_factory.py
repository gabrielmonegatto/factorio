#!/usr/bin/env python3
import psycopg2
import json
import sys
from psycopg2.extras import RealDictCursor

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"

TBL_INDEX = f'"{SCHEMA}"."tblD7Kxoc7gFTgEWoWo"'     # content_index (projects)
TBL_CONTENT = f'"{SCHEMA}"."tblFyPPXJTiynzBKFH2"'   # mineration_content (chunks)
TBL_TASKS = f'"{SCHEMA}"."tblVzN1Eo8tfk7GX2CJ"'     # tasks (dashboard)

# Mapeamento amigável das etapas para o dashboard de tasks
ETAPAS_CONFIG = {
    "published_en": {
        "task_name": "Publicar Livro (EN)",
        "task_slug": "publish-books-en",
        "area": "produto"
    },
    "translation_es": {
        "task_name": "Traduzir Livro (ES)",
        "task_slug": "translate-content",
        "area": "produto"
    },
    "narration_es": {
        "task_name": "Narrar Áudio (ES)",
        "task_slug": "narrate-audio",
        "area": "channels"
    },
    "narration_en": {
        "task_name": "Narrar Áudio (EN)",
        "task_slug": "narrate-audio-en",
        "area": "channels"
    },
    "transcript_en": {
        "task_name": "Transcrever Áudio (EN)",
        "task_slug": "transcribe-audio",
        "area": "channels"
    }
}

def reconcile():
    print("🔌 Conectando ao banco de dados do Teable...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Obter todos os projetos/livros cadastrados na content_index
        cur.execute(f'SELECT __id, "Name", author, brand, project_slug, pipeline_state FROM {TBL_INDEX} ORDER BY __id;')
        projects = cur.fetchall()
        print(f"Encontrados {len(projects)} projetos no catálogo.")
        
        # 2. Obter estatísticas reais da CONTENT para cada projeto
        cur.execute(f"""
            SELECT 
                index_id,
                COUNT(*) as total,
                COUNT(CASE WHEN (pipeline_state->'published_en'->>'status') = 'done' THEN 1 END) as published_en_done,
                COUNT(CASE WHEN (pipeline_state->'translation_es'->>'status') = 'done' OR (pipeline_state->'translation_es'->>'content') IS NOT NULL THEN 1 END) as translation_es_done,
                COUNT(CASE WHEN (pipeline_state->'narration_es'->>'status') = 'done' OR (pipeline_state->'narration_es'->>'r2_url') IS NOT NULL THEN 1 END) as narration_es_done,
                COUNT(CASE WHEN (pipeline_state->'narration_en'->>'status') = 'done' OR (pipeline_state->'narration_en'->>'r2_url') IS NOT NULL THEN 1 END) as narration_en_done,
                COUNT(CASE WHEN (pipeline_state->'transcript_en'->>'status') = 'done' OR (pipeline_state->'transcript_en'->>'r2_url') IS NOT NULL THEN 1 END) as transcript_en_done
            FROM {TBL_CONTENT}
            GROUP BY index_id;
        """)
        stats_rows = cur.fetchall()
        stats_by_project = {row['index_id']: row for row in stats_rows}
        
        for proj in projects:
            proj_id = proj['__id']
            proj_name = proj['Name'] or "Sem Nome"
            author = proj['author'] or "Charles Spurgeon"
            brand = proj['brand'] or 'mananciall'
            project_slug = proj['project_slug'] or 'unknown'
            
            # Catálogo é agnóstico (Mineração). A área (canal ou produto) é determinada pelo slug do projeto
            if project_slug == 'yt_en_treasures_spurgeon':
                area = 'channels'
            else:
                area = 'produto'
            
            # Se o projeto não tem chunks na CONTENT, ignorar ou zerar
            stats = stats_by_project.get(proj_id, {
                "total": 0, "published_en_done": 0, "translation_es_done": 0,
                "narration_es_done": 0, "narration_en_done": 0, "transcript_en_done": 0
            })
            
            total = stats['total']
            if total == 0:
                continue
                
            pipeline_state = proj['pipeline_state'] or {}
            if isinstance(pipeline_state, str):
                pipeline_state = json.loads(pipeline_state)
                
            # Atualizar os estados agregados de cada etapa na INDEX
            stages = {
                "published_en": stats["published_en_done"],
                "translation_es": stats["translation_es_done"],
                "narration_es": stats["narration_es_done"],
                "narration_en": stats["narration_en_done"],
                "transcript_en": stats["transcript_en_done"]
            }
            
            updated_index_pipeline = {}
            
            for stage_key, done_count in stages.items():
                # Calcula porcentagem
                pct = int((done_count / total) * 100) if total > 0 else 0
                status = "done" if done_count == total else "pending"
                
                # Para manter compatibilidade com chaves antigas se houver
                current_stage_data = pipeline_state.get(stage_key) or {}
                if isinstance(current_stage_data, str):
                    try: current_stage_data = json.loads(current_stage_data)
                    except: current_stage_data = {}
                
                new_stage_data = {
                    "status": status,
                    "total": total,
                    "done": done_count,
                    "pct": pct
                }
                
                pipeline_state[stage_key] = new_stage_data
                
                # 3. Garantir a existência do registro correspondente na tabela TASKS (dashboard)
                # Chave canônica da task: task_{stage_key}_{proj_id}
                task_ref_id = f"task_{stage_key}_{proj_id}"
                
                # Configuração da etapa
                cfg = ETAPAS_CONFIG.get(stage_key, {"task_name": stage_key, "task_slug": stage_key, "area": "produto"})
                
                task_title = f"{cfg['task_name']} — {proj_name}"
                progress_str = f"{done_count}/{total}"
                
                # Mapeia status do teable
                teable_status = "Concluído" if status == "done" else "Pendente"
                
                # Se o progresso já começou mas não terminou, marca como Em Processamento
                if 0 < done_count < total:
                    teable_status = "Em Processamento"
                    
                # Verifica se a task existe
                cur.execute(f'SELECT __id, "Status", "progresso" FROM {TBL_TASKS} WHERE __id = %s', (task_ref_id,))
                existing_task = cur.fetchone()
                
                # Projeto em formato de link para o Teable (JSON array com o ID do catálogo)
                projeto_link = json.dumps([proj_id])
                
                # Nome da tarefa (curto)
                task_short = cfg['task_slug']

                if not existing_task:
                    # Se não existe, cria a task agregada
                    print(f"  [+] Criando task agregada {task_ref_id} ({brand}/{area}/{project_slug}/{task_short}) no dashboard...")
                    cur.execute(f"""
                        INSERT INTO {TBL_TASKS} (
                            __id, "Task_ID", "Status", "progresso", "Projeto", "task", "area",
                            "brand", "project_slug", __created_by, __version
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1);
                    """, (
                        task_ref_id, task_title, teable_status, progress_str, projeto_link,
                        task_short, area, brand, project_slug, "usrCe4LHiMshx2Cw3C0"
                    ))
                else:
                    # Se já existe, atualiza progresso e as novas colunas
                    print(f"  [*] Sincronizando task {task_ref_id} ({brand}/{area}/{project_slug}/{task_short}): {progress_str} ({teable_status})...")
                    cur.execute(f"""
                        UPDATE {TBL_TASKS}
                        SET "Status" = %s, "progresso" = %s, "task" = %s, "area" = %s, 
                            "brand" = %s, "project_slug" = %s, __last_modified_time = NOW()
                        WHERE __id = %s;
                    """, (teable_status, progress_str, task_short, area, brand, project_slug, task_ref_id))
            
            # 4. Grava o novo pipeline_state na content_index
            cur.execute(f"""
                UPDATE {TBL_INDEX} 
                SET pipeline_state = %s::jsonb, __last_modified_time = NOW() 
                WHERE __id = %s;
            """, (json.dumps(pipeline_state, ensure_ascii=False), proj_id))
            
        conn.commit()
        print("🎉 RECONCILIAÇÃO COMPLETA! Todas as tabelas sincronizadas.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ ERRO na Reconciliação: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    reconcile()
