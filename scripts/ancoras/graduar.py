#!/usr/bin/env python3
"""
graduar.py — devolve o clipe ao preto do canal DEPOIS de animado.

## A regra que custou caro pra descobrir (23/08)

Anima claro, escurece na pós. Nunca o contrário.

Nossos stills saem com luminância 7/255 e até 83% do quadro em preto absoluto,
porque a bíblia visual manda esse preto. Só que um modelo i2v **só anima o que
distingue**: entregando preto, ele devolve preto com riscos rastejando, e aquele
rastejo é o que parece "câmera tremida" na tela.

Medido na mesma imagem, com os mesmos parâmetros do Wan:

  entrada escura            luz 21.6 · 0,31MB · vidraça e caixilhos SUMIRAM
  entrada clara + graduada  luz 17.4 · 1,15MB · cena inteira preservada

Mesmo tom final, quase 4x mais informação de imagem. Escurecer na pós ainda
esconde artefato, porque o artefato mora justamente na faixa que a gente apaga.

## Por que gama e não brilho

Gama comprime a sombra sem achatar a luz alta, então a lâmpada continua sendo
ponto de luz enquanto o resto afunda no preto. Brilho puxaria a cena toda pra
baixo e mataria o ponto de luz junto, que é a assinatura visual do canal.

Uso:
  python scripts/ancoras/graduar.py --dir scratch/ancoras/clipes_5s
  python scripts/ancoras/graduar.py --dir ... --gama 2.6   (mais escuro)
"""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import subir_clipes as sc  # noqa: E402

GAMA_PADRAO = 2.0
# Alvo de luminância do canal. Os stills originais medem 6,5 a 20,9; o clipe pede
# um respiro a mais que a imagem parada, então 20 é o ponto.
ALVO_PADRAO = 20.0


def gama_para_alvo(caminho, alvo):
    """Resolve o gama que leva ESTE clipe à luminância alvo.

    🧨 Gama fixo não serve. Cada cena parte de um brilho diferente: o mesmo 2.0
    que deixou a chuva em 24 deixou o mar em 68 (medido 23/08). O alvo é igual
    pra todas, a curva é de cada uma.

    Resolve no HISTOGRAMA de um quadro, sem recodificar: buscar por tentativa e
    erro custaria um encode inteiro por passo.
    """
    from PIL import Image
    quadro = "_alvo.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", caminho,
                    "-vf", r"select=eq(n\,30)", "-vframes", "1", quadro],
                   capture_output=True)
    if not os.path.exists(quadro):
        return GAMA_PADRAO
    h = Image.open(quadro).convert("L").histogram()
    os.remove(quadro)
    total = sum(h) or 1

    def luz(g):
        return sum(n * ((i / 255.0) ** g) * 255 for i, n in enumerate(h)) / total

    baixo, alto = 1.0, 8.0          # gama maior = mais escuro
    for _ in range(30):
        meio = (baixo + alto) / 2
        if luz(meio) > alvo:
            baixo = meio
        else:
            alto = meio
    return round((baixo + alto) / 2, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--saida", help="padrão: <dir>_graduado")
    ap.add_argument("--gama", type=float, help="gama fixo; sem isso, usa --alvo")
    ap.add_argument("--alvo", type=float, default=ALVO_PADRAO,
                    help="luminância alvo (0-255); resolve o gama de cada clipe")
    ap.add_argument("--contraste", type=float, default=1.10)
    ap.add_argument("--saturacao", type=float, default=0.90)
    args = ap.parse_args()

    destino = args.saida or (args.dir.rstrip("/\\") + "_graduado")
    os.makedirs(destino, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(args.dir, "*.mp4")))
    if not arquivos:
        sys.exit(f"❌ nenhum mp4 em {args.dir}")

    modo = f"gama fixo {args.gama}" if args.gama else f"alvo de luz {args.alvo}"
    print(f"🎨 {len(arquivos)} clipes · {modo} · contraste {args.contraste}\n")
    for f in arquivos:
        nome = os.path.basename(f)
        saida = os.path.join(destino, nome)
        gama = args.gama or gama_para_alvo(f, args.alvo)
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", f, "-vf",
             f"eq=gamma={1.0/gama:.4f}:contrast={args.contraste}:"
             f"saturation={args.saturacao}",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", saida],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ❌ {nome[:30]:30} {(r.stderr or '')[-160:]}")
            continue
        ma, _, la = sc.medir_movimento(f)
        md, _, ld = sc.medir_movimento(saida)
        print(f"  ✅ {nome[:30]:30} gama {gama:4.2f} · luz {la:5.1f} → {ld:5.1f} · "
              f"mov {ma:4.1f}% → {md:4.1f}% · {os.path.getsize(saida)/1e6:.2f}MB")
    print(f"\n🏁 saída em {destino}")


if __name__ == "__main__":
    main()
