import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Carrega as variáveis de ambiente centrais
load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN")

#IDs das tabelas centrais da Trindade de Dados
TABLE_OPERATIONS_ID = os.getenv("BASEROW_TABLE_OPERATIONS", 623)
TABLE_MINERATION_ID = os.getenv("BASEROW_TABLE_MINERATION", 1475)
TABLE_FACTORIO_ID = os.getenv("BASEROW_TABLE_FACTORIO", 0) # Preencher quando o ID for descoberto

def _get_headers() -> Dict[str, str]:
    if not BASEROW_TOKEN:
        raise ValueError("BASEROW_TOKEN não encontrado no ambiente.")
    return {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json"
    }

def verificar_backlog_operations(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Verifica a tabela central de OPERATIONS (taskflows) em busca de tarefas pendentes ou em progresso 
    que estejam designadas para a categoria 'Mineration'.
    Use esta ferramenta para descobrir qual é o seu próximo trabalho na fábrica.
    
    Argumentos:
        limit (int): Número máximo de tarefas para retornar de uma vez.
        
    Retorna:
        List[Dict[str, Any]]: Lista de tarefas do Baserow.
    """
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_OPERATIONS_ID}/?user_field_names=true&size={limit}"
    
    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        # Filtra por tarefas que não estão prontas e requerem atenção.
        # Ajuste a string exata do status de acordo com o que existe no seu Baserow.
        tarefas_ativas = []
        for row in results:
            status = row.get("status", {})
            if isinstance(status, dict):
                status_value = status.get("value", "Unknown")
            else:
                status_value = str(status)
                
            if status_value.lower() in ["backlog", "in progress", "failed"]:
                tarefas_ativas.append(row)
                
        return tarefas_ativas if tarefas_ativas else [{"mensagem": "A fila de operações está vazia. O Agente pode dormir."}]
        
    except Exception as e:
        return [{"error": f"Falha ao consultar OPERATIONS: {str(e)}"}]


def consultar_procedimento_factorio(task_name: str) -> Dict[str, Any]:
    """
    Consulta o blueprint (manual de instruções) de uma tarefa específica na tabela FACTORIO (taskflows_bank).
    Use esta ferramenta se você encontrou uma tarefa em OPERATIONS e não sabe exatamente quais parâmetros 
    ou scripts deve executar para resolvê-la.
    
    Argumentos:
        task_name (str): O nome da tarefa ou ID do procedimento (ex: 'Extrair Sermões Spurgeon').
        
    Retorna:
        Dict[str, Any]: Detalhes do procedimento.
    """
    if TABLE_FACTORIO_ID == 0:
        return {"error": "O ID da tabela FACTORIO não está configurado."}
        
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_FACTORIO_ID}/?user_field_names=true&search={task_name}"
    
    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            return results[0]
        else:
            return {"mensagem": f"Nenhum procedimento encontrado para '{task_name}'."}
    except Exception as e:
        return {"error": f"Falha ao consultar FACTORIO: {str(e)}"}


def atualizar_status_operations(row_id: int, novo_status: str, observacao: Optional[str] = None) -> Dict[str, Any]:
    """
    Atualiza o status de uma tarefa na esteira OPERATIONS (taskflows).
    Sempre chame esta ferramenta após concluir o trabalho braçal em MINERATION.
    
    Argumentos:
        row_id (int): ID da linha na tabela OPERATIONS.
        novo_status (str): Ex: 'Done', 'Failed', 'Reviewing'.
        observacao (Optional[str]): Um log do que aconteceu (sucesso ou falha).
        
    Retorna:
        Dict[str, Any]: Resultado da operação no Baserow.
    """
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_OPERATIONS_ID}/{row_id}/?user_field_names=true"
    
    payload = {
        # O campo status pode requerer o ID da opção ou string dependendo da API, enviando string por padrão
        # Se for single-select dropdown, ajustar para {"id": ID_DA_OPCAO}
        "status": novo_status 
    }
    
    # Adicionar observacao num campo de log caso exista no seu schema
    
    try:
        response = requests.patch(url, headers=_get_headers(), json=payload, timeout=10)
        response.raise_for_status()
        return {"success": True, "message": f"Tarefa {row_id} movida para {novo_status}."}
    except Exception as e:
        return {"success": False, "error": f"Erro ao atualizar OPERATIONS: {str(e)}"}
