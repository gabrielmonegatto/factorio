#!/usr/bin/env python3
"""
derivar_bustos.py — variantes de rotação por CÓDIGO, a partir dos bustos aprovados.

## Por que existe (incidente de 30/08, parte 2)

Pedir "5 poses" pra API com o retrato-mestre como referência devolve CLONES da
mesma pose (o mestre ancora pose junto com estilo), e quando o modelo se esforça
pra variar, alucina: um Murray saiu de ARMADURA AZUL, outro com uma frase
escrita em cima. Do lote de 10, sobraram 3 aproveitáveis, a ~75 créditos por
geração. O Gabriel: "esse processo está um lixo ainda". Está certo.

A rotação de bustos nos vídeos precisa de VARIEDADE VISUAL, não de poses
inéditas. Espelho + níveis de recorte produzem variantes genuinamente
diferentes na tela a partir de UMA imagem aprovada, em milissegundos, de graça,
sem chance de armadura. IA gera o retrato-base; aritmética gera a rotação.

O que cada derivação preserva por construção: identidade (é a mesma imagem),
estilo (idem) e fundo preto (recorte de imagem preta continua preta).

Uso:
  python scripts/derivar_bustos.py --canal murray --fontes 1 --n 5
  python scripts/derivar_bustos.py --canal maclaren --fontes 1,3 --n 5
"""
import argparse
import io
import os
import sys

from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(RAIZ, "remotion"))


def recortar(im, zoom, foco_y=0.38):
    """Zoom centrado no rosto (que vive no terço superior do quadro)."""
    w, h = im.size
    f = 1.0 / zoom
    cw, ch = int(w * f), int(h * f)
    x = (w - cw) // 2
    y = int((h - ch) * foco_y)
    return im.crop((x, y, x + cw, y + ch)).resize((w, h), Image.LANCZOS)


# Receita de variantes na ordem em que preenchem slots. Espelho vem antes de
# zoom forte: é a variação mais perceptível na tela e a mais barata.
VARIANTES = [
    ("original",       lambda im: im),
    ("espelho",        lambda im: ImageOps.mirror(im)),
    ("zoom",           lambda im: recortar(im, 1.16)),
    ("espelho_zoom",   lambda im: ImageOps.mirror(recortar(im, 1.16))),
    ("zoom_forte",     lambda im: recortar(im, 1.32, foco_y=0.30)),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--fontes", required=True,
                    help="índices dos bustos APROVADOS no R2, ex: 1 ou 1,3")
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()

    import canais, schedule_channel as SC
    SC.aplicar_canal(a.canal)
    s3 = SC.s3c(SC.load_env())
    base_r2 = f"{SC.CHANNEL_PREFIX}/_assets/avatars"

    fontes = []
    for idx in a.fontes.split(","):
        chave = f"{base_r2}/{a.canal}_bust_cf_{int(idx)}.png"
        corpo = s3.get_object(Bucket=SC.BUCKET, Key=chave)["Body"].read()
        fontes.append((int(idx), Image.open(io.BytesIO(corpo)).convert("RGB")))
        print(f"📥 fonte aprovada: cf_{idx}")

    ocupados = {i for i, _ in fontes}
    # Arquiva o que vai ser substituído (padrão da casa: nada se apaga).
    for i in range(1, a.n + 1):
        if i in ocupados:
            continue
        velho = f"{base_r2}/{a.canal}_bust_cf_{i}.png"
        try:
            s3.copy_object(Bucket=SC.BUCKET,
                           Key=f"{base_r2}/_descartado_poses/{a.canal}_bust_cf_{i}.png",
                           CopySource={"Bucket": SC.BUCKET, "Key": velho})
            s3.delete_object(Bucket=SC.BUCKET, Key=velho)
            print(f"🗄️  cf_{i} antigo arquivado em _descartado_poses/")
        except Exception:
            pass                                   # slot vazio: nada a arquivar

    # Preenche os slots livres alternando fonte e variante. A mesma variante
    # nunca repete pra mesma fonte, então cada slot sai visualmente distinto.
    usadas = {i: 0 for i, _ in fontes}
    rodada = 0
    for i in range(1, a.n + 1):
        if i in ocupados:
            continue
        idx, im = fontes[rodada % len(fontes)]
        usadas[idx] += 1
        nome_var, fn = VARIANTES[usadas[idx] % len(VARIANTES)]
        out = fn(im)
        buf = io.BytesIO()
        out.save(buf, "PNG")
        s3.put_object(Bucket=SC.BUCKET, Key=f"{base_r2}/{a.canal}_bust_cf_{i}.png",
                      Body=buf.getvalue(), ContentType="image/png")
        print(f"  [{i:02}] {a.canal}_bust_cf_{i}.png ← cf_{idx} ({nome_var}) "
              f"{len(buf.getvalue())//1024}KB")
        rodada += 1

    print(f"\n🏁 rotação completa com {a.n} bustos "
          f"({len(fontes)} gerados por IA + {a.n - len(fontes)} derivados, custo 0)")


if __name__ == "__main__":
    main()
