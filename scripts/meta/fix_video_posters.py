"""Gera o poster (frame de capa) dos videos campeoes que estao sem miniatura
no Teable e sobe. Fonte do frame: o proprio .mp4 ja no R2 (streaming, nao
baixa o arquivo inteiro).

Serve para reparar os campeoes que ficaram sem thumb (ex.: recorte de snapshot
de banco numa migracao).

  python fix_video_posters.py [--limit N]
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

from _common import D1, log

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "teable"))
from _teable import TABLE_CRIATIVOS, Teable  # noqa: E402

SP = pathlib.Path(
    r"C:\Users\MONEGA~1\AppData\Local\Temp\claude"
    r"\C--Users-Monegatto-Desktop-EternalL"
    r"\19f9fca5-fe81-4845-952f-054352f943b7\scratchpad")
RCLONE_CONF = SP / "rclone.conf"
BUCKET = "br4nds-creatives"
WORK = pathlib.Path(tempfile.gettempdir()) / "video_posters"
THUMB_MAX = 500


def r2_url(r2_key: str) -> str | None:
    """URL assinada temporaria do objeto no R2, para o ffmpeg ler via http."""
    r = subprocess.run(
        ["rclone", "--config", str(RCLONE_CONF), "link", f"r2br:{BUCKET}/{r2_key}"],
        capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def poster_from(src: str, out: pathlib.Path) -> pathlib.Path | None:
    raw = out.with_suffix(".png")
    for ss in ("00:00:01", "00:00:00"):
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", ss, "-i", src, "-frames:v", "1",
             "-vf", f"scale='min({THUMB_MAX},iw)':-2", str(raw)],
            capture_output=True, text=True)
        if r.returncode == 0 and raw.exists() and raw.stat().st_size:
            break
    if not raw.exists() or not raw.stat().st_size:
        return None
    with Image.open(raw) as im:
        im.load()
        im.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
        im.convert("RGB").save(out, "WEBP", quality=80, method=4)
    raw.unlink(missing_ok=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    db = D1()
    champs = {r["id"]: r["r2_key"] for r in db.query(
        "SELECT DISTINCT c.id, c.r2_key FROM creatives c "
        "JOIN meta_ads ma ON ma.r2_key = c.r2_key WHERE c.type='video'")}

    tb = Teable()
    tmap = {r["fields"]["ID"]: r for r in tb.all_records(TABLE_CRIATIVOS)
            if r["fields"].get("ID")}
    fid = next(f["id"] for f in tb.fields(TABLE_CRIATIVOS) if f["name"] == "Mídia")

    todo = [(cid, key) for cid, key in champs.items()
            if cid in tmap and not tmap[cid]["fields"].get("Mídia")]
    if args.limit:
        todo = todo[:args.limit]
    log(f"{len(todo)} campeoes sem poster")

    WORK.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for i, (cid, key) in enumerate(todo, 1):
        url = r2_url(key)
        if not url:
            log(f"  {cid}: sem url R2"); fail += 1; continue
        t = poster_from(url, WORK / f"{cid}.webp")
        if not t:
            log(f"  {cid}: ffmpeg falhou"); fail += 1; continue
        try:
            tb.upload_attachment(TABLE_CRIATIVOS, tmap[cid]["id"], fid, t)
            ok += 1
        except Exception as e:
            log(f"  {cid}: upload falhou {str(e)[:70]}"); fail += 1
        t.unlink(missing_ok=True)
        if i % 10 == 0:
            log(f"  {i}/{len(todo)} (ok {ok}, falhou {fail})")
    log(f"pronto: {ok} posters gerados, {fail} falharam")


if __name__ == "__main__":
    main()
