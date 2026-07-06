# VPS Architecture — EternalL Factory (187.127.44.153)

## Connection

**SSH:**
```bash
ssh -i ~/.ssh/id_eternall root@187.127.44.153
```

**Alternative (password):** `root` / `.gmIN&QAY8Q'L9vS`

Latency: ~962ms (Hostinger Brazil). Commands take a few seconds but work reliably.

## 9 Containers — Full Reference

| Container | Image | Port(s) | Purpose |
|-----------|-------|---------|---------|
| `factorio_proxy` | Caddy | 80/443 | Reverse proxy, SSL |
| `factorio_teable` | Teable | **3000** | Interface do banco/planilhas |
| `factorio_teable_db` | Postgres | **42345** | Banco do Teable |
| `factorio_agent_memory` | AgentMemory v0.9.27 | **3120** (API), **3122** (Viewer) | Memória persistente dos agentes |
| `factorio_teable_cache` | Redis | 6379 | Cache do Teable |
| `factorio_redis` | Redis | 6379 | Fila central |
| `factorio_postgres` | Postgres (PgVector) | **5432** | Banco geral + vetores |
| `factorio_agents` | Python 3.11 (custom) | **8001** | Webhook listener (FastAPI) |
| `factorio_mcp_universal` | MCP Server | **3111** | Hub MCP |

## Connection Strings

```env
# AgentMemory REST API
AGENTMEMORY_URL=http://187.127.44.153:3120
AGENTMEMORY_SECRET=factorio_secret

# AgentMemory MCP (Hermes config.yaml)
url: http://187.127.44.153:3120/agentmemory/mcp
headers:
  Authorization: Bearer factorio_secret

# Teable Postgres (DB)
postgresql://teable:teable_secret_password@187.127.44.153:42345/teable

# Postgres Geral (PgVector)
postgresql://postgres:postgres@187.127.44.153:5432/eternall

# Teable Web UI
http://187.127.44.153:3000

# AgentMemory Viewer
http://187.127.44.153:3122
```

## MCP Servers (both enabled together in Hermes config.yaml)

```yaml
mcp_servers:
  agentmemory:
    url: http://187.127.44.153:3120/agentmemory/mcp
    headers:
      Authorization: Bearer factorio_secret
    timeout: 180
    connect_timeout: 30
  openrouter:
    url: https://mcp.openrouter.ai/mcp
    headers:
      Authorization: Bearer sk-or-...
    timeout: 180
    connect_timeout: 30
```

Total: 53 (AgentMemory) + 13 (OpenRouter) = 66 MCP tools available.

## Updating config.yaml via SSH

```bash
ssh -i ~/.ssh/id_eternall root@187.127.44.153 "cat > /root/.hermes/profiles/diretor/config.yaml << 'EOF'
# content here
EOF"
```

The `factorio_agents` container runs a Python FastAPI (uvicorn) — it does NOT have Hermes installed. To add the Diretor 24/7 on Discord, install Hermes in this container or create a separate one.

## Dockerfile (factorio_agents)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "agente_minerador.webhook_listener:app", "--host", "0.0.0.0", "--port", "8001"]
```

Requirements: fastapi, uvicorn, requests, python-dotenv, openai-agents, litellm, langgraph, langchain, google-antigravity.

## Discord Gateway (target config)

When the Diretor is deployed on the VPS as a Hermes gateway, the target config:

```yaml
# Profile: diretor-vps
gateway:
  discord:
    enabled: true
    bot_token: "MTQ5Nj..."
    allowed_guilds: ["1481006974068854786"]
  channels:
    diretor: "#📢 diretor"    # Reports, discoveries, alerts
    geral: "#💬 geral"         # User chat & responses
    alertas: "#🔔 alertas"     # Bottlenecks, errors
    kpis: "#📊 kpis"          # Metrics
```

## Key Files on VPS

| Path | Content |
|------|---------|
| `/root/factorio/docker-compose.yml` | Docker Compose config |
| `/app/_factorio/agents/` | Agent source code (mounted volume) |
| `/factory/` | Factory data volume |

## Verification

```bash
# Check all containers
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Test AgentMemory
curl -s -H 'Authorization: Bearer factorio_secret' http://187.127.44.153:3120/agentmemory/health

# Check hermes MCP servers (from within session)
hermes mcp list
```