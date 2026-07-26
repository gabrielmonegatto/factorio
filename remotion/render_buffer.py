#!/usr/bin/env python3
"""
render_buffer.py — mantém vídeos RENDERIZADOS à frente (o estoque que o agendador consome).

Renderiza os próximos sermões prontos (em ordem) que ainda não têm mp4 no R2.
Roda via cron (ex: a cada 3h renderiza 1) OU manual com --count N pra encher o buffer.

Uso (na VPS):
  python3 render_buffer.py --count 14     # enche o buffer inicial
  python3 render_buffer.py                # renderiza 1 (default, pro cron)
"""
import os
import sys
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from schedule_channel import load_env, s3c, list_ready_sermons, video_rendered

FACTORY = os.path.join(HERE, "..", "docker", "factory.sh")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--cpus", default="12")
    args = ap.parse_args()

    env = load_env()
    s3 = s3c(env)
    ready = list_ready_sermons(s3)
    pend = [n for n in ready if not video_rendered(s3, n)]
    alvo = pend[:args.count]
    print(f"📦 prontos={len(ready)} | sem render={len(pend)} | vou renderizar: {' '.join(alvo) or '(nada)'}")

    for nnnn in alvo:
        print(f"🎬 renderizando {nnnn}...")
        env2 = {**os.environ, "FACTORY_CPUS": args.cpus, "FACTORY_MEM": "24g"}
        r = subprocess.run(["bash", FACTORY, "render", str(int(nnnn))], env=env2)
        print(f"   {'✅' if r.returncode == 0 else '❌ rc='+str(r.returncode)} {nnnn}")


if __name__ == "__main__":
    main()
