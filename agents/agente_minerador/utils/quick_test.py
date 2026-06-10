#!/usr/bin/env python3
"""
Quick test: verifica se OpenRouter e Gemini estão OK.

Uso:
    python quick_test.py
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).parent
ENV_PATH = ROOT / "_factorio" / ".env"


def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def test_gemini():
    try:
        import requests
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            return "GEMINI_API_KEY nao encontrada"
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", []) if "gemini" in m["name"]]
            return f"OK - {len(models)} modelos (ex: {models[0]})"
        return f"ERRO HTTP {r.status_code}"
    except Exception as e:
        return f"ERRO: {e}"


def test_openrouter():
    try:
        from openrouter_client import chat
        result = chat("Responda apenas: OK", temperature=0.0)
        return f"OK - {result.strip()}" if "OK" in result else f"Resposta inesperada: {result[:100]}"
    except Exception as e:
        return f"ERRO: {e}"


def main():
    load_env()
    print("\n" + "=" * 50)
    print("  EternalL - Diagnostico")
    print("=" * 50)
    print(f"  Gemini AI Studio:    {test_gemini()}")
    print(f"  OpenRouter DeepSeek: {test_openrouter()}")
    print("=" * 50)


if __name__ == "__main__":
    main()