"""Base compartilhada dos scripts de atribuicao Meta -> criativos.

Cobre: leitura do .env (CRLF), cliente D1 via REST, cliente Graph API com
retry, e o hash perceptual (dHash) usado como ponte ad -> PNG do acervo.
"""
from __future__ import annotations

import io
import json
import os
import pathlib
import sys
import time

import requests
from PIL import Image

CF_ACCOUNT = "99d059f0a8f89aecc93f3830b69b2f6c"
D1_DATABASE = "4d71058c-9f72-4cce-869b-9513df5b5950"
GRAPH = "https://graph.facebook.com/v21.0"

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / ".cache"


def _find_env() -> pathlib.Path:
    for d in [HERE, *HERE.parents]:
        cand = d / "_factorio" / ".env"
        if cand.exists():
            return cand
    raise SystemExit("nao achei _factorio/.env subindo a partir de " + str(HERE))


def env(key: str, required: bool = True) -> str:
    """Le uma chave do _factorio/.env. O arquivo e CRLF; o \\r vai embora aqui."""
    if os.environ.get(key):
        return os.environ[key]
    for line in _find_env().read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip().lstrip("﻿")
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    if required:
        raise SystemExit(f"chave {key} ausente em _factorio/.env")
    return ""


def log(msg: str) -> None:
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


# ---------------------------------------------------------------- D1 (REST)

class D1:
    """Cliente D1 remoto. Usa a REST API direto para nao depender do wrangler
    (que localmente esta logado na conta ZOAC)."""

    def __init__(self) -> None:
        self.url = (
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}"
            f"/d1/database/{D1_DATABASE}/query"
        )
        self.h = {
            "Authorization": "Bearer " + env("BR4NDS_D1_TOKEN"),
            "Content-Type": "application/json",
        }
        self.s = requests.Session()

    def query(self, sql: str, params: list | None = None) -> list[dict]:
        body = {"sql": sql}
        if params:
            body["params"] = [_p(x) for x in params]
        for attempt in range(6):
            try:
                r = self.s.post(self.url, headers=self.h, json=body, timeout=180)
            except requests.RequestException as e:
                # o upload pro R2 satura a banda de subida e derruba conexao
                if attempt == 5:
                    raise
                log(f"  rede instavel ({type(e).__name__}), retry em {2 ** attempt}s")
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                data = r.json()
                if not data.get("success"):
                    raise RuntimeError(f"D1: {data.get('errors')}")
                out: list[dict] = []
                for blk in data.get("result", []):
                    out.extend(blk.get("results") or [])
                return out
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"D1 HTTP {r.status_code}: {r.text[:400]}")
        return []

    def upsert_many(self, sql: str, rows: list[list], chunk: int = 40) -> int:
        """Executa o mesmo statement para muitas linhas, em lotes."""
        done = 0
        for i in range(0, len(rows), chunk):
            for row in rows[i:i + chunk]:
                self.query(sql, row)
                done += 1
            log(f"  ... {done}/{len(rows)}")
        return done

    def exec_batch(self, stmts: list[str], chunk: int = 150, label: str = "") -> int:
        """Manda varios statements literais por request.

        Bem mais rapido que um round-trip por linha; use com lit() para
        escapar os valores.
        """
        done = 0
        for i in range(0, len(stmts), chunk):
            part = stmts[i:i + chunk]
            self.query(";\n".join(s.rstrip(";") for s in part) + ";")
            done += len(part)
            if len(stmts) > chunk:
                log(f"  ... {label}{done}/{len(stmts)}")
        return done


def lit(x) -> str:
    """Valor literal seguro para SQL (aspas simples dobradas)."""
    if x is None:
        return "NULL"
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, (int, float)):
        return repr(x)
    return "'" + str(x).replace("'", "''") + "'"


def _p(x):
    """D1 REST so aceita escalares; None vira NULL, bool vira int."""
    if isinstance(x, bool):
        return int(x)
    if x is None or isinstance(x, (int, float, str)):
        return x
    return json.dumps(x, ensure_ascii=False)


# ------------------------------------------------------------- Graph API

class Graph:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or env("META_ADS_TOKEN")
        self.s = requests.Session()

    # Limite de app do Meta nao passa em 20s: quando bate, precisa de
    # minutos. Espera crescente ate ~17min no total.
    BACKOFF = (30, 60, 120, 300, 600)

    def get(self, path: str, **params) -> dict:
        params["access_token"] = self.token
        url = path if path.startswith("http") else f"{GRAPH}/{path}"
        backoff = self.BACKOFF
        for attempt in range(len(backoff) + 1):
            try:
                r = self.s.get(url, params=params, timeout=180)
            except requests.RequestException as e:
                if attempt >= len(backoff):
                    raise
                log(f"  rede instavel ({type(e).__name__}), retry")
                time.sleep(backoff[attempt])
                continue
            if r.status_code == 200:
                return r.json()
            try:
                err = r.json().get("error", {})
            except Exception:
                err = {"message": r.text[:300]}
            # 4/17/613/80004 = rate limit; 1/2 = "reduza o volume pedido"
            if err.get("code") in (1, 2, 4, 17, 613, 80004) or r.status_code >= 500:
                if attempt >= len(backoff):
                    raise RuntimeError(f"Graph desistiu: {err}")
                wait = backoff[attempt]
                log(f"  erro {err.get('code')} ({err.get('message', '')[:55]}), "
                    f"aguardando {wait}s")
                time.sleep(wait)
                continue
            raise RuntimeError(f"Graph {r.status_code}: {err}")
        raise RuntimeError("Graph: estourou as tentativas")

    def paginate(self, path: str, **params):
        """Itera todas as paginas de um edge, seguindo paging.next."""
        page = self.get(path, **params)
        while True:
            for item in page.get("data", []):
                yield item
            nxt = (page.get("paging") or {}).get("next")
            if not nxt:
                return
            page = self.get(nxt)


# ------------------------------------------------------------------ dHash

def dhash(img: Image.Image, size: int = 8) -> str:
    """Hash perceptual de 64 bits (hex de 16 chars).

    Compara cada pixel com o vizinho da direita numa miniatura cinza de
    (size+1)x size. Sobrevive a recompressao/resize -- que e exatamente o
    que o Meta faz com nossos PNGs ao virar JPG no CDN deles.
    """
    g = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for row in range(size):
        base = row * (size + 1)
        for col in range(size):
            bits = (bits << 1) | (1 if px[base + col] > px[base + col + 1] else 0)
    return f"{bits:016x}"


def dhash_bytes(raw: bytes) -> str:
    with Image.open(io.BytesIO(raw)) as im:
        im.load()
        return dhash(im)


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def fetch_image(url: str, cache_key: str, session: requests.Session | None = None) -> bytes | None:
    """Baixa a imagem com cache em disco (.cache/), para reexecucao barata."""
    CACHE.mkdir(exist_ok=True)
    path = CACHE / (cache_key + ".bin")
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    s = session or requests
    for attempt in range(3):
        try:
            r = s.get(url, timeout=90)
            if r.status_code == 200 and r.content:
                path.write_bytes(r.content)
                return r.content
            if r.status_code == 404:
                return None
        except Exception as e:  # rede instavel
            if attempt == 2:
                log(f"  falha ao baixar {cache_key}: {e}")
                return None
        time.sleep(2 ** attempt)
    return None


ACCOUNTS = [
    ("act_1363438474022368", "LF 1 - Bluue", "bluue"),
    ("act_3462187117241841", "LF 8 - BLUUE New", "bluue"),
    ("act_731993897678273", "LF 10 - Bluue Test Safe", "bluue"),
    ("act_1276336571351856", "CA1 - Bluue $", "bluue"),
    ("act_2794654284238893", "CA2 - Bluue $", "bluue"),
    ("act_1261729839382630", "Tonaface", "tonaface"),
]

# Duas contas faturam em dolar. Sem isso, somar `spend` de contas diferentes
# mistura moeda e o total sai errado -- por isso a moeda vai gravada na linha,
# e a conversao fica na leitura (BI), nao na carga.
CURRENCY = {
    "act_1363438474022368": "BRL",
    "act_3462187117241841": "BRL",
    "act_731993897678273": "BRL",
    "act_1276336571351856": "USD",
    "act_2794654284238893": "USD",
    "act_1261729839382630": "USD",
}
ACCOUNT_NAME = {a[0]: a[1] for a in ACCOUNTS}
