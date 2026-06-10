import requests
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://localhost:8000")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN", "u5kC5qV6FhK1xO7pQ4yR3i9wA8tE0oB2")

headers = {"Authorization": f"Token {BASEROW_TOKEN}"}

TABLES = {
    "taskflows (Operations)": 623,
    "intel_channels_videos (Intelligence)": 631,
    "mineration_content (Mineration)": 1475,
}

print("=" * 50)
print("📊 BACKLOG REPORT — Agente Minerador")
print("=" * 50)

for name, table_id in TABLES.items():
    try:
        url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/?user_field_names=true&size=1"
        print(f"DEBUG: Consultando {name} em {url}")
        r = requests.get(url, headers=headers, timeout=10)
        print(f"DEBUG: Status {r.status_code}")
        r.raise_for_status()
        count = r.json().get("count", "?")
        print(f"\n📋 {name}: {count} registros totais")
    except Exception as e:
        print(f"\n❌ {name}: Erro — {e}")

# Contar por status no taskflows — busca todos e conta localmente
print("\n--- Status do taskflows ---")
try:
    all_rows = []
    page = 1
    while True:
        url = f"{BASEROW_URL}/api/database/rows/table/623/?user_field_names=true&size=200&page={page}"
        print(f"DEBUG: Paginação taskflows {page}")
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        all_rows.extend(data.get("results", []))
        if not data.get("next"):
            break
        page += 1

    status_counts = Counter()
    for row in all_rows:
        status = row.get("status", {})
        label = status.get("value", "Sem status") if isinstance(status, dict) else "Sem status"
        status_counts[label] += 1

    for status in ["Backlog", "In Progress", "Blocked", "Failed", "Done"]:
        print(f"  {status}: {status_counts.get(status, 0)}")

    print(f"\n  Próximas prioridades (Alta):")
    altas = [r for r in all_rows if
             isinstance(r.get("priority"), dict) and r["priority"].get("value") == "Alta" and
             isinstance(r.get("status"), dict) and r["status"].get("value") == "Backlog"]
    for t in altas[:5]:
        print(f"  → [{t['id']}] {t.get('title', '(sem título)')}")

except Exception as e:
    print(f"  Erro ao contar status: {e}")

print("\n" + "=" * 50)
