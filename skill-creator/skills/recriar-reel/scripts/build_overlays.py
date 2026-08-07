"""Overlay layer for the reel2 recreation (v4 purple design system).

Sections: hook fullscreen -> title+card -> big card -> black lockup ->
big card -> split cards -> 2 black lockups -> card -> scrolling CTA.
"""
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / "overlay"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 720, 1280
FPS = 30
DUR = 41.3
N_FRAMES = int(DUR * FPS) + 1  # 1240 (render caps at 1239 via -t)

SUP = "/System/Library/Fonts/Supplemental"
F_BOLD = f"{SUP}/Arial Bold.ttf"
F_BOLD_IT = f"{SUP}/Arial Bold Italic.ttf"
F_ROUND = f"{SUP}/Arial Rounded Bold.ttf"

LILAC = (198, 160, 255, 255)
YELLOW = (240, 225, 74, 255)
PURPLE = (124, 58, 237, 255)
WHITE = (255, 255, 255, 255)
DARK = (20, 18, 26, 255)

BG = Image.open(ROOT / "bg.png").convert("RGB")
plan = json.loads((ROOT / "tts" / "plan.json").read_text())


def font(path, size):
    return ImageFont.truetype(path, size)


FDIR = str(ROOT / "fonts")
P_BI = f"{FDIR}/Poppins-BoldItalic.ttf"
P_REG = f"{FDIR}/Poppins-Regular.ttf"
P_XB = f"{FDIR}/Poppins-ExtraBold.ttf"
P_SB = f"{FDIR}/Poppins-SemiBold.ttf"
P_MED = f"{FDIR}/Poppins-Medium.ttf"
FONTS = {
    "kar": font(P_XB, 54),
    "lkbig": font(P_BI, 86),
    "lkhuge": font(P_BI, 92),
    "lksm": font(P_REG, 48),
    "title_big": font(P_BI, 76),
    "title_huge": font(P_BI, 94),
    "title_sm": font(P_REG, 50),
    "m75": font(P_SB, 33),
    "badge": font(P_SB, 27),
    "cta1": font(P_SB, 44),
    "cta2": font(P_MED, 29),
}
_probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))


def draw_text(d, xy, text, fnt, fill, anchor="mm", shadow=3, stroke=0):
    x, y = xy
    if shadow:
        d.text((x + shadow, y + shadow), text, font=fnt, fill=(0, 0, 0, 150),
               anchor=anchor, stroke_width=stroke,
               stroke_fill=(0, 0, 0, 150))
    d.text((x, y), text, font=fnt, fill=fill, anchor=anchor,
           stroke_width=stroke,
           stroke_fill=(34, 32, 40, 255) if stroke else None)


# ------------------------------------------------------------------- chrome
def card_shadow(layer, rect, radius):
    x0, y0, x1, y1 = rect
    pad = 46
    sh = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(sh).rounded_rectangle(
        [pad, pad, pad + x1 - x0, pad + y1 - y0], radius=radius, fill=115)
    sh = sh.filter(ImageFilter.GaussianBlur(13))
    dark = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    dark.putalpha(sh)
    layer.alpha_composite(dark, (x0 - pad, y0 - pad + 10))


def card_chrome(layer, rect, radius=28, border=6):
    x0, y0, x1, y1 = rect
    card_shadow(layer, rect, radius)
    mask = Image.new("L", (x1 - x0, y1 - y0), 255)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, x1 - x0 - 1, y1 - y0 - 1], radius=radius, fill=0)
    layer.paste(BG.crop(rect), (x0, y0), mask)
    ImageDraw.Draw(layer).rounded_rectangle(
        [x0, y0, x1 - 1, y1 - 1], radius=radius, outline=(255, 255, 255, 255),
        width=border)


def eye(d, cx, cy, color, s=1.0):
    d.ellipse([cx - 13 * s, cy - 8 * s, cx + 13 * s, cy + 8 * s],
              outline=color, width=max(2, int(3 * s)))
    d.ellipse([cx - 5 * s, cy - 5 * s, cx + 5 * s, cy + 5 * s], fill=color)


CHROME = {}
CHROME_WINDOWS = [
    (8.85, 13.2, "c2", [((205, 520, 515, 1071), 24, 5)]),
    (13.2, 15.467, "c3", [((54, 112, 666, 1062), 28, 6)]),
    (16.633, 22.5, "c5a", [((54, 112, 666, 1062), 28, 6)]),
    (22.5, 27.7, "c5b", [((40, 318, 328, 884), 20, 5),
                          ((368, 318, 656, 884), 20, 5)]),
    (30.233, 36.9, "c7", [((62, 272, 658, 1108), 28, 6)]),
]


def chrome_for(t):
    for (a, b, key, cards) in CHROME_WINDOWS:
        if a <= t < b:
            if key not in CHROME:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                for rect, r, bw in cards:
                    card_chrome(lay, rect, radius=r, border=bw)
                CHROME[key] = lay
            return CHROME[key], key
    return None, ""


def make_backdrop(w, h, alpha):
    pad = 30
    img = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(img).rounded_rectangle([pad, pad, pad + w, pad + h],
                                          radius=28, fill=alpha)
    mask = img.filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", mask.size, (10, 8, 16, 0))
    out.putalpha(mask)
    return out, pad


_bd, _bp = make_backdrop(560, 150, 250)
BACKDROPS = [(13.25, 15.44, 85 - _bp, 562 - _bp, _bd),
             (16.66, 22.45, 85 - _bp, 562 - _bp, _bd)]

# ------------------------------------------------------------------ captions
ACCENTS = {"final": LILAC, "comparación": LILAC, "revela": LILAC,
           "visual": YELLOW}

events = []  # (t0,t1,kind,payload)
segs = {s["idx"]: s for s in plan}


def words_of(i):
    return [(w["w"].rstrip(".,:;”“\""), w["t0"], w["t1"])
            for w in segs[i]["words"]]


# seg0: title lockup (first 4 words) + karaoke for the rest
w0 = words_of(0)


def line_positions(lines, fonts):
    """words laid left-to-right on shared baselines, tight cascade."""
    pos = {}
    for words, x, bl, fk, fill in lines:
        cx = x
        for wd in words:
            pos[wd] = (cx, bl, fk, fill)
            cx += _probe.textlength(wd + " ", font=fonts[fk])
    return pos


TITLE_LINES = [
    (["Esto"], 115, 320, "title_big", WHITE),
    (["fue", "un"], 215, 365, "title_sm", WHITE),
    (["intento"], 250, 434, "title_huge", WHITE),
]
TITLE_POS_W = line_positions(TITLE_LINES, FONTS)
for k in range(4):
    events.append((w0[k][1], 13.15, "title", k))
for (txt, t0, t1) in w0[4:]:
    if t0 < 9.95 or txt in ("de", "y"):
        continue
    nxt = [x[1] for x in w0 if x[1] > t0]
    events.append((t0, min(nxt[0] if nxt else t1 + 0.3, 13.15), "kar",
                   (txt, 360, 645, WHITE)))

# seg1: karaoke inside card until 15.42, then black lockup words
w1 = words_of(1)
LK4_POS = line_positions([
    (["la", "forma"], 100, 535, "lkbig", WHITE),
    (["de"], 185, 582, "lksm", WHITE),
    (["entregarlo"], 170, 650, "lkhuge", LILAC),
], FONTS)
for j, (txt, t0, t1) in enumerate(w1):
    if txt in LK4_POS and t0 >= 14.8:
        events.append((max(t0, 15.52), 16.58, "lk", ("lk4", txt)))
    elif t0 < 15.40:
        nxt = w1[j + 1][1] if j + 1 < len(w1) else t1 + 0.3
        events.append((t0, min(nxt, 15.40), "kar", (txt, 360, 660, WHITE)))

# seg2: karaoke inside card
w2 = words_of(2)
for j, (txt, t0, t1) in enumerate(w2):
    nxt = w2[j + 1][1] if j + 1 < len(w2) else t1 + 0.3
    events.append((t0, min(nxt, 22.45), "kar", (txt, 360, 660, WHITE)))

# seg3: karaoke above split cards (last word holds until section end)
w3 = words_of(3)
for j, (txt, t0, t1) in enumerate(w3):
    nxt = w3[j + 1][1] if j + 1 < len(w3) else 27.65
    events.append((max(t0, 22.52), min(nxt, 27.65), "kar",
                   (txt, 360, 235, ACCENTS.get(txt, WHITE))))

# seg4: two black lockups
_lk6a = line_positions([
    (["El"], 95, 490, "lksm", WHITE),
    (["algoritmo"], 135, 562, "lkbig", WHITE),
    (["no"], 480, 614, "lksm", WHITE),
], FONTS)
_lk6b = line_positions([
    (["impulsa"], 110, 512, "lkbig", LILAC),
    (["contenido"], 225, 556, "lksm", WHITE),
    (["al", "azar"], 290, 624, "lkbig", LILAC),
], FONTS)
LK6 = {}
for k, v in _lk6a.items():
    LK6[k] = (*v, 29.0)
for k, v in _lk6b.items():
    LK6[k] = (*v, 30.2)
for (txt, t0, t1) in words_of(4):
    key = txt if txt in LK6 else txt.capitalize() if txt.capitalize() in LK6 else None
    if key:
        events.append((t0, LK6[key][4], "lk", ("lk6", key)))

# seg5: karaoke above card 7
w5 = words_of(5)
for j, (txt, t0, t1) in enumerate(w5):
    nxt = w5[j + 1][1] if j + 1 < len(w5) else t1 + 0.3
    events.append((max(t0, 30.35), min(nxt, 36.85), "kar",
                   (txt, 360, 210, ACCENTS.get(txt, WHITE))))


def active(t):
    return [e for e in events if e[0] <= t < e[1]]


def frame_key(t):
    _, ck = chrome_for(t)
    key = [repr([(e[2], e[3]) for e in active(t)]), ck]
    key.append("bd" if any(a <= t < b for (a, b, *_r) in BACKDROPS) else "")
    key.append("75m" if 2.3 <= t < 8.72 else "")
    key.append("bdg" if 9.6 <= t < 13.15 else "")
    key.append("cta" if t >= 37.2 else "")
    return "|".join(key)


def render(t, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ch, _ = chrome_for(t)
    if ch is not None:
        img.alpha_composite(ch)
    for (a, b, bx, by, bim) in BACKDROPS:
        if a <= t < b:
            img.alpha_composite(bim, (bx, by))
    d = ImageDraw.Draw(img)
    if 2.3 <= t < 8.72:
        tw = _probe.textlength("2,9M de vistas", font=FONTS["m75"])
        w = tw + 88
        d.rounded_rectangle([28, 150, 28 + w, 216], radius=33,
                            fill=(250, 250, 252, 250))
        eye(d, 60, 183, DARK, 1.0)
        d.text((84, 183), "2,9M de vistas", font=FONTS["m75"], fill=DARK,
               anchor="lm")
    if 9.6 <= t < 13.15:
        tw = _probe.textlength("2,9M", font=FONTS["badge"])
        w = tw + 72
        d.rounded_rectangle([360 - w / 2, 1090, 360 + w / 2, 1138], radius=14,
                            fill=(250, 250, 252, 245))
        eye(d, 360 - w / 2 + 26, 1114, DARK, 0.9)
        d.text((360 - w / 2 + 46, 1114), "2,9M", font=FONTS["badge"],
               fill=DARK, anchor="lm")
    for (t0, t1, kind, payload) in active(t):
        if kind == "kar":
            txt, cx, cy, fill = payload
            draw_text(d, (cx, cy), txt, FONTS["kar"], fill, shadow=4,
                      stroke=3)
        elif kind == "title":
            k = payload
            txt = w0[k][0]
            x, y, fk, fill = TITLE_POS_W[txt]
            draw_text(d, (x, y), txt, FONTS[fk], fill, anchor="ls", shadow=3)
        elif kind == "lk":
            grp, key = payload
            if grp == "lk4":
                x, y, fk, fill = LK4_POS[key]
            else:
                x, y, fk, fill, _ = LK6[key]
            draw_text(d, (x, y), key, FONTS[fk], fill, anchor="ls", shadow=0)
    if t >= 37.2:
        d.rounded_rectangle([50, 554, 670, 648], radius=47, fill=PURPLE)
        d.text((360, 601), 'Comenta "Formatos"', font=FONTS["cta1"],
               fill=WHITE, anchor="mm")
        tw2 = _probe.textlength("Para +50 Formatos Virales", font=FONTS["cta2"])
        d.rounded_rectangle([360 - tw2 / 2 - 24, 662, 360 + tw2 / 2 + 24, 714],
                            radius=26, fill=(26, 16, 37, 245))
        d.text((360, 688), "Para +50 Formatos Virales", font=FONTS["cta2"],
               fill=WHITE, anchor="mm")
    img.save(path)


cache = {}
for f in range(N_FRAMES):
    t = f / FPS
    path = OUT / f"{f:05d}.png"
    k = frame_key(t)
    if k in cache:
        shutil.copyfile(cache[k], path)
    else:
        render(t, path)
        cache[k] = path
print(f"r2 overlays: {N_FRAMES} frames, {len(cache)} unique")
