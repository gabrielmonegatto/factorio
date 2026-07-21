"""Casa cada ad do Meta com um criativo do acervo pelo hash perceptual.

Regra: pega o criativo de menor distancia de Hamming. So aceita o match se
ele for INEQUIVOCO -- se ha mais de um candidato dentro da margem (artes
quase identicas, tipo V2 ou story/feed), manda pra reconciliacao manual em
vez de chutar.

  python meta_match.py --dry-run     # so relatorio, nao grava
  python meta_match.py               # grava match_method='phash'
  python meta_match.py --threshold 8 --margin 3
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict

from _common import D1, hamming, lit, log

# Muitos ads sao nomeados com o numero do criativo: "1096 - Feed.png - 20 Maio".
# Quando a imagem nao casa (o Meta recortou, ou e uma variacao), esse nome
# ainda resolve — e e exato quando existe um unico criativo com aquele
# numero+formato.
NAME_RE = re.compile(r"(?<!\d)(\d{1,5})\s*[-_ ]\s*(feed|story)", re.I)
AR_OF = {"FEED": "4x5", "STORY": "9x16"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=6, help="distancia maxima aceita (0-64)")
    ap.add_argument("--margin", type=int, default=2,
                    help="candidatos ate best+margin contam como concorrentes")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rematch", action="store_true",
                    help="reavalia tambem quem ja casou por phash (nunca mexe em manual)")
    args = ap.parse_args()

    db = D1()

    creatives = db.query("SELECT id, r2_key, dhash FROM creatives WHERE dhash IS NOT NULL")
    if not creatives:
        raise SystemExit("nenhum criativo com dhash -- rode creatives_dhash.py antes")
    log(f"{len(creatives)} criativos com dhash")

    cond = "r2_key IS NULL" if not args.rematch else "(r2_key IS NULL OR match_method IN ('phash','name'))"
    ads = db.query(f"SELECT ad_id, ad_name, brand, dhash FROM meta_ads WHERE {cond}")
    log(f"{len(ads)} ads a casar")

    # Indice (marca, numero, formato) -> criativos, para a ponte pelo nome.
    # A marca entra na chave porque numero de ad se repete entre marcas: um
    # ad "123 - Feed" da Tonaface nao pode casar com o criativo 123 da Bluue.
    by_num: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
    for c in db.query(
        "SELECT r2_key, brand, ad_number, aspect_ratio FROM creatives "
        "WHERE ad_number IS NOT NULL AND r2_key IS NOT NULL"
    ):
        by_num[(c["brand"], c["ad_number"], c["aspect_ratio"] or "")].append(c)

    # int uma vez so: hamming em hex string custa caro em 2500 x N.
    cand = [(int(c["dhash"], 16), c["r2_key"]) for c in creatives if c["r2_key"]]

    matched: list[str] = []
    ambiguous = 0
    far = 0
    by_dist: dict[int, int] = defaultdict(int)

    by_name = 0
    for i, ad in enumerate(ads, 1):
        if not ad["dhash"]:
            # Sem imagem comparavel: so resta o nome.
            key = _from_name(ad.get("ad_name"), ad.get("brand"), by_num)
            if key:
                by_name += 1
                matched.append(
                    f"UPDATE meta_ads SET r2_key={lit(key)}, match_method='name', "
                    f"match_distance=NULL, match_confidence=0.75 WHERE ad_id={lit(ad['ad_id'])}"
                )
            continue

        h = int(ad["dhash"], 16)
        dists = [(bin(h ^ chash).count("1"), key) for chash, key in cand]
        best = min(d for d, _ in dists)

        if best > args.threshold:
            # A imagem nao bateu; tenta o numero no nome do ad.
            key = _from_name(ad.get("ad_name"), ad.get("brand"), by_num)
            if key:
                by_name += 1
                matched.append(
                    f"UPDATE meta_ads SET r2_key={lit(key)}, match_method='name', "
                    f"match_distance={best}, match_confidence=0.75 WHERE ad_id={lit(ad['ad_id'])}"
                )
            else:
                far += 1
            continue
        by_dist[best] += 1
        # Concorrentes dentro da margem: se houver mais de um criativo
        # distinto, o match nao e confiavel -> reconciliacao manual.
        near = {key for d, key in dists if d <= best + args.margin}
        if len(near) > 1:
            ambiguous += 1
            continue
        key = near.pop()
        conf = round(1.0 - best / 64.0, 4)
        matched.append(
            f"UPDATE meta_ads SET r2_key={lit(key)}, match_method='phash', "
            f"match_distance={best}, match_confidence={conf} WHERE ad_id={lit(ad['ad_id'])}"
        )
        if i % 200 == 0:
            log(f"  {i}/{len(ads)} avaliados")

    log(f"casaram: {len(matched)} (imagem: {len(matched) - by_name}, nome do ad: {by_name}) "
        f"| ambiguos: {ambiguous} | sem candidato: {far}")
    if by_dist:
        log("distribuicao de distancia: " +
            ", ".join(f"d={d}:{n}" for d, n in sorted(by_dist.items())))

    if args.dry_run:
        log("dry-run: nada gravado")
        return
    if matched:
        db.exec_batch(matched, label="gravando ")

    tot = db.query(
        "SELECT COUNT(*) n, SUM(CASE WHEN r2_key IS NOT NULL THEN 1 ELSE 0 END) m FROM meta_ads"
    )[0]
    log(f"estado: {tot['m']}/{tot['n']} ads com criativo atribuido")


def _from_name(ad_name: str | None, brand: str | None, by_num: dict) -> str | None:
    """Extrai numero+formato do nome do ad e devolve o r2_key, se for unico.

    Exige unicidade: se o acervo tem V1 e V2 do mesmo numero/formato, nao da
    para saber qual rodou — vai para reconciliacao manual."""
    if not ad_name:
        return None
    m = NAME_RE.search(ad_name)
    if not m:
        return None
    cands = by_num.get((brand, int(m.group(1)), AR_OF[m.group(2).upper()]), [])
    return cands[0]["r2_key"] if len(cands) == 1 else None


if __name__ == "__main__":
    main()
