#!/usr/bin/env python3
"""Escreve MUITAS linhas numa aba do Google Sheets, direto pela API.

Por que existe: o MCP gdrive-custom recebe as linhas dentro do payload da tool —
com milhares de linhas isso estoura o contexto do agente. Este script reusa o
mesmo token OAuth do MCP e envia tudo numa chamada da API.

Uso:
    uv run --directory /Volumes/KINGSTON/claude/tools/mcps python \
        /Volumes/KINGSTON/claude/tools/planejador-google-ads/scripts/sheets_bulk.py \
        <spreadsheet_id> <titulo_da_aba> <arquivo.json> [--index N] [--congelar]

O arquivo.json é uma lista de listas (primeira linha = cabeçalho).
Cria a aba se não existir; se existir, limpa e reescreve.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = Path("/Volumes/KINGSTON/claude/tools/mcps/servers/gdrive/token.json")
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def servico():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def escrever(sid: str, aba: str, linhas: list, index: int | None = None,
             congelar: bool = True) -> None:
    svc = servico()
    meta = svc.spreadsheets().get(spreadsheetId=sid).execute()
    existentes = {s["properties"]["title"]: s["properties"]["sheetId"]
                  for s in meta["sheets"]}

    if aba in existentes:
        sheet_id = existentes[aba]
        svc.spreadsheets().values().clear(
            spreadsheetId=sid, range=f"'{aba}'!A:Z", body={}).execute()
    else:
        req = {"addSheet": {"properties": {
            "title": aba,
            "gridProperties": {"rowCount": len(linhas) + 10,
                               "columnCount": len(linhas[0]) + 2},
        }}}
        if index is not None:
            req["addSheet"]["properties"]["index"] = index
        resp = svc.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": [req]}).execute()
        sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]

    svc.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f"'{aba}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": linhas},
    ).execute()

    if congelar:
        n_col = len(linhas[0])
        svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
            {"updateSheetProperties": {
                "properties": {"sheetId": sheet_id,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount"}},
            {"repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": {"red": 0.16, "green": 0.24, "blue": 0.35},
                    "textFormat": {"bold": True,
                                   "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    "horizontalAlignment": "CENTER", "wrapStrategy": "WRAP"}},
                "fields": "userEnteredFormat"}},
            {"setBasicFilter": {"filter": {"range": {
                "sheetId": sheet_id, "startRowIndex": 0,
                "endRowIndex": len(linhas), "startColumnIndex": 0,
                "endColumnIndex": n_col}}}},
            {"updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                          "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 320}, "fields": "pixelSize"}},
        ]}).execute()

    print(f"[OK] '{aba}': {len(linhas) - 1} linhas de dados (sheetId {sheet_id})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        sys.exit(__doc__)
    idx = None
    if "--index" in sys.argv:
        idx = int(sys.argv[sys.argv.index("--index") + 1])
    escrever(args[0], args[1], json.loads(Path(args[2]).read_text()), index=idx)
