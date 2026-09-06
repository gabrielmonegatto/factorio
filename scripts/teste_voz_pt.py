#!/usr/bin/env python3
"""
teste_voz_pt.py — prova de voz pra rede em português (Spurgeon BR), custo zero.

Pega um trecho de sermão do Spurgeon (D1), traduz com LLM (OpenRouter/DeepSeek,
versículos em linguagem de Almeida), e narra o MESMO trecho nas 3 vozes PT-BR do
Kokoro (pf_dora, pm_alex, pm_santa) com lang 'p'. Sai um mp3 por voz em
/tmp/voz_pt/ pro Gabriel escolher de ouvido. Gate: a voz é decisão dele.

Uso (na VPS): python3 scripts/teste_voz_pt.py [--numero 1] [--chars 1800]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "remotion"))
import narrar_sermao as N  # noqa: E402

VOZES = ["pf_dora", "pm_alex", "pm_santa"]
SAIDA = "/tmp/voz_pt"
PROMPT = (
    "Você é tradutor literário de sermões do século XIX para português do Brasil. "
    "Traduza o texto abaixo de Charles Spurgeon com fidelidade e naturalidade oral "
    "(vai ser NARRADO em voz alta): frases fluidas, sem arcaísmos forçados, mas com "
    "solenidade de púlpito. Citações bíblicas: verta no estilo da Almeida (ex.: "
    "'Eu sou o Senhor, não mudo'), nunca invente referência. Referências como "
    "'Malachi 3:6' viram 'Malaquias, capítulo três, versículo seis'. Devolva SÓ o "
    "texto traduzido, sem títulos, notas ou comentários.\n\n"
)


def texto_do_sermao(env, numero):
    # O texto NÃO mora em `sermons` (só metadados): mora em `chapters.body`,
    # ligado por `chapter_id`. A primeira versão pegou o campo string mais longo
    # de `sermons` (o audio_key, 96 chars) e a LLM "traduziu" inventando um
    # sermão inteiro a partir do título. Fonte errada = alucinação garantida.
    rows = N.d1(env, "SELECT s.titulo, c.body FROM sermons s JOIN chapters c ON c.id=s.chapter_id "
                     "WHERE s.canal='spurgeon' AND s.numero=? LIMIT 1", [numero])
    if not rows or not rows[0].get("body"):
        sys.exit(f"sermão {numero} sem texto em chapters")
    return rows[0]["titulo"], rows[0]["body"]


def traduzir(env, texto):
    body = {"model": "deepseek/deepseek-chat-v3.1", "temperature": 0.3,
            "messages": [{"role": "user", "content": PROMPT + texto}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {env['OPENROUTER_API_KEY']}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=180) as resp:
        j = json.loads(resp.read())
    return j["choices"][0]["message"]["content"].strip(), j.get("usage", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--numero", type=int, default=1)
    ap.add_argument("--chars", type=int, default=1800)
    a = ap.parse_args()
    env = N.load_env()
    os.makedirs(SAIDA, exist_ok=True)

    titulo, texto = texto_do_sermao(env, a.numero)
    trecho = N.normalizar_narracao(texto)[: a.chars]
    trecho = trecho[: trecho.rfind(".") + 1] or trecho
    print(f"📖 {titulo!r}: {len(trecho)} chars em inglês")
    pt, uso = traduzir(env, trecho)
    print(f"🌐 traduzido ({uso.get('total_tokens', '?')} tokens):\n{pt[:500]}...\n")
    open(f"{SAIDA}/trecho_en.txt", "w", encoding="utf-8").write(trecho)
    open(f"{SAIDA}/trecho_pt.txt", "w", encoding="utf-8").write(pt)

    for voz in VOZES:
        wav = f"{SAIDA}/{voz}.wav"
        subprocess.run(["docker", "run", "--rm", "--name", f"factorio_tts_teste_{voz}",
                        "--memory=8g", "--cpus=4", "-v", f"{SAIDA}:/data",
                        "-v", "/srv/factorio/hfcache:/cache", N.TTS_IMAGE,
                        "--input", "/data/trecho_pt.txt", "--output", f"/data/{voz}.wav",
                        "--voice", voz, "--lang", "p", "--speed", "0.9",
                        "--split", "sentence", "--silence", "0.75", "--trim"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(["docker", "run", "--rm", "-v", f"{SAIDA}:/data", "--entrypoint", "ffmpeg",
                        N.TTS_IMAGE, "-y", "-loglevel", "error", "-i", f"/data/{voz}.wav",
                        "-ac", "1", "-b:a", "96k", f"/data/{voz}.mp3"], check=True)
        os.remove(wav)
        print(f"🎙️  {voz}: {SAIDA}/{voz}.mp3 ({os.path.getsize(f'{SAIDA}/{voz}.mp3')//1000} KB)")


if __name__ == "__main__":
    main()
