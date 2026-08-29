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

API = "https://api.magnific.com/v1/ai/text-to-image/nano-banana-pro-flash"

# ── Referência visual POR PREGADOR ────────────────────────────────────────
# A URL da fotografia é parte do contrato, não comentário: é o que torna o
# rosto auditável. Sem isso ninguém consegue checar se o busto é do homem
# certo, e foi exatamente o que faltou quando o Murray saiu errado.
# Todas conferidas em 29/08/2026 (Wikimedia Commons, domínio público).
REFERENCIAS = {
    "murray": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Andrew_Murray.JPG",
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
        "url": "https://upload.wikimedia.org/wikipedia/commons/e/ed/Alexander_Maclaren_%2801%29.jpg",
        "mime": "image/jpeg",
        "quem": "Alexander Maclaren (1826-1910), pregador batista escocês de Manchester",
        "traços": ("elderly man in his sixties, bald on the crown with white hair at "
                   "the sides, full white beard, deep-set intelligent eyes, scholarly "
                   "and severe but kind, wearing a black Victorian frock coat with a "
                   "white shirt and dark bow tie"),
    },
}

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
            raise SystemExit(f"❌ a Magnific reportou FAILED: {json.dumps(data)[:300]}")
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

    for i in range(1, a.n + 1):
        pose = POSES[(i - 1) % len(POSES)]
        prompt = (
            f"Photorealistic studio portrait of the exact same man shown in the "
            f"reference photograph. Keep his facial identity unchanged: {ref['traços']}. "
            f"Pose and expression: {pose}. Pure black background, dramatic Rembrandt "
            f"lighting, sharp detail, square composition, no text, no watermark.")
        nome = f"{a.canal}_bust_cf_{i}.png"
        if a.dry_run:
            print(f"  [{i:02}] {nome}\n       {prompt[:120]}...")
            continue

        d = chamar(API, {
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "resolution": a.resolucao,
            "reference_images": [{"image": ref["url"], "mime_type": ref["mime"],
                                  "text": "the man whose face must be preserved"}],
        })
        task = (d.get("data") or d).get("task_id")
        if not task:
            raise SystemExit(f"❌ resposta sem task_id: {json.dumps(d)[:300]}")
        urls = esperar(task)
        if not urls:
            raise SystemExit(f"❌ tarefa {task} terminou sem imagem")

        alvo = urls[0] if isinstance(urls[0], str) else urls[0].get("url")
        with urllib.request.urlopen(alvo, timeout=180, context=CTX) as r:
            dados = r.read()
        chave = f"{SC.CHANNEL_PREFIX}/_assets/avatars/{nome}"
        s3.put_object(Bucket=SC.BUCKET, Key=chave, Body=dados, ContentType="image/png")
        print(f"  [{i:02}] ok {len(dados)//1024}KB → {nome}")

    print(f"\n🏁 {a.n} bustos de {a.canal} no R2 (Nano Banana Pro {a.resolucao}, "
          f"ilimitado no Premium)")


if __name__ == "__main__":
    main()
