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
# 🧨 O Wan 2.2 14B é MoE: dois experts de ~28GB em bf16. NÃO cabe nos 24GB do
# 4090 nem com offload (um expert sozinho já estoura). Pra 14B a placa mínima
# é A100 80GB. O 4090 só serve pro 5B, que é modelo de demo.
GPUS = {
    "4090": ("NVIDIA GeForce RTX 4090", 0.34),
    "a100": ("NVIDIA A100 PCIe", 1.19),
    "h100": ("NVIDIA H100 PCIe", 1.99),
}
GPU = GPUS["a100"][0]
CHAVE_SSH = os.path.expanduser("~/.ssh/id_ed25519_factorio")
DISCO_GB = 120                           # 14B: dois experts + text encoder + torch


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
    # 🧨 MINA (22/08, a mesma do doc 21 com workers.dev): a API do RunPod está
    # atrás da Cloudflare, que devolve 403 ao User-Agent padrão do urllib
    # ("Python-urllib/3.x"). Com curl a MESMA chamada passa. Sem este header,
    # toda mutation falha e parece falta de permissão ou de GPU — não é.
    # 🧨 MINA (22/08): a API do RunPod é INSTÁVEL. Já deu 403 transitório,
    # timeout de leitura e reset de conexão em rodadas seguidas. Reprova aqui,
    # num lugar só, senão cada chamada precisa do próprio tratamento — e uma
    # queda no meio do polling deixaria a máquina ligada torrando dinheiro.
    ultimo = None
    for t in range(1, 6):
        try:
            req = urllib.request.Request(GQL + key, data=json.dumps({"query": query}).encode(),
                                         method="POST",
                                         headers={"Content-Type": "application/json",
                                                  "User-Agent": "factorio-ancoras/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            if "errors" in d:
                raise RuntimeError(json.dumps(d["errors"])[:400])
            return d["data"]
        except Exception as e:
            ultimo = e
            if t < 5:
                time.sleep(4 * t)
    raise ultimo


def criar_pod(key, pubkey, nome, nuvem="COMMUNITY"):
    q = f'''mutation {{ podFindAndDeployOnDemand(input: {{
        cloudType: {nuvem}, gpuCount: 1, volumeInGb: 0,
        containerDiskInGb: {DISCO_GB}, minVcpuCount: 8, minMemoryInGb: 24,
        gpuTypeId: "{GPU}", name: "{nome}", templateId: "{TEMPLATE}",
        ports: "22/tcp", supportPublicIp: true,
        env: [{{ key: "PUBLIC_KEY", value: "{pubkey}" }}]
    }}) {{ id }} }}'''
    return gql(key, q)["podFindAndDeployOnDemand"]["id"]


def esperar_ssh(key, pod_id, teto_s=600):
    """Espera o SSH aparecer. Alguns pods (sobretudo COMMUNITY) nunca entregam
    IP público — por isso quem chama descarta e pede outro em vez de insistir."""
    t0 = time.time()
    visto = None
    while time.time() - t0 < teto_s:
        d = gql(key, f'query {{ pod(input: {{podId: "{pod_id}"}}) {{ '
                     f'desiredStatus runtime {{ ports {{ ip publicPort privatePort isIpPublic }} }} }} }}')
        pod = d.get("pod") or {}
        rt = pod.get("runtime")
        for p in (rt or {}).get("ports") or []:
            if p["privatePort"] == 22 and p.get("isIpPublic"):
                return p["ip"], p["publicPort"]
        estado = f"{pod.get('desiredStatus')}/{'runtime' if rt else 'sem runtime'}"
        if estado != visto:
            print(f"   ... {estado} ({time.time()-t0:.0f}s)")
            visto = estado
        time.sleep(10)
    raise TimeoutError("pod não expôs SSH a tempo")


def subir_pod(key, pubkey, tentativas=3):
    """Cria pod e garante SSH. Pod que não sobe é MORTO antes da próxima tentativa
    (senão fica ligado cobrando enquanto tentamos outro)."""
    for t in range(1, tentativas + 1):
        pod_id = None
        for c in range(1, 5):                      # 403 transitório da API
            nuvem = "SECURE" if (t + c) % 2 else "COMMUNITY"
            try:
                pod_id = criar_pod(key, pubkey, "ancoras-i2v", nuvem)
                print(f"🚀 pod {pod_id} criado ({nuvem}, tentativa {t}.{c})")
                break
            except Exception as e:
                print(f"   {nuvem} recusou: {str(e)[:90]}")
                time.sleep(6)
        if not pod_id:
            continue
        try:
            ip, porta = esperar_ssh(key, pod_id)
            # 🧨 MINA (22/08): a porta 22 aparecer NÃO significa que a chave já
            # foi instalada. O sshd sobe antes de o start script gravar o
            # PUBLIC_KEY, e o login devolve "Permission denied". Antes isso
            # passava calado e o erro só aparecia lá na frente, disfarçado.
            for _ in range(36):                    # até 3 min de paciência
                r = ssh(ip, porta, "echo PRONTO", timeout=25)
                if "PRONTO" in r.stdout:
                    print(f"   ssh autenticado em {ip}:{porta}")
                    return pod_id, ip, porta
                time.sleep(5)
            raise RuntimeError("ssh nunca autenticou (chave não instalada)")
        except Exception as e:
            print(f"   pod {pod_id} não serviu ({e}); descartando")
            matar(key, pod_id)
    raise RuntimeError("não consegui um pod com SSH em 3 tentativas")


def matar(key, pod_id):
    """Insiste. Pod vivo esquecido custa US$ 8/dia — não pode depender de 1 tentativa."""
    for t in range(1, 6):
        try:
            gql(key, f'mutation {{ podTerminate(input: {{podId: "{pod_id}"}}) }}')
            print(f"🛑 pod {pod_id} terminado")
            return
        except Exception as e:
            print(f"   tentativa {t} de matar falhou: {str(e)[:80]}")
            time.sleep(5)
    print(f"🚨 NÃO CONSEGUI TERMINAR {pod_id} — DESLIGUE NO PAINEL DO RUNPOD AGORA")


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
         "-o", "ServerAliveInterval=20", "-o", "ServerAliveCountMax=6",
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
    ap.add_argument("--gpu", choices=list(GPUS), default="a100")
    ap.add_argument("--modelo", choices=["5b", "14b"], default="14b")
    ap.add_argument("--largura", type=int, default=1280)
    ap.add_argument("--altura", type=int, default=720)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stills = [f for f in os.listdir(args.stills) if f.lower().endswith((".png", ".jpg"))]
    if not stills:
        sys.exit(f"❌ nenhum still em {args.stills}")
    global GPU
    GPU, custo_h = GPUS[args.gpu]
    print(f"📦 {len(stills)} stills | {GPU} (US$ {custo_h}/h) | modelo {args.modelo} "
          f"| {args.largura}x{args.altura} | teto {args.teto}min "
          f"(máx US$ {custo_h*args.teto/60:.2f})")
    if args.dry_run:
        print("(dry-run — nada criado)")
        return

    env = env_fabrica()
    key = env.get("RUNPOD_API_KEY") or sys.exit("❌ falta RUNPOD_API_KEY")
    pubkey = open(CHAVE_SSH + ".pub").read().strip()

    pod_id = None
    t_inicio = time.time()
    t_pod = None          # só conta dinheiro a partir do pod criado
    try:
        pod_id, ip, porta = subir_pod(key, pubkey)
        t_pod = t_pod or time.time()
        print(f"🔌 ssh root@{ip}:{porta} ({time.time()-t_inicio:.0f}s)")

        # 🧨 MINA: a imagem é Ubuntu 24.04, que aplica PEP 668 e RECUSA pip
        # global sem --break-system-packages. Sem isso o pip "roda" (exit 0 no
        # pipe), o import falha depois, e você paga GPU pra descobrir.
        print("⚙️  instalando diffusers (main) ...")
        ssh(ip, porta,
            "mkdir -p /work/stills /work/out && "
            "pip install -q --break-system-packages --upgrade "
            "'git+https://github.com/huggingface/diffusers' "
            "transformers accelerate ftfy imageio imageio-ffmpeg sentencepiece",
            timeout=1800)

        # verificação real ANTES de gastar: se não importa, aborta e desliga.
        v = ssh(ip, porta, "python -c \"from diffusers import WanPipeline, AutoencoderKLWan; "
                           "import torch; print('IMPORT_OK', torch.cuda.get_device_name(0))\"", timeout=300)
        if "IMPORT_OK" not in v.stdout:
            raise RuntimeError(f"ambiente não ficou pronto: {(v.stdout + v.stderr)[-500:]}")
        print("   ", v.stdout.strip())

        scp(ip, porta, os.path.join(HERE, "pod_wan_i2v.py"), f"root@{ip}:/work/")
        for s in stills:
            scp(ip, porta, os.path.join(args.stills, s), f"root@{ip}:/work/stills/")
        print(f"📤 {len(stills)} stills enviados ({time.time()-t_inicio:.0f}s)")

        # 🧨 MINA (22/08): rodar a geração DENTRO da sessão ssh perde tudo se a
        # conexão cair — e ela caiu depois de 33min ("connection reset by peer"),
        # queimando US$ 0,22 sem entregar nada. Trabalho longo roda SOLTO no pod
        # (setsid + nohup, saída sem buffer num log) e a gente só espia o log
        # com conexões curtas. Queda de rede vira inconveniente, não prejuízo.
        restante = args.teto * 60 - (time.time() - t_pod)
        print(f"🎬 gerando solto no pod (resta {restante/60:.0f}min de teto) ...")
        # grava um runner no pod e dispara solto: aspas atravessando
        # python -> ssh -> shell remoto é fonte garantida de bug.
        NL = chr(10)
        runner = NL.join([
            "#!/bin/bash",
            "cd /work",
            "export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True",
            (f"python -u pod_wan_i2v.py --entrada /work/stills --saida /work/out "
             f"--frames {args.frames} --steps {args.steps} --lado {args.lado} "
             f"> /work/log.txt 2>&1"),
            "touch /work/PRONTO",
            "",
        ])
        ssh(ip, porta, "rm -f /work/log.txt /work/PRONTO && "
                       "cat > /work/run.sh <<'EOS'" + NL + runner + "EOS" + NL +
                       "chmod +x /work/run.sh", timeout=60)
        ssh(ip, porta, "setsid /work/run.sh < /dev/null > /dev/null 2>&1 & echo LANCADO", timeout=60)

        visto = 0
        while True:
            sobra = args.teto * 60 - (time.time() - t_pod)
            if sobra <= 0:
                print("⏹️  teto de tempo atingido, encerrando")
                break
            r = ssh(ip, porta, "cat /work/log.txt 2>/dev/null | tail -60; "
                               "test -f /work/PRONTO && echo __FIM__", timeout=90)
            saida = r.stdout or ""
            linhas = [l for l in saida.splitlines() if l.startswith("[wan]")]
            for l in linhas[visto:]:
                print("   " + l)
            visto = len(linhas)
            if "__FIM__" in saida:
                break
            time.sleep(30)

        os.makedirs(args.saida, exist_ok=True)
        scp(ip, porta, f"root@{ip}:/work/out/*", args.saida + "/")
        baixados = [f for f in os.listdir(args.saida) if f.endswith(".mp4")]
        print(f"📥 {len(baixados)} clipes baixados -> {args.saida}")

    finally:
        if pod_id:
            matar(key, pod_id)
            conferir_limpo(key)
        mins = (time.time() - t_pod) / 60 if t_pod else 0.0
        print(f"⏱️  {mins:.1f} min de pod ≈ US$ {custo_h*mins/60:.2f}")


if __name__ == "__main__":
    main()
