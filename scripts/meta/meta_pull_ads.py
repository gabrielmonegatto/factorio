"""Varre os ads das contas do Meta, baixa a imagem de cada criativo e
calcula o dHash. Upsert em meta_ads. Idempotente.

  python meta_pull_ads.py                 # todas as contas
  python meta_pull_ads.py --account act_1363438474022368
  python meta_pull_ads.py --no-images     # so metadados (rapido)

Preserva r2_key/match_method ja gravados (inclusive os manuais).
"""
from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from _common import ACCOUNTS, D1, Graph, dhash_bytes, fetch_image, lit, log

AD_FIELDS = (
    "id,name,effective_status,created_time,"
    "campaign{id,name},adset{id,name},"
    "creative{id,name,image_hash,image_url,thumbnail_url,object_story_spec}"
)


def creative_image_url(cr: dict) -> str | None:
    """A melhor URL de imagem disponivel no creative.

    image_url e a arte em tamanho cheio; thumbnail_url e o fallback (video,
    ou creative que so expoe miniatura)."""
    if not cr:
        return None
    if cr.get("image_url"):
        return cr["image_url"]
    spec = cr.get("object_story_spec") or {}
    for key in ("link_data", "video_data", "photo_data"):
        node = spec.get(key) or {}
        if node.get("picture"):
            return node["picture"]
        if node.get("image_url"):
            return node["image_url"]
    return cr.get("thumbnail_url")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", help="processa so uma conta (act_...)")
    ap.add_argument("--no-images", action="store_true", help="pula download/dhash")
    ap.add_argument("--from-insights", action="store_true",
                    help="so os ads que tem entrega em meta_insights (recomendado: "
                         "as contas tem ~23k ads, mas so uma fracao rodou de fato)")
    args = ap.parse_args()

    accounts = [a for a in ACCOUNTS if not args.account or a[0] == args.account]
    if not accounts:
        raise SystemExit("conta nao encontrada em ACCOUNTS")

    db = D1()
    g = Graph()
    sess = requests.Session()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # dHash ja conhecido por creative_id -> nao rebaixa imagem em reexecucoes.
    known = {
        r["creative_id"]: r["dhash"]
        for r in db.query("SELECT creative_id, dhash FROM meta_ads WHERE dhash IS NOT NULL")
        if r.get("creative_id")
    }
    log(f"{len(known)} creatives ja com dhash em cache no banco")

    total_ads = 0
    total_hash = 0

    for acct_id, acct_name, brand in accounts:
        log(f"=== {acct_name} ({acct_id})")

        # Fase 1: metadados dos ads.
        if args.from_insights:
            ids = [r["ad_id"] for r in db.query(
                "SELECT DISTINCT ad_id FROM meta_insights WHERE account_id = ?", [acct_id])]
            log(f"  {len(ids)} ads com entrega em meta_insights")
            ads = []
            for i in range(0, len(ids), 50):     # ?ids= aceita 50 por vez
                chunk = ids[i:i + 50]
                try:
                    batch = g.get("", ids=",".join(chunk), fields=AD_FIELDS)
                except Exception:
                    # Um id invalido (ad apagado no Meta) derruba o lote
                    # inteiro; reprocessa um a um e descarta so o culpado.
                    batch = {}
                    for one in chunk:
                        try:
                            batch[one] = g.get(one, fields=AD_FIELDS)
                        except Exception as e:
                            log(f"  ad {one} indisponivel: {str(e)[:70]}")
                ads.extend(v for v in batch.values() if isinstance(v, dict) and v.get("id"))
                if (i // 50) % 10 == 0 and i:
                    log(f"  {len(ads)}/{len(ids)} metadados")
        else:
            ads = list(g.paginate(f"{acct_id}/ads", fields=AD_FIELDS, limit=100))
        log(f"  {len(ads)} ads lidos")

        # Fase 2: baixa+hasheia as imagens novas em paralelo. Serial fica
        # lento demais quando a banda esta ocupada (upload pro R2).
        pend = {}
        for ad in ads:
            cr = ad.get("creative") or {}
            cid, url = cr.get("id"), creative_image_url(cr)
            if cid and url and cid not in known:
                pend[cid] = url
        if pend and not args.no_images:
            log(f"  {len(pend)} creatives novos para hashear")

            def work(item):
                cid, url = item
                raw = fetch_image(url, f"meta_{cid}", sess)
                if not raw:
                    return cid, None
                try:
                    return cid, dhash_bytes(raw)
                except Exception as e:
                    log(f"  dhash falhou em creative {cid}: {e}")
                    return cid, None

            with ThreadPoolExecutor(max_workers=12) as pool:
                for i, (cid, dh) in enumerate(pool.map(work, pend.items()), 1):
                    if dh:
                        known[cid] = dh
                        total_hash += 1
                    if i % 100 == 0:
                        log(f"  hasheados {i}/{len(pend)}")

        # Fase 3: grava.
        stmts: list[str] = []
        n = 0
        for ad in ads:
            n += 1
            cr = ad.get("creative") or {}
            camp = ad.get("campaign") or {}
            adset = ad.get("adset") or {}
            cid = cr.get("id")
            url = creative_image_url(cr)
            dh = known.get(cid)

            cols = {
                "ad_id": ad["id"],
                "account_id": acct_id,
                "account_name": acct_name,
                "brand": brand,
                "campaign_id": camp.get("id"),
                "campaign_name": camp.get("name"),
                "adset_id": adset.get("id"),
                "adset_name": adset.get("name"),
                "ad_name": ad.get("name"),
                "effective_status": ad.get("effective_status"),
                "creative_id": cid,
                "creative_name": cr.get("name"),
                "image_hash": cr.get("image_hash"),
                "image_url": url,
                "thumbnail_url": cr.get("thumbnail_url"),
                "dhash": dh,
                "created_time": ad.get("created_time"),
                "updated_at": now,
            }
            keys = ",".join(cols)
            vals = ",".join(lit(v) for v in cols.values())
            # Nao toca em r2_key/match_*: o casamento (auto ou manual) e soberano.
            sets = ",".join(f"{k}=excluded.{k}" for k in cols if k != "ad_id")
            stmts.append(
                f"INSERT INTO meta_ads ({keys}) VALUES ({vals}) "
                f"ON CONFLICT(ad_id) DO UPDATE SET {sets}"
            )

        if stmts:
            db.exec_batch(stmts, label=f"{acct_name}: ")
        total_ads += n
        log(f"  {n} ads gravados")

    com_dhash = db.query("SELECT COUNT(*) n FROM meta_ads WHERE dhash IS NOT NULL")[0]["n"]
    log(f"pronto: {total_ads} ads no total, {total_hash} imagens hasheadas agora, "
        f"{com_dhash} ads com dhash no banco")


if __name__ == "__main__":
    main()
