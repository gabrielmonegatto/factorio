# Teable REST API Scout

How to inventory a running Teable instance via its REST API.

## Prerequisites

- Teable running at `http://localhost:3000` (Docker container)
- An access token (Bearer auth)

## Finding the Token

Look in existing Python scripts under `scratch/`:
```bash
grep -r "TEABLE_TOKEN\|teable_acc" scratch/ 2>/dev/null
```

The token looks like: `teable_accTyjWZd49HtTkEi4R_.../T+vZFGorQ=`

## Key Endpoints (all under `http://localhost:3000/api/`)

| Endpoint | Returns |
|----------|---------|
| `GET /api/space` | All spaces |
| `GET /api/space/{id}/base` | Bases in a space |
| `GET /api/base/{id}/table` | Tables in a base |
| `GET /api/table/{id}/field` | Fields/columns in a table |
| `GET /api/table/{id}/record?take=N` | First N records + `total` count |

## Token Storage (crucial — Hermes redacts credentials)

Hermes **redacts** credential-like strings from terminal output. Never pass tokens inline in terminal commands. Store in a JSON file:

```json
// scratch/.teable_token.json
{"token": "teable_accTyj..."}
```

Then read it from Python:
```python
import os, json, requests
with open(os.path.join(os.path.dirname(__file__), ".teable_token.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
```

## Full Scout Script

See `scratch/teable_rest_scout.py` in the EternalL project — it enumerates all spaces, bases, tables, fields, and record counts.

## Sample Output Structure

```
Space: EternalL
├── Base: Eternall (35 tabelas)
│   ├── tasks          ← SSOT da fábrica (columns: Task ID, Brand, Project_Slug, area, Status, Projeto, Progresso, task)
│   ├── content_index  ← Catálogo de projetos
│   ├── content_chunks ← Chunks de conteúdo
│   ├── knowledge      ← Base de conhecimento dos agentes
│   └── ... 30+ more
├── Base: Monegatto (financeiro pessoal)
└── Base: Br4nds (inteligência de marcas)
Space: Eternall
└── Base: Base (vazia)
```
