import httpx
from config import BASEROW_URL, BASEROW_HUB_TOKEN

BASE = f"{BASEROW_URL}/api/database/rows/table"

def _headers():
    return {
        "Authorization": f"Token {BASEROW_HUB_TOKEN}",
        "Content-Type": "application/json",
    }

def register_tools(mcp):

    @mcp.tool()
    async def baserow_query(tabela_id: int, user_field_names: bool = True, limit: int = 100) -> list:
        async with httpx.AsyncClient() as c:
            params = {"user_field_names": str(user_field_names).lower(), "limit": limit}
            r = await c.get(f"{BASE}/{tabela_id}/", headers=_headers(), params=params, timeout=15)
            r.raise_for_status()
            return r.json().get("results", [])

    @mcp.tool()
    async def baserow_insert(tabela_id: int, dados: dict) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE}/{tabela_id}/?user_field_names=true", headers=_headers(), json=dados, timeout=15)
            r.raise_for_status()
            return r.json()

    @mcp.tool()
    async def baserow_update(tabela_id: int, linha_id: int, dados: dict) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.patch(f"{BASE}/{tabela_id}/{linha_id}/?user_field_names=true", headers=_headers(), json=dados, timeout=15)
            r.raise_for_status()
            return r.json()

    @mcp.tool()
    async def baserow_delete(tabela_id: int, linha_id: int) -> str:
        async with httpx.AsyncClient() as c:
            r = await c.delete(f"{BASE}/{tabela_id}/{linha_id}/", headers=_headers(), timeout=15)
            r.raise_for_status()
            return f"Linha {linha_id} deletada com sucesso."

    return mcp
