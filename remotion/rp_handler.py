"""
rp_handler.py — RunPods Serverless handler de render (qualquer canal, via `canal` no job).

Fluxo por job:
  input: { "sermon": 1 }   (ou "sermonNumber")
  1. build_job.py baixa os assets do R2, seleciona bg/busto/trilha, gera o QR e escreve props.json
  2. Remotion renderiza Sermon-Full-Production (duração calculada por calculateMetadata — sem bug de 3h)
  3. Upload do mp4 pro R2 (bucket mananciall, <renders_prefix do canal>/NNNN.mp4)
  4. Retorna a URL pública

Credenciais R2 vêm por variável de ambiente (configuradas no endpoint do RunPods).
"""
import os
import subprocess
import boto3
import runpod

import canais
from botocore.config import Config

BUCKET = "mananciall"
APP = "/app"

R2_ENDPOINT = os.environ.get("R2_ENDPOINT")
R2_PUBLIC_URL = (os.environ.get("R2_PUBLIC_URL") or "").rstrip("/")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=os.environ.get("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def handler(job):
    inp = job.get("input", {}) or {}
    # `canal` no job, com o padrão do canais.py: job antigo sem o campo continua
    # caindo no Spurgeon, que é o que ele sempre fez.
    canal = inp.get("canal") or canais.PADRAO
    raw = inp.get("sermon", inp.get("sermonNumber", 1))
    frames = inp.get("frames")  # ex "0-150" p/ teste curto; ausente = vídeo completo
    concurrency = str(inp.get("concurrency", 4))  # paralelismo de frames; sobe p/ render full
    nnnn = f"{int(raw):04d}"
    props_path = os.path.join(APP, f"props_{nnnn}.json")
    suffix = "_test" if frames else ""
    out_path = f"/tmp/render_{canal}_{nnnn}{suffix}.mp4"

    # 1. Prepara o job (download R2 + QR + props)
    print(f"🧱 [handler] build_job para sermão {nnnn}...")
    subprocess.run(
        ["python3", "build_job.py", "--canal", canal, "--sermon", str(int(raw)),
         "--out", props_path, "--public-dir", os.path.join(APP, "public")],
        cwd=APP, check=True,
    )

    # 2. Render Remotion (concurrency conservador p/ CPU de serverless)
    print(f"🎬 [handler] renderizando Sermon-Full-Production{' (TESTE frames '+frames+')' if frames else ''}...")
    cmd = ["npx", "remotion", "render", "Sermon-Full-Production", out_path,
           f"--props={props_path}", "--log=verbose"]
    # concurrency só se explicitado no input; senão o Remotion detecta os cores do worker
    # (evita erro "concurrency > cores"). Ex de teste: {"concurrency": 2}
    if inp.get("concurrency"):
        cmd.append(f"--concurrency={concurrency}")
    if frames:
        cmd.append(f"--frames={frames}")
    # captura stdout+stderr do Remotion pra reportar a causa REAL em caso de falha
    proc = subprocess.run(cmd, cwd=APP, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stdout or "")[-1500:] + "\n---STDERR---\n" + (proc.stderr or "")[-2500:]
        raise RuntimeError(f"remotion render falhou (exit {proc.returncode}):\n{tail}")

    if not os.path.exists(out_path):
        raise FileNotFoundError(f"Render terminou mas {out_path} não existe.")

    # 3. Upload pro R2
    # ⚠️ era "renders/spurgeon/" fixo: o render serverless de QUALQUER canal
    # subia por cima do acervo do Spurgeon. Auditoria de 23/08.
    key = f"{canais.get(canal)['renders_prefix']}/{nnnn}{suffix}.mp4"
    print(f"📤 [handler] upload -> {key}")
    s3.upload_file(out_path, BUCKET, key, ExtraArgs={"ContentType": "video/mp4"})

    try:
        os.remove(out_path)
    except OSError:
        pass

    public_url = f"{R2_PUBLIC_URL}/{key}" if R2_PUBLIC_URL else key
    print(f"✅ [handler] pronto: {public_url}")
    return {"videoUrl": public_url, "key": key, "sermon": nnnn}


runpod.serverless.start({"handler": handler})
