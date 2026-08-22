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
        # marketing / publicação
        "titulo_sufixo": " (Charles Spurgeon)",
        "tags": "Charles Spurgeon,sermon,christian,gospel,faith,spurgeon sermons",
        "hashtags": "#CharlesSpurgeon #Christian #Gospel #Faith #Hope",
        "cta_livro": "The Best of Charles Spurgeon",
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
        "titulo_sufixo": " (KJV)",
        "tags": "bible,kjv,king james,scripture,bible reading,audio bible",
        "hashtags": "#Bible #KJV #Scripture #AudioBible",
        "cta_livro": "",
        "cta_texto": "",
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
        "um_por_dia": False,               # acervo 90-120: 1 a cada 2 dias (doc 19)
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        "cta_assets": [],
        "titulo_sufixo": " (D.L. Moody)",
        "tags": "D.L. Moody,DL Moody,sermon,christian,gospel,evangelist,moody sermons",
        "hashtags": "#DLMoody #Christian #Gospel #Faith #Hope",
        "cta_livro": "",
        "cta_texto": "",
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
