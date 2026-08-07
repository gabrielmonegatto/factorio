#!/usr/bin/env python3
"""
populate-memory.py — Bulk-populate AgentMemory with factory knowledge.
Usage: python3 populate-memory.py
Requires: SSH key ~/.ssh/id_ed25519_factorio, AgentMemory on port 3120
"""

import paramiko, json, os, time

HOST = "187.127.44.153"
USER = "root"
PORT = 22
KEY_PATH = os.path.expanduser("~/.ssh/id_ed25519_factorio")

MEMORIES = [
    ("INFRA: Dominios", "infra", "DOMINIOS: db.markeologia.com.br (Teable), admin.markeologia.com.br (Outline Holding), admin.br4nds.com.br (Outline Br4nds), agents.markeologia.com.br (Hermes), minio.markeologia.com.br (MinIO). Caddy no factorio_proxy."),
    ("INFRA: Containers", "infra", "14 containers: factorio_agents, proxy, teable+db+cache, agent_memory, redis, mcp_universal, outline_holding, outline_br4nds, outline_db, outline_redis, outline_minio+setup."),
    ("DB: Teable", "db", "TEABLE: docker exec factorio_teable_db psql -U teable -d teable (42345). Schema bseWeczeNfCSaMlu2EC (58 tab). TASKS: tblVzN1Eo8tfk7GX2CJ (425)."),
    ("DB: Outline", "db", "OUTLINE: docker exec outline_db psql -U outline -d outline (54322). 45 tab. admin.markeologia.com.br e admin.br4nds.com.br."),
    ("TASKS: Status", "tasks", "425 tasks: 365 pendentes, 36 concluido, 24 processando. GARGALO: yt_en_treasures_spurgeon (301). Pipeline parado pelo CEO."),
    ("TASKS: Tabelas", "tasks", "TABELAS: tbl9cM460hpuqi2jbqv (69k verses), tblz2WQnbhh06TEa7Ro (36k YT), tblVzN1Eo8tfk7GX2CJ (425 tasks). AgentJournal: tblAgentJournal001 (5)."),
    ("TRIGGER: Deploy", "trigger", "TRIGGER proj_dsuhcyzyqgruytusyipj deploy 20260706.1. 10 tasks. Pipeline PARADO (CEO). TRIGGER_SECRET_KEY no .env."),
    ("GATEWAY: Hermes", "gateway", "HERMES v0.18.0. Entrypoint --no-supervise --force. Profile diretor-vps cron-only. SSH key instalada."),
    ("OBS: Journal", "observations", "5 registros AgentJournal. Ultimo: 425 tasks, gargalo yt_en_treasures_spurgeon. Pipeline parado pra replanejamento."),
    ("INFRA: Acessos", "infra", "AgentMemory auth Bearer. Teable db.markeologia.com.br. SSH key. MCP no IDE."),
]

def run(client, cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    return out, stdout.channel.recv_exit_status()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH, timeout=15)
    print(f"Populating {len(MEMORIES)} memories...\n")

    for i, (label, mtype, content) in enumerate(MEMORIES):
        payload = json.dumps({"content": content, "agent": "fabrica", "type": mtype})
        cmd = f"curl -s -X POST -H 'Authorization: Bearer *** -H 'Content-Type: application/json' -d '{payload}' 'http://localhost:3120/agentmemory/remember'"
        sftp = client.open_sftp()
        with sftp.file(f"/tmp/pm_{i}.sh", "w") as f: f.write(f"#!/bin/sh\n{cmd}\n")
        sftp.close()
        out, rc = run(client, f"sh /tmp/pm_{i}.sh")
        status = "OK" if rc == 0 else f"RC={rc}"
        print(f"  [{i+1}/{len(MEMORIES)}] {status} — {mtype}: {label}")
        time.sleep(0.3)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check.sh", "w") as f:
        f.write(f"#!/bin/sh\ncurl -s -H 'Authorization: Bearer *** 'http://localhost:3120/agentmemory/memories?limit=20'\n")
    sftp.close()
    out, rc = run(client, "sh /tmp/check.sh")
    print(f"\nDone. Verify output:\n{out[:300]}")
    client.close()

if __name__ == "__main__":
    main()