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

# 2.0 mede luminância ~17, que é a faixa dos stills originais do canal (7 a 21).
# 2.6 e 3.2 escurecem mais e foram medidos, mas começam a comer a cena de novo.
GAMA_PADRAO = 2.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--saida", help="padrão: <dir>_graduado")
    ap.add_argument("--gama", type=float, default=GAMA_PADRAO)
    ap.add_argument("--contraste", type=float, default=1.10)
    ap.add_argument("--saturacao", type=float, default=0.90)
    args = ap.parse_args()

    destino = args.saida or (args.dir.rstrip("/\\") + "_graduado")
    os.makedirs(destino, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(args.dir, "*.mp4")))
    if not arquivos:
        sys.exit(f"❌ nenhum mp4 em {args.dir}")

    print(f"🎨 {len(arquivos)} clipes · gama {args.gama} · contraste {args.contraste}\n")
    for f in arquivos:
        nome = os.path.basename(f)
        saida = os.path.join(destino, nome)
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", f, "-vf",
             f"eq=gamma={1.0/args.gama:.4f}:contrast={args.contraste}:"
             f"saturation={args.saturacao}",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", saida],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ❌ {nome[:30]:30} {(r.stderr or '')[-160:]}")
            continue
        ma, _, la = sc.medir_movimento(f)
        md, _, ld = sc.medir_movimento(saida)
        print(f"  ✅ {nome[:30]:30} luz {la:5.1f} → {ld:5.1f} · "
              f"mov {ma:4.1f}% → {md:4.1f}% · {os.path.getsize(saida)/1e6:.2f}MB")
    print(f"\n🏁 saída em {destino}")


if __name__ == "__main__":
    main()
