#!/usr/bin/env python3
"""
gerar_stills.py — etapa 1 da biblioteca de âncoras visuais (doc 22).

Gera os STILLS que depois viram micro-clipes. Roda no Worker `factorio-imagens`
(Workers AI), que é GRÁTIS até 10.000 neurônios/dia (~173 imagens no FLUX
schnell). Nenhum gate de dinheiro aqui.

## Três arquivos, três responsabilidades

  biblia_visual.json   → COMO tudo parece (style block, paleta medida, proibições).
                          Muda quase nunca: mexer nele é rebranding.
  catalogo_cenas.json  → O QUE se produz (42 cenas mineradas dos 212 sermões).
                          Cresce sempre.
  este script          → junta os dois e chama o Worker.

Separar isso foi decisão do Gabriel em 22/08: "uma coisa é o estilo, outra é as
imagens que vamos criar a partir desse estilo".

## Por que still antes de vídeo

Ablation do paper "Lights, Camera, Consistency": sem seed frame de imagem, a
consistência despenca de 7,99 pra 0,55. E o descarte é o trabalho (12:1 a 25:1
na indústria). Descartar custa 3 segundos aqui e custa GPU lá na frente.

Uso:
  python scripts/ancoras/gerar_stills.py --listar
  python scripts/ancoras/gerar_stills.py --familia mar --dry-run
  python scripts/ancoras/gerar_stills.py --todas
  python scripts/ancoras/gerar_stills.py --tema provacao
  python scripts/ancoras/gerar_stills.py --todas --modelo @cf/leonardo/lucid-origin
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request

WORKER = "https://factorio-imagens.eternall.workers.dev/gerar"
PREFIXO_R2 = "ancoras/spurgeon"
HERE = os.path.dirname(os.path.abspath(__file__))


def carregar(nome):
    with open(os.path.join(HERE, nome), encoding="utf-8") as f:
        return json.load(f)


def segredo_worker():
    s = os.environ.get("FACTORIO_IMAGENS_SEGREDO")
    if s:
        return s
    env = os.path.join(HERE, "..", "..", ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8", errors="ignore"):
            line = line.replace("\r", "").strip()
            if line.startswith("FACTORIO_IMAGENS_SEGREDO="):
                return line.split("=", 1)[1]
    sys.exit("❌ FACTORIO_IMAGENS_SEGREDO não encontrado (env nem .env)")


def gerar(chave, prompt, segredo, modelo=None, tentativas=3):
    corpo = {"chave": chave, "prompt": prompt, "forca": True}
    if modelo:
        corpo["modelo"] = modelo
    dados = json.dumps(corpo).encode()
    erro = "?"
    for t in range(1, tentativas + 1):
        req = urllib.request.Request(
            WORKER, data=dados, method="POST",
            # 🧨 MINA (doc 21): sem User-Agent próprio o workers.dev devolve 403.
            headers={"x-segredo": segredo, "Content-Type": "application/json",
                     "User-Agent": "factorio-ancoras/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                d = json.loads(r.read())
            if d.get("ok"):
                return d
            erro = d.get("erro", "resposta sem ok")
            # 🧨 cota diária estourada: não adianta insistir, o dia acabou.
            if "4006" in str(erro) or "daily free allocation" in str(erro):
                return {"ok": False, "erro": "COTA_DIARIA", "detalhe": erro}
        except urllib.error.HTTPError as e:
            # 🧨 MINA (22/08): o Worker devolve o motivo NO CORPO com status 500,
            # e o urllib levanta antes de ler. Sem ler o corpo aqui, "cota
            # estourada" vira "erro 500 genérico" e o script insiste 42 vezes
            # à toa (custou 7 minutos numa rodada).
            try:
                corpo = json.loads(e.read().decode())
                erro = corpo.get("erro", str(e))
            except Exception:
                erro = str(e)[:160]
            if "4006" in erro or "daily free allocation" in erro:
                return {"ok": False, "erro": "COTA_DIARIA", "detalhe": erro}
        except Exception as e:
            erro = str(e)[:160]
        if t < tentativas:
            time.sleep(3 * t)
    return {"ok": False, "erro": erro}


def env_fabrica(chave):
    v = os.environ.get(chave)
    if v:
        return v
    env = os.path.join(HERE, "..", "..", ".env")
    for line in open(env, encoding="utf-8", errors="ignore"):
        line = line.replace(chr(13), "").strip()
        if line.startswith(chave + "="):
            return line.split("=", 1)[1]
    sys.exit(f"❌ {chave} não encontrado no .env")


def gerar_openai(chave_r2, prompt, s3, tentativas=3):
    """Rota alternativa: a Workers AI tem teto DIÁRIO de 10.000 neurônios, e ele
    acaba rápido. A OpenAI é paga por imagem, então serve pra não travar o dia.
    Grava no MESMO lugar do R2 pra esteira não saber a diferença."""
    key = env_fabrica("OPENAI_API_KEY")
    body = json.dumps({"model": "gpt-image-1", "prompt": prompt,
                       "size": "1536x1024", "n": 1}).encode()
    erro = "?"
    for t in range(1, tentativas + 1):
        req = urllib.request.Request("https://api.openai.com/v1/images/generations",
              data=body, method="POST",
              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                       "User-Agent": "factorio-ancoras/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read())
            img = base64.b64decode(d["data"][0]["b64_json"])
            s3.put_object(Bucket="mananciall", Key=chave_r2, Body=img,
                          ContentType="image/png")
            return {"ok": True, "bytes": len(img)}
        except urllib.error.HTTPError as e:
            try:
                erro = json.loads(e.read().decode()).get("error", {}).get("message", str(e))[:150]
            except Exception:
                erro = str(e)[:150]
        except Exception as e:
            erro = str(e)[:150]
        if t < tentativas:
            time.sleep(4 * t)
    return {"ok": False, "erro": erro}


def cliente_r2():
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=env_fabrica("R2_ENDPOINT"),
        aws_access_key_id=env_fabrica("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env_fabrica("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"), region_name="auto")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familia", help="capela|mar|fogo|natureza|objetos|arquitetura|abstrato")
    ap.add_argument("--tema", help="gera só as cenas com esta etiqueta (ex: provacao)")
    ap.add_argument("--cena", help="gera só esta cena pelo id")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--modelo", help="modelo Workers AI (padrão: flux-1-schnell do Worker)")
    ap.add_argument("--via", choices=["cloudflare", "openai"], default="cloudflare",
                    help="cloudflare = grátis com teto diário · openai = pago por imagem, sem teto")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    biblia = carregar("biblia_visual.json")
    catalogo = carregar("catalogo_cenas.json")
    cenas = catalogo["cenas"]
    estilo = biblia["style_block"]

    if args.listar:
        por_fam = {}
        for c in cenas:
            por_fam.setdefault(c["familia"], []).append(c)
        for fam, itens in por_fam.items():
            print(f"\n{fam} ({len(itens)})")
            for c in itens:
                print(f"  {c['id']:22} {c['nome_pt']:26} [{','.join(c['temas'])}]")
        print(f"\n{len(cenas)} cenas no catálogo")
        return

    alvo = cenas
    if args.cena:
        alvo = [c for c in cenas if c["id"] == args.cena]
    elif args.familia:
        alvo = [c for c in cenas if c["familia"] == args.familia]
    elif args.tema:
        alvo = [c for c in cenas if args.tema in c["temas"]]
    elif not args.todas:
        sys.exit("informe --todas, --familia X, --tema Y, --cena Z ou --listar")
    if not alvo:
        sys.exit("❌ nenhuma cena bate com o filtro")

    usa_openai = args.via == "openai"
    segredo = s3 = None
    if not args.dry_run:
        if usa_openai:
            s3 = cliente_r2()
        else:
            segredo = segredo_worker()
    ok = falha = 0
    t0 = time.time()
    via = "OpenAI gpt-image-1 (pago)" if usa_openai else (args.modelo or "flux-1-schnell (grátis)")
    print(f"🎨 {len(alvo)} cenas | via: {via}")

    for i, c in enumerate(alvo, 1):
        chave = f"{PREFIXO_R2}/{c['familia']}/{c['id']}.png"
        prompt = c["imagem_en"] + estilo
        if args.dry_run:
            print(f"  [dry] {chave}")
            continue
        t = time.time()
        r = gerar_openai(chave, prompt, s3) if usa_openai else gerar(chave, prompt, segredo, args.modelo)
        if r.get("ok"):
            ok += 1
            print(f"  ✅ {i:>2}/{len(alvo)} {c['id']:22} {r['bytes']/1000:>4.0f}KB {time.time()-t:>4.1f}s")
        elif r.get("erro") == "COTA_DIARIA":
            print(f"\n🛑 COTA DIÁRIA DA WORKERS AI ESTOURADA em {ok} imagens.")
            print("   Reseta amanhã. Pra passar disso: plano Workers Paid (US$ 5/mês).")
            break
        else:
            falha += 1
            print(f"  ❌ {i:>2}/{len(alvo)} {c['id']:22} {r.get('erro')}")

    if not args.dry_run:
        print(f"\n🏁 {ok} gerados, {falha} falhas, {time.time()-t0:.0f}s")
        print(f"   R2: {PREFIXO_R2}/  (custo: zero)")


if __name__ == "__main__":
    main()
