"""Render broll idx 106 locally: neon-yellow isometric box icon on black,
green $ badge pops in the final second. 5s @30fps -> gen/b106.mp4."""
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
W, H, FPS, DUR = 720, 1280, 30, 5.0
N = int(DUR * FPS)
YEL = (240, 220, 40)
PINK = (243, 23, 161)
GREEN = (40, 200, 90)

CX, CY, S = 360, 640, 150  # box center / half-size


def box_pts(s):
    """isometric box: top diamond + two side faces."""
    top = [(CX, CY - s), (CX + s, CY - s * 0.5), (CX, CY), (CX - s, CY - s * 0.5)]
    left = [(CX - s, CY - s * 0.5), (CX, CY), (CX, CY + s), (CX - s, CY + s * 0.5)]
    right = [(CX + s, CY - s * 0.5), (CX, CY), (CX, CY + s), (CX + s, CY + s * 0.5)]
    return top, left, right


def frame(i):
    t = i / FPS
    bob = math.sin(t * 2.2) * 6
    img = Image.new("RGB", (W, H), (0, 0, 0))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dy = bob
    top, left, right = box_pts(S)
    for poly in (top, left, right):
        d.polygon([(x, y + dy) for x, y in poly], outline=YEL + (255,), width=10)
    # pink ribbon across top
    d.line([(CX - S, CY - S * 0.5 + dy), (CX + S, CY - S * 0.5 + dy)],
           fill=PINK + (255,), width=12)
    d.line([(CX, CY - S + dy), (CX, CY + dy)], fill=PINK + (255,), width=12)
    # speed lines
    for k, (x0, y0) in enumerate([(120, 420), (600, 420), (150, 900), (585, 905)]):
        ph = math.sin(t * 3 + k) * 8
        d.line([(x0 - 40, y0 + ph), (x0 + 40, y0 + ph)], fill=YEL + (160,), width=8)
    # $ badge pop in last second
    if t >= 4.0:
        p = min(1.0, (t - 4.0) / 0.35)
        ease = 1 - (1 - p) ** 3
        r = 52 * (1.25 - 0.25 * ease) * ease
        bx, by = CX + S * 0.78, CY - S * 0.85 + dy
        if r > 1:
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=GREEN + (255,),
                      outline=(255, 255, 255, 255), width=6)
            # dollar glyph drawn as strokes
            fr = r * 0.5
            d.line([(bx, by - fr), (bx, by + fr)], fill=(255, 255, 255, 255), width=7)
            d.arc([bx - fr, by - fr, bx + fr, by], 60, 300, fill=(255, 255, 255, 255), width=7)
            d.arc([bx - fr, by, bx + fr, by + fr], 240, 120, fill=(255, 255, 255, 255), width=7)
    glow = lay.filter(ImageFilter.GaussianBlur(12))
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0))
    out = Image.alpha_composite(Image.alpha_composite(
        Image.new("RGBA", (W, H), (0, 0, 0, 255)), glow), lay)
    return out.convert("RGB")


proc = subprocess.Popen(
    ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
     str(ROOT / "gen" / "b106.mp4")], stdin=subprocess.PIPE)
for i in range(N):
    proc.stdin.write(frame(i).tobytes())
proc.stdin.close()
proc.wait()
print("b106.mp4 ok")
