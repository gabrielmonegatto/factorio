# Domain Map — EternalL Factory Services

All services are behind Caddy reverse proxy (`factorio_proxy`, ports 80/443).
Some domains proxy through Cloudflare, some point directly to the VPS IP.

## Service Domains

| Domain | Backend Service | Container | Status | Notes |
|--------|----------------|-----------|--------|-------|
| `db.markeologia.com.br` | Teable UI | `factorio_teable:3000` | 307→/space | Login page loads |
| `admin.markeologia.com.br` | Outline Holding | `outline_holding:3000` | 200 OK | **unhealthy** healthcheck |
| `admin.br4nds.com.br` | Outline Br4nds | `outline_br4nds:3000` | 200 OK | **unhealthy** healthcheck |
| `agents.markeologia.com.br` | Hermes Webhook | `factorio_agents:8001` | 200 OK | Returns `{"status":"online"}` |
| `mcp.markeologia.com.br` | MCP Universal | `factorio_mcp_universal:3111` | 404 | API endpoint, no web UI |
| `memory.markeologia.com.br` | AgentMemory API | `factorio_agent_memory:3111` | 404 | Requires auth header |
| `memory-viewer.markeologia.com.br` | Memory Viewer | `factorio_agent_memory:3113` | 403 | Requires auth |
| `minio.markeologia.com.br` | MinIO Console | `outline_minio:9001` | 200 OK | |
| `s3.markeologia.com.br` | MinIO S3 API | `outline_minio:9000` | 403 | Requires auth header |

## Caddyfile (inside `factorio_proxy`)

```
db.markeologia.com.br     reverse_proxy factorio_teable:3000
admin.markeologia.com.br  reverse_proxy outline_holding:3000
admin.br4nds.com.br       reverse_proxy outline_br4nds:3000
mcp.markeologia.com.br    reverse_proxy factorio_mcp_universal:3111
agents.markeologia.com.br reverse_proxy factorio_agents:8001
memory.markeologia.com.br reverse_proxy factorio_agent_memory:3111
memory-viewer.markeologia.com.br reverse_proxy factorio_agent_memory:3113
minio.markeologia.com.br  reverse_proxy outline_minio:9001
s3.markeologia.com.br     reverse_proxy outline_minio:9000
```

## DNS Notes

- `.markeologia.com.br` subdomains → Cloudflare (104.21.61.168 / 172.67.212.45)
- `admin.br4nds.com.br` → Cloudflare (104.21.67.69)
- Direct IP (187.127.44.153) → mostly for internal/dev access

## Health Status

- ✅ **Green**: db, agents, minio, mcp (expected 404)
- ⚠️ **Yellow**: memory, memory-viewer, s3 (expected 403/404 — auth required)
- 🔴 **Unhealthy**: outline_holding, outline_br4nds (healthcheck failing)
  - Container IS up and serving HTTP 200
  - Health endpoint likely missing or misconfigured
  - Fix: add `/health` endpoint or adjust healthcheck in docker-compose