import time
from config import BASEROW_URL

START_TIME = time.time()

def register_tools(mcp):

    @mcp.tool()
    async def system_health() -> dict:
        uptime = time.time() - START_TIME
        return {
            "status": "online",
            "servico": "MCP Universal",
            "versao": "0.1.0",
            "uptime_segundos": round(uptime),
            "workspace_hub": "MCP_HUB (ID 160)",
            "tabelas": {
                "wiki_conceitos": 1522,
                "tools_registry": 1523,
                "tools_logs": 1524,
                "agent_configs": 1525,
                "system_config": 1526,
            },
            "tools_count": 16,
            "baserow_conectado": True,
        }

    @mcp.tool()
    async def system_config() -> dict:
        from ..config import BASEROW_URL
        return {
            "baserow_url": BASEROW_URL,
            "hub_porta": 3111,
            "transportes": ["stdio", "sse"],
            "tools_grupos": ["baserow.*", "llm.*", "memory.*", "system.*"],
        }

    @mcp.tool()
    async def system_listar_tools() -> list:
        return [
            "baserow_query", "baserow_insert", "baserow_update", "baserow_delete",
            "llm_call", "llm_chat_json", "llm_chat_structured",
            "memory_save", "memory_search", "memory_update", "memory_promover", "memory_consolidar", "memory_status",
            "system_health", "system_config", "system_listar_tools",
        ]

    return mcp
