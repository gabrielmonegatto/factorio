---
name: hermes-production-deployment
description: "Deploy Hermes Agent in production: Docker, VPS, gateway (Discord), MCP servers, personality profiles, cron jobs, and 24/7 operation."
version: 1.0.0
author: Diretor de Operações
platforms: [windows, linux]
metadata:
  hermes:
    tags: [hermes, deployment, production, gateway, discord, mcp, docker, vps]
    related_skills: [hermes-agent]
---

# Hermes Production Deployment

How to take Hermes from a local interactive session to a 24/7 production agent running on a VPS with Discord gateway, MCP servers, personality, and cron jobs.

---

## Architecture

```
VPS (Docker)
└── Container (Python 3.11-slim)
    ├── Webhook Listener (FastAPI, port 8001) — receives triggers
    └── Hermes Gateway — Discord bot 24/7
        ├── MCP: AgentMemory (memória compartilhada)
        ├── MCP: OpenRouter (fallback de modelos)
        ├── Cron jobs (pulse matinal, relatórios, checkpoints)
        └── Personality: perfil do agente
```

**Principle:** The container runs TWO services — the existing worker (webhook listener) and the Hermes gateway. The entrypoint starts the webhook in background, then the gateway in foreground (container stays alive as long as gateway runs).

---

## Step-by-Step Setup

### 1. Install Hermes inside the container

Do NOT use the install.sh script inside Docker build — it fails on slim images. Install via pip AFTER the container is running:

```bash
# Inside the container
pip install hermes-agent mcp
```

For Dockerfile, just include in requirements.txt:
```
hermes-agent
mcp>=1.0.0
```

### 2. Create the configuration directory

```bash
mkdir -p /root/.hermes/personalities
```

### 3. Create config.yaml

```yaml
model:
  default: deepseek/deepseek-v4-flash-20260423
  provider: openrouter

agent:
  max_turns: 90
  reasoning_effort: medium
  gateway_timeout: 1800
  task_completion_guidance: true

personality: diretor  # matches filename in personalities/ directory

memory:
  memory_enabled: true
  user_profile_enabled: true

gateway:
  discord:
    enabled: true
    require_mention: true        # bot only responds when @mentioned
    auto_thread: true
    reactions: true
    history_backfill: true
    history_backfill_limit: 50

mcp_servers:
  agentmemory:
    url: http://factorio_agent_memory:3111/mcp    # internal Docker network
    timeout: 180
  openrouter:
    url: https://mcp.openrouter.ai/mcp
    headers:
      Authorization: "Bearer ${OPENROUTER_API_KEY}"  # reads from env var
    timeout: 180

cron:
  jobs:
    pulse-matinal:
      schedule: "0 6 * * *"
      prompt: "Pulse Matinal - cheque estado da fabrica e poste resumo"
      deliver: "discord:GUILD_ID:CHANNEL_NAME"
    relatorio-diario:
      schedule: "0 8 * * *"
      prompt: "Relatorio diario - consulte areas e progresso"
      deliver: "discord:GUILD_ID:CHANNEL_NAME"
    checkpoint-noite:
      schedule: "0 19 * * *"
      prompt: "Checkpoint noturno - resumo do dia"
      deliver: "discord:GUILD_ID:CHANNEL_NAME"
```

### 4. Create personality file

Save as `/root/.hermes/personalities/diretor.md`:

```markdown
# Personality Name

Voce e o [NOME]. Seu proposito e [MISSAO].
Nao se apresente como Hermes Agent generico.

## Personalidade
- [CARACTERISTICAS]
- Chama o usuario de chefe ou irmao
- Executa comandos, nunca pede pro usuario rodar algo

## Contexto da Operacao
- [STACK, REGRAS, CONHECIMENTO BASE]
```

The `personality: nome` field in config.yaml loads this file automatically. The Hermes gateway does NOT support `--personality` CLI flag (removed in v0.18.0).

### 5. Create .env with real credentials

The `.env` file needs REAL tokens, not placeholders. Best approach:

```bash
# Run inside container - reads from container env vars
echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" > /root/.hermes/.env
echo "DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN" >> /root/.hermes/.env
```

**NEVER hardcode tokens in heredoc commands** — the `***` redaction breaks heredoc syntax. Use env var interpolation instead.

### 6. Start the gateway

```bash
cd /root/.hermes
nohup hermes gateway run </dev/null > /var/log/hermes_gateway.log 2>&1 &
echo $! > /root/.hermes/gateway.pid
```

### 7. Restart after config change

```bash
hermes gateway restart
# Or if that fails:
kill $(cat /root/.hermes/gateway.pid) && sleep 2 && hermes gateway run ...
```

### 8. Make it survive container restarts

The container's entrypoint should:
1. Generate `.env` from container env vars
2. Start webhook listener in background
3. Start Hermes gateway in foreground (keeps container alive)

```bash
#!/bin/bash
set -e
cat > /root/.hermes/.env << EOF
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN
EOF

cd /app
uvicorn some_listener:app --host 0.0.0.0 --port 8001 &
sleep 3

cd /root/.hermes
hermes gateway run
```

---

## Common Pitfalls

### 🔴 install.sh fails in Docker build
**Problem:** `curl ... | bash` exits with code 2 on slim images.
**Fix:** Install via `pip install hermes-agent` inside the running container, or after the container is built.

### 🔴 Personality not loaded, agent responds generically
**Problem:** Agent says "I am Hermes Agent, an LLM developed by Nous Research..." instead of its intended persona.
**Fix:** 
1. Create `personalities/<name>.md` file
2. Set `personality: <name>` in config.yaml
3. Restart gateway

### 🔴 MCP servers fail to connect
**Problem:** "Session terminated" or "Connection refused" on MCP servers.
**Fix:** 
- AgentMemory: internal Docker port is 3111 (MCP endpoint), not 3120 (host port)
- OpenRouter: needs `Authorization: Bearer <real-key>` header — verify `.env` has real key, not `***`
- Use Docker internal hostnames (`container_name:internal_port`) not external IPs

### 🔴 `.env` with `***` tokens
**Problem:** Writing tokens via heredoc or echo produces literal `***` because Hermes redacts output.
**Fix:** Use environment variable interpolation: `echo "KEY=$REAL_ENV_VAR" > .env`

### 🔴 SSH key confirmation popup on Windows
**Problem:** Windows opens a GUI dialog for SSH key passphrase, blocking CLI automation.
**Fix:** Run `ssh-add C:\Users\<user>\.ssh\id_rsa` in PowerShell first to cache credentials. Or use password-based SSH auth for non-interactive agents.

### 🔴 `--personality` flag not recognized
**Problem:** `hermes gateway run --personality name` fails with "unrecognized arguments".
**Fix:** The `--personality` CLI flag was removed. Use `personality: name` in config.yaml instead.

### 🔴 Another gateway instance already running
**Problem:** "Another gateway instance is already running (PID X)."
**Fix:** Use `hermes gateway restart` or `hermes gateway run --replace`.

---

## Verification

```bash
# Check gateway is alive
cat /root/.hermes/gateway.pid
ps aux | grep hermes

# Check logs
tail -20 /var/log/hermes_gateway.log
# Look for: discord connected, model loaded, no errors

# Test in Discord
# @mention the bot - it should respond with its personality, not generic intro
```

---

## Environment Requirements

| Env Var | Required | Purpose |
|---------|----------|---------|
| `DISCORD_BOT_TOKEN` | ✅ | Discord bot authentication |
| `OPENROUTER_API_KEY` | ✅ | LLM provider |
| `AGENTMEMORY_SECRET` | ⏹️ | AgentMemory auth (if used) |
| `DISCORD_ALLOWED_USERS` | ⏹️ | Restrict bot usage to specific user IDs |