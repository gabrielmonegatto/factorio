#!/usr/bin/env python3
"""
estabilizar.py — tira a tremida de câmera dos clipes, na pós, sem GPU.

## Por que na pós e não no prompt

O prompt já pede `static camera` e o modelo mesmo assim inventa deriva e tremor:
ele não tem noção de tripé, só de "vídeos costumam se mexer". Brigar com isso no
prompt é caro (cada tentativa é uma rodada de GPU) e não converge. Estabilizar
depois é determinístico, roda no PC, custa zero e é o que a edição de verdade faz.

## Como funciona (vidstab, dois passes)

  1. `vidstabdetect` mede o deslocamento de cada quadro e grava num .trf
  2. `vidstabtransform` reposiciona os quadros pra anular esse deslocamento

Reposicionar deixa borda vazia, então o filtro dá um zoom pequeno pra cobrir.
Por isso o clipe perde uns 2% de enquadramento: é o preço, e é barato.

## O número que ele mostra

`tremida` = deslocamento médio por quadro em pixels, lido do .trf do passe 1.
Rodar o passe 1 no arquivo JÁ estabilizado diz o quanto sobrou. É medida, não
opinião: se não cair, o filtro não serviu pra esse clipe.

Uso:
  python scripts/ancoras/estabilizar.py --dir scratch/ancoras/clipes_5s
  python scripts/ancoras/estabilizar.py --dir ... --zoom 4   (tremida forte)
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


LARG_MINI, ALT_MINI = 80, 44        # miniatura pra estimar deslocamento
BUSCA = 5                           # raio de busca, em pixels da miniatura


def quadros_mini(caminho):
    """Quadros em cinza e miniatura, como bytes crus."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", caminho, "-vf",
         f"scale={LARG_MINI}:{ALT_MINI},format=gray", "-f", "rawvideo", "-"],
        capture_output=True)
    n = LARG_MINI * ALT_MINI
    d = r.stdout
    return [d[i:i + n] for i in range(0, len(d) - n + 1, n)]


def melhor_deslocamento(a, b):
    """(dx, dy) que melhor alinha b em a, por menor soma de diferenças."""
    melhor, mdx, mdy = None, 0, 0
    for dy in range(-BUSCA, BUSCA + 1):
        for dx in range(-BUSCA, BUSCA + 1):
            soma = cont = 0
            for y in range(BUSCA, ALT_MINI - BUSCA, 2):     # amostra: metade das linhas
                ya = y * LARG_MINI
                yb = (y + dy) * LARG_MINI
                for x in range(BUSCA, LARG_MINI - BUSCA, 2):
                    soma += abs(a[ya + x] - b[yb + x + dx])
                    cont += 1
            m = soma / cont
            if melhor is None or m < melhor:
                melhor, mdx, mdy = m, dx, dy
    return mdx, mdy


def medir_tremida(caminho, trf=None):
    """Deslocamento global médio entre quadros consecutivos, em pixels do vídeo.

    🧨 A primeira versão disto lia o .trf do vidstab como TEXTO e devolvia 0,00
    pra tudo. O arquivo é BINÁRIO (cabeçalho TRF1) — a métrica parecia funcionar
    e não media nada. Esta versão estima o deslocamento por conta própria,
    alinhando miniaturas de quadros consecutivos: é lenta, mas é conferível.
    """
    qs = quadros_mini(caminho)
    if len(qs) < 2:
        return None
    escala = 1280.0 / LARG_MINI
    ds = []
    for i in range(1, len(qs)):
        dx, dy = melhor_deslocamento(qs[i - 1], qs[i])
        ds.append(((dx * dx + dy * dy) ** 0.5) * escala)
    return sum(ds) / len(ds)


def estabilizar(entrada, saida, zoom, suavidade):
    trf = "_vidstab.trf"
    # o .trf continua sendo do vidstab (ele sabe ler o próprio formato);
    # quem não sabia ler era eu, então a MEDIÇÃO é feita por fora
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", entrada, "-vf",
                    f"vidstabdetect=shakiness=10:accuracy=15:result={trf}",
                    "-f", "null", "-"], capture_output=True)
    antes = medir_tremida(entrada)
    r = run(["ffmpeg", "-v", "error", "-y", "-i", entrada, "-vf",
             f"vidstabtransform=input={trf}:zoom={zoom}:smoothing={suavidade}:"
             "optzoom=0:interpol=bicubic,unsharp=5:5:0.6:3:3:0.3",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", saida])
    if r.returncode != 0 or not os.path.exists(saida):
        return antes, None, (r.stderr or "")[-300:]
    return antes, medir_tremida(saida), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--saida", help="padrão: <dir>_estavel")
    ap.add_argument("--zoom", type=float, default=2.0,
                    help="%% de zoom pra cobrir a borda que a correção abre")
    ap.add_argument("--suavidade", type=int, default=30,
                    help="quadros na janela de suavização; mais = mais firme")
    args = ap.parse_args()

    destino = args.saida or (args.dir.rstrip("/\\") + "_estavel")
    os.makedirs(destino, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(args.dir, "*.mp4")))
    if not arquivos:
        sys.exit(f"❌ nenhum mp4 em {args.dir}")

    print(f"🎯 {len(arquivos)} clipes · zoom {args.zoom}% · suavidade {args.suavidade}\n")
    for f in arquivos:
        nome = os.path.basename(f)
        antes, depois, erro = estabilizar(f, os.path.join(destino, nome),
                                          args.zoom, args.suavidade)
        if erro:
            print(f"  ❌ {nome[:34]:34} {erro}")
            continue
        queda = 100 * (1 - depois / antes) if antes else 0
        print(f"  {'✅' if queda > 15 else '⚠️ '} {nome[:34]:34} "
              f"tremida {antes:5.2f} → {depois:5.2f} px/quadro  ({queda:+.0f}%)")
    print(f"\n🏁 saída em {destino}")


if __name__ == "__main__":
    main()
