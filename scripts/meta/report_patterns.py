"""Relatorio de padroes de campanha: hora x dia, dia da semana, regiao, e
hora do clique (Meta) vs hora da compra real (first-party).

Le meta_breakdown_hourly / meta_breakdown_region / meta_insights /
purchases_sent do D1 e cospe um JSON + resumo no terminal.

Normalizacoes que importam (sem elas o relatorio MENTE):
- Fuso: LF1/LF10 reportam em America/Sao_Paulo; CA1/CA2/Tonaface em
  America/Los_Angeles. Tudo e convertido para hora de Sao Paulo.
  DST americano 2026: comeca 08/03 (LA = UTC-7); antes, UTC-8. SP = UTC-3 fixo.
- Moeda: CA1/CA2/Tonaface faturam em USD -> convertido a 5.40 (mesma
  convencao do BI) ao agregar.
- A "hora" do Meta e a hora do CLIQUE atribuido; a do first-party e a hora
  em que o dinheiro caiu. Sao perguntas diferentes.

  python report_patterns.py [--out report.json]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict

from _common import D1, log

USD_BRL = 5.40
DST_2026 = dt.date(2026, 3, 8)          # inicio do DST americano
WEEKDAYS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def to_sp(date_s: str, hour: int, tz: str) -> tuple[str, int]:
    """Converte (data, hora) do fuso da conta para Sao Paulo."""
    if tz == "America/Sao_Paulo":
        return date_s, hour
    d = dt.date.fromisoformat(date_s)
    delta = 4 if d >= DST_2026 else 5    # LA -> SP
    t = dt.datetime(d.year, d.month, d.day, hour) + dt.timedelta(hours=delta)
    return t.date().isoformat(), t.hour


def brl(v: float, currency: str) -> float:
    return v * USD_BRL if currency == "USD" else v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="report_patterns.json")
    ap.add_argument("--since", default="2026-01-01")
    args = ap.parse_args()
    db = D1()
    rep: dict = {"generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                 "since": args.since, "usd_brl": USD_BRL}

    # ---------------- 1. heatmap hora x dia-da-semana (hora do clique, SP)
    rows = db.query(f"SELECT * FROM meta_breakdown_hourly WHERE date >= '{args.since}'")
    hm = defaultdict(lambda: {"spend": 0.0, "purchases": 0, "revenue": 0.0,
                              "clicks": 0, "impressions": 0})
    for r in rows:
        d_sp, h_sp = to_sp(r["date"], r["hour"], r["tz"])
        wd = dt.date.fromisoformat(d_sp).weekday()
        c = hm[(wd, h_sp)]
        c["spend"] += brl(r["spend"], r["currency"])
        c["revenue"] += brl(r["revenue"], r["currency"])
        c["purchases"] += r["purchases"]
        c["clicks"] += r["clicks"]
        c["impressions"] += r["impressions"]
    rep["heatmap_click"] = [
        {"weekday": wd, "hour": h, **{k: round(v, 2) for k, v in c.items()}}
        for (wd, h), c in sorted(hm.items())]
    rep["hourly_rows"] = len(rows)

    # agregado por hora (todas as semanas)
    by_hour = defaultdict(lambda: [0.0, 0, 0.0])
    for (wd, h), c in hm.items():
        by_hour[h][0] += c["spend"]; by_hour[h][1] += c["purchases"]; by_hour[h][2] += c["revenue"]
    rep["by_hour_click"] = [
        {"hour": h, "spend": round(s, 2), "purchases": p, "revenue": round(rv, 2),
         "roas": round(rv / s, 2) if s else None}
        for h, (s, p, rv) in sorted(by_hour.items())]

    # ---------------- 2. dia da semana (diario, base completa)
    rows = db.query(f"""SELECT mi.date, mi.spend, mi.purchases, mi.revenue, mi.account_id
                        FROM meta_insights mi WHERE mi.date >= '{args.since}'""")
    from _common import CURRENCY  # mapa conta -> moeda (mantido pela outra frente)
    by_wd = defaultdict(lambda: [0.0, 0, 0.0, set()])
    for r in rows:
        wd = dt.date.fromisoformat(r["date"]).weekday()
        cur = CURRENCY.get(r["account_id"], "BRL")
        by_wd[wd][0] += brl(r["spend"] or 0, cur)
        by_wd[wd][1] += r["purchases"] or 0
        by_wd[wd][2] += brl(r["revenue"] or 0, cur)
        by_wd[wd][3].add(r["date"])
    rep["by_weekday"] = [
        {"weekday": wd, "label": WEEKDAYS[wd], "days": len(dates),
         "spend": round(s, 2), "purchases": p, "revenue": round(rv, 2),
         "roas": round(rv / s, 2) if s else None,
         "purchases_per_day": round(p / len(dates), 1) if dates else 0}
        for wd, (s, p, rv, dates) in sorted(by_wd.items())]

    # ---------------- 3. regiao (filtro de confianca: >= 50 compras)
    rows = db.query(f"SELECT * FROM meta_breakdown_region WHERE date >= '{args.since}'")
    by_reg = defaultdict(lambda: [0.0, 0, 0.0])
    for r in rows:
        by_reg[r["region"]][0] += brl(r["spend"], r["currency"])
        by_reg[r["region"]][1] += r["purchases"]
        by_reg[r["region"]][2] += brl(r["revenue"], r["currency"])
    regs = [{"region": k, "spend": round(s, 2), "purchases": p,
             "revenue": round(rv, 2), "roas": round(rv / s, 2) if s else None,
             "trusted": p >= 50}
            for k, (s, p, rv) in by_reg.items() if s > 0]
    regs.sort(key=lambda x: -x["spend"])
    rep["by_region"] = regs
    rep["region_rows"] = len(rows)

    # ---------------- 4. first-party: hora REAL da compra (UTC-3)
    # transaction_date = criacao do pedido (hora real do comportamento).
    # paid_date NAO serve: a Flow atualiza status em lote ~04:40-05:00 UTC,
    # o que criava um falso pico de compras a 1h da manha.
    rows = db.query("""SELECT transaction_date AS ts, value
                       FROM purchases_sent WHERE transaction_date IS NOT NULL""")
    fp_hour = defaultdict(lambda: [0, 0.0])
    fp_wd = defaultdict(lambda: [0, 0.0])
    fp_hm = defaultdict(int)
    n_fp = 0
    for r in rows:
        try:
            t = dt.datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
        except Exception:
            continue
        t = t + dt.timedelta(hours=-3)   # UTC -> SP
        n_fp += 1
        fp_hour[t.hour][0] += 1; fp_hour[t.hour][1] += (r["value"] or 0)
        fp_wd[t.weekday()][0] += 1; fp_wd[t.weekday()][1] += (r["value"] or 0)
        fp_hm[(t.weekday(), t.hour)] += 1
    rep["firstparty_n"] = n_fp
    rep["fp_by_hour"] = [{"hour": h, "purchases": c, "revenue": round(v, 2)}
                         for h, (c, v) in sorted(fp_hour.items())]
    rep["fp_by_weekday"] = [{"weekday": wd, "label": WEEKDAYS[wd], "purchases": c,
                             "revenue": round(v, 2)} for wd, (c, v) in sorted(fp_wd.items())]
    rep["fp_heatmap"] = [{"weekday": wd, "hour": h, "purchases": c}
                         for (wd, h), c in sorted(fp_hm.items())]

    json.dump(rep, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"salvo em {args.out}")

    # ---------------- resumo no terminal
    log(f"linhas hora: {rep['hourly_rows']} | regiao: {rep['region_rows']} | first-party: {n_fp}")
    top_h = sorted(rep["by_hour_click"], key=lambda x: -(x["purchases"]))[:5]
    log("top horas por compras (hora do clique, SP): " +
        ", ".join(f"{x['hour']}h={x['purchases']}" for x in top_h))
    if rep["fp_by_hour"]:
        top_fp = sorted(rep["fp_by_hour"], key=lambda x: -x["purchases"])[:5]
        log("top horas por compras (hora REAL, SP): " +
            ", ".join(f"{x['hour']}h={x['purchases']}" for x in top_fp))
    for x in rep["by_weekday"]:
        log(f"  {x['label']}: spend {x['spend']:>12,.0f}  compras {x['purchases']:>5}  "
            f"roas {x['roas']}  ({x['purchases_per_day']}/dia)")


if __name__ == "__main__":
    main()
