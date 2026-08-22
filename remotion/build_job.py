#!/usr/bin/env python3
"""
build_job.py — Monta o KIT de UM vídeo (de qualquer canal) para o Remotion renderizar.

Dado o número do sermão, este script:
  1. Localiza a pasta do sermão no R2 (bucket mananciall)
  2. Baixa os assets por-sermão (áudio, transcript, hook, outro) para <public>/storage/sermons/<N>/
  3. Seleciona e baixa bg/busto/trilha ROTATIVOS (fórmula determinística por N) para <public>/images e <public>/audio
  4. Baixa a BGM fixa do hook (432hz)
  5. Gera o QR real apontando pro redirect do canal (`redirect_base` + N) -> <public>/storage/sermons/<N>/qr.png
  6. Escreve props.json (caminhos LOCAIS relativos ao public/, resolvidos por staticFile no Remotion)

A duração do vídeo NÃO é definida aqui — o calculateMetadata do Remotion mede os áudios e calcula sozinho
(isso é o que mata o bug do vídeo de 3h). Aqui só entregamos os caminhos certos.

Uso:
  python build_job.py --canal moody --sermon 1 [--public-dir ./public] [--out ./props_0001.json]

Roda tanto local quanto dentro do container do RunPods (o rp_handler.py chama este script).
"""
import os
import sys
import json
import argparse
import re
import boto3
from botocore.config import Config

import canais

# Preenchidos em main() a partir de canais.get(--canal).
C = None
BUCKET = CHANNEL_PREFIX = None
GLOBAL_WORSHIP_PREFIX = "channels/channels_youtube/_globalassets/worship"


def load_env(path):
    env = {}
    if os.path.exists(path):
        for raw in open(path, encoding="utf-8"):
            line = raw.replace("\r", "").strip()
            if not line or line.startswith("#"):
                continue
            i = line.find("=")
            if i > 0:
                env[line[:i]] = line[i + 1:]
    # também aceita variáveis já no ambiente (RunPods injeta por env)
    for k in ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT", "R2_PUBLIC_URL"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def s3_client(env):
    return boto3.client(
        "s3",
        endpoint_url=env["R2_ENDPOINT"],
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def list_keys(s3, prefix):
    keys = []
    token = None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        res = s3.list_objects_v2(**kw)
        for o in res.get("Contents", []):
            keys.append(o["Key"])
        if res.get("IsTruncated"):
            token = res.get("NextContinuationToken")
        else:
            break
    return keys


def download(s3, key, dest, force=False):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # force=True para assets MUTÁVEIS (CTAs): o volume public/ é persistente e o
    # cache-por-existência já baixou "voz velha" pra dentro do vídeo uma vez. Nunca de novo.
    if not force and os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"  · já existe: {os.path.relpath(dest)}")
        return
    print(f"  ↓ {key}  ->  {os.path.relpath(dest)}")
    s3.download_file(BUCKET, key, dest)


def find_sermon_folder(s3, sermon_num):
    """Acha o prefixo da pasta do sermão (ex: .../0021_-_christs_...) pelo número zero-padded."""
    nnnn = f"{int(sermon_num):04d}"
    keys = list_keys(s3, f"{CHANNEL_PREFIX}/{nnnn}")
    if not keys:
        # sermões combinados (ex: 0007-0008_-_...) — tenta achar por prefixo do número
        keys = [k for k in list_keys(s3, f"{CHANNEL_PREFIX}/") if re.search(rf"/{nnnn}[-_]", k)]
    if not keys:
        raise SystemExit(f"❌ Sermão {nnnn} não encontrado no R2 sob {CHANNEL_PREFIX}/")
    # o prefixo da pasta é tudo até o primeiro arquivo
    folder = keys[0].rsplit("/", 1)[0]
    return folder, nnnn


def pick_rotating(s3, subdir, pattern, n):
    """Seleção determinística de asset rotativo por N (igual à lógica antiga do ffmpeg)."""
    keys = sorted(
        k for k in list_keys(s3, f"{CHANNEL_PREFIX}/_assets/{subdir}/")
        if re.search(pattern, k)
    )
    if not keys:
        raise SystemExit(f"❌ Nenhum asset em _assets/{subdir}/ casando {pattern}")
    return keys[(int(n) - 1) % len(keys)]


def pick_bgm(s3, n):
    keys = sorted(k for k in list_keys(s3, f"{GLOBAL_WORSHIP_PREFIX}/") if re.search(r"worship_.*\.mp3$", k))
    if not keys:
        keys = sorted(list_keys(s3, f"{GLOBAL_WORSHIP_PREFIX}/"))
    return keys[(int(n) - 1) % len(keys)]


def generate_qr(dest, url):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
    except ImportError:
        raise SystemExit("❌ Falta a lib 'qrcode'. Instale: pip install \"qrcode[pil]\"")
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=12, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a0f00", back_color="white")
    img.save(dest)
    print(f"  🔳 QR gerado ({url})  ->  {os.path.relpath(dest)}")


def pick_first(keys, *needles):
    """Retorna a primeira key cujo nome de arquivo casa qualquer needle (regex)."""
    for n in needles:
        for k in keys:
            if re.search(n, k.rsplit("/", 1)[-1], re.IGNORECASE):
                return k
    return None


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--sermon", required=True, help="Número do sermão (1, 21, ...)")
    ap.add_argument("--public-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "public"))
    ap.add_argument("--out", default=None, help="Caminho do props.json de saída")
    ap.add_argument("--env", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
    args = ap.parse_args()

    global C, BUCKET, CHANNEL_PREFIX
    C = canais.get(args.canal)
    BUCKET, CHANNEL_PREFIX = C["bucket"], C["prefix"]

    env = load_env(os.path.abspath(args.env))
    for req in ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT"):
        if not env.get(req):
            raise SystemExit(f"❌ Falta {req} no .env / ambiente")

    s3 = s3_client(env)
    public = os.path.abspath(args.public_dir)

    folder, nnnn = find_sermon_folder(s3, args.sermon)
    print(f"🎯 Sermão {nnnn}  ->  {folder}")
    sermon_keys = list_keys(s3, folder + "/")

    # --- arquivos por-sermão (robusto a variações de nome) ---
    wanted = {
        # o acervo tem os dois formatos: 44 sermões em .wav e 68 em .mp3
        "sermon":     pick_first(sermon_keys, r"^sermon_\d+\.(wav|mp3)$", r"sermon.*\.(wav|mp3)$"),
        "transcript": pick_first(sermon_keys, r"^transcript\.json$"),
        "hook_wav":   pick_first(sermon_keys, r"^hook\.wav$"),
        "hook_json":  pick_first(sermon_keys, r"^hook\.json$"),
        "outro_wav":  pick_first(sermon_keys, r"^cta_narration\.wav$"),
        "outro_json": pick_first(sermon_keys, r"^cta_narration\.json$"),
        "marketing":  pick_first(sermon_keys, r"^marketing_meta\.json$"),
    }
    missing = [k for k, v in wanted.items() if not v]
    if missing:
        raise SystemExit(f"❌ Sermão {nnnn} sem arquivos essenciais: {missing}\n   Keys: {[k.rsplit('/',1)[-1] for k in sermon_keys]}")

    sd = os.path.join(public, "storage", "sermons", nnnn)
    # preserva a extensão de origem (.wav ou .mp3) — renomear quebraria a leitura do áudio
    sermon_ext = os.path.splitext(wanted["sermon"])[1].lower() or ".wav"
    sermon_local = f"sermon{sermon_ext}"
    download(s3, wanted["sermon"],     os.path.join(sd, sermon_local))
    download(s3, wanted["transcript"], os.path.join(sd, "transcript.json"))
    download(s3, wanted["hook_wav"],   os.path.join(sd, "hook.wav"))
    download(s3, wanted["hook_json"],  os.path.join(sd, "hook.json"))
    download(s3, wanted["outro_wav"],  os.path.join(sd, "cta_narration.wav"))
    download(s3, wanted["outro_json"], os.path.join(sd, "cta_narration.json"))

    # marketing meta (título)
    mk_dest = os.path.join(sd, "marketing_meta.json")
    download(s3, wanted["marketing"], mk_dest)
    marketing = json.load(open(mk_dest, encoding="utf-8"))
    sermon_title = json.load(open(os.path.join(sd, "transcript.json"), encoding="utf-8")).get("title", f"Sermon {nnnn}")

    # --- assets rotativos (determinísticos por N) ---
    A = C.get("assets")
    if not A:
        raise SystemExit(f"❌ canal {C['slug']!r} não tem bloco `assets` em canais.py.\n"
                         f"   Gere os assets visuais antes: scripts/gerar_assets_canal.py")
    bg_key = pick_rotating(s3, *A["fundo"], args.sermon)
    bust_key = pick_rotating(s3, *A["busto"], args.sermon)
    bgm_key = pick_bgm(s3, args.sermon)

    bg_name = bg_key.rsplit("/", 1)[-1]
    bust_name = bust_key.rsplit("/", 1)[-1]
    bgm_name = bgm_key.rsplit("/", 1)[-1]

    download(s3, bg_key,   os.path.join(public, "images", bg_name))
    download(s3, bust_key, os.path.join(public, "images", bust_name))
    download(s3, bgm_key,  os.path.join(public, "audio", bgm_name))

    # --- assets FIXOS: chave no R2 -> NOME LOCAL que o staticFile() dos
    # templates espera cravado. Ver a nota "nome local é contrato" em canais.py.
    for origem, local in A["fixos"].items():
        download(s3, f"{CHANNEL_PREFIX}/_assets/{origem}", os.path.join(public, "images", local))
    # BGM fixa do hook (432hz)
    download(s3, f"{GLOBAL_WORSHIP_PREFIX}/frequencial_432hz_01.mp3", os.path.join(public, "audio", "frequencial_432hz_01.mp3"))
    # narração FIXA das telas de CTA. Canal sem CTA gravado (`cta_assets: []`)
    # simplesmente não recebe o prop: o schema marca opcional e o template roda
    # a animação por duração-fallback, mudo. Baixar aqui quebraria o canal novo.
    tem_cta = bool(C.get("cta_assets"))
    if tem_cta:
        # force=True: são mutáveis (regravadas ao trocar a copy). Nunca cache.
        download(s3, f"{CHANNEL_PREFIX}/_assets/introfixed.mp3", os.path.join(public, "audio", "introfixed.mp3"), force=True)
        download(s3, f"{CHANNEL_PREFIX}/_assets/finalfixed.mp3", os.path.join(public, "audio", "finalfixed.mp3"), force=True)
    else:
        print("  · canal sem CTA narrado: telas de CTA ficam mudas (fallback do template)")

    # --- QR real ---
    # `redirect_base` já termina em "v=" e carrega o formato de CADA canal
    # (o do Spurgeon é o legado sem canal, que os QRs publicados usam).
    redirect_url = f"{C['redirect_base']}{nnnn}"
    generate_qr(os.path.join(sd, "qr.png"), redirect_url)

    # --- props.json (caminhos relativos ao public/, resolvidos por staticFile) ---
    rel = f"storage/sermons/{nnnn}"
    props = {
        "narrationUrl": f"{rel}/{sermon_local}",
        "bgmUrl": f"audio/{bgm_name}",
        "bgmVolume": 0.05,
        "backgroundImageUrl": f"images/{bg_name}",
        "preacherImageUrl": f"images/{bust_name}",
        "transcriptSlug": f"{rel}/transcript.json",
        "subtitleStyle": "classic",
        "kenBurnsIntensity": "subtle",
        "qrCodeUrl": f"{rel}/qr.png",
        "ctaBookTitle": C["cta_livro"],
        "sermonTitle": sermon_title,
        "sermonNumber": nnnn,
        "marketingTitle": marketing.get("marketingTitle", sermon_title),
        # texto CURTO e magnético da capa (≤6 palavras). Cai no título se ainda não existir.
        "thumbnailText": marketing.get("thumbnailText", ""),
        # hook (dinâmico) + outro hook (dinâmico). CTAs fixos ficam SILENCIOSOS nesta v1
        # (SpurgeonCTA roda a animação por duração-fallback, sem narração) — simplifica e evita asset faltante.
        "hookAudioUrl": f"{rel}/hook.wav",
        "hookTranscriptSlug": f"{rel}/hook.json",
        "outroHookAudioUrl": f"{rel}/cta_narration.wav",
        "outroHookTranscriptSlug": f"{rel}/cta_narration.json",
        # narração de marketing FIXA das telas de CTA (inscrição + QR) — voz do canal
        **({"introCtaAudioUrl": "audio/introfixed.mp3",
            "outroCtaAudioUrl": "audio/finalfixed.mp3"} if tem_cta else {}),
        # placeholder exigido pelo tipo; a duração real vem do calculateMetadata
        "totalSermonFrames": 63084,
    }

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), f"props_{nnnn}.json")
    json.dump(props, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n✅ Job pronto. Props -> {out}")
    print(f"   Render: npx remotion render Sermon-Full-Production out_{nnnn}.mp4 --props={os.path.basename(out)}")
    return out


if __name__ == "__main__":
    main()
