#!/usr/bin/env python3
"""
generate_marketing.py — Gera os textos de marketing de um sermão (a etapa que falta nos 93).

Produz o `marketing_meta.json` com QUATRO campos (antes eram três):
  - marketingTitle : título do vídeo (SEO, contexto completo, ≤70 chars)
  - thumbnailText  : ⚡ NOVO — texto da CAPA, ≤6 palavras, magnético
  - hookText       : narração de abertura (~25s)
  - outroText      : narração de fechamento (~25s)

Por que separar título e thumbnail: são trabalhos DIFERENTES.
O título é lido com calma (SEO, contexto). A thumbnail é vista MINÚSCULA, em 0,5s,
no meio de um feed — precisa de tensão, não de descrição.

Uso:
  python generate_marketing.py --canal moody --sermon 3
  python generate_marketing.py --canal moody --all --dry-run
"""
import os
import re
import sys
import json
import argparse
import urllib.request

import boto3
from botocore.config import Config

import canais

BUCKET = CHANNEL_PREFIX = None      # preenchidos em main() a partir de canais.get()
MODEL = "google/gemini-2.5-flash"
HERE = os.path.dirname(os.path.abspath(__file__))

# ─── O PROMPT ───────────────────────────────────────────────────────────────
# Lição aprendida (22/07): pedir "um título atraente" gera DESCRIÇÃO, não ISCA.
# O modelo precisa dos gatilhos explícitos + exemplos (ele aprende pelo exemplo).
#
# Generalizado em 21/08: o prompt era do Spurgeon do começo ao fim. Rodar ele
# no Moody produziria vídeo do Moody com título assinado "(Charles Spurgeon)",
# que é atribuição falsa, não erro de estilo. Agora canal, pregador e sufixo
# vêm de canais.py; a GRAMÁTICA de copy (visceral, 2ª pessoa, tensão) é a mesma
# porque é ela que define a família Treasures.
SYSTEM_MOLDE = """You write for "{canal}", a YouTube channel of narrated
{pregador} sermons. Your job is to reach into the viewer's PAIN and make them stop —
without ever lying. Be visceral. Speak to the ache, the fear, the longing underneath.

Return STRICT JSON with exactly these FIVE fields:

1. "marketingTitle" — the VIDEO title. Rules, all mandatory:
   • VISCERAL — hit a real human pain or longing (fear, guilt, exhaustion, doubt, loss).
   • Prefer second person ("You", "Your"). Make it feel personal.
   • ALWAYS end with "{sufixo}" — the name pulls those who know him.
   • Under ~70 chars including the suffix.
   GOOD: "The One Truth That Will Never Fail You{sufixo}"
         "Why You Keep Losing Your Peace{sufixo}"
   BAD (dry, descriptive): "Understanding the Immutability of God"

2. "thumbnailText" — the THUMBNAIL text. Hardest field.
   • MAX 6 WORDS. Seen TINY, for half a second.
   • TENSION or CURIOSITY GAP, never a description. Second person when possible.
   • TRUE to the sermon — curiosity with integrity, never clickbait lies.
   • Patterns: accusation "YOU FORGOT HIM AGAIN" · contrast "EVERYTHING CHANGES. HE DOESN'T."
     · superlative "THE SIN GOD HATES MOST" · revelation "THE PRAYER GOD ALWAYS ANSWERS"

3. "videoDescription" — 2 to 3 sentences. A PASSIONATE, visceral invitation.
   • Speak to the viewer's pain, then promise the relief this message brings.
   • End by inviting them to watch / to the link.
   • 🚫 NEVER reveal or hint at the source: do NOT mention "sermon", "original",
     "transcript", "public domain", dates, or that it is old/archived material.
     Write as a living message speaking to them TODAY. (The name is credited in the title.)

4. "hookText" — opening narration, 60-80 words (~25s). Speak TO the listener. Open a
   loop the message closes. Only spoken words, no labels.

5. "outroText" — closing narration, 60-85 words (~25s). Land the core hope, then ask
   for subscribe/like and to scan the QR code (or tap the link) for {pregador}'s books.
   Only spoken words."""


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
        sys.exit(f"❌ sermão {nnnn} não encontrado no R2")
    return keys[0].rsplit("/", 1)[0]


def montar_system(c):
    """Molde -> prompt do canal. Erra alto se o canal não tem pregador."""
    if not c.get("pregador"):
        raise SystemExit(
            f"❌ canal {c['slug']!r} não tem `pregador` em canais.py.\n"
            f"   Este gerador escreve copy de SERMÃO. Canal de narração bíblica\n"
            f"   precisa do prompt dele, não deste.")
    return SYSTEM_MOLDE.format(canal=c["nome"], pregador=c["pregador"],
                               sufixo=c["titulo_sufixo"])


def llm(env, system, sermon_title, transcript_text):
    body = json.dumps({
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Sermon Title: {sermon_title}\n\nTranscript:\n{transcript_text[:14000]}"},
        ],
    }).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=body, method="POST",
                                 headers={"Authorization": f"Bearer {env['OPENROUTER_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read())
    return json.loads(out["choices"][0]["message"]["content"])


def list_pending(s3):
    """Sermões que ainda não têm copy (ou têm copy velho, sem thumbnailText)."""
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

    folders = {}
    for k in keys:
        m = re.match(rf"{CHANNEL_PREFIX}/(\d[\d-]*)_-_[^/]+/(.+)$", k)
        if m:
            folders.setdefault(m.group(1), set()).add(m.group(2))

    pending = []
    for num, files in sorted(folders.items()):
        if "transcript.json" not in files:
            continue  # sem transcrição não dá pra gerar copy
        pending.append(num[:4])
    return pending


def process(env, s3, system, nnnn, dry, force):
    folder = find_folder(s3, nnnn)
    if not force and not dry:
        try:
            cur = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/marketing_meta.json")["Body"].read())
            if cur.get("thumbnailText"):
                print(f"⏭️  {nnnn} já tem copy completo")
                return "skip"
        except Exception:
            pass
    try:
        transcript = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/transcript.json")["Body"].read())
    except Exception:
        print(f"⚠️  {nnnn} sem transcript.json — pulando")
        return "skip"

    meta = llm(env, system, transcript.get("title", nnnn), transcript.get("text", ""))
    tt = (meta.get("thumbnailText") or "").strip()
    flag = " ⚠️>6 palavras" if len(tt.split()) > 6 else ""
    print(f"✅ {nnnn}: \"{tt}\"{flag}")

    if not dry:
        s3.put_object(Bucket=BUCKET, Key=f"{folder}/marketing_meta.json",
                      Body=json.dumps(meta, ensure_ascii=False, indent=2).encode(),
                      ContentType="application/json")
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--sermon", help="número do sermão (ou use --all)")
    ap.add_argument("--all", action="store_true", help="processa todos que faltam")
    ap.add_argument("--limit", type=int, default=0, help="máximo de sermões no modo --all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="regera mesmo se já existir")
    args = ap.parse_args()

    global BUCKET, CHANNEL_PREFIX
    C = canais.get(args.canal)
    BUCKET, CHANNEL_PREFIX = C["bucket"], C["prefix"]
    system = montar_system(C)
    print(f"✍️  copy de {C['nome']} (assina como {C['titulo_sufixo'].strip()})")

    env = load_env()
    if not env.get("OPENROUTER_API_KEY"):
        sys.exit("❌ falta OPENROUTER_API_KEY")

    if args.all:
        s3 = s3c(env)
        pend = list_pending(s3)
        if args.limit:
            pend = pend[:args.limit]
        print(f"📋 {len(pend)} sermões na fila de copy\n")
        stats = {"ok": 0, "skip": 0, "erro": 0}
        for i, n in enumerate(pend, 1):
            try:
                stats[process(env, s3, system, n, args.dry_run, args.force)] += 1
            except Exception as e:
                stats["erro"] += 1
                print(f"❌ {n}: {str(e)[:120]}")
            if i % 10 == 0:
                print(f"   ... {i}/{len(pend)}")
        print(f"\n🏁 gerados={stats['ok']} pulados={stats['skip']} erros={stats['erro']}")
        return

    if not args.sermon:
        sys.exit("informe --sermon N ou --all")
    if not env.get("OPENROUTER_API_KEY"):
        sys.exit("❌ falta OPENROUTER_API_KEY")
    s3 = s3c(env)
    nnnn = f"{int(args.sermon):04d}"
    folder = find_folder(s3, nnnn)

    # já existe (e tem o campo novo)?
    if not args.force and not args.dry_run:
        try:
            cur = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/marketing_meta.json")["Body"].read())
            if cur.get("thumbnailText"):
                print(f"ℹ️  {nnnn} já tem marketing completo. Use --force pra regerar.")
                return
        except Exception:
            pass

    transcript = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/transcript.json")["Body"].read())
    title = transcript.get("title", nnnn)
    print(f"🧠 gerando copy do {nnnn} — {title}")

    meta = llm(env, system, title, transcript.get("text", ""))

    # guarda-corpo: a regra das 6 palavras é a que mais importa
    tt = (meta.get("thumbnailText") or "").strip()
    if len(tt.split()) > 6:
        print(f"⚠️  thumbnailText veio com {len(tt.split())} palavras (limite 6): \"{tt}\"")

    print(json.dumps(meta, indent=2, ensure_ascii=False))

    if args.dry_run:
        print("\n(dry-run — nada gravado)")
        return

    s3.put_object(Bucket=BUCKET, Key=f"{folder}/marketing_meta.json",
                  Body=json.dumps(meta, ensure_ascii=False, indent=2).encode(),
                  ContentType="application/json")
    print(f"\n✅ salvo -> {folder}/marketing_meta.json")


if __name__ == "__main__":
    main()
