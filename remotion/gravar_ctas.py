#!/usr/bin/env python3
"""
gravar_ctas.py — grava os dois CTAs FIXOS do canal (telas 2 e 5 do vídeo).

## O que são

Diferente do hook, que muda a cada vídeo, estes dois são o MESMO áudio em todos
os vídeos do canal: o convite pra se inscrever na entrada e o agradecimento com
o QR na saída. Por serem fixos, ficam em `_assets/` e não na pasta do sermão.

## Por que virou script

A copy do Spurgeon não existia em texto em lugar nenhum: só existia dentro dos
mp3 que já estavam no ar desde julho. Foi recuperada em 22/08 transcrevendo o
próprio áudio com o `factorio-asr`. Agora ela vive em `canais.py`, e canal novo
herda a estrutura em vez de reinventar a roda ou copiar arquivo.

## ⚠️ Trocar a copy obriga a RE-RENDERIZAR

O `build_job` baixa estes dois com `force=True` justamente porque são mutáveis,
mas o vídeo já publicado carrega a versão antiga colada dentro. Mudou a copy,
os vídeos velhos ficam com a copy velha. É de propósito: re-renderizar 100
vídeos pra trocar uma frase não se paga.

Uso (na VPS, onde o Kokoro roda):
  python3 gravar_ctas.py --canal moody --dry-run
  python3 gravar_ctas.py --canal moody
"""
import argparse
import os
import subprocess

import boto3
from botocore.config import Config

import canais

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "/srv/factorio/data/ctas" if os.path.isdir("/srv/factorio/data") else os.path.join(HERE, "_ctas")
TTS_IMAGE = os.environ.get("TTS_IMAGE", "factorio-tts")

# texto no canais.py -> nome do arquivo em _assets/ (contrato com o build_job)
PECAS = [("cta_intro_texto", "introfixed.mp3"),
         ("cta_outro_texto", "finalfixed.mp3")]


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


def narrar(c, texto, wav):
    """Mesma receita de voz do sermão. Divergir aqui soa como erro de montagem:
    o espectador ouve a mesma pessoa mudando de ritmo na emenda."""
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    txt = wav.replace(".wav", ".txt")
    open(txt, "w", encoding="utf-8").write(texto)
    d = os.path.dirname(os.path.abspath(wav))
    subprocess.run([
        "docker", "run", "--rm", "--memory=8g",
        "-v", f"{d}:/data", "-v", "/srv/factorio/hfcache:/cache", TTS_IMAGE,
        "--input", f"/data/{os.path.basename(txt)}",
        "--output", f"/data/{os.path.basename(wav)}",
        "--voice", c["voz"], "--speed", str(c["voz_speed"]),
        "--split", "sentence", "--silence", str(c.get("pausa_frase_s", 0.75)), "--trim",
    ], check=True)
    os.remove(txt)


def para_mp3(wav, mp3):
    d = os.path.dirname(os.path.abspath(wav))
    subprocess.run([
        "docker", "run", "--rm", "-v", f"{d}:/data", "--entrypoint", "ffmpeg", TTS_IMAGE,
        "-y", "-loglevel", "error", "-i", f"/data/{os.path.basename(wav)}",
        "-ac", "1", "-b:a", "64k", f"/data/{os.path.basename(mp3)}",
    ], check=True)


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--dry-run", action="store_true", help="mostra o texto e para")
    args = ap.parse_args()

    c = canais.get(args.canal)
    faltando = [k for k, _ in PECAS if not (c.get(k) or "").strip()]
    if faltando:
        raise SystemExit(
            f"❌ canal {c['slug']!r} sem {', '.join(faltando)} em canais.py.\n"
            f"   Canal sem CTA gravado roda com as telas MUDAS (é o fallback do template).")

    print(f"🎙️  {c['nome']} · voz {c['voz']} @ {c['voz_speed']}")
    for chave, nome in PECAS:
        print(f"\n  {nome}:")
        print(f"    {c[chave]}")
    if args.dry_run:
        print("\n(dry-run: nada foi gravado nem subiu)")
        return

    env = load_env()
    s3 = s3c(env)
    for chave, nome in PECAS:
        base = os.path.join(WORK, c["slug"])
        wav = os.path.join(base, nome.replace(".mp3", ".wav"))
        mp3 = os.path.join(base, nome)
        narrar(c, c[chave], wav)
        para_mp3(wav, mp3)
        chave_r2 = f"{c['prefix']}/_assets/{nome}"
        s3.upload_file(mp3, c["bucket"], chave_r2, ExtraArgs={"ContentType": "audio/mpeg"})
        print(f"  ↑ {chave_r2}  ({os.path.getsize(mp3)//1024}KB)")
        os.remove(wav)
        os.remove(mp3)
    print("\n✅ CTAs fixos no ar. O build_job baixa os dois com force=True a cada render.")


if __name__ == "__main__":
    main()
