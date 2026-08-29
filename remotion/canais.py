#!/usr/bin/env python3
"""
canais.py — configuração POR CANAL da esteira de vídeo.

Por que existe: até 15/08/2026 a esteira era mono-canal. `CHANNEL_PREFIX`,
`STATE_KEY`, `EXPECTED_CHANNEL_ID`, voz e prefixo de render estavam grudados
em 8 arquivos diferentes. Canal novo significava copiar arquivo, e copiar
arquivo significa três versões divergentes do mesmo bug.

Agora canal novo = uma entrada neste dicionário.

## Como usar (todo script da esteira)

    import canais
    C = canais.get(args.canal)      # ou canais.get() → lê env CANAL, default spurgeon
    prefix = C["prefix"]

## MINA: cada canal tem o SEU token do YouTube

Um refresh_token vale pra UM canal. Por isso cada canal declara `env_prefix`,
e as credenciais viram `{env_prefix}_CLIENT_ID` / `_CLIENT_SECRET` / `_REFRESH_TOKEN`.
O Spurgeon usa `YT` (mantém o `.env` atual funcionando sem migração).

## MINA: `youtube_channel_id` não é decoração

É o guardião nascido do incidente de 11/08, quando a re-auth foi feita na conta
pessoal do Gabriel e 18 vídeos foram parar no canal errado sem UM erro sequer.
Token válido não prova canal certo. Canal sem esse ID preenchido NÃO publica.

## MINA: nome de arquivo LOCAL é contrato, não descrição

Os templates chamam `staticFile("images/cathedral_bg_cf_1.png")` e
`staticFile("images/spurgeon_avatar.png")` com o nome cravado. Então o bloco
`assets.fixos` mapeia CHAVE NO R2 -> NOME LOCAL: o fundo do Moody vem de
`hall/hall_bg_cf_1.png` e aterrissa como `cathedral_bg_cf_1.png`. É feio e é
de propósito: enquanto os dois canais compartilharem os mesmos templates,
renomear o contrato é mexer em 8 arquivos .tsx pra não ganhar nada. O nome
certo entra quando o Moody ganhar pasta de marca própria.
"""
import os

CANAIS = {
    # ─────────────────────────────────────────────────────────────────────
    "spurgeon": {
        "nome": "Charles Spurgeon Treasures",
        "bucket": "mananciall",
        "prefix": "channels/channels_youtube/treasures_charlesspurgeon",
        "renders_prefix": "renders/spurgeon",
        "state_key": "schedule/spurgeon_schedule.json",
        "youtube_channel_id": "UCXqp7wuorli1uLZKJM96T6Q",
        "env_prefix": "YT",
        "idioma": "en",
        "voz": "bm_george",
        "voz_speed": "0.9",
        # calendário
        "um_por_dia": True,
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        # CTAs fixos (mutáveis: trocar dispara re-render — ver gate de frescor)
        "cta_assets": ["_assets/introfixed.mp3", "_assets/finalfixed.mp3"],
        # CTAs FIXOS narrados (telas 2 e 5 do vídeo). Copy recuperada em 22/08
        # transcrevendo os proprios mp3 que ja estavam no ar: nao existia texto
        # fonte em lugar nenhum, so o audio. Agora existe, e canal novo herda a
        # estrutura em vez de reinventar.
        "cta_intro_texto": (
            "So take this opportunity to subscribe to the channel, turn on notifications, "
            "and visit our collection with the best books and devotionals by Charles Spurgeon "
            "to enrich your soul. Link in the description below. God bless you, and let us begin."),
        "cta_outro_texto": (
            "If you enjoyed this message, consider subscribing to the channel, turning on "
            "notifications, and visiting our collection with the best books and devotionals by "
            "Charles Spurgeon to enrich your soul. God bless you."),

        # marketing / publicação
        # nome do pregador como o espectador o conhece; entra no prompt de
        # marketing e no sufixo do titulo. Canal sem pregador (Biblia) fica vazio.
        "pregador": "Charles Spurgeon",
        # LIKE usado no `works.author` do D1 de mineracao. Fica separado do
        # `pregador` porque o banco guarda o nome como a FONTE escreveu
        # ("Charles Haddon Spurgeon"), nao como o canal assina.
        "autor_mineracao": "%purgeon%",
        # modelo do faster-whisper na VPS. `.en` so serve pra ingles;
        # canal em PT/ES tem que usar "small" (multilingue).
        "asr_modelo": "small.en",
        "pausa_frase_s": 0.75,
        "titulo_sufixo": " (Charles Spurgeon)",
        "tags": "Charles Spurgeon,sermon,christian,gospel,faith,spurgeon sermons",
        "hashtags": "#CharlesSpurgeon #Christian #Gospel #Faith #Hope",
        "cta_livro": "The Best of Charles Spurgeon",
        # MARCA QUE APARECE NA TELA. Estava cravada dentro dos .tsx, e por isso
        # o 1º vídeo do Moody exibiu "The Best of Charles Spurgeon" no CTA.
        # Descoberto assistindo o render, não lendo código (23/08).
        "colecao_titulo": "The Best of Charles Spurgeon",
        "link_label": "mananciall.org/en/treasures-spurgeon",
        "cta_texto": "📖 Charles Spurgeon's books & devotionals: {link}",
        # QR impresso no vídeo: curto de propósito (menos módulos = lê melhor).
        # Formato LEGADO sem canal — os QRs já publicados apontam pra cá.
        "redirect_base": "https://mananciall.org/go?s=yt&v=",
        # link limpo pra descrição/sobre do canal (o Worker loga como medium=canal)
        "link_canal": "https://mananciall.org/go/charlesspurgeontreasures",
        "assets": {
            "fundo": ("cathedral", r"cathedral_bg_cf_\d+\.png$"),
            "busto": ("avatars", r"spurgeon_bust_cf_\d+\.png$"),
            "fixos": {
                "cathedral/cathedral_bg_cf_1.png": "cathedral_bg_cf_1.png",
                "cathedral/cathedral_bg_cf_3.png": "cathedral_bg_cf_3.png",
                "avatars/spurgeon_base.png": "spurgeon_base.png",
                "channelavatar.png": "spurgeon_avatar.png",
            },
        },
    },
    # ─────────────────────────────────────────────────────────────────────
    # Canal 2 — narração bíblica em inglês (KJV).
    # Decisões travadas em 03/08: KJV primeiro (WEB depois), voz `am_michael`
    # speed 0.80, pausa de 0,75s entre frases com as pontas aparadas.
    # ⬜ PENDENTE antes de publicar: criar o canal no YouTube, rodar
    #    auth_youtube.py escolhendo ELE, e preencher `youtube_channel_id`.
    "biblia_kjv": {
        "nome": "(a definir) — Bíblia KJV",
        "bucket": "mananciall",
        "prefix": "channels/channels_youtube/biblia_kjv",
        "renders_prefix": "renders/biblia_kjv",
        "state_key": "schedule/biblia_kjv_schedule.json",
        "youtube_channel_id": "",          # ⬜ vazio = publicação BLOQUEADA
        "env_prefix": "YT_BIBLIA",
        "idioma": "en",
        # 20/08: Gabriel trocou am_michael por am_onyx ouvindo o A/B do Moody
        # ("onyx é f#da pra narrar a Bíblia inteira"). Michael voltou pro pool.
        # ✅ VELOCIDADE TRAVADA 20/08 em 0.80, depois de 12 amostras: primeiro
        # 0.76/0.80/0.84 no Salmo 23, depois 0.68/0.72/0.76 em três naturezas
        # de texto do corpus real (narrativa/poesia/ensino). Gabriel decidiu 0.80.
        # ⚠️ Ele havia achado 0.80 "corrido" na 1ª rodada e preferido 0.76;
        # mudou de ideia ouvindo as passagens reais. Se soar rápido em produção,
        # 0.76 é o candidato imediato.
        "voz": "am_onyx",
        "voz_speed": "0.80",
        "pausa_frase_s": 0.75,             # específico deste canal (ver doc 10)
        "um_por_dia": True,
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        "cta_assets": [],
        "pregador": "",
        "autor_mineracao": "",   # corpus vem do preparar_corpus, nao da mineracao
        "asr_modelo": "small.en",
        "titulo_sufixo": " (KJV)",
        "tags": "bible,kjv,king james,scripture,bible reading,audio bible",
        "hashtags": "#Bible #KJV #Scripture #AudioBible",
        "cta_livro": "",
        "cta_texto": "",
        "colecao_titulo": "",
        "link_label": "",
        "redirect_base": "https://mananciall.org/go/biblia?v=",
        "link_canal": "",
        "assets": None,                    # ⬜ nenhum asset visual gerado ainda
    },
    # ─────────────────────────────────────────────────────────────────────
    # Canal 3 — D.L. Moody Treasures (arquétipo TREASURES, 2º da família).
    # Voz escolhida no A/B de 20/08: am_adam. Velocidade provisória até o
    # teste de lapidação (0.80/0.84/0.88/0.92) ser ouvido pelo Gabriel.
    # ⬜ PENDENTE: canal no YouTube + YT_MOODY_* + youtube_channel_id.
    "moody": {
        # nome EXATO do canal no YouTube (conferido pela API em 21/08)
        "nome": "Dwight Lyman Moody Treasures",
        "bucket": "mananciall",
        "prefix": "channels/channels_youtube/treasures_dlmoody",
        "renders_prefix": "renders/moody",
        "state_key": "schedule/moody_schedule.json",
        "youtube_channel_id": "UCX1HH8v0nQ03VLVq_DujdqA",
        "env_prefix": "YT_MOODY",
        "idioma": "en",
        "voz": "am_adam",
        # ✅ TRAVADA 20/08 em 0.84, depois de ouvir 0.80/0.84/0.88/0.92.
        # Fica um clique abaixo do Spurgeon (0.9): o Moody é mais conversado.
        "voz_speed": "0.84",
        "videos_por_dia": 0.5,             # acervo 77: 1 a cada 2 dias, pra durar (doc 19)
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        "cta_assets": ["_assets/introfixed.mp3", "_assets/finalfixed.mp3"],
        # Idêntico ao Spurgeon, com o nome do Moody. Cheguei a gravar uma versão
        # que só dizia "our library of Christian classics" pra não prometer uma
        # coleção que ainda não existe na livraria. Decisão do Gabriel em 22/08,
        # e ele está certo: a coleção sai em dias, o vídeo fica no ar por
        # DÉCADAS. Gravar a versão fraca pra sempre, pra ficar correto por uma
        # semana, é o pior lado da troca.
        # ⬜ PENDENTE: criar a coleção "The Best of D.L. Moody" na livraria.
        "cta_intro_texto": (
            "So take this opportunity to subscribe to the channel, turn on notifications, "
            "and visit our collection with the best books and devotionals by D.L. Moody "
            "to enrich your soul. Link in the description below. God bless you, and let us begin."),
        "cta_outro_texto": (
            "If you enjoyed this message, consider subscribing to the channel, turning on "
            "notifications, and visiting our collection with the best books and devotionals by "
            "D.L. Moody to enrich your soul. God bless you."),
        "pregador": "D.L. Moody",
        "autor_mineracao": "%Moody%",
        "asr_modelo": "small.en",
        "pausa_frase_s": 0.75,
        "titulo_sufixo": " (D.L. Moody)",
        "tags": "D.L. Moody,DL Moody,sermon,christian,gospel,evangelist,moody sermons",
        "hashtags": "#DLMoody #Christian #Gospel #Faith #Hope",
        "cta_livro": "The Best of D.L. Moody",
        "cta_texto": "📖 D.L. Moody's books & devotionals: {link}",
        "colecao_titulo": "The Best of D.L. Moody",
        "link_label": "mananciall.org/go/moody",
        "redirect_base": "https://mananciall.org/go/moody?v=",
        "link_canal": "https://mananciall.org/go/dlmoodytreasures",
        "assets": {
            "fundo": ("hall", r"hall_bg_cf_\d+\.png$"),
            "busto": ("avatars", r"moody_bust_cf_\d+\.png$"),
            "fixos": {
                "hall/hall_bg_cf_1.png": "cathedral_bg_cf_1.png",
                "hall/hall_bg_cf_3.png": "cathedral_bg_cf_3.png",
                # o Moody não tem retrato "base" próprio; a pose 1 faz o papel
                "avatars/moody_bust_cf_1.png": "spurgeon_base.png",
                "channelavatar.png": "spurgeon_avatar.png",
            },
        },
    },
    # ─────────────────────────────────────────────────────────────────────
    # Canal 4 — Alexander Maclaren Treasures (arquétipo TREASURES, 3º da família).
    #
    # Escolhido pelo Gabriel em 26/08 como Treasures 3, e é o MAIOR acervo da
    # rede depois do Spurgeon: 1.482 capítulos já minerados (19 obras do CCEL,
    # 27/08), mediana de 14k chars = sermão de ~25min. A 1/dia dá QUATRO ANOS
    # sem repetir. Passa no filtro doutrinário da casa (doc 18_REDE_TREASURES,
    # critério 6): herança reformada branda, púlpito expositivo e devocional.
    #
    # ⬜ GATES DO GABRIEL, nesta ordem:
    #    1. escolher a voz (amostras bm_lewis/bm_daniel/bm_fable geradas em 27/08)
    #    2. criar o canal no YouTube + verificar por telefone (senão a capa dá 403)
    #    3. auth_youtube.py -> YT_MACLAREN_* no .env
    #    4. preencher `youtube_channel_id` aqui
    #    5. criar a coleção "The Best of Alexander Maclaren" na livraria
    # Sem o passo 4 o publish ABORTA de propósito (assert_canal_certo).
    "maclaren": {
        "nome": "Alexander Maclaren Treasures",
        "bucket": "mananciall",
        "prefix": "channels/channels_youtube/treasures_maclaren",
        "renders_prefix": "renders/maclaren",
        "state_key": "schedule/maclaren_schedule.json",
        "youtube_channel_id": "",          # ⬜ gate 4
        "env_prefix": "YT_MACLAREN",
        "idioma": "en",
        # ✅ TRAVADA 27/08 pelo Gabriel, depois de ouvir bm_lewis/bm_daniel/
        # bm_fable no mesmo trecho real ("What Crouches at the Door").
        # Britânica porque Maclaren era escocês pregando em Manchester.
        # bm_george está fora: é a voz do Spurgeon, e a regra da casa é uma voz
        # por canal, senão os dois soam como o mesmo canal pra quem ouve os dois.
        "voz": "bm_lewis",
        "voz_speed": "0.9",
        "videos_por_dia": 1.0,             # 1.482 capítulos = ~4 anos de diário
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        # Teto menor que o padrão de 55k: o maior sermão do Maclaren no acervo
        # tem ~50k, e as peças acima disso são container que o seletor de nível
        # não repartiu (ver o status `longo` em narrar_sermao.py).
        "chars_max": 52000,
        "cta_assets": ["_assets/introfixed.mp3", "_assets/finalfixed.mp3"],
        "cta_intro_texto": (
            "So take this opportunity to subscribe to the channel, turn on notifications, "
            "and visit our collection with the best books and expositions by Alexander Maclaren "
            "to enrich your soul. Link in the description below. God bless you, and let us begin."),
        "cta_outro_texto": (
            "If you enjoyed this message, consider subscribing to the channel, turning on "
            "notifications, and visiting our collection with the best books and expositions by "
            "Alexander Maclaren to enrich your soul. God bless you."),
        "pregador": "Alexander Maclaren",
        "autor_mineracao": "%aclaren%",
        "asr_modelo": "small.en",
        "pausa_frase_s": 0.75,
        "titulo_sufixo": " (Alexander Maclaren)",
        "tags": "Alexander Maclaren,maclaren,sermon,christian,bible exposition,expository preaching",
        "hashtags": "#AlexanderMaclaren #Christian #Bible #Faith #Exposition",
        "cta_livro": "The Best of Alexander Maclaren",
        "cta_texto": "📖 Alexander Maclaren's books & expositions: {link}",
        "colecao_titulo": "The Best of Alexander Maclaren",
        "link_label": "mananciall.org/go/maclaren",
        "redirect_base": "https://mananciall.org/go/maclaren?v=",
        "link_canal": "https://mananciall.org/go/maclarentreasures",
        "assets": None,                    # ⬜ busto e fundo ainda não gerados
    },
    # ─────────────────────────────────────────────────────────────────────
    # Canal Treasures gerado pelo BERÇÁRIO (scripts/novo_canal.py) em 28/08/2026.
    # ⬜ GATES DO GABRIEL: canal no YouTube -> verificar por TELEFONE ->
    #    auth_youtube.py (YT_MURRAY_*) -> preencher youtube_channel_id ->
    #    coleção "The Best of Andrew Murray" na livraria. Sem o ID o publish ABORTA (guardião).
    "murray": {
        "nome": "Andrew Murray Treasures",
        "bucket": "mananciall",
        "prefix": "channels/channels_youtube/treasures_murray",
        "renders_prefix": "renders/murray",
        "state_key": "schedule/murray_schedule.json",
        "youtube_channel_id": "",
        "env_prefix": "YT_MURRAY",
        "idioma": "en",
        "voz": "bm_daniel",
        "voz_speed": "0.9",
        "videos_por_dia": 0.5,
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        "chars_max": 55000,
        "cta_assets": ["_assets/introfixed.mp3", "_assets/finalfixed.mp3"],
        "cta_intro_texto": (
            "So take this opportunity to subscribe to the channel, turn on notifications, "
            "and visit our collection with the best books and writings by Andrew Murray "
            "to enrich your soul. Link in the description below. God bless you, and let us begin."),
        "cta_outro_texto": (
            "If you enjoyed this message, consider subscribing to the channel, turning on "
            "notifications, and visiting our collection with the best books and writings by "
            "Andrew Murray to enrich your soul. God bless you."),
        "pregador": "Andrew Murray",
        "autor_mineracao": "%Murray%",
        "asr_modelo": "small.en",
        "pausa_frase_s": 0.75,
        "titulo_sufixo": " (Andrew Murray)",
        "tags": "Andrew Murray,murray,sermon,christian,gospel,preaching",
        "hashtags": "#AndrewMurray #Christian #Gospel #Faith",
        "cta_livro": "The Best of Andrew Murray",
        "cta_texto": "📖 Andrew Murray's books & writings: {link}",
        "colecao_titulo": "The Best of Andrew Murray",
        "link_label": "mananciall.org/go/murray",
        "redirect_base": "https://mananciall.org/go/murray?v=",
        "link_canal": "https://mananciall.org/go/murraytreasures",
        "assets": None,                    # ⬜ busto e fundo ainda não gerados
    },
}

PADRAO = "spurgeon"


def get(slug=None):
    """Config do canal. Ordem: argumento → env CANAL → padrão (spurgeon)."""
    slug = slug or os.environ.get("CANAL") or PADRAO
    if slug not in CANAIS:
        raise SystemExit(
            f"❌ canal desconhecido: {slug!r}. Conhecidos: {', '.join(sorted(CANAIS))}")
    c = dict(CANAIS[slug])
    c["slug"] = slug
    _normalizar_cadencia(c)
    return c


CADENCIAS_OK = (0.5, 1.0, 2.0)


def _normalizar_cadencia(c):
    """Resolve a cadência do canal pra UM campo: `videos_por_dia`.

    ⚠️ MINA ENCONTRADA EM 24/08, antes de inaugurar o Moody.
    O campo antigo era o booleano `um_por_dia`, e `False` significava
    **2 vídeos POR DIA** (manhã e noite). A config do Moody trazia
    `um_por_dia: False` com o comentário "1 a cada 2 dias" ao lado: o
    comentário dizia o CONTRÁRIO do que o código fazia, e "1 a cada 2 dias"
    nem existia como opção.

    E não estourava na inauguração: o warmup é 1/dia pra todo mundo, então o
    erro só apareceria no 15º vídeo, dobrando a cadência de um canal com 77
    capítulos. Bug com data marcada é pior que bug barulhento.

    Booleano que carrega três significados possíveis é o defeito de raiz.
    Agora a cadência é um NÚMERO e diz o que é: 0.5 = um a cada dois dias,
    1 = um por dia, 2 = dois por dia. `um_por_dia` continua aceito pros canais
    antigos, e vira número aqui.
    """
    if "videos_por_dia" not in c:
        c["videos_por_dia"] = 1.0 if c.get("um_por_dia", True) else 2.0
    v = float(c["videos_por_dia"])
    if v not in CADENCIAS_OK:
        raise SystemExit(
            f"❌ canal {c['slug']}: videos_por_dia={v} não existe no calendário.\n"
            f"   Valores aceitos: {CADENCIAS_OK} (0.5=a cada 2 dias, 1=diário, 2=manhã+noite).")
    c["videos_por_dia"] = v
    c["um_por_dia"] = (v == 1.0)   # só pra quem ainda lê o campo velho
    return c


def creds_youtube(c, env):
    """Credenciais do YouTube DESTE canal, resolvidas pelo env_prefix.

    Erra alto e cedo: credencial faltando é melhor descoberta aqui do que
    num HTTP 400 no meio de um upload de 190MB.
    """
    p = c["env_prefix"]
    faltando = [f"{p}_{k}" for k in ("CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN")
                if not env.get(f"{p}_{k}")]
    if faltando:
        raise SystemExit(
            f"❌ canal {c['slug']}: faltam no .env → {', '.join(faltando)}\n"
            f"   Rode auth_youtube.py autenticando no canal {c['nome']!r}.")
    return (env[f"{p}_CLIENT_ID"], env[f"{p}_CLIENT_SECRET"], env[f"{p}_REFRESH_TOKEN"])


def add_arg_canal(ap):
    """Adiciona --canal em qualquer argparse da esteira, com o mesmo texto."""
    ap.add_argument("--canal", default=None,
                    help=f"slug do canal ({', '.join(sorted(CANAIS))}); "
                         f"default: env CANAL ou {PADRAO}")
