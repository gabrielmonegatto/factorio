# AgentMemory Operations — EternalL Factory VPS

## Overview

AgentMemory runs on VPS 187.127.44.153, port 3120 (container `factorio_agent_memory`).
Auth is Bearer token, stored in the container's environment at `/proc/1/environ`.

## Secret Extraction

**Do NOT hardcode the secret** — Hermes redacts `***` values in terminal output,
breaking shell commands. Always extract dynamically:

```bash
# From the VPS host:
docker exec factorio_agent_memory sh -c 'cat /proc/1/environ | tr "\\000" "\\n" | grep AGENTMEMORY_SECRET | cut -d= -f2'
```

## Pattern: SCP+Python (Clean, Recommended)

Write a Python script locally, SCP to VPS, execute via SSH. The secret stays
in Python scope — no shell quoting issues.

```bash
# 1. Write script
cat > /tmp/save_am.py << 'ENDSCRIPT'
import requests, subprocess
result = subprocess.run(
    ["docker", "exec", "factorio_agent_memory", "sh", "-c",
     "cat /proc/1/environ | tr '\\\\000' '\\\\n' | grep AGENTMEMORY_SECRET | cut -d= -f2"],
    capture_output=True, text=True)
secret = result.stdout.strip()
resp = requests.post("http://localhost:3120/agentmemory/remember",
    headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
    json={"content": "YOUR SNAPSHOT HERE", "type": "state", "tags": ["fabrica:snapshot"]})
print(f"Status: {resp.status_code}")
ENDSCRIPT

# 2. SCP
scp -i ~/.ssh/id_ed25519_factorio /tmp/save_am.py root@187.127.44.153:/tmp/

# 3. Execute + cleanup
ssh -i ~/.ssh/id_ed25519_factorio root@187.127.44.153 'python3 /tmp/save_am.py && rm /tmp/save_am.py'
```

## Pattern: paramiko SFTP (Alternative)

The `scripts/populate-memory.py` uses this approach — write a shell script to
a temp file via SFTP, then execute it with `client.exec_command()`. Avoids
inline `***` but more complex code.

## API Endpoints (AgentMemory)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/agentmemory/remember` | POST | Create a memory | Bearer |
| `/agentmemory/memories` | GET | List all memories | Bearer |
| `/agentmemory/search` | POST | Search memories | Bearer |
| `/agentmemory/health` | GET | Health check | Bearer (optional) |
| `/agentmemory/observe` | POST | Observation (requires hookType, sessionId, project, cwd, timestamp) | Bearer |

## Memory Tags

| Tag | Purpose |
|-----|---------|
| `fabrica:snapshot` | Periodic factory state snapshots |
| `fabrica:estado` | Current factory state (latest) |
| `fabrica:alerta` | Bottlenecks, failures, alerts |
| `fabrica:decisao` | Architecture decisions |
| `fabrica:aprendizado` | Lessons learned |

## Known Issues

- **`***` redaction**: Hermes replaces secret values with `***` in tool output.
  This breaks shell commands that contain the literal secret. Always extract
  dynamically (Docker env) or use the SCP+Python pattern.
- **Memory viewer auth**: `memory-viewer.markeologia.com.br` returns 403 (auth).
  The viewer may have separate credentials not yet configured.
- **MCP mode may fail**: The AgentMemory MCP server can return
  "Session terminated" errors. Gateway mode works fine without MCP — use
  direct REST API calls instead of the MCP protocol.