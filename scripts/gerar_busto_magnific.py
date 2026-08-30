#!/usr/bin/env python3
"""
gerar_busto_magnific.py — busto do pregador COM A FOTO REAL como referência.

## Por que existe

O gerador antigo (`gerar_assets_canal.py`) descreve o rosto em TEXTO e manda
pro Worker da Cloudflare. Isso não funciona pra pessoa histórica específica:
"pregador vitoriano de barba" é um arquétipo, não um homem. Foi assim que o
Andrew Murray saiu com cara de Maclaren, e o Gabriel pegou olhando o Google.

Nenhum ajuste de prompt conserta isso, porque o problema não é a descrição:
é não haver referência visual nenhuma. A saída é condicionar por IMAGEM.

## Por que aqui e não na Cloudflare (medido em 29/08)

Testei os três caminhos de img2img da Workers AI com a foto do Murray:
  - `stable-diffusion-v1-5-img2img` → 5018, a conta não tem acesso
  - `flux-2-klein-4b/9b`            → aceitam imagem, mas exigem multipart
                                       (nosso Worker manda JSON+base64)
  - `stable-diffusion-xl-lightning` → nem aceita imagem, é só texto
E mesmo resolvido o formato, img2img comum preserva composição, NÃO identidade.
Pra manter o rosto é preciso um modelo treinado em consistência de personagem,
que é justamente o Nano Banana (Gemini 2.5 Flash Image).

Fundo e cena continuam na Cloudflare, de graça: lá não há rosto pra errar.

## Custo

Nano Banana Pro em 1K/2K está na lista de ILIMITADOS do plano Premium, então
não consome o saldo mensal. `--resolucao 4K` sairia da lista e passaria a
custar 150 créditos por imagem: está bloqueado atrás de `--permitir-4k`.

Uso:
  python scripts/gerar_busto_magnific.py --canal murray --n 5
  python scripts/gerar_busto_magnific.py --canal maclaren --n 5 --dry-run
"""
import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

# ⚠️ O Python do Windows do Gabriel usa um armazém de CAs velho e recusa
# certificados válidos (aconteceu com ccel.org e com api.magnific.com:
# "certificate has expired" em site que está perfeitamente no ar).
# `certifi` traz o pacote atualizado. Sem isto, este script só rodaria na VPS,
# e a chave da Magnific mora AQUI — mandar credencial pra VPS é gate do
# Gabriel, não decisão minha. Então o script se adapta à máquina.
try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(RAIZ, "remotion"))

class FalhaDaImagem(Exception):
    """Erro que atinge UMA imagem, não o lote. Ver o laço de tentativas."""


API = "https://api.magnific.com/v1/ai/text-to-image/nano-banana-pro-flash"

# ── Referência visual POR PREGADOR ────────────────────────────────────────
# A URL da fotografia é parte do contrato, não comentário: é o que torna o
# rosto auditável. Sem isso ninguém consegue checar se o busto é do homem
# certo, e foi exatamente o que faltou quando o Murray saiu errado.
#
# ⚠️ ESPELHADAS NO NOSSO R2, e não apontando pra Wikimedia direto.
# Apontar pro upload.wikimedia.org funcionou duas vezes e na terceira a
# Magnific devolveu "Unable to resolve image / could not download image":
# a Wikimedia barra o fetcher deles. Referência que a API não consegue
# baixar é o mesmo que não ter referência, e o busto volta a ser inventado.
# Originais (domínio público, conferidos em 29/08/2026):
#   murray   → commons/9/9c/Andrew_Murray.JPG
#   maclaren → commons/e/ed/Alexander_Maclaren_(01).jpg
REFERENCIAS = {
    "murray": {
        "url": "https://pub-cd23eb57aece4069a2df4818e6b9eed3.r2.dev/referencias/pregadores/murray.jpg",
        "mime": "image/jpeg",
        "quem": ("Andrew Murray (1828-1917), ministro sul-africano da Igreja "
                 "Reformada Holandesa"),
        # Descrição escrita OLHANDO a foto, pra reforçar o que a referência já diz.
        "traços": ("middle-aged man with a high broad forehead and deeply receding "
                   "hairline, dark brown hair swept back and full over the ears, dark "
                   "full beard along the jaw and chin with the upper lip nearly "
                   "clean-shaven, long straight nose, serious direct gaze, wearing a "
                   "high-buttoned black clerical frock coat with two white rectangular "
                   "Geneva preaching bands at the throat"),
    },
    "maclaren": {
        "url": "https://pub-cd23eb57aece4069a2df4818e6b9eed3.r2.dev/referencias/pregadores/maclaren.jpg",
        "mime": "image/jpeg",
        "quem": "Alexander Maclaren (1826-1910), pregador batista escocês de Manchester",
        "traços": ("elderly man in his sixties, bald on the crown with white hair at "
                   "the sides, full white beard, deep-set intelligent eyes, scholarly "
                   "and severe but kind, wearing a black Victorian frock coat with a "
                   "white shirt and dark bow tie"),
    },
}

# ── LINGUAGEM VISUAL DO ARQUÉTIPO ─────────────────────────────────────────
#
# ⚠️ TREASURES NÃO É FOTOGRAFIA. Corrigido em 29/08 depois que o Gabriel viu os
# primeiros bustos: "ficaram super maneiros, porém REALISTAS; estamos usando pro
# treasures uma linguagem específica que fica um desenho, não parecendo uma foto".
#
# A armadilha aqui é sutil: os prompts antigos (Spurgeon, Moody) TAMBÉM dizem
# "photorealistic", e mesmo assim saem pintados — porque o modelo da Cloudflare
# renderiza pintado de qualquer jeito. O Nano Banana leva a palavra ao pé da
# letra e devolve fotografia de estúdio, com poro de pele e textura de tecido.
# Ou seja: trocar de modelo mudou o estilo sem ninguém mexer no prompt.
# Copiar a redação antiga pra cá foi o erro; o estilo tem que ser DITO.
#
# O estilo fotográfico não foi jogado fora: o Gabriel quer usá-lo no próximo
# arquétipo de canal. Por isso ele mora numa constante nomeada, e não espalhado
# nos prompts — arquétipo novo escolhe a sua e pronto.
ESTILO_TREASURES = (
    "Rendered as a PAINTED digital portrait, NOT a photograph: smooth painterly "
    "brushwork, idealized skin without visible pores or skin texture, hair and "
    "beard in soft flowing brushstrokes, warm golden-brown palette, the dark "
    "clothing dissolving into the background, subtle vignette, the finish of a "
    "classical oil portrait. No photographic grain, no camera lens artifacts.")

# Reservado pro arquétipo fotográfico que vem depois; NÃO usar no Treasures.
ESTILO_FOTO = ("Photorealistic studio photograph, sharp detail, natural skin "
               "texture, real fabric weave.")

# O pedido de POSE muda; a identidade fica travada pela referência.
POSES = [
    "looking directly at the camera, calm and resolute",
    "three-quarter view, head slightly turned, attentive",
    "warm and fatherly expression, eyes kind",
    "quiet intensity, thoughtful and still",
    "slightly lower angle, upright and dignified",
]


def env():
    e = {}
    for line in open(os.path.join(RAIZ, ".env"), encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "").strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            e.setdefault(k, v)
    return e


E = env()


def chamar(caminho, corpo=None, metodo="POST"):
    """A doc diz x-magnific-api-key; o header antigo da Freepik ainda responde
    em parte da frota. Tenta os dois antes de desistir, e diz qual funcionou."""
    ultimo = None
    for header in ("x-magnific-api-key", "x-freepik-api-key"):
        req = urllib.request.Request(
            caminho, method=metodo,
            data=json.dumps(corpo).encode() if corpo is not None else None,
            headers={header: E.get("MAGNIFIC_API_KEY", ""),
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            ultimo = f"{header} → HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
            if e.code not in (401, 403):
                raise SystemExit(f"❌ {ultimo}")
    raise SystemExit(f"❌ nenhum header autenticou. Último: {ultimo}")


def saturacao_do_fundo(dados):
    """Quanta COR existe na região de fundo (0 = preto/cinza puro).

    ⚠️ Esta métrica substituiu a de luminância, que me enganou duas vezes.
    Medir brilho não pega fundo pintado escuro: um busto do Maclaren saiu com
    backdrop VERMELHO de estúdio e passou com "borda 6.2", porque vermelho
    escuro tem luminância baixa e porque a média diluía a região clara num mar
    de canto escuro. Trocar média por percentil também não resolveu: o corte de
    ponto preto já zerava a borda extrema, e o vermelho vivia no MIOLO do fundo,
    atrás da cabeça, fora da faixa amostrada.

    Cor é o sinal certo, e é binário na prática: fundo preto dá saturação ~0 a
    12; backdrop pintado dá 50 a 210. Não tem zona cinzenta pra errar.

    Amostra as laterais e o topo (18% de cada), que é onde há fundo num
    retrato de cabeça e ombros. O rodapé fica de fora: lá está o peito.
    """
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(dados)).convert("HSV").resize((256, 256))
    px = im.load()
    m = int(256 * 0.18)
    sat = [px[x, y][1] for x in range(256) for y in range(256)
           if x < m or x >= 256 - m or y < m]
    return sum(sat) / len(sat)


TETO_SATURACAO = 20.0     # acima disso é backdrop pintado, não é preto


def luminancia_da_borda(dados):
    """Média de brilho da moldura externa (0=preto, 255=branco).

    ⚠️ FUNDO PRETO NÃO É ESTÉTICA, É REQUISITO. O template compõe o busto com
    `mixBlendMode: 'screen'`, e screen só some com o fundo se ele for preto:
    qualquer cinza vira véu por cima da cena. Medido em 29/08, SETE dos dez
    primeiros bustos saíram com estante de livros atrás, mesmo o prompt pedindo
    "pure black background" — o modelo obedece na maioria das vezes, não sempre.
    Pedir e não conferir é o mesmo que não pedir.
    """
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(dados)).convert("L")
    w, h = im.size
    px = im.load()
    m = max(4, int(w * 0.03))
    vals = []
    for x in range(0, w, 8):
        vals += [px[x, y] for y in range(0, m, 4)] + [px[x, y] for y in range(h - m, h, 4)]
    for y in range(0, h, 8):
        vals += [px[x, y] for x in range(0, m, 4)] + [px[x, y] for x in range(w - m, w, 4)]
    return sum(vals) / len(vals)


TETO_BORDA = 18.0        # acima disso o screen já deixa véu visível
PONTO_PRETO = 0.16       # abaixo disto (0..1) é fundo, não é o pregador


def cravar_preto(dados):
    """Puxa o ponto preto pra baixo: fundo quase-preto vira preto DE VERDADE.

    O estilo pintado do Treasures nasce com vinheta suave, e vinheta não é
    #000000. Medido em 29/08: com o estilo fotográfico o gate de fundo passava
    quase sempre; com o pintado, só 1 em 5 passou, e insistir em refazer não
    converge — é feitio do estilo, não azar.

    Brigar com o modelo por algo que se resolve em duas linhas de aritmética é
    desperdício. Isto é um ajuste de níveis clássico: tudo abaixo do ponto preto
    vai a zero e o resto é reesticado, então a queda é SUAVE. Nada de corte
    duro, que deixaria halo em volta da cabeça (a mesma mina do recorte dos
    bustos do Gemini, quando o corte reto fez o busto parecer adesivo).

    O paletó escuro escurece junto, e isso é desejado: o figurino se dissolver
    no fundo já é parte da linguagem do arquétipo.
    """
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(dados)).convert("RGB")
    p = int(PONTO_PRETO * 255)
    tabela = [0 if v <= p else min(255, round((v - p) * 255 / (255 - p)))
              for v in range(256)]
    im = im.point(tabela * 3)
    saida = io.BytesIO()
    im.save(saida, "PNG")
    return saida.getvalue()


def esperar(task_id, limite_s=300):
    """A API é assíncrona. Sem webhook, resta perguntar de tempos em tempos."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < limite_s:
        d = chamar(f"{API}/{task_id}", metodo="GET")
        data = d.get("data", d)
        status = data.get("status", "?")
        if status == "COMPLETED":
            return data.get("generated", [])
        if status == "FAILED":
            # Devolve em vez de matar o processo: um "Content violation" numa
            # pose derrubou o lote do Murray no 5º e perdeu o que já tinha sido
            # feito. Falha de UMA imagem é falha de uma imagem.
            raise FalhaDaImagem(data.get("error") or json.dumps(data)[:160])
        time.sleep(5)
    raise SystemExit(f"❌ tarefa {task_id} não terminou em {limite_s}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True, choices=sorted(REFERENCIAS))
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--resolucao", default="2K")
    ap.add_argument("--permitir-4k", action="store_true",
                    help="4K sai do ilimitado e passa a custar 150 créditos/imagem")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.resolucao == "4K" and not a.permitir_4k:
        sys.exit("⛔ 4K não é ilimitado no Premium (150 créditos/imagem). "
                 "Se é isso mesmo, repita com --permitir-4k.")
    if not E.get("MAGNIFIC_API_KEY"):
        sys.exit("❌ falta MAGNIFIC_API_KEY no .env")

    ref = REFERENCIAS[a.canal]
    print(f"🎨 {ref['quem']}")
    print(f"   referência: {ref['url']}")

    import canais, schedule_channel as SC
    SC.aplicar_canal(a.canal)
    s3 = SC.s3c(SC.load_env())

    reprovados = 0
    for i in range(1, a.n + 1):
        pose = POSES[(i - 1) % len(POSES)]
        nome = f"{a.canal}_bust_cf_{i}.png"
        if a.dry_run:
            print(f"  [{i:02}] {nome}  ({pose})")
            continue

        # Até 3 tentativas, endurecendo a exigência de fundo a cada reprovação.
        # O modelo acerta o preto na maioria das vezes, mas não sempre: sem este
        # laço, 7 em 10 bustos foram pro R2 com estante de livros atrás.
        dados = None
        for tentativa in range(1, 4):
            # A exigência de fundo entra SEMPRE, não só na repetição: com o
            # estilo pintado a taxa de acerto na 1ª tentativa era ~35%, e
            # deixar a regra pra 2ª rodada era jogar fora uma geração inteira.
            # "no signature" porque o estilo de pintura convida o modelo a
            # assinar: um busto do Maclaren veio com "J. Davies" no canto,
            # atribuição inventada num retrato que vai pro ar por anos.
            reforco = (" The background MUST be solid pure black (#000000), completely "
                       "empty: no room, no wall, no painted backdrop, no colored or "
                       "red or brown studio background, no furniture, no scenery, "
                       "nothing but pure black behind him. "
                       "No signature, no artist signature, no lettering of any kind."
                       + ("" if tentativa == 1 else
                          " PREVIOUS ATTEMPT FAILED: the background had colour in it. "
                          "It must be absolute black, like a subject lit in a dark room."))
            prompt = (
                f"Head-and-shoulders portrait of the exact same man shown in the "
                f"reference photograph. Keep his facial identity unchanged: {ref['traços']}. "
                f"Pose and expression: {pose}. {ESTILO_TREASURES} "
                f"Pure black background, dramatic Rembrandt lighting, square "
                f"composition, no text, no watermark.{reforco}")
            try:
                d = chamar(API, {
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "resolution": a.resolucao,
                    "reference_images": [{"image": ref["url"], "mime_type": ref["mime"],
                                          "text": "the man whose face must be preserved"}],
                })
                task = (d.get("data") or d).get("task_id")
                if not task:
                    raise FalhaDaImagem(f"resposta sem task_id: {json.dumps(d)[:160]}")
                urls = esperar(task)
                if not urls:
                    raise FalhaDaImagem("tarefa terminou sem imagem")
            except FalhaDaImagem as e:
                print(f"       ↻ tentativa {tentativa}: a Magnific recusou ({e}), refazendo")
                continue
            alvo = urls[0] if isinstance(urls[0], str) else urls[0].get("url")
            with urllib.request.urlopen(alvo, timeout=180, context=CTX) as r:
                candidato = cravar_preto(r.read())

            sat = saturacao_do_fundo(candidato)
            borda = luminancia_da_borda(candidato)
            if sat <= TETO_SATURACAO and borda <= TETO_BORDA:
                dados = candidato
                break
            motivo = (f"fundo colorido (saturação {sat:.0f} > {TETO_SATURACAO:.0f})"
                      if sat > TETO_SATURACAO
                      else f"fundo claro (borda {borda:.0f} > {TETO_BORDA:.0f})")
            print(f"       ↻ tentativa {tentativa}: {motivo}, refazendo")
        if dados is None:
            reprovados += 1
            print(f"  [{i:02}] ⛔ {nome} DESCARTADO: sem fundo preto em 3 tentativas. "
                  f"NÃO vai pro R2 (quebraria o screen do template).")
            continue
        chave = f"{SC.CHANNEL_PREFIX}/_assets/avatars/{nome}"
        s3.put_object(Bucket=SC.BUCKET, Key=chave, Body=dados, ContentType="image/png")
        print(f"  [{i:02}] ok {len(dados)//1024}KB → {nome}")

    print(f"\n🏁 {a.n - reprovados}/{a.n} bustos de {a.canal} no R2 "
          f"(Nano Banana Pro {a.resolucao}, ilimitado no Premium)")
    if reprovados:
        print(f"   ⛔ {reprovados} reprovados no gate de fundo preto. "
              f"Rode de novo pra preencher as vagas.")


if __name__ == "__main__":
    main()
