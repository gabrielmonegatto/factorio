#!/usr/bin/env python3
"""
gerar_assets_canal.py — gera os assets visuais de um canal via Workers AI.

## Por que existe um Worker no meio

O `CLOUDFLARE_API_TOKEN` do `.env` tem D1 e Workers, mas NÃO tem Workers AI
(a API REST responde 401). O Worker `factorio-imagens` chama o modelo pelo
BINDING, que funciona em runtime sem token de API. Ele grava direto no R2.

## A receita visual da família TREASURES

Lida dos assets reais do Spurgeon que já estão no ar:
  - fundo: interior de igreja de época, MUITO escuro, luz entrando por vitral,
    dramático e cinematográfico, 16:9
  - busto: retrato fotorrealista do pregador, fundo PRETO, luz Rembrandt,
    traje formal do século XIX, quadrado

Cada canal muda o AMBIENTE e a PALETA, não a gramática:
  - Spurgeon: catedral gótica inglesa, fria, azulada
  - Moody: salão de avivamento americano em madeira, quente, âmbar

Uso:
  python scripts/gerar_assets_canal.py --canal moody --dry-run
  python scripts/gerar_assets_canal.py --canal moody
  python scripts/gerar_assets_canal.py --canal moody --so fundos
"""
import argparse
import json
import os
import sys
import time
import urllib.request

WORKER = "https://factorio-imagens.eternall.workers.dev/gerar"

# ── receitas por canal ──────────────────────────────────────────────────────
# `base` entra em TODO prompt do grupo: é o que mantém a família visual.
RECEITAS = {
    "moody": {
        "prefix": "channels/channels_youtube/treasures_dlmoody/_assets",
        "fundos": {
            "n": 20,
            "subdir": "hall",
            "nome": "hall_bg_cf_{i}.png",
            "base": ("interior of a 19th century American revival meeting hall, "
                     "warm amber light, wooden beams and pews, dust motes in shafts "
                     "of light, deeply shadowed, cinematic, atmospheric, "
                     "photorealistic, wide 16:9 composition, no people, no text"),
            "variacoes": [
                "tall arched windows with golden evening light pouring in",
                "empty wooden pews receding into darkness, single lamp lit",
                "raised preaching platform seen from the back of the hall",
                "gas lamps glowing along the side walls at dusk",
                "high wooden ceiling with exposed trusses, light from above",
                "wide gallery balcony above rows of empty seats",
                "morning light through plain glass windows, motes of dust",
                "long central aisle leading toward a simple pulpit",
                "candles and oil lamps casting warm pools of light",
                "rain on the windows, grey light, warm interior lamps",
                "winter light, cold outside, amber glow inside",
                "the hall seen from the platform looking out at empty seats",
                "simple wooden cross on the back wall, dim light",
                "side chapel alcove with worn wooden bench",
                "narrow wooden staircase to the gallery, shafts of light",
                "late afternoon sun low through the west windows",
                "an open hymnal on a lectern, lamp light beside it",
                "the entrance doors from inside, light spilling through",
                "an organ pipe wall in shadow, warm highlights",
                "empty hall at night, a single lamp still burning",
            ],
        },
        "bustos": {
            "n": 5,
            "subdir": "avatars",
            "nome": "moody_bust_cf_{i}.png",
            "base": ("photorealistic portrait of Dwight L. Moody, the 19th century "
                     "American evangelist: a stout bearded man in his fifties with a "
                     "full dark beard, receding hairline, kind and earnest expression, "
                     "wearing a formal black Victorian suit with white shirt. "
                     "Pure black background, dramatic Rembrandt lighting, warm amber "
                     "key light, sharp detail, square composition, no text"),
            "variacoes": [
                "looking directly at the camera, calm and steady",
                "three-quarter view, head slightly turned, thoughtful",
                "warm and approachable expression, faint smile",
                "serious and resolute, strong jaw, direct gaze",
                "slightly lower angle, dignified and composed",
            ],
        },
        "avatar": {
            "n": 1,
            "subdir": "",
            "nome": "channelavatar.png",
            "base": ("photorealistic tight head-and-shoulders portrait of Dwight L. "
                     "Moody, 19th century American evangelist, full dark beard, "
                     "formal black Victorian suit, warm amber Rembrandt lighting on "
                     "a pure black background, centered square composition, "
                     "crisp and readable as a small circular profile picture, no text"),
            "variacoes": [""],
        },
        "banner": {
            "n": 1,
            "subdir": "",
            "nome": "channelbanner.png",
            "base": ("wide cinematic banner: interior of a 19th century American "
                     "revival meeting hall bathed in warm amber light, empty wooden "
                     "pews, shafts of light from tall windows, deep shadows at the "
                     "edges, very wide panoramic composition with empty space in the "
                     "center for a title, atmospheric, photorealistic, no people, no text"),
            "variacoes": [""],
        },
    },
}


def token_segredo():
    """Segredo do Worker: env primeiro, senão lê do .env da fábrica."""
    s = os.environ.get("FACTORIO_IMAGENS_SEGREDO")
    if s:
        return s
    env = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8", errors="ignore"):
            line = line.replace(chr(13), "").strip()
            if line.startswith("FACTORIO_IMAGENS_SEGREDO="):
                return line.split("=", 1)[1]
    sys.exit("FACTORIO_IMAGENS_SEGREDO nao encontrado (env nem .env)")


def gerar(chave, prompt, segredo, tentativas=3):
    corpo = json.dumps({"chave": chave, "prompt": prompt}).encode()
    for t in range(1, tentativas + 1):
        req = urllib.request.Request(
            WORKER, data=corpo, method="POST",
            headers={"x-segredo": segredo, "Content-Type": "application/json",
                     # MINA: sem User-Agent de navegador o workers.dev responde
                     # 403 (bloqueio de bot) ao User-Agent padrao do urllib.
                     "User-Agent": "factorio-assets/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            if d.get("ok"):
                return d
            erro = d.get("erro")
        except Exception as e:
            erro = str(e)
        if t < tentativas:
            time.sleep(3 * t)
    return {"ok": False, "erro": erro}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--so", help="fundos | bustos | avatar | banner")
    args = ap.parse_args()

    r = RECEITAS.get(args.canal)
    if not r:
        sys.exit(f"sem receita pro canal {args.canal!r}. Conhecidos: {', '.join(RECEITAS)}")

    grupos = [args.so] if args.so else ["fundos", "bustos", "avatar", "banner"]
    segredo = None if args.dry_run else token_segredo()
    total_ok = total_falha = 0

    for g in grupos:
        cfg = r[g]
        print(f"\n=== {g} ({cfg['n']}) ===", flush=True)
        for i in range(1, cfg["n"] + 1):
            var = cfg["variacoes"][(i - 1) % len(cfg["variacoes"])]
            prompt = cfg["base"] + (", " + var if var else "")
            sub = f"/{cfg['subdir']}" if cfg["subdir"] else ""
            chave = f"{r['prefix']}{sub}/{cfg['nome'].format(i=i)}"
            if args.dry_run:
                print(f"  [{i:02d}] {chave}")
                print(f"       {prompt[:110]}...")
                continue
            d = gerar(chave, prompt, segredo)
            if d.get("ok"):
                total_ok += 1
                print(f"  [{i:02d}] ok  {round(d['bytes']/1024)}KB  {chave.rsplit('/',1)[-1]}", flush=True)
            else:
                total_falha += 1
                print(f"  [{i:02d}] FALHOU {chave.rsplit('/',1)[-1]}: {d.get('erro')}", flush=True)

    if not args.dry_run:
        print(f"\ngerados: {total_ok} | falhas: {total_falha}")


if __name__ == "__main__":
    main()
