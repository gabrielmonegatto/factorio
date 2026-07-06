#!/usr/bin/env python3
"""Auto-cure: unstucks stuck + retries failed tasks.
Fixes both public.mananciall_sermon_pipeline AND old Teable tasks."""
import os, sys, psycopg2 as pg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
except ImportError:
    pass

import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
if "***" in DB_URL:
    DB_URL = DB_URL.replace("***", "teable_secret_password")

conn = pg.connect(DB_URL)
cur = conn.cursor()

total_cured = 0

# === NEW PIPELINE (public.mananciall_sermon_pipeline) ===
# 1. Stuck narration
cur.execute("""
    UPDATE public.mananciall_sermon_pipeline
    SET narration_status = 'pending', updated_at = NOW()
    WHERE narration_status = 'processing' AND updated_at < NOW() - INTERVAL '20 minutes'
""")
total_cured += cur.rowcount
print(f"  Narration stuck: {cur.rowcount}")

# 2. Stuck audio
cur.execute("""
    UPDATE public.mananciall_sermon_pipeline
    SET audio_status = 'pending', updated_at = NOW()
    WHERE audio_status = 'processing' AND updated_at < NOW() - INTERVAL '20 minutes'
""")
total_cured += cur.rowcount
print(f"  Audio stuck: {cur.rowcount}")

# 3. Failed -> retry
for field in ['narration_status', 'ai_cleaning_status']:
    cur.execute(f"""
        UPDATE public.mananciall_sermon_pipeline
        SET {field} = 'pending', updated_at = NOW()
        WHERE {field} = 'failed'
    """)
    total_cured += cur.rowcount
    print(f"  {field} failed->retry: {cur.rowcount}")

# === OLD TEABLE PIPELINE ===
# 4. Stuck tasks (>20min in 'Em Processamento')
cur.execute("""
    UPDATE "bseWeczeNfCSaMlu2EC"."tblVzN1Eo8tfk7GX2CJ"
    SET "Status" = 'Pendente', "Logs" = COALESCE("Logs",'') || E'\\n[AUTO-CURE ' || NOW()::text || '] Resetado de Em Processamento para Pendente (preso >20min).\\n',
        __last_modified_time = NOW()
    WHERE "Status" = 'Em Processamento'
      AND __last_modified_time < NOW() - INTERVAL '20 minutes'
""")
total_cured += cur.rowcount
print(f"  Teable stuck: {cur.rowcount}")

# 5. Error tasks -> retry (narrate-audio, transcribe-audio, translate-content)
for task_type in ['narrate-audio', 'transcribe-audio', 'translate-content']:
    cur.execute("""
        UPDATE "bseWeczeNfCSaMlu2EC"."tblVzN1Eo8tfk7GX2CJ"
        SET "Status" = 'Pendente', 
            "Logs" = COALESCE("Logs",'') || E'\\n[AUTO-RETRY ' || NOW()::text || '] Resetado de Erro para Pendente.\\n',
            __last_modified_time = NOW()
        WHERE "Task" = %s AND "Status" = 'Erro'
    """, (task_type,))
    total_cured += cur.rowcount
    print(f"  Teable {task_type} errors->retry: {cur.rowcount}")

conn.commit()
cur.close()
conn.close()
print(f"\n✅ Total cured: {total_cured}")