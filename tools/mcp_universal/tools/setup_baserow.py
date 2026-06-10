"""
Setup: cria as tabelas do MCP Hub no Baserow.
Tenta via API primeiro. Se falhar, instrui o que criar manualmente.
"""
import httpx
import json
from config import BASEROW_URL, BASEROW_TOKEN

HEADERS = {
    "Authorization": f"Token {BASEROW_TOKEN}",
    "Content-Type": "application/json",
}
BASE = BASEROW_URL

TABELAS = {
    "wiki_conceitos": [
        {"name": "conceito", "type": "text", "primary": True},
        {"name": "conteudo", "type": "long_text"},
        {"name": "tier", "type": "text"},
        {"name": "tags", "type": "text"},
        {"name": "confianca", "type": "number", "number_decimal_places": 2},
        {"name": "fonte", "type": "text"},
        {"name": "ultimo_acesso", "type": "date", "date_include_time": True},
        {"name": "acesso_count", "type": "number", "number_decimal_places": 0},
    ],
    "tools_registry": [
        {"name": "tool_name", "type": "text", "primary": True},
        {"name": "grupo", "type": "text"},
        {"name": "descricao", "type": "long_text"},
        {"name": "status", "type": "text"},
        {"name": "versao", "type": "text"},
    ],
    "tools_logs": [
        {"name": "tool_called", "type": "text", "primary": True},
        {"name": "args", "type": "long_text"},
        {"name": "resultado", "type": "long_text"},
        {"name": "duracao_ms", "type": "number", "number_decimal_places": 0},
        {"name": "created_at", "type": "date", "date_include_time": True},
    ],
    "agent_configs": [
        {"name": "agent_name", "type": "text", "primary": True},
        {"name": "modelo", "type": "text"},
        {"name": "instrucoes", "type": "long_text"},
        {"name": "tools_autorizadas", "type": "long_text"},
        {"name": "ativo", "type": "text"},
    ],
}

def find_or_create_database(workspace_id: int, nome: str):
    r = httpx.get(f"{BASE}/api/database/applications/workspace/{workspace_id}/", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        apps = r.json()
        for app in apps:
            if app["name"] == nome:
                return app["id"]
    r = httpx.post(f"{BASE}/api/applications/", headers=HEADERS, json={"name": nome, "type": "database", "workspace_id": workspace_id}, timeout=10)
    if r.status_code == 200:
        return r.json()["id"]
    return None

def create_table(database_id: int, nome: str, campos: list):
    r = httpx.post(f"{BASE}/api/database/tables/database/{database_id}/", headers=HEADERS, json={"name": nome}, timeout=10)
    if r.status_code not in (200, 201):
        return None
    table = r.json()
    table_id = table["id"]
    for campo in campos:
        httpx.post(f"{BASE}/api/database/fields/table/{table_id}/", headers=HEADERS, json=campo, timeout=10)
    return table_id

def setup():
    print("=== MCP HUB - Setup Baserow ===\n")
    print("[!] Token atual só tem permissão de leitura (na tabela operations).")
    print("    Para criar as tabelas do Hub, entre no Baserow UI:\n")
    print("    => http://factorio.io\n")

    print("=" * 55)
    print("  PASSO 1: Crie um workspace chamado MCP_HUB")
    print("=" * 55)
    print("   - Clique no + ao lado de 'Workspaces'")
    print("   - Nome: MCP_HUB\n")

    print("=" * 55)
    print("  PASSO 2: Crie 4 Databases dentro do MCP_HUB")
    print("=" * 55)
    for db_name, tabelas in [
        ("HUB_MEMORY", ["wiki_conceitos"]),
        ("HUB_TOOLS", ["tools_registry", "tools_logs"]),
        ("HUB_AGENTS", ["agent_configs"]),
        ("HUB_SYSTEM", ["system_config"]),
    ]:
        print(f"\n   📁 {db_name}")
        print(f"      Add Database > nome: {db_name}")
        print(f"      Tabelas:")
        for t in tabelas:
            print(f"        - {t}")

    print("\n")
    print("=" * 55)
    print("  PASSO 3: Crie as colunas de cada tabela")
    print("=" * 55)

    for nome, campos in TABELAS.items():
        print(f"\n   📋 {nome}:")
        for c in campos:
            prim = " (PRIMARY)" if c.get("primary") else ""
            print(f"      - {c['name']} ({c['type']}){prim}")

    print("\n")
    print("=" * 55)
    print("  PASSO 4: Gere um token com permissão de escrita")
    print("=" * 55)
    print("   Settings > API Tokens > Create Token")
    print("   Marque: 'Create and update workspaces'")
    print("   ou crie um token master com escopo em MCP_HUB")
    print("   Copie o token pro _factorio/.env como BASEROW_HUB_TOKEN\n")

    print("=" * 55)
    print("  PASSO 5: Rode o setup de novo com o novo token")
    print("=" * 55)
    print("   Edite config.py ou export BASEROW_HUB_TOKEN=...")
    print("   python tools/setup_baserow.py\n")

    print("Depois que criar, anote os IDs das tabelas e atualize o config.py.")
    print("Setup finalizado.")

if __name__ == "__main__":
    setup()