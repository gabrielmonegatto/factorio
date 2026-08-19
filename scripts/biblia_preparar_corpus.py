#!/usr/bin/env python3
"""
biblia_preparar_corpus.py — baixa a KJV e fatia em blocos de ~1h pro canal de Bíblia.

Fonte: scrollmapper/bible_databases (KJV 1769, domínio público nos EUA).
66 livros · 1.189 capítulos · ~790.892 palavras · ~94h de áudio a 140 wpm.

## Regras de corte (decididas no doc 10)

1. **Nunca corta capítulo no meio.** A fronteira é sempre fim de capítulo.
2. **Nunca mistura livros num bloco.** Livro curto vira bloco curto; livro longo
   vira "Parte 1, 2, 3...". Misturar Gênesis com Êxodo no mesmo vídeo confunde
   quem procura por livro, que é como essa audiência busca.
3. Alvo de ~60 min. Um capítulo sozinho maior que o alvo vira bloco próprio
   (Salmo 119 é o caso extremo).

## Decisão ainda ABERTA (item A2 do doc 10)

Ler ou não o número do versículo em voz alta. Este script gera o texto SEM os
números (o público de descanso/estudo detesta a interrupção), mas guarda o
intervalo de versículos no meta.json — então dá pra regerar com números sem
baixar nada de novo, se a decisão mudar.

Uso:
  python biblia_preparar_corpus.py --dry-run     # só o plano, não sobe nada
  python biblia_preparar_corpus.py               # fatia e sobe pro R2
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.request

FONTE = "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/KJV.json"
WPM = 140                 # ritmo de narração pausada
ALVO_MIN = 60             # duração alvo por bloco
ALVO_PALAVRAS = WPM * ALVO_MIN


def carregar_env():
    aqui = os.path.dirname(os.path.abspath(__file__))
    env = dict(os.environ)
    for p in (os.path.join(aqui, "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="ignore"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def slug(txt):
    t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def baixar(destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 1_000_000:
        print("ja baixado:", destino, flush=True)
        return
    print("baixando a KJV ...", flush=True)
    urllib.request.urlretrieve(FONTE, destino)
    print("ok:", os.path.getsize(destino), "bytes", flush=True)


def texto_do_capitulo(cap, com_numeros=False):
    """Junta os versos num parágrafo corrido. Sem número, por padrão."""
    partes = []
    for v in cap["verses"]:
        t = " ".join(v["text"].split())
        partes.append(f'{v["verse"]}. {t}' if com_numeros else t)
    return " ".join(partes)


def fatiar(dados, com_numeros=False):
    """Devolve a lista de blocos, cada um contido num único livro."""
    blocos = []
    for livro in dados["books"]:
        nome = livro["name"]
        atual, palavras_atual = [], 0
        pendentes = []
        for cap in livro["chapters"]:
            txt = texto_do_capitulo(cap, com_numeros)
            n = len(txt.split())
            # capítulo que sozinho estoura o alvo vira bloco próprio
            if atual and palavras_atual + n > ALVO_PALAVRAS:
                pendentes.append((atual, palavras_atual))
                atual, palavras_atual = [], 0
            atual.append((cap["chapter"], txt, n))
            palavras_atual += n
        if atual:
            pendentes.append((atual, palavras_atual))

        varias = len(pendentes) > 1
        for i, (caps, pal) in enumerate(pendentes, 1):
            ini, fim = caps[0][0], caps[-1][0]
            titulo = nome if not varias else f"{nome} (Part {i} of {len(pendentes)})"
            blocos.append({
                "livro": nome,
                "parte": i if varias else None,
                "de_partes": len(pendentes) if varias else None,
                "capitulos": [c[0] for c in caps],
                "cap_inicio": ini,
                "cap_fim": fim,
                "titulo": titulo,
                "palavras": pal,
                "minutos_estimados": round(pal / WPM, 1),
                "texto": "\n\n".join(c[1] for c in caps),
            })
    return blocos


def s3c(env):
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--com-numeros", action="store_true",
                    help="lê o número do versículo (decisão A2 ainda aberta)")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "..", "scratch", "kjv.json"))
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.cache)), exist_ok=True)
    baixar(args.cache)
    dados = json.load(open(args.cache, encoding="utf-8"))

    blocos = fatiar(dados, args.com_numeros)
    total_pal = sum(b["palavras"] for b in blocos)
    total_h = total_pal / WPM / 60
    print(f"\n{len(blocos)} blocos | {total_pal:,} palavras | {total_h:.1f}h de audio\n", flush=True)

    curtos = [b for b in blocos if b["minutos_estimados"] < 20]
    longos = [b for b in blocos if b["minutos_estimados"] > 75]
    print(f"blocos < 20min: {len(curtos)} | blocos > 75min: {len(longos)}")
    for b in longos[:5]:
        print(f"   longo: {b['titulo']} = {b['minutos_estimados']}min")

    if args.dry_run:
        print("\n--- primeiros 12 blocos ---")
        for i, b in enumerate(blocos[:12], 1):
            print(f"  {i:04d} {b['titulo']:<34} cap {b['cap_inicio']}-{b['cap_fim']:<4} "
                  f"{b['minutos_estimados']:>5}min")
        print("\n(dry-run: nada foi enviado)")
        return

    env = carregar_env()
    s3 = s3c(env)
    BUCKET = "mananciall"
    PREFIX = "channels/channels_youtube/biblia_kjv"

    manifesto = []
    for i, b in enumerate(blocos, 1):
        nnnn = f"{i:04d}"
        pasta = f"{PREFIX}/{nnnn}_-_{slug(b['titulo'])}"
        s3.put_object(Bucket=BUCKET, Key=f"{pasta}/text.txt",
                      Body=b["texto"].encode("utf-8"),
                      ContentType="text/plain; charset=utf-8")
        meta = {k: v for k, v in b.items() if k != "texto"}
        meta["id"] = nnnn
        meta["com_numeros_de_versiculo"] = args.com_numeros
        s3.put_object(Bucket=BUCKET, Key=f"{pasta}/meta.json",
                      Body=json.dumps(meta, ensure_ascii=False, indent=2).encode(),
                      ContentType="application/json")
        manifesto.append(meta)
        if i % 25 == 0 or i == len(blocos):
            print(f"  {i}/{len(blocos)} enviados", flush=True)

    s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}/manifest.json",
                  Body=json.dumps({"traducao": "KJV (1769), dominio publico",
                                   "fonte": FONTE,
                                   "wpm_assumido": WPM,
                                   "alvo_min": ALVO_MIN,
                                   "com_numeros_de_versiculo": args.com_numeros,
                                   "blocos": len(manifesto),
                                   "palavras": total_pal,
                                   "horas_estimadas": round(total_h, 1),
                                   "itens": manifesto},
                                  ensure_ascii=False, indent=2).encode(),
                  ContentType="application/json")
    print(f"\nPRONTO: {len(manifesto)} blocos no R2 sob {PREFIX}/")


if __name__ == "__main__":
    main()
