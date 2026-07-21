"""Cliente minimo da API do Teable (db.markeologia.com.br).

A regra da casa (docs/STACK.md) e falar pela API REST, nunca por SQL bruto
no Postgres do container -- a API garante integridade e versionamento da UI.
"""
from __future__ import annotations

import mimetypes
import pathlib
import sys
import time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "meta"))
from _common import env, log  # noqa: E402

# O registro do Windows nao conhece webp/avif; sem isso o guess_type devolve
# None, o arquivo sobe como text/plain e a galeria do Teable nao renderiza.
for _ext, _mime in ((".webp", "image/webp"), (".avif", "image/avif"), (".mp4", "video/mp4")):
    mimetypes.add_type(_mime, _ext)

BASE_BR4NDS = "bseyIWRa5nyTWMlNBpi"
TABLE_CRIATIVOS = "tblQeaMuTZTD5Dzlqq3"   # br4nds_criativos
TABLE_PLAYERS = "tblu6LzuO20JpokBL8P"     # players_criativos (concorrentes)


class Teable:
    def __init__(self) -> None:
        self.url = env("TEABLE_URL").rstrip("/")
        self.s = requests.Session()
        self.s.headers.update({"Authorization": "Bearer " + env("TEABLE_TOKEN")})

    def _call(self, method: str, path: str, **kw):
        url = self.url + path
        for attempt in range(4):
            try:
                r = self.s.request(method, url, timeout=180, **kw)
            except requests.RequestException as e:
                if attempt == 3:
                    raise
                log(f"  rede instavel ({type(e).__name__}), retry")
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            if not r.ok:
                raise RuntimeError(f"Teable {method} {path} -> {r.status_code}: {r.text[:300]}")
            return r.json() if r.text else {}
        raise RuntimeError("Teable: estourou as tentativas")

    def get(self, path: str, **params):
        return self._call("GET", path, params=params or None)

    def post(self, path: str, body: dict):
        return self._call("POST", path, json=body)

    def patch(self, path: str, body: dict):
        return self._call("PATCH", path, json=body)

    def delete(self, path: str):
        return self._call("DELETE", path)

    # ------------------------------------------------------------ helpers

    def fields(self, table: str) -> list[dict]:
        return self.get(f"/api/table/{table}/field")

    def all_records(self, table: str, page: int = 1000) -> list[dict]:
        out, skip = [], 0
        while True:
            r = self.get(f"/api/table/{table}/record",
                         take=page, skip=skip, fieldKeyType="name")
            recs = r.get("records", [])
            out.extend(recs)
            if len(recs) < page:
                return out
            skip += page

    def create_records(self, table: str, rows: list[dict], chunk: int = 500) -> list[dict]:
        """rows = [{campo: valor}, ...]. Devolve os registros criados."""
        made = []
        for i in range(0, len(rows), chunk):
            part = rows[i:i + chunk]
            r = self.post(f"/api/table/{table}/record", {
                "fieldKeyType": "name",
                "typecast": True,
                "records": [{"fields": f} for f in part],
            })
            made.extend(r.get("records", []))
            log(f"  criados {len(made)}/{len(rows)}")
        return made

    def update_record(self, table: str, record_id: str, fields: dict):
        return self.patch(f"/api/table/{table}/record/{record_id}", {
            "fieldKeyType": "name", "typecast": True, "record": {"fields": fields},
        })

    def upload_attachment(self, table: str, record_id: str, field_id: str, path: pathlib.Path):
        """Sobe um arquivo local para um campo attachment.

        O content-type vai explicito: sem ele o Teable grava como text/plain
        e a galeria nao renderiza a imagem."""
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with open(path, "rb") as fh:
            return self._call(
                "POST",
                f"/api/table/{table}/record/{record_id}/{field_id}/uploadAttachment",
                files={"file": (path.name, fh, mime)},
            )
