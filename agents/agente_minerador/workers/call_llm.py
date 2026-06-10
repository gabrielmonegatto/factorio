#!/usr/bin/env python3
"""
Worker: call_llm.py

Executa chamadas ao OpenRouter via linha de comando.
Útil para workers que precisam de LLM sem depender do SDK do Antigravity.

Uso:
    python call_llm.py --prompt "Resuma este texto..." --model deepseek/deepseek-chat
    python call_llm.py --prompt "Extraia o JSON..." --json
    python call_llm.py --prompt "Classifique..." --temperature 0.0

Saída:
    A resposta do modelo é impressa no stdout.
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openrouter_client import chat, chat_json


def main():
    parser = argparse.ArgumentParser(description="Chama OpenRouter via CLI")
    parser.add_argument("--prompt", "-p", required=True, help="Prompt para o modelo")
    parser.add_argument("--model", "-m", default="deepseek/deepseek-chat", help="Modelo no OpenRouter")
    parser.add_argument("--temperature", "-t", type=float, default=0.2, help="Temperatura")
    parser.add_argument("--system", "-s", default="", help="System prompt opcional")
    parser.add_argument("--json", action="store_true", help="Requer saída em JSON")

    args = parser.parse_args()

    if args.json:
        result = chat_json(prompt=args.prompt, model=args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = chat(
            prompt=args.prompt,
            model=args.model,
            temperature=args.temperature,
            system_prompt=args.system,
        )
        print(result)


if __name__ == "__main__":
    main()