#!/usr/bin/env python3
"""
montar_short.py — monta o short COMPLETO com as cenas trocando junto com a fala.

## O que muda em relação ao short anterior

Antes: uma âncora fixa o clipe inteiro. Agora o trecho é dividido em BATIDAS
(fronteiras de frase, tiradas do word-level) e cada batida recebe a cena que
casa com o que está sendo dito naquele instante.

## Por que o corte cai em fronteira de frase

Duas razões, as duas com fonte (doc 22 §11c):
  1. O estudo de 1.200 Reels mede que ~12 planos/60s rende MAIS que ~24, ou
     seja ~5s por plano. Frase do Spurgeon dá mais ou menos isso.
  2. O que captura atenção é o INÍCIO do movimento, não o movimento contínuo
     (Abrams & Christ 2003). Trocar de cena É um onset. Cortar no meio da frase
     desperdiça o onset em cima de uma palavra sem peso.

## Fonte das cenas

Por padrão usa os STILLS (com push-in lento na composição), porque eles já estão
prontos e bonitos. Quando os clipes animados existirem, é só `--fonte video`:
a composição aceita os dois.

Uso:
  python scripts/ancoras/montar_short.py --sermao 1 --clip 1
  python scripts/ancoras/montar_short.py --sermao 1 --clip 1 --min-batida 4.5
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, "..", ".."))
REMOTION = os.path.join(RAIZ, "remotion")
PUBLIC_SHORTS = os.path.join(REMOTION, "public", "shorts")
PUBLIC_CENAS = os.path.join(REMOTION, "public", "cenas")
OUT_DIR = os.path.join(REMOTION, "out", "shorts")
PREFIXO = "channels/channels_youtube/treasures_charlesspurgeon"
FADE_S = 0.15

sys.path.insert(0, HERE)
sys.path.insert(0, REMOTION)
import casar_ancora as ca  # noqa: E402
import canais  # noqa: E402

PUBLIC_IMAGENS = os.path.join(REMOTION, "public", "images")


def asset_rotativo(cli, prefixo_canal, subdir, padrao, n):
    """Mesma escolha determinística do build_job: o asset varia por sermão mas é
    sempre o mesmo pro mesmo N, então re-render dá o mesmo vídeo."""
    res = cli.list_objects_v2(Bucket="mananciall",
                              Prefix=f"{prefixo_canal}/_assets/{subdir}/", MaxKeys=200)
    chaves = sorted(o["Key"] for o in res.get("Contents", [])
                    if re.search(padrao, o["Key"]))
    if not chaves:
        sys.exit(f"❌ nenhum asset em _assets/{subdir}/ casando {padrao}")
    return chaves[(int(n) - 1) % len(chaves)]


def assets_da_marca(cli, C, nnnn):
    """🧨 A composição NÃO tem mais default de fundo nem de busto (commit 0b2be45:
    o default nomeado fazia o vídeo do Moody exibir o Spurgeon). Quem monta é
    obrigado a mandar. Sem isso o short renderiza sem catedral e sem busto, e
    nada acusa erro: sai um vídeo, só que careca."""
    A = C.get("assets") or sys.exit(f"❌ canal {C['slug']!r} sem bloco `assets` em canais.py")
    os.makedirs(PUBLIC_IMAGENS, exist_ok=True)
    saida = {}
    for prop, campo in (("backgroundImageUrl", "fundo"), ("preacherImageUrl", "busto")):
        chave = asset_rotativo(cli, C["prefix"], *A[campo], nnnn)
        nome = chave.rsplit("/", 1)[-1]
        # force: o nome local é contrato com o .tsx e é o MESMO entre canais, então
        # cache por existência serviria a catedral do Spurgeon num vídeo do Moody
        cli.download_file("mananciall", chave, os.path.join(PUBLIC_IMAGENS, nome))
        saida[prop] = f"images/{nome}"
    # o campo é `pregador` (o nome como o espectador conhece), não o nome do canal
    saida["attribution"] = (C.get("pregador") or "").upper()
    return saida


def s3():
    return ca.s3()


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"❌ falhou: {' '.join(map(str, cmd))}\n{(r.stderr or r.stdout)[-1500:]}")
    return r


def batidas(words, min_s=4.0, max_s=9.0):
    """Divide o clipe em batidas em FRONTEIRA DE FRASE. Uma batida curta demais
    vira corte nervoso; longa demais desperdiça o catálogo."""
    frases, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?;:][\"')\]]?$", w["text"]):
            frases.append(cur); cur = []
    if cur:
        frases.append(cur)

    out, buf = [], []
    for f in frases:
        buf.extend(f)
        dur = (buf[-1]["end"] - buf[0]["start"]) / 1000.0
        if dur >= min_s:
            out.append(buf); buf = []
    if buf:
        if out and (buf[-1]["end"] - buf[0]["start"]) / 1000.0 < min_s / 2:
            out[-1].extend(buf)          # sobra curta: gruda na anterior
        else:
            out.append(buf)
    # quebra batida longa demais no meio (sem fronteira disponível)
    final = []
    for b in out:
        dur = (b[-1]["end"] - b[0]["start"]) / 1000.0
        if dur > max_s and len(b) > 6:
            meio = len(b) // 2
            final += [b[:meio], b[meio:]]
        else:
            final.append(b)
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sermao", help="número do sermão (AMBÍGUO: ver --pasta)")
    ap.add_argument("--pasta", help="nome COMPLETO da pasta no R2. Preferir este: "
                    "o acervo tem numeração duplicada (dois sermões '0001').")
    ap.add_argument("--clip", type=int, default=1)
    ap.add_argument("--fonte", choices=["imagem", "video"], default="imagem")
    ap.add_argument("--min-batida", type=float, default=4.0)
    ap.add_argument("--sem-render", action="store_true")
    ap.add_argument("--trilha", default="worship_piano_01",
                    help="faixa em _globalassets/worship (sem extensão), ou 'nenhuma'")
    ap.add_argument("--trilha-volume", type=float, default=0.07)
    args = ap.parse_args()

    cli = s3()
    C = canais.get("spurgeon")
    # 🧨 NUMERAÇÃO DUPLICADA. O acervo tem DOIS sermões '0001'
    # (consolation_in_christ e the_immutability_of_god), e pelo menos 9 números
    # colidem. Casar por prefixo e pegar o primeiro publica o sermão ERRADO sem
    # dar erro nenhum. Quando o número é ambíguo, este script recusa e pede
    # --pasta em vez de escolher por conta própria.
    if args.pasta:
        alvo, nnnn = f"{C['prefix']}/{args.pasta}", args.pasta.split("_")[0]
        res = cli.list_objects_v2(Bucket="mananciall", Prefix=alvo + "/", MaxKeys=200)
        keys = [o["Key"] for o in res.get("Contents", [])]
        if not keys:
            sys.exit(f"❌ pasta {args.pasta!r} não achada no R2")
        pasta = alvo
    else:
        if not args.sermao:
            sys.exit("informe --pasta (preferido) ou --sermao N")
        nnnn = f"{int(args.sermao):04d}"
        res = cli.list_objects_v2(Bucket="mananciall",
                                  Prefix=f"{C['prefix']}/{nnnn}", MaxKeys=400)
        keys = [o["Key"] for o in res.get("Contents", [])]
        if not keys:
            sys.exit(f"❌ sermão {nnnn} não achado no R2")
        pastas = sorted({k.split("/")[3] for k in keys})
        if len(pastas) > 1:
            lista = chr(10).join("   " + x for x in pastas)
            sys.exit(f"❌ '{nnnn}' é ambíguo, casa {len(pastas)} pastas:" + chr(10)
                     + lista + chr(10) + "   Use --pasta <nome completo>.")
        pasta = f"{C['prefix']}/{pastas[0]}"
        keys = [k for k in keys if k.startswith(pasta + "/")]
    arquivos = [k.rsplit("/", 1)[1] for k in keys]

    meta = json.loads(cli.get_object(Bucket="mananciall", Key=f"{pasta}/clips_meta.json")["Body"].read())
    clip = meta["clips"][args.clip - 1]
    dur_ms = clip["end_ms"] - clip["start_ms"]
    # a fonte entra no nome: sem isso a montagem em vídeo sobrescreve a de stills
    # e não sobra com o que comparar
    # tag pelo nome da PASTA, não pelo número: dois '0001' gerariam o mesmo
    # arquivo e um sobrescreveria o outro
    base_tag = pasta.rsplit("/", 1)[-1]
    tag = f"{base_tag}_c{args.clip:02d}_cenas_{args.fonte}"
    print(f"📖 {meta.get('title', nnnn)} · clipe {args.clip} · {dur_ms/1000:.1f}s")
    print(f"   \"{clip['hook_text']}\"\n")

    # 1. batidas + cena por batida
    cenas_cat = ca.carregar_catalogo()
    bs = batidas(clip["words"], min_s=args.min_batida)
    # bússola do clipe inteiro: guia as batidas que sozinhas não casam
    fam_pref = ca.familia_dominante(clip["text"], cenas_cat)
    usados, shots = set(), []
    for i, b in enumerate(bs):
        texto = " ".join(w["text"] for w in b)
        r, _ = ca.escolher(texto, cenas_cat, usados, familia_pref=fam_pref)
        usados.add(r["cena"]["id"])
        ini = 0 if i == 0 else b[0]["start"]
        fim = dur_ms if i == len(bs) - 1 else bs[i + 1][0]["start"]
        shots.append({"start": ini, "end": fim, "cena": r["cena"],
                      "pontos": r["pontos"], "motivos": r["motivos"][:3]})
        print(f"  {ini/1000:>5.1f}s→{fim/1000:>5.1f}s  {r['cena']['nome_pt']:24} "
              f"({r['pontos']:>4} pts) {r['motivos'][:2]}")
        print(f"          \"{texto[:78]}...\"")

    # 2. assets locais (a composição lê de public/)
    os.makedirs(PUBLIC_CENAS, exist_ok=True)
    os.makedirs(PUBLIC_SHORTS, exist_ok=True)
    ext = "mp4" if args.fonte == "video" else "png"
    prefixo_r2 = "renders/ancoras" if args.fonte == "video" else "ancoras/spurgeon"
    for sh in shots:
        c = sh["cena"]
        sh["kind"] = "video" if args.fonte == "video" else "image"
        nome = f"{c['id']}.{ext}"
        destino = os.path.join(PUBLIC_CENAS, nome)
        if not os.path.exists(destino):
            chave = (f"{prefixo_r2}/{c['id']}.{ext}" if args.fonte == "video"
                     else f"{prefixo_r2}/{c['familia']}/{c['id']}.png")
            try:
                cli.download_file("mananciall", chave, destino)
            except Exception:
                # Nem toda cena tem clipe: o verificador recusa subir o que saiu
                # congelado. Melhor a cena aparecer como still (com push-in) do
                # que a montagem inteira quebrar por causa de uma batida.
                if args.fonte != "video":
                    raise
                if os.path.exists(destino):
                    os.remove(destino)
                nome = f"{c['id']}.png"
                destino = os.path.join(PUBLIC_CENAS, nome)
                if not os.path.exists(destino):
                    cli.download_file("mananciall",
                        f"ancoras/spurgeon/{c['familia']}/{c['id']}.png", destino)
                sh["kind"] = "image"
                print(f"     ↩️  {c['id']}: sem clipe no R2, usando o still")
        sh["src"] = f"cenas/{nome}"
        if sh["kind"] == "video":
            # duração real do mp4: a composição usa pra esticar o clipe até
            # cobrir a cena em vez de repetir o loop no meio dela
            p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "csv=p=0", destino],
                               capture_output=True, text=True)
            try:
                sh["clip_ms"] = int(float(p.stdout.strip()) * 1000)
            except ValueError:
                sh["clip_ms"] = 0

    # 3. áudio do clipe
    master = None
    for f in arquivos:
        if re.match(r"^sermon[\w-]*\.(wav|mp3)$", f):
            master = f"{pasta}/{f}"; break
    if not master:
        sys.exit("❌ áudio master não achado")
    cache = os.path.join(PUBLIC_SHORTS, "_masters", f"{nnnn}_{os.path.basename(master)}")
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    if not os.path.exists(cache):
        print(f"\n⬇️  baixando master ...")
        cli.download_file("mananciall", master, cache)
    wav = os.path.join(PUBLIC_SHORTS, f"{tag}.wav")
    d = dur_ms / 1000.0
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{clip['start_ms']/1000:.3f}", "-t", f"{d:.3f}",
         "-i", cache, "-af", f"afade=t=in:st=0:d={FADE_S},afade=t=out:st={d-FADE_S:.3f}:d={FADE_S}",
         "-ar", "44100", "-ac", "2", wav])

    # 3b. trilha de fundo
    bgm = None
    if args.trilha and args.trilha != "nenhuma":
        os.makedirs(os.path.join(PUBLIC_SHORTS, "_bgm"), exist_ok=True)
        local = os.path.join(PUBLIC_SHORTS, "_bgm", f"{args.trilha}.mp3")
        if not os.path.exists(local):
            print(f"⬇️  baixando trilha {args.trilha} ...")
            cli.download_file("mananciall",
                f"channels/channels_youtube/_globalassets/worship/{args.trilha}.mp3", local)
        bgm = f"shorts/_bgm/{args.trilha}.mp3"
        print(f"🎵 trilha: {args.trilha} @ {args.trilha_volume}")

    # 4. props
    props = {
        "audioUrl": f"shorts/{tag}.wav",
        "words": clip["words"],
        "hookText": clip["hook_text"],
        "anchorShots": [{"start": s["start"], "end": s["end"], "src": s["src"],
                         "kind": s["kind"],
                         "nome": s["cena"]["nome_pt"],
                         **({"clipMs": s["clip_ms"]} if s.get("clip_ms") else {})}
                        for s in shots],
    }
    props.update(assets_da_marca(cli, C, nnnn))
    print(f"🖼️  fundo/busto: {props['backgroundImageUrl']} · {props['preacherImageUrl']}")
    if bgm:
        props["bgmUrl"] = bgm
        props["bgmVolume"] = args.trilha_volume
    props_path = os.path.join(PUBLIC_SHORTS, f"{tag}_props.json")
    json.dump(props, open(props_path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\n🎞️  {len(shots)} cenas na linha do tempo")

    if args.sem_render:
        print(f"(--sem-render) props em {props_path}")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    saida = os.path.join(OUT_DIR, f"{tag}.mp4")
    npx = "npx.cmd" if os.name == "nt" else "npx"
    print("🎬 renderizando ...")
    run([npx, "remotion", "render", "Short-Sermon", saida,
         f"--props={props_path}", "--log=error"], cwd=REMOTION)
    print(f"✅ {saida} ({os.path.getsize(saida)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
