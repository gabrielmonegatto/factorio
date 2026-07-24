"""Baixa os videos campeoes (os que tiveram veiculacao), sobe o .mp4 para o
R2 e gera a miniatura (frame de capa) no Teable.

So os campeoes: o arquivo de video e pesado e a maioria nunca sera reusada.
Resumivel: pula o que ja esta no R2.

  python pull_video_champions.py --dry-run
  python pull_video_champions.py [--limit N]
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

from _common import D1, env, log

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "teable"))
from _teable import TABLE_CRIATIVOS, Teable  # noqa: E402

SP = pathlib.Path(
    r"C:\Users\MONEGA~1\AppData\Local\Temp\claude"
    r"\C--Users-Monegatto-Desktop-EternalL"
    r"\19f9fca5-fe81-4845-952f-054352f943b7\scratchpad"
)
RCLONE_CONF = SP / "rclone.conf"        # remote r2br -> bucket br4nds-creatives
BUCKET = "br4nds-creatives"
WORK = pathlib.Path(tempfile.gettempdir()) / "video_champions"
THUMB_MAX = 500


def r2_has(r2_key: str) -> bool:
    r = subprocess.run(
        ["rclone", "--config", str(RCLONE_CONF), "lsf", f"r2br:{BUCKET}/{r2_key}"],
        capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def drive_download(drive_id: str, dest_dir: pathlib.Path) -> pathlib.Path | None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["rclone", "backend", "copyid", "meudrive:", drive_id, str(dest_dir) + "/"],
        capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  download falhou ({drive_id}): {r.stderr[:120]}")
        return None
    vids = list(dest_dir.glob("*.mp4")) + list(dest_dir.glob("*.MP4"))
    return vids[0] if vids else None


def make_thumb(video: pathlib.Path, out: pathlib.Path) -> pathlib.Path | None:
    """Frame de capa (1s, ou o inicio se o video for curto) -> webp 500px."""
    raw = out.with_suffix(".png")
    for ss in ("00:00:01", "00:00:00"):
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", ss, "-i", str(video), "-frames:v", "1",
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


def r2_upload(local: pathlib.Path, r2_key: str) -> bool:
    r = subprocess.run(
        ["rclone", "--config", str(RCLONE_CONF), "copyto", str(local),
         f"r2br:{BUCKET}/{r2_key}", "--s3-upload-concurrency", "4"],
        capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  upload R2 falhou: {r.stderr[:120]}")
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    db = D1()
    champs = db.query("""
        SELECT DISTINCT c.id, c.drive_id, c.r2_key, c.drive_path
          FROM creatives c JOIN meta_ads ma ON ma.r2_key = c.r2_key
         WHERE c.type='video' AND c.drive_id IS NOT NULL
      ORDER BY c.id
    """)
    if args.limit:
        champs = champs[:args.limit]
    log(f"{len(champs)} campeoes a processar")
    if args.dry_run:
        for c in champs[:8]:
            log(f"  {c['id']} -> {c['r2_key']} | {c['drive_path'].rsplit('/',1)[-1][:44]}")
        return

    tb = Teable()
    tmap = {r["fields"]["ID"]: r for r in tb.all_records(TABLE_CRIATIVOS)
            if r["fields"].get("ID")}
    fid = next(f["id"] for f in tb.fields(TABLE_CRIATIVOS) if f["name"] == "Mídia")
    WORK.mkdir(parents=True, exist_ok=True)

    up = thumb = skip = fail = 0
    for i, c in enumerate(champs, 1):
        cid = c["id"]
        if r2_has(c["r2_key"]):
            skip += 1
        else:
            d = WORK / cid
            local = drive_download(c["drive_id"], d)
            if not local:
                fail += 1
                continue
            if not r2_upload(local, c["r2_key"]):
                fail += 1
                continue
            up += 1
            # miniatura de frame -> Teable (se ainda nao tiver)
            rec = tmap.get(cid)
            if rec and not rec["fields"].get("Mídia"):
                t = make_thumb(local, d / f"{cid}.webp")
                if t:
                    try:
                        tb.upload_attachment(TABLE_CRIATIVOS, rec["id"], fid, t)
                        thumb += 1
                    except Exception as e:
                        log(f"  thumb {cid} falhou: {str(e)[:80]}")
            for f in d.glob("*"):
                f.unlink(missing_ok=True)
            d.rmdir()
        if i % 10 == 0:
            log(f"  {i}/{len(champs)} (subiu {up}, thumb {thumb}, pulou {skip}, falhou {fail})")

    log(f"pronto: {up} no R2, {thumb} miniaturas, {skip} ja existiam, {fail} falharam")


if __name__ == "__main__":
    main()
