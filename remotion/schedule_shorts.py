#!/usr/bin/env python3
"""
schedule_shorts.py — o agendador de SHORTS (1/dia, set-and-forget).

Irmão do `schedule_channel.py`, que faz o mesmo pros vídeos longos. Mantém um
buffer de shorts já agendados à frente; o YouTube publica sozinho no calendário.

## A fila

673 shorts já minerados (160 sermões × ~4,2 clipes). A ordem é a do sermão e,
dentro dele, a NOTA que o minerador deu: o clipe de nota 10 do sermão 1 sai
antes do de nota 7. Assim o canal começa pelo melhor material de cada sermão em
vez de queimar os bons no fim.

## Por que renderiza aqui e não antes

Renderizar os 673 de uma vez seria ~2 dias de máquina pra um material que só
começa a sair daqui a dois anos. O agendador renderiza só o que vai publicar,
e o resultado fica no R2 pra não refazer.

## As minas herdadas do agendador dos longos (não repetir)

  - REBASE DO CALENDÁRIO: se o cron para alguns dias (token expirado, por
    exemplo), jogar todo slot vencido em "agora+2h" empilha vários no mesmo
    minuto. A régua inteira desloca pro primeiro não agendado cair amanhã.
  - PERSISTIR O REBASE: se a nova base só existir na variável local, o run
    seguinte recarrega a antiga do R2 e recalcula de outro ponto — dá dia com
    dois vídeos e dia com nenhum.
  - CONFERIR O CANAL antes de subir: token certo, canal errado publica no lugar
    errado e não tem desfazer.

Uso (na VPS, 1x/dia por cron):
  python3 schedule_shorts.py --dry-run
  python3 schedule_shorts.py --confirm
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

import canais

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "mananciall"
HORA_UTC = 15                 # ~11:00 no leste dos EUA; shorts rendem mais de dia
BUFFER_DIAS = 5               # quantos dias à frente manter agendados
MAX_POR_RUN = 3               # teto de cota do YouTube por execução


def load_env():
    env = dict(os.environ)
    for p in (os.path.join(HERE, "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="ignore"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def s3c(env):
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def fila(s3, C):
    """Todos os shorts minerados, na ordem de publicação.

    Ordem: sermão crescente e, dentro do sermão, maior nota primeiro.
    """
    pag = s3.get_paginator("list_objects_v2")
    metas = []
    for pg in pag.paginate(Bucket=BUCKET, Prefix=C["prefix"] + "/"):
        for o in pg.get("Contents", []):
            if o["Key"].endswith("clips_meta.json"):
                metas.append(o["Key"])
    itens = []
    for k in sorted(metas):
        pasta = k.split("/")[3]
        nnnn = pasta.split("_")[0]
        m = json.loads(s3.get_object(Bucket=BUCKET, Key=k)["Body"].read())
        clips = m.get("clips", [])
        # guarda o índice ORIGINAL: é ele que o render_short usa (--clip N)
        ordenados = sorted(enumerate(clips, 1),
                           key=lambda p: -(p[1].get("score") or 0))
        for idx, c in ordenados:
            itens.append({
                "id": f"{nnnn}_c{idx:02d}",
                "sermao": nnnn, "clip": idx,
                "titulo_sermao": m.get("title", pasta),
                "hook": c.get("hook_text", ""),
                "score": c.get("score"),
                "dur": round((c["end_ms"] - c["start_ms"]) / 1000),
            })
    return itens


def slot(i, inicio):
    d = inicio + dt.timedelta(days=i)
    return dt.datetime(d.year, d.month, d.day, HORA_UTC, 0, 0, tzinfo=dt.timezone.utc)


def ja_renderizado(s3, C, tag):
    chave = f"{C['renders_prefix']}_shorts/{tag}.mp4"
    try:
        s3.head_object(Bucket=BUCKET, Key=chave)
        return chave
    except Exception:
        return None


def renderizar(C, item):
    """Chama o montador de shorts (cenas + trilha) e devolve o mp4 local."""
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "..", "scripts", "ancoras", "montar_short.py"),
         "--sermao", str(int(item["sermao"])), "--clip", str(item["clip"]),
         "--fonte", "video"],
        capture_output=True, text=True, cwd=os.path.join(HERE, ".."))
    if r.returncode != 0:
        print(f"   ❌ render falhou: {(r.stderr or r.stdout)[-400:]}")
        return None
    saida = os.path.join(HERE, "out", "shorts",
                         f"{item['sermao']}_c{item['clip']:02d}_cenas_video.mp4")
    return saida if os.path.exists(saida) else None


def texto_publicacao(C, item):
    """Título, descrição e tags. #Shorts no título é o que faz o YouTube
    classificar como Short mesmo antes de ler o formato do arquivo."""
    hook = (item["hook"] or "").strip().rstrip(".")
    pregador = C.get("pregador", "")
    titulo = f"{hook} — {pregador} #shorts"[:100]
    desc = (f"{hook}\n\n"
            f"Trecho do sermão \"{item['titulo_sermao']}\", de {pregador}.\n\n"
            f"Sermão completo no canal.\n\n"
            f"#{pregador.replace(' ', '')} #sermon #christian #faith #shorts")
    tags = C.get("tags", "")
    return titulo, desc, tags


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--confirm", action="store_true",
                    help="OBRIGATÓRIO pra publicar de verdade (é irreversível)")
    ap.add_argument("--max", type=int, default=MAX_POR_RUN)
    args = ap.parse_args()

    C = canais.get(args.canal)
    chave_estado = f"schedule/{C['slug']}_shorts_schedule.json"
    print(f"🎬 shorts de {C['nome']}")

    env = load_env()
    s3 = s3c(env)

    try:
        estado = json.loads(s3.get_object(Bucket=BUCKET, Key=chave_estado)["Body"].read())
    except Exception:
        estado = {}
    estado.setdefault("agendados", {})
    if "inicio" not in estado:
        estado["inicio"] = (dt.date.today() + dt.timedelta(days=1)).isoformat()
    inicio = dt.date.fromisoformat(estado["inicio"])

    itens = fila(s3, C)
    agora = dt.datetime.now(dt.timezone.utc)
    horizonte = agora + dt.timedelta(days=BUFFER_DIAS)
    print(f"📅 início={inicio} · fila: {len(itens)} shorts · "
          f"agendados: {len(estado['agendados'])} · horizonte: {horizonte.date()}")

    # ── rebase da régua (mina herdada do agendador dos longos) ──────────────
    i0 = next((i for i, it in enumerate(itens) if it["id"] not in estado["agendados"]), None)
    if i0 is None:
        print("🏁 fila inteira já agendada")
        return
    base = agora + dt.timedelta(hours=2)
    pd = base.date() if base.hour < HORA_UTC else (base + dt.timedelta(days=1)).date()
    primeiro = dt.datetime(pd.year, pd.month, pd.day, HORA_UTC, 0, 0, tzinfo=dt.timezone.utc)
    if slot(i0, inicio) < primeiro:
        inicio = (primeiro - dt.timedelta(days=i0)).date()
        estado["inicio"] = inicio.isoformat()     # PERSISTIR, senão o próximo run recalcula
        print(f"   ↩️  calendário rebaseado: {itens[i0]['id']} passa a sair {primeiro.date()}")

    feitos = 0
    for i, it in enumerate(itens):
        if it["id"] in estado["agendados"]:
            continue
        quando = slot(i, inicio)
        if quando > horizonte:
            break
        if feitos >= args.max:
            print(f"   ⏸️  teto de {args.max} por execução atingido")
            break

        titulo, desc, tags = texto_publicacao(C, it)
        print(f"\n▶️  {it['id']} · nota {it['score']} · {it['dur']}s · {quando:%Y-%m-%d %H:%M} UTC")
        print(f"   \"{titulo}\"")

        if args.dry_run:
            feitos += 1
            continue
        if not args.confirm:
            sys.exit("❌ publicar é irreversível: rode com --confirm (ou --dry-run)")

        chave = ja_renderizado(s3, C, f"{it['sermao']}_c{it['clip']:02d}_cenas_video")
        if chave:
            local = os.path.join(HERE, "out", "shorts", os.path.basename(chave))
            if not os.path.exists(local):
                os.makedirs(os.path.dirname(local), exist_ok=True)
                s3.download_file(BUCKET, chave, local)
            print("   ♻️  já renderizado, reusando do R2")
        else:
            print("   🎞️  renderizando ...")
            local = renderizar(C, it)
            if not local:
                continue
            s3.upload_file(local, BUCKET,
                           f"{C['renders_prefix']}_shorts/{os.path.basename(local)}",
                           ExtraArgs={"ContentType": "video/mp4"})

        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "publish_youtube.py"),
             "--canal", C["slug"], "--video", local, "--title", titulo,
             "--description", desc, "--tags", tags,
             "--publish-at", quando.strftime("%Y-%m-%dT%H:%M:%SZ"), "--confirm"],
            capture_output=True, text=True, cwd=HERE)
        if r.returncode != 0:
            print(f"   ❌ upload falhou: {(r.stderr or r.stdout)[-400:]}")
            continue
        vid = ""
        for linha in (r.stdout or "").splitlines():
            if "videoId" in linha or "youtu.be" in linha:
                vid = linha.strip()
        estado["agendados"][it["id"]] = {"publishAt": quando.isoformat(), "saida": vid}
        s3.put_object(Bucket=BUCKET, Key=chave_estado,
                      Body=json.dumps(estado, ensure_ascii=False, indent=1).encode(),
                      ContentType="application/json")
        feitos += 1
        print(f"   ✅ agendado · {vid}")

    if args.dry_run:
        print(f"\n(dry-run) {feitos} short(s) entrariam no calendário")
    else:
        print(f"\n🏁 {feitos} short(s) agendados · "
              f"{len(itens) - len(estado['agendados'])} ainda na fila")


if __name__ == "__main__":
    main()
