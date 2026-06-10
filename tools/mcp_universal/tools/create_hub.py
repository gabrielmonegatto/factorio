import httpx, json

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc5Mzg5NjYwLCJpYXQiOjE3NzkzODkwNjAsImp0aSI6ImRiZGUzODJkNmZhMTQ5MDhhMDVmMmJkZWU5NGY1NDY5IiwidXNlcl9pZCI6IjEifQ.ebX8YfsAYcH3V6ER7i885_bS1h2vK_PHhwlEnfUGrvQ'
H = {'Authorization': f'JWT {TOKEN}', 'Content-Type': 'application/json'}
BASE = 'http://factorio.io'
WS_ID = 160

DBS = {
    'HUB_MEMORY': {
        'wiki_conceitos': [
            {'name': 'conceito', 'type': 'text', 'primary': True},
            {'name': 'conteudo', 'type': 'long_text'},
            {'name': 'tier', 'type': 'text'},
            {'name': 'tags', 'type': 'text'},
            {'name': 'confianca', 'type': 'number', 'number_decimal_places': 2},
            {'name': 'fonte', 'type': 'text'},
            {'name': 'ultimo_acesso', 'type': 'date', 'date_include_time': True},
            {'name': 'acesso_count', 'type': 'number', 'number_decimal_places': 0},
        ]
    },
    'HUB_TOOLS': {
        'tools_registry': [
            {'name': 'tool_name', 'type': 'text', 'primary': True},
            {'name': 'grupo', 'type': 'text'},
            {'name': 'descricao', 'type': 'long_text'},
            {'name': 'status', 'type': 'text'},
            {'name': 'versao', 'type': 'text'},
        ],
        'tools_logs': [
            {'name': 'tool_called', 'type': 'text'},
            {'name': 'args', 'type': 'long_text'},
            {'name': 'resultado', 'type': 'long_text'},
            {'name': 'duracao_ms', 'type': 'number', 'number_decimal_places': 0},
            {'name': 'created_at', 'type': 'date', 'date_include_time': True},
        ],
    },
    'HUB_AGENTS': {
        'agent_configs': [
            {'name': 'agent_name', 'type': 'text', 'primary': True},
            {'name': 'modelo', 'type': 'text'},
            {'name': 'instrucoes', 'type': 'long_text'},
            {'name': 'tools_autorizadas', 'type': 'long_text'},
            {'name': 'ativo', 'type': 'text'},
        ],
    },
    'HUB_SYSTEM': {
        'system_config': [
            {'name': 'chave', 'type': 'text', 'primary': True},
            {'name': 'valor', 'type': 'text'},
            {'name': 'descricao', 'type': 'long_text'},
        ],
    },
}

TABLE_IDS = {}

for db_name, tabelas in DBS.items():
    print(f'\n=== CRIANDO DATABASE: {db_name} ===')
    r = httpx.post(f'{BASE}/api/applications/workspace/{WS_ID}/', headers=H, json={'name': db_name, 'type': 'database'}, timeout=10)
    if r.status_code not in (200, 201):
        print(f'  ERRO: {r.status_code} - {r.text[:200]}')
        continue
    db = r.json()
    db_id = db['id']
    print(f'  Database ID: {db_id}')

    for tbl_name, campos in tabelas.items():
        r2 = httpx.post(f'{BASE}/api/database/tables/database/{db_id}/', headers=H, json={'name': tbl_name}, timeout=10)
        if r2.status_code not in (200, 201):
            print(f'  ERRO tabela {tbl_name}: {r2.status_code} - {r2.text[:200]}')
            continue
        tbl = r2.json()
        tbl_id = tbl['id']
        print(f'  Tabela: {tbl_name} (ID: {tbl_id})')
        TABLE_IDS[tbl_name] = tbl_id

        for campo in campos:
            r3 = httpx.post(f'{BASE}/api/database/fields/table/{tbl_id}/', headers=H, json=campo, timeout=10)
            if r3.status_code not in (200, 201):
                print(f'    ERRO campo {campo["name"]}: {r3.status_code}')
            else:
                print(f'    + {campo["name"]} ({campo["type"]})')

print('\n========================================')
print('TABELA IDs:', json.dumps(TABLE_IDS, indent=2))
print('========================================')
