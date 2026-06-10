import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Carrega as chaves do seu arquivo .env
env_path = Path(r"C:\Users\Monegatto\Desktop\EternalL\_factorio\.env")
load_dotenv(dotenv_path=env_path)

from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

async def test_gemini():
    print("Iniciando teste de motor Gemini 2.5 Flash no SDK Antigravity...")
    os.environ["ANTIGRAVITY_HARNESS_PATH"] = r"C:\Users\Monegatto\AppData\Local\agy\bin\agy.exe"
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_key:
        print("ERRO: GEMINI_API_KEY não encontrada no .env!")
        return

    config = LocalAgentConfig(
        system_instructions="Você é um assistente de testes rápido e objetivo.",
        model="gemini-2.5-flash",
        api_key=gemini_key,
        capabilities=CapabilitiesConfig(),
        tools=[],
        triggers=[],
    )
    
    agent = Agent(config)
    await agent.__aenter__()
    try:
        print("Cérebro conectado! Enviando o prompt...")
        # Envia uma mensagem pra testar
        resposta = await agent.run("Responda exatamente e apenas com esta frase: 'O motor Gemini está funcionando perfeitamente na carcaça do Antigravity SDK!'")
        
        # A resposta do Antigravity Agent fica em .text ou convertendo pra string
        # A API pode ter mudado, mas normalmente as mensagens vêm em um objeto. 
        # Vamos imprimir a estrutura ou o texto:
        print("\n" + "="*50)
        print("🤖 RESPOSTA DO CÉREBRO GEMINI:")
        try:
            print(resposta.text)
        except AttributeError:
            print(resposta)
        print("="*50 + "\n")
    except Exception as e:
        print(f"Erro ao chamar o modelo: {e}")
    finally:
        await agent.__aexit__(None, None, None)

if __name__ == "__main__":
    asyncio.run(test_gemini())
