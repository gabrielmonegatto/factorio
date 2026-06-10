import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Carrega as chaves do seu arquivo .env
env_path = Path(r"C:\Users\Monegatto\Desktop\EternalL\_factorio\.env")
load_dotenv(dotenv_path=env_path)

# Novos imports do OpenAI Agents SDK
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

# O LiteLLM busca a chave do OpenRouter nas variáveis de ambiente nativamente
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

WORK_DIR = Path(__file__).parent
AGENTS_MD_PATH = WORK_DIR / "AGENTS.md"
from subagents.mapeador.mapper_agent import mapeador_agent
from subagents.bibliotecario.librarian_agent import bibliotecario_agent
from agents import Agent, Runner, MultiProvider, RunConfig

def load_system_instructions() -> str:
    if AGENTS_MD_PATH.exists():
        return AGENTS_MD_PATH.read_text(encoding="utf-8")
    return "Você é o Agente Minerador Líder do projeto Mananciall."

async def tool_chamar_mapeador(url: str) -> str:
    """
    Delega a missão de extrair dados de uma fonte para o especialista Mapeador.
    Ele retornará uma lista (JSON) das obras encontradas.
    """
    print(f"\n🔄 [Handoff] Delegando a URL '{url}' para o Subagente Mapeador...")
    provider = MultiProvider(
        openai_base_url="https://openrouter.ai/api/v1",
        openai_api_key=os.environ["OPENROUTER_API_KEY"],
        unknown_prefix_mode="model_id",
    )
    resultado = await Runner.run(
        mapeador_agent, 
        f"Por favor, mapeie a fonte e retorne a lista de obras em JSON: {url}",
        run_config=RunConfig(model_provider=provider)
    )
    return "Relatório do Mapeador: " + str(resultado.final_output if hasattr(resultado, 'final_output') else resultado)

import subprocess

def disparar_ingestao_baserow(json_path: str):
    """Aciona o script determinístico e idempotente para merge com o Baserow"""
    print(f"\n🔄 [Handoff] Iniciando Ingestão Determinística no Baserow...")
    script_path = WORK_DIR / "scripts" / "ingest_to_baserow.py"
    
    # Roda o script de ingestão como subprocesso
    process = subprocess.Popen(
        ["python", str(script_path), json_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Imprime o output em tempo real
    for line in iter(process.stdout.readline, ''):
        print(f"[Ingestão] {line}", end='')
        
    process.stdout.close()
    return_code = process.wait()
    if return_code == 0:
        print("✅ Ingestão no Baserow finalizada com sucesso.")
    else:
        print("❌ Ingestão no Baserow falhou ou foi interrompida.")

async def iniciar_ciclo_de_mineracao():
    print("\n[TRIGGER] Iniciando ciclo de orquestração do Líder...")
    
    provider = MultiProvider(
        openai_base_url="https://openrouter.ai/api/v1",
        openai_api_key=os.environ["OPENROUTER_API_KEY"],
        unknown_prefix_mode="model_id",
    )
    
    # Instancia o Agente Líder
    from agents import function_tool
    lider = Agent(
        name="LiderMinerador",
        instructions=load_system_instructions() + "\n\nATENÇÃO: Você é apenas o ORQUESTRADOR. Você recebe uma URL, repassa para o Mapeador extrair os dados. Quando receber os dados de volta, você FINALIZA a execução imprimindo a lista final de obras no terminal. Não tente acionar outros agentes por enquanto.",
        model="deepseek/deepseek-v4-flash",
        tools=[function_tool(tool_chamar_mapeador)]
    )
    
    print("🧠 Invocando o Cérebro Líder (Orquestrador)...")
    try:
        # Ordem direta para o líder:
        ordem = "Temos uma nova fonte aprovada. Por favor, orquestre o mapeamento e validação da URL RAIZ: https://bibletruthpublishers.com/"
        resultado = await Runner.run(lider, ordem, run_config=RunConfig(model_provider=provider))
        
        print("\n✅ Resposta do Líder:")
        try:
            print(resultado.final_output)
        except AttributeError:
            print(resultado)
            
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        
    # Após a extração, dispara a ingestão determinística
    # O Mapeador salva o JSON bruto sempre em /tmp/resultados.json dentro do container
    json_path = "/tmp/resultados.json"
    if os.path.exists(json_path):
        disparar_ingestao_baserow(json_path)
    else:
        print(f"⚠️ JSON de extração não encontrado em {json_path}. Pulando ingestão.")

import requests

def get_openrouter_usage(api_key: str) -> float:
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("usage", 0.0)
    except Exception as e:
        print(f"Erro ao checar custo: {e}")
    return 0.0

async def main():
    print("=====================================================")
    print("🚀 Iniciando Fábrica Autônoma (OpenAI Agents SDK)")
    print("=====================================================")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("AVISO: OPENROUTER_API_KEY não encontrada no .env")
        return

    usage_before = get_openrouter_usage(api_key)

    print("\n[MODO DE ORQUESTRAÇÃO] Executando o trio (Líder -> Mapeador -> Bibliotecário)...")
    await iniciar_ciclo_de_mineracao()
    print("\n✅ Ciclo finalizado com sucesso.")
    
    usage_after = get_openrouter_usage(api_key)
    cost = usage_after - usage_before
    print(f"\n💰 Custo total desta execução (OpenRouter): ${cost:.4f}")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ Fábrica pausada manualmente pelo usuário.")
