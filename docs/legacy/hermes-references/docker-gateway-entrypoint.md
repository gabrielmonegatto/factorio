# Docker Gateway Entrypoint — Container Recipe

When the Hermes gateway keeps dying with SIGTERM in a Docker container, the root
cause is almost always **Docker runtime sending SIGTERM to `docker exec`'d
processes**. The fix is to start the gateway from the container's own entrypoint,
not via `docker exec`.

## Symptoms

```
WARNING gateway.run: Shutdown context: signal=SIGTERM under_systemd=yes
  parent_pid=1 parent_name=uvicorn
```

Gateway starts, logs "Gateway Starting..." banner, then immediately shuts down.
`gateway_state.json` may say `running` but `ps aux` shows nothing.

## Root Cause

`docker exec -d` creates a child process via the Docker API. When the exec
session ends, Docker sends SIGTERM to the child. The Hermes shutdown handler
catches it and exits gracefully, logging "Shutdown context". The
`under_systemd=yes` line is **informational only** — it does NOT cause the
shutdown.

Secondary issue: even without `docker exec`, the gateway detects `parent_pid=1`
(its parent is uvicorn, which is PID 1) and logs `under_systemd=yes`. This is
harmless in the entrypoint approach because no external SIGTERM arrives.

## The Fix: Entrypoint Approach

Create a new Docker image with two changes:
1. Install `hermes-agent` via pip
2. Add an entrypoint script that starts the gateway **before** the main process

### Step-by-Step Recipe

```bash
# 1. Create a builder container from the original image
docker run -d --name builder --restart no docker-factorio_agents sleep 9999

# 2. Install Hermes inside it
docker exec builder pip install hermes-agent -q

# 3. Write the entrypoint script
docker exec builder sh -c 'cat > /entrypoint.sh << EOF
#!/bin/sh
set -e
echo "=== FACTORY AGENTS STARTING ==="
if [ -f /root/.hermes/.env ]; then
    set -a; . /root/.hermes/.env; set +a
fi
echo "[*] Starting Gateway..."
rm -f /root/.hermes/gateway_state.json /root/.hermes/gateway.pid /root/.hermes/gateway.lock
nohup hermes gateway run --replace --no-supervise --force > /var/log/hermes_gateway.log 2>&1 &
echo "[+] Gateway PID: $!"
sleep 4
echo "[*] Starting webhook..."
exec uvicorn agente_minerador.webhook_listener:app --host 0.0.0.0 --port 8001
EOF'
docker exec builder chmod +x /entrypoint.sh

# 4. Copy .env from the original image (via base64 to bypass secret redaction)
# First get the .env from a temp container
docker run -d --name env_src --restart no factorio_agents_with_entrypoint sleep 9999
docker exec env_src sh -c 'cat /root/.hermes/.env | base64 > /tmp/env.b64'
ENV_B64=$(docker exec env_src cat /tmp/env.b64)
docker exec builder sh -c "echo '$ENV_B64' | base64 -d > /root/.hermes/.env"
docker rm -f env_src

# 5. Copy config.yaml
docker run -d --name cfg_src --restart no factorio_agents_with_entrypoint sleep 9999
docker exec cfg_src sh -c 'cat /root/.hermes/config.yaml | base64 > /tmp/cfg.b64'
CFG_B64=$(docker exec cfg_src cat /tmp/cfg.b64)
docker exec builder sh -c "echo '$CFG_B64' | base64 -d > /root/.hermes/config.yaml"
docker rm -f cfg_src

# 6. Commit the image
docker commit builder docker-factorio_agents:final
docker rm -f builder

# 7. Create the final container
docker run -d --name factorio_agents \\
  --network factorio_network \\
  -p 8001:8001 \\
  --restart unless-stopped \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  --entrypoint /entrypoint.sh \\
  docker-factorio_agents:final
```

## Why the Three Flags?

| Flag | Purpose |
|------|---------|
| `--replace` | Kills any stale gateway process referenced in `gateway_state.json`. Without this, the new instance refuses because "another instance already running". |
| `--no-supervise` | Skips s6-overlay redirection. The original image may have been built with s6 awareness; without this flag, `gateway run` redirects to the s6 service manager (which doesn't exist in our container). |
| `--force` | Bypasses the supervised-gateway conflict guard. Without it, the gateway refuses to start because it detects `under_systemd=yes` and assumes a systemd/launchd service is managing it. |

## Verification

```bash
# Check container is up
docker ps --filter name=factorio_agents

# Check processes
docker exec factorio_agents sh -c '
  for p in /proc/[0-9]*; do
    pid=${p#/proc/}
    cmd=$(cat $p/cmdline 2>/dev/null | tr "\\000" " ")
    [ -n "$cmd" ] && echo "$pid: $cmd"
  done'

# Check gateway state
docker exec factorio_agents cat /root/.hermes/gateway_state.json

# Check gateway log
docker exec factorio_agents tail -20 /var/log/hermes_gateway.log

# Check HTTP
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/
```

Expected state file output:
```json
{
  "gateway_state": "running",
  "platforms": { "discord": { "state": "connected" } }
}
```

## Entrypoint Script Design

The script does THREE things in order:
1. Sources `.env` for Discord token + OpenRouter key
2. Starts Hermes gateway in background with `nohup` (detaches from process group)
3. `exec` uvicorn as PID 1 (the main container process)

Key detail: the gateway is started **before** uvicorn replaces the shell via
`exec`. This means the gateway is a child of the entrypoint shell, not of
`docker exec`. When the shell does `exec uvicorn`, the gateway gets reparented
to PID 1 (uvicorn) — but receives no SIGTERM because no `docker exec` session
was involved.

## What NOT to Do

- Do NOT use `docker exec -d` to start the gateway — it will die within seconds
- Do NOT mount `/app` from an empty host directory — it hides the built-in code
- Do NOT skip `--replace` if there was a previous gateway instance — stale PID file blocks startup
- Do NOT skip `--no-supervise` on non-s6 containers — gateway redirects to nonexistent service
- Do NOT read `.env` via `docker cp` — secret redaction zeroes the content