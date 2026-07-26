#!/usr/bin/env python3
"""
narrate_marketing.py — Narra e transcreve o hook/outro de um sermão (etapas A3+A4).

É o elo que faltava: o `marketing_meta.json` tem os TEXTOS, mas o vídeo precisa do
ÁUDIO narrado + a transcrição com timing (pras legendas do hook aparecerem sincronizadas).

Fluxo por sermão:
  1. baixa marketing_meta.json do R2
  2. narra hookText  → hook.wav          (Kokoro, voz do canal)
  3. narra outroText → cta_narration.wav (Kokoro)
  4. transcreve os dois → hook.json / cta_narration.json (AssemblyAI, word-level)
  5. sobe tudo pro R2

Depois disso o sermão fica PRONTO PRA RENDER.

Uso (na VPS, onde o Kokoro roda):
  python3 narrate_marketing.py --sermon 3
  python3 narrate_marketing.py --all --limit 5
"""
import os
import re
import sys
import json
import time
import argparse
import subprocess
import urllib.request

import boto3
from botocore.config import Config

BUCKET = "mananciall"
CHANNEL_PREFIX = "channels/channels_youtube/treasures_charlesspurgeon"
VOICE = "bm_george"   # voz do canal — NÃO mudar (consistência entre vídeos)
SPEED = "0.9"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "/srv/factorio/data/narrate" if os.path.isdir("/srv/factorio/data") else os.path.join(HERE, "_narrate")
TTS_IMAGE = os.environ.get("TTS_IMAGE", "factorio-tts")


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
    res = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{CHANNEL_PREFIX}/{nnnn}", MaxKeys=5)
    keys = [o["Key"] for o in res.get("Contents", [])]
    if not keys:
        res = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{CHANNEL_PREFIX}/", MaxKeys=1000)
        keys = [o["Key"] for o in res.get("Contents", []) if re.search(rf"/{nnnn}[-_]", o["Key"])]
    if not keys:
        raise RuntimeError(f"sermão {nnnn} não encontrado")
    return keys[0].rsplit("/", 1)[0]


def kokoro(text, out_wav):
    """Narra via container do Kokoro (o mesmo que a fábrica usa)."""
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    txt = out_wav.replace(".wav", ".txt")
    open(txt, "w", encoding="utf-8").write(text)
    host_dir = os.path.dirname(os.path.abspath(out_wav))
    subprocess.run([
        "docker", "run", "--rm", "--cpus=1.5", "--memory=4g",
        "-v", f"{host_dir}:/data", "-v", "/srv/factorio/hfcache:/cache",
        TTS_IMAGE,
        "--input", f"/data/{os.path.basename(txt)}",
        "--output", f"/data/{os.path.basename(out_wav)}",
        "--voice", VOICE, "--speed", SPEED,
    ], check=True, capture_output=True, text=True)
    os.remove(txt)


def transcribe(wav_path, api_key):
    """AssemblyAI: sobe o wav e devolve a transcrição com timing por palavra."""
    with open(wav_path, "rb") as f:
        req = urllib.request.Request("https://api.assemblyai.com/v2/upload", data=f.read(),
                                     headers={"authorization": api_key}, method="POST")
        upload_url = json.loads(urllib.request.urlopen(req, timeout=300).read())["upload_url"]

    body = json.dumps({"audio_url": upload_url, "language_code": "en"}).encode()
    req = urllib.request.Request("https://api.assemblyai.com/v2/transcript", data=body,
                                 headers={"authorization": api_key, "content-type": "application/json"},
                                 method="POST")
    tid = json.loads(urllib.request.urlopen(req, timeout=60).read())["id"]

    while True:
        time.sleep(3)
        req = urllib.request.Request(f"https://api.assemblyai.com/v2/transcript/{tid}",
                                     headers={"authorization": api_key})
        d = json.loads(urllib.request.urlopen(req, timeout=60).read())
        if d["status"] == "completed":
            return {"title": os.path.basename(wav_path), "text": d.get("text", ""),
                    "words": d.get("words", [])}
        if d["status"] == "error":
            raise RuntimeError(f"AssemblyAI: {d.get('error')}")


def process(env, s3, nnnn, force=False):
    folder = find_folder(s3, nnnn)
    files = {o["Key"].rsplit("/", 1)[-1]
             for o in s3.list_objects_v2(Bucket=BUCKET, Prefix=folder + "/").get("Contents", [])}

    need = {"hook.wav", "hook.json", "cta_narration.wav", "cta_narration.json"}
    if not force and need.issubset(files):
        print(f"⏭️  {nnnn} já narrado")
        return "skip"
    if "marketing_meta.json" not in files:
        print(f"⚠️  {nnnn} sem copy — rode generate_marketing.py antes")
        return "skip"

    meta = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/marketing_meta.json")["Body"].read())
    work = os.path.join(WORK, nnnn)
    os.makedirs(work, exist_ok=True)

    for text_key, wav_name, json_name in (
        ("hookText", "hook.wav", "hook.json"),
        ("outroText", "cta_narration.wav", "cta_narration.json"),
    ):
        text = (meta.get(text_key) or "").strip()
        if not text:
            print(f"⚠️  {nnnn} sem {text_key}")
            continue
        wav = os.path.join(work, wav_name)

        print(f"   🎙️  narrando {wav_name}...")
        kokoro(text, wav)

        print(f"   📝 transcrevendo {json_name}...")
        tr = transcribe(wav, env["ASSEMBLYAI_API_KEY"])

        s3.upload_file(wav, BUCKET, f"{folder}/{wav_name}", ExtraArgs={"ContentType": "audio/wav"})
        s3.put_object(Bucket=BUCKET, Key=f"{folder}/{json_name}",
                      Body=json.dumps(tr, ensure_ascii=False).encode(),
                      ContentType="application/json")
        os.remove(wav)

    print(f"✅ {nnnn} pronto pra render")
    return "ok"


def list_pending(s3):
    token, keys = None, []
    while True:
        kw = {"Bucket": BUCKET, "Prefix": f"{CHANNEL_PREFIX}/", "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        res = s3.list_objects_v2(**kw)
        keys += [o["Key"] for o in res.get("Contents", [])]
        if not res.get("IsTruncated"):
            break
        token = res.get("NextContinuationToken")
    folders = {}
    for k in keys:
        m = re.match(rf"{CHANNEL_PREFIX}/(\d[\d-]*)_-_[^/]+/(.+)$", k)
        if m:
            folders.setdefault(m.group(1)[:4], set()).add(m.group(2))
    pend = []
    for num, f in sorted(folders.items()):
        if "marketing_meta.json" in f and not {"hook.wav", "hook.json",
                                               "cta_narration.wav", "cta_narration.json"}.issubset(f):
            pend.append(num)
    return pend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sermon")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    env = load_env()
    for k in ("R2_ENDPOINT", "ASSEMBLYAI_API_KEY"):
        if not env.get(k):
            sys.exit(f"❌ falta {k}")
    s3 = s3c(env)

    if args.all:
        pend = list_pending(s3)
        if args.limit:
            pend = pend[:args.limit]
        print(f"📋 {len(pend)} sermões pra narrar\n")
        st = {"ok": 0, "skip": 0, "erro": 0}
        for i, n in enumerate(pend, 1):
            print(f"[{i}/{len(pend)}] sermão {n}")
            try:
                st[process(env, s3, n, args.force)] += 1
            except Exception as e:
                st["erro"] += 1
                print(f"❌ {n}: {str(e)[:150]}")
        print(f"\n🏁 ok={st['ok']} pulados={st['skip']} erros={st['erro']}")
        return

    if not args.sermon:
        sys.exit("informe --sermon N ou --all")
    process(env, s3, f"{int(args.sermon):04d}", args.force)


if __name__ == "__main__":
    main()
