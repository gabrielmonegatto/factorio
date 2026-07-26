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

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "mananciall"
STATE_KEY = "schedule/spurgeon_schedule.json"
CHANNEL_PREFIX = "channels/channels_youtube/treasures_charlesspurgeon"

WARMUP_DAYS = 14          # 1/dia nesse período
MORNING_UTC = 12          # ~08:00 ET
EVENING_UTC = 23          # ~19:00 ET
BUFFER_DAYS = 14          # quantos dias à frente manter agendado
MAX_UPLOADS_PER_RUN = 5   # cota do YouTube ~6 uploads/dia; folga de segurança

# vídeos já subidos manualmente (privados) — o agendador só define o publishAt deles
SEEDED = {"0001": "t12Ml4-C5m0", "0002": "A21zMhdAvoM", "0003": "Rgh2fyiEYmI"}


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
    data = urllib.parse.urlencode({
        "client_id": env["YT_CLIENT_ID"], "client_secret": env["YT_CLIENT_SECRET"],
        "refresh_token": env["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())["access_token"]


def slot_datetime(i, channel_start):
    """publishAt (UTC) do i-ésimo vídeo (0-indexed) segundo o calendário."""
    if i < WARMUP_DAYS:
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
        s3.head_object(Bucket=BUCKET, Key=f"renders/spurgeon/{nnnn}.mp4")
        return True
    except Exception:
        return False


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
    ap.add_argument("--max", type=int, default=MAX_UPLOADS_PER_RUN)
    args = ap.parse_args()

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

    token = None if args.dry_run else yt_token(env)
    uploads = 0
    to_render = []

    for i, nnnn in enumerate(ready):
        when = slot_datetime(i, channel_start)
        if when > horizon:
            break                      # além do buffer — fica pra próximo run
        if nnnn in state["scheduled"]:
            continue                   # já agendado
        # slot no passado (atrasado) — empurra pro próximo horário livre a partir de agora
        if when < now:
            when = now + dt.timedelta(hours=2)
        pa = when.strftime("%Y-%m-%dT%H:%M:%SZ")

        # já existe vídeo subido (seed) → só agenda
        if nnnn in SEEDED:
            print(f"  🗓️  {nnnn} (já subido) → {pa}")
            if not args.dry_run:
                schedule_existing(env, SEEDED[nnnn], pa, token)
                state["scheduled"][nnnn] = {"videoId": SEEDED[nnnn], "publishAt": pa}
            continue

        # precisa estar renderizado
        if not video_rendered(s3, nnnn):
            to_render.append(nnnn)
            print(f"  ⏳ {nnnn} → {pa} (FALTA RENDERIZAR — pula neste run)")
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
                 "factorio-render:v5", "python3", "-u", "publish_sermon.py",
                 "--sermon", str(int(nnnn)), "--publish-at", pa],
                capture_output=True, text=True)
            out = r.stdout + r.stderr
            vid = ""
            for line in out.splitlines():
                if "youtu.be/" in line:
                    vid = line.split("youtu.be/")[-1].split()[0].strip()
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
