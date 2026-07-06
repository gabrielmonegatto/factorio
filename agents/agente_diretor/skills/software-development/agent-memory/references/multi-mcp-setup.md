# Multi-MCP Setup: AgentMemory + OpenRouter

The Diretor profile runs **two MCP servers simultaneously** for full Factory capability:

```yaml
mcp_servers:
  agentmemory:
    url: http://<HOST>:3120/agentmemory/mcp
    headers:
      Authorization: "Bearer ***    timeout: 180
    connect_timeout: 30
  openrouter:
    url: https://mcp.openrouter.ai/mcp
    headers:
      Authorization: "Bearer ***    timeout: 180
    connect_timeout: 30
```

## Why Both

| Server | Tools | Purpose |
|--------|-------|---------|
| **agentmemory** | 53 MCP tools | Shared brain — memory_save, memory_recall, memory_smart_search, memory_patterns |
| **openrouter** | 13 MCP tools | Model hub — chat-send, models-list, credits-get, benchmarks, rankings-daily |

## Tool Naming Convention

Hermes prefixes each tool by server name:

- `mcp_agentmemory_memory_recall`
- `mcp_agentmemory_memory_save`
- `mcp_openrouter_chat_send`
- `mcp_openrouter_models_list`

## Trade-offs

- **2 servers = 2 connections** at startup. Each adds ~1-2s to Hermes boot.
- Both servers persist for the agent's lifetime. Connection drops auto-retry (5 attempts, exponential backoff, max 60s).
- OpenRouter MCP has a **$10 weekly spend cap** by default — extend via the OAuth approval screen. The key expires every 7 days (re-auth needed periodically).