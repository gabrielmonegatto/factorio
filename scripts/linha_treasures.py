#!/usr/bin/env python3
"""
linha_treasures.py — a LINHA DE PRODUÇÃO dos canais Treasures, com vitrine no Notion.

## Por que existe (pedido do Gabriel, 05/09/2026)

"A publicação do canal é apenas uma etapa: todos os Treasures, ao cair na linha
no Notion, já são construídos de ponta a ponta, e uma ou outra tarefa que são
gates meus eu reviso, marco OK lá e o fluxo segue."

Ou seja: 1 linha do banco `Canais` = 1 canal atravessando 13 estações. A
máquina mede o estado REAL (D1, R2, canais.py, .env, cron) e escreve no Notion
em que estação o canal está e o que falta. O Gabriel só toca em 5 checkboxes
(os gates dele). Nada de status digitado à mão: o Notion é vitrine, o estado
mora na máquina (regra-mãe do doc 24).

## As estações (a primeira NÃO satisfeita é a `Etapa` do canal)

  00 backlog        Estado=backlog. Gabriel muda pra "esteira" = puxou pra linha
  01 fonte          obras do autor registradas no D1 de mineração (berçário)
  02 mineração      >= 30 capítulos minerados no D1
  03 config+voz     slug existe no canais.py
  04 CTAs           introfixed/finalfixed no R2 (com a pausa de 1,7s)
  05 narração       cron de pré-estreia instalado e >= 15 narrados
  06 busto          >= 1 busto pintado no R2  +  [Gabriel] "Busto aprovado"
  07 canal YouTube  [Gabriel] "Canal YouTube criado" + "Verificado por telefone"
  08 OAuth          YT_<SLUG>_REFRESH_TOKEN no .env + youtube_channel_id no canais.py
  09 loja           [Gabriel] "Coleção na loja"
  10 estoque        >= 15 renderizados no R2
  11 estreia        [Gabriel] "Estrear autorizado" -> máquina liga a esteira
  12 no ar          >= 1 vídeo agendado/publicado

Estações 06/07/09 andam EM PARALELO com a narração: o `Bloqueio` lista todos
os gates abertos, não só o da etapa atual, pra o Gabriel adiantar o que puder.

## O que a máquina FAZ sozinha (--avancar, roda na VPS por cron)

  - mede e espelha (Etapa, Bloqueio, contadores) em toda linha Treasures;
  - estação 06 sem busto: abre Task pro Claude gerar (gate: créditos Magnific);
  - estação 08 com os 2 checks do YouTube marcados: abre Task de OAuth;
  - estação 11 autorizada e com tudo pronto: `esteira_canal.sh ligar <slug>`
    (produtor + agendador) e, se "Estreia" tiver data, `estrear_canal --aplicar`;
  - estação 12: Estado vira "no ar".

O que ela NÃO faz: criar canal no YouTube, verificar telefone, aprovar busto,
criar coleção na loja, autorizar estreia. São gates permanentes do Gabriel.

## Uso

  python scripts/linha_treasures.py --semear            # cria as linhas iniciais
  python scripts/linha_treasures.py --espelhar          # mede e escreve no Notion
  python scripts/linha_treasures.py --avancar           # espelha + age nos gates liberados
  python scripts/linha_treasures.py --puxar             # (Windows) berçário pros recém-puxados
  (--dry-run em qualquer um: só imprime)

Esquema do banco Canais que este script pressupõe (criado em 05/09 via MCP):
  Etapa (select 00..12) · Bloqueio · Pregador · Fonte · Voz · Capítulos ·
  Narrados · Renderizados · Agendados · Link · Estreia (date) · 5 checkboxes:
  Busto aprovado · Canal YouTube criado · Verificado por telefone ·
  Coleção na loja · Estrear autorizado
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(RAIZ, "remotion"))
import canais  # noqa: E402
import narrar_sermao as N  # noqa: E402

NOTION = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"
DS_CANAIS = "3d0f06f1-0ce3-813d-943b-000bd7806de0"
DS_TASKS = "3a7f06f1-0ce3-817d-a2fa-000bd4381682"
UNIDADE_MANANCIALL = None   # relação opcional; preenchida se existir no .env

MIN_CAPITULOS = 30
MIN_NARRADOS = 15
MIN_RENDERS = 15
NA_VPS = os.path.exists("/etc/cron.d") and os.path.exists("/app/_factorio")

ESTACOES = ["00 backlog", "01 fonte", "02 mineração", "03 config+voz", "04 CTAs",
            "05 narração", "06 busto", "07 canal YouTube", "08 OAuth", "09 loja",
            "10 estoque", "11 estreia", "12 no ar"]

# Linhas iniciais: o que já existe na máquina + o resto da Lista Final 1.0.
SEMENTES = [
    # slug, nome, pregador, fonte, estado
    ("spurgeon", "Charles Spurgeon Treasures", "Charles Spurgeon", "ccel:spurgeon", "no ar"),
    ("moody", "D.L. Moody Treasures", "D.L. Moody", "gutenberg", "no ar"),
    ("maclaren", "Alexander Maclaren Treasures", "Alexander Maclaren", "ccel:maclaren", "esteira"),
    ("murray", "Andrew Murray Treasures", "Andrew Murray", "ccel:murray", "esteira"),
    ("henry", "Matthew Henry Treasures", "Matthew Henry", "ccel:henry", "esteira"),
    ("wesley", "John Wesley Treasures", "John Wesley", "ccel:wesley", "esteira"),
    ("ryle", "J.C. Ryle Treasures", "J.C. Ryle", "ccel:ryle", "esteira"),
    ("whyte", "Alexander Whyte Treasures", "Alexander Whyte", "ccel:whyte", "esteira"),
    ("meyer", "F.B. Meyer Treasures", "F.B. Meyer", "ccel:meyer", "esteira"),
    ("parker", "Joseph Parker Treasures", "Joseph Parker", "archive", "backlog"),
    ("chrysostom", "John Chrysostom Treasures", "John Chrysostom", "ccel:chrysostom", "backlog"),
    ("talmage", "T. De Witt Talmage Treasures", "T. De Witt Talmage", "archive", "backlog"),
]


# ── Notion (urllib puro, sem dependência) ──────────────────────────────────
def notion(env, path, method="GET", body=None):
    req = urllib.request.Request(f"{NOTION}/{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", f"Bearer {env['NOTION_TOKEN']}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"❌ Notion {method} {path}: {e.code} {e.read()[:400]!r}")


def texto(prop):
    return "".join(x.get("plain_text", "") for x in (prop.get("rich_text") or prop.get("title") or []))


def linhas_treasures(env):
    """Todas as linhas do banco Canais com Arquétipo=Treasures, indexadas por slug."""
    out, cursor = {}, None
    while True:
        body = {"filter": {"property": "Arquétipo", "select": {"equals": "Treasures"}},
                "page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = notion(env, f"data_sources/{DS_CANAIS}/query", "POST", body)
        for p in r["results"]:
            pr = p["properties"]
            slug = texto(pr.get("Slug", {})).strip()
            out[slug or p["id"]] = {
                "id": p["id"], "slug": slug,
                "canal": texto(pr.get("Canal", {})),
                "pregador": texto(pr.get("Pregador", {})),
                "fonte": texto(pr.get("Fonte", {})),
                "estado": (pr.get("Estado", {}).get("select") or {}).get("name"),
                "etapa": (pr.get("Etapa", {}).get("select") or {}).get("name"),
                "estreia": (pr.get("Estreia", {}).get("date") or {}).get("start"),
                "ok": {k: bool(pr.get(k, {}).get("checkbox")) for k in
                       ("Busto aprovado", "Canal YouTube criado", "Verificado por telefone",
                        "Coleção na loja", "Estrear autorizado")},
            }
        if not r.get("has_more"):
            break
        cursor = r.get("next_cursor")
    return out


def props(**kw):
    """Atalho: dict Python -> propriedades Notion (por tipo do valor/nome)."""
    p = {}
    for k, v in kw.items():
        if v is None:
            continue
        if k == "Canal":
            p[k] = {"title": [{"text": {"content": v}}]}
        elif k in ("Etapa", "Estado", "Arquétipo", "Plataforma", "Cadência"):
            p[k] = {"select": {"name": v}}
        elif k == "Link":
            p[k] = {"url": v}
        elif k in ("Atualizado em",):
            p[k] = {"date": {"start": v}}
        elif isinstance(v, bool):
            p[k] = {"checkbox": v}
        elif isinstance(v, (int, float)):
            p[k] = {"number": v}
        else:
            p[k] = {"rich_text": [{"text": {"content": str(v)[:1900]}}]}
    return p


# ── Medição do estado REAL ─────────────────────────────────────────────────
def medir(env, s3, slug, pregador):
    f = {"config": slug in canais.CANAIS, "works": 0, "capitulos": 0, "narrados": 0,
         "ctas": False, "bustos": 0, "renders": 0, "agendados": 0, "start": None,
         "creds": False, "channel_id": "", "cron": None, "voz": "", "cadencia": None,
         "link": None, "assets": False, "produtor": False}
    try:
        f["works"] = N.d1(env, "SELECT count(*) n FROM works WHERE author=?", [pregador])[0]["n"]
    except Exception:
        pass
    if not f["config"]:
        return f
    c = canais.get(slug)
    f["voz"], f["cadencia"] = c.get("voz", ""), c.get("videos_por_dia")
    f["channel_id"] = c.get("youtube_channel_id") or ""
    f["link"] = c.get("link_canal") or (f"https://www.youtube.com/channel/{f['channel_id']}"
                                        if f["channel_id"] else None)
    f["creds"] = bool(env.get(f"{c['env_prefix']}_REFRESH_TOKEN"))
    f["assets"] = bool(c.get("assets"))       # render precisa do bloco fundo/busto
    for r in N.d1(env, "SELECT status, count(*) n FROM sermons WHERE canal=? GROUP BY status", [slug]):
        if r["status"] != "descartado":
            f["capitulos"] += r["n"]
        if r["status"] not in ("fila", "longo", "descartado"):
            f["narrados"] += r["n"]
    ass = s3.list_objects_v2(Bucket=c["bucket"], Prefix=c["prefix"] + "/_assets/", MaxKeys=500)
    nomes = [o["Key"].split("_assets/", 1)[1] for o in ass.get("Contents", [])]
    f["ctas"] = "introfixed.mp3" in nomes and "finalfixed.mp3" in nomes
    f["bustos"] = sum(1 for n in nomes if re.match(rf"avatars/{slug}_bust_cf_\d+\.png$", n))
    pag = s3.get_paginator("list_objects_v2")
    f["renders"] = sum(1 for pg in pag.paginate(Bucket=c["bucket"], Prefix=c["renders_prefix"] + "/")
                       for o in pg.get("Contents", []) if o["Key"].endswith(".mp4"))
    try:
        est = json.loads(s3.get_object(Bucket=c["bucket"], Key=c["state_key"])["Body"].read())
        f["agendados"], f["start"] = len(est.get("scheduled", {})), est.get("channel_start")
    except Exception:
        pass
    if NA_VPS:
        if os.path.exists(f"/etc/cron.d/factory-{slug}"):
            f["cron"] = "ligado"
        elif os.path.exists(f"/etc/cron.d/factory-{slug}-preestreia"):
            f["cron"] = "preestreia"
        r = subprocess.run(["systemctl", "is-active", f"factory-producer@{slug}"],
                           capture_output=True, text=True)
        f["produtor"] = r.stdout.strip() == "active"
    return f


def classificar(linha, f):
    """Devolve (etapa, bloqueios). A etapa é a primeira estação não satisfeita;
    os bloqueios são TODOS os itens abertos, com dono, pra o Gabriel adiantar."""
    ok = linha["ok"]
    if f["agendados"] >= 1:          # a realidade vence checkbox: canal publicando está no ar
        return "12 no ar", []
    if linha["estado"] == "backlog":
        return "00 backlog", ["🧑 Gabriel: mudar Estado pra 'esteira' quando quiser puxar pra linha"]
    checks = [
        ("01 fonte", f["works"] >= 1, "🤖 berçário: registrar obras (novo_canal --etapas descobrir,registrar)"),
        ("02 mineração", f["capitulos"] >= MIN_CAPITULOS, f"🤖 minerar ({f['capitulos']}/{MIN_CAPITULOS} capítulos)"),
        ("03 config+voz", f["config"], "🤖 berçário: gerar config no canais.py"),
        ("04 CTAs", f["ctas"], "🤖 berçário: gravar CTAs"),
        ("05 narração", f["cron"] in ("preestreia", "ligado") and f["narrados"] >= MIN_NARRADOS,
         f"🤖 narrando ({f['narrados']}/{MIN_NARRADOS} pra estreia; cron={f['cron'] or 'ausente'})"),
        ("06 busto", f["bustos"] >= 1 and ok["Busto aprovado"] and f["assets"],
         ("💬 sessão: gerar busto pintado (Magnific)" if f["bustos"] == 0
          else f"🧑 Gabriel: aprovar busto ({f['bustos']} no R2) e marcar 'Busto aprovado'"
          if not ok["Busto aprovado"]
          else "💬 sessão: busto aprovado; configurar bloco `assets` no canais.py")),
        ("07 canal YouTube", ok["Canal YouTube criado"] and ok["Verificado por telefone"],
         "🧑 Gabriel: criar canal no YouTube + verificar por telefone (marcar os 2 checks)"),
        ("08 OAuth", f["creds"] and bool(f["channel_id"]),
         "💬 sessão+Gabriel: auth_youtube.py -> .env + youtube_channel_id no canais.py"),
        ("09 loja", ok["Coleção na loja"], "🧑 Gabriel: coleção 'The Best of' na livraria (marcar check)"),
        ("10 estoque", f["renders"] >= MIN_RENDERS,
         (f"🤖 renderizando ({f['renders']}/{MIN_RENDERS}, produtor ligado)" if f["produtor"]
          else "🤖 render aguarda o busto aprovado (a máquina liga o produtor sozinha)")),
        ("11 estreia", ok["Estrear autorizado"] and f["cron"] == "ligado" and bool(f["start"]),
         "🧑 Gabriel: marcar 'Estrear autorizado' (e opcionalmente a data em 'Estreia')"),
        ("12 no ar", f["agendados"] >= 1, "🤖 agendador publica no próximo ciclo"),
    ]
    etapa, bloqueios = None, []
    for nome, feito, msg in checks:
        if not feito:
            etapa = etapa or nome
            bloqueios.append(msg)
    return etapa or "12 no ar", bloqueios


# ── Ações da máquina ───────────────────────────────────────────────────────
def task_existe(env, chave):
    r = notion(env, f"data_sources/{DS_TASKS}/query", "POST", {
        "filter": {"and": [{"property": "Demanda", "title": {"contains": chave}},
                           {"property": "Status", "select": {"does_not_equal": "Finalizado"}}]},
        "page_size": 1})
    return bool(r["results"])


def abrir_task(env, demanda, prompt, responsaveis, gate, dry):
    if task_existe(env, demanda):
        return "já existe"
    if dry:
        return "criaria"
    notion(env, "pages", "POST", {
        "parent": {"type": "data_source_id", "data_source_id": DS_TASKS},
        "properties": {
            "Demanda": {"title": [{"text": {"content": demanda}}]},
            "Status": {"select": {"name": "Iniciar"}},
            "Gate": {"select": {"name": gate}},
            "Responsável": {"multi_select": [{"name": r} for r in responsaveis]},
            "Prompt": {"rich_text": [{"text": {"content": prompt[:1900]}}]},
        }})
    return "aberta"


def agir(env, linha, f, etapa, dry):
    """Só o que é seguro e liberado. Devolve lista de notas do que fez."""
    slug, notas = linha["slug"], []
    if f["config"] and f["bustos"] == 0:
        notas.append("task busto: " + abrir_task(
            env, f"Linha Treasures · busto de {linha['pregador']} ({slug})",
            f"Gerar o busto PINTADO de {linha['pregador']} no padrão Treasures: "
            f"scripts/gerar_busto_magnific.py --canal {slug} --mestre (aprovação do Gabriel no mestre), "
            f"depois poses + derivar_bustos.py. Gate: créditos Magnific (>2k precisa aprovação). "
            f"Resultado esperado: _assets/avatars/{slug}_bust_cf_N.png no R2. Ver docs/21.",
            ["Claude"], "aprovação", dry))
    if f["config"] and linha["ok"]["Canal YouTube criado"] and linha["ok"]["Verificado por telefone"] \
            and not (f["creds"] and f["channel_id"]):
        notas.append("task oauth: " + abrir_task(
            env, f"Linha Treasures · OAuth do canal {slug}",
            f"Com o Gabriel logado no canal '{linha['canal']}': python remotion/auth_youtube.py "
            f"--canal {slug} -> gravar {canais.get(slug)['env_prefix']}_* no .env (Windows E VPS, "
            f"gate de credencial) e preencher youtube_channel_id no canais.py + scp pra VPS.",
            ["Monegatto", "Claude"], "aprovação", dry))
    busto_ok = f["bustos"] >= 1 and linha["ok"]["Busto aprovado"] and f["assets"]
    if NA_VPS and busto_ok and f["narrados"] >= MIN_NARRADOS and not f["produtor"] \
            and f["cron"] != "ligado":
        # O produtor não precisa de YouTube: renderiza o estoque enquanto o Gabriel
        # cuida de canal/OAuth/loja. É a mesma unidade systemd do esteira_canal.sh.
        cmd = ["systemctl", "enable", "--now", f"factory-producer@{slug}"]
        if dry:
            notas.append("ligaria produtor: " + " ".join(cmd))
        else:
            r = subprocess.run(cmd, capture_output=True, text=True)
            notas.append("produtor ligado" if r.returncode == 0 else f"produtor falhou: {r.stderr[-200:]}")
    if etapa == "11 estreia" and linha["ok"]["Estrear autorizado"] and NA_VPS \
            and f["creds"] and f["channel_id"] and f["renders"] >= MIN_RENDERS:
        if f["cron"] != "ligado":
            cmd = ["bash", os.path.join(RAIZ, "scripts", "esteira_canal.sh"), "ligar", slug]
            if dry:
                notas.append("ligaria: " + " ".join(cmd))
            else:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                notas.append("esteira ligada" if r.returncode == 0 else f"ligar falhou: {r.stderr[-200:]}")
        elif linha["estreia"] and f["start"] and linha["estreia"] != f["start"]:
            cmd = ["python3", os.path.join(RAIZ, "remotion", "estrear_canal.py"), "--canal", slug,
                   "--data", linha["estreia"], "--aplicar"]
            if dry:
                notas.append("estrearia: " + " ".join(cmd))
            else:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=os.path.join(RAIZ, "remotion"))
                notas.append(f"estreia movida pra {linha['estreia']}" if r.returncode == 0
                             else f"estrear falhou: {r.stderr[-200:]}")
    return notas


# ── Comandos ───────────────────────────────────────────────────────────────
def semear(env, dry):
    existentes = linhas_treasures(env)
    for slug, nome, pregador, fonte, estado in SEMENTES:
        if slug in existentes:
            print(f"   = {slug} já existe")
            continue
        cad = canais.get(slug).get("videos_por_dia") if slug in canais.CANAIS else None
        cadencia = {2.0: "2/dia", 1.0: "1/dia", 0.5: "0.5/dia"}.get(cad, "sem cadência")
        p = props(Canal=nome, Slug=slug, Pregador=pregador, Fonte=fonte, Estado=estado,
                  Cadência=cadencia, **{"Arquétipo": "Treasures", "Plataforma": "YouTube"})
        if dry:
            print(f"   + criaria {slug} ({estado})")
            continue
        notion(env, "pages", "POST", {"parent": {"type": "data_source_id", "data_source_id": DS_CANAIS},
                                     "properties": p})
        print(f"   + {slug} criado ({estado})")


def espelhar(env, s3, agir_tb, dry):
    linhas = linhas_treasures(env)
    hoje = dt.date.today().isoformat()
    for slug, linha in sorted(linhas.items()):
        if not linha["slug"]:
            print(f"⚠️  linha sem Slug: {linha['canal']!r} (preencher no Notion)")
            continue
        f = medir(env, s3, slug, linha["pregador"] or slug)
        etapa, bloqueios = classificar(linha, f)
        notas = agir(env, linha, f, etapa, dry) if agir_tb else []
        estado = "no ar" if etapa == "12 no ar" else linha["estado"]
        bloqueio = "\n".join(bloqueios[:6]) or "✅ nada pendente"
        if notas:
            bloqueio += "\n🤖 " + " · ".join(notas)
        print(f"📺 {slug:10} {etapa:16} cap={f['capitulos']:5} nar={f['narrados']:4} "
              f"rend={f['renders']:4} ag={f['agendados']:3} busto={f['bustos']} "
              f"cron={f['cron'] or '-':10} creds={'S' if f['creds'] else 'N'}")
        for b in bloqueios[:6]:
            print(f"      {b}")
        for n in notas:
            print(f"      🤖 {n}")
        if dry:
            continue
        notion(env, f"pages/{linha['id']}", "PATCH", {"properties": props(
            Etapa=etapa, Bloqueio=bloqueio, Estado=estado, Voz=f["voz"] or None,
            **{"Capítulos": f["capitulos"], "Narrados": f["narrados"],
               "Renderizados": f["renders"], "Agendados": f["agendados"],
               "Link": f["link"], "Atualizado em": hoje})})


def puxar(env, dry):
    """(Windows) Linhas puxadas pra 'esteira' que ainda não existem na máquina:
    roda o berçário. Só fonte CCEL por enquanto (archive = adaptador pendente)."""
    for slug, linha in linhas_treasures(env).items():
        if linha["estado"] != "esteira" or slug in canais.CANAIS or not linha["slug"]:
            continue
        m = re.match(r"ccel:(\S+)", linha["fonte"] or "")
        if not m:
            print(f"⏸️  {slug}: fonte {linha['fonte']!r} sem adaptador automático (só ccel:<autor>)")
            continue
        cmd = [sys.executable, os.path.join(HERE, "novo_canal.py"), "--slug", slug,
               "--pregador", linha["pregador"], "--ccel", m.group(1), "--cadencia", "0.5"]
        print(("rodaria: " if dry else "🍼 berçário: ") + " ".join(cmd))
        if not dry:
            subprocess.run(cmd, cwd=RAIZ, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semear", action="store_true")
    ap.add_argument("--espelhar", action="store_true")
    ap.add_argument("--avancar", action="store_true", help="espelhar + agir nos gates liberados")
    ap.add_argument("--puxar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = N.load_env()
    if not env.get("NOTION_TOKEN"):
        sys.exit("❌ NOTION_TOKEN ausente no .env")
    if a.semear:
        semear(env, a.dry_run)
    if a.puxar:
        puxar(env, a.dry_run)
    if a.espelhar or a.avancar:
        espelhar(env, N.s3c(env), agir_tb=a.avancar, dry=a.dry_run)
    if not any((a.semear, a.espelhar, a.avancar, a.puxar)):
        ap.print_help()


if __name__ == "__main__":
    main()
