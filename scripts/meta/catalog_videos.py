"""Cataloga os videos do Drive na tabela creatives (type=video).

Entra so METADADO: nome, leva, drive_id, tamanho e uma match_key derivada do
nome do arquivo. O .mp4 em si NAO baixa aqui -- so os campeoes serao puxados
depois (o arquivo e pesado e a maioria nunca sera reusada).

  python catalog_videos.py --index <videos_index.json> --dry-run
  python catalog_videos.py --index <videos_index.json>
"""
from __future__ import annotations

import argparse
import json
import re

from _common import D1, lit, log

BRAND = "bluue"


def match_key(filename: str) -> str:
    """Chave de casamento: base do nome sem extensao, so alfanumerico maiusculo.

    Alinha com o token que extraimos do ad_name do Meta ('BL7-IA-C7-...mp4').
    Se houver parentese com a fonte real ('BL20-V3(BL7-IA-C7...)'), usa o
    conteudo do parentese, que e o criativo de origem."""
    base = filename.rsplit(".", 1)[0]
    par = re.search(r"\(([^)]*BL\d[^)]*)\)", base, re.I)
    if par:
        base = par.group(1)
    return re.sub(r"[^A-Z0-9]", "", base.upper())


def leva_of(path: str, filename: str) -> int | None:
    m = re.match(r"BL(\d+)", filename, re.I)
    if m:
        return int(m.group(1))
    m = re.match(r"LEVA-(\d+)", path, re.I)
    return int(m.group(1)) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True, help="videos_index.json do rclone lsjson")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = json.load(open(args.index, encoding="utf-8"))
    items = [x for x in items if (x.get("MimeType") == "video/mp4"
                                  or x["Path"].lower().endswith(".mp4"))]
    log(f"{len(items)} videos no indice")

    db = D1()
    seen = {r["drive_id"] for r in db.query(
        "SELECT drive_id FROM creatives WHERE drive_id IS NOT NULL")}

    rows = []
    dup = 0
    for i, x in enumerate(sorted(items, key=lambda z: z["Path"]), 1):
        if x["ID"] in seen:
            dup += 1
            continue
        vid = f"BLV-{i:04d}"
        rows.append({
            "id": vid,
            "brand": BRAND,
            "type": "video",
            "format": "mp4",
            # endereco-destino no R2 ja definido: o join com meta_ads funciona
            # antes do upload, e o campeao sobe exatamente aqui depois.
            "r2_key": f"bluue/videos/{vid}.mp4",
            "size_bytes": x["Size"],
            "drive_id": x["ID"],
            "drive_path": x["Path"],        # a match_key sai daqui, na hora do match
            "drive_modified": (x.get("ModTime") or "")[:19] or None,
        })

    log(f"a inserir: {len(rows)} | ja catalogados (dup): {dup}")
    if args.dry_run:
        for r in rows[:6]:
            fn = r["drive_path"].rsplit("/", 1)[-1]
            log(f"  {r['id']} | leva {leva_of(r['drive_path'], fn)} "
                f"| key={match_key(fn)[:28]} | {r['size_bytes']//2**20}MB | {r['drive_path'][:46]}")
        return

    keys = ("id", "brand", "type", "format", "r2_key", "size_bytes",
            "drive_id", "drive_path", "drive_modified")
    stmts = []
    for r in rows:
        vals = ",".join(lit(r[k]) for k in keys)
        stmts.append(f"INSERT INTO creatives ({','.join(keys)}) VALUES ({vals})")
    if stmts:
        db.exec_batch(stmts, chunk=100, label="inserindo ")

    tot = db.query("SELECT COUNT(*) n FROM creatives WHERE type='video'")[0]["n"]
    log(f"pronto: {tot} videos catalogados no D1")


if __name__ == "__main__":
    main()
