#!/usr/bin/env python3
"""
casar_ancora.py — o elo que faltava: escolhe a ÂNCORA certa pro trecho do sermão.

## Por que isso é o diferencial

Filmpac (57 coleções), Storyblocks (19) e Artgrid (26) indexam por ASSUNTO e
parâmetro técnico. Nenhum indexa por SIGNIFICADO (doc 22 §11a). Nosso catálogo
indexa por tema, e os temas saíram do próprio Spurgeon.

Resultado: quando o trecho fala de tempestade, a âncora é mar revolto ou
fornalha, que são as imagens que ELE usa pra falar disso. O visual deixa de ser
enfeite e vira ilustração do texto.

## Por que NÃO usa LLM

O catálogo foi minerado do MESMO corpus que a esteira narra. Então as palavras
de imagem do Spurgeon ("storm", "anchor", "furnace") aparecem literalmente no
trecho. Casamento léxico direto resolve, é determinístico, custa zero e não
depende de API (que já nos deixou na mão duas vezes hoje).

O LLM entra só como desempate opcional (--llm), quando nada casa por léxico.

Uso:
  python scripts/ancoras/casar_ancora.py --texto "the storm shall not sink thee"
  python scripts/ancoras/casar_ancora.py --sermao 1          # todos os clipes
  python scripts/ancoras/casar_ancora.py --sermao 1 --gravar # escreve no clips_meta
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))

# Palavras-gatilho em inglês por tema. Vêm do vocabulário do próprio corpus:
# é o que liga o texto narrado (EN) às etiquetas do catálogo (PT).
GATILHOS = {
    "provacao":     ["trial", "tried", "affliction", "tempest", "storm", "furnace", "trouble", "suffer", "adversity", "chasten"],
    "consolo":      ["comfort", "console", "solace", "rest", "peace", "calm", "quiet", "balm", "soothe"],
    "medo":         ["fear", "afraid", "terror", "dread", "tremble", "alarm"],
    "esperanca":    ["hope", "expect", "await", "promise", "assurance", "anchor"],
    "fe":           ["faith", "believe", "trust", "confidence", "rely"],
    "morte":        ["death", "die", "dying", "grave", "tomb", "mortal", "perish", "dust"],
    "graca":        ["grace", "mercy", "free", "unmerited", "favour", "favor"],
    "pecado":       ["sin", "guilt", "transgression", "iniquity", "guilty", "corrupt"],
    "arrependimento": ["repent", "repentance", "contrite", "sorrow", "turn", "backslide", "cold"],
    "oracao":       ["pray", "prayer", "supplication", "intercede", "plead", "cry"],
    "perseveranca": ["persevere", "endure", "steadfast", "continue", "hold fast", "patience"],
    "juizo":        ["judgment", "judge", "wrath", "condemn", "reckon", "account", "damned"],
    "salvacao":     ["save", "saved", "salvation", "redeem", "deliver", "rescue"],
    "libertacao":   ["free", "loose", "chain", "bond", "captive", "fetter", "liberty"],
    "humildade":    ["humble", "lowly", "meek", "dust", "nothing", "worm"],
    "solidao":      ["alone", "lonely", "forsaken", "desolate", "solitary"],
    "brevidade":    ["brief", "vapour", "vapor", "fleeting", "short", "vanish", "shadow", "swift"],
    "seguranca":    ["safe", "secure", "keep", "preserve", "refuge", "shelter", "fortress"],
    "imutabilidade": ["unchanging", "immutable", "same", "never change", "eternal", "everlasting"],
    "purificacao":  ["purify", "refine", "cleanse", "wash", "purge", "dross"],
    "urgencia":     ["now", "today", "delay", "haste", "before it be too late", "hasten"],
    "palavra":      ["scripture", "word", "bible", "written", "text", "promise"],
    "vigilancia":   ["watch", "awake", "vigilant", "sober", "ready"],
    "recompensa":   ["reward", "crown", "inherit", "prize", "recompense"],
    "caminho":      ["path", "road", "walk", "journey", "pilgrim", "way"],
    "fundamento":   ["foundation", "rock", "cornerstone", "build", "stand"],
    "colheita":     ["harvest", "reap", "sow", "seed", "fruit", "gather"],
    "escuridao":    ["dark", "darkness", "night", "gloom", "black"],
    "revelacao":    ["reveal", "light", "shine", "manifest", "shew", "show"],
    "tristeza":     ["grief", "sorrow", "weep", "tears", "mourn", "sad"],
    "paz":          ["peace", "still", "quiet", "rest", "tranquil"],
    "adoracao":     ["worship", "adore", "praise", "glory", "magnify"],
    "provisao":     ["provide", "supply", "bread", "feed", "need", "want"],
    "eternidade":   ["eternal", "forever", "everlasting", "endless", "heaven"],
}


def carregar_catalogo():
    with open(os.path.join(HERE, "catalogo_cenas.json"), encoding="utf-8") as f:
        return json.load(f)["cenas"]


# Vocabulário de imagem REALMENTE minerado dos 212 sermões (>= 90 ocorrências).
# Restringir o casamento léxico a esta lista mata o ruído: sem ela, a cena casava
# por "view" e "itself", que são palavras de enquadramento do prompt, não imagem.
# "way", "well", "house", "home" e "book" ficaram DE FORA apesar de frequentes:
# no uso do Spurgeon são figura de linguagem (doc 22 §10).
IMAGENS_DO_CORPUS = set(['battle', 'blood', 'bone', 'bread', 'cloud', 'crown', 'darkness', 'door', 'dove', 'dust', 'field', 'fire', 'flame', 'flood', 'foundation', 'fruit', 'furnace', 'garment', 'gate', 'gold', 'grave', 'hill', 'lamb', 'light', 'lion', 'morning', 'mountain', 'night', 'river', 'road', 'rock', 'sea', 'seed', 'smoke', 'soldier', 'star', 'stone', 'stream', 'sun', 'sword', 'tears', 'temple', 'throne', 'thunder', 'tree', 'wall', 'war', 'water', 'wave', 'wilderness', 'wind', 'wine', 'wound'])


def palavras_da_cena(cena):
    """Só conta palavra que é imagem de verdade no corpus do Spurgeon."""
    return {w for w in re.findall(r"[a-z]{3,}", cena["imagem_en"].lower())
            if w in IMAGENS_DO_CORPUS}


def pontuar(texto, cenas):
    t = texto.lower()
    palavras_texto = set(re.findall(r"[a-z]{3,}", t))
    resultados = []
    for c in cenas:
        pontos = 0.0
        motivos = []

        # 1. casamento LÉXICO direto (peso maior: a cena veio dessas palavras)
        comuns = palavras_da_cena(c) & palavras_texto
        if comuns:
            pontos += 3.0 * len(comuns)
            motivos.append("imagem:" + ",".join(sorted(comuns)[:3]))

        # 2. casamento por TEMA (via gatilhos em inglês)
        for tema in c["temas"]:
            hits = [g for g in GATILHOS.get(tema, []) if g in t]
            if hits:
                pontos += 1.5 * len(hits)
                motivos.append(f"{tema}:{hits[0]}")

        if pontos:
            resultados.append({"cena": c, "pontos": round(pontos, 1), "motivos": motivos})
    resultados.sort(key=lambda r: -r["pontos"])
    return resultados


def escolher(texto, cenas, usados=None, topo=3):
    """Melhor cena não usada ainda. Evitar repetição não é estética: a política
    de 'inauthentic content' do YouTube mira template repetido (doc 22 §11f)."""
    usados = usados or set()
    ranking = pontuar(texto, cenas)
    for r in ranking:
        if r["cena"]["id"] not in usados:
            return r, ranking[:topo]
    # nada casou: cai numa cena neutra da família abstrato, também sem repetir
    for c in cenas:
        if c["familia"] == "abstrato" and c["id"] not in usados:
            return {"cena": c, "pontos": 0, "motivos": ["fallback"]}, ranking[:topo]
    return None, ranking[:topo]


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


PREFIXO = "channels/channels_youtube/treasures_charlesspurgeon"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texto", help="casa um texto avulso")
    ap.add_argument("--sermao", help="casa todos os clipes minerados deste sermão")
    ap.add_argument("--gravar", action="store_true", help="escreve a âncora no clips_meta.json do R2")
    args = ap.parse_args()

    cenas = carregar_catalogo()

    if args.texto:
        r, topo = escolher(args.texto, cenas)
        print(f"\n🎯 {r['cena']['nome_pt']}  ({r['cena']['id']}, {r['cena']['familia']})")
        print(f"   {r['cena']['significado']}")
        print(f"   pontos={r['pontos']}  motivos={r['motivos']}")
        print("\n   outras opções:")
        for o in topo[1:]:
            print(f"     {o['pontos']:>5}  {o['cena']['nome_pt']:26} {o['motivos'][:2]}")
        return

    if not args.sermao:
        sys.exit("informe --texto ou --sermao")

    cli = s3()
    nnnn = f"{int(args.sermao):04d}"
    res = cli.list_objects_v2(Bucket="mananciall", Prefix=f"{PREFIXO}/{nnnn}", MaxKeys=100)
    keys = [o["Key"] for o in res.get("Contents", [])]
    if not keys:
        sys.exit(f"❌ sermão {nnnn} não achado")
    pasta = keys[0].rsplit("/", 1)[0]
    chave = f"{pasta}/clips_meta.json"
    meta = json.loads(cli.get_object(Bucket="mananciall", Key=chave)["Body"].read())

    usados = set()
    print(f"\n📖 {meta.get('title', nnnn)}\n")
    for i, clip in enumerate(meta.get("clips", []), 1):
        r, topo = escolher(clip["text"], cenas, usados)
        if not r:
            print(f"  {i}. (sem âncora disponível)"); continue
        usados.add(r["cena"]["id"])
        clip["ancora"] = {"id": r["cena"]["id"], "familia": r["cena"]["familia"],
                          "pontos": r["pontos"], "motivos": r["motivos"][:4]}
        print(f"  {i}. \"{clip['hook_text']}\"")
        print(f"     → {r['cena']['nome_pt']:24} ({r['pontos']} pts) {r['motivos'][:3]}")

    if args.gravar:
        cli.put_object(Bucket="mananciall", Key=chave,
                       Body=json.dumps(meta, ensure_ascii=False, indent=2).encode(),
                       ContentType="application/json")
        print(f"\n✅ âncoras gravadas em {chave}")
    else:
        print("\n(sem --gravar: nada foi escrito)")


if __name__ == "__main__":
    main()
