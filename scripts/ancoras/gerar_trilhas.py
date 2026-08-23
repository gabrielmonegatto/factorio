#!/usr/bin/env python3
"""
gerar_trilhas.py — trilhas ORIGINAIS por clima, com o Google Lyria 3 no OpenRouter.

## Por que gerar em vez de licenciar

As 4 faixas atuais (`_globalassets/worship/`) resolvem o vídeo longo, mas são as
mesmas em tudo. Trilha própria dá três coisas: zero risco de direito autoral,
liberdade de fazer quantas quisermos, e o principal — **trilha CASADA COM O
CLIMA da cena**, do mesmo jeito que a âncora é casada com o tema.

## Preço real (conferido no catálogo do OpenRouter em 23/08/2026)

  google/lyria-3-pro-preview   US$ 0,08 por música completa, 48kHz
  google/lyria-3-clip-preview  US$ 0,04 por clipe de 30s

As 6 trilhas de clima abaixo custam **US$ 0,48** no Pro. É compra única: a
biblioteca serve o canal inteiro pra sempre.

## Regra de mixagem (por que o volume é tão baixo)

No short a voz É o produto. Trilha alta rouba inteligibilidade, que é o único
ativo que temos. O default da composição é 0.07, e o vídeo longo usa 0.05.
Nunca subir sem ouvir no celular, com fone ruim, que é onde o público está.

Uso:
  python scripts/ancoras/gerar_trilhas.py --listar
  python scripts/ancoras/gerar_trilhas.py --clima consolo --dry-run
  python scripts/ancoras/gerar_trilhas.py --todos
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
API = "https://openrouter.ai/api/v1/chat/completions"
MODELO_PRO = "google/lyria-3-pro-preview"
MODELO_CLIP = "google/lyria-3-clip-preview"
PREFIXO_R2 = "channels/channels_youtube/_globalassets/worship_ia"

# O bloco de estilo da trilha, análogo ao style block da bíblia visual: entra em
# TODO prompt e é o que faz as faixas soarem da mesma casa.
ESTILO = (" Instrumental only, absolutely no vocals, no lyrics, no choir, no spoken word. "
          "Sparse and restrained: it must sit far behind a spoken voice and never compete "
          "with it. Slow tempo, wide dynamic space, long sustained notes, no percussion "
          "hits, no build-up, no drop, no melodic hook that draws attention. "
          "Warm analogue texture, gentle tape hiss, subtle reverb. Loopable, "
          "no fade-in or fade-out, consistent from start to end. 19th century English "
          "sacred restraint, never cinematic trailer, never epic, never uplifting pop.")

CLIMAS = {
    "consolo":   "A quiet solo piano in a large empty stone room, soft felt hammers, long pauses between phrases, tender and consoling in a minor key that resolves gently.",
    "provacao":  "Low sustained strings and a distant deep drone, restless but never loud, a slow unresolved tension like weather gathering far away.",
    "reverencia":"Very slow warm organ pads in a stone church, almost still, breathing chords that hold for a long time, solemn and vast.",
    "esperanca": "Sparse piano notes over a soft warm pad, slowly rising in register, gentle and patient, light appearing without any triumph or fanfare.",
    "lamento":   "A single cello line, unaccompanied and slow, mournful and dignified, long bow strokes with silence between phrases.",
    "vigilia":   "A slow repeating two-note figure on a muted piano over near-silence, like a clock in a dark room, patient and unresolved.",
}


def env_fabrica(chave):
    v = os.environ.get(chave)
    if v:
        return v
    for line in open(os.path.join(RAIZ, ".env"), encoding="utf-8", errors="ignore"):
        line = line.replace(chr(13), "").strip()
        if line.startswith(chave + "="):
            return line.split("=", 1)[1]
    sys.exit(f"❌ {chave} não encontrado no .env")


def s3():
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=env_fabrica("R2_ENDPOINT"),
        aws_access_key_id=env_fabrica("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env_fabrica("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"), region_name="auto")


def gerar(clima, prompt, modelo, key, tentativas=3):
    body = json.dumps({
        "model": modelo,
        "modalities": ["text", "audio"],
        "messages": [{"role": "user", "content": prompt + ESTILO}],
    }).encode()
    erro = "?"
    for t in range(1, tentativas + 1):
        req = urllib.request.Request(API, data=body, method="POST",
              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                       # 🧨 sem User-Agent próprio a Cloudflare devolve 403/1010
                       "User-Agent": "factorio-trilhas/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                d = json.loads(r.read())
            msg = d["choices"][0]["message"]
            audio = msg.get("audio") or {}
            b64 = audio.get("data")
            if not b64:
                # alguns modelos devolvem em content como lista de partes
                for parte in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
                    if isinstance(parte, dict) and parte.get("type") == "output_audio":
                        b64 = (parte.get("output_audio") or {}).get("data")
            if not b64:
                erro = f"resposta sem áudio: {json.dumps(msg)[:200]}"
            else:
                return base64.b64decode(b64), audio.get("format", "mp3")
        except urllib.error.HTTPError as e:
            try:
                erro = json.loads(e.read().decode()).get("error", {}).get("message", str(e))[:200]
            except Exception:
                erro = str(e)[:200]
            if "402" in str(e) or "credit" in erro.lower():
                return None, f"SEM_CREDITO: {erro}"
        except Exception as e:
            erro = str(e)[:200]
        if t < tentativas:
            time.sleep(5 * t)
    return None, erro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clima", help=" | ".join(CLIMAS))
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--clip", action="store_true", help="usa o modelo de 30s (US$0,04) em vez do completo (US$0,08)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.listar:
        for k, v in CLIMAS.items():
            print(f"\n{k}\n  {v}")
        print(f"\n{len(CLIMAS)} climas · US$ {0.04 if args.clip else 0.08:.2f} cada")
        return

    alvo = list(CLIMAS) if args.todos else ([args.clima] if args.clima else None)
    if not alvo:
        sys.exit("informe --clima X, --todos ou --listar")
    if any(c not in CLIMAS for c in alvo):
        sys.exit(f"clima inválido. Conhecidos: {', '.join(CLIMAS)}")

    modelo = MODELO_CLIP if args.clip else MODELO_PRO
    preco = 0.04 if args.clip else 0.08
    print(f"🎵 {len(alvo)} trilhas · {modelo} · ~US$ {preco*len(alvo):.2f}")
    if args.dry_run:
        for c in alvo:
            print(f"  [dry] {PREFIXO_R2}/{c}.mp3")
        return

    key = env_fabrica("OPENROUTER_API_KEY")
    cli = s3()
    ok = 0
    for c in alvo:
        t = time.time()
        dados, fmt = gerar(c, CLIMAS[c], modelo, key)
        if not dados:
            print(f"  ❌ {c}: {fmt}")
            if str(fmt).startswith("SEM_CREDITO"):
                print("\n🛑 OpenRouter sem crédito. Ponha saldo e rode de novo.")
                break
            continue
        chave = f"{PREFIXO_R2}/{c}.{fmt if fmt in ('mp3','wav') else 'mp3'}"
        cli.put_object(Bucket="mananciall", Key=chave, Body=dados,
                       ContentType=f"audio/{'mpeg' if fmt=='mp3' else fmt}")
        ok += 1
        print(f"  ✅ {c:12} {len(dados)/1e6:>5.1f}MB {time.time()-t:>5.0f}s -> {chave}")
    print(f"\n🏁 {ok}/{len(alvo)} trilhas · gasto ~US$ {preco*ok:.2f}")


if __name__ == "__main__":
    main()
