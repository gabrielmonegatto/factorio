#!/usr/bin/env python3
"""
publish_youtube.py — Sobe um vídeo pro YouTube AGENDADO (o elo final da fábrica).

A jogada: sobe como PRIVADO com `publishAt`. O YouTube publica sozinho na data marcada.
Assim a fábrica produz em lote (20 vídeos num fim de semana) e o canal parece diário.

Credenciais (no .env ou ambiente):
  YT_CLIENT_ID        — do OAuth 2.0 Client (Google Cloud Console)
  YT_CLIENT_SECRET
  YT_REFRESH_TOKEN    — gerado uma vez pelo fluxo de autorização (ver auth_youtube.py)

Uso:
  python publish_youtube.py --video 0021.mp4 --title "..." --description "..." \
      --thumbnail thumb.png --publish-at 2026-07-25T13:00:00Z --tags "spurgeon,sermon"

⚠️ GATE HUMANO: publicar é ação externa irreversível. Este script NÃO roda sozinho
   sem `--confirm` — a fábrica prepara tudo, mas quem aperta o botão é decisão consciente.
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"


def load_env():
    env = dict(os.environ)
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def access_token(env):
    """Troca o refresh_token por um access_token (válido ~1h)."""
    data = urllib.parse.urlencode({
        "client_id": env["YT_CLIENT_ID"],
        "client_secret": env["YT_CLIENT_SECRET"],
        "refresh_token": env["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]


def upload(video_path, meta, token):
    """Upload resumável do YouTube: 1) inicia sessão com o metadata, 2) manda os bytes."""
    body = json.dumps(meta).encode()
    size = os.path.getsize(video_path)

    req = urllib.request.Request(
        UPLOAD_URL + "?uploadType=resumable&part=snippet,status",
        data=body, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(size),
            "X-Upload-Content-Type": "video/mp4",
        })
    with urllib.request.urlopen(req) as r:
        session = r.headers["Location"]

    print(f"⬆️  enviando {size/1048576:.0f} MB...")
    with open(video_path, "rb") as f:
        put = urllib.request.Request(session, data=f.read(), method="PUT",
                                     headers={"Content-Type": "video/mp4",
                                              "Content-Length": str(size)})
        with urllib.request.urlopen(put) as r:
            return json.loads(r.read())


def post_comment(video_id, text, token):
    body = json.dumps({"snippet": {"videoId": video_id,
                       "topLevelComment": {"snippet": {"textOriginal": text}}}}).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def set_thumbnail(video_id, thumb_path, token):
    data = open(thumb_path, "rb").read()
    req = urllib.request.Request(
        f"{THUMB_URL}?videoId={video_id}", data=data, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "image/png"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--thumbnail")
    ap.add_argument("--publish-at", help="ISO UTC, ex 2026-07-25T13:00:00Z (agenda a publicação)")
    ap.add_argument("--category", default="22")  # 22 = People & Blogs
    ap.add_argument("--comment", help="texto do 1º comentário (com o link). Postado, mas fixado é manual")
    ap.add_argument("--confirm", action="store_true", help="OBRIGATÓRIO — publicar é irreversível")
    args = ap.parse_args()

    if not args.confirm:
        sys.exit("⛔ Falta --confirm. Publicar no YouTube é ação externa irreversível:\n"
                 "   revise título/descrição/data e rode de novo com --confirm.")

    env = load_env()
    for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"):
        if not env.get(k):
            sys.exit(f"❌ Falta {k} no .env (rode auth_youtube.py uma vez pra gerar o refresh token)")

    meta = {
        "snippet": {
            "title": args.title[:100],
            "description": args.description[:5000],
            "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "categoryId": args.category,
            "defaultLanguage": "en",
        },
        "status": {
            # agendado = privado + publishAt. O YouTube libera sozinho na data.
            "privacyStatus": "private" if args.publish_at else "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    if args.publish_at:
        meta["status"]["publishAt"] = args.publish_at

    token = access_token(env)
    res = upload(args.video, meta, token)
    vid = res.get("id")
    print(f"✅ vídeo no YouTube: https://youtu.be/{vid}")

    if args.thumbnail and os.path.exists(args.thumbnail):
        set_thumbnail(vid, args.thumbnail, token)
        print("🖼️  thumbnail definida")

    # comentário automático com o link (a API não FIXA — Gabriel fixa com 1 clique no Studio)
    if args.comment:
        try:
            post_comment(vid, args.comment, token)
            print("💬 comentário com link postado (fixar manualmente no Studio)")
        except Exception as e:
            print(f"⚠️  não deu pra postar o comentário: {str(e)[:120]}")

    if args.publish_at:
        print(f"🗓️  agendado pra {args.publish_at}")
    print(json.dumps({"videoId": vid, "url": f"https://youtu.be/{vid}"}))


if __name__ == "__main__":
    main()
