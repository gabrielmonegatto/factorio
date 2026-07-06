import os
import sys
import json
import time
import argparse
import requests
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
import re

# Adiciona o diretório atual ao sys.path para garantir importações locais robustas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from r2_client import upload_file_to_r2

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TASKS_TABLE = "tblVzN1Eo8tfk7GX2CJ"
TASKS_FULL = f'"{SCHEMA}"."{TASKS_TABLE}"'

SCHEMA_CONTENT = "bseWeczeNfCSaMlu2EC"
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

def slugify_hyphen(text):
    if not text:
        return ""
    import unicodedata
    s = unicodedata.normalize("NFD", text)
    s = s.encode("ascii", "ignore").decode("utf-8").lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def update_task(cur, conn, record_id, status, logs, resultado=None):
    cur.execute(f"""
        UPDATE {TASKS_FULL}
        SET "Status" = %s, "Logs" = %s, "resultado" = %s, __last_modified_time = NOW()
        WHERE __id = %s
    """, (status, logs, resultado, record_id))
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description="Transcritor integrado à API do Groq (Whisper)")
    parser.add_argument("--record-id", required=True, help="ID da task no Teable/Postgres")
    args = parser.parse_args()

    record_id = args.record_id
    logs = f"[INFO] Iniciando processamento de transcrição para a task {record_id}...\n"
    
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Busca os dados da task
        cur.execute(f'SELECT * FROM {TASKS_FULL} WHERE __id = %s', (record_id,))
        task = cur.fetchone()
        
        if not task:
            raise Exception(f"Task {record_id} não encontrada na tabela {TASKS_TABLE}.")
            
        audio_path = task.get("Instruction")
        title = task.get("Task_ID") or "sermon_sem_titulo"
        
        if not audio_path:
            raise Exception("A coluna 'Instruction' está vazia. Não há caminho de áudio para transcrever.")
            
        is_url = audio_path.startswith(("http://", "https://"))
        temp_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp"))
        os.makedirs(temp_dir, exist_ok=True)
        
        is_temp_download = False
        
        if is_url:
            logs += f"[INFO] Task: {title}\n[INFO] Áudio é um link remoto R2: {audio_path}\n"
            logs += f"[R2] Efetuando download do áudio temporário para transcrição...\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
            local_audio_path = os.path.join(temp_dir, f"audio_transcribe_{record_id}.mp3")
            resp = requests.get(audio_path)
            if resp.status_code != 200:
                raise Exception(f"Falha ao baixar áudio do R2 (Status {resp.status_code}): {resp.reason}")
            with open(local_audio_path, "wb") as f:
                f.write(resp.content)
            
            audio_path = local_audio_path
            is_temp_download = True
        else:
            audio_path = os.path.abspath(audio_path)
            if not os.path.exists(audio_path):
                raise Exception(f"Arquivo de áudio não encontrado no caminho: {audio_path}")
            logs += f"[INFO] Task: {title}\n[INFO] Áudio de entrada local: {audio_path}\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
        # 2. Carrega credenciais do .env
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
        env_vars = load_env(env_path)
        api_key = env_vars.get("GROQ_API_KEY")
        
        if not api_key:
            raise Exception("Chave GROQ_API_KEY não encontrada no arquivo .env")
            
        # 3. Comprime o áudio se for WAV ou muito grande (> 20MB) para caber no limite de 25MB da API
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        use_temp_mp3 = False
        upload_path = audio_path
        
        # Só comprime se for local e terminar com .wav ou for muito grande
        if (audio_path.lower().endswith(".wav") or file_size_mb > 20.0) and not is_url:
            logs += f"[INFO] Áudio original é muito grande ({file_size_mb:.2f} MB) ou está em formato WAV. Comprimindo para MP3 temporário de voz...\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
            temp_mp3 = os.path.join(os.path.dirname(audio_path), "temp_transcribe.mp3")
            
            # Comando FFmpeg otimizado para fala (16kHz sample rate, 1 canal mono, 48kbps bitrate)
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", audio_path,
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                "-ab", "48k",
                "-f", "mp3",
                temp_mp3
            ]
            
            try:
                subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                upload_path = temp_mp3
                use_temp_mp3 = True
                compressed_size = os.path.getsize(temp_mp3) / (1024 * 1024)
                logs += f"[INFO] Compressão via FFmpeg concluída com sucesso. Novo tamanho: {compressed_size:.2f} MB\n"
                update_task(cur, conn, record_id, "Em Processamento", logs)
            except Exception as fe:
                logs += f"[AVISO] Falha ao comprimir via FFmpeg: {fe}. Tentando enviar o áudio original mesmo assim...\n"
                update_task(cur, conn, record_id, "Em Processamento", logs)
        
        logs += "[GROQ] Enviando áudio para transcrição via API do Groq (Whisper Large v3)...\n"
        update_task(cur, conn, record_id, "Em Processamento", logs)
        
        # 4. Envia o áudio para o Groq
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        data = [
            ("model", "whisper-large-v3"),
            ("response_format", "verbose_json"),
            ("timestamp_granularities[]", "word"),
            ("timestamp_granularities[]", "segment")
        ]
        
        file_name = os.path.basename(upload_path)
        mime_type = "audio/mpeg" if file_name.endswith(".mp3") else "audio/wav"
        
        with open(upload_path, "rb") as f_audio:
            files = {
                "file": (file_name, f_audio, mime_type)
            }
            logs += f"[GROQ] Chamando API do Groq de forma síncrona...\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
            response = requests.post(url, headers=headers, data=data, files=files)
            
        # Apaga o arquivo temporário de compressão de áudio local imediatamente
        if use_temp_mp3 and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
                logs += "[INFO] Arquivo temporário de áudio comprimido removido.\n"
                update_task(cur, conn, record_id, "Em Processamento", logs)
            except Exception as re:
                logs += f"[AVISO] Falha ao remover arquivo temporário: {re}\n"
                update_task(cur, conn, record_id, "Em Processamento", logs)
            
        if response.status_code != 200:
            raise Exception(f"Falha na API do Groq (Status {response.status_code}): {response.text}")
            
        groq_data = response.json()
        logs += "[GROQ] Transcrição concluída pela API. Iniciando mapeamento de formato...\n"
        update_task(cur, conn, record_id, "Em Processamento", logs)
        
        # Mapeia a resposta do Groq para o formato compatível com o conversor json_to_ass.py
        words_raw = []
        if "words" in groq_data:
            words_raw = groq_data["words"]
        elif "segments" in groq_data:
            for seg in groq_data["segments"]:
                if "words" in seg:
                    words_raw.extend(seg["words"])
                    
        assembly_style_result = {
            "text": groq_data.get("text", ""),
            "words": []
        }
        
        for w in words_raw:
            word_text = w.get("word") or w.get("text") or ""
            start_ms = int(w.get("start", 0.0) * 1000)
            end_ms = int(w.get("end", 0.0) * 1000)
            
            assembly_style_result["words"].append({
                "text": word_text,
                "start": start_ms,
                "end": end_ms
            })
            
        # 5. Salva a transcrição no R2 se for URL, senão salva localmente
        if is_url:
            temp_json = os.path.join(temp_dir, f"transcript_{record_id}.json")
            with open(temp_json, "w", encoding="utf-8") as f:
                json.dump(assembly_style_result, f, indent=2, ensure_ascii=False)
                
            # Busca metadados reais do livro no banco para determinar book_slug e chapter_slug
            book_slug = "unknown-book"
            chapter_slug = slugify_hyphen(title)
            clean_id = record_id.replace("task_transcribe_", "")
            
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
                
            r2_key = f"audiobooks/{book_slug}/{chapter_slug}.json"
            logs += f"[R2] Fazendo upload do JSON de transcrição para o R2 no path '{r2_key}'...\n"
            update_task(cur, conn, record_id, "Em Processamento", logs)
            
            public_url = upload_file_to_r2(temp_json, r2_key)
            logs += f"[SUCESSO] Transcrição salva no R2 com sucesso! URL pública: {public_url}\n"
            
            # Remove arquivos temporários locais
            if os.path.exists(temp_json):
                os.remove(temp_json)
            if is_temp_download and os.path.exists(audio_path):
                os.remove(audio_path)
            
            transcript_result = public_url
        else:
            # Fluxo local tradicional
            output_dir = os.path.dirname(audio_path)
            transcript_output_path = os.path.join(output_dir, "transcript.json")
            
            with open(transcript_output_path, "w", encoding="utf-8") as f:
                json.dump(assembly_style_result, f, indent=2, ensure_ascii=False)
                
            logs += f"[SUCESSO] Transcrição concluída e salva localmente em: {transcript_output_path}\n"
            transcript_result = transcript_output_path
            
        update_task(cur, conn, record_id, "Concluído", logs, transcript_result)
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
