#!/usr/bin/env python3
"""
subir_referencia.py — espelha a foto do pregador no nosso R2, EM PÉ.

## Por que existe (dois defeitos, os dois medidos em 29/08/2026)

**1. A Magnific não baixa da Wikimedia.** Apontar `reference_images` direto pro
`upload.wikimedia.org` funcionou duas vezes e na terceira voltou "Unable to
resolve image / could not download image": eles barram o fetcher da Magnific.
Referência que a API não alcança é o mesmo que não ter referência, e o busto
volta a ser inventado do zero.

**2. Foto deitada mata o reconhecimento.** O retrato do Maclaren na Wikimedia
está gravado em PAISAGEM (2560x1920) com `EXIF orientation 8`: só aparece em pé
se quem abre respeitar o EXIF. A Magnific não respeita. Ela recebeu um rosto de
lado, não achou rosto nenhum, e caiu de volta no texto — o busto saiu um
cientista vitoriano num laboratório, com fundo de biblioteca. O do Murray, cuja
foto é retrato com orientação 1, saiu perfeito no mesmo pipeline.

Esse é o tipo de defeito que não dá erro: a API responde 200, cobra, e devolve
uma imagem bonita do homem errado.

## O que este script faz

Baixa, **aplica a rotação do EXIF de verdade nos pixels** (`exif_transpose`),
converte pra RGB, e sobe pro R2 público. A partir daí a referência é um retrato
em pé que qualquer serviço entende, sem depender de metadado.

Uso:
  python scripts/subir_referencia.py --slug murray \\
      --url https://upload.wikimedia.org/wikipedia/commons/9/9c/Andrew_Murray.JPG
  python scripts/subir_referencia.py --todas        # refaz as já cadastradas
"""
import argparse
import io
import os
import ssl
import sys
import urllib.request

from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(RAIZ, "remotion"))

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()

# Originais em domínio público (Wikimedia Commons), conferidos em 29/08/2026.
ORIGINAIS = {
    "murray": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Andrew_Murray.JPG",
    "maclaren": "https://upload.wikimedia.org/wikipedia/commons/e/ed/Alexander_Maclaren_%2801%29.jpg",
}
PREFIXO_R2 = "referencias/pregadores"


def base_publica():
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf-8", errors="ignore"):
        l = l.replace("\r", "").strip()
        if l.startswith("R2_PUBLIC_URL="):
            return l.split("=", 1)[1].strip().rstrip("/")
    sys.exit("❌ falta R2_PUBLIC_URL no .env")


def subir(slug, url, s3):
    req = urllib.request.Request(
        url, headers={"User-Agent": "EternalL/1.0 (br4nds.b4you@gmail.com)"})
    bruto = urllib.request.urlopen(req, timeout=180, context=CTX).read()

    im = Image.open(io.BytesIO(bruto))
    antes, orient = im.size, (im.getexif().get(274) or 1)
    # A LINHA QUE IMPORTA: aplica a rotação NOS PIXELS. Depois disso o arquivo
    # não depende mais de ninguém ler o EXIF pra aparecer em pé.
    im = ImageOps.exif_transpose(im).convert("RGB")

    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    dados = buf.getvalue()

    chave = f"{PREFIXO_R2}/{slug}.jpg"
    s3.put_object(Bucket="mananciall", Key=chave, Body=dados, ContentType="image/jpeg")

    girou = " (GIRADA)" if orient not in (1, 0) else ""
    retrato = "retrato" if im.size[1] >= im.size[0] else "⚠️ AINDA PAISAGEM"
    print(f"  {slug:10} exif={orient}{girou}  {antes} → {im.size} {retrato}  "
          f"{len(dados)//1024}KB")
    return f"{base_publica()}/{chave}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--url")
    ap.add_argument("--todas", action="store_true")
    a = ap.parse_args()

    import canais, schedule_channel as SC
    SC.aplicar_canal("murray")          # qualquer canal serve: só quero o cliente S3
    s3 = SC.s3c(SC.load_env())

    alvos = ORIGINAIS.items() if a.todas else [(a.slug, a.url or ORIGINAIS.get(a.slug))]
    if not a.todas and not (a.slug and alvos[0][1]):
        sys.exit("informe --slug (cadastrado) ou --slug + --url, ou use --todas")

    print("📤 espelhando referências no R2 público:")
    for slug, url in alvos:
        print(f"     ← {url}")
        print("     → " + subir(slug, url, s3))


if __name__ == "__main__":
    main()
