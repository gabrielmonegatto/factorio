"""Monta a composição hyperframes da legenda animada (camada com alpha).

Centro do bloco de legenda na linha do SEGUNDO terço (y = 2H/3), em qualquer aspect.
Cards curtos (2-5 palavras), fonte Anton em caixa alta, branco com borda preta,
ênfase em ouro. Animação karaokê: o card entra inteiro e cada palavra dá um pop
ao ser falada.

Uso:
    python captions.py --video REFRAMED.mp4 --transcript T.json --out PROJDIR
    python captions.py ... --font Anton --color '#FFFFFF' --accent '#FFC72C'
"""
from __future__ import annotations
import argparse, html, json, re, shutil, subprocess, unicodedata
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Um card NUNCA termina numa destas (palavra funcional pendurada no fim da linha
# é o erro clássico de legenda — quebra a leitura no pior ponto possível).
GLUE = {
    "O","A","OS","AS","UM","UMA","DE","DO","DA","DOS","DAS","EM","NO","NA","NOS","NAS",
    "E","OU","QUE","POR","PRA","PARA","COM","SE","SEU","SUA","SEUS","SUAS","MEU","MINHA",
    "AO","À","AOS","ÀS","MAIS","MUITO","TÃO","JÁ","NEM","NÃO","É","AÍ","ESSE","ESSA",
    "ESTE","ESTA","AQUELE","AQUELA","QUANDO","ONDE","COMO","QUANTO","TODO","TODA","CADA",
    "SEM","SOB","SOBRE","ENTRE","ATÉ","DESDE","NUM","NUMA","PELO","PELA","VAI","TEM","FOI","ERA",
}
NUM = re.compile(r"\d")


def norm(w: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFC", w)
                   if c.isalnum() or c in "-$%").upper()


def load_words(path: Path) -> list[dict]:
    """Normaliza Scribe (ElevenLabs) ou hyperframes/Whisper -> [{t,s,e}].

    REGRA DURA: só tokens de FALA. O Scribe emite type="audio_event" para
    "(música de encerramento)", "(resmunga)" etc. — não é fala e nunca vira legenda.
    """
    d = json.loads(path.read_text())
    raw = d["words"] if isinstance(d, dict) and "words" in d else d
    out = []
    for w in raw:
        t = w.get("type", "word")
        if t != "word":                         # descarta spacing E audio_event
            continue
        txt = w.get("text", w.get("word", ""))
        if "(" in txt or ")" in txt:            # segunda barreira: tag entre parênteses
            continue
        if not norm(txt):
            continue
        out.append({"t": norm(txt), "raw": txt,
                    "s": float(w["start"]), "e": float(w["end"])})
    if not out:
        raise RuntimeError(f"{path.name}: nenhuma palavra falada — transcrição vazia?")
    return out


def group(words: list[dict], punch: set[str]) -> list[dict]:
    """Fala -> cards curtos. Quebra em pausa/pontuação; prefere fechar em vírgula."""
    segs, cur = [], []
    for i, w in enumerate(words):
        if cur:
            p = words[i - 1]
            if re.search(r"[.!?]$", p["raw"]) or (w["s"] - p["e"]) >= 0.32:
                segs.append(cur); cur = []
        cur.append(w)
    if cur:
        segs.append(cur)

    cards, since = [], 99
    for seg in segs:
        i = 0
        while i < len(seg):
            best = []
            for n in (2, 3, 4, 5):
                if i + n > len(seg):
                    continue
                ch = seg[i:i + n]; rest = len(seg) - (i + n)
                ends_punct = bool(re.search(r"[,;:.!?]$", ch[-1]["raw"]))
                if ch[-1]["e"] - ch[0]["s"] > 2.4:      # card longo demais pra ler
                    continue
                if n == 5 and not ends_punct:           # 5 palavras só pra fechar oração
                    continue
                sc = 0
                if ends_punct:                    sc += 100
                if ch[-1]["t"] in GLUE and rest:  sc -= 100
                if rest == 1:                     sc -= 40
                if rest == 0:                     sc += 20
                sc += {2: 0, 3: 8, 4: 5, 5: 2}[n]
                best.append((sc, n))
            n = max(best)[1] if best else min(4, len(seg) - i)
            ch = seg[i:i + n]; i += n
            ws = []
            for w in ch:
                em = since >= 2 and len(w["t"]) > 2 and (w["t"] in punch or bool(NUM.search(w["t"])))
                if em:
                    since = 0
                ws.append({**w, "em": em})
            since += 1
            cards.append({"in": ch[0]["s"], "out": ch[-1]["e"], "w": ws})
    return cards


def build(video: Path, cards: list[dict], out: Path, font: str,
          color: str, accent: str, family: str) -> None:
    # ffprobe pode emitir um separador sobrando ("1080x1080x") — pegue só os 2 primeiros
    dims = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(video)],
        capture_output=True, text=True, check=True).stdout.strip().split("x")
    w, h = int(dims[0]), int(dims[1])
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(video)], capture_output=True, text=True, check=True).stdout.strip())

    line2 = round(2 * h / 3)                    # centro da legenda: 2º terço
    fs = round(0.0815 * min(w, h))              # corpo relativo ao MENOR lado:
    stroke = max(4, round(fs * 0.114))          #   mesma presença em qualquer aspect
    pad = round(0.078 * w)

    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(ASSETS / font, out / font)
    (out / "hyperframes.json").write_text('{"paths":{"blocks":"compositions","assets":"assets"}}')

    # Card que começa depois do fim do vídeo nunca apareceria — sinal de que a
    # transcrição não é deste corte. Descarta e avisa, em vez de gerar lixo mudo.
    live = [c for c in cards if c["in"] < dur - 0.05]
    if len(live) < len(cards):
        print(f"    AVISO: {len(cards)-len(live)} card(s) além do fim do vídeo "
              f"({dur:.1f}s) — a transcrição é do clipe certo?")
    cards = live

    divs, tl = [], []
    for gi, c in enumerate(cards):
        nxt = cards[gi + 1]["in"] if gi + 1 < len(cards) else dur
        gin = max(0.0, c["in"] - 0.06)
        gout = min(c["out"] + 0.30, nxt - 0.02, dur)     # segura um tempo, sai antes do próximo
        if gout - gin < 0.30:
            gout = min(gin + 0.30, dur)
        spans = []
        for wi, wd in enumerate(c["w"]):
            spans.append(f'<span class="{"w em" if wd["em"] else "w"}" '
                         f'id="g{gi}w{wi}">{html.escape(wd["t"])}</span>')
            t = max(wd["s"], gin + 0.02)                  # o pop nunca precede o card
            pk = 1.14 if wd["em"] else 1.08
            tl.append(f'tl.to("#g{gi}w{wi}",{{scale:{pk},duration:.09,ease:"power2.out"}},{t:.3f});')
            tl.append(f'tl.to("#g{gi}w{wi}",{{scale:1,duration:.14,ease:"power2.inOut"}},{t+.09:.3f});')
        divs.append(f'<div class="cap" id="c{gi}" data-start="{gin:.3f}" '
                    f'data-duration="{gout-gin:.3f}" data-track-index="1">'
                    f'<div class="txt" id="g{gi}">{"".join(spans)}</div></div>')
        tl.append(f'tl.set("#c{gi}",{{autoAlpha:1}},{gin:.3f});')
        tl.append(f'tl.fromTo("#g{gi}",{{opacity:0,y:{round(h*0.01)},scale:.94}},'
                  f'{{opacity:1,y:0,scale:1,duration:.13,ease:"back.out(2)"}},{gin:.3f});')
        tl.append(f'tl.to("#c{gi}",{{autoAlpha:0,duration:.10}},{gout-0.10:.3f});')

    nl = chr(10)
    (out / "index.html").write_text(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width={w}, height={h}"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
 @font-face{{font-family:"{family}";src:url("./{font}") format("truetype");font-display:block;}}
 *{{margin:0;padding:0;box-sizing:border-box}}
 html,body{{width:{w}px;height:{h}px;overflow:hidden;background:transparent}}
 /* O clipe ocupa o FRAME INTEIRO: um clipe de altura 0 é recortado pelo engine e
    a legenda some. O padding-top empurra a caixa de conteúdo pra {line2}..{h}, então
    align-items:center crava o CENTRO do card na linha do 2º terço, com 1 ou 2 linhas. */
 .cap{{position:absolute;left:0;top:0;width:{w}px;height:{h}px;
   padding-top:{2*line2-h}px;display:flex;align-items:center;justify-content:center;
   visibility:hidden;}}
 /* .cap carrega SÓ autoAlpha; .txt carrega o transform. O GSAP sobrescreve a
    propriedade transform inteira — se o posicionamento dependesse dela, sumiria. */
 .txt{{width:100%;padding:0 {pad}px;text-align:center;
   font-family:"{family}",sans-serif;font-size:{fs}px;line-height:1.06;
   letter-spacing:.012em;text-transform:uppercase;}}
 .txt .w{{display:inline-block;margin:0 .12em;color:{color};
   -webkit-text-stroke:{stroke}px #000;paint-order:stroke fill;
   text-shadow:0 {round(stroke*0.7)}px 0 rgba(0,0,0,.30);will-change:transform,opacity;}}
 .txt .em{{color:{accent};}}
</style></head>
<body>
 <div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}"
      data-width="{w}" data-height="{h}">
{nl.join("  " + d for d in divs)}
 </div>
 <script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{paused:true}});
  gsap.set(".cap",{{autoAlpha:0}});
{nl.join("  " + t for t in tl)}
  window.__timelines["main"] = tl;
 </script>
</body></html>""")
    print(f"  {video.stem:38} {len(cards):3d} cards  {w}x{h}  fonte {fs}px  legenda y={line2}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--transcript", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--punch", type=Path, help="txt, uma palavra de ênfase por linha")
    ap.add_argument("--font", default="Anton-Regular.ttf")
    ap.add_argument("--family", default="Anton")
    ap.add_argument("--color", default="#FFFFFF")
    ap.add_argument("--accent", default="#FFC72C")
    a = ap.parse_args()
    punch = {norm(l) for l in a.punch.read_text().split()} if a.punch else set()
    cards = group(load_words(a.transcript), punch)
    build(a.video, cards, a.out, a.font, a.color, a.accent, a.family)
    (a.out / "cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
