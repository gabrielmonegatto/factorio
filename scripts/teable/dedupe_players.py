"""Remove registros duplicados em players_criativos (mesmo Foreplay ID,
copias identicas de import repetido). Mantem 1 por anuncio.

Keeper = o que tiver curadoria humana; senao o que tiver midia; senao o
primeiro. Deleta o resto via API (registros validos aceitam DELETE).

  python dedupe_players.py --dry-run
  python dedupe_players.py
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _teable import TABLE_PLAYERS, Teable  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "meta"))
from _common import log  # noqa: E402

CURATION = ["Gancho", "Avatar", "Gatilho Emocional", "Gatilhos Mentais", "Oferta"]


def score(r: dict) -> tuple:
    """Maior = melhor keeper: curadoria > midia > qualquer."""
    f = r["fields"]
    return (sum(1 for c in CURATION if f.get(c)), 1 if f.get("Mídia") else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tb = Teable()
    recs = tb.all_records(TABLE_PLAYERS)

    by_fid = collections.defaultdict(list)
    for r in recs:
        by_fid[r["fields"].get("ID")].append(r)

    to_delete = []
    for fid_val, group in by_fid.items():
        if len(group) < 2:
            continue
        keeper = max(group, key=score)
        for r in group:
            if r["id"] != keeper["id"]:
                to_delete.append(r)

    brands = collections.Counter(r["fields"].get("Player") for r in to_delete)
    log(f"grupos duplicados: {sum(1 for g in by_fid.values() if len(g) > 1)}")
    log(f"registros a remover: {len(to_delete)} | por marca: {dict(brands)}")

    # salvaguarda: nunca remover Rugiet/Hims (recem-recriados, unicos)
    perigo = [r for r in to_delete if r["fields"].get("Player") in ("Rugiet", "Hims")]
    if perigo:
        raise SystemExit(f"ABORTADO: {len(perigo)} de Rugiet/Hims na lista de remocao")

    if args.dry_run:
        log("dry-run: nada removido")
        return

    ok = fail = 0
    for i, r in enumerate(to_delete, 1):
        try:
            tb.delete(f"/api/table/{TABLE_PLAYERS}/record/{r['id']}")
            ok += 1
        except Exception as e:
            log(f"  {r['id']}: {str(e)[:70]}"); fail += 1
        if i % 50 == 0:
            log(f"  {i}/{len(to_delete)} (ok {ok}, falhou {fail})")
    log(f"pronto: {ok} removidos, {fail} falharam")


if __name__ == "__main__":
    main()
