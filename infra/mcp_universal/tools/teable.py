import httpx
from os import getenv

# Read Teable configuration with fallback to local docker container route
TEABLE_URL = getenv("TEABLE_URL", "http://factorio_teable:3000").rstrip("/")
TEABLE_TOKEN = getenv("TEABLE_TOKEN", "")

def _headers():
    return {
        "Authorization": f"Bearer {TEABLE_TOKEN}",
        "Content-Type": "application/json",
    }

def register_tools(mcp):

    @mcp.tool()
    async def teable_query(table_id: str, limit: int = 100) -> list:
        """
        Consulta registros de uma tabela no Teable.
        Retorna uma lista de objetos contendo os IDs e campos de cada linha.
        """
        url = f"{TEABLE_URL}/api/table/{table_id}/record"
        params = {"take": limit}
        
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=_headers(), params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            return [{"id": rec["id"], "fields": rec["fields"]} for rec in data.get("records", [])]

    @mcp.tool()
    async def teable_insert(table_id: str, fields: dict) -> dict:
        """
        Insere uma nova linha/registro em uma tabela do Teable.
        Recebe os dados como um dicionário de campos {campo: valor}.
        """
        url = f"{TEABLE_URL}/api/table/{table_id}/record"
        payload = {"records": [{"fields": fields}]}
        
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=_headers(), json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            return records[0] if records else {}

    @mcp.tool()
    async def teable_update(table_id: str, record_id: str, fields: dict) -> dict:
        """
        Atualiza uma linha/registro existente no Teable usando o ID do registro.
        """
        url = f"{TEABLE_URL}/api/table/{table_id}/record"
        payload = {"records": [{"id": record_id, "fields": fields}]}
        
        async with httpx.AsyncClient() as client:
            r = await client.patch(url, headers=_headers(), json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            return records[0] if records else {}

    @mcp.tool()
    async def teable_delete(table_id: str, record_ids: list) -> str:
        """
        Deleta um ou mais registros de uma tabela do Teable passando uma lista de IDs de registros.
        """
        url = f"{TEABLE_URL}/api/table/{table_id}/record"
        # Convert IDs list to multiple ids[] query params
        params = [("ids", rid) for rid in record_ids]
        
        async with httpx.AsyncClient() as client:
            r = await client.delete(url, headers=_headers(), params=params, timeout=20)
            r.raise_for_status()
            return f"Registros {record_ids} deletados com sucesso do Teable."

    return mcp
