#!/usr/bin/env python3
"""
canal_branding.py — aplica o watermark de marca do canal no YouTube.

## O que é esse watermark

NÃO é logo queimado no vídeo. É um recurso do próprio YouTube: uma imagem
pequena que o player desenha por cima de TODOS os vídeos do canal, e que ao
ser clicada INSCREVE. É o único botão de inscrição permanente que existe, e
sai de graça. Num sermão de 1h isso vale mais que qualquer card.

## Especificação (conferida na doc oficial em 21/08/2026)

  - mínimo 150x150, PNG ou JPEG, abaixo de 1MB pelo Studio
  - a API `watermarks.set` aceita até 10MB e custa 50 unidades de quota
  - sucesso = HTTP 204 sem corpo
  - sem bloco `timing`, aparece no vídeo INTEIRO (é o que queremos)

## Por que o quadrado sai daqui e não do Canva

O watermark tem que ser o MESMO rosto do avatar, senão vira um segundo
elemento visual competindo. Então ele é derivado de `_assets/channelavatar.png`
e gravado de volta no R2 como `_assets/watermark_150.png`: canal novo repete
o comando, não repete a decisão.

## ⚠️ Colisão que vale saber

O YouTube desenha o watermark no canto INFERIOR DIREITO, que é exatamente onde
o `SermonMaster` coloca o busto do pregador. Sobrepõe o ombro, não o rosto, mas
é bom olhar o primeiro vídeo publicado antes de rodar isso nos 90 seguintes.

Uso:
  python canal_branding.py --canal moody --dry-run     # só gera e mostra
  python canal_branding.py --canal moody               # gera, sobe e aplica
"""
import argparse
import io
import json
import os
import urllib.parse
import urllib.request
import uuid

import boto3
from botocore.config import Config
from PIL import Image

import canais

TOKEN_URL = "https://oauth2.googleapis.com/token"
WATERMARK_URL = "https://www.googleapis.com/upload/youtube/v3/watermarks/set"
LADO = 150
NOME_R2 = "watermark_150.png"


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


def s3_client(env):
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def gerar_quadrado(bruto):
    """Avatar -> PNG 150x150. Corta pelo centro em vez de espremer."""
    im = Image.open(io.BytesIO(bruto)).convert("RGB")
    lado = min(im.size)
    e, t = (im.width - lado) // 2, (im.height - lado) // 2
    im = im.crop((e, t, e + lado, t + lado)).resize((LADO, LADO), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def access_token(c, env):
    cid, secret, refresh = canais.creds_youtube(c, env)
    data = urllib.parse.urlencode({
        "client_id": cid, "client_secret": secret,
        "refresh_token": refresh, "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(
            urllib.request.Request(TOKEN_URL, data=data, method="POST")) as r:
        return json.loads(r.read())["access_token"]


def assert_canal_certo(c, token):
    """Mesmo guardião do publish_youtube.py: token válido ≠ canal certo."""
    esperado = c.get("youtube_channel_id")
    if not esperado:
        raise SystemExit(f"❌ ABORTADO: canal {c['slug']!r} sem `youtube_channel_id`.")
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
        headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=40) as r:
        itens = json.loads(r.read()).get("items", [])
    if not itens:
        raise SystemExit("❌ ABORTADO: o token não devolveu nenhum canal.")
    cid = itens[0]["id"]
    nome = itens[0]["snippet"]["title"]
    if cid != esperado:
        raise SystemExit(
            f"❌ ABORTADO: token autenticado no canal ERRADO.\n"
            f"   esperado: {esperado} ({c['nome']})\n"
            f"   token é de: {cid} ({nome})")
    print(f"  ✓ canal confirmado: {nome} ({cid})")


def aplicar(c, token, png):
    """POST multipart: parte JSON com o InvideoBranding + parte com o PNG."""
    corpo = {"targetChannelId": c["youtube_channel_id"]}   # sem `timing` = vídeo inteiro
    limite = "===" + uuid.uuid4().hex + "==="
    b = limite.encode()
    dados = (b"--" + b + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
             + json.dumps(corpo).encode() + b"\r\n"
             + b"--" + b + b"\r\nContent-Type: image/png\r\n\r\n" + png + b"\r\n"
             + b"--" + b + b"--\r\n")
    url = (WATERMARK_URL + "?" + urllib.parse.urlencode(
        {"channelId": c["youtube_channel_id"], "uploadType": "multipart"}))
    req = urllib.request.Request(url, data=dados, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": f"multipart/related; boundary={limite}",
        "Content-Length": str(len(dados))})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status
    except urllib.error.HTTPError as e:
        raise SystemExit(f"❌ watermarks.set falhou: HTTP {e.code}\n{e.read().decode()[:600]}")


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--dry-run", action="store_true",
                    help="gera o quadrado e para; não sobe nem aplica")
    args = ap.parse_args()

    c = canais.get(args.canal)
    env = load_env()
    s3 = s3_client(env)
    chave = f"{c['prefix']}/_assets/"

    bruto = s3.get_object(Bucket=c["bucket"], Key=chave + "channelavatar.png")["Body"].read()
    png = gerar_quadrado(bruto)
    print(f"🖼  {c['nome']}: avatar {len(bruto)//1024}KB -> watermark {LADO}x{LADO} "
          f"({len(png)//1024}KB)")
    if len(png) > 1024 * 1024:
        raise SystemExit("❌ passou de 1MB; o Studio recusa acima disso.")

    if args.dry_run:
        saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), NOME_R2)
        open(saida, "wb").write(png)
        print(f"   dry-run: gravado em {saida} (nada subiu, nada foi aplicado)")
        return

    s3.put_object(Bucket=c["bucket"], Key=chave + NOME_R2, Body=png,
                  ContentType="image/png")
    print(f"   ↑ R2: {chave + NOME_R2}")

    token = access_token(c, env)
    assert_canal_certo(c, token)
    status = aplicar(c, token, png)
    print(f"   ✅ watermark aplicado (HTTP {status}), vídeo inteiro, todos os vídeos do canal")


if __name__ == "__main__":
    main()
