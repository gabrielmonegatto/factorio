#!/usr/bin/env python3
"""
hybrid_render.py — Render HÍBRIDO de um sermão (custo ~10x menor que full-Remotion).

Fluxo:
  1. build_job.py  -> baixa assets do R2, gera QR, escreve props_NNNN.json
  2. subtitle_ass.py -> gera a legenda .ass (idêntica ao SubtitleLayer do Remotion)
  3. Remotion renderiza SÓ os curtos: Clip-Intro (hook+CTA), Clip-Outro (hook+CTA+endscreen)
     + 1 still da base do corpo (Sermon-Body-Base)
  4. ffmpeg monta o CORPO: base (loop) + legenda queimada + narração + trilha  [o pesado, barato]
  5. ffmpeg concatena: intro + corpo + outro  (com fade-pra-preto nas junções)
  6. upload pro R2 -> renders/spurgeon/NNNN.mp4

Uso: python hybrid_render.py --sermon 2 [--public-dir ./public] [--no-upload]
"""
import os
import sys
import json
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "mananciall"


def sh(cmd, **kw):
    print("▶", " ".join(str(c) for c in cmd[:6]), "...")
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"falhou (exit {r.returncode}):\n{(r.stdout or '')[-800:]}\n{(r.stderr or '')[-2000:]}")
    return r


def ffprobe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def pubpath(public, rel):
    return os.path.join(public, rel.replace("/", os.sep))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sermon", required=True)
    ap.add_argument("--public-dir", default=os.path.join(HERE, "public"))
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    py = args.python
    public = os.path.abspath(args.public_dir)
    nnnn = f"{int(args.sermon):04d}"
    work = os.path.join(HERE, "_hybrid", nnnn)
    os.makedirs(work, exist_ok=True)
    props = os.path.join(HERE, f"props_{nnnn}.json")

    # 1. build_job (assets + QR + props)
    print(f"\n=== [1/6] build_job {nnnn} ===")
    sh([py, os.path.join(HERE, "build_job.py"), "--sermon", str(int(args.sermon)),
        "--out", props, "--public-dir", public], cwd=HERE)
    P = json.load(open(props, encoding="utf-8"))

    # 2. legenda .ass do corpo
    print(f"\n=== [2/6] legenda .ass ===")
    ass = os.path.join(work, f"sermon_{nnnn}.ass")
    transcript = pubpath(public, P["transcriptSlug"])
    sh([py, os.path.join(HERE, "subtitle_ass.py"), "--transcript", transcript, "--out", ass])

    # 3. Remotion: intro, outro, base still
    print(f"\n=== [3/6] Remotion (clipes curtos + base) ===")
    intro = os.path.join(work, "intro.mp4")
    outro = os.path.join(work, "outro.mp4")
    base = os.path.join(work, "base.png")
    npx = "npx.cmd" if os.name == "nt" else "npx"
    sh([npx, "remotion", "render", "Clip-Intro", intro, f"--props={props}"], cwd=HERE)
    sh([npx, "remotion", "render", "Clip-Outro", outro, f"--props={props}"], cwd=HERE)
    sh([npx, "remotion", "still", "Sermon-Body-Base", base, f"--props={props}"], cwd=HERE)

    # 4. CORPO no ffmpeg: base (loop) + legenda + narração + trilha
    print(f"\n=== [4/6] corpo (ffmpeg) ===")
    narration = pubpath(public, P["narrationUrl"])
    bgm = pubpath(public, P["bgmUrl"])
    bgm_vol = P.get("bgmVolume", 0.05)
    dur = ffprobe_dur(narration) + 3.0  # 3s de respiro no fim
    body = os.path.join(work, "body.mp4")
    ass_ff = ass.replace("\\", "/").replace(":", "\\:")  # escape p/ filtro subtitles
    vf = f"scale=1920:1080,subtitles='{ass_ff}'"
    sh([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", base,
        "-i", narration,
        "-stream_loop", "-1", "-i", bgm,
        "-filter_complex",
        f"[0:v]{vf}[v];[2:a]volume={bgm_vol}[bg];[1:a][bg]amix=inputs=2:duration=first:dropout_transition=0[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{dur:.2f}",
        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", body,
    ])

    # 5. concat intro + corpo + outro (fade-pra-preto nas junções)
    print(f"\n=== [5/6] concat (fade preto) ===")
    di, db, do = ffprobe_dur(intro), ffprobe_dur(body), ffprobe_dur(outro)
    F = 0.3
    fc = (
        f"[0:v]fade=t=out:st={di-F:.2f}:d={F}[v0];"
        f"[1:v]fade=t=in:st=0:d={F},fade=t=out:st={db-F:.2f}:d={F}[v1];"
        f"[2:v]fade=t=in:st=0:d={F}[v2];"
        f"[v0][0:a][v1][1:a][v2][2:a]concat=n=3:v=1:a=1[v][a]"
    )
    final = os.path.join(work, f"{nnnn}.mp4")
    sh([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", intro, "-i", body, "-i", outro,
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", final,
    ])
    total = ffprobe_dur(final)
    print(f"✅ vídeo final: {final}  ({total/60:.1f} min, {os.path.getsize(final)/1048576:.0f} MB)")

    # 6. upload
    if not args.no_upload:
        print(f"\n=== [6/6] upload R2 ===")
        import boto3
        from botocore.config import Config
        env = {}
        for l in open(os.path.join(HERE, "..", ".env"), encoding="utf-8"):
            l = l.replace("\r", "").strip()
            if l and not l.startswith("#") and "=" in l:
                k, v = l.split("=", 1); env[k] = v
        s3 = boto3.client("s3", endpoint_url=env["R2_ENDPOINT"], aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                          config=Config(signature_version="s3v4"), region_name="auto")
        key = f"renders/spurgeon/{nnnn}.mp4"
        s3.upload_file(final, BUCKET, key, ExtraArgs={"ContentType": "video/mp4"})
        print(f"✅ upload -> {key}")

    return final


if __name__ == "__main__":
    main()
