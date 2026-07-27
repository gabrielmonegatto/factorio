"""Recupera a mídia dos criativos de concorrente (players_criativos) cujo
arquivo se perdeu, re-baixando do CDN da Foreplay a partir do cache local.

Custo: ZERO crédito Foreplay -- le so o cache (scratch/foreplay_media_cache.json)
e baixa do CDN publico (r2.foreplay.co). Nao chama a API paga.

  python recover_players_media.py --dry-run
  python recover_players_media.py [--limit N]
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _teable import TABLE_PLAYERS, Teable  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "meta"))
from _common import log  # noqa: E402

CACHE = pathlib.Path(__file__).resolve().parents[1].parent / "scratch" / "foreplay_media_cache.json"
DISK_LIST = pathlib.Path(
    r"C:\Users\MONEGA~1\AppData\Local\Temp\claude"
    r"\C--Users-Monegatto-Desktop-EternalL"
    r"\7318f669-4d31-46de-8f25-97fce4e56a49\scratchpad\files_on_disk.txt")
WORK = pathlib.Path(tempfile.gettempdir()) / "players_recover"


def media_url(entry: dict) -> str | None:
    """Melhor URL de mídia do cache: imagem cheia, senao video, senao thumb."""
    return entry.get("image") or entry.get("video") or entry.get("thumbnail")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    cache = json.load(open(CACHE, encoding="utf-8"))
    disk = {l.strip() for l in open(DISK_LIST, encoding="utf-8") if l.strip()}
    tb = Teable()
    fid = next(f["id"] for f in tb.fields(TABLE_PLAYERS) if f["name"] == "Mídia")

    todo = []
    for r in tb.all_records(TABLE_PLAYERS):
        m = r["fields"].get("Mídia")
        if not m or m[0]["path"].split("/")[-1] in disk:
            continue  # sem midia OU arquivo presente
        entry = cache.get(r["fields"].get("ID"))
        url = media_url(entry) if entry else None
        if url:
            todo.append((r["id"], r["fields"].get("ID"), url))
    if args.limit:
        todo = todo[:args.limit]
    log(f"{len(todo)} players a recuperar")
    if args.dry_run:
        for rid, aid, url in todo[:6]:
            log(f"  {aid} <- {url[:80]}")
        return

    WORK.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()

    def work(item):
        rec_id, aid, url = item
        try:
            rr = sess.get(url, timeout=60)
            if rr.status_code != 200 or not rr.content:
                return aid, False
            ext = ".mp4" if url.lower().split("?")[0].endswith((".mp4", ".mov")) else ".jpg"
            fpath = WORK / f"{aid}{ext}"
            fpath.write_bytes(rr.content)
            # limpa a Midia morta antes: uploadAttachment ANEXA, entao sem isso
            # ficaria [arquivo_morto, novo] e a galeria mostraria o morto.
            # Sem typecast: com typecast=True o clear de attachment nulo falha.
            tb.patch(f"/api/table/{TABLE_PLAYERS}/record/{rec_id}",
                     {"fieldKeyType": "name", "record": {"fields": {"Mídia": None}}})
            tb.upload_attachment(TABLE_PLAYERS, rec_id, fid, fpath)
            fpath.unlink(missing_ok=True)
            return aid, True
        except Exception as e:
            log(f"  {aid}: {str(e)[:70]}")
            return aid, False

    ok = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, (_aid, done) in enumerate(pool.map(work, todo), 1):
            ok += bool(done)
            if i % 50 == 0:
                log(f"  {i}/{len(todo)} (ok {ok})")
    log(f"pronto: {ok}/{len(todo)} mídias recuperadas")


if __name__ == "__main__":
    main()
