"""Recria os registros de player defeituosos (IDs invalidos da migracao, so
Rugiet+Hims) como registros NOVOS e validos, preservando TODA a curadoria
humana e re-anexando a midia a partir do cache do Foreplay.

Nao-destrutivo: os defeituosos ficam intocados. A remocao deles e passo
separado, com aprovacao humana (gate de delecao).

Idempotente: pula quem ja tem um registro valido (id de 19 chars) com o
mesmo Foreplay ID.

  python recreate_broken_players.py --dry-run
  python recreate_broken_players.py [--limit N]
"""
from __future__ import annotations

import argparse
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
WORK = pathlib.Path(tempfile.gettempdir()) / "players_recreate"

# Campos a copiar do registro velho para o novo. 'Mídia' fica de fora (o
# arquivo velho morreu; re-anexamos do cache). Tudo mais, inclusive a
# curadoria humana, e carregado tal e qual.
COPY_FIELDS = [
    "ID", "Player", "Copy Principal", "Headline", "Formato", "Duração (Dias)",
    "Landing Page URL", "Data de Início", "Status", "Mídia URL Original",
    "Etapa do Funil", "Oferta", "Gancho", "Avatar", "Gatilho Emocional",
    "Gatilhos Mentais", "CTA",
]
VALID_ID_LEN = 19   # registro sao do Teable v2; os quebrados tem 25


def media_url(entry: dict) -> str | None:
    return entry.get("image") or entry.get("video") or entry.get("thumbnail")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    cache = json.load(open(CACHE, encoding="utf-8"))
    tb = Teable()
    fid = next(f["id"] for f in tb.fields(TABLE_PLAYERS) if f["name"] == "Mídia")

    recs = tb.all_records(TABLE_PLAYERS)
    valid_ids = {r["fields"].get("ID") for r in recs if len(r["id"]) == VALID_ID_LEN}
    broken = [r for r in recs if len(r["id"]) != VALID_ID_LEN]
    todo = [r for r in broken if r["fields"].get("ID") not in valid_ids]
    if args.limit:
        todo = todo[:args.limit]
    log(f"defeituosos: {len(broken)} | a recriar (sem valido equivalente): {len(todo)}")

    if args.dry_run:
        for r in todo[:5]:
            f = r["fields"]
            cur = [c for c in ("Gancho", "Avatar", "Gatilho Emocional") if f.get(c)]
            e = cache.get(f.get("ID"), {})
            log(f"  {f.get('Player')} | {f.get('ID')} | curadoria:{cur} | midia:{bool(media_url(e))}")
        return

    # 1) cria os registros novos (sem midia), carregando todos os campos
    payload = []
    for r in todo:
        f = r["fields"]
        payload.append({k: f[k] for k in COPY_FIELDS if f.get(k) is not None})
    created = tb.create_records(TABLE_PLAYERS, payload)
    log(f"{len(created)} registros novos criados")

    # mapa Foreplay ID -> novo record id
    newmap = {c["fields"].get("ID"): c["id"] for c in created}

    # 2) baixa a midia do cache e anexa nos novos
    WORK.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()

    def work(r):
        aid = r["fields"].get("ID")
        rec_id = newmap.get(aid)
        url = media_url(cache.get(aid, {}))
        if not rec_id or not url:
            return aid, False
        try:
            rr = sess.get(url, timeout=60)
            if rr.status_code != 200 or not rr.content:
                return aid, False
            ext = ".mp4" if url.lower().split("?")[0].endswith((".mp4", ".mov")) else ".jpg"
            fp = WORK / f"{aid}{ext}"
            fp.write_bytes(rr.content)
            tb.upload_attachment(TABLE_PLAYERS, rec_id, fid, fp)
            fp.unlink(missing_ok=True)
            return aid, True
        except Exception as e:
            log(f"  {aid}: {str(e)[:70]}")
            return aid, False

    ok = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, (_aid, done) in enumerate(pool.map(work, todo), 1):
            ok += bool(done)
            if i % 50 == 0:
                log(f"  midia {i}/{len(todo)} (ok {ok})")
    log(f"pronto: {len(created)} recriados, {ok} com midia. "
        f"Os {len(broken)} defeituosos seguem intocados (aguardam gate de delecao).")


if __name__ == "__main__":
    main()
