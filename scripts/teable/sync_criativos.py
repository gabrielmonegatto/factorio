"""Espelha o acervo de criativos (D1) na tabela br4nds_criativos do Teable.

Mao unica: D1 -> Teable, e SO nos campos de maquina. As colunas de curadoria
(Gancho, Avatar, Gatilhos, Copy...) sao do humano e nunca sao tocadas -- e
justamente o trabalho que nao da para automatizar.

  python sync_criativos.py --dry-run     # mostra o que faria
  python sync_criativos.py               # dados (sem midia)
  python sync_criativos.py --media       # sobe as miniaturas que faltam
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "meta"))
from _common import D1, log  # noqa: E402

from _teable import TABLE_CRIATIVOS, Teable  # noqa: E402

# Staging local dos PNGs (mesma pasta usada no upload para o R2).
STAGING = pathlib.Path(
    r"C:\Users\MONEGA~1\AppData\Local\Temp\claude"
    r"\C--Users-Monegatto-Desktop-EternalL"
    r"\19f9fca5-fe81-4845-952f-054352f943b7\scratchpad\upload"
)
THUMBS = pathlib.Path(__file__).resolve().parent / ".thumbs"
THUMB_MAX = 500          # px no maior lado
CDN = "https://bluue-63w.pages.dev/api/creative-img/"

AR = {"9x16": "Story 9:16", "4x5": "Feed 4:5"}
FUNIL = {"impacto": "Impacto", "remarketing": "Remarketing"}

SQL = """
SELECT c.id, c.brand, c.product, c.type, c.aspect_ratio, c.funnel_stage,
       c.ad_number, c.r2_key, c.drive_modified,
       pf.ads, pf.spend, pf.impressions, pf.clicks, pf.purchases, pf.revenue,
       pf.ultimo
  FROM creatives c
  LEFT JOIN (
    SELECT ma.r2_key AS r2_key,
           COUNT(DISTINCT ma.ad_id) AS ads,
           SUM(mi.spend) AS spend, SUM(mi.impressions) AS impressions,
           SUM(mi.clicks) AS clicks, SUM(mi.purchases) AS purchases,
           SUM(mi.revenue) AS revenue, MAX(mi.date) AS ultimo
      FROM meta_ads ma JOIN meta_insights mi ON mi.ad_id = ma.ad_id
     WHERE ma.r2_key IS NOT NULL
     GROUP BY ma.r2_key
  ) pf ON pf.r2_key = c.r2_key
"""


def machine_fields(r: dict, now: str) -> dict:
    spend = r.get("spend") or 0
    imp = r.get("impressions") or 0
    f = {
        "ID": r["id"],
        "Marca": (r.get("brand") or "").capitalize() or None,
        "Produto": r.get("product"),
        "Formato": "VIDEO" if r.get("type") == "video" else "IMAGE",
        "Proporção": AR.get(r.get("aspect_ratio") or ""),
        "Etapa do Funil": FUNIL.get(r.get("funnel_stage") or ""),
        "Nº do Ad": r.get("ad_number"),
        "Arquivo (R2)": CDN + r["r2_key"] if r.get("r2_key") else None,
        "Produzido em": (r.get("drive_modified") or "")[:10] or None,
        "Investido": round(spend, 2) or None,
        "Compras": r.get("purchases") or None,
        "Receita": round(r.get("revenue") or 0, 2) or None,
        "ROAS": round((r.get("revenue") or 0) / spend, 2) if spend else None,
        "CTR %": round((r.get("clicks") or 0) / imp * 100, 2) if imp else None,
        "Nº de Anúncios": r.get("ads") or None,
        "Última veiculação": r.get("ultimo"),
        "Sincronizado em": now,
    }
    return {k: v for k, v in f.items() if v is not None}


def thumb_for(r2_key: str) -> pathlib.Path | None:
    """Gera (e cacheia) a miniatura. Subir os 6,7 GB originais para a VPS
    seria desnecessario: a galeria so precisa de preview."""
    out = THUMBS / (r2_key.replace("/", "_").rsplit(".", 1)[0] + ".webp")
    if out.exists() and out.stat().st_size:
        return out
    src = STAGING / r2_key
    if not src.exists():
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(src) as im:
            im.load()
            im.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
            im.convert("RGB").save(out, "WEBP", quality=80, method=4)
    except Exception as e:
        log(f"  thumb falhou em {r2_key}: {e}")
        return None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--media", action="store_true", help="passada de upload das miniaturas")
    ap.add_argument("--limit", type=int, help="processa so N (teste)")
    args = ap.parse_args()

    tb = Teable()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    rows = D1().query(SQL)
    if args.limit:
        rows = rows[:args.limit]
    log(f"{len(rows)} criativos no D1")

    existing = {}
    for rec in tb.all_records(TABLE_CRIATIVOS):
        rid = rec["fields"].get("ID")
        if rid:
            existing[rid] = rec
    log(f"{len(existing)} ja no Teable")

    if args.media:
        return media_pass(tb, rows, existing)

    novos = [r for r in rows if r["id"] not in existing]
    updates = [r for r in rows if r["id"] in existing]
    log(f"a criar: {len(novos)} | a atualizar: {len(updates)}")

    if args.dry_run:
        if novos:
            log("exemplo do que seria criado:")
            for k, v in machine_fields(novos[0], now).items():
                log(f"   {k}: {v}")
        return

    if novos:
        tb.create_records(TABLE_CRIATIVOS, [machine_fields(r, now) for r in novos])

    # Atualiza so quem tem performance -- evita 2500 PATCHs por nada.
    mexeu = 0
    for r in updates:
        if not (r.get("spend") or r.get("ads")):
            continue
        tb.update_record(TABLE_CRIATIVOS, existing[r["id"]]["id"], machine_fields(r, now))
        mexeu += 1
        if mexeu % 50 == 0:
            log(f"  atualizados {mexeu}")
    log(f"pronto: {len(novos)} criados, {mexeu} atualizados")


def media_pass(tb: Teable, rows: list[dict], existing: dict) -> None:
    THUMBS.mkdir(exist_ok=True)
    fid = next(f["id"] for f in tb.fields(TABLE_CRIATIVOS) if f["name"] == "Mídia")

    pend = [r for r in rows
            if r["id"] in existing
            and not existing[r["id"]]["fields"].get("Mídia")
            and r.get("r2_key")]
    log(f"{len(pend)} registros sem midia")

    def work(r):
        t = thumb_for(r["r2_key"])
        if not t:
            return r["id"], False
        try:
            tb.upload_attachment(TABLE_CRIATIVOS, existing[r["id"]]["id"], fid, t)
            return r["id"], True
        except Exception as e:
            log(f"  upload falhou {r['id']}: {str(e)[:90]}")
            return r["id"], False

    ok = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, (_rid, done) in enumerate(pool.map(work, pend), 1):
            ok += bool(done)
            if i % 50 == 0:
                log(f"  {i}/{len(pend)} (ok: {ok})")
    log(f"pronto: {ok}/{len(pend)} miniaturas no Teable")


if __name__ == "__main__":
    main()
