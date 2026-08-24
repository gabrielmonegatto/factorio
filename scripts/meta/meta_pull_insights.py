"""Puxa metricas diarias por ad e faz upsert em meta_insights.

Grao = (ad_id, date). Reexecutar sobre o mesmo periodo e seguro: sobrescreve
os mesmos dias (numeros do Meta mudam por ate ~72h de atribuicao, entao
reprocessar a ultima semana todo dia e o comportamento desejado).

  python meta_pull_insights.py                    # ultimos 30 dias
  python meta_pull_insights.py --days 7           # janela curta (cron diario)
  python meta_pull_insights.py --since 2026-01-01 --until 2026-07-20
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time

from _common import ACCOUNTS, CURRENCY, D1, Graph, lit, log

FIELDS = ("ad_id,spend,impressions,clicks,ctr,actions,action_values,"
          "conversions,conversion_values,date_start")

# O pixel padrao (Purchase) parou de disparar em 30/04/2026; de maio em
# diante a compra vem como conversao custom ofuscada 'p'. Lemos os dois e
# ficamos com o maior -- as janelas nao se sobrepoem, entao nao duplica.
PURCHASE_KEYS = {
    "offsite_conversion.fb_pixel_purchase",
    "onsite_web_purchase",
    "onsite_web_app_purchase",
    "omni_purchase",
    "web_in_store_purchase",
    "purchase",
}
CUSTOM_PURCHASE = {"offsite_conversion.fb_pixel_custom.p"}
CUSTOM_ATC = {"offsite_conversion.fb_pixel_custom.a_t_c", "add_to_cart",
              "offsite_conversion.fb_pixel_add_to_cart"}
CUSTOM_IC = {"offsite_conversion.fb_pixel_custom.i_c", "initiate_checkout",
             "offsite_conversion.fb_pixel_initiate_checkout"}
LEAD_KEYS = {"lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"}


def _sum(actions: list | None, keys: set[str]) -> float:
    """Maior valor entre os aliases pedidos.

    O Meta devolve o mesmo evento sob varios nomes (purchase, omni_purchase,
    onsite_web_purchase...) com valores identicos; somar inflaria o numero,
    entao pegamos o maior."""
    if not actions:
        return 0.0
    vals = [float(a.get("value") or 0) for a in actions if a.get("action_type") in keys]
    return max(vals) if vals else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--account")
    ap.add_argument("--resume", action="store_true",
                    help="por conta, comeca do dia seguinte ao ultimo ja gravado "
                         "(retoma carga longa interrompida por rate limit)")
    ap.add_argument("--chunk-days", type=int, default=15,
                    help="tamanho do bloco de datas por request; janela longa com "
                         "granularidade diaria estoura o limite do Meta (erro 500/1)")
    args = ap.parse_args()

    today = dt.date.today()
    until = dt.date.fromisoformat(args.until) if args.until else today
    since = dt.date.fromisoformat(args.since) if args.since else until - dt.timedelta(days=args.days - 1)
    log(f"janela: {since} -> {until}")

    accounts = [a for a in ACCOUNTS if not args.account or a[0] == args.account]
    db = D1()
    g = Graph()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    grand = 0

    def make_blocks(ini: dt.date) -> list[tuple[dt.date, dt.date]]:
        """Uma janela longa com time_increment=1 no nivel de ad faz o Meta
        responder erro em vez de paginar; por isso fatiamos."""
        out, cur = [], ini
        while cur <= until:
            end = min(cur + dt.timedelta(days=args.chunk_days - 1), until)
            out.append((cur, end))
            cur = end + dt.timedelta(days=1)
        return out

    for acct_id, acct_name, _brand in accounts:
        ini = since
        if args.resume:
            got = db.query(
                "SELECT MAX(date) d FROM meta_insights WHERE account_id = ?", [acct_id])
            last = got[0]["d"] if got else None
            if last:
                ini = max(since, dt.date.fromisoformat(last) + dt.timedelta(days=1))
                log(f"  {acct_name}: ja tem ate {last}, retomando de {ini}")
        blocks = make_blocks(ini)
        if not blocks:
            log(f"=== {acct_name} ({acct_id}) — nada a fazer")
            continue
        log(f"=== {acct_name} ({acct_id}) — {len(blocks)} blocos")
        acct_rows = 0
        for bi, (b0, b1) in enumerate(blocks, 1):
            try:
                rows = list(g.paginate(
                    f"{acct_id}/insights",
                    level="ad",
                    time_increment=1,
                    time_range=json.dumps({"since": str(b0), "until": str(b1)}),
                    fields=FIELDS,
                    limit=500,
                ))
            except Exception as e:
                log(f"  bloco {b0}..{b1} falhou ({e}); segue para o proximo")
                continue

            stmts = []
            for row in rows:
                actions = row.get("actions")
                conv = row.get("conversions")
                conv_val = row.get("conversion_values")
                cols = {
                    "ad_id": row.get("ad_id"),
                    "date": row.get("date_start"),
                    "account_id": acct_id,
                    "currency": CURRENCY.get(acct_id, "BRL"),
                    "spend": float(row.get("spend") or 0),
                    "impressions": int(row.get("impressions") or 0),
                    "clicks": int(row.get("clicks") or 0),
                    "link_clicks": int(_sum(actions, {"link_click"})),
                    "ctr": float(row.get("ctr") or 0),
                    "purchases": int(max(_sum(actions, PURCHASE_KEYS),
                                         _sum(conv, CUSTOM_PURCHASE))),
                    "revenue": max(_sum(row.get("action_values"), PURCHASE_KEYS),
                                   _sum(conv_val, CUSTOM_PURCHASE)),
                    "atc": int(max(_sum(actions, CUSTOM_ATC), _sum(conv, CUSTOM_ATC))),
                    "checkouts": int(max(_sum(actions, CUSTOM_IC), _sum(conv, CUSTOM_IC))),
                    "leads": int(_sum(actions, LEAD_KEYS)),
                    "updated_at": now,
                }
                if not cols["ad_id"] or not cols["date"]:
                    continue
                keys = ",".join(cols)
                vals = ",".join(lit(v) for v in cols.values())
                sets = ",".join(f"{k}=excluded.{k}" for k in cols if k not in ("ad_id", "date"))
                stmts.append(
                    f"INSERT INTO meta_insights ({keys}) VALUES ({vals}) "
                    f"ON CONFLICT(ad_id,date) DO UPDATE SET {sets}"
                )

            if stmts:
                db.exec_batch(stmts, chunk=200)
            acct_rows += len(stmts)
            log(f"  bloco {bi}/{len(blocks)} ({b0}..{b1}): {len(stmts)} linhas "
                f"| acumulado {acct_rows}")

        grand += acct_rows

    tot = db.query(
        "SELECT COUNT(*) n, COALESCE(SUM(spend),0) spend, COALESCE(SUM(revenue),0) rev "
        f"FROM meta_insights WHERE date >= {lit(str(since))}"
    )[0]
    log(f"pronto: {grand} linhas gravadas. Na janela: {tot['n']} linhas, "
        f"spend {tot['spend']:.2f}, receita {tot['rev']:.2f}")


if __name__ == "__main__":
    main()
