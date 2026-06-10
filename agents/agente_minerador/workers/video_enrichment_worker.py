"""
VideoEnrichmentWorker — POSTGRES EDITION (v3.0)
Atribui nomes de canais a 36k+ vídeos usando o mapa DEFINITIVO do Postgres.
"""
import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

import functools
print = functools.partial(print, flush=True)

load_dotenv("c:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

HOST = "http://factorio.io"
EMAIL = os.getenv("BASEROW_EMAIL", "gabriel.monegatto@gmail.com")
PASSWORD = os.getenv("BASEROW_PASSWORD", "123mudar")
TABLE_VIDEOS = 631
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "postgres_uuid_map.json")

def get_headers():
    r = requests.post(f"{HOST}/api/user/token-auth/", json={"username": EMAIL, "password": PASSWORD})
    return {"Authorization": f"JWT {r.json()['token']}"}

def run_enrichment():
    headers = get_headers()
    print("🚀 Iniciando Enriquecimento de Vídeos (Postgres Edition)...")

    # 1. Carregar Mapa do Postgres
    print(f"🔍 Carregando mapa de {MAPPING_FILE}...")
    with open(MAPPING_FILE, 'r') as f:
        uuid_map = json.load(f)
    print(f"✅ Mapa carregado com {len(uuid_map)} canais.")

    # 2. Processar Vídeos em Lote
    page = 1
    total_updated = 0
    
    while True:
        print(f"📦 Lendo página {page}...")
        # Lotes de 200 (limite do Baserow por página)
        url = f"{HOST}/api/database/rows/table/{TABLE_VIDEOS}/?user_field_names=true&size=200&page={page}"
        r = requests.get(url, headers=headers)
        
        if r.status_code != 200:
            print(f"❌ Erro ao buscar vídeos: {r.text}")
            break
            
        data = r.json()
        rows = data.get('results', [])
        if not rows:
            print("🏁 Fim dos registros.")
            break

        batch_updates = []
        for row in rows:
            # Pular se já tem nome
            if row.get('channel_name'): continue
            
            uuid = row.get('channel_id')
            if uuid in uuid_map:
                batch_updates.append({
                    "id": row['id'],
                    "channel_name": uuid_map[uuid]
                })

        if batch_updates:
            # Refresh token
            headers = get_headers()
            update_url = f"{HOST}/api/database/rows/table/{TABLE_VIDEOS}/batch/?user_field_names=true"
            up_r = requests.patch(update_url, headers=headers, json={"items": batch_updates})
            if up_r.status_code in [200, 204]:
                total_updated += len(batch_updates)
                print(f"   ✅ {len(batch_updates)} vídeos enriquecidos. (Total: {total_updated})")
            else:
                print(f"   ❌ Erro no lote: {up_r.text}")

        page += 1
        # Delay mínimo para alta performance
        time.sleep(0.1)

    print(f"🏆 Missão cumprida! {total_updated} vídeos foram identificados.")

if __name__ == "__main__":
    run_enrichment()
