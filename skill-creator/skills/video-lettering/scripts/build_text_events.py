import json, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).parent
COLORS = {"branco":"white","azul":"cyan","ciano":"cyan","vermelho":"red","rosa":"pink","magenta":"pink","amarelo":"yellow","cinza":"white"}
def norm(w):
    w = unicodedata.normalize("NFD", w)
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]", "", w.upper())
scenes = json.load(open(ROOT/"storyboard_merged.json"))
tr = json.load(open(ROOT/"edit"/"transcripts"/"source.json"))
words = [(w["start"], w["end"], w["text"]) for w in tr["words"] if w.get("type")=="word"]
wnorm = [norm(t) for _,_,t in words]
def split_depth0(txt, sep="/"):
    parts, buf, depth = [], "", 0
    for c in txt:
        if c == "(": depth += 1
        elif c == ")": depth = max(0, depth-1)
        if c == sep and depth == 0:
            parts.append(buf); buf = ""
        else:
            buf += c
    parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def parse_state(txt):
    txt = split_depth0(txt, "—")[0]
    lines = []
    for seg in split_depth0(txt):
        line = []; pos = 0
        for m in re.finditer(r"\(([^)]*)\)", seg):
            chunk = seg[pos:m.start()].strip(" ,;:")
            ann = m.group(1).lower(); color = "white"
            for k,v in COLORS.items():
                if k in ann: color = v; break
            for w in chunk.split(): line.append({"w":w,"color":color})
            pos = m.end()
        for w in seg[pos:].strip(" ,;:").split(): line.append({"w":w,"color":"white"})
        if line: lines.append(line)
    return lines
def match_times(sw, t0, t1):
    lo = 0
    while lo < len(words) and words[lo][0] < t0-0.6: lo += 1
    hi = lo
    while hi < len(words) and words[hi][0] < t1+0.4: hi += 1
    j = lo; times = [None]*len(sw)
    for i,w in enumerate(sw):
        n = norm(w["w"])
        if not n: continue
        for k in range(j, min(hi, j+8)):
            if wnorm[k]==n or (len(n)>4 and n in wnorm[k]):
                times[i] = min(max(words[k][0], t0), t1-0.1); j = k+1; break
    known = [(i,t) for i,t in enumerate(times) if t is not None]
    if not known:
        for i in range(len(times)): times[i] = t0 + (t1-t0)*i/max(1,len(times))
    else:
        for i in range(len(times)):
            if times[i] is None:
                prev = max([t for k,t in known if k<i], default=t0)
                nxt = min([t for k,t in known if k>i], default=t1-0.15)
                times[i] = (prev+nxt)/2
    for i in range(1,len(times)): times[i] = max(times[i], times[i-1])
    return times
states = []
for s in scenes:
    txt = (s.get("texto_linhas") or "").strip()
    if not txt: continue
    t0, t1 = float(s["start_s"]), float(s["end_s"])
    over = s["kind"]=="broll"
    extras = (s.get("extras") or "").lower()
    arrow = "seta" in extras or "chevron" in extras
    parts = [p for p in re.split(r"\s*(?:→|\|\|)\s*", txt) if p.strip()]
    parts = [re.sub(r"^[^A-ZÀ-Ü(]*?:\s*", "", p) for p in parts]
    span = (t1-t0)/max(1,len(parts))
    for pi,p in enumerate(parts):
        st0 = t0+pi*span; st1 = t0+(pi+1)*span if pi+1<len(parts) else t1
        lines = parse_state(p)
        flat = [w for ln in lines for w in ln]
        if not flat: continue
        times = match_times(flat, st0, st1)
        k = 0
        for ln in lines:
            for w in ln:
                w["t_show"] = round(times[k],3); k += 1
        punch = (len(flat)==1 and len(flat[0]["w"])<=10) or "gigante" in txt.lower()
        states.append({"t0":round(st0,3),"t1":round(st1,3),"over_video":over,"punch":punch,"arrow":arrow,"lines":lines})
json.dump(states, open(ROOT/"text_events.json","w"), ensure_ascii=False, indent=1)
print(len(states), "estados")
