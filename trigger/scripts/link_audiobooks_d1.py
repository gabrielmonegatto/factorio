#!/usr/bin/env python3
"""
link_audiobooks_d1.py — liga os audiobooks já narrados (R2) aos capítulos do site (D1).

O PROBLEMA: a fábrica narrou 1.214 capítulos (R2 `audiobooks/`), mas o site só serve 23,
porque `chapters.audio_url` no D1 `mananciall-db` está vazio. Áudio pronto, invisível.

O CASAMENTO: R2 `audiobooks/<pasta>/<pref>-<NN>-<titulo>.mp3` → D1 (book_slug, number=NN).
Os totais batem 1:1 nos 9 livros narrados (734/366/20/20/16/16/15/14/13).

Gera SQL de UPDATE pra rodar via wrangler. Não escreve nada sozinho.

Uso (na VPS, que tem credencial do R2):
  python3 link_audiobooks_d1.py            # dry-run: só relatório
  python3 link_audiobooks_d1.py --sql OUT  # grava o SQL em OUT
"""
import os
import re
import sys
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = "mananciall"

# pasta no R2 -> slug do livro no D1 (só onde diferem)
SLUG_R2_PARA_D1 = {
    "morning-and-evening-daily-readings": "morning-and-evening",
    "faith-s-checkbook-of-decisive-testimony": "faiths-checkbook",
    "essentials-of-prayer": "the-essentials-of-prayer",
}


def load_env():
    env = dict(os.environ)
    for p in (os.path.join(HERE, "..", "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", help="arquivo de saída com os UPDATEs")
    args = ap.parse_args()

    env = load_env()
    base = env["R2_PUBLIC_URL"].rstrip("/")

    import boto3
    from botocore.config import Config
    s3 = boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                      aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                      config=Config(signature_version="s3v4"), region_name="auto")

    chaves, tok = [], None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": "audiobooks/", "MaxKeys": 1000}
        if tok:
            kw["ContinuationToken"] = tok
        r = s3.list_objects_v2(**kw)
        chaves += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            break
        tok = r.get("NextContinuationToken")

    mp3 = [k for k in chaves if k.endswith(".mp3")]
    print(f"🎧 mp3 no R2: {len(mp3)}")

    linhas, sem_numero = [], []
    por_livro = {}
    for k in sorted(mp3):
        partes = k.split("/")
        if len(partes) < 3:
            continue
        pasta, arquivo = partes[1], partes[2]
        # <prefixo>-<NN>-<resto>.mp3  → NN é o número do capítulo
        m = re.match(r"^[a-z]+-(\d+)-", arquivo)
        if not m:
            sem_numero.append(k)
            continue
        numero = int(m.group(1))
        slug = SLUG_R2_PARA_D1.get(pasta, pasta)
        url = f"{base}/{k}"
        linhas.append((slug, numero, url))
        por_livro[slug] = por_livro.get(slug, 0) + 1

    print(f"🔗 capítulos mapeados: {len(linhas)}")
    for s, n in sorted(por_livro.items(), key=lambda x: -x[1]):
        print(f"   {s:32} {n}")
    if sem_numero:
        print(f"⚠️  sem número no nome ({len(sem_numero)}): {sem_numero[:5]}")

    if args.sql:
        with open(args.sql, "w", encoding="utf-8") as f:
            for slug, numero, url in linhas:
                u = url.replace("'", "''")
                f.write(
                    f"UPDATE chapters SET audio_url='{u}' "
                    f"WHERE book_slug='{slug}' AND number={numero} "
                    f"AND (audio_url IS NULL OR audio_url='');\n"
                )
        print(f"📝 SQL gravado em {args.sql} ({len(linhas)} UPDATEs)")


if __name__ == "__main__":
    main()
