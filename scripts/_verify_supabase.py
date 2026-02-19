import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")

if not DB_URL:
    print("Erro: SUPABASE_DB_URL não definido no .env")
    exit(1)

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT to_regclass('mananciall.journey_production');")
    exists = cur.fetchone()[0]
    
    if exists:
        print("✅ Tabela mananciall.journey_production encontrada!")
        
        # Count rows
        cur.execute("SELECT count(*) FROM mananciall.journey_production;")
        count = cur.fetchone()[0]
        print(f"📊 Total de registros: {count}")
        
    else:
        print("❌ Tabela mananciall.journey_production NÃO encontrada.")
        
    cur.close()
    conn.close()

except Exception as e:
    print(f"Erro ao conectar: {e}")
