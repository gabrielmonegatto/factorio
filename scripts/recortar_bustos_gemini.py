#!/usr/bin/env python3
"""
recortar_bustos_gemini.py — extrai bustos de canal de uma folha de contato do Gemini.

## Por que existe

O Gemini entrega as N poses numa IMAGEM SÓ, desenhada parecendo um gerenciador
de arquivos: cartões arredondados, rótulo de nome de arquivo embaixo e um
"xadrez de transparência" que é PIXEL PINTADO, não canal alpha.

## A mina que isso resolve

O busto é composto no vídeo com `mixBlendMode: 'screen'` (SermonMaster.tsx).
Screen faz o preto sumir e SOMA o resto. Um fundo xadrez claro (~180 de brilho)
vira um retângulo branco em cima do vídeo inteiro. Então o fundo tem que virar
PRETO PURO, não transparente e muito menos claro.

## Como o xadrez é separado do sujeito

Cor sozinha não serve: a barba branca do pregador tem o mesmo brilho e a mesma
neutralidade do xadrez. O que separa é a ESTRUTURA — quadrado de xadrez é liso
(desvio local ~0), barba tem textura. Então:

  1. candidato = vizinhança 5x5 lisa E cor perto de uma das cores do xadrez
  2. fechamento morfológico costura as costuras entre quadrados
  3. só vale o que está LIGADO à borda (a camisa branca fica de fora: está
     cercada pelo terno escuro)
  4. a borda não é cortada a faca: some numa rampa, como o busto do Spurgeon

Uso:
  python scripts/recortar_bustos_gemini.py ENTRADA.jpg --saida DIR --prefixo moody_bust_cf
  python scripts/recortar_bustos_gemini.py ENTRADA.jpg --saida DIR --debug
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

# Enquadramento alvo, medido do busto do Spurgeon que já está no ar:
# sujeito ocupa ~95% da altura, topo da cabeça a ~4% da borda de cima.
ALTURA_SUJEITO = 0.95
MARGEM_TOPO = 0.04
# fração do lado da célula que a borda leva pra sumir no preto
ESVANECIMENTO = 0.035
LADO_SAIDA = 1024


def achar_celulas(a):
    """Localiza as áreas de imagem pela projeção do xadrez (claro e neutro)."""
    chk = ((a.max(2) - a.min(2)) < 22) & (a.mean(2) > 160)

    def faixas(proj, lim, minlen=40):
        out, ini = [], None
        for i, v in enumerate(proj):
            if v > lim and ini is None:
                ini = i
            elif v <= lim and ini is not None:
                if i - ini > minlen:
                    out.append((ini, i))
                ini = None
        if ini is not None and len(proj) - ini > minlen:
            out.append((ini, len(proj)))
        return out

    cols = faixas(chk.sum(0), 30)
    rows = faixas(chk.sum(1), 30)
    if not cols or not rows:
        sys.exit("não achei o xadrez: essa folha de contato tem outro formato")
    return [(x0, y0, x1, y1) for (y0, y1) in rows for (x0, x1) in cols]


def matte(cel):
    """Devolve alpha do sujeito (1.0 = sujeito, 0.0 = fundo)."""
    cinza = cel.mean(2)
    # desvio local 5x5: quadrado de xadrez é liso, barba/cabelo não
    med = ndimage.uniform_filter(cinza, 5)
    med2 = ndimage.uniform_filter(cinza * cinza, 5)
    liso = np.sqrt(np.maximum(med2 - med * med, 0)) < 4.0

    # claro + liso pega as DUAS cores do xadrez e o degradê entre elas de uma vez.
    # A camisa branca também passa aqui, mas cai fora na etapa de conectividade:
    # está cercada pelo terno escuro, não encosta na borda.
    cand = liso & (cinza > 150)

    # costura as juntas entre quadrados vizinhos.
    # MINA: `border_value=1` é obrigatório. O padrão (0) erode 3px da moldura
    # inteira, o fundo deixa de encostar na borda e o matte sai 100% sujeito.
    cand = ndimage.binary_closing(cand, structure=np.ones((7, 7)), border_value=1)

    lbl, n = ndimage.label(cand)
    if n == 0:
        return np.ones(cinza.shape, np.float32)
    bordas = set(lbl[0].tolist()) | set(lbl[-1].tolist())
    bordas |= set(lbl[:, 0].tolist()) | set(lbl[:, -1].tolist())
    bordas.discard(0)
    fundo = np.isin(lbl, list(bordas))

    fundo = ndimage.binary_dilation(fundo, iterations=2)   # franja do JPEG

    # Recorte duro vira adesivo colado. O busto do Spurgeon não tem silhueta:
    # nasceu sobre preto e se DISSOLVE na escuridão. Reproduzimos isso com uma
    # rampa medida em distância da borda, não com um blur do contorno — blur
    # espalha a franja clara, a rampa apaga ela.
    dist = ndimage.distance_transform_edt(~fundo)
    rampa = max(6.0, ESVANECIMENTO * min(cinza.shape))
    return np.clip((dist - 2.0) / rampa, 0.0, 1.0).astype(np.float32)


def reenquadrar(rgb, alpha):
    """Recorta um quadrado com o mesmo enquadramento dos bustos do Spurgeon."""
    ys, xs = np.where(alpha > 0.5)
    if len(ys) == 0:
        return rgb
    topo, base = ys.min(), ys.max()
    cx = int((xs.min() + xs.max()) / 2)
    lado = int((base - topo + 1) / ALTURA_SUJEITO)
    y0 = int(topo - lado * MARGEM_TOPO)
    x0 = cx - lado // 2

    fora = np.zeros((lado, lado, 3), np.uint8)
    sy0, sx0 = max(0, y0), max(0, x0)
    sy1 = min(rgb.shape[0], y0 + lado)
    sx1 = min(rgb.shape[1], x0 + lado)
    fora[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = rgb[sy0:sy1, sx0:sx1]
    return fora


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--prefixo", default="bust_cf")
    ap.add_argument("--debug", action="store_true", help="salva o matte junto")
    args = ap.parse_args()

    os.makedirs(args.saida, exist_ok=True)
    a = np.asarray(Image.open(args.entrada).convert("RGB")).astype(float)
    celulas = achar_celulas(a)
    print(f"{len(celulas)} poses na folha")

    for i, (x0, y0, x1, y1) in enumerate(celulas, 1):
        # 20px pra dentro: o canto arredondado do cartão é marrom escuro, não
        # entra no matte por não ser claro, e sobraria como sujeito.
        cel = a[y0 + 20:y1 - 20, x0 + 20:x1 - 20]
        al = matte(cel)
        # compor sobre PRETO PURO é só multiplicar pelo alpha
        rgb = np.clip(cel * al[..., None], 0, 255).astype(np.uint8)
        quad = reenquadrar(rgb, al)
        im = Image.fromarray(quad).resize((LADO_SAIDA, LADO_SAIDA), Image.LANCZOS)
        dest = os.path.join(args.saida, f"{args.prefixo}_{i}.png")
        im.save(dest)
        print(f"  [{i}] {os.path.basename(dest)}  sujeito={100*(al>0.5).mean():.0f}% da célula")
        if args.debug:
            Image.fromarray((al * 255).astype(np.uint8)).save(
                os.path.join(args.saida, f"_matte_{i}.png"))


if __name__ == "__main__":
    main()
