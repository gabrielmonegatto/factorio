#!/usr/bin/env python3
"""
narrate_marketing.py — Narra e transcreve o hook/outro de um sermão (etapas A3+A4).

É o elo que faltava: o `marketing_meta.json` tem os TEXTOS, mas o vídeo precisa do
ÁUDIO narrado + a transcrição com timing (pras legendas do hook aparecerem sincronizadas).

Fluxo por sermão:
  1. baixa marketing_meta.json do R2
  2. narra hookText  → hook.wav          (Kokoro, voz do canal)
  3. narra outroText → cta_narration.wav (Kokoro)
  4. transcreve os dois → hook.json / cta_narration.json (mesmo motor do sermão)
  5. sobe tudo pro R2

Depois disso o sermão fica PRONTO PRA RENDER.

Uso (na VPS, onde o Kokoro roda):
  python3 narrate_marketing.py --canal moody --sermon 3
  python3 narrate_marketing.py --canal moody --all --limit 5
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

import canais
# Transcricao vem de narrar_sermao: um so lugar decide motor, ordem de reserva
# e conserto de timing. Duplicar isso aqui era garantir que o hook e o sermao
# divergissem no primeiro ajuste.
from narrar_sermao import transcrever

# Preenchidos em main() a partir de canais.get(--canal). Voz e velocidade são
# DO CANAL e não podem divergir da narração do sermão: hook numa voz e corpo em
# outra, dentro do mesmo vídeo, soa como erro de montagem.
BUCKET = CHANNEL_PREFIX = VOICE = SPEED = None
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


def kokoro(text, out_wav, pausa=0.75):
    """Narra via container do Kokoro, com a MESMA receita do sermao.

    Antes daqui saia narracao sem `--trim` e com `--cpus=1.5`. Os dois doiam:
    sem trim o hook tinha pausa de 2,1s entre frases enquanto o corpo do mesmo
    video tinha 0,83s (muda de ritmo na emenda, e o ouvido pega), e o teto de
    1,5 CPU custava 8x o tempo de parede a troco de nada.
    """
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    txt = out_wav.replace(".wav", ".txt")
    open(txt, "w", encoding="utf-8").write(text)
    host_dir = os.path.dirname(os.path.abspath(out_wav))
    subprocess.run([
        "docker", "run", "--rm", "--memory=8g",
        "-v", f"{host_dir}:/data", "-v", "/srv/factorio/hfcache:/cache",
        TTS_IMAGE,
        "--input", f"/data/{os.path.basename(txt)}",
        "--output", f"/data/{os.path.basename(out_wav)}",
        "--voice", VOICE, "--speed", SPEED,
        "--split", "sentence", "--silence", str(pausa), "--trim",
    ], check=True, capture_output=True, text=True)
    os.remove(txt)


def process(env, s3, C, nnnn, force=False):
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
        kokoro(text, wav, C.get("pausa_frase_s", 0.75))

        print(f"   📝 transcrevendo {json_name}...")
        tr = transcrever(wav, env, C)

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
    # 🧨 MINA DE 09/09/2026 (a terceira da mesma família: ver schedule_channel e
    # generate_marketing). 77 números do acervo do Spurgeon têm DUAS pastas, e
    # agrupar pelo NÚMERO funde os arquivos das duas. Aqui isso escondia sermão
    # pendente: a pasta B tinha hook e cta, a A não, e o número saía da fila.
    # Avaliar sempre a pasta que o `find_folder` abre: a primeira lexicográfica.
    pastas = {}
    for k in keys:
        m = re.match(rf"{CHANNEL_PREFIX}/((\d[\d-]*)_-_[^/]+)/(.+)$", k)
        if m:
            pastas.setdefault(m.group(1), set()).add(m.group(3))
    folders = {}
    for nome in sorted(pastas):
        folders.setdefault(nome[:4], pastas[nome])
    pend = []
    for num, f in sorted(folders.items()):
        if "marketing_meta.json" in f and not {"hook.wav", "hook.json",
                                               "cta_narration.wav", "cta_narration.json"}.issubset(f):
            pend.append(num)
    return pend


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--sermon")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    global BUCKET, CHANNEL_PREFIX, VOICE, SPEED
    C = canais.get(args.canal)
    BUCKET, CHANNEL_PREFIX = C["bucket"], C["prefix"]
    VOICE, SPEED = C["voz"], str(C["voz_speed"])
    print(f"🎙️  {C['nome']} · voz {VOICE} @ {SPEED}")

    env = load_env()
    if not env.get("R2_ENDPOINT"):
        sys.exit("❌ falta R2_ENDPOINT")
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
                st[process(env, s3, C, n, args.force)] += 1
            except Exception as e:
                st["erro"] += 1
                print(f"❌ {n}: {str(e)[:150]}")
        print(f"\n🏁 ok={st['ok']} pulados={st['skip']} erros={st['erro']}")
        return

    if not args.sermon:
        sys.exit("informe --sermon N ou --all")
    process(env, s3, C, f"{int(args.sermon):04d}", args.force)


if __name__ == "__main__":
    main()
