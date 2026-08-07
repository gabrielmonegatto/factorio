#!/usr/bin/env python3
"""
traduzir_narrar.py — traduz um texto e narra na voz do idioma (peça da esteira multilíngue).

A esteira nasceu cravada em inglês (VOICE=bm_george, language_code=en). Este script é o
primeiro tijolo da lateralização: recebe texto EN, devolve áudio em ES/PT.

Vozes do Kokoro por idioma (todas rodam em CPU, custo zero):
  en → bm_george (voz atual do canal)
  pt → pm_alex
  es → em_alex

Uso (na VPS):
  python3 traduzir_narrar.py --in texto_en.txt --lang pt --out /data/saida
"""
import os
import sys
import json
import argparse
import subprocess
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TTS_IMAGE = os.environ.get("TTS_IMAGE", "factorio-tts")
SPEED = "0.9"

VOZ = {"en": "bm_george", "pt": "pm_alex", "es": "em_alex"}
IDIOMA = {"pt": "português do Brasil", "es": "espanhol neutro (latino-americano)"}

# ⚠️ MINA: o Kokoro tem lang_code SEPARADO da voz. Trocar só a voz e deixar o
# lang_code em 'a' faz ele fonetizar português/espanhol com regras do INGLÊS —
# sai um gringo lendo português. Os dois têm que casar.
# ('a'=inglês US · 'b'=inglês UK · 'p'=português BR · 'e'=espanhol · 'f'=francês · 'i'=italiano)
LANG_CODE = {"en": "b", "pt": "p", "es": "e"}


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


def traduzir(texto, lang, env):
    """Tradução de sermão: preserva o tom de púlpito, não resume, não moderniza demais."""
    prompt = (
        f"Traduza o sermão abaixo para {IDIOMA[lang]}.\n\n"
        "REGRAS:\n"
        "- Preserve o tom de púlpito: solene, direto, pastoral. É pregação, não artigo.\n"
        "- NÃO resuma, NÃO corte, NÃO adicione. Traduza integralmente.\n"
        "- Mantenha as citações bíblicas no fraseado tradicional do idioma de destino.\n"
        "- Texto deve soar natural FALADO em voz alta (vai virar narração).\n"
        "- Devolva SOMENTE a tradução, sem comentários seus.\n\n"
        f"SERMÃO:\n{texto}"
    )
    body = json.dumps({
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body, method="POST",
        headers={"Authorization": "Bearer " + env["OPENROUTER_API_KEY"],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


def narrar(texto, lang, out_wav):
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    txt = out_wav.replace(".wav", ".txt")
    open(txt, "w", encoding="utf-8").write(texto)
    host = os.path.dirname(os.path.abspath(out_wav))
    subprocess.run([
        "docker", "run", "--rm", "--cpus=3", "--memory=6g",
        "-v", f"{host}:/data", "-v", "/srv/factorio/hfcache:/cache", TTS_IMAGE,
        "--input", f"/data/{os.path.basename(txt)}",
        "--output", f"/data/{os.path.basename(out_wav)}",
        "--voice", VOZ[lang], "--speed", SPEED,
        "--lang", LANG_CODE[lang],   # sem isto, fonetiza com regras do inglês
    ], check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--lang", required=True, choices=["pt", "es"])
    ap.add_argument("--out", required=True, help="pasta de saída")
    args = ap.parse_args()

    env = load_env()
    texto = open(args.entrada, encoding="utf-8").read()

    print(f"🌐 traduzindo para {args.lang} ({len(texto)} chars)...", flush=True)
    traduzido = traduzir(texto, args.lang, env)
    print(f"   ✅ {len(traduzido)} chars traduzidos", flush=True)

    os.makedirs(args.out, exist_ok=True)
    txt_path = os.path.join(args.out, f"sermao1_{args.lang}.txt")
    open(txt_path, "w", encoding="utf-8").write(traduzido)

    wav = os.path.join(args.out, f"sermao1_{args.lang}.wav")
    print(f"🎙️  narrando com {VOZ[args.lang]}...", flush=True)
    narrar(traduzido, args.lang, wav)
    print(f"   ✅ {wav} ({os.path.getsize(wav)//1024} KB)", flush=True)


if __name__ == "__main__":
    main()
