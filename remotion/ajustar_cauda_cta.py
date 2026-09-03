#!/usr/bin/env python3
"""
ajustar_cauda_cta.py — padroniza a pausa pós-CTA em TODOS os canais.

## De onde veio (medido em 02/09)

O Gabriel notou que no Spurgeon existe "uma breve pausa natural" entre o CTA
de abertura e o começo do sermão, e pediu pra replicar. Medindo com
silencedetect: a pausa é simplesmente SILÊNCIO GRAVADO na cauda do próprio
introfixed.mp3. Spurgeon: 1,72s. Moody: 2,97s. Murray: 3,03s. Maclaren: nem
tinha CTA (nasceu antes do berçário).

Ou seja: a referência aprovada de ouvido é ~1,7s, e os canais novos estavam
com o DOBRO (ar morto). Este script corta a cauda existente e recoloca
exatamente CAUDA_S de silêncio, nos dois CTAs (intro e final) dos canais
pedidos.

## O efeito colateral que ele PREVINE

Mexer no mp3 do CTA muda o timestamp no R2, e o gate de frescor do produtor
(assets_cutoff) marca TODO render mais velho que o CTA como "não fresco",
disparando re-render em massa. Pra vídeo já agendado/publicado isso é puro
desperdício. Então depois de ajustar, o script dá "touch" (copy sobre si) nos
renders dos números protegidos, pra eles continuarem mais novos que o CTA.

Uso (na VPS):
  python3 ajustar_cauda_cta.py --canais moody,murray,maclaren
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, ".")
import canais
import narrar_sermao as N

CAUDA_S = 1.7          # a pausa do Spurgeon, aprovada de ouvido
LIMIAR = "-35dB"


def ajustar(s3, c, arquivo):
    chave = f"{c['prefix']}/_assets/{arquivo}"
    local = f"/tmp/cta_{c['slug']}_{arquivo}"
    saida = local.replace(".mp3", "_ok.mp3")
    try:
        s3.download_file(c["bucket"], chave, local)
    except Exception:
        print(f"   {c['slug']}/{arquivo}: não existe, pulando")
        return
    # corta a cauda de silêncio atual e recoloca exatamente CAUDA_S
    filtro = (f"areverse,silenceremove=start_periods=1:start_threshold={LIMIAR},"
              f"areverse,apad=pad_dur={CAUDA_S}")
    subprocess.run(["docker", "run", "--rm", "-v", "/tmp:/tmp",
                    "--entrypoint", "ffmpeg", "factorio-tts",
                    "-y", "-loglevel", "error", "-i", local,
                    "-af", filtro, "-b:a", "96k", saida], check=True)
    s3.upload_file(saida, c["bucket"], chave)
    print(f"   {c['slug']}/{arquivo}: cauda padronizada em {CAUDA_S}s")
    for p in (local, saida):
        os.remove(p)


def tocar_renders_protegidos(s3, c):
    """Renders de vídeos agendados/publicados ficam 'frescos' de novo."""
    try:
        est = json.loads(s3.get_object(Bucket=c["bucket"],
                                       Key=c["state_key"])["Body"].read())
        protegidos = list(est.get("scheduled", {}).keys())
    except Exception:
        return
    tocados = 0
    for nnnn in protegidos:
        k = f"{c['renders_prefix']}/{nnnn}.mp4"
        try:
            s3.copy_object(Bucket=c["bucket"], Key=k,
                           CopySource={"Bucket": c["bucket"], "Key": k},
                           MetadataDirective="REPLACE", ContentType="video/mp4")
            tocados += 1
        except Exception:
            pass
    if tocados:
        print(f"   {c['slug']}: {tocados} renders protegidos re-datados "
              f"(sem re-render em massa)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canais", required=True, help="slugs separados por vírgula")
    a = ap.parse_args()
    env = N.load_env()
    s3 = N.s3c(env)
    for slug in a.canais.split(","):
        c = canais.get(slug.strip())
        print(f"🎚️  {c['nome']}")
        for arq in ("introfixed.mp3", "finalfixed.mp3"):
            ajustar(s3, c, arq)
        tocar_renders_protegidos(s3, c)


if __name__ == "__main__":
    main()
