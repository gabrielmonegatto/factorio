#!/usr/bin/env python3
"""
notion_canal_moody.py — cria no Notion a pagina do canal D.L. MOODY TREASURES,
ja preenchida como REPLICA do Spurgeon (1a instancia real do template v4).

Replica responde 4 perguntas de estrategia e herda o resto do canal-mae.
Decisoes que ficam com o Gabriel estao marcadas [GABRIEL].

Uso: python notion_canal_moody.py
"""
import json
import os
import sys
import urllib.request

API = "https://api.notion.com/v1"
VER = "2022-06-28"
RAIZ = "33d6bf27-9f65-4043-8a5d-c53fe0b241a3"   # pagina "Business System"


def token():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    for line in open(p, encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "").strip()
        if line.startswith("NOTION_TOKEN="):
            return line.split("=", 1)[1]
    sys.exit("NOTION_TOKEN nao encontrado")


TOK = token()


def call(metodo, caminho, corpo=None):
    req = urllib.request.Request(
        API + caminho,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        method=metodo,
        headers={"Authorization": "Bearer " + TOK, "Notion-Version": VER,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit("HTTP %s em %s %s:\n%s" % (e.code, metodo, caminho, e.read().decode()[:600]))


def rt(t):
    return [{"type": "text", "text": {"content": t}}]


def h2(t):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": rt(t)}}


def h3(t):
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": rt(t)}}


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def para(t):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt(t)}}


def bullet(t):
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rt(t)}}


def todo(t):
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": rt(t), "checked": False}}


def callout(t, emoji, cor):
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": rt(t), "icon": {"emoji": emoji}, "color": cor}}


CORPO = [
    callout("REPLICA do Charles Spurgeon Treasures - 1a instancia do template de "
            "lancamento. Estrategia herdada do canal-mae; aqui so o que muda. "
            "Decisoes pendentes marcadas [GABRIEL].", "\U0001F501", "green_background"),
    para(""),

    h2("Cabecalho"),
    divider(),
    bullet("Nome proposto: D.L. Moody Treasures  [GABRIEL bate o martelo]"),
    bullet("Slug na esteira: moody"),
    bullet("Idioma: ingles"),
    bullet("Arquetipo: REPLICA (canal-mae: Charles Spurgeon Treasures)"),
    bullet("Fonte: 15 obras de D.L. Moody no Project Gutenberg (verificado 19/08/2026)"),
    para(""),

    h2("ETAPA 1 - Estrategia (so o que difere do canal-mae)"),
    divider(),

    h3("1.1 O que se HERDA do Spurgeon (sem rediscutir)"),
    bullet("Formato: sermao narrado ~30min, visual proprio, legenda queimada"),
    bullet("Calendario: 1 video/dia as 12:00 UTC, agendador com buffer de 14 dias"),
    bullet("Packaging: titulo de dor + sufixo com o nome do pregador; thumb com retrato"),
    bullet("Funil: QR + link na descricao -> mananciall.org/go com v= proprio do canal"),
    bullet("Esteira inteira: mineracao -> narracao -> render -> agendamento -> vigia"),

    h3("1.2 Materia-prima (verificada, nao estimada no chute)"),
    bullet("15 obras EN no Project Gutenberg. Coletaneas de sermoes: The Overcoming "
           "Life, Wondrous Love, Weighed and Wanting (10 mandamentos), Men of the "
           "Bible, The Way to God, Secret Power, Prevailing Prayer, Sowing and "
           "Reaping, To the Work, Sovereign Grace, Pleasure & Profit in Bible Study"),
    bullet("2 volumes de anedotas (Moody's Anecdotes, Moody's Stories): materia-prima "
           "de HOOKS e shorts, nao de video longo"),
    bullet("Estimativa honesta: 90 a 120 sermoes/capitulos mineraveis"),
    bullet("Acervo FINITO: sustenta 3 a 4 meses a 1/dia. Extensao futura: sermoes "
           "avulsos digitalizados no archive.org (nao contado ainda)"),
    callout("Prosa do Moody: simples, direta, cheia de historia. E a mais facil de "
            "modelar de toda a Onda 1 - por isso ele e o primeiro replicado.",
            "\U0001F4D6", "gray_background"),

    h3("1.3 Formato e frequencia"),
    bullet("Herda 30min/1 por dia. Sermao do Moody e mais curto que o do Spurgeon: "
           "videos devem ficar em 20-30min (ok, mesmo formato)"),
    bullet("Capitulos de livro tematico (ex.: 10 mandamentos) viram SERIE - "
           "playlist propria, titulos numerados"),

    h3("1.4 Ofertas atreladas"),
    bullet("Mesma mecanica do Spurgeon: QR + link -> /go?v= proprio"),
    bullet("[GABRIEL] Destino: hoje nao existe 'The Best of D.L. Moody' na livraria "
           "Mananciall. Criar a coletanea, ou apontar pro catalogo geral ate existir"),

    h3("1.9 Criterios de vida ou morte (de replica, nao de canal novo)"),
    bullet("Checkpoint: video 30 (ou 90 dias, o que vier primeiro)"),
    bullet("Referencia = a curva do IRMAO: comparar views/CTR/retencao com o Spurgeon "
           "no MESMO ponto da vida dele (video 30), nao com numero absoluto"),
    bullet("Seguir: curva >= 70% da curva do Spurgeon no mesmo ponto"),
    bullet("Investigar packaging: curva < 50% da do irmao com a mesma esteira"),
    bullet("Matar/pivotar: so com dado das 4 saidas (escalar/perseverar/pivotar/matar)"),
    para(""),

    h2("ETAPA 2 - Identidade (propostas pra aprovacao)"),
    divider(),
    bullet("Promessa: as pregacoes do maior evangelista americano do sec. XIX, "
           "narradas com clareza pra ouvir hoje"),
    bullet("Tom: caloroso, direto, evangelistico. Moody era storyteller de povo - "
           "contrasta de proposito com a solenidade do Spurgeon"),
    bullet("[GABRIEL] Voz: AMERICANA (Moody e de Chicago; Spurgeon britanico ja usa "
           "bm_george; am_michael esta reservado pra Biblia KJV). A/B proposto: "
           "am_onyx vs am_fenrir com trecho real do Moody - escolher no OUVIDO"),
    bullet("Visual: mesma familia Treasures (retrato do pregador + fundo de epoca), "
           "paleta propria mais quente (ambar) pra diferenciar do Spurgeon. Fotos "
           "do Moody sao sec. XIX = dominio publico"),
    bullet("Nunca faz (herdado): nunca revelar a fonte na descricao; nunca titulo "
           "caca-clique que o sermao nao entrega; nunca trilha sem procedencia"),
    para(""),

    h2("ETAPA 3 - Producao (os 9 entregaveis)"),
    divider(),
]

ENTREGAVEIS = [
    ("1. Licenca provada", "Claude",
     "IDs do Gutenberg + morte do autor (1899) arquivados junto do corpus",
     ["Arquivar lista das 15 obras com ids e links do Gutenberg",
      "Registrar: autor morto em 1899, obras pre-1930, dominio publico nos EUA"]),
    ("2. Identidade visual pronta", "Gabriel",
     "Avatar, banner e template de video no R2, aprovados no olho",
     ["Bater o martelo no nome [GABRIEL]",
      "Escolher retrato de epoca do Moody (PD) e criar avatar/banner",
      "Adaptar o template visual do Spurgeon com a paleta nova",
      "Subir pro R2 em channels/channels_youtube/treasures_dlmoody/_assets/"]),
    ("3. Canal criado e credencial funcionando", "Gabriel",
     "channels?mine=true retorna o canal do Moody, ID confere com canais.py",
     ["Criar o canal de marca no YouTube",
      "Projeto GCP proprio + YouTube Data API v3",
      "Publishing status: Testing -> In production ANTES de autenticar",
      "auth_youtube.py escolhendo o canal do MOODY na tela",
      "Credenciais como YT_MOODY_* nos DOIS .env da VPS",
      "Confirmar por API o canal autenticado"]),
    ("4. Canal ligado na esteira", "Claude",
     "--canal moody --dry-run correto; guardiao barra enquanto faltar config",
     ["Entrada 'moody' em canais.py (prefix treasures_dlmoody, env YT_MOODY)",
      "Generalizar o SYSTEM do generate_marketing.py (hoje hardcoded no Spurgeon)",
      "Preencher youtube_channel_id quando o canal existir"]),
    ("5. Voz travada", "Gabriel",
     "A/B ouvido e aprovado; voz + velocidade fixadas em canais.py",
     ["Gerar A/B: am_onyx vs am_fenrir com trecho real do Moody",
      "Gabriel escolhe no ouvido",
      "Travar em canais.py e nunca mais mexer"]),
    ("6. Corpus minerado e na fila", "Claude",
     "90-120 sermoes limpos no R2 com manifest, numerados",
     ["Baixar as 13 obras de sermao do Gutenberg (anedotas ficam pra shorts)",
      "Limpar boilerplate do Gutenberg e fatiar por sermao/capitulo",
      "Gerar copy de marketing por sermao (prompt do canal)",
      "Narrar, transcrever e deixar pronto pra render"]),
    ("7. Primeiro video renderizado e aprovado", "Gabriel",
     "MP4 assistido do inicio ao fim e aprovado",
     ["Renderizar 1 sermao completo",
      "Assistir inteiro e conferir audio/legenda/visual/CTA"]),
    ("8. Piloto publicado", "Gabriel",
     "1 video no ar no canal CERTO (channelId conferido); depois 3 limpos seguidos",
     ["Publicar o primeiro com gate humano",
      "Conferir channelId por API",
      "3 videos limpos seguidos = estavel"]),
    ("9. Automacao com vigia", "Claude",
     "Cron ligado E alarme testado com falha proposital",
     ["Ligar cron do agendador com --canal moody",
      "Alarme Discord: erro OU 48h sem publicar",
      "Testar o alarme forcando falha"]),
]


def main():
    print("criando a pagina do canal ...")
    pagina = call("POST", "/pages", {
        "parent": {"type": "page_id", "page_id": RAIZ},
        "icon": {"emoji": "\U0001F525"},
        "properties": {"title": {"title": rt("Canal - D.L. Moody Treasures")}},
        "children": CORPO,
    })
    pid = pagina["id"]
    print("pagina:", pagina["url"])

    db = call("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": pid},
        "is_inline": True,
        "title": rt("Entregaveis - Moody"),
        "properties": {
            "Entregavel": {"title": {}},
            "Dono": {"select": {"options": [
                {"name": "Gabriel", "color": "orange"},
                {"name": "Claude", "color": "blue"}]}},
            "Status": {"select": {"options": [
                {"name": "Nao iniciada", "color": "default"},
                {"name": "Em andamento", "color": "yellow"},
                {"name": "Concluido", "color": "green"}]}},
            "Criterio de pronto": {"rich_text": {}},
        },
    })
    for nome, dono, dod, passos in ENTREGAVEIS:
        call("POST", "/pages", {
            "parent": {"database_id": db["id"]},
            "properties": {
                "Entregavel": {"title": rt(nome)},
                "Dono": {"select": {"name": dono}},
                "Status": {"select": {"name": "Nao iniciada"}},
                "Criterio de pronto": {"rich_text": rt(dod)},
            },
            "children": [h3("Passos")] + [todo(p) for p in passos],
        })
        print("  ok:", nome)

    print("\nPRONTO:", pagina["url"])


if __name__ == "__main__":
    main()
