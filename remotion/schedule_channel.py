#!/usr/bin/env python3
"""
schedule_channel.py — O AGENDADOR do canal (set-and-forget).

Mantém um buffer de vídeos JÁ AGENDADOS à frente. O YouTube publica sozinho no calendário.
Roda 1x/dia (cron). Cada run: preenche os slots do calendário até o horizonte, dos vídeos
que já estão renderizados (no R2), respeitando a cota de upload do YouTube.

CALENDÁRIO (decidido 25/07):
  - Semanas 1-2 (dias 0-13): 1/dia às 12:00 UTC (~08:00 ET)
  - Dia 14 em diante: 2/dia às 12:00 e 23:00 UTC (~08:00 e ~19:00 ET)
  - Ordem: sequencial (0001, 0002, 0003...)

Estado no R2: schedule/spurgeon_schedule.json  (channel_start + o que já foi agendado).

Uso (na VPS):
  python3 schedule_channel.py --dry-run     # mostra o calendário, não agenda
  python3 schedule_channel.py               # agenda o que falta (respeitando cota)
"""
import os
import sys
import json
import argparse
import datetime as dt
import subprocess
import urllib.request

import canais

HERE = os.path.dirname(os.path.abspath(__file__))

# Preenchidos em main() a partir de canais.get(--canal). Ficam como globais
# porque as funções auxiliares abaixo já os usavam assim quando eram constantes.
C = None
BUCKET = STATE_KEY = CHANNEL_PREFIX = RENDERS_PREFIX = None
EXPECTED_CHANNEL_ID = None
CTA_ASSET_KEYS = []


def aplicar_canal(slug=None):
    """Carrega a config do canal e publica nas globais que a esteira usa."""
    global C, BUCKET, STATE_KEY, CHANNEL_PREFIX, RENDERS_PREFIX
    global EXPECTED_CHANNEL_ID, CTA_ASSET_KEYS, UM_POR_DIA, WARMUP_DAYS
    global MORNING_UTC, EVENING_UTC, BUFFER_DAYS, MAX_UPLOADS_PER_RUN
    C = canais.get(slug)
    BUCKET = C["bucket"]
    STATE_KEY = C["state_key"]
    CHANNEL_PREFIX = C["prefix"]
    RENDERS_PREFIX = C["renders_prefix"]
    EXPECTED_CHANNEL_ID = C["youtube_channel_id"]
    CTA_ASSET_KEYS = [f"{CHANNEL_PREFIX}/{k}" for k in C["cta_assets"]]
    UM_POR_DIA = C["um_por_dia"]
    WARMUP_DAYS = C["warmup_days"]
    MORNING_UTC = C["morning_utc"]
    EVENING_UTC = C["evening_utc"]
    BUFFER_DAYS = C["buffer_days"]
    MAX_UPLOADS_PER_RUN = C["max_uploads_per_run"]
    return C

# Cadência (1/dia, horários, buffer, cota por run) vem de canais.py via
# aplicar_canal(). Decisão do Gabriel em 04/08: "um por dia, sem desespero".
# O modo 2/dia continua vivo: é só pôr "um_por_dia": False na config do canal.

# vídeos já subidos manualmente (privados) — o agendador só define o publishAt deles.
# Vazio: os antigos foram deletados (troca de CTA em 28/07); tudo re-sobe fresco via publish_sermon.
SEEDED = {}


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
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"], aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def yt_token(env):
    import urllib.parse
    cid_, secret_, refresh_ = canais.creds_youtube(C, env)
    data = urllib.parse.urlencode({
        "client_id": cid_, "client_secret": secret_,
        "refresh_token": refresh_, "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        token = json.loads(r.read())["access_token"]
    assert_canal_certo(token)
    return token


# ⚠️ INCIDENTE 11/08/2026 — o que este guardião existe pra impedir:
# a re-auth de 07/08 foi feita na conta pessoal do Gabriel em vez do canal do
# projeto. O token renovava, a API respondia 200, tudo "funcionava" — e 5 vídeos
# foram parar públicos no canal PESSOAL enquanto o canal do projeto ficava parado
# há 8 dias. Token válido não prova canal certo. Agora prova.
# O ID esperado vem de canais.py (campo `youtube_channel_id`).


def assert_canal_certo(token):
    """Aborta se o token autenticado não for o do canal deste script."""
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
        headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=40) as r:
        itens = json.loads(r.read()).get("items", [])
    if not EXPECTED_CHANNEL_ID:
        raise SystemExit(
            f"❌ ABORTADO: canal {C['slug']!r} sem `youtube_channel_id` em canais.py.\n"
            f"   Crie o canal, rode auth_youtube.py nele e preencha o ID.")
    if not itens:
        raise SystemExit("❌ ABORTADO: o token não devolveu canal nenhum.")
    cid = itens[0]["id"]
    titulo = itens[0]["snippet"]["title"]
    if cid != EXPECTED_CHANNEL_ID:
        raise SystemExit(
            f"❌ ABORTADO: token autenticado no canal ERRADO.\n"
            f"   esperado: {EXPECTED_CHANNEL_ID}\n"
            f"   recebido: {cid} ({titulo})\n"
            f"   Rode auth_youtube.py e escolha o canal do projeto.")
    print(f"🔐 canal confirmado: {titulo} ({cid})")


def slot_datetime(i, channel_start):
    """publishAt (UTC) do i-ésimo vídeo (0-indexed) segundo o calendário."""
    if UM_POR_DIA:
        day, hour = i, MORNING_UTC
    elif i < WARMUP_DAYS:
        day, hour = i, MORNING_UTC
    else:
        j = i - WARMUP_DAYS
        day, hour = WARMUP_DAYS + j // 2, (MORNING_UTC if j % 2 == 0 else EVENING_UTC)
    d = channel_start + dt.timedelta(days=day)
    return dt.datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=dt.timezone.utc)


def list_ready_sermons(s3):
    """Sermões prontos pra render/publicar (têm sermão+transcrição+copy+hook+outro), em ordem."""
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
    import re
    folders = {}
    for k in keys:
        m = re.match(rf"{CHANNEL_PREFIX}/(\d[\d-]*)_-_[^/]+/(.+)$", k)
        if m:
            folders.setdefault(m.group(1)[:4], set()).add(m.group(2))
    def ok(f):
        has = lambda rx: any(__import__("re").match(rx, x) for x in f)
        return (has(r"sermon_\d+\.(wav|mp3)$") and "transcript.json" in f and "marketing_meta.json" in f
                and has(r"hook\.(wav|mp3)$") and "hook.json" in f
                and has(r"cta_narration\.(wav|mp3)$") and "cta_narration.json" in f)
    return sorted(n for n, f in folders.items() if ok(f))


def video_rendered(s3, nnnn):
    try:
        s3.head_object(Bucket=BUCKET, Key=f"{RENDERS_PREFIX}/{nnnn}.mp4")
        return True
    except Exception:
        return False


# CTAs/áudios fixos que ficam EMBUTIDOS no vídeo. Se um deles muda no R2, todo
# render feito ANTES dessa troca fica velho (voz/fala desatualizada) e precisa refazer.
# (a lista concreta vem de canais.py e é montada em aplicar_canal())


def assets_cutoff(s3):
    """LastModified mais recente entre os CTAs fixos. Render mais antigo que isso = velho."""
    latest = None
    for k in CTA_ASSET_KEYS:
        try:
            lm = s3.head_object(Bucket=BUCKET, Key=k)["LastModified"]
            if latest is None or lm > latest:
                latest = lm
        except Exception:
            pass
    return latest


def video_fresh(s3, nnnn, cutoff):
    """True só se o mp4 existe E é mais novo que os CTAs fixos (não precisa refazer)."""
    try:
        lm = s3.head_object(Bucket=BUCKET, Key=f"{RENDERS_PREFIX}/{nnnn}.mp4")["LastModified"]
    except Exception:
        return False
    return cutoff is None or lm >= cutoff


def schedule_existing(env, video_id, publish_at, token):
    """Só define o publishAt de um vídeo já subido (privado → agendado)."""
    body = json.dumps({"id": video_id, "status": {"privacyStatus": "private",
                       "publishAt": publish_at, "selfDeclaredMadeForKids": False}}).encode()
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status",
                                 data=body, method="PUT",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=40).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=None)
    canais.add_arg_canal(ap)
    args = ap.parse_args()

    # tem que vir ANTES de qualquer uso das globais (BUCKET, STATE_KEY, cota...)
    aplicar_canal(args.canal)
    if args.max is None:
        args.max = MAX_UPLOADS_PER_RUN
    print(f"🏷️  canal: {C['slug']} ({C['nome']})")

    env = load_env()
    s3 = s3c(env)

    # estado
    try:
        state = json.loads(s3.get_object(Bucket=BUCKET, Key=STATE_KEY)["Body"].read())
    except Exception:
        state = {}
    if "channel_start" not in state:
        # primeiro slot = amanhã (dá buffer)
        state["channel_start"] = (dt.date.today() + dt.timedelta(days=1)).isoformat()
    if "scheduled" not in state:
        state["scheduled"] = {}   # sermao -> {videoId, publishAt}
    channel_start = dt.date.fromisoformat(state["channel_start"])

    ready = list_ready_sermons(s3)
    now = dt.datetime.now(dt.timezone.utc)
    horizon = now + dt.timedelta(days=BUFFER_DAYS)

    print(f"📅 channel_start={channel_start} | sermões prontos: {len(ready)} | horizonte: {horizon.date()}")
    print(f"   já agendados: {len(state['scheduled'])}\n")

    cutoff = assets_cutoff(s3)   # renders mais antigos que os CTAs fixos = velhos, não sobem
    token = None if args.dry_run else yt_token(env)
    uploads = 0
    to_render = []

    # ── REBASE DO CALENDÁRIO ────────────────────────────────────────────────
    # MINA (04/08/2026): a versão antiga jogava TODO slot vencido em `now + 2h`.
    # Depois da parada de 6 dias (token do YouTube expirado), 3 vídeos caíram no
    # MESMO minuto. Remendar item a item não resolve: o atrasado colide com o
    # slot futuro de quem vem depois.
    # Conserto: desloca a régua inteira pra que o PRIMEIRO não agendado caia
    # amanhã, e o resto siga 1/dia sem buraco nem empilhamento.
    i0 = next((i for i, n in enumerate(ready) if n not in state["scheduled"]), None)
    if i0 is not None:
        # Próximo slot de 12:00 UTC ainda alcançável (2h de folga pro upload).
        # MINA (10/08): mirar sempre em "amanhã" furava um dia inteiro quando o
        # cron das 06:00 rodava e o slot das 12:00 do MESMO dia ainda dava tempo.
        base = now + dt.timedelta(hours=2)
        pd = base.date() if base.hour < MORNING_UTC else (base + dt.timedelta(days=1)).date()
        primeiro = dt.datetime(pd.year, pd.month, pd.day,
                               MORNING_UTC, 0, 0, tzinfo=dt.timezone.utc)
        if slot_datetime(i0, channel_start) < primeiro:
            channel_start = (primeiro - dt.timedelta(days=i0)).date()
            # MINA (10/08): PERSISTIR o rebase. A 1ª versão só mexia na variável
            # local; o run seguinte do cron recarregava o channel_start velho do
            # R2 e recalculava de outra base → datas duplicadas (2 vídeos no
            # mesmo dia) e dias sem vídeo nenhum.
            state["channel_start"] = channel_start.isoformat()
            horizon = now + dt.timedelta(days=BUFFER_DAYS)
            print(f"   ↩️  calendário rebaseado: {ready[i0]} passa a sair "
                  f"{primeiro.date()}, 1/dia a partir dali (persistido)")

    for i, nnnn in enumerate(ready):
        when = slot_datetime(i, channel_start)
        if when > horizon:
            break                      # além do buffer — fica pra próximo run
        if nnnn in state["scheduled"]:
            continue                   # já agendado
        # Slot no passado não deveria mais existir (o rebase acima cuida disso).
        # Se acontecer, PULA em vez de empurrar pra `now`: empurrar era justamente
        # o que empilhava vários vídeos no mesmo minuto. Melhor sair um dia depois
        # do que sair três de uma vez.
        if when < now:
            print(f"  ⏭️  {nnnn} → slot {when:%Y-%m-%d %H:%M} no passado, pulando (rebase pega no próximo run)")
            continue
        pa = when.strftime("%Y-%m-%dT%H:%M:%SZ")

        # já existe vídeo subido (seed) → só agenda
        if nnnn in SEEDED:
            print(f"  🗓️  {nnnn} (já subido) → {pa}")
            if not args.dry_run:
                schedule_existing(env, SEEDED[nnnn], pa, token)
                state["scheduled"][nnnn] = {"videoId": SEEDED[nnnn], "publishAt": pa}
            continue

        # precisa estar renderizado E fresco (mp4 mais novo que os CTAs fixos)
        if not video_fresh(s3, nnnn, cutoff):
            to_render.append(nnnn)
            print(f"  ⏳ {nnnn} → {pa} (SEM RENDER FRESCO — pula neste run)")
            continue

        if uploads >= args.max:
            print(f"  ⛔ {nnnn} → {pa} (cota do run atingida, fica pro próximo)")
            continue

        print(f"  ⬆️  {nnnn} → agenda pra {pa}")
        if not args.dry_run:
            r = subprocess.run(
                ["docker", "run", "--rm", "--env-file", "/srv/factorio/.env",
                 "-v", "/srv/factorio/data/public:/app/public",
                 "-v", "/srv/factorio/data/hybrid:/app/_hybrid",
                 "-v", "/app/_factorio/remotion/publish_sermon.py:/app/publish_sermon.py",
                 "-v", "/app/_factorio/remotion/publish_youtube.py:/app/publish_youtube.py",
                 # MINA: canais.py também precisa entrar no container, senão o
                 # publish_sermon lá dentro cai no default e publica no canal errado.
                 "-v", "/app/_factorio/remotion/canais.py:/app/canais.py",
                 "factorio-render:v5", "python3", "-u", "publish_sermon.py",
                 "--canal", C["slug"],
                 "--sermon", str(int(nnnn)), "--publish-at", pa],
                capture_output=True, text=True)
            out = r.stdout + r.stderr
            # extrai o videoId (11 chars) — regex evita colar lixo do JSON (ex: VID"})
            import re as _re
            vid = ""
            for m in _re.finditer(r"youtu\.be/([A-Za-z0-9_-]{11})", out):
                vid = m.group(1)
            if r.returncode == 0 and vid:
                state["scheduled"][nnnn] = {"videoId": vid, "publishAt": pa}
                uploads += 1
                print(f"     ✅ https://youtu.be/{vid}")
            else:
                print(f"     ❌ falhou: {out[-300:]}")

    if not args.dry_run:
        s3.put_object(Bucket=BUCKET, Key=STATE_KEY,
                      Body=json.dumps(state, indent=2).encode(), ContentType="application/json")

    print(f"\n🏁 agendados neste run: {uploads} | total agendado: {len(state['scheduled'])}")
    if to_render:
        print(f"⚠️  precisam renderizar (rode o batch render): {' '.join(to_render[:20])}")


if __name__ == "__main__":
    main()
