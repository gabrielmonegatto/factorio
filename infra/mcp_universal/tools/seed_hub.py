import requests, json

TOKEN = 'r8vI3txj6ATdmnDLTJ5V20wgsOfBIAPx'
H = {'Authorization': f'Token {TOKEN}', 'Content-Type': 'application/json'}
BASE = 'http://factorio.io'

tools = [
    ('baserow_query', 'baserow', 'Consulta linhas de uma tabela Baserow'),
    ('baserow_insert', 'baserow', 'Insere linha em tabela Baserow'),
    ('baserow_update', 'baserow', 'Atualiza linha em tabela Baserow'),
    ('baserow_delete', 'baserow', 'Deleta linha de tabela Baserow'),
    ('llm_call', 'llm', 'Chama LLM via OpenRouter com prompt'),
    ('llm_chat_json', 'llm', 'Chama LLM e retorna JSON estruturado'),
    ('llm_chat_structured', 'llm', 'Chama LLM com schema JSON definido'),
    ('memory_save', 'memory', 'Salva conceito na memoria 4-tiers'),
    ('memory_search', 'memory', 'Busca conceitos na memoria'),
    ('memory_update', 'memory', 'Atualiza conceito existente'),
    ('memory_promover', 'memory', 'Promove memoria entre tiers'),
    ('memory_consolidar', 'memory', 'Consolida memorias de um tier'),
    ('memory_status', 'memory', 'Status da memoria (qtd por tier)'),
    ('system_health', 'system', 'Health check do servidor MCP'),
    ('system_config', 'system', 'Configuracoes do servidor MCP'),
    ('system_listar_tools', 'system', 'Lista todas as tools disponiveis'),
]

print('=== REGISTRANDO TOOLS ===')
for name, grupo, desc in tools:
    payload = {'tool_name': name, 'grupo': grupo, 'descricao': desc, 'status': 'active', 'versao': '1.0.0'}
    r = requests.post(f'{BASE}/api/database/rows/table/1523/?user_field_names=true', headers=H, json=payload, timeout=10)
    if r.status_code in (200, 201):
        print(f'  + {name}')
    else:
        print(f'  ! {name}: {r.status_code} - {r.text[:80]}')

print()
print('=== REGISTRANDO SYSTEM CONFIG ===')
configs = [
    ('hub_name', 'MCP Universal', 'Nome do hub central de ferramentas'),
    ('hub_versao', '0.1.0', 'Versao atual do MCP Universal'),
    ('hub_porta', '3111', 'Porta do servidor MCP'),
    ('workspace_hub', 'MCP_HUB', 'Workspace do Baserow dedicado ao Hub'),
    ('workspace_id', '160', 'ID do workspace MCP_HUB no Baserow'),
    ('db_memory', 'HUB_MEMORY', 'Database de memoria 4-tiers'),
    ('db_tools', 'HUB_TOOLS', 'Database de registro de tools'),
    ('db_agents', 'HUB_AGENTS', 'Database de configuracao de agentes'),
    ('db_system', 'HUB_SYSTEM', 'Database de configuracao do sistema'),
]
for chave, valor, desc in configs:
    payload = {'chave': chave, 'valor': valor, 'descricao': desc}
    r = requests.post(f'{BASE}/api/database/rows/table/1526/?user_field_names=true', headers=H, json=payload, timeout=10)
    if r.status_code in (200, 201):
        print(f'  + {chave} = {valor}')
    else:
        print(f'  ! {chave}: {r.status_code}')

print('\nHub configurado e populado com sucesso!')