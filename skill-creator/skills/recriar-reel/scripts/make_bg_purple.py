"""V4 static art: banding-free purple gradient with grain, CTA doc mock."""
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent / "v4"
ROOT.mkdir(exist_ok=True)
W, H = 720, 1280

# --- background: vertical dark->violet + radial lavender glow bottom-center,
#     floor never pure black, mono grain to kill banding
top = np.array([10, 5, 18], dtype=np.float64)       # #0A0512
mid = np.array([84, 38, 178], dtype=np.float64)     # deep violet
glow = np.array([201, 168, 248], dtype=np.float64)  # #C9A8F8

yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
t = yy / H
# vertical ramp with smoothstep between top and mid
v = np.clip((t - 0.18) / 0.62, 0, 1)
v = v * v * (3 - 2 * v)
base = top[None, None, :] * (1 - v[..., None]) + mid[None, None, :] * v[..., None]
# radial glow from bottom center
d = np.sqrt(((xx - 360) / 620) ** 2 + ((yy - 1400) / 700) ** 2)
g = np.clip(1 - d, 0, 1) ** 2.2
img = base + (glow - mid)[None, None, :] * g[..., None]
# gentle top-corner vignette
dv = np.sqrt(((xx - 360) / 900) ** 2 + ((yy - 500) / 1200) ** 2)
img *= (1 - 0.35 * np.clip(dv - 0.35, 0, 1))[..., None]
# mono grain ~2%
rng = np.random.default_rng(7)
img += rng.normal(0, 2.6, (H, W, 1))
bg = Image.fromarray(np.clip(img, 8, 255).astype(np.uint8))
bg.save(ROOT / "bg.png")

# --- CTA doc mock on the new bg, stronger blur, lilac highlights
LILAC = (168, 122, 255)
cta = bg.copy()
doc = Image.new("RGB", (W, H), (0, 0, 0))
dd = ImageDraw.Draw(doc)
dd.rounded_rectangle([120, 80, 600, 1200], radius=40, fill=(246, 245, 249))
random.seed(7)
y = 130
while y < 1150:
    dd.rounded_rectangle([160, y, 160 + random.randint(90, 150), y + 20],
                         radius=6, fill=LILAC)
    y += 34
    for _ in range(random.randint(2, 3)):
        dd.rounded_rectangle([160, y, 160 + random.randint(280, 400), y + 12],
                             radius=5, fill=(170, 170, 180))
        y += 22
    dd.rounded_rectangle([160, y, 160 + random.randint(180, 260), y + 12],
                         radius=5, fill=(126, 132, 228))
    y += 40
doc_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(doc_mask).rounded_rectangle([120, 80, 600, 1200], radius=40,
                                           fill=255)
cta.paste(doc.filter(ImageFilter.GaussianBlur(12)), (0, 0),
          doc_mask.filter(ImageFilter.GaussianBlur(7)))
cta.save(ROOT / "cta_bg.png")
print("v4 assets ok")
