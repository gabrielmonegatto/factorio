# VPS Health Check — Diagnostic Checklist

Full diagnostic procedure to run when checking VPS health. Can be run manually (SSH in sequence) or via `scripts/vps-health-check.py` (automated).

## Quick Inventory

| Check | Command | What to look for |
|-------|---------|------------------|
| **Containers** | `docker ps` | All 12+ containers UP. Current: agents, proxy, teable+db+cache, agent_memory, redis, postgres, mcp_universal, outline_app(holding+br4nds), outline_db, outline_redis, outline_minio |
| **Gateway State** | `cat /root/.hermes/gateway_state.json` | `running`, Discord `connected` |
| **Gateway Process** | `ps aux \| grep hermes \| grep -v grep` | **Must match** gateway_state PID |
| **Disk** | `df -h /` | < 80% used |
| **Memory** | `free -h` | < 80% used |
| **Uptime** | `uptime` | Load < 2.0 |
| **Cron Jobs** | `hermes cron list` or check `cronjob list` | Pulse + Checkpoint active |

## Step-by-Step Manual Procedure

```bash
# 1. List containers
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# 2. Gateway state file
docker exec factorio_agents cat /root/.hermes/gateway_state.json

# 3. Cross-check: is the gateway process actually alive?
docker exec factorio_agents ps aux | grep hermes | grep -v grep

# 4. Check if gateway responds via Discord (via logs)
docker exec factorio_agents tail -20 /var/log/hermes_gateway.log

# 5. Disk
df -h /

# 6. Memory
free -h

# 7. Uptime + load
uptime
```

## Critical Diagnostics

### Gateway State vs Real Process (the most common trap)

`gateway_state.json` can report `"gateway_state": "running"` even when the OS
process has died. Always cross-check with `ps aux | grep hermes`.

**If state says running but ps shows nothing:**
1. The gateway wrote the state file then crashed (common on restart cycles)
2. Restart: `docker exec factorio_agents hermes gateway run --replace`

### Gateway Log Patterns

| Log pattern | Meaning | Action |
|-------------|---------|--------|
| `Another gateway instance is already running (PID X)` | Gateway detected itself on re-run | `--replace` flag |
| `✗ Gateway instance is already running` | Normal idempotency guard | Already running — OK |
| `Gateway shutting down` | SIGTERM received | Check what sent it |
| `Platform discord: disconnected` | Discord connection lost | May auto-reconnect |

## SSH from Windows

SSH key auth is required (see main SKILL.md SSH section). After setup:

```python
import paramiko, os
key_path = os.path.join(os.path.expanduser("~"), ".ssh", "id_ed25519_factorio")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=key_path, timeout=15)
```

**Never** ask for password interactively or use `sshpass`.

## What to Check After Restart

1. **Containers**: all 9 UP
2. **Gateway**: state file says `running`, PID in state matches `ps aux`
3. **Discord**: platform state says `connected`
4. **Cron**: pulse and checkpoint jobs listed in `cronjob list`
5. **Logs**: tail of gateway log shows no errors
6. **Disk/Mem**: within healthy ranges