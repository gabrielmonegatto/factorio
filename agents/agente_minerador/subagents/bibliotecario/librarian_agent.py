import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

SQUAD_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(SQUAD_DIR))

from agents import Agent, function_tool
from workers.baserow_insert import inserir_no_baserow

env_path = Path(r"C:\Users\Monegatto\Desktop\EternalL\_factorio\.env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")
TABLE_ID = "1479"

def checar_duplicidade_baserow(url_ou_titulo: str) -> bool:
    """
    Verifica se uma obra (pela URL ou Titulo) já existe no Baserow.
    Retorna True se JÁ EXISTE (duplicada), False se é NOVA.
    """
    if not BASEROW_TOKEN:
        print("[Baserow Bibliotecario] Token não encontrado!")
        return False
        
    # Busca simples no baserow (usando search que pesquisa em todos os campos textuais)
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_ID}/?user_field_names=true&search={url_ou_titulo}"
    headers = {
        "Authorization": f"Token {BASEROW_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("count", 0) > 0:
            return True
        return False
    except Exception as e:
        print(f"[Baserow Bibliotecario] Erro ao checar duplicidade: {e}")
        return False

def registrar_obra_nova(titulo: str, autor: str, url: str) -> str:
    """
    Usa esta ferramenta APENAS para registrar uma obra que comprovadamente NÃO é duplicada.
    """
    sucesso = inserir_no_baserow(titulo, autor, url)
    if sucesso:
        return f"OK: '{titulo}' registrado no banco de dados."
    return "Falha ao registrar no banco de dados."

bibliotecario_agent = Agent(
    name="Subagente_Bibliotecario",
    instructions=(
        "Você é o Bibliotecário da fábrica, responsável por garantir a integridade do banco de dados (Baserow).\n"
        "Sua missão é receber uma lista de obras mapeadas (em JSON ou texto) e validar item por item.\n\n"
        "COMO OPERAR:\n"
        "1. Para CADA item da lista recebida, use a ferramenta `checar_duplicidade_baserow` passando a URL (preferencial) ou o Título.\n"
        "2. Se a ferramenta retornar True, a obra já existe e deve ser IGNORADA.\n"
        "3. Se a ferramenta retornar False, a obra é NOVA e deve ser salva usando a ferramenta `registrar_obra_nova`.\n"
        "4. Ao final de todas as checagens, retorne um relatório final informando quantas obras repetidas foram ignoradas e quantas novas foram salvas."
    ),
    model="deepseek/deepseek-v4-flash",
    tools=[
        function_tool(checar_duplicidade_baserow),
        function_tool(registrar_obra_nova)
    ]
)
