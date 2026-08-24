#!/usr/bin/env python3
"""
render_buffer.py — mantém vídeos RENDERIZADOS à frente (o estoque que o agendador consome).

Renderiza os próximos sermões prontos (em ordem) que ainda não têm mp4 no R2.
Roda via cron (ex: a cada 3h renderiza 1) OU manual com --count N pra encher o buffer.

Uso (na VPS):
  python3 render_buffer.py --canal moody --count 14   # enche o buffer inicial
  python3 render_buffer.py --canal moody             # renderiza 1 (pro cron)
  python3 render_buffer.py --canal moody --loop      # PRODUTOR 24/7 desse canal
                                          #   até a fila esvaziar, dorme e recheca

O modo --loop é o que o serviço systemd factory-producer roda: mantém a fábrica
viva, produzindo continuamente enquanto houver sermão pronto sem render.
"""
import os
import sys
import time
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import canais
from schedule_channel import load_env, s3c, list_ready_sermons, assets_cutoff, video_fresh

FACTORY = os.path.join(HERE, "..", "docker", "factory.sh")


def render_one(canal, nnnn, cpus):
    print(f"🎬 [{canal}] renderizando {nnnn}...", flush=True)
    env2 = {**os.environ, "FACTORY_CPUS": cpus, "FACTORY_MEM": "24g"}
    r = subprocess.run(["bash", FACTORY, "render", str(int(nnnn)), canal], env=env2)
    ok = r.returncode == 0
    print(f"   {'✅' if ok else '❌ rc='+str(r.returncode)} {nnnn}", flush=True)
    return ok


def next_pending(s3):
    # "pendente" = sem render OU com render velho (mp4 mais antigo que os CTAs fixos).
    # Assim, trocar introfixed/finalfixed no R2 dispara refazer tudo, sem apagar nada.
    ready = list_ready_sermons(s3)
    cutoff = assets_cutoff(s3)
    pend = [n for n in ready if not video_fresh(s3, n, cutoff)]
    return ready, pend


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--cpus", default="12")
    ap.add_argument("--loop", action="store_true",
                    help="produtor 24/7: renderiza sem parar; fila vazia dorme e recheca")
    ap.add_argument("--sleep", type=int, default=1800,
                    help="segundos de espera quando a fila está vazia (modo --loop)")
    args = ap.parse_args()

    # A esteira é POR CANAL: cada canal tem seu produtor, sua fila e seu
    # estoque. Nada aqui olha pra dois canais ao mesmo tempo, de propósito.
    C = canais.get(args.canal)
    import schedule_channel as SC
    SC.C, SC.BUCKET, SC.CHANNEL_PREFIX = C, C["bucket"], C["prefix"]
    canal = C["slug"]

    env = load_env()
    s3 = s3c(env)

    if args.loop:
        print(f"♾️  PRODUTOR 24/7 de {C['nome']} (cpus={args.cpus}, recheca a cada {args.sleep}s quando vazio)", flush=True)
        # falhas consecutivas de UM mesmo sermão não travam a fábrica: pula pro próximo
        fail_streak = {}
        while True:
            ready, pend = next_pending(s3)
            pend = [n for n in pend if fail_streak.get(n, 0) < 3]
            if not pend:
                print(f"📦 [{canal}] prontos={len(ready)} | fila vazia — dormindo {args.sleep}s", flush=True)
                time.sleep(args.sleep)
                continue
            nnnn = pend[0]
            print(f"📦 [{canal}] prontos={len(ready)} | sem render={len(pend)} | próximo: {nnnn}", flush=True)
            if not render_one(canal, nnnn, args.cpus):
                fail_streak[nnnn] = fail_streak.get(nnnn, 0) + 1
            else:
                fail_streak.pop(nnnn, None)
        return

    ready, pend = next_pending(s3)
    alvo = pend[:args.count]
    print(f"📦 [{canal}] prontos={len(ready)} | sem render={len(pend)} | vou renderizar: {' '.join(alvo) or '(nada)'}")
    for nnnn in alvo:
        render_one(canal, nnnn, args.cpus)


if __name__ == "__main__":
    main()
