#!/usr/bin/env python3
"""DB Health Check — Quick connectivity test for all 3 factory databases.
Usage: python3 db-connect.py
Requires: SSH key at ~/.ssh/id_ed25519_factorio
"""
import paramiko, os, sys

HOST = "187.127.44.153"
USER = "root"
PORT = 22
key_path = os.path.join(os.path.expanduser("~"), ".ssh", "id_ed25519_factorio")

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    rc = stdout.channel.recv_exit_status()
    return out, err, rc

def psql(client, container, user, db, query):
    return run(client, f"docker exec {container} psql -U {user} -d {db} -c \"{query}\" 2>/dev/null")

def check(client, name, container, user, db):
    print(f"\n── {name} ──")
    out, err, rc = psql(client, container, user, db,
        "SELECT count(*) AS tables FROM information_schema.tables WHERE table_schema='public'")
    if rc == 0:
        print(f"  Tables: {out[out.find('(')+1:out.find(' row')] if '(1 row)' in out else out.strip()}")
    else:
        print(f"  FAIL: {err[:200]}")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, key_filename=key_path, timeout=15)
except Exception as e:
    print(f"SSH failed: {e}")
    print("Install SSH key first: run setup_ssh_key.py")
    sys.exit(1)

print(f"Connected to {HOST}")
check(client, "TEABLE", "factorio_teable_db", "teable", "teable")
check(client, "POSTGRES GERAL", "factorio_postgres", "postgres", "eternall")
check(client, "OUTLINE", "outline_db", "outline", "outline")
client.close()
print("\nDone.")