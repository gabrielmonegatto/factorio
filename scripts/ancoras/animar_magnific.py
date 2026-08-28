#!/usr/bin/env python3
"""
animar_magnific.py — anima os stills pela API da Magnific (ex-Freepik), com Kling.

## Por que este caminho existe ao lado do animar.py

O `animar.py` aluga GPU e roda o Wan 2.2 5B. Medido em 25/08/2026, o custo REAL
dele é US$ 0,22 por clipe (a A6000 custa US$ 1,15/h, não os US$ 0,33 que eu tinha
cravado errado na tabela). Nesse preço, modelo aberto em GPU alugada deixou de
ser o caminho barato: o Kling pela Magnific sai por ~US$ 0,07 no plano anual, com
qualidade muito superior e licença comercial escrita no plano — o que importa num
canal monetizado.

## A trava que este script tem e o animar.py não tinha

A conta é de terceiro e tem limite de crédito. Então aqui:
  - o padrão é NÃO gastar: sem --confirmar, ele só mostra o que faria;
  - existe teto duro de clipes por execução (--limite), default 1;
  - cada geração é contada e o total aparece no fim, em créditos e em dólar.
Foi exatamente a falta disso que queimou o saldo do RunPod.

## Anima claro, escurece depois (a regra do doc 22 §12)

Vale igual aqui: o still do canal tem luminância 7/255 e até 83% de preto
absoluto, e modelo i2v só anima o que distingue. Sobe clareado, volta escuro com
`graduar.py`.

Uso:
  python scripts/ancoras/animar_magnific.py --stills scratch/ancoras/todas --limite 1
  python scripts/ancoras/animar_magnific.py --stills ... --limite 1 --confirmar
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import casar_ancora as ca  # noqa: E402
import subir_clipes as sc  # noqa: E402

BASE = os.environ.get("MAGNIFIC_API_BASE", "https://api.magnific.com")
ROTA = "/v1/ai/image-to-video/kling-v2-5-pro"
# 140 créditos por clipe de 5s no Kling 2.5 720p (tabela oficial, 25/08/2026).
# O valor em dólar é derivado do plano anual Premium+, não é preço publicado:
# R$1.620/ano ÷ 600.000 créditos ÷ 5,15 BRL/USD.
CREDITOS_POR_CLIPE = 140
USD_POR_CREDITO = 0.00052


def env(chave, obrigatorio=True):
    v = os.environ.get(chave)
    if not v:
        p = os.path.join(RAIZ, ".env")
        if os.path.exists(p):
            for linha in open(p, encoding="utf-8", errors="ignore"):
                linha = linha.replace("\r", "").strip()
                if linha.startswith(chave + "="):
                    v = linha.split("=", 1)[1]
                    break
    if not v and obrigatorio:
        sys.exit(f"❌ falta {chave} no .env")
    return v


def _contexto_ssl():
    """🧨 O urllib deste Python não acha a raiz de certificado e devolve
    'certificate has expired' — que parece problema DO SERVIDOR e não é: o mesmo
    endereço abre normal no curl. Apontar o bundle do certifi resolve. Sem isto,
    a primeira chamada real falha com um erro que manda investigar o lado errado.
    """
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def chamar(rota, chave, corpo=None, metodo="GET"):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(BASE + rota, data=dados, method=metodo, headers={
        "x-magnific-api-key": chave,
        "Content-Type": "application/json",
        # 🧨 A mesma mina do RunPod e do Groq: User-Agent padrão do urllib leva 403
        # em quem está atrás de Cloudflare, e o erro parece falta de permissão.
        "User-Agent": "factorio-ancoras/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=120, context=_contexto_ssl()) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # 🧨 Ler o CORPO do erro. urllib levanta antes de ler, e sem isso um
        # "sem crédito" vira um 500 genérico e o script fica reprovando à toa.
        corpo_erro = ""
        try:
            corpo_erro = e.read().decode()[:400]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} em {rota}: {corpo_erro}") from None


def clarear(caminho, gama=0.30):
    """Levanta a sombra antes de mandar. O preto volta na pós (graduar.py)."""
    from PIL import Image
    import io
    im = Image.open(caminho).convert("RGB")
    tabela = [min(255, int((i / 255.0) ** gama * 255 + 0.5)) for i in range(256)] * 3
    buf = io.BytesIO()
    im.point(tabela).save(buf, format="PNG")
    return buf.getvalue()


def gerar(chave, imagem_b64, prompt, negativo, webhook=None):
    corpo = {"image": imagem_b64, "duration": "5", "cfg_scale": 0.5}
    if prompt:
        corpo["prompt"] = prompt[:2500]
    if negativo:
        corpo["negative_prompt"] = negativo[:2500]
    if webhook:
        corpo["webhook_url"] = webhook
    d = chamar(ROTA, chave, corpo, "POST")
    return (d.get("data") or {}).get("task_id"), (d.get("data") or {}).get("status")


def esperar(chave, task_id, teto_s=900):
    t0 = time.time()
    visto = None
    while time.time() - t0 < teto_s:
        d = chamar(f"{ROTA}/{task_id}", chave)
        dado = d.get("data") or {}
        st = dado.get("status")
        if st != visto:
            print(f"      {st} ({time.time()-t0:.0f}s)")
            visto = st
        if st == "COMPLETED":
            urls = dado.get("generated") or dado.get("result") or []
            if isinstance(urls, str):
                urls = [urls]
            return urls[0] if urls else None
        if st == "FAILED":
            raise RuntimeError(f"geração falhou: {json.dumps(dado)[:300]}")
        time.sleep(10)
    raise TimeoutError("passou do teto de espera")


def baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "factorio-ancoras/1.0"})
    with urllib.request.urlopen(req, timeout=300, context=_contexto_ssl()) as r,             open(destino, "wb") as f:
        f.write(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", required=True)
    ap.add_argument("--saida", default=os.path.join(RAIZ, "scratch", "ancoras", "clipes_kling"))
    ap.add_argument("--limite", type=int, default=1,
                    help="TETO DURO de clipes por execução. Conta de teste tem "
                         "crédito contado: o default é 1 de propósito.")
    ap.add_argument("--clarear", type=float, default=0.30)
    ap.add_argument("--confirmar", action="store_true",
                    help="sem isto, NADA é gerado e nada é cobrado")
    ap.add_argument("--pular-existentes", action="store_true", default=True)
    args = ap.parse_args()

    stills = sorted(f for f in os.listdir(args.stills) if f.lower().endswith((".png", ".jpg")))
    if not stills:
        sys.exit(f"❌ nenhum still em {args.stills}")
    os.makedirs(args.saida, exist_ok=True)
    if args.pular_existentes:
        prontos = {os.path.splitext(f)[0] for f in os.listdir(args.saida) if f.endswith(".mp4")}
        stills = [s for s in stills if os.path.splitext(s)[0] not in prontos]

    fila = stills[:args.limite]
    custo = len(fila) * CREDITOS_POR_CLIPE
    print(f"🎬 Magnific · Kling 2.5 Pro · 5s")
    print(f"   {len(stills)} still(s) na fila, {len(fila)} nesta execução (limite {args.limite})")
    print(f"   custo: {custo} créditos ≈ US$ {custo*USD_POR_CREDITO:.2f}\n")

    cenas = ca.carregar_catalogo()
    ids = [c["id"] for c in cenas]
    por_id = {c["id"]: c for c in cenas}
    negativo = json.load(open(os.path.join(HERE, "biblia_visual.json"),
                              encoding="utf-8")).get("negative_zh_video", "")

    for nome in fila:
        base = os.path.splitext(nome)[0]
        cid = sc.id_de_cena(base, ids)
        cena = por_id.get(cid) or {}
        print(f"  {base}")
        print(f"     prompt: {(cena.get('movimento_en') or '(sem cena no catálogo)')[:90]}")
        if not args.confirmar:
            continue

        chave = env("MAGNIFIC_API_KEY")
        b64 = base64.b64encode(clarear(os.path.join(args.stills, nome), args.clarear)).decode()
        task, st = gerar(chave, b64, cena.get("movimento_en"), negativo)
        if not task:
            print("     ❌ a API não devolveu task_id")
            continue
        print(f"     task {task} ({st})")
        url = esperar(chave, task)
        if not url:
            print("     ❌ terminou sem URL de vídeo")
            continue
        destino = os.path.join(args.saida, f"{base}.mp4")
        baixar(url, destino)
        mov, _, luz = sc.medir_movimento(destino)
        print(f"     ✅ {destino} · {os.path.getsize(destino)/1e6:.1f}MB · "
              f"mov {mov:.1f}% · luz {luz:.1f}")

    if not args.confirmar:
        print(f"\n(ensaio — nada gerado, nada cobrado). Pra valer: --confirmar")
    else:
        print(f"\n🏁 {len(fila)} clipe(s) · {custo} créditos ≈ US$ {custo*USD_POR_CREDITO:.2f}")


if __name__ == "__main__":
    main()
