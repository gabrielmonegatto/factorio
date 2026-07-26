#!/usr/bin/env python3
"""
publish_sermon.py — Publica UM sermão no YouTube (o passo final da fábrica).

Junta tudo: gera a thumbnail, monta título/descrição, pega o vídeo e sobe PRIVADO
(pra revisão no Studio) ou AGENDADO (--publish-at).

Roda dentro do container de render (tem remotion p/ thumb + as credenciais via env).
Uso:
  python3 publish_sermon.py --sermon 1                       # sobe PRIVADO
  python3 publish_sermon.py --sermon 1 --publish-at 2026-07-26T13:00:00Z
"""
import os
import sys
import json
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "mananciall"


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[:3]} falhou:\n{(r.stdout or '')[-500:]}\n{(r.stderr or '')[-1500:]}")
    return r


REDIRECT = "https://mananciall.org/go?s=yt&v="


def descricao(video_desc, nnnn):
    # resumo apaixonado (do LLM) + link clicável (celular não lê QR). NUNCA revela a fonte.
    link = f"{REDIRECT}{nnnn}"
    return (
        f"{video_desc}\n\n"
        f"📖 Charles Spurgeon's books & devotionals: {link}\n\n"
        f"🔔 Subscribe for more.\n\n"
        f"#CharlesSpurgeon #Christian #Gospel #Faith #Hope"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sermon", required=True)
    ap.add_argument("--publish-at", help="ISO UTC — agenda; ausente = PRIVADO")
    ap.add_argument("--public-dir", default=os.path.join(HERE, "public"))
    args = ap.parse_args()

    nnnn = f"{int(args.sermon):04d}"
    public = os.path.abspath(args.public_dir)
    props = os.path.join(HERE, f"props_{nnnn}.json")
    py = sys.executable

    # 1. build_job (garante props + assets + thumbnailText)
    print(f"=== [1/4] preparando assets do {nnnn} ===")
    sh([py, os.path.join(HERE, "build_job.py"), "--sermon", str(int(args.sermon)),
        "--out", props, "--public-dir", public], cwd=HERE)
    P = json.load(open(props, encoding="utf-8"))

    # 2. thumbnail
    print("=== [2/4] gerando thumbnail ===")
    thumb = os.path.join(HERE, f"_thumb_{nnnn}.png")
    npx = "npx.cmd" if os.name == "nt" else "npx"
    sh([npx, "remotion", "still", "Thumbnail", thumb, f"--props={props}"], cwd=HERE)

    # 3. vídeo: local (_hybrid) ou baixa do R2
    print("=== [3/4] localizando o vídeo ===")
    video = os.path.join(HERE, "_hybrid", nnnn, f"{nnnn}.mp4")
    if not os.path.exists(video):
        import boto3
        from botocore.config import Config
        env = {**os.environ}
        s3 = boto3.client("s3", endpoint_url=env["R2_ENDPOINT"], aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                          config=Config(signature_version="s3v4"), region_name="auto")
        video = os.path.join(HERE, f"_video_{nnnn}.mp4")
        s3.download_file(BUCKET, f"renders/spurgeon/{nnnn}.mp4", video)

    # 4. publica
    print("=== [4/4] subindo pro YouTube ===")
    title = P.get("marketingTitle") or P.get("sermonTitle")
    # pega o resumo apaixonado do marketing_meta (baixado pelo build_job)
    mk_path = os.path.join(public, "storage", "sermons", nnnn, "marketing_meta.json")
    video_desc = ""
    if os.path.exists(mk_path):
        video_desc = json.load(open(mk_path, encoding="utf-8")).get("videoDescription", "")
    if not video_desc:
        video_desc = title  # fallback
    cmd = [py, os.path.join(HERE, "publish_youtube.py"),
           "--video", video, "--title", title,
           "--description", descricao(video_desc, nnnn),
           "--thumbnail", thumb,
           "--tags", "Charles Spurgeon,sermon,christian,gospel,faith,spurgeon sermons",
           "--comment", f"📖 Get Charles Spurgeon's books & devotionals here 👉 {REDIRECT}{nnnn}",
           "--confirm"]
    if args.publish_at:
        cmd += ["--publish-at", args.publish_at]
    r = subprocess.run(cmd, cwd=HERE)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
