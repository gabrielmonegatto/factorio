#!/usr/bin/env python3
"""
notion_workflows.py — espelha no Notion a tabela de WORKFLOWS ATIVOS da fábrica.

## Por que existe

Pedido do Gabriel em 24/08: "precisa estar claro e documentado em algum lugar,
por exemplo no Notion uma tabela com os workflows ativos". O que ele quer ver de
relance é que cada canal é um fluxo ISOLADO: quebrou um, os outros seguem; e que
esse fluxo se copia, ajusta, e vira o próximo canal.

## De onde vem o dado (importa)

    docs/18_AUTOMACOES.md  →  seed-automacoes.mjs  →  D1 `automacoes`  →  aqui

Este script NÃO tem lista própria. Digitar as automações de novo aqui criaria
uma TERCEIRA cópia da mesma verdade, e cópia que ninguém sincroniza vira mentira
sozinha: foi exatamente o defeito que o seeder do BI teve (dizia que a fonte era
o doc 18 e trazia a lista colada dentro dele, então automação removida do doc
ficava viva no painel pra sempre).

Por isso este script também ARQUIVA a linha cujo slug sumiu do D1. Espelho que
só sabe adicionar não é espelho, é acúmulo.

## Uso

    python notion_workflows.py             # prévia: diz o que faria
    python notion_workflows.py --aplicar   # cria/atualiza/arquiva de verdade

Idempotente: rodar duas vezes seguidas não duplica nada.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.notion.com/v1"
VER = "2022-06-28"

# Mesma raiz que notion_canal_moody.py e notion_template_canal.py usam: a página
# "Business System". A página "🏭 Fábrica" seria o lar natural, mas não está
# compartilhada com esta integração — e escrever onde a integração não enxerga
# falha silenciosa, então fica onde o resto já mora.
RAIZ = "33d6bf27-9f65-4043-8a5d-c53fe0b241a3"
TITULO_DB = "Workflows ativos"

D1_PROD = "ddae6874-2058-4aa1-927e-0e7887e2cba6"   # mananciall-db (PROD)

HERE = os.path.dirname(os.path.abspath(__file__))


def env():
    e = {}
    p = os.path.join(HERE, "..", ".env")
    for line in open(p, encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "").strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            e.setdefault(k, v)
    return e


E = env()


def _req(url, data=None, headers=None, method="GET", tentativas=3):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                                         headers=headers or {})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "replace")[:400]
            # 429 = rate limit do Notion. Vale esperar; o resto não.
            if e.code == 429 and i < tentativas - 1:
                time.sleep(2 * (i + 1))
                continue
            raise SystemExit(f"❌ HTTP {e.code} em {url}\n   {corpo}")


def notion(metodo, caminho, corpo=None):
    tok = E.get("NOTION_TOKEN")
    if not tok:
        sys.exit("❌ falta NOTION_TOKEN no .env")
    return _req(API + caminho,
                data=json.dumps(corpo).encode() if corpo is not None else None,
                method=metodo,
                headers={"Authorization": "Bearer " + tok,
                         "Notion-Version": VER,
                         "Content-Type": "application/json"})


def d1(sql, params=None):
    acc, tok = E.get("CLOUDFLARE_ACCOUNT_ID"), E.get("CLOUDFLARE_API_TOKEN")
    if not (acc and tok):
        sys.exit("❌ faltam CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN no .env")
    r = _req(f"https://api.cloudflare.com/client/v4/accounts/{acc}"
             f"/d1/database/{D1_PROD}/query",
             data=json.dumps({"sql": sql, "params": params or []}).encode(),
             method="POST",
             headers={"Authorization": "Bearer " + tok,
                      "Content-Type": "application/json"})
    if not r.get("success"):
        sys.exit("❌ D1: " + "; ".join(e.get("message", "?") for e in r.get("errors", [])))
    return r["result"][0]["results"]


# ── esquema da tabela no Notion ────────────────────────────────────────────
# MINA da API do Notion (já documentada em notion_template_canal.py): propriedade
# do tipo `status` NÃO pode ser criada via API, só na interface. Aqui é `select`
# com as mesmas opções.
CORES = {"Viva": "green", "Armada": "yellow", "Manual": "gray", "Morta": "red"}

PROPS = {
    "Workflow":  {"title": {}},
    "Slug":      {"rich_text": {}},          # a chave do upsert
    "Projeto":   {"select": {}},
    "Status":    {"select": {"options": [{"name": k, "color": v} for k, v in CORES.items()]}},
    "Onde roda": {"select": {}},
    "Gatilho":   {"rich_text": {}},
    "Cadência":  {"rich_text": {}},
    "Etapas":    {"rich_text": {}},
    "Código":    {"rich_text": {}},
    "Log":       {"rich_text": {}},
    "Notas":     {"rich_text": {}},
}


def txt(valor, limite=1900):
    """rich_text do Notion. O campo estoura em 2000 caracteres, então corta antes."""
    s = (valor or "").strip()
    return [{"type": "text", "text": {"content": s[:limite]}}] if s else []


def resumo_etapas(bruto):
    """As etapas vêm do D1 como JSON [[nome, detalhe], ...]. Vira uma linha legível."""
    try:
        etapas = json.loads(bruto) if isinstance(bruto, str) else (bruto or [])
    except Exception:
        return str(bruto or "")
    partes = []
    for i, e in enumerate(etapas, 1):
        nome = e[0] if isinstance(e, (list, tuple)) and e else str(e)
        partes.append(f"{i}. {nome}")
    return "  ·  ".join(partes)


def achar_db():
    """Procura a tabela pelo título entre os filhos da raiz (não cria duplicata)."""
    cursor, achado = None, None
    while True:
        q = f"/blocks/{RAIZ}/children?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        r = notion("GET", q)
        for b in r.get("results", []):
            if b["type"] == "child_database":
                # No bloco child_database o `title` é STRING pura, não rich_text
                # (é rich_text quando vem de /databases/<id>). Tratar os dois.
                bruto = b["child_database"].get("title") or ""
                nome = bruto if isinstance(bruto, str) else \
                    "".join(s.get("plain_text", "") for s in bruto)
                if nome.strip() == TITULO_DB:
                    achado = b["id"]
        if not r.get("has_more"):
            return achado
        cursor = r.get("next_cursor")


def criar_db():
    r = notion("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": RAIZ},
        "is_inline": True,
        "title": [{"type": "text", "text": {"content": TITULO_DB}}],
        "description": [{"type": "text", "text": {"content":
            "Espelho do catálogo em docs/18_AUTOMACOES.md (via D1 `automacoes`). "
            "Não edite aqui: edite o doc e re-semeie, senão a edição some no "
            "próximo espelhamento."}}],
        "properties": PROPS,
    })
    return r["id"]


def linhas_existentes(db):
    """slug -> page_id, de tudo que já está na tabela."""
    mapa, cursor = {}, None
    while True:
        r = notion("POST", f"/databases/{db}/query",
                   {"page_size": 100, **({"start_cursor": cursor} if cursor else {})})
        for p in r.get("results", []):
            slug = "".join(s.get("plain_text", "")
                           for s in p["properties"].get("Slug", {}).get("rich_text", []))
            if slug:
                mapa[slug] = p["id"]
        if not r.get("has_more"):
            return mapa
        cursor = r.get("next_cursor")


def props_da_linha(a):
    return {
        "Workflow":  {"title": txt(a.get("nome") or a["id"], 200)},
        "Slug":      {"rich_text": txt(a["id"], 100)},
        "Projeto":   {"select": {"name": a["projeto"]} if a.get("projeto") else None},
        "Status":    {"select": {"name": a["status"]} if a.get("status") else None},
        "Onde roda": {"select": {"name": a["onde_roda"]} if a.get("onde_roda") else None},
        "Gatilho":   {"rich_text": txt(a.get("gatilho"))},
        "Cadência":  {"rich_text": txt(a.get("cadencia"))},
        "Etapas":    {"rich_text": txt(resumo_etapas(a.get("etapas")))},
        "Código":    {"rich_text": txt(a.get("codigo"))},
        "Log":       {"rich_text": txt(a.get("log"))},
        "Notas":     {"rich_text": txt(a.get("notas"))},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true",
                    help="sem isto, só mostra o que faria")
    args = ap.parse_args()

    autos = d1("SELECT * FROM automacoes ORDER BY COALESCE(ordem, 999), id")
    print(f"📚 fonte: D1 `automacoes` · {len(autos)} workflows")

    db = achar_db()
    if not db:
        if not args.aplicar:
            print(f"👀 criaria a tabela {TITULO_DB!r} na raiz e poria {len(autos)} linhas")
            print("   (prévia — rode com --aplicar)")
            return
        db = criar_db()
        print(f"🆕 tabela criada: {db}")
    else:
        print(f"📋 tabela existente: {db}")

    atuais = linhas_existentes(db) if args.aplicar or db else {}
    vivos = {a["id"] for a in autos}
    novos = [a for a in autos if a["id"] not in atuais]
    muda = [a for a in autos if a["id"] in atuais]
    # Ghost removal: slug que sumiu do D1 não pode continuar vivo no painel.
    fantasmas = [s for s in atuais if s not in vivos]

    print(f"   novos={len(novos)} · atualiza={len(muda)} · arquiva={len(fantasmas)}")
    for s in fantasmas:
        print(f"   👻 {s} sumiu da fonte → arquivar")

    if not args.aplicar:
        for a in novos:
            print(f"   ➕ {a['id']}")
        print("   (prévia — rode com --aplicar)")
        return

    for a in autos:
        corpo = {"properties": props_da_linha(a)}
        if a["id"] in atuais:
            notion("PATCH", f"/pages/{atuais[a['id']]}", corpo)
        else:
            corpo["parent"] = {"database_id": db}
            notion("POST", "/pages", corpo)
        print(f"   ✅ {a['id']}")
    for s in fantasmas:
        notion("PATCH", f"/pages/{atuais[s]}", {"archived": True})
        print(f"   🗑️  {s} arquivado")

    print(f"\n🏁 tabela {TITULO_DB!r} espelhada: {len(autos)} workflows")
    print(f"   https://www.notion.so/{db.replace('-', '')}")


if __name__ == "__main__":
    main()
