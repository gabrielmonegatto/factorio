# 🖥️ INFRAESTRUTURA — VPS, CONTAINERS, DOMÍNIOS
> Tudo sobre a VPS de produção

---

## Servidor

| Item | Valor |
|---|---|
| IP | 187.127.44.153 |
| SSH | root, via chave (~/.ssh/id_ed25519_factorio) |
| OS | Debian 13 (trixie) |
| Docker | Compose + 14 containers |

---

## Containers

| Nome | Função | Porta |
|---|---|---|
| `factorio_agents` | Hermes Gateway + Webhook | 8001 |
| `factorio_proxy` | Caddy (reverse proxy) | 80/443 |
| `factorio_teable` | Teable (interface web) | 3000 |
| `factorio_teable_db` | Postgres do Teable | 42345 |
| `factorio_teable_cache` | Redis do Teable | — |
| `factorio_agent_memory` | AgentMemory API | 3120/3122 |
| `factorio_redis` | Redis (geral) | 6379 |
| `factorio_mcp_universal` | MCP Server | 3111 |
| `outline_holding` | Wiki Holding | 5000 |
| `outline_br4nds` | Wiki Br4nds | 5001 |
| `outline_db` | Postgres do Outline | 54322 |
| `outline_redis` | Redis do Outline | — |
| `outline_minio` | S3 do Outline | 9000/9001 |
| `outline_minio_setup` | Setup do MinIO | — |

---

## Domínios (Caddy)

| Domínio | Destino | Status |
|---|---|---|
| db.markeologia.com.br | → Teable | ✅ 307 → /space |
| admin.markeologia.com.br | → Outline Holding | ✅ 200 |
| admin.br4nds.com.br | → Outline Br4nds | ✅ 200 |
| agents.markeologia.com.br | → Hermes Agents | ✅ 200 |
| minio.markeologia.com.br | → MinIO Console | ✅ 200 |
| mcp.markeologia.com.br | → MCP Universal | ⚠️ 404 (API) |
| memory.markeologia.com.br | → AgentMemory | ⚠️ 404 (API) |
| memory-viewer.markeologia.com.br | → Memory Viewer | ⚠️ 403 (auth) |
| s3.markeologia.com.br | → MinIO S3 | ⚠️ 403 (auth) |

---

## Acessos a Banco de Dados

| Banco | Container | Porta | Conexão |
|---|---|---|---|
| Teable DB | `factorio_teable_db` | 42345 | `docker exec` psql -U teable -d teable |
| Outline DB | `outline_db` | 54322 | `docker exec` psql -U outline -d outline |
| Postgres Geral (5432) | **DESTRUÍDO** | — | Não recriar — dados migrados pro Teable |

---

## Gateway Hermes

| Item | Valor |
|---|---|
| Versão | v0.18.0 |
| Profile | `diretor-vps` (cron-only) |
| Entrypoint | `/entrypoint.sh` (inicia gateway + uvicorn) |
| Discord | Desconectado (modo cron) |
| Trigger.dev | proj_dsuhcyzyqgruytusyipj |