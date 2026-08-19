#!/usr/bin/env python3
"""
notion_template_canal.py — cria no Notion o TEMPLATE de lançamento de canal novo.

## Por que a v2 (16/08/2026)

A v1 tinha 42 linhas rastreadas. Gabriel reclamou, com razão: virou inventário,
não painel. A pesquisa (Gawande, "The Checklist Manifesto") dá o número:
checklist bom tem 5 a 9 itens, só os "killer items" (perigosos de pular E fáceis
de esquecer), e cabe numa página. Acima de 60-90s pra rodar, vira distração.

Desenho novo:
  - 9 ENTREGÁVEIS rastreados no banco (cada um com dono, status e critério de pronto)
  - as microtarefas viram to_do DENTRO da página do entregável (controle nosso,
    não linha de painel)
  - as minas ficam coladas no entregável onde mordem, não numa seção distante

Segue a gramática visual do "Exemplo de Checklist" do Gabriel: heading_2 +
divider por seção, itens em banco EMBUTIDO (is_inline).

MINA da API do Notion: propriedade tipo `status` NÃO pode ser criada via API
(só na interface). O campo Status aqui é `select` com as mesmas opções.

Uso:
  python notion_template_canal.py                    # cria
  python notion_template_canal.py --arquivar <id>    # arquiva a versão velha antes
"""
import argparse
import json
import os
import sys
import urllib.request

API = "https://api.notion.com/v1"
VER = "2022-06-28"
RAIZ_PADRAO = "33d6bf27-9f65-4043-8a5d-c53fe0b241a3"   # página "Business System"


def token():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    for line in open(p, encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "").strip()
        if line.startswith("NOTION_TOKEN="):
            return line.split("=", 1)[1]
    sys.exit("NOTION_TOKEN nao encontrado no .env")


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


def rt(txt):
    return [{"type": "text", "text": {"content": txt}}]


def h2(t):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": rt(t)}}


def h3(t):
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": rt(t)}}


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def para(t):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt(t)}}


def todo(t):
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": rt(t), "checked": False}}


def callout(t, emoji, cor):
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": rt(t), "icon": {"emoji": emoji}, "color": cor}}


# ── OS 9 ENTREGÁVEIS ────────────────────────────────────────────────────────
# (entregavel, dono, criterio_de_pronto, [passos], mina_ou_None)
ENTREGAVEIS = [
    ("1. Licenca da fonte provada", "Gabriel",
     "Documento de prova arquivado junto do corpus: obra, edicao, ano e link",
     ["Escolher a obra-fonte do canal",
      "Confirmar que esta em dominio publico ou tem licenca comercial",
      "Checar as camadas SEPARADAS: texto, traducao, audio, arranjo",
      "Arquivar a prova (edicao publicada + data) junto do corpus"],
     "As camadas tem donos e datas DIFERENTES. Obra de 1780 com traducao de 1990 = "
     "traducao protegida. Musica: composicao e master sao direitos separados, e "
     "licenca mecanica cobre audio mas nao video (isso e sincronizacao)."),

    ("2. Identidade visual pronta", "Gabriel",
     "Avatar, banner e template de video no R2, aprovados no olho",
     ["Definir nome e handle (conferir disponibilidade)",
      "Criar avatar e banner",
      "Definir o visual do video: fundo, tipografia e estilo de legenda",
      "Subir tudo pro R2 em {prefix}/_assets/",
      "Escrever descricao e palavras-chave do canal"],
     "Visual generico de banco de imagem repetido N vezes e o que dispara a politica "
     "de conteudo inautentico do YouTube. Original nao e capricho, e requisito de "
     "monetizacao."),

    ("3. Canal criado e credencial funcionando", "Gabriel",
     "channels?mine=true retorna o canal certo, e o ID confere com canais.py",
     ["Criar o canal (canal de marca na conta Google)",
      "Criar projeto no Google Cloud e ativar YouTube Data API v3 (um projeto POR canal)",
      "Mudar publishing status de Testing para In production ANTES de autenticar",
      "Criar credencial OAuth tipo App para computador",
      "Rodar auth_youtube.py escolhendo o canal certo na tela",
      "Gravar credenciais nos DOIS .env da VPS (/app e /srv)",
      "Confirmar por API qual canal o token autenticou"],
     "Tres incidentes moram aqui. (1) OAuth em Testing expira o token em 7 dias, "
     "sempre. (2) Token valido NAO prova canal certo: 18 videos foram parar na conta "
     "pessoal sem UM erro. (3) A VPS tem DOIS .env e trocar em um so quebra o upload."),

    ("4. Canal ligado na esteira", "Claude",
     "--canal <slug> --dry-run sai correto, e o guardiao BARRA quando falta config",
     ["Criar a entrada em remotion/canais.py",
      "Preencher youtube_channel_id (sem ele a publicacao fica bloqueada)",
      "Criar o prefixo no R2 e subir os _assets",
      "Rodar --dry-run e conferir o calendario",
      "Testar que o guardiao aborta com canal incompleto"],
     "Um refresh_token vale pra UM canal. Canal novo usa o SEU env_prefix "
     "(ex.: YT_BIBLIA_*), nunca reaproveita o do canal anterior."),

    ("5. Voz travada", "Gabriel",
     "Amostra real aprovada no ouvido, e voz + velocidade fixadas em canais.py",
     ["Gerar amostras candidatas com texto real do canal",
      "Escolher no ouvido (nao no papel)",
      "Conferir que e DIFERENTE das vozes dos outros canais da holding",
      "Aplicar a regra de pausa: cortar em ponto, aparar as pontas, emendar",
      "QA em 3 trechos de natureza diferente"],
     "O Kokoro cola ~1,1s de silencio em CADA ponta de cada trecho. Emendar sem aparar "
     "da pausa de ~2,6s por mais que se reduza o silencio inserido. Medir por "
     "transcricao word-level, nunca por ouvido."),

    ("6. Corpus fatiado e na fila", "Claude",
     "Fila persistida com o acervo inteiro cortado, e o total de videos conhecido",
     ["Baixar a fonte e validar a integridade",
      "Definir o recorte por video (duracao alvo e regra de corte)",
      "Fatiar respeitando fronteira natural (capitulo, secao, frase)",
      "Definir a ordem de publicacao",
      "Gravar a fila no estado"],
     None),

    ("7. Primeiro video renderizado e aprovado", "Gabriel",
     "MP4 completo assistido do inicio ao fim e aprovado",
     ["Renderizar 1 video completo",
      "Assistir inteiro, nao so o comeco",
      "Conferir audio, legenda, visual e CTA",
      "Ajustar o que aparecer e re-renderizar"],
     "Certificacao de audio se faz TRANSCREVENDO o mp4 renderizado, nunca confiando em "
     "timestamp de arquivo. Ja aconteceu de CTA velho ficar cacheado e o gate de "
     "frescor dizer que estava novo."),

    ("8. Piloto publicado", "Gabriel",
     "1 video no ar no canal CERTO, com channelId conferido por API",
     ["Publicar 1 video de verdade (gate humano)",
      "Conferir por API que caiu no canal certo",
      "Conferir titulo, descricao, thumb e agendamento no YouTube Studio",
      "Rodar mais 2 e confirmar 3 limpos seguidos"],
     None),

    ("9. Automacao com vigia ligada", "Claude",
     "Cron rodando E alarme testado com uma falha proposital",
     ["Ligar o cron ou servico",
      "Configurar alarme no Discord: erro OU 48h sem publicar",
      "Testar o alarme forcando uma falha",
      "Documentar como pausar a esteira em emergencia"],
     "Os dois incidentes do Spurgeon (6 e 8 dias parado) foram descobertos pelo Gabriel "
     "olhando o canal, nao pelo sistema. Canal nao entra em producao sem vigia."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default=RAIZ_PADRAO)
    ap.add_argument("--arquivar", default=None, help="id de pagina antiga pra arquivar")
    args = ap.parse_args()

    if args.arquivar:
        call("PATCH", "/pages/" + args.arquivar, {"archived": True})
        print("versao antiga arquivada")

    print("criando a pagina ...")
    pagina = call("POST", "/pages", {
        "parent": {"type": "page_id", "page_id": args.parent},
        "icon": {"emoji": "\U0001F3ED"},
        "properties": {"title": {"title": rt("Template - Lancamento de canal novo")}},
        "children": [
            callout("Duplique esta pagina para cada canal novo. Sao 9 entregaveis. "
                    "Abra cada um para ver os passos e as minas. Nada e pronto sem o "
                    "criterio de pronto cumprido com verificacao real: comando rodado, "
                    "print, numero medido.", "\U0001F4CB", "blue_background"),
            para(""),
            h2("Cabecalho do canal"),
            divider(),
            para("Nome do canal:"),
            para("Slug na esteira (canais.py):"),
            para("Idioma:"),
            para("Nicho e promessa ao espectador:"),
            para("Fonte do conteudo:"),
            para("Data de inicio:"),
            para(""),
            h2("Os 9 entregaveis"),
            divider(),
        ],
    })
    pid = pagina["id"]
    print("pagina:", pagina["url"])

    print("criando o banco embutido ...")
    db = call("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": pid},
        "is_inline": True,
        "title": rt("Entregaveis do canal"),
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
    dbid = db["id"]

    for nome, dono, dod, passos, mina in ENTREGAVEIS:
        filhos = []
        if mina:
            filhos.append(callout(mina, "\U0001F9E8", "red_background"))
        filhos.append(h3("Passos"))
        filhos += [todo(p) for p in passos]
        call("POST", "/pages", {
            "parent": {"database_id": dbid},
            "properties": {
                "Entregavel": {"title": rt(nome)},
                "Dono": {"select": {"name": dono}},
                "Status": {"select": {"name": "Nao iniciada"}},
                "Criterio de pronto": {"rich_text": rt(dod)},
            },
            "children": filhos,
        })
        print("  ok:", nome)

    print("escrevendo o rodape ...")
    call("PATCH", "/blocks/" + pid + "/children", {"children": [
        para(""),
        h2("Ordem e dependencias"),
        divider(),
        para("O 1 trava tudo: licenca errada e canal perdido depois de meses de trabalho."),
        para("O 3 trava so a publicacao. O 5 e o 6 podem correr em paralelo com ele."),
        para("O 2 e o 5 travam o render, porque definem visual e timbre."),
        para(""),
        h2("Retrospectiva (preencher no fim)"),
        divider(),
        para("O que quebrou que nao estava previsto?"),
        para("Que mina nova entrou neste template?"),
        para("Quanto tempo do primeiro commit ao primeiro video?"),
    ]})

    print("\nPRONTO:", pagina["url"])


if __name__ == "__main__":
    main()
