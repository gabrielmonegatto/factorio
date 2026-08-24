#!/usr/bin/env python3
"""
mine_clips.py — Estágio 1 da fábrica de shorts: minerar momentos do sermão.

Lê o transcript.json (word-level) do R2, agrupa em FRASES numeradas com timestamps,
e pede pro LLM escolher 3-5 trechos candidatos a short. O corte é SEMPRE em
fronteira de frase (o LLM devolve índices de frase, nunca timestamps — timestamps
são calculados aqui, do word-level, sem alucinação possível).

Critérios no prompt (de 12_FABRICA_SHORTS.md):
  - autocontido: entende-se sem o resto do sermão
  - arco completo: gancho → desenvolvimento → fecho
  - gancho verbal nos primeiros 3 segundos
  - 30 a 60 segundos
  - frase memorável e aplicável hoje > doutrina abstrata

Saída: clips_meta.json na pasta do sermão no R2 (e stdout).

Uso:
  python mine_clips.py --sermon 1              # gera e sobe pro R2
  python mine_clips.py --sermon 1 --dry-run    # só mostra
  python mine_clips.py --sermon 1 --force      # regera mesmo se já existir
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

BUCKET = "mananciall"
CHANNEL_PREFIX = None      # preenchido em main() a partir de canais.get()
# 🥊 Escolhido por páreo medido em 23/08 (6 modelos × 3 sermões, script em
# scripts/ancoras/pareo_mineradores.py). O gemini-2.5-flash que estava aqui foi
# o PIOR dos seis: 11/15 de índice válido (devolvia faixa fora ou sobreposta) e
# só 9/15 de hook fiel — inventava hook com palavra que não está no trecho.
# O deepseek-v4-flash deu 13/13 de índice, 13/13 de hook fiel, foi o mais rápido
# e é 12x mais barato (US$0,12 contra US$1,43 pra minerar o acervo inteiro).
# No olho também ganhou: escolheu a anedota concreta onde os outros pegaram
# doutrina abstrata, que é o que a nossa própria instrução manda evitar.
MODEL = "deepseek/deepseek-v4-flash"
HERE = os.path.dirname(os.path.abspath(__file__))

MIN_S, MAX_S = 28.0, 62.0   # duração aceitável do clipe (com folga de 2s nas pontas)
MIN_CLIPS, MAX_CLIPS = 3, 5

SYSTEM_MOLDE = """You are the clip miner for "{canal}", a channel of narrated
{pregador} sermons. Your job: find the 3-5 BEST self-contained moments to become
vertical shorts (30-60s) for YouTube Shorts / TikTok / Reels.

You receive the sermon as NUMBERED SENTENCES with start times. Return STRICT JSON:

{"clips": [
  {
    "start_sentence": <int>,          // first sentence index (inclusive)
    "end_sentence": <int>,            // last sentence index (inclusive)
    "hook_text": "<max 6 words>",     // on-screen hook card, ALL CAPS feel, tension/curiosity
    "score": <1-10>,                  // relative within THIS sermon
    "reason": "<one short line>"
  }, ...
]}

Selection rules, all mandatory:
- SELF-CONTAINED: the excerpt must make full sense with zero context.
- COMPLETE ARC: it opens a thought and lands it. Never cut mid-argument.
- HOOK IN 3s: the FIRST sentence must grab (question, bold claim, direct address,
  vivid image). If a great passage starts weak, start one sentence later.
- 30-60 SECONDS total (you see sentence start times — do the math).
- What performs in this niche: a memorable, quotable line applicable to the
  viewer's life TODAY (fear, anxiety, guilt, hope, prayer, suffering, purpose)
  beats abstract doctrine. {pregador} is aphoristic — find the aphorisms.
- Prefer second-person or universal moments over historical references.
- hook_text: max 6 words, tension or curiosity, TRUE to the excerpt, never a lie.
- Clips must NOT overlap.
Return 3 to 5 clips, best first."""


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
        sys.exit(f"❌ sermão {nnnn} não encontrado no R2")
    return keys[0].rsplit("/", 1)[0]


def build_sentences(words):
    """Agrupa o word-level em frases. Fronteira = palavra terminada em .!?…"""
    sentences, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?…][\"')\]]?$", w["text"]):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    return [{
        "i": i,
        "start": s[0]["start"],
        "end": s[-1]["end"],
        "text": " ".join(w["text"] for w in s),
    } for i, s in enumerate(sentences)]


def llm(env, system, title, sentences):
    lines = [f"[{s['i']}] t={s['start']/1000:.1f}s  {s['text']}" for s in sentences]
    body = json.dumps({
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Sermon: {title}\n\n" + "\n".join(lines)},
        ],
    }).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=body, method="POST",
                                 headers={"Authorization": f"Bearer {env['OPENROUTER_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read())
    return json.loads(out["choices"][0]["message"]["content"])


def materialize(clips_raw, sentences, words):
    """Converte índices de frase em timestamps reais + subset word-level do clipe."""
    out = []
    n = len(sentences)
    for c in clips_raw:
        try:
            a, b = int(c["start_sentence"]), int(c["end_sentence"])
        except (KeyError, ValueError, TypeError):
            continue
        if not (0 <= a <= b < n):
            continue
        # reparo determinístico: o LLM erra conta de duração; ajusta o FIM do
        # clipe (nunca o gancho) em fronteira de frase até caber em 30-60s
        def dur_s(x, y):
            return (sentences[y]["end"] - sentences[x]["start"]) / 1000.0
        while dur_s(a, b) < MIN_S and b + 1 < n and dur_s(a, b + 1) <= MAX_S:
            b += 1
        while dur_s(a, b) > MAX_S and b > a and dur_s(a, b - 1) >= MIN_S:
            b -= 1
        start_ms = sentences[a]["start"]
        end_ms = sentences[b]["end"]
        dur = (end_ms - start_ms) / 1000.0
        if not (MIN_S <= dur <= MAX_S):
            continue
        clip_words = [
            {"text": w["text"], "start": w["start"] - start_ms, "end": w["end"] - start_ms}
            for w in words if start_ms <= w["start"] and w["end"] <= end_ms
        ]
        out.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_s": round(dur, 1),
            "hook_text": (c.get("hook_text") or "").strip(),
            "score": c.get("score"),
            "reason": c.get("reason", ""),
            "text": " ".join(s["text"] for s in sentences[a:b + 1]),
            "words": clip_words,
        })
    # sem sobreposição: ordena por score desc e descarta quem colide com um melhor
    out.sort(key=lambda c: -(c["score"] or 0))
    kept = []
    for c in out:
        if all(c["end_ms"] <= k["start_ms"] or c["start_ms"] >= k["end_ms"] for k in kept):
            kept.append(c)
    return kept[:MAX_CLIPS]


def process(env, s3, system, nnnn, dry=False, force=False):
    folder = find_folder(s3, nnnn)
    key = f"{folder}/clips_meta.json"
    if not force:
        try:
            cur = json.loads(s3.get_object(Bucket=BUCKET, Key=key)["Body"].read())
            if cur.get("clips"):
                print(f"⏭️  {nnnn} já tem {len(cur['clips'])} clipes minerados (use --force)")
                return cur
        except Exception:
            pass

    transcript = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{folder}/transcript.json")["Body"].read())
    words = transcript.get("words") or sys.exit(f"❌ {nnnn} sem word-level")
    sentences = build_sentences(words)
    title = transcript.get("title", nnnn)
    print(f"⛏️  minerando {nnnn} — {title} ({len(sentences)} frases)")

    raw = llm(env, system, title, sentences).get("clips", [])
    clips = materialize(raw, sentences, words)
    if len(clips) < MIN_CLIPS:
        print(f"⚠️  só {len(clips)} clipes válidos (LLM propôs {len(raw)}; o resto caiu na validação de duração/índice)")

    meta = {"sermon": nnnn, "title": title, "model": MODEL, "clips": clips}
    for i, c in enumerate(clips, 1):
        print(f"  {i}. [{c['start_ms']/1000:.0f}s→{c['end_ms']/1000:.0f}s] {c['duration_s']}s "
              f"score={c['score']} \"{c['hook_text']}\" — {c['reason']}")

    if not dry:
        s3.put_object(Bucket=BUCKET, Key=key,
                      Body=json.dumps(meta, ensure_ascii=False, indent=2).encode(),
                      ContentType="application/json")
        print(f"✅ salvo -> {key}")
    return meta


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--sermon", help="número do sermão")
    ap.add_argument("--todos", action="store_true",
                    help="minera TODO sermão com transcrição e sem clips_meta")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    global CHANNEL_PREFIX
    C = canais.get(args.canal)
    CHANNEL_PREFIX = C["prefix"]
    if not C.get("pregador"):
        sys.exit(f"❌ canal {C['slug']!r} sem `pregador`: este minerador corta SERMÃO.")
    # 🧨 NÃO usar .format() aqui: o molde é quase todo JSON, e o Python lê cada
    # `{"clips"` como campo a substituir — estoura KeyError e o minerador MORRE
    # em toda execução. Foi o que aconteceu quando o molde virou multi-canal: o
    # script parou de rodar e ninguém viu, porque nada tenta minerar sozinho.
    # Só 2 dos 212 sermões tinham clipes por causa disso (achado 23/08).
    # Substituição literal não se importa com as chaves do JSON.
    system = SYSTEM_MOLDE
    for campo, valor in (("canal", C["nome"]), ("pregador", C["pregador"])):
        system = system.replace("{" + campo + "}", valor)
    print(f"✂️  garimpando clipes de {C['nome']}")

    env = load_env()
    if not env.get("OPENROUTER_API_KEY"):
        sys.exit("❌ falta OPENROUTER_API_KEY")
    s3 = s3c(env)

    if args.todos:
        # 🧨 Idempotente por construção: pula quem já tem clips_meta. Uma queda no
        # meio de 210 sermões é retomada rodando o mesmo comando de novo.
        pag = s3.get_paginator("list_objects_v2")
        tem_tr, tem_clips = set(), set()
        for pg in pag.paginate(Bucket=BUCKET, Prefix=CHANNEL_PREFIX + "/"):
            for o in pg.get("Contents", []):
                partes = o["Key"].split("/")
                if len(partes) < 5 or partes[3].startswith("_"):
                    continue
                if o["Key"].endswith("transcript.json"):
                    tem_tr.add(partes[3])
                elif o["Key"].endswith("clips_meta.json"):
                    tem_clips.add(partes[3])
        fila = sorted(p for p in tem_tr - tem_clips)
        print(f"📚 {len(tem_tr)} com transcrição · {len(tem_clips)} já minerados · "
              f"{len(fila)} na fila")
        ok = erro = 0
        for i, pasta in enumerate(fila, 1):
            nnnn = pasta.split("_")[0]
            try:
                process(env, s3, system, nnnn, dry=args.dry_run, force=args.force)
                ok += 1
            except SystemExit as e:
                print(f"  ⏭️  {nnnn}: {e}")
                erro += 1
            except Exception as e:
                print(f"  ❌ {nnnn}: {str(e)[:120]}")
                erro += 1
            if i % 10 == 0:
                print(f"  ── {i}/{len(fila)} · {ok} ok · {erro} com problema")
        print("")
        print(f"🏁 {ok} minerados · {erro} com problema")
        return

    if not args.sermon:
        sys.exit("informe --sermon N ou --todos")
    nnnn = f"{int(args.sermon):04d}"
    process(env, s3, system, nnnn, dry=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
