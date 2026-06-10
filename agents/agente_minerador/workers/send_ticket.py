import argparse
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("c:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://localhost:80")
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN", "")
TABLE_ID = 1520  # agent_communications

def main():
    parser = argparse.ArgumentParser(description="Envia comunicações/tickets de agentes para o Baserow.")
    parser.add_argument("--agent", required=True, help="Nome do agente (ex: agente_minerador)")
    parser.add_argument("--type", required=True, choices=["report", "alert", "decision_required", "info"], help="Tipo de comunicação")
    parser.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"], help="Prioridade")
    parser.add_argument("--message", required=True, help="Mensagem do ticket")
    parser.add_argument("--context", default="", help="Contexto adicional")
    parser.add_argument("--status", default="pending", choices=["pending", "read", "resolved"], help="Status do ticket")
    parser.add_argument("--cycle_id", default="", help="ID da execução atual")

    args = parser.parse_args()

    headers = {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_ID}/?user_field_names=true"

    payload = {
        "agent": args.agent,
        "type": args.type,
        "priority": args.priority,
        "message": args.message,
        "context": args.context,
        "status": args.status,
        "cycle_id": args.cycle_id,
        "created_at": datetime.now().isoformat()
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            print(f"✅ Ticket enviado com sucesso! ID: {response.json().get('id')}")
        else:
            print(f"❌ Falha ao enviar ticket. Status: {response.status_code}, Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão ao enviar ticket: {e}")

if __name__ == "__main__":
    main()
