#!/usr/bin/env python3
"""
animar.py — liga um pod no RunPod, anima os stills e DESLIGA. Sempre.

## A regra de ouro deste script

O risco financeiro da fábrica de âncoras não é o preço por clipe (é ~1 centavo).
É esquecer o pod ligado: um 4090 esquecido queima US$ 8,16 por dia. Por isso:

  - o `terminate` mora num `finally` — sai por erro, por Ctrl+C ou por sucesso,
    o pod morre do mesmo jeito;
  - existe um teto duro de minutos (`--teto`); estourou, mata e sai;
  - no fim o script CONFERE pela API que não sobrou pod de pé.

## Por que scp e não R2 no pod

A máquina é alugada de terceiro. Credencial de R2 não sobe pra GPU de aluguel.
Os stills sobem por scp e os mp4 descem por scp.

Uso:
  python scripts/ancoras/animar.py --stills scratch/ancoras/selecao --dry-run
  python scripts/ancoras/animar.py --stills scratch/ancoras/selecao --teto 45
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
GQL = "https://api.runpod.io/graphql?api_key="
TEMPLATE = "runpod-torch-v280"           # runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
GPU = "NVIDIA GeForce RTX 4090"          # US$ 0,34/h — melhor custo por clipe (doc 22 §5)
CHAVE_SSH = os.path.expanduser("~/.ssh/id_ed25519_factorio")
DISCO_GB = 60                            # modelo ~10GB + torch + saída


def env_fabrica():
    env = dict(os.environ)
    p = os.path.join(RAIZ, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="ignore"):
            line = line.replace("\r", "").strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k, v)
    return env


def gql(key, query):
    req = urllib.request.Request(GQL + key, data=json.dumps({"query": query}).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    if "errors" in d:
        raise RuntimeError(json.dumps(d["errors"])[:400])
    return d["data"]


def criar_pod(key, pubkey, nome, nuvem="COMMUNITY"):
    q = f'''mutation {{ podFindAndDeployOnDemand(input: {{
        cloudType: {nuvem}, gpuCount: 1, volumeInGb: 0,
        containerDiskInGb: {DISCO_GB}, minVcpuCount: 8, minMemoryInGb: 24,
        gpuTypeId: "{GPU}", name: "{nome}", templateId: "{TEMPLATE}",
        ports: "22/tcp", supportPublicIp: true,
        env: [{{ key: "PUBLIC_KEY", value: "{pubkey}" }}]
    }}) {{ id }} }}'''
    return gql(key, q)["podFindAndDeployOnDemand"]["id"]


def esperar_ssh(key, pod_id, teto_s=420):
    t0 = time.time()
    while time.time() - t0 < teto_s:
        d = gql(key, f'query {{ pod(input: {{podId: "{pod_id}"}}) {{ '
                     f'desiredStatus runtime {{ ports {{ ip publicPort privatePort isIpPublic }} }} }} }}')
        rt = (d.get("pod") or {}).get("runtime")
        if rt and rt.get("ports"):
            for p in rt["ports"]:
                if p["privatePort"] == 22 and p.get("isIpPublic"):
                    return p["ip"], p["publicPort"]
        time.sleep(10)
    raise TimeoutError("pod não expôs SSH a tempo")


def matar(key, pod_id):
    try:
        gql(key, f'mutation {{ podTerminate(input: {{podId: "{pod_id}"}}) }}')
        print(f"🛑 pod {pod_id} terminado")
    except Exception as e:
        print(f"⚠️  FALHA AO TERMINAR {pod_id}: {e}\n   >>> CONFIRA NO PAINEL DO RUNPOD <<<")


def conferir_limpo(key):
    d = gql(key, "query { myself { pods { id name desiredStatus } currentSpendPerHr } }")
    m = d["myself"]
    vivos = [p for p in (m.get("pods") or []) if p["desiredStatus"] != "TERMINATED"]
    print(f"🔎 pods vivos: {vivos or 'nenhum'} | gasto/h: {m.get('currentSpendPerHr')}")
    return not vivos


def ssh(ip, porta, cmd, timeout=3600):
    return subprocess.run(
        ["ssh", "-i", CHAVE_SSH, "-p", str(porta), "-o", "StrictHostKeyChecking=no",
         "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR",
         f"root@{ip}", cmd],
        capture_output=True, text=True, timeout=timeout)


def scp(ip, porta, origem, destino, recursivo=False):
    cmd = ["scp", "-i", CHAVE_SSH, "-P", str(porta), "-o", "StrictHostKeyChecking=no",
           "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR"]
    if recursivo:
        cmd.append("-r")
    cmd += [origem, destino]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=1800)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", required=True, help="pasta local com os stills aprovados")
    ap.add_argument("--saida", default="scratch/ancoras/clipes")
    ap.add_argument("--frames", type=int, default=61)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--lado", type=int, default=704)
    ap.add_argument("--teto", type=int, default=45, help="teto duro em minutos")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stills = [f for f in os.listdir(args.stills) if f.lower().endswith((".png", ".jpg"))]
    if not stills:
        sys.exit(f"❌ nenhum still em {args.stills}")
    custo_h = 0.34
    print(f"📦 {len(stills)} stills | GPU {GPU} (US$ {custo_h}/h) | teto {args.teto}min "
          f"(máx US$ {custo_h*args.teto/60:.2f})")
    if args.dry_run:
        print("(dry-run — nada criado)")
        return

    env = env_fabrica()
    key = env.get("RUNPOD_API_KEY") or sys.exit("❌ falta RUNPOD_API_KEY")
    pubkey = open(CHAVE_SSH + ".pub").read().strip()

    pod_id = None
    t_inicio = time.time()
    try:
        for nuvem in ("COMMUNITY", "SECURE"):
            try:
                pod_id = criar_pod(key, pubkey, "ancoras-i2v", nuvem)
                print(f"🚀 pod {pod_id} criado ({nuvem})")
                break
            except Exception as e:
                print(f"   {nuvem} indisponível: {str(e)[:120]}")
        if not pod_id:
            sys.exit("❌ sem 4090 disponível nas duas nuvens")

        ip, porta = esperar_ssh(key, pod_id)
        print(f"🔌 ssh root@{ip}:{porta} ({time.time()-t_inicio:.0f}s)")

        # o sshd às vezes sobe alguns segundos depois da porta aparecer
        for _ in range(30):
            if ssh(ip, porta, "echo ok", timeout=30).stdout.strip() == "ok":
                break
            time.sleep(5)

        print("⚙️  instalando diffusers (main) ...")
        r = ssh(ip, porta,
                "mkdir -p /work/stills /work/out && "
                "pip install -q --upgrade 'git+https://github.com/huggingface/diffusers' "
                "transformers accelerate ftfy imageio imageio-ffmpeg sentencepiece 2>&1 | tail -3")
        print("   ", (r.stdout or r.stderr).strip()[-300:] or "ok")

        scp(ip, porta, os.path.join(HERE, "pod_wan_i2v.py"), f"root@{ip}:/work/")
        for s in stills:
            scp(ip, porta, os.path.join(args.stills, s), f"root@{ip}:/work/stills/")
        print(f"📤 {len(stills)} stills enviados ({time.time()-t_inicio:.0f}s)")

        restante = args.teto * 60 - (time.time() - t_inicio)
        print(f"🎬 gerando (resta {restante/60:.0f}min de teto) ...")
        r = ssh(ip, porta,
                f"cd /work && python pod_wan_i2v.py --entrada /work/stills --saida /work/out "
                f"--frames {args.frames} --steps {args.steps} --lado {args.lado} 2>&1 | tail -40",
                timeout=max(300, int(restante)))
        print((r.stdout or r.stderr)[-3000:])

        os.makedirs(args.saida, exist_ok=True)
        scp(ip, porta, f"root@{ip}:/work/out/*", args.saida + "/")
        baixados = [f for f in os.listdir(args.saida) if f.endswith(".mp4")]
        print(f"📥 {len(baixados)} clipes baixados -> {args.saida}")

    finally:
        if pod_id:
            matar(key, pod_id)
            conferir_limpo(key)
        mins = (time.time() - t_inicio) / 60
        print(f"⏱️  {mins:.1f} min de pod ≈ US$ {custo_h*mins/60:.2f}")


if __name__ == "__main__":
    main()
