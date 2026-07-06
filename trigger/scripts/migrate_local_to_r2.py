import os
import sys
import json
import re
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Adiciona o diretório atual ao sys.path para garantir importações locais robustas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from r2_client import upload_file_to_r2

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA_CONTENT = "bseWeczeNfCSaMlu2EC"
TBL_CONTENT = f'"{SCHEMA_CONTENT}"."tblFyPPXJTiynzBKFH2"'
TBL_INDEX = f'"{SCHEMA_CONTENT}"."tblD7Kxoc7gFTgEWoWo"'

# Lock para sincronização de prints e contadores
print_lock = threading.Lock()
migrated_count = 0
skipped_count = 0
error_count = 0
processed_count = 0

def slugify_hyphen(text):
    if not text:
        return ""
    import unicodedata
    s = unicodedata.normalize("NFD", text)
    s = s.encode("ascii", "ignore").decode("utf-8").lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def migrate_single_record(row, idx, total_records, temp_dir):
    global migrated_count, skipped_count, error_count, processed_count
    
    rec_id = row["__id"]
    title = row["title"] or "Sem Título"
    book_name = row["book_name"] or row["book_index_name"] or "unknown-book"
    
    # Carrega metadados e pipeline_state
    try:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
    except Exception:
        meta = {}
        
    try:
        pipeline_state = row["pipeline_state"] if isinstance(row["pipeline_state"], dict) else json.loads(row["pipeline_state"] or "{}")
    except Exception:
        pipeline_state = {}
        
    # Verifica se já está no R2
    audio_url_exist = pipeline_state.get("narration_en", {}).get("r2_url")
    json_url_exist = pipeline_state.get("transcript_en", {}).get("r2_url")
    
    if audio_url_exist and json_url_exist:
        with print_lock:
            processed_count += 1
            skipped_count += 1
            print(f"[{processed_count}/{total_records}] ℹ️ Registro {rec_id} já migrado (R2). Pulando...")
        return
        
    audio_local = meta.get("audio_path") or pipeline_state.get("narration_en", {}).get("local_path")
    json_local = meta.get("transcript_path") or pipeline_state.get("transcript_en", {}).get("local_path")
    
    if not audio_local or not json_local:
        with print_lock:
            processed_count += 1
            skipped_count += 1
            print(f"[{processed_count}/{total_records}] ⚠️ Registro {rec_id} sem caminhos locais em metadados. Pulando...")
        return
        
    # Garante que os caminhos locais são absolutos
    audio_local = os.path.abspath(audio_local)
    json_local = os.path.abspath(json_local)
    
    if not os.path.exists(audio_local):
        with print_lock:
            processed_count += 1
            error_count += 1
            print(f"[{processed_count}/{total_records}] ❌ WAV local não encontrado: {audio_local}. Pulando...")
        return
        
    if not os.path.exists(json_local):
        with print_lock:
            processed_count += 1
            error_count += 1
            print(f"[{processed_count}/{total_records}] ❌ JSON local não encontrado: {json_local}. Pulando...")
        return
        
    # Determina os slugs
    book_slug = slugify_hyphen(book_name)
    chapter_slug = slugify_hyphen(title)
    
    with print_lock:
        print(f"[{processed_count+1}/{total_records}] 🔄 Processando: {book_slug}/{chapter_slug} (ID: {rec_id})...")
        
    temp_mp3 = os.path.join(temp_dir, f"migrate_{rec_id}.mp3")
    
    conn = None
    try:
        # 1. Converte WAV para MP3 (128 kbps) usando FFmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", audio_local,
            "-vn",
            "-ab", "128k",
            "-ar", "44100",
            temp_mp3
        ]
        # Executa FFmpeg silenciosamente
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 2. Upload do MP3 para R2
        mp3_key = f"audiobooks/{book_slug}/{chapter_slug}.mp3"
        mp3_url = upload_file_to_r2(temp_mp3, mp3_key)
        
        # 3. Upload do JSON de Transcrição para R2
        json_key = f"audiobooks/{book_slug}/{chapter_slug}.json"
        json_url = upload_file_to_r2(json_local, json_key)
        
        # 4. Atualiza metadados e pipeline_state
        meta["audio_path"] = mp3_url
        meta["transcript_path"] = json_url
        
        now_str = datetime.now().isoformat()
        if "narration_en" not in pipeline_state:
            pipeline_state["narration_en"] = {}
        if "transcript_en" not in pipeline_state:
            pipeline_state["transcript_en"] = {}
            
        pipeline_state["narration_en"].update({
            "status": "done",
            "r2_url": mp3_url,
            "local_path": None,
            "updated_at": now_str
        })
        pipeline_state["transcript_en"].update({
            "status": "done",
            "r2_url": json_url,
            "local_path": None,
            "updated_at": now_str
        })
        
        # Abre conexão dedicada para a thread
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE {TBL_CONTENT}
            SET metadata = %s,
                pipeline_state = %s::jsonb,
                __last_modified_time = NOW()
            WHERE __id = %s
        """, (json.dumps(meta, ensure_ascii=False), json.dumps(pipeline_state, ensure_ascii=False), rec_id))
        conn.commit()
        
        # 5. Remove os arquivos locais para liberar espaço
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        if os.path.exists(audio_local):
            os.remove(audio_local)
        if os.path.exists(json_local):
            os.remove(json_local)
            
        # Se a pasta contendo os arquivos estiver vazia, remove a pasta
        parent_dir = os.path.dirname(audio_local)
        if os.path.exists(parent_dir) and not os.listdir(parent_dir):
            try:
                os.rmdir(parent_dir)
            except Exception:
                pass
            
        with print_lock:
            processed_count += 1
            migrated_count += 1
            print(f"  ✅ Concluído {rec_id}! ({processed_count}/{total_records})")
            
    except Exception as e:
        if conn:
            conn.rollback()
        with print_lock:
            processed_count += 1
            error_count += 1
            print(f"  ❌ Erro ao processar registro {rec_id}: {e}")
        # Garante limpeza do MP3 temporário se houver erro
        if os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except Exception:
                pass
    finally:
        if conn:
            conn.close()

def main():
    print("🚀 [MIGRAÇÃO PARALELA] Iniciando migração em lote de Audiobooks para R2...")
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Seleciona devocionais concluídos
    cur.execute(f"""
        SELECT 
            mc.__id, 
            mc.title, 
            mc.book_name, 
            mc.metadata, 
            mc.pipeline_state, 
            ci."Name" as book_index_name
        FROM {TBL_CONTENT} mc
        LEFT JOIN {TBL_INDEX} ci ON (ci.__id = mc.index_id OR ci.__auto_number::text = mc.index_id)
        WHERE mc.status = 'concluido'
          AND (
              mc.index_id IN ('recsxt0CLYAIgh8zlwz', 'rec_book_spurgeon_fc', 'recwKRJwpFIToJIu0IU')
              OR ci."Name" ILIKE '%all%grace%'
              OR ci."Name" ILIKE '%faith%checkbook%'
              OR ci."Name" ILIKE '%morning%evening%'
          )
        ORDER BY mc.__id ASC
    """)
    records = cur.fetchall()
    total_records = len(records)
    conn.close()
    
    print(f"📦 Encontrados {total_records} registros concluídos elegíveis para migração.")
    
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp"))
    os.makedirs(temp_dir, exist_ok=True)
    
    # Executa a migração em paralelo com 8 threads
    max_workers = 8
    print(f"🧵 Iniciando ThreadPoolExecutor com {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for row in records:
            executor.submit(migrate_single_record, row, records.index(row) + 1, total_records, temp_dir)
            
    print("\n🏁 [MIGRAÇÃO PARALELA] Processo concluído!")
    print(f"  - Migrados com sucesso: {migrated_count}")
    print(f"  - Pulados (já no R2 ou sem local): {skipped_count}")
    print(f"  - Erros: {error_count}")

if __name__ == "__main__":
    main()
