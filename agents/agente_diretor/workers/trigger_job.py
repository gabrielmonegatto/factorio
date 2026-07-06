#!/usr/bin/env python3
"""
trigger_job.py — Dispara um job no Trigger.dev via API REST.
Uso: python trigger_job.py --task-slug <slug> [--payload '{"key":"val"}']

Exemplos:
  python trigger_job.py --task-slug process-translations
  python trigger_job.py --task-slug process-narrations --payload '{"project": "morning-and-evening"}'
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

TRIGGER_SECRET_KEY = os.getenv("TRIGGER_SECRET_KEY", "")
TRIGGER_API_URL = os.getenv("TRIGGER_API_URL", "https://api.trigger.dev")

def trigger_job(task_slug: str, payload: dict = None):
    if not TRIGGER_SECRET_KEY:
        print(json.dumps({"error": "TRIGGER_SECRET_KEY não configurada no .env"}))
        sys.exit(1)

    url = f"{TRIGGER_API_URL}/api/v1/tasks/{task_slug}/trigger"
    body = json.dumps(payload or {}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {TRIGGER_SECRET_KEY}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(json.dumps({"status": "triggered", "run_id": result.get("id"), "task": task_slug}))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(json.dumps({"error": f"HTTP {e.code}", "details": error_body, "task": task_slug}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "task": task_slug}))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Dispara job no Trigger.dev")
    parser.add_argument("--task-slug", required=True, help="Slug do job (ex: process-translations)")
    parser.add_argument("--payload", default="{}", help="JSON payload para o job")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Payload JSON inválido: {e}"}))
        sys.exit(1)

    trigger_job(args.task_slug, payload)

if __name__ == "__main__":
    main()
