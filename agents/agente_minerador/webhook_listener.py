from fastapi import FastAPI, Request
import uvicorn
import requests
import os
from dotenv import load_dotenv

# Em desenvolvimento local, carrega o .env se existir.
# No Docker, as variáveis de ambiente já vêm injetadas pelo docker-compose (env_file).
load_dotenv()

BASEROW_URL = os.getenv("BASEROW_URL", "http://baserow")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")
TABLE_OPERATIONS_ID = int(os.getenv("BASEROW_TABLE_OPERATIONS", "623"))

app = FastAPI(
    title="Fábrica EternalL — API de Triggers",
    description=(
        "Porta de entrada da Fábrica Determinística. "
        "Recebe webhooks do Baserow e despacha tarefas para OPERATIONS sem gastar tokens."
    ),
    version="1.0.0"
)

def get_headers():
    if not BASEROW_TOKEN:
        raise ValueError("BASEROW_TOKEN não configurado no ambiente.")
    return {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json",
        "Host": "factorio.io"
    }

def criar_tarefa_operations(titulo: str, area: str = "Mineração") -> bool:
    """
    Insere uma nova tarefa na tabela central OPERATIONS com status Backlog.
    100% determinístico — sem IA, sem tokens.
    """
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_OPERATIONS_ID}/?user_field_names=true"
    payload = {
        "title": titulo,
        "status": "Backlog",
        "area": area
    }
    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ [OPERATIONS] Tarefa criada: {titulo}")
        return True
    except Exception as e:
        print(f"❌ [OPERATIONS] Erro ao criar tarefa: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Detalhes: {e.response.text}")
        return False

# ─────────────────────────────────────────────
# ROTAS — Mineração
# ─────────────────────────────────────────────

@app.post(
    "/webhook/fonts-index",
    summary="Trigger: Nova Fonte para Mineração",
    tags=["Mineração"]
)
async def webhook_fonts_index(request: Request):
    """
    Recebe o webhook do Baserow quando uma linha em `fonts_index` é criada ou atualizada.

    **Regra de negócio:**
    - Se o status da fonte for `Minerar` → cria uma Task em OPERATIONS com status **Backlog**.
    - Somente quando o OPERATIONS mover a task para `Em Execução` o Agente Minerador será acionado.
    """
    try:
        payload = await request.json()
        evento = payload.get("event_type", "desconhecido")
        import json
        print(f"DEBUG PAYLOAD: {json.dumps(payload)}")
        print(f"🔔 [fonts-index] Evento recebido: {evento}")

        # O Baserow envia os dados da linha dentro de 'items'
        for row in payload.get("items", []):
            # O campo agora se chama pipeline_status
            status_raw = row.get("pipeline_status", {})
            status_value = (
                status_raw.get("value", "") if isinstance(status_raw, dict) else str(status_raw)
            )

            if status_value.lower() == "minerar!":
                nome_fonte = row.get("Name", row.get("name", f"Fonte #{row.get('id', '?')}"))
                print(f"🎯 Fonte marcada para mineração: {nome_fonte}")
                criar_tarefa_operations(f"Mapear Fonte: {nome_fonte}", area="Mineração")

        return {"status": "ok", "evento": evento}

    except Exception as e:
        print(f"❌ [fonts-index] Erro interno: {e}")
        return {"status": "erro", "detalhe": str(e)}


# ─────────────────────────────────────────────
# ROTAS — Operações (Esteira)
# ─────────────────────────────────────────────

@app.post(
    "/webhook/operations",
    summary="Trigger: Task Iniciada",
    tags=["Operações"]
)
async def webhook_operations(request: Request):
    """
    Recebe o webhook da tabela OPERATIONS (taskflows) quando algo muda.
    Se Status == 'Iniciar!' e Area == 'Mineração', acorda o Agente Minerador Líder.
    """
    try:
        payload = await request.json()
        evento = payload.get("event_type", "desconhecido")
        
        for row in payload.get("items", []):
            status_raw = row.get("status", {})
            status_value = status_raw.get("value", "") if isinstance(status_raw, dict) else str(status_raw)
            
            area_raw = row.get("area", {})
            area_value = area_raw.get("value", "") if isinstance(area_raw, dict) else str(area_raw)
            
            title = row.get("title", f"Task #{row.get('id')}")

            if status_value == "Iniciar!" and area_value == "Mineração":
                print(f"🚀 [WORKER ACIONADO] Agente Minerador Líder acordado para a missão: {title}")
                # Aqui no futuro chamaremos a API do LangGraph/Prefect
                
        return {"status": "ok", "evento": evento}
    except Exception as e:
        print(f"❌ [operations] Erro interno: {e}")
        return {"status": "erro", "detalhe": str(e)}


# ─────────────────────────────────────────────
# ROTAS — Sistema
# ─────────────────────────────────────────────

@app.get("/", summary="Health Check", tags=["Sistema"])
def health_check():
    """Verifica se a API está online."""
    return {"status": "online", "sistema": "Fábrica EternalL — API de Triggers", "versao": "1.0.0"}


if __name__ == "__main__":
    print("🚀 Iniciando API de Triggers da Fábrica EternalL...")
    uvicorn.run("webhook_listener:app", host="0.0.0.0", port=8001, reload=True)
