#!/usr/bin/env python3
"""
create_runpod.py — cria (ou atualiza) o template + endpoint serverless do render Spurgeon no RunPods.

Lê RUNPOD_API_KEY e as credenciais R2 do .env, cria um template apontando pra imagem do Docker Hub
(monegatto/spurgeon-render:latest) com as env vars do R2, e cria um endpoint CPU.

Uso: python create_runpod.py
Saída: IMPRIME o endpoint_id + o comando pronto pra disparar um render.
"""
import os
import sys
import json
import urllib.request

IMAGE = "monegatto/spurgeon-render:v4"
TEMPLATE_NAME = "spurgeon-render-tpl"
ENDPOINT_NAME = "spurgeon-render"


def load_env(path):
    env = {}
    for raw in open(path, encoding="utf-8"):
        line = raw.replace("\r", "").strip()
        if not line or line.startswith("#"):
            continue
        i = line.find("=")
        if i > 0:
            env[line[:i]] = line[i + 1:]
    return env


def api(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main():
    env = load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
    token = env.get("RUNPOD_API_KEY")
    if not token:
        sys.exit("❌ RUNPOD_API_KEY não encontrado no .env")

    r2_env = {k: env[k] for k in ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT", "R2_PUBLIC_URL") if env.get(k)}

    # 1. Template
    print("🧩 Criando template...")
    st, tpl = api("POST", "https://rest.runpod.io/v1/templates", token, {
        "name": TEMPLATE_NAME,
        "imageName": IMAGE,
        "isServerless": True,
        "containerDiskInGb": 40,
        "env": r2_env,
    })
    if st not in (200, 201):
        print(f"  resposta {st}: {json.dumps(tpl)[:400]}")
        # se já existe, tenta achar
        sys.exit("❌ Falha ao criar template (ver acima). Se já existe, ajuste o nome ou apague no painel.")
    template_id = tpl.get("id")
    print(f"  ✅ template_id = {template_id}")

    # 2. Endpoint CPU (Remotion é CPU/Chromium — muitos vCPUs aceleram o render por paralelismo de frames)
    print("🚀 Criando endpoint CPU...")
    st, ep = api("POST", "https://rest.runpod.io/v1/endpoints", token, {
        "templateId": template_id,
        "name": ENDPOINT_NAME,
        "computeType": "CPU",
        "vcpuCount": 16,
        "workersMin": 0,
        "workersMax": 1,
        "executionTimeoutMs": 3_600_000,  # 1h por job
        "idleTimeout": 5,
        "cpuFlavorIds": ["cpu5c"],  # compute-optimized
    })
    if st not in (200, 201):
        sys.exit(f"❌ Falha ao criar endpoint {st}: {json.dumps(ep)[:400]}")
    endpoint_id = ep.get("id")
    print(f"  ✅ endpoint_id = {endpoint_id}")

    print("\n=== PRONTO ===")
    print(f"Endpoint: {endpoint_id}")
    print("Disparar render do sermão 1:")
    print(f'  curl -s -X POST https://api.runpod.ai/v2/{endpoint_id}/run \\')
    print(f'    -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"input":{{"sermon":1}}}}\'')
    # salva pra reuso
    json.dump({"template_id": template_id, "endpoint_id": endpoint_id},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "runpod_ids.json"), "w"))


if __name__ == "__main__":
    main()
