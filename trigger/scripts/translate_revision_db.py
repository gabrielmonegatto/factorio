import os
import sys
import json
import argparse
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time
import re

# Configurações do Banco
import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA_WORKFLOW = "bseWeczeNfCSaMlu2EC"
SCHEMA_CONTENT = "bseWeczeNfCSaMlu2EC"

TASKS_FULL = f'"{SCHEMA_WORKFLOW}"."tblVzN1Eo8tfk7GX2CJ"'
TBL_CONTENT = f'"{SCHEMA_CONTENT}"."tblFyPPXJTiynzBKFH2"'
TBL_INDEX = f'"{SCHEMA_CONTENT}"."tblD7Kxoc7gFTgEWoWo"'

def load_env(env_path):
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"\'')
    return env_vars

def update_task(cur, conn, record_id, status, logs, resultado=None):
    cur.execute(f"""
        UPDATE {TASKS_FULL}
        SET "Status" = %s, "Logs" = %s, "resultado" = %s, __last_modified_time = NOW()
        WHERE __id = %s
    """, (status, logs, resultado, record_id))
    conn.commit()

def translate_with_gemini(text, title, api_key):
    # Tentamos com gemini-3.1-flash-lite. Se falhar, fazemos fallback automático para gemini-1.5-flash
    models = ["gemini-3.1-flash-lite", "gemini-1.5-flash"]
    last_err = None

    prompt = f"""
Você é um tradutor teológico experiente. Traduza o seguinte título e texto devocional de Charles Spurgeon do inglês para o espanhol.
Use uma linguagem reverente, solene e apropriada para a teologia reformada protestante clássica em espanhol (ex: use termos consagrados como "Gracia", "Soberanía", "Redentor").
Preserve todos os parágrafos e quebras de linha exatamente como estão.

Título Original: {title}
Texto Original:
{text}

Retorne o resultado estritamente no seguinte formato JSON (sem markdown envolta, apenas o JSON puro):
{{
  "titulo_traduzido": "sua tradução aqui",
  "texto_traduzido": "sua tradução aqui"
}}
"""

    for model in models:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": {
                            "type": "object",
                            "properties": {
                                "titulo_traduzido": {"type": "string"},
                                "texto_traduzido": {"type": "string"}
                            },
                            "required": ["titulo_traduzido", "texto_traduzido"]
                        }
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    text_out = res_json['candidates'][0]['content']['parts'][0]['text']
                    data = json.loads(text_out.strip())
                    return data, model
                elif response.status_code == 429:
                    print(f"⚠️ Gemini 429 Rate Limit. Dormindo 10s (Tentativa {attempt+1}/{max_retries})...", file=sys.stderr)
                    time.sleep(10)
                else:
                    last_err = f"API Error {response.status_code}: {response.text}"
                    break # Pula para o próximo modelo se for outro erro
            except Exception as e:
                last_err = str(e)
                time.sleep(5)
            
    raise Exception(f"Falha na tradução com Gemini (Todos os modelos tentados falharam). Último erro: {last_err}")

def revise_with_llama(original_text, original_title, translated_text, translated_title, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Você é um revisor de teologia clássica reformada em espanhol. Sua tarefa é comparar o texto original em inglês de Charles Spurgeon com o rascunho de tradução em espanhol fornecido e fazer correções estilísticas e teológicas para que o espanhol flua de forma eloqüente, natural e reverente (combinando com o estilo dos sermões clássicos em espanhol).

Título Original (EN): {original_title}
Rascunho do Título Traduzido (ES): {translated_title}

Texto Original (EN):
{original_text}

Rascunho do Texto Traduzido (ES):
{translated_text}

Por favor, faça a revisão fina do título e do texto. Retorne o resultado estritamente no seguinte formato JSON (sem markdown envolta, apenas o JSON puro):
{{
  "titulo_revisado": "sua revisão aqui",
  "texto_revisado": "sua revisão aqui"
}}
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {
            "type": "json_object"
        },
        "temperature": 0.2
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                content_out = res_json['choices'][0]['message']['content']
                data = json.loads(content_out.strip())
                return data
            elif response.status_code == 429:
                retry_after = 20.0
                try:
                    res_err = response.json()
                    msg = res_err.get("error", {}).get("message", "")
                    m = re.search(r"try again in ([\d\.]+)s", msg)
                    if m:
                        retry_after = float(m.group(1)) + 2.0
                except:
                    pass
                print(f"⚠️ Groq 429 Rate Limit. Dormindo {retry_after:.2f}s (Tentativa {attempt+1}/{max_retries})...", file=sys.stderr)
                time.sleep(retry_after)
            else:
                raise Exception(f"Groq API Error {response.status_code}: {response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Falha na revisão estilística com Llama após {max_retries} tentativas: {e}")
            print(f"⚠️ Erro na chamada do Groq: {e}. Tentando novamente...", file=sys.stderr)
            time.sleep(5)
    raise Exception(f"Falha na revisão estilística com Llama após {max_retries} tentativas (fim do loop).")

def revise_with_gemini(original_text, original_title, translated_text, translated_title, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
Você é um revisor de teologia clássica reformada em espanhol. Sua tarefa é comparar o texto original em inglês de Charles Spurgeon com o rascunho de tradução em espanhol fornecido e fazer correções estilísticas e teológicas para que o espanhol flua de forma eloqüente, natural e reverente (combinando com o estilo dos sermões clássicos em espanhol).

Título Original (EN): {original_title}
Rascunho do Título Traduzido (ES): {translated_title}

Texto Original (EN):
{original_text}

Rascunho do Texto Traduzido (ES):
{translated_text}

Por favor, faça a revisão fina do título e do texto. Retorne o resultado estritamente no seguinte formato JSON (sem markdown envolta, apenas o JSON puro):
{{
  "titulo_revisado": "sua revisão aqui",
  "texto_revisado": "sua revisão aqui"
}}
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "titulo_revisado": {"type": "string"},
                    "texto_revisado": {"type": "string"}
                },
                "required": ["titulo_revisado", "texto_revisado"]
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        res_json = response.json()
        content_out = res_json['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(content_out.strip())
        return data
    else:
        raise Exception(f"Gemini Revision Fallback Error {response.status_code}: {response.text}")

def main():
    logs = ""
    parser = argparse.ArgumentParser(description="Esteira de Tradução e Revisão do Factorio")
    parser.add_argument("--project-id", help="ID do projeto (livro) no catálogo")
    parser.add_argument("--chunk-id", help="ID do chunk específico para tradução isolada")
    parser.add_argument("--limit", type=int, default=10, help="Limite de chunks a processar")
    args = parser.parse_args()

    if not args.project_id and not args.chunk_id:
        print("❌ Erro: Forneça --project-id ou --chunk-id", file=sys.stderr)
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Carrega as chaves do .env
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
        env_vars = load_env(env_path)
        
        gemini_key = env_vars.get("GEMINI_API_KEY")
        groq_key = env_vars.get("GROQ_API_KEY")
        
        if not gemini_key or not groq_key:
            raise Exception("Chaves GEMINI_API_KEY ou GROQ_API_KEY não encontradas no arquivo .env")

        # 2. Determinar o ID da task agregada para logs
        if args.project_id:
            project_id = args.project_id
            task_ref_id = f"task_translation_es_{project_id}"
            
            # Garante que a task agregada existe no dashboard
            cur.execute(f'SELECT "Name" FROM {TBL_INDEX} WHERE __id = %s', (project_id,))
            proj_row = cur.fetchone()
            proj_name = proj_row["Name"] if proj_row else "Livro Desconhecido"
            
            cur.execute(f'SELECT __id FROM {TASKS_FULL} WHERE __id = %s', (task_ref_id,))
            if not cur.fetchone():
                cur.execute(f"""
                    INSERT INTO {TASKS_FULL} (
                        __id, "Task_ID", "Status", "progresso", "Projeto", "Task", "Area", "Instruction", "Logs",
                        __created_by, __version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    task_ref_id, f"Traduzir Livro (ES) — {proj_name}", "Pendente", "0/0", json.dumps([project_id]),
                    "translate-content", "produto", f"Processamento de tradução do livro {proj_name}",
                    "[INFO] Iniciado automaticamente pelo runner.\n", "usrCe4LHiMshx2Cw3C0", 1
                ))
                conn.commit()
        else:
            task_ref_id = f"task_chunk_translation_{args.chunk_id}"

        logs = f"[INFO] Iniciando esteira de Tradução e Revisão. Target: Project={args.project_id}, Chunk={args.chunk_id}\n"
        update_task(cur, conn, task_ref_id, "Em Processamento", logs)

        # 3. Buscar os chunks para processamento
        if args.chunk_id:
            cur.execute(f'SELECT __id, title, content, pipeline_state, index_id FROM {TBL_CONTENT} WHERE __id = %s', (args.chunk_id,))
            chunks = cur.fetchall()
        else:
            cur.execute(f"""
                SELECT __id, title, content, pipeline_state, index_id 
                FROM {TBL_CONTENT} 
                WHERE index_id = %s 
                  AND content IS NOT NULL AND content != ''
                  AND (pipeline_state IS NULL OR pipeline_state->'translation_es'->>'content' IS NULL)
                ORDER BY __id ASC
                LIMIT %s;
            """, (project_id, args.limit))
            chunks = cur.fetchall()

        if not chunks:
            logs += "[INFO] Nenhum chunk pendente encontrado para processar.\n"
            update_task(cur, conn, task_ref_id, "Concluído", logs, "Nenhum chunk pendente.")
            print("Nenhum chunk pendente.")
            return

        logs += f"[INFO] Encontrados {len(chunks)} chunks pendentes. Iniciando loop de tradução...\n"
        update_task(cur, conn, task_ref_id, "Em Processamento", logs)

        for i, chunk in enumerate(chunks):
            chunk_id = chunk["__id"]
            title = chunk["title"] or "Sem Título"
            instruction = chunk["content"]
            
            logs += f"\n--- [{i+1}/{len(chunks)}] Processando Chunk: {title} ({chunk_id}) ---\n"
            update_task(cur, conn, task_ref_id, "Em Processamento", logs)

            # Fase de Tradução (Gemini)
            logs += f"  [GEMINI] Traduzindo '{title[:30]}'...\n"
            update_task(cur, conn, task_ref_id, "Em Processamento", logs)
            
            try:
                translation_data, used_model = translate_with_gemini(instruction, title, gemini_key)
                translated_title = translation_data.get("titulo_traduzido")
                translated_text = translation_data.get("texto_traduzido")
                logs += f"  [GEMINI] Tradução concluída via {used_model}.\n"
            except Exception as e:
                logs += f"  [ERRO GEMINI] {e}\n"
                update_task(cur, conn, task_ref_id, "Erro", logs)
                raise e

            # Fase de Revisão (Llama / Gemini fallback)
            logs += "  [LLAMA] Revisando teologia...\n"
            update_task(cur, conn, task_ref_id, "Em Processamento", logs)
            
            try:
                revision_data = revise_with_llama(
                    instruction, title,
                    translated_text, translated_title,
                    groq_key
                )
                logs += "  [LLAMA] Revisão concluída via Groq.\n"
            except Exception as groq_err:
                logs += f"  [AVISO GROQ] {groq_err}. Fallback para Gemini...\n"
                update_task(cur, conn, task_ref_id, "Em Processamento", logs)
                try:
                    revision_data = revise_with_gemini(
                        instruction, title,
                        translated_text, translated_title,
                        gemini_key
                    )
                    logs += "  [GEMINI-FALLBACK] Revisão concluída via fallback.\n"
                except Exception as e:
                    logs += f"  [ERRO FALLBACK] {e}\n"
                    update_task(cur, conn, task_ref_id, "Erro", logs)
                    raise e

            revised_title = revision_data.get("titulo_revisado")
            revised_text = revision_data.get("texto_revisado")

            # Salvar no pipeline_state do chunk
            pipeline_state = chunk.get("pipeline_state") or {}
            if isinstance(pipeline_state, str):
                try: pipeline_state = json.loads(pipeline_state)
                except: pipeline_state = {}

            pipeline_state["translation_es"] = {
                "status": "done",
                "title": revised_title,
                "content": revised_text,
                "updated_at": datetime.now().isoformat()
            }

            cur.execute(f"""
                UPDATE {TBL_CONTENT}
                SET pipeline_state = %s::jsonb, __last_modified_time = NOW()
                WHERE __id = %s
            """, (json.dumps(pipeline_state, ensure_ascii=False), chunk_id))
            conn.commit()
            
            logs += f"  [SUCESSO] Chunk {chunk_id} gravado no banco.\n"
            update_task(cur, conn, task_ref_id, "Em Processamento", logs)

        # 4. Chamar reconciliação para atualizar o progresso geral
        logs += "\n[RECONCILIATION] Iniciando reconciliação de progresso...\n"
        update_task(cur, conn, task_ref_id, "Em Processamento", logs)
        
        try:
            # Importa e executa a reconciliação localmente
            from reconcile_factory import reconcile
            reconcile()
            logs += "[RECONCILIATION] Reconciliação concluída.\n"
        except Exception as re_err:
            logs += f"[AVISO RECONCILIATION] Erro ao sincronizar: {re_err}\n"

        logs += "\n[FIM] Lote processado com sucesso!\n"
        update_task(cur, conn, task_ref_id, "Concluído", logs, "Lote concluído.")
        print("Lote concluído com sucesso!")

    except Exception as e:
        error_msg = f"\n❌ ERRO na esteira de tradução/revisão: {e}\n"
        print(error_msg, file=sys.stderr)
        if conn:
            try:
                update_task(cur, conn, task_ref_id, "Erro", logs + error_msg)
            except Exception as pe:
                print(f"Erro ao salvar status de erro no banco: {pe}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
