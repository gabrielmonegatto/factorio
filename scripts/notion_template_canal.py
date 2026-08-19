#!/usr/bin/env python3
"""
notion_template_canal.py — cria no Notion o TEMPLATE de lançamento de canal novo.

Segue a gramática visual que o Gabriel já usa no "Exemplo de Checklist":
seções com heading_2 + divider, e os itens num BANCO EMBUTIDO (is_inline)
em vez de caixinhas soltas — assim dá pra filtrar, agrupar e acompanhar status.

MINA da API do Notion: propriedade do tipo `status` NÃO pode ser criada via API
(só na interface). Por isso o campo Status aqui é `select` com as mesmas opções.
Pra virar status de verdade, converte na mão depois: os dados são preservados.

Uso:
  python notion_template_canal.py                 # cria sob "Business System"
  python notion_template_canal.py --parent <id>   # sob outra página
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


def h2(txt):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": rt(txt)}}


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def para(txt):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt(txt)}}


def callout(txt, emoji, cor):
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": rt(txt), "icon": {"emoji": emoji}, "color": cor}}


# ── conteúdo do checklist ───────────────────────────────────────────────────
BLOCOS = [
    ("0 - Licenca", [
        ("Definir a obra-fonte e PROVAR que e livre pra uso comercial", "Gabriel",
         "Prova arquivada junto do corpus: edicao, data e link"),
        ("Checar as camadas separadas de direito", "Claude",
         "Texto, audio, traducao e arranjo tem dono e data proprios"),
        ("Registrar a decisao com data", "Claude",
         "Escrita neste doc, nao combinada verbalmente"),
    ]),
    ("1 - Identidade", [
        ("Nome e handle", "Gabriel", "Disponivel no YouTube"),
        ("Avatar e banner", "Gabriel", "Arquivos no R2 em {prefix}/_assets/"),
        ("Visual do video (fundo, tipografia, legenda)", "Claude",
         "Original, nao banco de imagem generico"),
        ("Descricao e palavras-chave do canal", "Gabriel", "Publicado"),
    ]),
    ("2 - Canal e credencial", [
        ("Criar o canal (canal de marca na conta Google)", "Gabriel", "Canal existe e tem ID"),
        ("Projeto no Google Cloud + YouTube Data API v3 ativada", "Gabriel",
         "Um projeto POR CANAL, pra ter cota separada"),
        ("Publishing status: Testing para In production", "Gabriel",
         "Confirmado na tela ANTES de autenticar"),
        ("Criar credencial OAuth tipo App para computador", "Gabriel",
         "Client ID e Secret em maos"),
        ("Rodar auth_youtube.py escolhendo o canal certo", "Gabriel",
         "Script imprime as 3 linhas"),
        ("Gravar credenciais nos DOIS .env da VPS", "Claude",
         "/app/_factorio/.env e /srv/factorio/.env"),
        ("Confirmar por API qual canal o token autenticou", "Claude",
         "channels?mine=true bate com o ID esperado"),
    ]),
    ("3 - Ligar na esteira", [
        ("Criar entrada em remotion/canais.py", "Claude",
         "Prefixo, renders, estado, voz, calendario e tags preenchidos"),
        ("Preencher youtube_channel_id", "Claude",
         "Sem isso a publicacao fica bloqueada de proposito"),
        ("Criar prefixo no R2 e subir os _assets", "Claude", "Listagem mostra os arquivos"),
        ("Testar --canal <slug> --dry-run", "Claude", "Calendario sai correto"),
        ("Testar que o guardiao BARRA antes de estar pronto", "Claude",
         "Mensagem de aborto, nao upload"),
    ]),
    ("4 - Corpus e formato", [
        ("Levantar o acervo e o tamanho real", "Claude", "N de videos e horas totais estimados"),
        ("Definir o recorte por video", "Gabriel", "Duracao alvo e regra de corte"),
        ("Ordem de publicacao", "Gabriel", "Canonica ou por demanda"),
        ("Cadencia", "Gabriel", "Recomendado: 1 por dia"),
    ]),
    ("5 - Voz e audio", [
        ("Escolher a voz no ouvido, com amostra real", "Gabriel", "Aprovado"),
        ("Voz DIFERENTE dos outros canais da holding", "Claude",
         "Dois canais com a mesma voz viram o mesmo canal"),
        ("Travar voz e velocidade na config", "Claude", "Em canais.py, e nunca mais mexer"),
        ("Aplicar a regra de pausa (cortar em ponto, aparar pontas, emendar)", "Claude",
         "Medido por transcricao word-level, nao por ouvido"),
        ("QA em 3 trechos de natureza diferente", "Gabriel", "Ouvido e aprovado"),
    ]),
    ("6 - Camada original", [
        ("Visual original de verdade", "Claude", "Nao e banco de imagem repetido N vezes"),
        ("Trilha composta, licenciada com prova, ou nenhuma", "Gabriel", "Prova arquivada"),
        ("Camada editorial propria", "Claude",
         "Intro de contexto, estrutura e timestamps visiveis"),
        ("Variacao real entre videos", "Claude", "Fingerprint parecido e o que o radar pega"),
        ("Ler a politica vigente antes de submeter a monetizacao", "Gabriel", "Lida"),
    ]),
    ("7 - Funil", [
        ("Destino do CTA definido", "Gabriel", "URL viva"),
        ("QR e link apontando pro /go com v= proprio do canal", "Claude", "Redirect testado"),
        ("Rastreio de scan chegando", "Claude", "Um scan real aparece no log"),
    ]),
    ("8 - Piloto e estabilidade", [
        ("1 video publicado de verdade", "Gabriel", "No ar, conferido no canal"),
        ("Conferir que caiu no canal CERTO", "Claude", "channelId do video confere"),
        ("3 videos limpos seguidos", "Claude", "Sem intervencao manual"),
    ]),
    ("9 - Automacao e vigia", [
        ("Fila com o corpus fatiado", "Claude", "Estado persistido"),
        ("Cron ou servico ligado", "Claude", "systemctl e cron.d conferidos"),
        ("Alarme de falha no Discord", "Claude", "Erro OU 48h sem publicar dispara aviso"),
    ]),
]

CORES = ["red", "orange", "yellow", "green", "blue", "purple", "pink", "brown", "gray", "default"]

MINAS = [
    "OAuth em modo Testing expira o refresh token em 7 dias, sempre. O canal Spurgeon "
    "morreu calado por 6 dias por isso. Publicar o app e o conserto de raiz; "
    "re-autenticar sem publicar e band-aid de uma semana.",

    "Token valido NAO prova canal certo. A re-auth de 07/08 foi feita na conta pessoal: "
    "o token renovava, a API respondia 200, o log dizia sucesso, e 18 videos foram parar "
    "no canal errado. O guardiao so protege se o youtube_channel_id estiver preenchido.",

    "A VPS tem DOIS arquivos .env: o do repo (/app) e o operacional (/srv, que os "
    "containers leem via --env-file). Trocar credencial em um so quebra o upload.",

    "Um refresh_token vale pra UM canal. Canal novo usa o seu proprio env_prefix "
    "(ex.: YT_BIBLIA_*), nunca reaproveita o do canal anterior.",

    "O Kokoro cola ~1,1s de silencio em CADA ponta de cada trecho gerado. Emendar sem "
    "aparar da pausa de ~2,6s por mais que se reduza o silencio inserido.",

    "A esteira nao tem alarme. Os dois incidentes do Spurgeon (6 e 8 dias parado) foram "
    "descobertos pelo Gabriel olhando o canal. Canal novo nao entra em producao sem vigia.",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default=RAIZ_PADRAO)
    args = ap.parse_args()

    print("criando a pagina ...")
    pagina = call("POST", "/pages", {
        "parent": {"type": "page_id", "page_id": args.parent},
        "icon": {"emoji": "\U0001F3ED"},
        "properties": {"title": {"title": rt("Template - Lancamento de canal novo")}},
        "children": [
            callout("Duplique esta pagina para cada canal novo. Nada e pronto sem o "
                    "criterio de pronto cumprido com verificacao real: comando rodado, "
                    "print, numero medido. Nunca 'deve funcionar'.",
                    "\U0001F4CB", "blue_background"),
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
            h2("Checklist"),
            divider(),
        ],
    })
    pid = pagina["id"]
    print("pagina:", pagina["url"])

    print("criando o banco embutido ...")
    db = call("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": pid},
        "is_inline": True,
        "title": rt("Checklist do canal"),
        "properties": {
            "Item": {"title": {}},
            "Bloco": {"select": {"options": [
                {"name": b[0], "color": CORES[i]} for i, b in enumerate(BLOCOS)]}},
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

    total = 0
    for bloco, itens in BLOCOS:
        for nome, dono, dod in itens:
            call("POST", "/pages", {
                "parent": {"database_id": dbid},
                "properties": {
                    "Item": {"title": rt(nome)},
                    "Bloco": {"select": {"name": bloco}},
                    "Dono": {"select": {"name": dono}},
                    "Status": {"select": {"name": "Nao iniciada"}},
                    "Criterio de pronto": {"rich_text": rt(dod)},
                },
            })
            total += 1
    print(total, "itens inseridos")

    print("escrevendo as minas ...")
    filhos = [para(""), h2("Minas conhecidas (custaram dias de canal parado)"), divider()]
    filhos += [callout(t, "\U0001F9E8", "red_background") for t in MINAS]
    filhos += [para(""), h2("Retrospectiva (preencher no fim)"), divider(),
               para("O que quebrou que nao estava previsto?"),
               para("Que mina nova entrou neste template?"),
               para("Quanto tempo do primeiro commit ao primeiro video?")]
    for i in range(0, len(filhos), 90):
        call("PATCH", "/blocks/" + pid + "/children", {"children": filhos[i:i + 90]})

    print("\nPRONTO:", pagina["url"])


if __name__ == "__main__":
    main()
