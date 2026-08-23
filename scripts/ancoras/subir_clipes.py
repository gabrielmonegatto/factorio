#!/usr/bin/env python3
"""
subir_clipes.py — verifica e sobe os clipes animados pro R2.

## Por que existe um passo entre o pod e o short

O `animar.py` desce os mp4 por scp pra `scratch/ancoras/clipes/` (credencial de R2
não sobe pra GPU alugada, doc 22 §8). Mas o `montar_short.py --fonte video` lê de
`renders/ancoras/{id}.mp4` no R2. Este script fecha a ponte.

## Por que MEDE o movimento antes de subir

Já entregamos "clipe" que era still parado (23/08). O modelo pode devolver 81
quadros idênticos e o mp4 fica com tamanho e duração certos: só olhar o arquivo
não denuncia. A medida honesta é a diferença média entre quadros consecutivos
(`signalstats YDIF` do ffmpeg). Perto de zero = imagem congelada, não sobe.

Uso:
  python scripts/ancoras/subir_clipes.py --conferir
  python scripts/ancoras/subir_clipes.py
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
PREFIXO_R2 = "renders/ancoras"
# Faixas medidas no lote 5B de 22/08, o que o Gabriel chamou de "estático":
#   arquitetura_01 0.30 e fogo_01 0.42  → parados de fato
#   mar_05         5.41                 → movimento farto
# Cena escura com névoa se mexe pouco por natureza, então o corte não é binário:
# abaixo de PARADO não sobe; entre PARADO e FRACO sobe com aviso.
YDIF_PARADO = 0.35
YDIF_FRACO = 1.0

sys.path.insert(0, HERE)
import casar_ancora as ca  # noqa: E402


def medir_movimento(caminho):
    """YDIF médio: diferença de luminância entre quadros consecutivos."""
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", caminho, "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YDIF",
         "-f", "null", "-"],
        capture_output=True, text=True)
    vals = [float(m) for m in re.findall(r"YDIF=([\d.]+)", r.stderr)]
    if not vals:
        return None, 0
    return sum(vals) / len(vals), len(vals)


def id_de_cena(base, ids):
    """O still local carrega o prefixo da família (`mar_storm_swell`), mas o
    catálogo e o R2 conhecem a cena só pelo id (`storm_swell`). Subir com o nome
    errado faz o `montar_short.py --fonte video` bater em 404 numa chave que
    parece certa. Resolve pelo catálogo, não por corte cego de prefixo."""
    if base in ids:
        return base
    candidatos = [i for i in ids if base.endswith("_" + i)]
    # o mais longo: evita casar 'agua' quando existe 'agua_parada'
    return max(candidatos, key=len) if candidatos else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(RAIZ, "scratch", "ancoras", "clipes"))
    ap.add_argument("--conferir", action="store_true", help="só mede, não sobe")
    ap.add_argument("--forcar", action="store_true", help="sobe mesmo o clipe parado")
    args = ap.parse_args()

    arquivos = sorted(glob.glob(os.path.join(args.dir, "*.mp4")))
    if not arquivos:
        sys.exit(f"❌ nenhum mp4 em {args.dir}")

    cenas = ca.carregar_catalogo()
    ids = [c["id"] for c in cenas]
    cli = None if args.conferir else ca.s3()
    print(f"🔎 {len(arquivos)} clipes em {args.dir}\n")
    subiu = parados = orfaos = 0
    for f in arquivos:
        base = os.path.splitext(os.path.basename(f))[0]
        cid = id_de_cena(base, ids)
        if not cid:
            print(f"  ⚠️  {base:28} não bate com nenhuma cena do catálogo")
            orfaos += 1
            continue
        ydif, n = medir_movimento(f)
        mb = os.path.getsize(f) / 1e6
        if ydif is None:
            print(f"  ⚠️  {cid:28} não deu pra medir")
            continue
        vivo = ydif >= YDIF_PARADO
        fraco = vivo and ydif < YDIF_FRACO
        marca = "🧊" if not vivo else ("🌫️ " if fraco else "🎞️ ")
        nota = "  ← PARADO, não sobe" if not vivo else ("  ← movimento fraco" if fraco else "")
        print(f"  {marca} {cid:28} YDIF {ydif:5.2f} · {n:3d} quadros · {mb:4.1f}MB{nota}")
        if not vivo:
            parados += 1
        if args.conferir or (not vivo and not args.forcar):
            continue
        cli.upload_file(f, "mananciall", f"{PREFIXO_R2}/{cid}.mp4",
                        ExtraArgs={"ContentType": "video/mp4"})
        subiu += 1

    print(f"\n🏁 {subiu} subiram · {parados} parados · {orfaos} sem cena"
          + ("  (--conferir: nada subiu)" if args.conferir else ""))
    if parados and not args.forcar:
        print("   Clipe parado não vira âncora. Regerar com mais steps ou outro prompt de movimento.")


if __name__ == "__main__":
    main()
