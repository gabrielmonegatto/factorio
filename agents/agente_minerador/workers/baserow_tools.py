import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Carrega as variáveis do ambiente central
load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")
TABLE_MINERATION_ID = 1475

def get_headers() -> Dict[str, str]:
    if not BASEROW_TOKEN:
        raise ValueError("BASEROW_TOKEN não encontrado no ambiente.")
    return {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json"
    }

def buscar_fila_mineracao() -> List[Dict[str, Any]]:
    """
    Busca na tabela de Mineração (ID 1475) os itens que estão pendentes de processamento.
    Retorna uma lista de dicionários contendo os dados de cada linha.
    Use esta ferramenta para descobrir o que precisa ser minerado, limpo ou processado.
    
    Retorna:
        List[Dict[str, Any]]: Lista de itens com os campos 'id', 'title', 'status', 'raw_content', etc.
    """
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_MINERATION_ID}/?user_field_names=true&size=10"
    
    # Busca itens que estejam com status 'pending' (ajuste conforme o filtro real do Baserow)
    # Por padrão, vamos buscar as primeiras 10 linhas. 
    # Em produção, adicionaríamos: &filter__field_XXXX__equal=pending
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        
        # Filtra localmente itens com status nulo ou 'pending' caso a API não filtre
        pendentes = []
        for row in results:
            status = row.get("status", "")
            if not status or "pending" in str(status).lower():
                pendentes.append(row)
                
        # Se não achar 'pending', retorna os primeiros só para visualização do Agente
        return pendentes if pendentes else results
        
    except Exception as e:
        return [{"error": f"Falha ao buscar fila de mineração: {str(e)}"}]


def atualizar_status_mineracao(row_id: int, novo_status: str, content: Optional[str] = None, metadata: Optional[str] = None) -> Dict[str, Any]:
    """
    Atualiza uma linha específica na tabela de Mineração no Baserow após o Agente concluir o trabalho.
    
    Argumentos:
        row_id (int): O ID da linha no Baserow (ex: 45).
        novo_status (str): O novo status (ex: 'completed', 'failed', 'reviewing').
        content (Optional[str]): O texto limpo e processado (se aplicável).
        metadata (Optional[str]): Metadados adicionais extraídos em formato JSON (se aplicável).
        
    Retorna:
        Dict[str, Any]: A resposta da API indicando sucesso ou o erro encontrado.
    """
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_MINERATION_ID}/{row_id}/?user_field_names=true"
    
    payload = {
        "status": novo_status
    }
    if content is not None:
        payload["content"] = content
    if metadata is not None:
        payload["metadata"] = metadata
        
    try:
        response = requests.patch(url, headers=get_headers(), json=payload, timeout=10)
        response.raise_for_status()
        return {"success": True, "message": f"Linha {row_id} atualizada com sucesso para '{novo_status}'."}
    except Exception as e:
        return {"success": False, "error": f"Erro ao atualizar a linha {row_id}: {str(e)}"}
