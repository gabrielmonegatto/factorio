import json, math, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ROOT = Path(__file__).parent
OUT = ROOT/"type"; OUT.mkdir(exist_ok=True)
W,H,FPS = 720,1280,30
DUR = 275.033
N = int(DUR*FPS)+1
ANTON = str(ROOT/"fonts"/"Anton-Regular.ttf")
PAL = {"white":(255,255,255),"cyan":(20,190,240),"red":(240,18,16),"pink":(243,23,161),"yellow":(250,210,80)}
RAMP = 0.18
states = json.load(open(ROOT/"text_events.json"))
_probe = ImageDraw.Draw(Image.new("RGBA",(8,8)))
_fonts = {}
def font(size):
    if size not in _fonts: _fonts[size] = ImageFont.truetype(ANTON, size)
    return _fonts[size]
def fit_size(text, base, max_w=620):
    size = base
    while size > 30 and _probe.textlength(text, font=font(size)) > max_w: size -= 4
    return size
def layout(state):
    lines = state["lines"]
    base = 150 if state["punch"] else 76
    sizes = [fit_size(" ".join(w["w"] for w in ln), base) for ln in lines]
    gap = 18
    heights = [int(s*1.12) for s in sizes]
    total = sum(heights)+gap*(len(lines)-1)
    y = (H-total)//2 - 30
    pos = []
    for ln,s,h in zip(lines,sizes,heights):
        txt = " ".join(w["w"] for w in ln)
        lw = _probe.textlength(txt, font=font(s))
        cx = (W-lw)/2; xs=[]
        for w in ln:
            xs.append(cx); cx += _probe.textlength(w["w"]+" ", font=font(s))
        pos.append({"y":y+h//2,"size":s,"xs":xs}); y += h+gap
    return pos
for st in states: st["_layout"] = layout(st)
def chevron(d, cy, alpha):
    for dy in (0,34):
        d.line([(322,cy+dy),(360,cy+dy+26),(398,cy+dy)], fill=(255,255,255,int(255*alpha)), width=10, joint="curve")
def active(t): return [s for s in states if s["t0"] <= t < s["t1"]]
def frame_key(t):
    key=[]
    for s in active(t):
        for ln in s["lines"]:
            for w in ln:
                dt = t-w["t_show"]
                a = -1 if dt<0 else (100 if dt>=RAMP else int(dt/RAMP*20))
                key.append(f"{w['w']}{w['color']}{a}")
        if s["arrow"]: key.append(f"ar{int((math.sin(t*math.pi*2)+1)*8)}")
        key.append(f"s{s['t0']}")
    return "|".join(key) or "empty"
def render(t, path):
    img = Image.new("RGBA",(W,H),(0,0,0,0))
    glow = Image.new("RGBA",(W,H),(0,0,0,0))
    d = ImageDraw.Draw(img); dg = ImageDraw.Draw(glow); has_glow=False
    for s in active(t):
        for ln,lay in zip(s["lines"],s["_layout"]):
            f = font(lay["size"])
            for w,x in zip(ln,lay["xs"]):
                dt = t-w["t_show"]
                if dt < 0: continue
                p = min(1.0, dt/RAMP)
                base = PAL[w["color"]]
                col = tuple(int(c*(0.30+0.70*p)) for c in base)
                if s["over_video"]:
                    d.text((x+3,lay["y"]+3), w["w"], font=f, fill=(0,0,0,200), anchor="lm")
                d.text((x,lay["y"]), w["w"], font=f, fill=col+(255,), anchor="lm")
                if w["color"]!="white" and p>0.3:
                    dg.text((x,lay["y"]), w["w"], font=f, fill=base+(110,), anchor="lm"); has_glow=True
        if s["arrow"]:
            chevron(d, 1120, 0.55+0.45*math.sin(t*math.pi*2))
    if has_glow:
        glow = glow.filter(ImageFilter.GaussianBlur(7))
        img = Image.alpha_composite(glow, img)
    img.save(path)
cache={}
for fidx in range(N):
    t = fidx/FPS
    path = OUT/f"{fidx:05d}.png"
    k = frame_key(t)
    if k in cache: shutil.copyfile(cache[k], path)
    else:
        render(t, path); cache[k]=path
print(f"type: {N} frames, {len(cache)} unique")
