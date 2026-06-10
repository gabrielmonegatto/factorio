import os
import asyncio
from dotenv import load_dotenv

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.cli.interactive import chat_loop
from langgraph.checkpoint.sqlite import SqliteSaver

# Carrega variáveis globais do projeto (API Keys, etc)
load_dotenv("c:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

def build_director():
    # Caminho base desta fábrica
    factory_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(factory_dir, "memory.sqlite")
    
    # Criar checkpointer persistente (Memória Cognitiva)
    checkpointer = SqliteSaver.from_conn_string(db_path)
    
    # Configurar o Backend de Filesystem para o agente acessar ferramentas e logs
    fs_backend = FilesystemBackend(
        base_dir=factory_dir,
        allowed_extensions=[".py", ".json", ".log", ".md", ".txt", ".csv"]
    )
    
    # Criar o Agente Diretor seguindo o padrão canônico
    agent = create_deep_agent(
        name="Agente Diretor",
        model="gemini-3.1-flash-lite-preview", # Usando o nome exato do catálogo
        memory=[
            os.path.join(factory_dir, "AGENTS.md"),
            os.path.join(factory_dir, "memories", "AGENTS.md") # Memória durável
        ],
        middlewares=[fs_backend], # Injeta ferramentas de sistema de arquivos
        checkpointer=checkpointer
    )
    
    return agent

if __name__ == "__main__":
    # Inicia o loop de conversa no terminal ZED
    agent = build_director()
    print("\n=======================================================")
    print("👔 Agente Diretor de Operações [Online]")
    print(f"📁 Workspace: {os.path.dirname(os.path.abspath(__file__))}")
    print("=======================================================\n")
    
    # thread_id específico para as operações do diretor
    asyncio.run(chat_loop(agent, thread_id="operations_director_1"))
