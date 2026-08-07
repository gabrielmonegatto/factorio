import httpx
from os import getenv

# Read AgentMemory URL and secret key
AGENTMEMORY_URL = getenv("AGENTMEMORY_URL", "http://agent_memory:3111/agentmemory").rstrip("/")
AGENTMEMORY_SECRET = getenv("AGENTMEMORY_SECRET", "factorio_secret")

def _headers():
    return {
        "Authorization": f"Bearer {AGENTMEMORY_SECRET}",
        "Content-Type": "application/json",
    }

def register_tools(mcp):

    @mcp.tool()
    async def memory_save(tier: str, conceito: str, conteudo: str, tags: str = "", confianca: float = 1.0, fonte: str = "") -> str:
        """
        Salva um conceito/fato na memória persistente de 4-tiers do AgentMemory.
        """
        url = f"{AGENTMEMORY_URL}/remember"
        payload = {
            "content": f"[{tier.upper()}] {conceito}: {conteudo}",
            "agent": "antigravity-agent",
            "metadata": {
                "concept": conceito,
                "tier": tier,
                "tags": tags,
                "confidence": str(confianca),
                "source": fonte
            }
        }
        
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=_headers(), json=payload, timeout=15)
            r.raise_for_status()
            return f"Memória '{conceito}' salva com sucesso no AgentMemory (tier: {tier})."

    @mcp.tool()
    async def memory_search(consulta: str, tier: str = "", limite: int = 10) -> list:
        """
        Busca fatos e conceitos salvos na memória persistente do AgentMemory.
        """
        url = f"{AGENTMEMORY_URL}/memories"
        # We fetch latest memories and filter in python if tier is specified
        params = {"limit": 100}
        
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=_headers(), params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            memories = data.get("memories", [])
            
            # Simple text filter
            results = []
            query_lower = consulta.lower()
            for m in memories:
                content = m.get("content", "").lower()
                m_tier = m.get("metadata", {}).get("tier", "").lower()
                
                # Filter by search query
                if query_lower in content:
                    # Optional filter by tier
                    if not tier or tier.lower() == m_tier:
                        results.append({
                            "id": m.get("id"),
                            "content": m.get("content"),
                            "metadata": m.get("metadata", {}),
                            "createdAt": m.get("createdAt")
                        })
            return results[:limite]

    @mcp.tool()
    async def memory_status() -> dict:
        """
        Retorna o status geral e total de memórias cadastradas no AgentMemory da VPS.
        """
        url = f"{AGENTMEMORY_URL}/memories"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=_headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            memories = data.get("memories", [])
            
            tiers_count = {}
            for m in memories:
                tier = m.get("metadata", {}).get("tier", "unknown")
                tiers_count[tier] = tiers_count.get(tier, 0) + 1
                
            return {
                "total_memories": len(memories),
                "by_tier": tiers_count,
                "status": "connected"
            }

    return mcp
