#!/usr/bin/env python3
"""
build_job.py — Prepara UM sermão do canal Treasures of Spurgeon para render no Remotion.

Dado o número do sermão, este script:
  1. Localiza a pasta do sermão no R2 (bucket mananciall)
  2. Baixa os assets por-sermão (áudio, transcript, hook, outro) para <public>/storage/sermons/<N>/
  3. Seleciona e baixa bg/busto/trilha ROTATIVOS (fórmula determinística por N) para <public>/images e <public>/audio
  4. Baixa a BGM fixa do hook (432hz)
  5. Gera o QR real apontando pro redirect (https://mananciall.org/go?s=yt&v=<N>) -> <public>/storage/sermons/<N>/qr.png
  6. Escreve props.json (caminhos LOCAIS relativos ao public/, resolvidos por staticFile no Remotion)

A duração do vídeo NÃO é definida aqui — o calculateMetadata do Remotion mede os áudios e calcula sozinho
(isso é o que mata o bug do vídeo de 3h). Aqui só entregamos os caminhos certos.

Uso:
  python build_job.py --sermon 1 [--public-dir ./public] [--out ./props_0001.json]

Roda tanto local quanto dentro do container do RunPods (o rp_handler.py chama este script).
"""
import os
import sys
import json
import argparse
import re
import boto3
from botocore.config import Config

BUCKET = "mananciall"
CHANNEL_PREFIX = "channels/channels_youtube/treasures_charlesspurgeon"
GLOBAL_WORSHIP_PREFIX = "channels/channels_youtube/_globalassets/worship"
REDIRECT_BASE = "https://mananciall.org/go"  # QR -> Worker de redirect (loga + UTM). Ver 04_ROADMAP.md.


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


def download(s3, key, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
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
    ap.add_argument("--sermon", required=True, help="Número do sermão (1, 21, ...)")
    ap.add_argument("--public-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "public"))
    ap.add_argument("--out", default=None, help="Caminho do props.json de saída")
    ap.add_argument("--env", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
    args = ap.parse_args()

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
        "sermon":     pick_first(sermon_keys, r"^sermon_\d+\.wav$", r"sermon.*\.wav$"),
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
    download(s3, wanted["sermon"],     os.path.join(sd, "sermon.wav"))
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
    bg_key = pick_rotating(s3, "cathedral", r"cathedral_bg_cf_\d+\.png$", args.sermon)
    bust_key = pick_rotating(s3, "avatars", r"spurgeon_bust_cf_\d+\.png$", args.sermon)
    bgm_key = pick_bgm(s3, args.sermon)

    bg_name = bg_key.rsplit("/", 1)[-1]
    bust_name = bust_key.rsplit("/", 1)[-1]
    bgm_name = bgm_key.rsplit("/", 1)[-1]

    download(s3, bg_key,   os.path.join(public, "images", bg_name))
    download(s3, bust_key, os.path.join(public, "images", bust_name))
    download(s3, bgm_key,  os.path.join(public, "audio", bgm_name))

    # --- assets FIXOS que os componentes referenciam por staticFile hardcoded ---
    for fixed in ["cathedral/cathedral_bg_cf_1.png", "cathedral/cathedral_bg_cf_3.png", "avatars/spurgeon_base.png"]:
        name = fixed.rsplit("/", 1)[-1]
        download(s3, f"{CHANNEL_PREFIX}/_assets/{fixed}", os.path.join(public, "images", name))
    # avatar do canal (SubscribeUpperThird referencia como spurgeon_avatar.png)
    download(s3, f"{CHANNEL_PREFIX}/_assets/channelavatar.png", os.path.join(public, "images", "spurgeon_avatar.png"))
    # BGM fixa do hook (432hz)
    download(s3, f"{GLOBAL_WORSHIP_PREFIX}/frequencial_432hz_01.mp3", os.path.join(public, "audio", "frequencial_432hz_01.mp3"))
    # narração de marketing FIXA das telas de CTA (inscrição + QR) — intro e outro
    download(s3, f"{CHANNEL_PREFIX}/_assets/introfixed.mp3", os.path.join(public, "audio", "introfixed.mp3"))
    download(s3, f"{CHANNEL_PREFIX}/_assets/finalfixed.mp3", os.path.join(public, "audio", "finalfixed.mp3"))

    # --- QR real ---
    redirect_url = f"{REDIRECT_BASE}?s=yt&v={nnnn}"
    generate_qr(os.path.join(sd, "qr.png"), redirect_url)

    # --- props.json (caminhos relativos ao public/, resolvidos por staticFile) ---
    rel = f"storage/sermons/{nnnn}"
    props = {
        "narrationUrl": f"{rel}/sermon.wav",
        "bgmUrl": f"audio/{bgm_name}",
        "bgmVolume": 0.05,
        "backgroundImageUrl": f"images/{bg_name}",
        "preacherImageUrl": f"images/{bust_name}",
        "transcriptSlug": f"{rel}/transcript.json",
        "subtitleStyle": "classic",
        "kenBurnsIntensity": "subtle",
        "qrCodeUrl": f"{rel}/qr.png",
        "ctaBookTitle": "The Best of Charles Spurgeon",
        "sermonTitle": sermon_title,
        "sermonNumber": nnnn,
        "marketingTitle": marketing.get("marketingTitle", sermon_title),
        # hook (dinâmico) + outro hook (dinâmico). CTAs fixos ficam SILENCIOSOS nesta v1
        # (SpurgeonCTA roda a animação por duração-fallback, sem narração) — simplifica e evita asset faltante.
        "hookAudioUrl": f"{rel}/hook.wav",
        "hookTranscriptSlug": f"{rel}/hook.json",
        "outroHookAudioUrl": f"{rel}/cta_narration.wav",
        "outroHookTranscriptSlug": f"{rel}/cta_narration.json",
        # narração de marketing FIXA das telas de CTA (inscrição + QR) — voz do canal
        "introCtaAudioUrl": "audio/introfixed.mp3",
        "outroCtaAudioUrl": "audio/finalfixed.mp3",
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
