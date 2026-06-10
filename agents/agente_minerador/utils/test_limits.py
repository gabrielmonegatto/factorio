import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Adiciona o diretório correto para achar o .env e litellm
env_path = Path(r"C:\Users\Monegatto\Desktop\EternalL\_factorio\.env")
load_dotenv(dotenv_path=env_path)

# LiteLLM precisa pegar a chave explicitamente se não tiver importado os agents
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

from litellm import completion

def testar_limites():
    print("🔥 Iniciando Teste de Fogo: 10 requisições em série no gemini-2.5-flash...")
    
    for i in range(1, 11):
        print(f"-> Disparando requisição {i}/10...")
        try:
            res = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": "Diga apenas a palavra 'Limites'."}]
            )
            print(f"   ✅ [OK] Resposta recebida: {res.choices[0].message.content.strip()}")
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
                print(f"   ❌ [RATE LIMIT] Bateu no teto na requisição {i}! Erro: {e}")
            else:
                print(f"   ❌ [ERRO] Falha na req {i}: {e}")
            break

if __name__ == "__main__":
    testar_limites()
