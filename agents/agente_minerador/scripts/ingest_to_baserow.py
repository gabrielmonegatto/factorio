import os
import sys
import json
import requests
import math
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (onde está o BASEROW_API_KEY)
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

BASEROW_API_KEY = os.getenv("BASEROW_API_KEY")
TABLE_ID = "1479" # Tabela Mananciall_Obras
BASE_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"

# Arquivo para controle de idempotência
PROGRESS_FILE = Path(__file__).parent / ".ingest_progress.json"

def get_existing_urls():
    """Faz GET paginado no Baserow e retorna um set com todas as URLs cadastradas."""
    print("🔄 Baixando URLs existentes do Baserow para cache local...")
    existing_urls = set()
    url = f"{BASE_URL}?user_field_names=true&size=200"
    headers = {"Authorization": f"Token {BASEROW_API_KEY}"}
    
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Erro ao buscar dados do Baserow: {resp.text}")
            break
            
        data = resp.json()
        for row in data.get('results', []):
            if 'URL' in row and row['URL']:
                existing_urls.add(row['URL'])
                
        url = data.get('next')
        
    print(f"✅ Cache montado: {len(existing_urls)} URLs existentes no banco.")
    return existing_urls

def batch_insert(items_to_insert):
    """Envia um array de dicts em batch para o Baserow"""
    headers = {
        "Authorization": f"Token {BASEROW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # O Batch Insert do Baserow tem um formato específico
    payload = {
        "items": items_to_insert
    }
    
    resp = requests.post(f"{BASE_URL}batch/", headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"❌ Erro no Batch Insert: {resp.text}")
        return False
    return True

def carregar_progresso():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_index": 0}

def salvar_progresso(index):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"last_index": index}, f)

def main():
    if not BASEROW_API_KEY:
        print("❌ BASEROW_API_KEY não encontrada no arquivo .env!")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Uso: python ingest_to_baserow.py <caminho_do_json_minerado>")
        sys.exit(1)

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"❌ Arquivo não encontrado: {json_path}")
        sys.exit(1)

    # 1. Carregar JSON do Mapeador
    print(f"📂 Lendo arquivo de extração: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        obras_mineradas = json.load(f)

    # 2. Montar Cache Local Anti-Duplicidade
    existing_urls = get_existing_urls()

    # 3. Filtrar Inéditas via set()
    obras_ineditas = []
    for obra in obras_mineradas:
        # Se a URL não existe no banco, adicionamos na fila de insert
        if obra.get('url') not in existing_urls:
            obras_ineditas.append(obra)

    print(f"🔍 Análise de Duplicidade: {len(obras_mineradas)} total -> {len(obras_ineditas)} inéditas.")

    if not obras_ineditas:
        print("✅ Nenhuma obra nova para inserir. O banco já está atualizado.")
        sys.exit(0)

    # 4. Inserir em Batch com Idempotência
    progresso = carregar_progresso()
    start_idx = progresso.get("last_index", 0)
    
    if start_idx >= len(obras_ineditas):
        print("✅ Todas as inéditas já foram inseridas (recuperado do progresso).")
        PROGRESS_FILE.unlink(missing_ok=True) # Limpa o log de progresso
        sys.exit(0)

    batch_size = 50 # Limite conservador para a API
    total_batches = math.ceil(len(obras_ineditas) / batch_size)
    current_batch = math.floor(start_idx / batch_size) + 1

    print(f"🚀 Iniciando inserção em Batch (Retomando do item {start_idx})...")

    # Corta a lista de onde paramos
    obras_para_processar = obras_ineditas[start_idx:]
    
    for i in range(0, len(obras_para_processar), batch_size):
        lote_raw = obras_para_processar[i:i+batch_size]
        
        # Mapeando os campos do JSON para as colunas do Baserow
        lote_baserow = []
        for obj in lote_raw:
            lote_baserow.append({
                "Título Original": obj.get('title', ''),
                "Autor": obj.get('author', ''),
                "URL": obj.get('url', ''),
                "Status": "discovered",
                "Idioma": "EN" # Por padrão as raspadas da BTP são inglês
            })

        print(f"  Enviando Batch {current_batch}/{total_batches} ({len(lote_baserow)} itens)...")
        sucesso = batch_insert(lote_baserow)
        
        if sucesso:
            # Atualiza o índice global
            start_idx += len(lote_raw)
            salvar_progresso(start_idx)
            current_batch += 1
        else:
            print("🛑 Processo interrompido por erro na API. Progresso salvo para retomada.")
            sys.exit(1)

    print("🎉 Ingestão finalizada com sucesso!")
    # Limpa o arquivo de progresso após conclusão
    PROGRESS_FILE.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
