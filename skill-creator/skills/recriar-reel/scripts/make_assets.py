"""reel2 static art: tall scrolling CTA doc + music bed."""
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
SR = 44100

# --- tall doc for the scrolling CTA (720 x 2300), blurred, lilac highlights
DW, DH = 720, 2300
LILAC = (168, 122, 255)
bg = Image.open(ROOT / "bg.png").convert("RGB")
tall = bg.resize((DW, DH), Image.LANCZOS)
doc = Image.new("RGB", (DW, DH), (0, 0, 0))
dd = ImageDraw.Draw(doc)
dd.rounded_rectangle([110, 60, 610, DH - 60], radius=42, fill=(246, 245, 249))
random.seed(11)
y = 110
while y < DH - 130:
    dd.rounded_rectangle([150, y, 150 + random.randint(90, 160), y + 20],
                         radius=6, fill=LILAC)
    y += 34
    for _ in range(random.randint(2, 3)):
        dd.rounded_rectangle([150, y, 150 + random.randint(280, 410), y + 12],
                             radius=5, fill=(168, 168, 178))
        y += 22
    dd.rounded_rectangle([150, y, 150 + random.randint(170, 250), y + 12],
                         radius=5, fill=(126, 132, 228))
    y += 26
    dd.rectangle([150, y, 570, y + 5], fill=(40, 36, 52))
    y += 22
mask = Image.new("L", (DW, DH), 0)
ImageDraw.Draw(mask).rounded_rectangle([110, 60, 610, DH - 60], radius=42,
                                       fill=255)
tall.paste(doc.filter(ImageFilter.GaussianBlur(11)), (0, 0),
           mask.filter(ImageFilter.GaussianBlur(7)))
tall.save(ROOT / "cta_tall.png")

# --- music bed: original audio 0-8.80, then music_c scaled, tail fade
def load(p):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2",
         "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def rms(a):
    return float(np.sqrt(np.mean(a ** 2)))


src = load(ROOT / "source_audio.mp3")
mc = load(ROOT / "music_c.mp3")
END = 41.42
N = int(END * SR)
bed = np.zeros((N, 2), dtype=np.float32)
s880 = int(8.80 * SR)
bed[:s880] = src[:s880]

need = N - s880
seg = mc[int(9.0 * SR):int(9.0 * SR) + need].copy()
target = max(rms(src[int(2.0 * SR):int(8.0 * SR)]) * 0.8, 0.065)
seg *= target / (rms(seg) + 1e-9)
xf = int(0.30 * SR)
w = np.linspace(0, np.pi / 2, xf, dtype=np.float32)[:, None]
bed[s880:s880 + xf] = (src[s880:s880 + xf] * np.cos(w) ** 2
                       + seg[:xf] * np.sin(w) ** 2)
bed[s880 + xf:] = seg[xf:]
fo = int(0.5 * SR)
bed[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
peak = float(np.abs(bed).max())
if peak > 0.99:
    bed *= 0.99 / peak
subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR),
     "-i", "-", str(ROOT / "bed_r2.wav")],
    input=bed.astype(np.float32).tobytes(), check=True)
print(f"assets r2 ok (bed target rms {target:.3f}, peak {peak:.2f})")
