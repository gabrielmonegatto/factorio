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


def estrategia():
    """ETAPA 1 — a estrategia inteira do canal, nao so a tese.

    Ordem que o Gabriel definiu em 19/08: ESTRATEGIA -> IDENTIDADE -> PRODUCAO.

    A bifurcacao do ARQUETIPO e o que faz este template servir pros dois tipos de
    canal da holding sem inchar: canal de REPLICA herda a estrategia do irmao mais
    velho e responde 4 perguntas; canal NOVO responde as 9.
    """
    return [
        h2("ETAPA 1 - Estrategia"),
        divider(),
        callout("Nada de producao comeca antes desta etapa estar escrita. Canal nao "
                "morre por producao ruim, morre por estrategia que ninguem testou.",
                "\U0001F3AF", "yellow_background"),

        h3("1.1 Arquetipo do canal (decide o resto desta etapa)"),
        callout("REPLICA (ex.: linha Treasures) - a tese ja foi validada por um canal "
                "irmao. Aposta em VOLUME, PREVISIBILIDADE e materia-prima que ja existe: "
                "e editar e distribuir acervo. Aqui a estrategia se HERDA: responda so "
                "1.2, 1.3, 1.4 e 1.9, e aponte pro canal de origem.",
                "\U0001F501", "green_background"),
        callout("NOVO / CIRURGICO - tese ainda nao provada, formato ou publico diferente. "
                "Aqui responda TODAS as perguntas desta etapa, com evidencia. "
                "Este e o caso caro: erra o alvo e sao meses jogados fora.",
                "\U0001F3AF", "orange_background"),
        para("Arquetipo deste canal:"),
        para("Se REPLICA, canal de origem e o que se herda dele:"),

        h3("1.2 Materia-prima"),
        para("Fonte do conteudo:"),
        para("Tamanho do acervo (quantos videos ele da):"),
        para("Acaba ou e renovavel? Se acaba, o que vem depois:"),

        h3("1.3 Formato e frequencia"),
        para("Formato do video (duracao, estrutura, o que se ve na tela):"),
        para("Frequencia de publicacao:"),
        para("Por quanto tempo o acervo sustenta essa frequencia:"),

        h3("1.4 Ofertas atreladas"),
        para("O que se vende ou capta atraves deste canal:"),
        para("Onde entra na jornada (descricao, QR, comentario fixado, fim do video):"),
        para("Destino do trafego:"),

        h3("1.5 Quem assiste, e em que momento do dia"),
        para("Resposta:"),
        para("Contexto de consumo importa mais que demografia. 'Alguem estudando de "
             "madrugada e querendo silencio na cabeca' vale mais que 'cristaos 25-45'."),

        h3("1.6 O que essa pessoa digita, e qual a prova de demanda"),
        para("Resposta:"),
        para("Prova exigida: termos reais com volume, mais 3 videos outlier de outros "
             "canais (5-10x acima da media deles) provando que o tema puxa."),

        h3("1.7 Quem ja serve isso, e onde eles falham"),
        para("Resposta:"),
        para("Auditar 5 concorrentes. Referencia de nicho pouco disputado: menos de 50 "
             "videos na primeira pagina com mais de 10 mil views."),

        h3("1.8 Aposta de packaging"),
        para("Formula de titulo:"),
        para("Formula de thumbnail:"),
        para("Como sao os primeiros 30 segundos:"),
        callout("Titulo e capa vendem o CLIQUE. Os primeiros 30 segundos vendem a "
                "PERMANENCIA. Sao dois problemas separados, com solucoes separadas. "
                "Packaging e o artefato de maior alavanca que existe no YouTube.",
                "\U0001F4E6", "purple_background"),

        h3("1.9 Criterios de vida ou morte (escritos ANTES de comecar)"),
        para("Checkpoint em quantos videos:"),
        para("Numeros que definem seguir:"),
        para("Numeros que definem pivotar ou matar:"),

        h3("Benchmarks pra calibrar os criterios acima"),
        callout("CTR de 4 a 6% e o alvo pra canal sem rosto. Retencao: 40-50% de "
                "percentual assistido num video de 10min indica potencial. Passar dos "
                "primeiros 60s com mais de 65% da audiencia correlaciona com retencao "
                "muito maior no resto do video.", "\U0001F4CA", "gray_background"),
        callout("TEMPO REAL ATE TRACAO: a maioria dos canais so ve tracao entre o video "
                "30 e o 50, e leva de 6 a 12 meses com 30 a 60 videos pra chegar a mil "
                "inscritos. Nos primeiros 3 meses a maioria dos videos fica abaixo de "
                "100 views. Isso e o NORMAL, nao o fracasso. Julgar canal no video 10 e "
                "matar antes do algoritmo ter dados pra entender quem gosta.",
                "\U000023F3", "blue_background"),
        callout("DECIDIR COM DADO, NAO COM ANSIEDADE: sao 4 saidas, nao 2. ESCALAR "
                "(funciona), PERSEVERAR (falta dado), PIVOTAR (mudar direcao) e MATAR "
                "(parar). Teste barato: 3 a 5 videos com o formato novo, em 4 a 6 "
                "semanas, medindo CTR, retencao nos primeiros 30-60s e espectadores "
                "recorrentes. Custa 5 videos em vez de um canal.",
                "\U0001F9ED", "gray_background"),
        para(""),
    ]


def identidade():
    """ETAPA 2 — como o canal se apresenta. Decisoes, nao execucao."""
    return [
        h2("ETAPA 2 - Identidade"),
        divider(),
        callout("Aqui e a DECISAO de como o canal se apresenta. A execucao (criar os "
                "arquivos e subir pro R2) e o entregavel 2 da Etapa 3.",
                "\U0001F3A8", "gray_background"),
        para("Nome e handle:"),
        para("Promessa em uma frase (o que o espectador ganha):"),
        para("Tom e ritmo (solene, acolhedor, urgente, contemplativo):"),
        para("Voz do canal (tem que ser DIFERENTE dos outros canais da holding):"),
        para("Direcao visual (fundo, tipografia, paleta, estilo de thumbnail):"),
        para("O que este canal NUNCA faz (limites de marca):"),
        para(""),
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
            para("Arquetipo (Replica ou Novo):"),
            para(""),
        ] + estrategia() + identidade() + [
            h2("ETAPA 3 - Producao"),
            divider(),
            callout("Os 9 entregaveis. Abra cada um pra ver os passos e as minas. "
                    "Nada e pronto sem o criterio de pronto cumprido com verificacao "
                    "real: comando rodado, print, numero medido.",
                    "\U0001F3ED", "gray_background"),
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
        h2("Ordem e dependencias (dentro da Etapa 3)"),
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
