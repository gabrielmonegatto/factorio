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
# 🧨 MEDIR YDIF CRU MENTE. Ele é diferença ABSOLUTA de luminância, então cena
# escura marca pouco mesmo se mexendo muito — e escuro é a direção deste canal.
# Medido em 23/08: mar_05 marcava 5.41 e parecia dez vezes melhor que os outros,
# mas só era mais CLARO (luminância 116 contra 25). Relativizado, a distância cai
# de 10x pra 2x. Por isso o corte é sobre YDIF/YAVG, em porcentagem.
#   controle com prompt tímido  0.3%   parado de verdade
#   storm_swell / wave_on_rock  2.3-2.8%  utilizável
#   mar_05 (o melhor que já saiu) 4.7%
# Faixas recalibradas em 29/08 pro passo de 1s (as antigas eram do passo de 1
# quadro e barravam clipe bom do Kling).
MOV_PARADO = 2.0   # abaixo disso não sobe
MOV_FRACO = 5.0    # entre os dois, sobe com aviso

sys.path.insert(0, HERE)
import casar_ancora as ca  # noqa: E402


# 🧨 PASSO ENTRE OS QUADROS COMPARADOS. Comparar quadros CONSECUTIVOS mede
# VELOCIDADE, não deslocamento — e movimento lento e contínuo, que é exatamente
# o que a direção deste canal pede, marca quase zero. Medido em 29/08: o clipe
# da nave dá 0,2% entre quadros vizinhos e MUDA 4,1% DOS PIXELS entre o quadro 5
# e o 115. Ele foi barrado por "parado" sendo que está ótimo no olho.
# Comparando de 24 em 24 (1 segundo), movimento contemplativo aparece.
PASSO = 24


def _stat(caminho, chave, passo=PASSO):
    vf = (f"select='not(mod(n\,{passo}))',setpts=N/FRAME_RATE/TB,"
          f"signalstats,metadata=print:key=lavfi.signalstats.{chave}")
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", caminho, "-vf", vf,
                        "-f", "null", "-"], capture_output=True, text=True)
    return [float(m) for m in re.findall(chave + r"=([\d.]+)", r.stderr)]


def medir_movimento(caminho):
    """Movimento RELATIVO: diferença média entre quadros dividida pela luminância
    média da cena. Devolve (percentual, n_quadros, luminancia)."""
    dif = _stat(caminho, "YDIF")
    lum = _stat(caminho, "YAVG")
    if not dif or not lum:
        return None, 0, 0
    d = sum(dif) / len(dif)
    y = sum(lum) / len(lum)
    return 100.0 * d / max(y, 1.0), len(dif), y


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
        mov, n, lum = medir_movimento(f)
        mb = os.path.getsize(f) / 1e6
        if mov is None:
            print(f"  ⚠️  {cid:28} não deu pra medir")
            continue
        vivo = mov >= MOV_PARADO
        fraco = vivo and mov < MOV_FRACO
        marca = "🧊" if not vivo else ("🌫️ " if fraco else "🎞️ ")
        nota = "  ← PARADO, não sobe" if not vivo else ("  ← movimento fraco" if fraco else "")
        print(f"  {marca} {cid:28} mov {mov:4.1f}% · luz {lum:5.1f} · {n:3d}q · {mb:4.1f}MB{nota}")
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
