"""Cria o schema da tabela br4nds_criativos no Teable.

Espelha a forma de players_criativos (concorrentes) para que os dois lados
sejam comparaveis na mesma regua. Idempotente: campo que ja existe e pulado.

  python setup_criativos.py
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "meta"))
from _common import log  # noqa: E402

from _teable import TABLE_CRIATIVOS, Teable  # noqa: E402

# (nome, tipo, options). A ordem aqui vira a ordem das colunas na tabela.
#
# Bloco 1 = identidade e midia. Bloco 2 = performance, escrita pela maquina.
# Bloco 3 = curadoria, escrita por humano -- o sync NUNCA toca nesses.
FIELDS = [
    # --- identidade
    ("Marca", "singleSelect", {"choices": [{"name": n} for n in ("Bluue", "Tonaface", "Milagrosa")]}),
    ("Produto", "singleLineText", None),
    ("Formato", "singleSelect", {"choices": [{"name": n} for n in ("IMAGE", "VIDEO", "CAROUSEL", "DCO")]}),
    ("Proporção", "singleSelect", {"choices": [{"name": n} for n in ("Story 9:16", "Feed 4:5")]}),
    ("Etapa do Funil", "singleSelect", {"choices": [{"name": n} for n in ("Impacto", "Remarketing")]}),
    ("Nº do Ad", "number", {"formatting": {"type": "decimal", "precision": 0}}),
    ("Mídia", "attachment", None),
    ("Arquivo (R2)", "singleLineText", None),
    ("Produzido em", "date", {"formatting": {"date": "YYYY-MM-DD", "time": "None",
                                             "timeZone": "America/Sao_Paulo"}}),
    # --- performance (maquina)
    ("Investido", "number", {"formatting": {"type": "decimal", "precision": 2}}),
    ("Compras", "number", {"formatting": {"type": "decimal", "precision": 0}}),
    ("Receita", "number", {"formatting": {"type": "decimal", "precision": 2}}),
    ("ROAS", "number", {"formatting": {"type": "decimal", "precision": 2}}),
    ("CTR %", "number", {"formatting": {"type": "decimal", "precision": 2}}),
    ("Nº de Anúncios", "number", {"formatting": {"type": "decimal", "precision": 0}}),
    ("Última veiculação", "date", {"formatting": {"date": "YYYY-MM-DD", "time": "None",
                                                  "timeZone": "America/Sao_Paulo"}}),
    ("Sincronizado em", "date", {"formatting": {"date": "YYYY-MM-DD", "time": "HH:mm",
                                                "timeZone": "America/Sao_Paulo"}}),
    # --- curadoria (humano) — mesmos nomes de players_criativos
    ("Gancho", "singleLineText", None),
    ("Avatar", "singleLineText", None),
    ("Gatilho Emocional", "singleLineText", None),
    ("Gatilhos Mentais", "longText", None),
    ("CTA", "singleLineText", None),
    ("Headline", "singleLineText", None),
    ("Copy Principal", "longText", None),
    ("Oferta", "singleLineText", None),
    ("Notas", "longText", None),
]


def main() -> None:
    tb = Teable()
    existing = {f["name"]: f for f in tb.fields(TABLE_CRIATIVOS)}

    # O campo primario nasce como "Label"; vira o nosso ID (BLU-0748-FEED).
    if "Label" in existing and "ID" not in existing:
        tb.patch(f"/api/table/{TABLE_CRIATIVOS}/field/{existing['Label']['id']}", {"name": "ID"})
        log("renomeado: Label -> ID")
        existing["ID"] = existing.pop("Label")

    # Sobras do template de tabela nova.
    for lixo in ("Number", "Status"):
        if lixo in existing:
            tb.delete(f"/api/table/{TABLE_CRIATIVOS}/field/{existing[lixo]['id']}")
            log(f"removido campo padrao: {lixo}")
            existing.pop(lixo)

    for name, ftype, options in FIELDS:
        if name in existing:
            log(f"ja existe: {name}")
            continue
        body = {"type": ftype, "name": name}
        if options:
            body["options"] = options
        f = tb.post(f"/api/table/{TABLE_CRIATIVOS}/field", body)
        if not f.get("id"):
            log(f"FALHOU {name}: {f}")
            continue
        log(f"criado: {name} ({ftype})")

    total = tb.fields(TABLE_CRIATIVOS)
    log(f"schema pronto: {len(total)} campos")


if __name__ == "__main__":
    main()
