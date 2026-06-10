import os
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(r"C:\Users\Monegatto\Desktop\EternalL\_factorio\.env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")
# Pelo DOC_MINERACAO_INDUSTRIAL.md a tabela content_index tem ID 1479
TABLE_ID = "1479" 

def inserir_no_baserow(title: str, author: str, source_url: str) -> bool:
    """
    Insere uma nova linha na tabela content_index com os dados extraídos.
    Status inicial é "discovered", para revisão humana ou do Líder.
    """
    if not BASEROW_TOKEN:
        print("[Baserow] Erro: Token não encontrado no .env")
        return False
        
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_ID}/?user_field_names=true"
    headers = {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json"
    }
    # Os nomes das colunas dependem do Baserow do usuário. Assumimos os nomes lógicos do mapa:
    data = {
        "title": title,
        "author": author,
        "source_url": source_url,
        "status": "discovered"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        print(f"[Baserow] ✅ Inserido com sucesso: '{title}' por {author}")
        return True
    except Exception as e:
        print(f"[Baserow] ❌ Erro ao cadastrar '{title}': {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalhes: {e.response.text}")
        return False
