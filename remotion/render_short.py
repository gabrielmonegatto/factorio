#!/usr/bin/env python3
"""
render_short.py — Estágios 2+3 da fábrica de shorts: cortar + renderizar + subir.

Lê o clips_meta.json do sermão (gerado por mine_clips.py), corta o trecho do
áudio master com ffmpeg, monta os props e renderiza a composição Short-Sermon
(1080x1920). Sobe o mp4 pro R2 em <renders_prefix>_shorts/NNNN_cXX.mp4.

Uso:
  python render_short.py --sermon 1                # todos os clipes do sermão
  python render_short.py --sermon 1 --clip 1       # só o clipe 1 (1-based)
  python render_short.py --sermon 1 --no-upload    # deixa só o mp4 local
"""
import os
import re
import sys
import json
import argparse
import subprocess

import boto3
from botocore.config import Config

import canais

# Preenchidos em main() a partir de canais.get(--canal).
BUCKET = CHANNEL_PREFIX = SHORTS_RENDER_PREFIX = None
HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC_SHORTS = os.path.join(HERE, "public", "shorts")
# Sem o canal no caminho, o short 0001_c01 do Moody sobrescreve o do Spurgeon.
# Mesma armadilha que o build_job e o hybrid_render tinham (23/08).
OUT_DIR = None   # preenchido em main() com o slug do canal
FADE_S = 0.15  # fade de áudio nas pontas do corte, tira o "tec" do corte seco


def load_env():
    env = dict(os.environ)
    for p in (os.path.join(HERE, "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def s3c(env):
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def find_folder(s3, nnnn):
    res = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{CHANNEL_PREFIX}/{nnnn}", MaxKeys=100)
    keys = [o["Key"] for o in res.get("Contents", [])]
    if not keys:
        sys.exit(f"❌ sermão {nnnn} não encontrado no R2")
    return keys[0].rsplit("/", 1)[0], [k.rsplit("/", 1)[1] for k in keys]


def master_audio_key(folder, files):
    # acervo tem 44 .wav e 68 .mp3 — aceitar os dois (regra do build_job)
    for f in files:
        if re.match(r"^sermon[\w-]*\.(wav|mp3)$", f):
            return f"{folder}/{f}"
    sys.exit(f"❌ áudio master não encontrado em {folder} (arquivos: {files})")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"❌ comando falhou: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r


def process_clip(env, s3, nnnn, idx, clip, master_local, upload=True, anchor=None):
    tag = f"{nnnn}_c{idx:02d}" + (f"_{anchor}" if anchor else "")
    os.makedirs(PUBLIC_SHORTS, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. corte do áudio (re-encode wav: corte exato, sem drift de frame mp3)
    start_s = clip["start_ms"] / 1000.0
    dur_s = (clip["end_ms"] - clip["start_ms"]) / 1000.0
    clip_wav = os.path.join(PUBLIC_SHORTS, f"{tag}.wav")
    run(["ffmpeg", "-y", "-ss", f"{start_s:.3f}", "-t", f"{dur_s:.3f}", "-i", master_local,
         "-af", f"afade=t=in:st=0:d={FADE_S},afade=t=out:st={dur_s - FADE_S:.3f}:d={FADE_S}",
         "-ar", "44100", "-ac", "2", clip_wav])

    # 2. props
    props = {
        "audioUrl": f"shorts/{tag}.wav",
        "words": clip["words"],
        "hookText": clip["hook_text"],
    }
    if anchor:
        props["anchorVideoUrl"] = f"anchors/{anchor}.mp4"
    props_path = os.path.join(PUBLIC_SHORTS, f"{tag}_props.json")
    json.dump(props, open(props_path, "w", encoding="utf-8"), ensure_ascii=False)

    # 3. render
    out_mp4 = os.path.join(OUT_DIR, f"{tag}.mp4")
    print(f"🎬 renderizando {tag} ({dur_s:.0f}s) ...")
    npx = "npx.cmd" if os.name == "nt" else "npx"
    run([npx, "remotion", "render", "Short-Sermon", out_mp4,
         f"--props={props_path}", "--log=error"])
    size_mb = os.path.getsize(out_mp4) / 1e6
    print(f"   ✅ {out_mp4} ({size_mb:.1f} MB)")

    # 4. upload
    if upload:
        key = f"{SHORTS_RENDER_PREFIX}/{tag}.mp4"
        s3.upload_file(out_mp4, BUCKET, key, ExtraArgs={"ContentType": "video/mp4"})
        print(f"   ☁️  R2 -> {key}")
    return out_mp4


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--sermon", required=True)
    ap.add_argument("--clip", type=int, help="renderiza só o clipe N (1-based)")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--anchor", help="âncora visual (nome em public/anchors/, ex: candle)")
    args = ap.parse_args()

    global BUCKET, CHANNEL_PREFIX, SHORTS_RENDER_PREFIX
    C = canais.get(args.canal)
    BUCKET, CHANNEL_PREFIX = C["bucket"], C["prefix"]
    # shorts saem ao lado dos longos, com sufixo: renders/moody -> renders/moody_shorts
    SHORTS_RENDER_PREFIX = C["renders_prefix"] + "_shorts"
    global OUT_DIR
    OUT_DIR = os.path.join(HERE, "out", "shorts", C["slug"])
    print(f"✂️  {C['nome']} · shorts de {int(args.sermon):04d}")

    env = load_env()
    s3 = s3c(env)
    nnnn = f"{int(args.sermon):04d}"
    folder, files = find_folder(s3, nnnn)

    if "clips_meta.json" not in files:
        sys.exit(f"❌ {nnnn} sem clips_meta.json — rode antes: python mine_clips.py --sermon {int(nnnn)}")
    meta = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/clips_meta.json")["Body"].read())
    clips = meta.get("clips", [])
    if not clips:
        sys.exit(f"❌ {nnnn}: clips_meta.json vazio")

    # áudio master (cache local — 100MB, baixa uma vez)
    mkey = master_audio_key(folder, files)
    master_local = os.path.join(PUBLIC_SHORTS, "_masters", os.path.basename(f"{nnnn}_{os.path.basename(mkey)}"))
    os.makedirs(os.path.dirname(master_local), exist_ok=True)
    if not os.path.exists(master_local):
        print(f"⬇️  baixando master {mkey} ...")
        s3.download_file(BUCKET, mkey, master_local)

    todo = [(args.clip, clips[args.clip - 1])] if args.clip else list(enumerate(clips, 1))
    outs = []
    for idx, clip in todo:
        outs.append(process_clip(env, s3, nnnn, idx, clip, master_local, upload=not args.no_upload, anchor=args.anchor))
    print(f"\n🏁 {len(outs)} short(s) prontos")


if __name__ == "__main__":
    main()
