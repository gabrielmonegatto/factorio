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
# 🧨 MINA (23/08): o campo que a mutation aceita é o `id` do gpuType, NÃO o
# `displayName`. "NVIDIA A100 PCIe" (display) devolve "Unknown GPU type"; o id
# certo é "NVIDIA A100 80GB PCIe". Sempre conferir com a query gpuTypes { id }.
#
# 📌 ACHADO DE CUSTO: a RTX A6000 tem 48GB pelo MESMO preço do 4090 (US$0,33/h)
# e é 3,6x mais barata que a A100 80GB. Como o 14B com cpu_offload precisa de
# ~28GB (um expert por vez), 48GB bastam. É a placa certa pra esta fábrica.
# Preço da tabela = nuvem COMMUNITY. Quando ela está sem estoque o script cai na
# SECURE, que cobra mais (A6000 medida em 23/08: US$ 0,547/h contra 0,33). Por isso
# o teto é anunciado no PIOR caso: teto que subestima o gasto não é teto.
FATOR_SECURE = 1.7
GPUS = {
    "a6000": ("NVIDIA RTX A6000", 0.33, 48),      # ⭐ padrão pro 14B
    "4090":  ("NVIDIA GeForce RTX 4090", 0.34, 24),   # só serve pro 5B
    "l40s":  ("NVIDIA L40S", 0.79, 48),
    "a100":  ("NVIDIA A100 80GB PCIe", 1.19, 80),
    "h100":  ("NVIDIA H100 PCIe", 1.99, 80),
}
GPU = GPUS["a6000"][0]
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
    # 121 @ 24fps = 5,04s, o comprimento NATIVO do Wan 2.2 5B. Pedir menos
    # entrega menos movimento e ainda foge do que o modelo treinou.
    ap.add_argument("--frames", type=int, default=121)
    ap.add_argument("--steps", type=int, default=50)  # spec do Wan; 25 mata o movimento
    ap.add_argument("--lado", type=int, default=704)
    ap.add_argument("--teto", type=int, default=45, help="teto duro em minutos")
    ap.add_argument("--gpu", choices=list(GPUS), default="a6000")
    ap.add_argument("--modelo", choices=["5b", "14b"], default="14b")
    ap.add_argument("--largura", type=int, default=1280)
    ap.add_argument("--altura", type=int, default=720)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--variantes", help="JSON de variantes de prompt: banco de prova "
                    "sobre o primeiro still, um setup de pod pra N tentativas")
    ap.add_argument("--clarear", type=float, default=0.30,
                    help="gama no still ANTES de animar (0.30 levanta muito a "
                         "sombra). O preto do canal volta depois com graduar.py. "
                         "1.0 desliga.")
    ap.add_argument("--sem-catalogo", action="store_true",
                    help="ignora o movimento próprio de cada cena e usa o prompt "
                         "genérico por família (só pra comparar)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stills = [f for f in os.listdir(args.stills) if f.lower().endswith((".png", ".jpg"))]
    if not stills:
        sys.exit(f"❌ nenhum still em {args.stills}")
    global GPU
    GPU, custo_h, vram = GPUS[args.gpu]
    if args.modelo == "14b" and vram < 40:
        sys.exit(f"❌ {GPU} tem {vram}GB: o 14B precisa de 40GB+. Use --gpu a6000 (48GB, US$0,33/h)")
    teto_max = custo_h * FATOR_SECURE * args.teto / 60
    print(f"📦 {len(stills)} stills | {GPU} {vram}GB (US$ {custo_h}/h community) | modelo {args.modelo} "
          f"| {args.largura}x{args.altura} | teto {args.teto}min "
          f"(exposição máx US$ {teto_max:.2f} se cair na secure)")
    # 🧨 O catálogo tem movimento escrito PARA CADA CENA (42 deles), e até 23/08 o
    # gerador ignorava todos e usava um prompt genérico por família: as 5 cenas de
    # mar recebiam o mesmo texto e saíam iguais. Aqui o catálogo volta a mandar.
    prompts_path = None
    if not args.sem_catalogo and not args.variantes:
        import json as _json
        sys.path.insert(0, HERE)
        import casar_ancora as _ca
        import subir_clipes as _sc
        cenas = _ca.carregar_catalogo()
        ids = [c["id"] for c in cenas]
        por_id = {c["id"]: c for c in cenas}
        mapa = {}
        for s_nome in stills:
            base = os.path.splitext(s_nome)[0]
            cid = _sc.id_de_cena(base, ids)
            mov = (por_id.get(cid) or {}).get("movimento_en") if cid else None
            if mov:
                mapa[base] = mov
        if mapa:
            prompts_path = os.path.join(RAIZ, "scratch", "ancoras", "_prompts.json")
            os.makedirs(os.path.dirname(prompts_path), exist_ok=True)
            with open(prompts_path, "w", encoding="utf-8") as fh:
                _json.dump(mapa, fh, ensure_ascii=False, indent=1)
            print(f"📝 {len(mapa)}/{len(stills)} cenas com movimento próprio do catálogo")
        if len(mapa) < len(stills):
            print(f"   ⚠️  {len(stills)-len(mapa)} still(s) sem cena no catálogo: "
                  "vão cair no prompt genérico da família")

    # 🧨 ANIMA CLARO, ESCURECE DEPOIS. Medido em 23/08: o still do canal tem
    # luminância 7/255 e até 83% de preto absoluto, e o modelo i2v só anima o que
    # DISTINGUE — devolvia preto com riscos rastejando, que na tela vira "câmera
    # tremida". Clareando a entrada a cena inteira sobrevive (1,15MB de detalhe
    # contra 0,31MB); o preto volta na pós com graduar.py, e ainda esconde o
    # artefato, porque o artefato mora justamente na faixa que a gente apaga.
    pasta_stills = args.stills
    if args.clarear and args.clarear != 1.0:
        from PIL import Image
        pasta_stills = os.path.join(RAIZ, "scratch", "ancoras", "_stills_claros")
        os.makedirs(pasta_stills, exist_ok=True)
        tabela = [min(255, int((i / 255.0) ** args.clarear * 255 + 0.5))
                  for i in range(256)] * 3
        for s_nome in stills:
            Image.open(os.path.join(args.stills, s_nome)).convert("RGB")                  .point(tabela).save(os.path.join(pasta_stills, s_nome))
        print(f"☀️  {len(stills)} stills clareados (gama {args.clarear})")

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

        # Recursos do pod, ANTES de gastar. O 14B baixa ~56GB (dois experts) e
        # precisa de RAM de sistema pro offload. Disco cheio e OOM do kernel matam
        # o processo sem traceback: parecem "não fez nada". Melhor ver os números.
        # 🧨 `free -g` mostra a RAM do HOST, não o limite do container. Em 23/08 li
        # "503GB" e concluí que RAM não era o problema — era. O 14B carrega dois
        # experts de ~28GB e o kernel matou o processo no segundo, sem traceback,
        # contra um teto de cgroup MUITO menor. O número que importa é o do cgroup.
        r = ssh(ip, porta,
                "df -BG --output=avail / | tail -1; "
                "cat /sys/fs/cgroup/memory.max 2>/dev/null "
                "|| cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null "
                "|| echo max", timeout=60)
        vals = (r.stdout or "").split()
        if len(vals) >= 2:
            lim = vals[1]
            ram_gb = None if lim == "max" else int(lim) / 1e9
            print(f"    disco livre {vals[0]} · RAM do container "
                  + (f"{ram_gb:.0f}GB" if ram_gb else "sem limite"))
            if args.modelo == "14b" and ram_gb and ram_gb < 70:
                raise SystemExit(
                    f"❌ container com {ram_gb:.0f}GB de RAM: o 14B precisa de ~70GB "
                    "(dois experts de 28GB + text encoder). Use --modelo 5b, ou peça "
                    "um pod com mais RAM.")

        scp(ip, porta, os.path.join(HERE, "pod_wan_i2v.py"), f"root@{ip}:/work/")
        if args.variantes:
            scp(ip, porta, args.variantes, f"root@{ip}:/work/variantes.json")
        if prompts_path:
            scp(ip, porta, prompts_path, f"root@{ip}:/work/prompts.json")
        for s in stills:
            scp(ip, porta, os.path.join(pasta_stills, s), f"root@{ip}:/work/stills/")
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
            # 🧨 REPASSAR TODAS as flags. Em 23/08 só --lado ia, e o pod caía no
            # default 704x704 quadrado: a mesma resolução que o modelo não conhece
            # e que produziu o lote horrível. Flag que existe aqui e não atravessa
            # o ssh é flag que mente pro operador.
            (f"python -u pod_wan_i2v.py --entrada /work/stills --saida /work/out "
             f"--frames {args.frames} --steps {args.steps} --lado {args.lado} "
             f"--modelo {args.modelo} --largura {args.largura} --altura {args.altura} "
             + ("--loop " if args.loop else "")
             + ("--variantes /work/variantes.json " if args.variantes else "")
             + ("--prompts /work/prompts.json " if prompts_path else "")
             + f"> /work/log.txt 2>&1"),
            "touch /work/PRONTO",
            "",
        ])
        # imprimir o comando REAL: é a única prova de que a flag atravessou o ssh
        print("   $ " + [l for l in runner.split(NL) if l.startswith("python")][0])
        ssh(ip, porta, "rm -f /work/log.txt /work/PRONTO && "
                       "cat > /work/run.sh <<'EOS'" + NL + runner + "EOS" + NL +
                       "chmod +x /work/run.sh", timeout=60)
        ssh(ip, porta, "setsid /work/run.sh < /dev/null > /dev/null 2>&1 & echo LANCADO", timeout=60)

        os.makedirs(args.saida, exist_ok=True)
        visto = 0
        seguidas = 0
        baixados_ate_agora = set()
        while True:
            sobra = args.teto * 60 - (time.time() - t_pod)
            if sobra <= 0:
                print("⏹️  teto de tempo atingido, encerrando")
                break
            # 🧨 UMA consulta que estoura NÃO pode derrubar a rodada. Em 23/08 um
            # ssh de acompanhamento passou de 90s, a exceção subiu, o `finally`
            # matou o pod e 6 clipes prontos morreram junto (US$0,57). Rede
            # instável é normal; perder 8 horas de trabalho por causa dela não é.
            try:
                r = ssh(ip, porta, "cat /work/log.txt 2>/dev/null | tail -60; "
                                   "test -f /work/PRONTO && echo __FIM__", timeout=120)
                saida = r.stdout or ""
                seguidas = 0
            except Exception as e:
                seguidas += 1
                print(f"   ⚠️  consulta falhou ({str(e)[:60]}) — {seguidas}/10")
                if seguidas >= 10:      # 10 seguidas = o pod caiu de verdade
                    print("   ❌ pod não responde há 10 tentativas; encerrando")
                    break
                time.sleep(30)
                continue
            linhas = [l for l in saida.splitlines() if l.startswith("[wan]")]
            for l in linhas[visto:]:
                print("   " + l)
            visto = len(linhas)

            # 🧨 BAIXA O QUE JÁ FICOU PRONTO, a cada volta. Numa rodada de 8 horas,
            # esperar o fim pra buscar tudo é apostar 8 horas num único momento.
            try:
                rl = ssh(ip, porta, "ls /work/out/*.mp4 2>/dev/null", timeout=60)
                prontos = [x.strip().rsplit("/", 1)[-1] for x in (rl.stdout or "").splitlines() if x.strip()]
                novos = [x for x in prontos if x not in baixados_ate_agora]
                # o último pode estar sendo escrito agora; deixa pra próxima volta
                for nome in novos[:-1] if "__FIM__" not in saida else novos:
                    if scp(ip, porta, f"root@{ip}:/work/out/{nome}",
                           os.path.join(args.saida, nome)).returncode == 0:
                        baixados_ate_agora.add(nome)
                if novos[:-1] or ("__FIM__" in saida and novos):
                    print(f"   ⬇️  {len(baixados_ate_agora)} clipes já salvos localmente")
            except Exception as e:
                print(f"   ⚠️  não deu pra baixar parcial: {str(e)[:60]}")

            if "__FIM__" in saida:
                ultimo_log = saida
                break
            time.sleep(30)

        # 🧨 O filtro "[wan]" acima ESCONDE o traceback: em 23/08 o pod morreu logo
        # depois de carregar o modelo e a rodada terminou sem uma linha de erro na
        # tela. Quando não sai clipe, despejar o log cru é a única pista que resta,
        # porque o pod é destruído em seguida e leva o /work/log.txt junto.
        r = ssh(ip, porta, "ls /work/out/*.mp4 2>/dev/null | wc -l", timeout=60)
        n_remoto = int((r.stdout or "0").strip() or 0)
        if n_remoto == 0:
            print("")
            print("❌ o pod não produziu NENHUM mp4. Log cru do pod:")
            r = ssh(ip, porta, "tail -40 /work/log.txt 2>/dev/null", timeout=90)
            for l in (r.stdout or "(log vazio)").splitlines():
                print("   | " + l)
            raise SystemExit("❌ geração falhou no pod (nada pra baixar)")

        os.makedirs(args.saida, exist_ok=True)
        # 🧨 Contar os mp4 da PASTA depois do scp mente: sobra de rodada antiga é
        # contada como clipe novo. Em 23/08 o scp não achou nada e mesmo assim o
        # script anunciou "7 clipes baixados", todos velhos, do modelo errado.
        antes = {f: os.path.getmtime(os.path.join(args.saida, f))
                 for f in os.listdir(args.saida)}
        r = scp(ip, porta, f"root@{ip}:/work/out/*", args.saida + "/")
        if r.returncode != 0:
            raise SystemExit(f"❌ scp falhou: {(r.stderr or r.stdout)[-500:]}")
        novos = [f for f in os.listdir(args.saida)
                 if f.endswith(".mp4")
                 and os.path.getmtime(os.path.join(args.saida, f)) != antes.get(f)]
        print(f"📥 {len(novos)}/{n_remoto} clipes NOVOS -> {args.saida}")
        if len(novos) < n_remoto:
            print(f"   ⚠️  o pod tinha {n_remoto}; confira o que ficou pra trás")

    finally:
        if pod_id:
            matar(key, pod_id)
            conferir_limpo(key)
        mins = (time.time() - t_pod) / 60 if t_pod else 0.0
        print(f"⏱️  {mins:.1f} min de pod ≈ US$ {custo_h*mins/60:.2f}")


if __name__ == "__main__":
    main()
