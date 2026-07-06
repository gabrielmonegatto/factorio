import os
import sys
import json
import argparse
import re
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

# Adiciona o diretório atual ao sys.path para garantir importações locais robustas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from r2_client import upload_file_to_r2

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TASKS_TABLE = "tblVzN1Eo8tfk7GX2CJ"
PROJECTS_TABLE = "tblalvN0Db5K9S7Hrb6"

PROJECTS_FULL = f'"{SCHEMA}"."{PROJECTS_TABLE}"'
TASKS_FULL = f'"{SCHEMA}"."{TASKS_TABLE}"'

# Esquema de conteúdo para obter informações reais dos livros
SCHEMA_CONTENT = "bseWeczeNfCSaMlu2EC"
TBL_CONTENT = f'"{SCHEMA_CONTENT}"."tblFyPPXJTiynzBKFH2"'
TBL_INDEX = f'"{SCHEMA_CONTENT}"."tblD7Kxoc7gFTgEWoWo"'

def slugify(text):
    text = text.lower().strip()
    # Remove acentos
    import unicodedata
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '_', text)
    text = re.sub(r'-+', '-', text)
    return text

def slugify_hyphen(text):
    if not text:
        return ""
    import unicodedata
    s = unicodedata.normalize("NFD", text)
    s = s.encode("ascii", "ignore").decode("utf-8").lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def ensure_columns_exist(cur, conn):
    # Garante coluna spec na tabela de projetos
    cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = '{SCHEMA}' AND table_name = '{PROJECTS_TABLE}' AND column_name = 'spec'
    """)
    if not cur.fetchone():
        print("🔧 Criando coluna 'spec' in projects...")
        cur.execute(f'ALTER TABLE {PROJECTS_FULL} ADD COLUMN spec TEXT;')
        conn.commit()

    # Garante coluna resultado na tabela de tasks
    cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = '{SCHEMA}' AND table_name = '{TASKS_TABLE}' AND column_name = 'resultado'
    """)
    if not cur.fetchone():
        print("🔧 Criando coluna 'resultado' in tasks...")
        cur.execute(f'ALTER TABLE {TASKS_FULL} ADD COLUMN resultado TEXT;')
        conn.commit()

def update_task(cur, conn, record_id, status, logs, resultado=None):
    cur.execute(f"""
        UPDATE {TASKS_FULL}
        SET "Status" = %s, "Logs" = %s, "resultado" = %s, __last_modified_time = NOW()
        WHERE __id = %s
    """, (status, logs, resultado, record_id))
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description="Narrador integrado diretamente ao Postgres local do Teable")
    parser.add_argument("--record-id", required=True, help="ID do registro da task no Teable")
    args = parser.parse_args()

    record_id = args.record_id
    logs = f"[INFO] Iniciando processamento para a task {record_id}...\n"
    
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Garante que as colunas spec e resultado existam
        ensure_columns_exist(cur, conn)
        
        # 2. Busca os dados da task
        cur.execute(f'SELECT * FROM {TASKS_FULL} WHERE __id = %s', (record_id,))
        task = cur.fetchone()
        
        if not task:
            raise Exception(f"Task {record_id} não encontrada na tabela {TASKS_TABLE}.")
            
        instruction = task.get("Instruction")
        title = task.get("Task_ID") or task.get("Task") or "audio_sem_titulo"
        project_link = task.get("Projeto")
        
        if not instruction:
            raise Exception("A coluna 'Instruction' está vazia. Não há texto para narrar.")
            
        logs += f"[INFO] Task: {title}\n[INFO] Texto: {instruction[:60]}...\n"
        update_task(cur, conn, record_id, "Em Processamento", logs)
        
        # 3. Busca o projeto vinculado para extrair o Spec
        spec = {}
        project_id = None
        
        if project_link:
            try:
                p_ids = json.loads(project_link)
                if isinstance(p_ids, list) and len(p_ids) > 0:
                    project_id = p_ids[0]
            except Exception:
                project_id = project_link.strip('[]"\'')
                
        if project_id:
            logs += f"[INFO] Buscando especificações do projeto: {project_id}...\n"
            cur.execute(f'SELECT * FROM {PROJECTS_FULL} WHERE __id = %s', (project_id,))
            project = cur.fetchone()
            if project and project.get("spec"):
                try:
                    spec = json.loads(project["spec"])
                    logs += "[INFO] Especificações do projeto carregadas com sucesso.\n"
                except Exception as e:
                    logs += f"[AVISO] Falha ao parsear spec do projeto: {e}. Usando padrões.\n"
            else:
                logs += "[AVISO] Projeto encontrado mas sem coluna 'spec' ou valor vazio. Usando padrões.\n"
        else:
            logs += "[INFO] Nenhum projeto vinculado. Usando padrões de voz.\n"
            
        # Padrões do Narrador
        engine = spec.get("tts", {}).get("engine", "kokoro")
        voice = spec.get("tts", {}).get("voice", "bm_george")
        speed = spec.get("tts", {}).get("speed", 0.9)
        silence_ms = spec.get("tts", {}).get("silence_ms", 1000)
        lang = spec.get("tts", {}).get("lang", "a")
        output_base = spec.get("paths", {}).get("output_base", "apps/channels/channels_youtube/treasures_charlesspurgeon/")
        
        logs += f"[CONFIG] Engine: {engine} | Voz: {voice} | Speed: {speed}x | Pausa: {silence_ms}ms\n"
        update_task(cur, conn, record_id, "Em Processamento", logs)
        
        if engine != "kokoro":
            raise Exception(f"Motor de TTS '{engine}' não suportado.")
            
        # 4. Determina se é audiobook (ag_, fc_, me_) ou sermão tradicional (canal YouTube)
        title_lower = title.lower().strip()
        is_audiobook = title_lower.startswith(("ag", "fc", "me", "ptp", "pip", "nop", "wop", "rop", "eop"))
        
        temp_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp"))
        os.makedirs(temp_dir, exist_ok=True)
        temp_input = os.path.join(temp_dir, f"input_{record_id}.txt")
        
        # Salva texto temporário para o Kokoro ler
        with open(temp_input, "w", encoding="utf-8") as f:
            f.write(instruction)
            
        tts_script = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_kokoro.py"))
        
        if is_audiobook:
            logs += f"[INFO] Detectado como Audiobook. Pipeline R2 + MP3 ativado.\n"
            # Define caminhos de arquivo temporários
            audio_output_path = os.path.join(temp_dir, f"audio_{record_id}.wav")
            audio_mp3_path = os.path.join(temp_dir, f"audio_{record_id}.mp3")
        else:
            logs += f"[INFO] Detectado como Canal YouTube (Sermão). Mantendo fluxo local (WAV).\n"
            clean_slug = slugify(title)
            output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", output_base, clean_slug))
            os.makedirs(output_dir, exist_ok=True)
            
            # Nome do arquivo final (sermon_XX.wav)
            file_name = "audio.wav"
            num_match = re.match(r'^(\d+)', title)
            if num_match:
                num_clean = str(int(num_match.group(1))).zfill(2)
                file_name = f"sermon_{num_clean}.wav"
                
            audio_output_path = os.path.join(output_dir, file_name)
            audio_mp3_path = None
            
        # 5. Executa a síntese TTS Kokoro
        cmd = [
            sys.executable,
            tts_script,
            "--input", temp_input,
            "--output", audio_output_path,
            "--voice", voice,
            "--speed", str(speed),
            "--silence", str(silence_ms / 1000.0),
            "--lang", lang
        ]
        
        logs += f"[TTS] Executando comando de síntese...\n"
        update_task(cur, conn, record_id, "Em Processamento", logs)
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        # Limpa entrada de texto temporária
        if os.path.exists(temp_input):
            os.remove(temp_input)
            
        if res.returncode != 0:
            raise Exception(f"Erro no script de TTS:\nStdout: {res.stdout}\nStderr: {res.stderr}")
            
        # 6. Se for audiobook, comprime para MP3 e envia para o Cloudflare R2
        result_value = audio_output_path
        
        if is_audiobook:
            # A) Comprime para MP3 (128 kbps)
            logs += f"[FFmpeg] Convertendo WAV para MP3 (128 kbps)...\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", audio_output_path,
                "-vn",
                "-ab", "128k",
                "-ar", "44100",
                audio_mp3_path
            ]
            
            ff_res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if ff_res.returncode != 0:
                raise Exception(f"Erro ao converter áudio com FFmpeg:\nStderr: {ff_res.stderr}")
                
            # B) Busca metadados reais do livro no banco para determinar book_slug e chapter_slug
            book_slug = "unknown-book"
            chapter_slug = slugify_hyphen(title)
            clean_id = record_id.replace("task_spurgeon_", "")
            
            try:
                cur.execute(f"""
                    SELECT mc.title, mc.book_name, ci."Name" as book_index_name
                    FROM {TBL_CONTENT} mc
                    LEFT JOIN {TBL_INDEX} ci ON (ci.__id = mc.index_id OR ci.__auto_number::text = mc.index_id)
                    WHERE mc.__id = %s
                """, (clean_id,))
                mc_record = cur.fetchone()
                if mc_record:
                    book_name = mc_record.get("book_name") or mc_record.get("book_index_name")
                    if book_name:
                        book_slug = slugify_hyphen(book_name)
                    unit_title = mc_record.get("title")
                    if unit_title:
                        chapter_slug = slugify_hyphen(unit_title)
            except Exception as db_err:
                logs += f"[AVISO] Falha ao consultar metadados do livro no banco: {db_err}. Usando slugs gerados a partir do título da task.\n"
            
            # C) Upload para o R2
            r2_key = f"audiobooks/{book_slug}/{chapter_slug}.mp3"
            logs += f"[R2] Fazendo upload do MP3 para o bucket mananciall no path: '{r2_key}'...\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
            public_url = upload_file_to_r2(audio_mp3_path, r2_key)
            logs += f"[SUCESSO] Upload concluído! URL R2 pública: {public_url}\n"
            result_value = public_url
            
            # D) Remove os arquivos locais temporários
            if os.path.exists(audio_output_path):
                os.remove(audio_output_path)
            if os.path.exists(audio_mp3_path):
                os.remove(audio_mp3_path)
            logs += f"[CLEANUP] Arquivos temporários locais apagados para liberar espaço.\n"
            
        else:
            logs += f"[SUCESSO] Áudio local (WAV) gravado em: {audio_output_path}\n"
            
        # 7. Finaliza a task no banco
        update_task(cur, conn, record_id, "Concluído", logs, result_value)

        # 8. Enfileira a próxima task: Transcrever Áudio
        try:
            create_next_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "create_next_task.py"))
            cmd_next = [
                sys.executable,
                create_next_script,
                "--parent-id", record_id,
                "--next-task", "transcribe-audio",
                "--area", "channels",
                "--instruction", result_value
            ]
            res_next = subprocess.run(cmd_next, capture_output=True, text=True)
            if res_next.returncode == 0:
                logs += f"[PIPELINE] Próxima task enfileirada: {res_next.stdout.strip()}\n"
            else:
                logs += f"[AVISO] Falha ao enfileirar próxima task: {res_next.stderr.strip()}\n"
        except Exception as e_next:
            logs += f"[AVISO] Falha ao executar create_next_task.py: {e_next}\n"
        
        update_task(cur, conn, record_id, "Concluído", logs, result_value)
        print("✅ Execução concluída com sucesso!")
        
    except Exception as e:
        error_msg = f"\n❌ ERRO: {e}\n"
        print(error_msg, file=sys.stderr)
        logs += error_msg
        if conn:
            try:
                update_task(cur, conn, record_id, "Erro", logs)
            except Exception as pe:
                print(f"Erro ao salvar status de erro no banco: {pe}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
