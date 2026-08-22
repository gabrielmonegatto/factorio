#!/usr/bin/env python3
"""
gerar_stills.py — etapa 1 da biblioteca de âncoras visuais (doc 22).

Gera os STILLS que depois viram micro-clipes de 5s. Roda no Worker
`factorio-imagens` (Workers AI), que é GRÁTIS: nenhum gate de dinheiro aqui.

## Por que still antes de vídeo

O ablation do paper "Lights, Camera, Consistency" mede: sem seed frame de
imagem, a consistência despenca de 7,99 pra 0,55. E o descarte é o trabalho —
produtores relatam 12:1 a 25:1 de gerações por clipe aproveitado. Descartar
custa 3 segundos aqui e custa GPU lá na frente. Então descarta-se AQUI.

## O style block

A string `ESTILO` entra em 100% dos prompts, sem exceção. É ela que faz 300
clipes de assuntos diferentes parecerem o mesmo universo. Mexer nela = mexer na
identidade da biblioteca inteira (e obriga regerar tudo pra manter coesão).

## O que NUNCA gerar (regra do nicho, doc 22 §6)

Sem rosto, sem Cristo, sem personagem bíblico atuando, sem texto na imagem.
No público reformado, IA como atmosfera passa; IA como encarnação não passa.
A negativa está travada no fim do ESTILO — não remova.

Uso:
  python scripts/ancoras/gerar_stills.py --listar
  python scripts/ancoras/gerar_stills.py --familia mar --n 6 --dry-run
  python scripts/ancoras/gerar_stills.py --todas --n 6
  python scripts/ancoras/gerar_stills.py --todas --n 6 --modelo @cf/black-forest-labs/flux-2-dev
"""
import argparse
import json
import os
import sys
import time
import urllib.request

WORKER = "https://factorio-imagens.eternall.workers.dev/gerar"
PREFIXO_R2 = "ancoras/spurgeon"

# ─── STYLE BLOCK — entra em TODO prompt. É a identidade da biblioteca. ───────
ESTILO = (
    " Solemn, reverent, cinematic still. Desaturated palette of near-black, "
    "deep charcoal, warm amber and muted antique gold. Single soft directional "
    "light source, deep shadows, volumetric haze, shallow depth of field, "
    "subtle 35mm film grain, anamorphic look, muted contrast. "
    "No people, no faces, no figures, no text, no lettering, no watermark."
)

# ─── AS 7 FAMÍLIAS (doc 22 §6) ──────────────────────────────────────────────
# Cada cena é autocontida e NÃO figurativa. O vocabulário casa com o próprio
# Spurgeon: naufrágio, âncora, rocha, luz, porta estreita.
FAMILIAS = {
    "capela": [
        "Interior of an empty Victorian stone chapel nave, a single shaft of pale light falling through a high gothic window onto the worn stone floor, dust suspended in the air",
        "Rows of empty dark wooden pews receding into shadow, one lamp lit at the far end",
        "Coloured light from a stained glass window falling across a cold stone floor",
        "A high vaulted stone ceiling seen from below, faint light in the ribs of the arches",
        "An empty pulpit of dark carved wood, lit from one side, the hall beyond in darkness",
        "A long stone aisle at dusk, light fading through distant windows",
    ],
    "mar": [
        "Dark storm waves rolling slowly under a heavy leaden sky, cold spray catching the last of the light, open sea, no land",
        "A single distant lighthouse beam sweeping across black water at night",
        "Deep swell rising and falling in slow heavy motion, grey horizon",
        "Rain driving hard across the surface of a dark restless sea",
        "The moment a wave breaks against black rock, spray suspended in the air",
        "Still black water under fog at first light, absolutely calm after the storm",
    ],
    "fogo": [
        "Glowing embers dying down in an old stone hearth, slow curls of smoke rising, the last orange light in a dark room",
        "A single tall candle burning alone in a vast dark room, thin wisp of smoke",
        "An old oil lamp with a low flame on a wooden table, darkness all around",
        "The last flame guttering on a spent candle, wax pooled and cold",
        "Embers breathing orange and dimming in near total darkness",
        "A hearth fire seen through the doorway of a dark cold room",
    ],
    "natureza": [
        "Thick mist rolling slowly across an empty moor at first light, one bare tree standing alone in silhouette, dark tones",
        "A field of wheat bending in a slow wind under a heavy overcast sky",
        "A dark mountain ridge emerging from low cloud at dawn",
        "Heavy rain falling on still water among reeds, grey and quiet",
        "An ancient oak alone in a dark empty field, storm light behind it",
        "Snow falling slowly through bare black branches at dusk",
    ],
    "objetos": [
        "An old worn leather Bible lying open on a dark wooden table, gilded page edges catching the light of a single candle just out of frame",
        "A heavy iron chain lying broken on stone, one link parted, dim light",
        "A quill and inkwell beside a closed leather book on dark wood",
        "An empty wooden church pew seen from close, worn smooth by use, low light",
        "A ship's anchor resting on wet stone, weathered iron, cold grey light",
        "A plain wooden cross standing against a dark wall, no figure on it, single light source",
    ],
    "arquitetura": [
        "A narrow stone doorway at the far end of a dark corridor, warm light spilling through from beyond, heavy stone walls",
        "Worn stone steps ascending into darkness, faint light from above",
        "A tall arched stone passage, light entering only at the far end",
        "An empty stone road under a heavy dark sky, leading toward the horizon",
        "A weathered wooden door closed in a stone wall, thin light at its edges",
        "A high stone tower window seen from inside, cold light entering",
    ],
    "abstrato": [
        "Fine dust motes drifting slowly through a single shaft of light against deep darkness",
        "Slow volumetric fog rolling through a dark empty space, one warm light source behind it",
        "Soft embers of light rising slowly like sparks against black",
        "Rain running down old dark glass, warm light blurred beyond it",
        "Smoke curling slowly upward through a beam of pale light in a black room",
        "Deep water surface rippling slowly, a single amber reflection breaking apart",
    ],
}


def segredo_worker():
    s = os.environ.get("FACTORIO_IMAGENS_SEGREDO")
    if s:
        return s
    env = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8", errors="ignore"):
            line = line.replace("\r", "").strip()
            if line.startswith("FACTORIO_IMAGENS_SEGREDO="):
                return line.split("=", 1)[1]
    sys.exit("❌ FACTORIO_IMAGENS_SEGREDO não encontrado (env nem .env)")


def gerar(chave, prompt, segredo, modelo=None, tentativas=3):
    corpo = {"chave": chave, "prompt": prompt, "forca": True}
    if modelo:
        corpo["modelo"] = modelo
    dados = json.dumps(corpo).encode()
    erro = "?"
    for t in range(1, tentativas + 1):
        req = urllib.request.Request(
            WORKER, data=dados, method="POST",
            # MINA (doc 21): sem User-Agent próprio o workers.dev devolve 403.
            headers={"x-segredo": segredo, "Content-Type": "application/json",
                     "User-Agent": "factorio-ancoras/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                d = json.loads(r.read())
            if d.get("ok"):
                return d
            erro = d.get("erro", "resposta sem ok")
        except Exception as e:
            erro = str(e)[:160]
        if t < tentativas:
            time.sleep(3 * t)
    return {"ok": False, "erro": erro}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familia", help=f"uma de: {', '.join(FAMILIAS)}")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--n", type=int, default=6, help="quantas cenas por família (máx 6)")
    ap.add_argument("--modelo", help="modelo Workers AI (padrão: flux-1-schnell do Worker)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.listar:
        for f, cenas in FAMILIAS.items():
            print(f"\n{f} ({len(cenas)} cenas)")
            for i, c in enumerate(cenas, 1):
                print(f"  {i}. {c[:90]}...")
        return

    if args.todas:
        alvo = list(FAMILIAS)
    elif args.familia:
        if args.familia not in FAMILIAS:
            sys.exit(f"❌ família {args.familia!r} não existe. Use --listar")
        alvo = [args.familia]
    else:
        sys.exit("informe --familia X, --todas ou --listar")

    segredo = None if args.dry_run else segredo_worker()
    ok = falha = 0
    t0 = time.time()

    for fam in alvo:
        cenas = FAMILIAS[fam][: args.n]
        print(f"\n🎨 {fam} — {len(cenas)} stills")
        for i, cena in enumerate(cenas, 1):
            chave = f"{PREFIXO_R2}/{fam}/{fam}_{i:02d}.png"
            if args.dry_run:
                print(f"  [dry] {chave}")
                continue
            t = time.time()
            r = gerar(chave, cena + ESTILO, segredo, args.modelo)
            if r.get("ok"):
                ok += 1
                print(f"  ✅ {fam}_{i:02d}  {r['bytes']/1000:>4.0f}KB  {time.time()-t:>4.1f}s")
            else:
                falha += 1
                print(f"  ❌ {fam}_{i:02d}  {r.get('erro')}")

    if not args.dry_run:
        print(f"\n🏁 {ok} gerados, {falha} falhas, {time.time()-t0:.0f}s total")
        print(f"   R2: {PREFIXO_R2}/  (custo: zero — Workers AI)")


if __name__ == "__main__":
    main()
