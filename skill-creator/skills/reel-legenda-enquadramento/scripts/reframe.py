"""Reenquadra talking-heads pondo o OLHO na linha do primeiro terço (y = H/3).

Detecta o rosto com YuNet (landmarks dos olhos), tira a MEDIANA de N frames —
nunca um frame só, porque a pessoa se mexe e um frame isolado erra o alvo — e
recorta pro aspect pedido. Se o corte sozinho não alcança a linha (pessoa filmada
muito baixa/alta no quadro), aplica o menor zoom que torna o alvo alcançável.

Uso:
    python reframe.py VIDEO... --aspect 3:4 --out DIR
    python reframe.py VIDEO... --aspect 9:16 --out DIR --samples 20

Escreve DIR/<nome>.mp4 e DIR/reframe.json (a geometria usada, pra auditoria).
"""
from __future__ import annotations
import argparse, json, statistics as st, subprocess, sys
from pathlib import Path

import cv2

ASPECTS = {                      # rótulo -> (W, H). Todos com o lado menor em 1080.
    "9:16": (1080, 1920),
    "3:4":  (1080, 1440),
    "4:5":  (1080, 1350),
    "1:1":  (1080, 1080),
    "16:9": (1920, 1080),
}
MODEL = Path(__file__).resolve().parent.parent / "assets" / "yunet.onnx"


def probe(video: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(video)],
        capture_output=True, text=True, check=True).stdout.strip().split("x")
    return int(out[0]), int(out[1])


def eye_y(video: Path, sw: int, sh: int, samples: int) -> float:
    """Mediana do Y dos olhos ao longo do vídeo. Levanta se nunca achar rosto."""
    det = cv2.FaceDetectorYN_create(str(MODEL), "", (sw, sh), 0.7, 0.3, 5000)
    cap = cv2.VideoCapture(str(video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ys = []
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * (i + 0.5) / samples))
        ok, fr = cap.read()
        if not ok:
            continue
        _, faces = det.detect(fr)
        if faces is None or len(faces) == 0:
            continue
        f = max(faces, key=lambda f: f[2] * f[3])       # o rosto maior = o sujeito
        ys.append(float((f[5] + f[7]) / 2.0))           # landmarks: olho dir + olho esq
    cap.release()
    if not ys:
        raise RuntimeError(f"nenhum rosto detectado em {video.name} — não dá pra "
                           f"ancorar o olho; reenquadre à mão ou revise o clipe")
    if len(ys) < max(3, samples // 4):
        print(f"    AVISO: rosto em só {len(ys)}/{samples} amostras — enquadramento incerto",
              file=sys.stderr)
    return st.median(ys)


def plan(sw: int, sh: int, eye: float, tw: int, th: int) -> dict:
    """Menor zoom (>=1) que permite o olho cair em th/3, e o crop resultante.

    O crop tem o aspect do alvo. Sem zoom, a caixa é a maior que cabe na fonte.
    Se o olho está fundo demais no quadro, a caixa não desce o bastante — aí
    encolhe-se a caixa (= zoom in) até o alvo virar alcançável.
    """
    target = th / 3.0                                    # linha do primeiro terço
    a = tw / th
    z = 1.0
    for _ in range(64):                                  # converge em poucos passos
        # maior caixa de aspect `a` dentro da fonte, encolhida por z
        if sw / sh > a:
            ch = sh / z
            cw = ch * a
        else:
            cw = sw / z
            ch = cw / a
        if cw > sw or ch > sh:                           # zoom < 1 estouraria a fonte
            z *= 1.02
            continue
        scale = th / ch                                  # caixa -> tamanho final
        top = eye - target / scale                       # topo do crop, em px da fonte
        if 0 <= top <= sh - ch + 1e-6:
            top = min(max(top, 0.0), sh - ch)
            return {"zoom": round(z, 4), "crop": [round((sw - cw) / 2), round(top),
                                                  round(cw), round(ch)],
                    "eye_src": round(eye, 1),
                    "eye_final": round((eye - top) * scale, 1), "target": round(target, 1)}
        z *= 1.01                                        # inalcançável: aperta o quadro
    raise RuntimeError("não convergiu: olho fora de alcance mesmo com zoom")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+", type=Path)
    ap.add_argument("--aspect", required=True, choices=sorted(ASPECTS))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--samples", type=int, default=20)
    a = ap.parse_args()

    tw, th = ASPECTS[a.aspect]
    a.out.mkdir(parents=True, exist_ok=True)
    report = {}
    for v in a.videos:
        sw, sh = probe(v)
        p = plan(sw, sh, eye_y(v, sw, sh, a.samples), tw, th)
        x, y, cw, ch = p["crop"]
        vf = f"crop={cw}:{ch}:{x}:{y},scale={tw}:{th}:flags=lanczos"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-vf", vf,
                        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-c:a", "copy",
                        str(a.out / f"{v.stem}.mp4")], check=True)
        report[v.stem] = p | {"src": [sw, sh], "target": [tw, th]}
        z = f" zoom={p['zoom']}" if p["zoom"] > 1.001 else ""
        print(f"  {v.stem:38} olho {p['eye_src']:6.1f} -> y={p['eye_final']:6.1f} "
              f"(alvo {th/3:.0f}){z}")
    (a.out / "reframe.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
