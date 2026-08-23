#!/usr/bin/env python3
"""
pod_wan_i2v.py — roda DENTRO do pod do RunPod. Anima stills em micro-clipes.

Não tem credencial nenhuma aqui de propósito: a máquina é alugada de terceiro,
então os arquivos sobem e descem por scp. Nada de R2 key em GPU de aluguel.

Modelo: Wan2.2-TI2V-5B-Diffusers (o pequeno). Escolhido pro primeiro teste
porque baixa ~10GB em vez de ~30 e não arrisca OOM em 24GB — na primeira
rodada o caro não é throughput, é tempo perdido depurando memória.

Uso (no pod):
  python pod_wan_i2v.py --entrada /work/stills --saida /work/out \
      --frames 61 --steps 25 --lado 704
"""
import argparse
import json
import os
import time

import torch
from diffusers import WanImageToVideoPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video
from PIL import Image

# 🧨 O 5B é modelo de DEMO pra hardware fraco. Nenhum criador sério entrega com
# ele (doc 22 §10a). O 14B é o salto de qualidade documentado. Ele é MoE (dois
# experts de ~28GB em bf16), então NÃO cabe num 4090 de 24GB: pede A100 80GB.
REPO_5B  = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
REPO_14B = "Wan-AI/Wan2.2-I2V-A14B-Diffusers"
REPO = REPO_14B

# Movimento por família. O still já decidiu enquadramento, luz e cor;
# aqui só se descreve O QUE SE MEXE. Movimento lento é regra do canal:
# o visual não pode competir com a palavra falada.
MOVIMENTO = {
    "capela": "the shaft of light holds steady while dust motes drift slowly through it, almost imperceptible camera push in",
    "mar":    "the swell rises and falls in slow heavy motion, foam sliding across the surface, static camera",
    "fogo":   "the flame flickers gently and smoke curls slowly upward, embers pulse, static camera",
    "natureza": "mist drifts slowly across the frame, grass and branches sway faintly in a light wind, static camera",
    "objetos": "the light source flickers softly across the surface, faint shadows shifting, very slow camera push in",
    "arquitetura": "warm light flickers gently beyond the opening, dust drifting in the air, extremely slow camera push in",
    "abstrato": "slow continuous drifting motion, particles and haze moving gently, static camera",
}
PADRAO = "very slow subtle motion, static camera, cinematic"

NEGATIVO = ("bright colors, overexposed, static, blurred details, subtitles, text, watermark, "
            "people, faces, hands, figures, walking, fast motion, camera shake, jump cut, "
            "cartoon, low quality, jpeg artifacts, deformed")


def familia_de(nome):
    return nome.split("_")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--frames", type=int, default=61)   # 61 @ 24fps ~= 2.5s
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--lado", type=int, default=704)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--guidance", type=float, default=5.0)
    ap.add_argument("--loop", action="store_true",
                    help="primeiro frame = ultimo frame: o clipe fecha sem emenda")
    ap.add_argument("--modelo", choices=["5b", "14b"], default="14b")
    ap.add_argument("--variantes", help="JSON [{nome,prompt,negativo?}]: gera uma "
                    "saída por variante A PARTIR DO PRIMEIRO still. Banco de prova "
                    "de prompt pagando UM setup de pod em vez de um por tentativa.")
    ap.add_argument("--largura", type=int, help="se omitido, usa --lado (quadrado)")
    ap.add_argument("--altura", type=int)
    args = ap.parse_args()

    global REPO
    REPO = REPO_14B if args.modelo == "14b" else REPO_5B
    larg = args.largura or args.lado
    alt = args.altura or args.lado
    os.makedirs(args.saida, exist_ok=True)
    stills = sorted(f for f in os.listdir(args.entrada) if f.lower().endswith((".png", ".jpg")))
    if not stills:
        raise SystemExit(f"nenhum still em {args.entrada}")
    print(f"[wan] {REPO}", flush=True)
    print(f"[wan] {len(stills)} stills, {args.frames}f @ {args.steps} steps, {larg}x{alt}", flush=True)

    # 🧨 MINA (22/08): o card do modelo mostra `WanPipeline(image=...)`, mas o
    # WanPipeline é TEXTO-para-vídeo e recusa `image`. O caminho i2v do Wan 2.2
    # é o WanImageToVideoPipeline SEM image_encoder (ele é _optional_component,
    # e o repo 5B não traz essa subpasta — o modo é `expand_timesteps: true`).
    # `torch_dtype` virou `dtype` no diffusers novo. Detecta em vez de chutar:
    # chutar errado carrega tudo em fp32 e estoura os 24GB.
    import inspect
    campo = ("dtype" if "dtype" in
             inspect.signature(WanImageToVideoPipeline.from_pretrained).parameters
             else "torch_dtype")
    print(f"[wan] dtype kwarg = {campo}", flush=True)

    t0 = time.time()
    vae = AutoencoderKLWan.from_pretrained(REPO, subfolder="vae", **{campo: torch.float32})
    pipe = WanImageToVideoPipeline.from_pretrained(REPO, vae=vae, **{campo: torch.bfloat16})

    # 🧨 MINA (22/08): 5B em bf16 com 61 frames a 704px ESTOURA os 24GB do 4090
    # no decode do VAE (22,9GB alocados, morre pedindo 230MB). Os três consertos:
    #   1. cpu_offload: só o componente em uso fica na GPU. NÃO combinar com
    #      .to("cuda") — o offload já cuida do device, e chamar os dois quebra.
    #   2. tiling no VAE: decodifica o quadro em pedaços (é aqui que estoura).
    #   3. slicing: uma imagem por vez no decode.
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    pipe.vae.enable_slicing()
    print(f"[wan] modelo carregado em {time.time()-t0:.0f}s", flush=True)

    # modo banco de prova: um still, N prompts
    variantes = None
    if args.variantes:
        with open(args.variantes, encoding="utf-8") as fh:
            variantes = json.load(fh)
        stills = [stills[0]] * len(variantes)
        print(f"[wan] banco de prova: {len(variantes)} variantes sobre {stills[0]}", flush=True)

    medidas = []
    for i, nome in enumerate(stills, 1):
        base = os.path.splitext(nome)[0]
        fam = familia_de(base)
        var = variantes[i - 1] if variantes else None
        if var:
            base = var["nome"]
        # recorta pro aspecto alvo ANTES de redimensionar: esticar deforma
        im = Image.open(os.path.join(args.entrada, nome)).convert("RGB")
        alvo = larg / alt
        w, h = im.size
        if w / h > alvo:
            nw = int(h * alvo); im = im.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
        else:
            nh = int(w / alvo); im = im.crop((0, (h - nh) // 2, w, (h + nh) // 2))
        img = im.resize((larg, alt), Image.LANCZOS)
        prompt = var["prompt"] if var else MOVIMENTO.get(fam, PADRAO)
        negativo = (var.get("negativo") if var else None) or NEGATIVO

        t = time.time()
        extra = {"last_image": img} if args.loop else {}
        frames = pipe(
            prompt=prompt,
            negative_prompt=negativo,
            image=img,
            height=alt,
            width=larg,
            num_frames=args.frames,
            guidance_scale=args.guidance,
            num_inference_steps=args.steps,
            **extra,
        ).frames[0]
        dur = time.time() - t

        destino = os.path.join(args.saida, f"{base}.mp4")
        export_to_video(frames, destino, fps=args.fps)
        medidas.append({"still": base, "familia": fam, "segundos": round(dur, 1)})
        print(f"[wan] {i}/{len(stills)} {base:22} {dur:6.1f}s -> {destino}", flush=True)

    total = time.time() - t0
    resumo = {
        "modelo": REPO, "frames": args.frames, "steps": args.steps, "res": f"{larg}x{alt}",
        "n": len(stills), "total_s": round(total, 1),
        "media_s_por_clipe": round(sum(m["segundos"] for m in medidas) / len(medidas), 1),
        "clipes": medidas,
    }
    with open(os.path.join(args.saida, "medicao.json"), "w") as f:
        json.dump(resumo, f, indent=2)
    print(f"[wan] MEDIÇÃO {json.dumps(resumo)}", flush=True)


if __name__ == "__main__":
    main()
