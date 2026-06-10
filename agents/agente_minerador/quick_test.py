#!/usr/bin/env python3
"""
Quick test: verifica se o Agente Minerador + OpenRouter + Gemini estão OK.

Uso:
    python quick_test.py

Saída:
    ✅ ou ❌ para cada componente
"""
import os, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "openrouter_skill"))

ROOT = Path(__file__).parent
ENV_PATH = Path(r"C:\Users\Monegatto\Desktop\EternalL\_factorio\.env")

def dotenv_load():
    """Carrega .env manualmente sem dependência."""
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def test_gemini():
    """Testa chave Gemini (AI Studio)."""
    try:
        import requests
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            return "❌ GEMINI_API_KEY não encontrada no .env"
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", []) if "gemini" in m["name"]]
            return f"✅ Gemini OK - {len(models)} modelos disponiveis (ex: {models[0]})"
        return f"❌ Gemini erro HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return f"❌ Gemini erro: {e}"

def test_openrouter():
    """Testa chave OpenRouter com DeepSeek."""
    try:
        from openrouter_client import chat
        result = chat("Responda apenas: OK", temperature=0.0)
        if "OK" in result:
            return f"✅ OpenRouter OK - Resposta: {result.strip()}"
        return f"❌ OpenRouter resposta inesperada: {result[:100]}"
    except Exception as e:
        return f"❌ OpenRouter erro: {e}"

def test_google_antigravity():
    """Verifica se o SDK está instalado."""
    try:
        import google.antigravity
        return f"✅ google-antigravity SDK instalado (v{getattr(google.antigravity, '__version__', '?')})"
    except ImportError:
        return "❌ google-antigravity SDK NAO instalado. Rode: pip install google-antigravity"

def main():
    dotenv_load()
    print("\n" + "=" * 55)
    print("  EternalL - Diagnostico do Agente Minerador")
    print("=" * 55)
    print(f"  Env file: {ENV_PATH}")
    print(f"  Env loaded: {ENV_PATH.exists()}")
    print(f"  GEMINI_API_KEY: {'***' + os.getenv('GEMINI_API_KEY', '')[-4:] if os.getenv('GEMINI_API_KEY') else 'NAO DEFINIDA'}")
    print(f"  OPENROUTER_API_KEY: {'***' + os.getenv('OPENROUTER_API_KEY', '')[-4:] if os.getenv('OPENROUTER_API_KEY') else 'NAO DEFINIDA'}")
    print("-" * 55)
    print(" ", test_google_antigravity())
    print(" ", test_gemini())
    print(" ", test_openrouter())
    print("=" * 55)

if __name__ == "__main__":
    main()