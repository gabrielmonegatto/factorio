#!/usr/bin/env python3
"""
buscar_broll.py — caça b-roll GRÁTIS (Pexels/Pixabay) pras cenas do catálogo.

## Papel na hierarquia (doc 23 §4)

Stock grátis é o degrau ZERO do fornecimento: antes de gastar 140 créditos num
clipe Kling, conferir se a cena existe filmada de verdade. A expectativa honesta:
mar/natureza/abstrato o stock cobre; capela e objetos de época (púlpito
vitoriano, véu do templo) não — esses são IA mesmo.

## As duas defesas contra o "clipe que todo mundo usa"

Canais de mindset usam os MESMOS 200 clipes famosos do Pexels, e conteúdo
repetitivo é motivo documentado de desmonetização (doc 22 §11f). Aqui:
  1. a busca pula as primeiras páginas (--pular-populares, default 30 vídeos):
     o clipe da página 4 é tão bom quanto o da 1 e mil vezes menos visto;
  2. NADA entra cru na biblioteca: todo candidato aprovado passa pela graduação
     (graduar.py) que impõe a paleta do canal.

## Licenças (conferidas 25/08/2026)

Pexels e Pixabay: uso comercial permitido, sem atribuição obrigatória, inclusive
em vídeo monetizado. Proibido é REDISTRIBUIR o acervo como acervo, o que não é
o nosso caso. Chaves de API são grátis:
  Pexels : https://www.pexels.com/api/      -> PEXELS_API_KEY no .env
  Pixabay: https://pixabay.com/api/docs/    -> PIXABAY_API_KEY no .env

Uso:
  python scripts/ancoras/buscar_broll.py --listar          # só mostra as buscas
  python scripts/ancoras/buscar_broll.py --familia mar     # baixa candidatos
  python scripts/ancoras/buscar_broll.py --todas
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import casar_ancora as ca  # noqa: E402
import subir_clipes as sc  # noqa: E402

# Busca derivada do catálogo, mas EDITADA à mão: o `imagem_en` é prompt de
# geração (longo, cheio de direção de luz) e motor de busca de stock quer 3-5
# palavras concretas. Cena sem entrada aqui = não vale buscar (é IA mesmo).
BUSCAS = {
    "storm_swell":        "dark storm ocean waves",
    "wave_on_rock":       "wave crashing rock slow motion",
    "still_water_dawn":   "calm lake fog dawn",
    "flood_waters":       "flood water field",
    "lighthouse_beam":    "lighthouse beam night sea",
    "anchor_on_stone":    "old anchor sea mist",
    "mist_moor":          "fog rolling field tree",
    "wheat_in_wind":      "wheat field wind",
    "lone_oak_storm":     "lone tree storm clouds",
    "mountain_in_cloud":  "mountain peak clouds timelapse",
    "rain_on_reeds":      "rain water reeds pond",
    "bare_branches_snow": "snow falling bare branches",
    "single_candle":      "single candle flame dark",
    "dying_embers":       "embers fire dying dark",
    "furnace_mouth":      "forge furnace glowing",
    "oil_lamp_low":       "oil lamp flame dark table",
    "guttering_flame":    "candle burning out smoke",
    "dust_in_beam":       "dust particles light beam dark",
    "rising_smoke":       "smoke rising black background",
    "rain_on_dark_glass": "rain window night bokeh",
    "embers_rising":      "sparks rising night fire",
    "ripple_amber":       "water ripples dark reflection",
    "empty_road_storm":   "empty dirt road storm clouds",
    "fortress_wall":      "old stone wall clouds",
    "ruined_wall_ivy":    "ivy stone ruin wind",
    "stone_stairs_dark":  "dark stone stairs light",
}


def env(chave):
    v = os.environ.get(chave)
    if not v:
        p = os.path.join(RAIZ, ".env")
        if os.path.exists(p):
            for linha in open(p, encoding="utf-8", errors="ignore"):
                linha = linha.replace("\r", "").strip()
                if linha.startswith(chave + "="):
                    return linha.split("=", 1)[1]
    return v


def _ssl():
    """🧨 A MESMA mina do animar_magnific: o urllib deste Python não acha a raiz
    de certificado e devolve 'certificate has expired', que parece problema do
    SERVIDOR e não é (curl abre normal). Este script nasceu antes do conserto e
    repetiu o erro. Conserto que fica num arquivo só não protege os outros."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def http_json(url, headers=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": "factorio-broll/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=60, context=_ssl()) as r:
        return json.loads(r.read())


def pexels(chave, busca, pular, n):
    """Vídeos landscape HD. `page` alto = fora do circuito batido."""
    pagina = pular // 15 + 1
    d = http_json("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
        {"query": busca, "orientation": "landscape", "size": "medium",
         "per_page": 15, "page": pagina}), {"Authorization": chave})
    saida = []
    for v in d.get("videos", [])[:n]:
        arqs = [f for f in v.get("video_files", [])
                if f.get("width") and 1200 <= f["width"] <= 2000]
        if arqs:
            saida.append({"fonte": "pexels", "id": v["id"], "dur": v.get("duration"),
                          "url": sorted(arqs, key=lambda f: f["width"])[0]["link"]})
    return saida


def pixabay(chave, busca, pular, n):
    pagina = pular // 15 + 1
    d = http_json("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": chave, "q": busca, "per_page": 15, "page": pagina}))
    saida = []
    for v in d.get("hits", [])[:n]:
        arq = (v.get("videos") or {}).get("medium") or {}
        if arq.get("url"):
            saida.append({"fonte": "pixabay", "id": v["id"], "dur": v.get("duration"),
                          "url": arq["url"]})
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cena", help="uma cena do catálogo")
    ap.add_argument("--familia")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--por-cena", type=int, default=3, help="candidatos por fonte")
    ap.add_argument("--pular-populares", type=int, default=30,
                    help="quantos resultados do topo IGNORAR (anti-clipe-batido)")
    ap.add_argument("--saida", default=os.path.join(RAIZ, "scratch", "ancoras", "broll"))
    args = ap.parse_args()

    cenas = {c["id"]: c for c in ca.carregar_catalogo()}
    if args.listar:
        for cid, q in BUSCAS.items():
            fam = cenas.get(cid, {}).get("familia", "?")
            print(f"  {fam:12} {cid:22} -> \"{q}\"")
        print(f"\n{len(BUSCAS)} cenas buscáveis de {len(cenas)} no catálogo "
              f"({len(cenas)-len(BUSCAS)} são IA obrigatória: época/capela)")
        return

    if args.cena:
        alvo = {args.cena: BUSCAS[args.cena]} if args.cena in BUSCAS else \
            sys.exit(f"❌ {args.cena} não é buscável (ou não existe)")
    elif args.familia:
        alvo = {cid: q for cid, q in BUSCAS.items()
                if cenas.get(cid, {}).get("familia") == args.familia}
    elif args.todas:
        alvo = BUSCAS
    else:
        sys.exit("informe --cena, --familia, --todas ou --listar")

    kpex = env("PEXELS_API_KEY")
    kpix = env("PIXABAY_API_KEY")
    if not (kpex or kpix):
        sys.exit("❌ falta PEXELS_API_KEY e/ou PIXABAY_API_KEY no .env "
                 "(grátis: pexels.com/api e pixabay.com/api/docs)")

    os.makedirs(args.saida, exist_ok=True)
    manifesto_p = os.path.join(args.saida, "manifesto.json")
    manifesto = json.load(open(manifesto_p, encoding="utf-8")) if os.path.exists(manifesto_p) else {}

    for cid, busca in alvo.items():
        print(f"\n🔎 {cid} — \"{busca}\"")
        candidatos = []
        for nome, fn, k in (("pexels", pexels, kpex), ("pixabay", pixabay, kpix)):
            if not k:
                continue
            try:
                candidatos += fn(k, busca, args.pular_populares, args.por_cena)
            except Exception as e:
                print(f"   ⚠️  {nome}: {str(e)[:120]}")
            time.sleep(1.2)          # cortesia com API grátis
        for c in candidatos:
            nome_arq = f"{cid}__{c['fonte']}_{c['id']}.mp4"
            destino = os.path.join(args.saida, nome_arq)
            if not os.path.exists(destino):
                try:
                    req = urllib.request.Request(c["url"], headers={"User-Agent": "factorio-broll/1.0"})
                    with urllib.request.urlopen(req, timeout=300, context=_ssl()) as r,                             open(destino, "wb") as f:
                        f.write(r.read())
                except Exception as e:
                    print(f"   ❌ download {c['fonte']}/{c['id']}: {str(e)[:100]}")
                    continue
            mov, _, luz = sc.medir_movimento(destino)
            mb = os.path.getsize(destino) / 1e6
            print(f"   📥 {nome_arq:40} {c['dur'] or '?':>4}s · mov {mov:4.1f}% · "
                  f"luz {luz:5.1f} · {mb:5.1f}MB")
            manifesto[nome_arq] = {"cena": cid, **c}
        json.dump(manifesto, open(manifesto_p, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    print(f"\n🏁 candidatos em {args.saida} — escolha os aprovados e rode "
          f"graduar.py NELES antes de qualquer uso (stock cru não entra na biblioteca)")


if __name__ == "__main__":
    main()
