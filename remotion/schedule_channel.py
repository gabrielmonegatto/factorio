#!/usr/bin/env python3
"""
schedule_channel.py — O AGENDADOR do canal (set-and-forget).

Mantém um buffer de vídeos JÁ AGENDADOS à frente. O YouTube publica sozinho no calendário.
Roda 1x/dia (cron). Cada run: preenche os slots do calendário até o horizonte, dos vídeos
que já estão renderizados (no R2), respeitando a cota de upload do YouTube.

CALENDÁRIO (decidido 25/07):
  - Semanas 1-2 (dias 0-13): 1/dia às 12:00 UTC (~08:00 ET)
  - Dia 14 em diante: 2/dia às 12:00 e 23:00 UTC (~08:00 e ~19:00 ET)
  - Ordem: sequencial (0001, 0002, 0003...)

Estado no R2: schedule/spurgeon_schedule.json  (channel_start + o que já foi agendado).

Uso (na VPS):
  python3 schedule_channel.py --dry-run     # mostra o calendário, não agenda
  python3 schedule_channel.py               # agenda o que falta (respeitando cota)
"""
import os
import sys
import json
import argparse
import datetime as dt
import subprocess
import urllib.request

import canais

HERE = os.path.dirname(os.path.abspath(__file__))

# Preenchidos em main() a partir de canais.get(--canal). Ficam como globais
# porque as funções auxiliares abaixo já os usavam assim quando eram constantes.
C = None
BUCKET = STATE_KEY = CHANNEL_PREFIX = RENDERS_PREFIX = None
EXPECTED_CHANNEL_ID = None
CTA_ASSET_KEYS = []


def aplicar_canal(slug=None):
    """Carrega a config do canal e publica nas globais que a esteira usa."""
    global C, BUCKET, STATE_KEY, CHANNEL_PREFIX, RENDERS_PREFIX
    global EXPECTED_CHANNEL_ID, CTA_ASSET_KEYS, VIDEOS_POR_DIA, WARMUP_DAYS
    global MORNING_UTC, EVENING_UTC, BUFFER_DAYS, MAX_UPLOADS_PER_RUN
    C = canais.get(slug)
    BUCKET = C["bucket"]
    STATE_KEY = C["state_key"]
    CHANNEL_PREFIX = C["prefix"]
    RENDERS_PREFIX = C["renders_prefix"]
    EXPECTED_CHANNEL_ID = C["youtube_channel_id"]
    CTA_ASSET_KEYS = [f"{CHANNEL_PREFIX}/{k}" for k in C["cta_assets"]]
    VIDEOS_POR_DIA = C["videos_por_dia"]
    WARMUP_DAYS = C["warmup_days"]
    MORNING_UTC = C["morning_utc"]
    EVENING_UTC = C["evening_utc"]
    BUFFER_DAYS = C["buffer_days"]
    MAX_UPLOADS_PER_RUN = C["max_uploads_per_run"]
    return C

# Cadência (horários, buffer, cota por run) vem de canais.py via aplicar_canal().
# Decisão do Gabriel em 04/08: "um por dia, sem desespero".
# A cadência é o campo `videos_por_dia`: 0.5, 1 ou 2. Era um booleano até 24/08,
# e o booleano mentia — ver _normalizar_cadencia() em canais.py.

# vídeos já subidos manualmente (privados) — o agendador só define o publishAt deles.
# Vazio: os antigos foram deletados (troca de CTA em 28/07); tudo re-sobe fresco via publish_sermon.
SEEDED = {}


def load_env():
    env = dict(os.environ)
    for p in (os.path.join(HERE, "..", ".env"), "/srv/factorio/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.replace("\r", "").strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k, v)
    return env


def s3c(env):
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"], aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def yt_token(env):
    import urllib.parse
    cid_, secret_, refresh_ = canais.creds_youtube(C, env)
    data = urllib.parse.urlencode({
        "client_id": cid_, "client_secret": secret_,
        "refresh_token": refresh_, "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        token = json.loads(r.read())["access_token"]
    assert_canal_certo(token)
    return token


# ⚠️ INCIDENTE 11/08/2026 — o que este guardião existe pra impedir:
# a re-auth de 07/08 foi feita na conta pessoal do Gabriel em vez do canal do
# projeto. O token renovava, a API respondia 200, tudo "funcionava" — e 5 vídeos
# foram parar públicos no canal PESSOAL enquanto o canal do projeto ficava parado
# há 8 dias. Token válido não prova canal certo. Agora prova.
# O ID esperado vem de canais.py (campo `youtube_channel_id`).


def assert_canal_certo(token):
    """Aborta se o token autenticado não for o do canal deste script."""
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
        headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=40) as r:
        itens = json.loads(r.read()).get("items", [])
    if not EXPECTED_CHANNEL_ID:
        raise SystemExit(
            f"❌ ABORTADO: canal {C['slug']!r} sem `youtube_channel_id` em canais.py.\n"
            f"   Crie o canal, rode auth_youtube.py nele e preencha o ID.")
    if not itens:
        raise SystemExit("❌ ABORTADO: o token não devolveu canal nenhum.")
    cid = itens[0]["id"]
    titulo = itens[0]["snippet"]["title"]
    if cid != EXPECTED_CHANNEL_ID:
        raise SystemExit(
            f"❌ ABORTADO: token autenticado no canal ERRADO.\n"
            f"   esperado: {EXPECTED_CHANNEL_ID}\n"
            f"   recebido: {cid} ({titulo})\n"
            f"   Rode auth_youtube.py e escolha o canal do projeto.")
    print(f"🔐 canal confirmado: {titulo} ({cid})")


def slot_datetime(i, channel_start):
    """publishAt (UTC) do i-ésimo vídeo (0-indexed) segundo o calendário.

    O WARMUP é sempre 1/dia, em qualquer cadência: canal recém-nascido precisa
    de dias seguidos de sinal, e é justamente aí que a cadência final não vale.
    Passado o warmup manda o `videos_por_dia` do canal:
        2.0 → dois por dia (manhã e noite)
        1.0 → um por dia
        0.5 → um a cada dois dias (acervo pequeno, esticado pra durar)
    """
    if i < WARMUP_DAYS:
        day, hour = i, MORNING_UTC
    else:
        j = i - WARMUP_DAYS
        if VIDEOS_POR_DIA == 2.0:
            day, hour = WARMUP_DAYS + j // 2, (MORNING_UTC if j % 2 == 0 else EVENING_UTC)
        elif VIDEOS_POR_DIA == 0.5:
            day, hour = WARMUP_DAYS + j * 2, MORNING_UTC
        else:
            day, hour = WARMUP_DAYS + j, MORNING_UTC
    d = channel_start + dt.timedelta(days=day)
    return dt.datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=dt.timezone.utc)


def proximo_slot(anterior, n_ja):
    """O slot SEGUINTE a um horário, na cadência do canal.

    Complementa o `slot_datetime`: aquele responde "onde cai o i-ésimo vídeo do
    calendário ideal", este responde "qual o próximo horário depois deste". É
    este que o agendador usa em regime, porque calendário real anda a partir do
    que já foi prometido, não de um índice (ver a MINA do buraco de 14 dias).
    """
    if n_ja < WARMUP_DAYS:                       # warmup é sempre 1/dia
        prox = anterior + dt.timedelta(days=1)
    elif VIDEOS_POR_DIA == 2.0:
        if anterior.hour < EVENING_UTC:          # manhã -> noite do MESMO dia
            return anterior.replace(hour=EVENING_UTC, minute=0, second=0, microsecond=0)
        prox = anterior + dt.timedelta(days=1)
    elif VIDEOS_POR_DIA == 0.5:
        prox = anterior + dt.timedelta(days=2)
    else:
        prox = anterior + dt.timedelta(days=1)
    return prox.replace(hour=MORNING_UTC, minute=0, second=0, microsecond=0)


def list_ready_sermons(s3):
    """Sermões prontos pra render/publicar (têm sermão+transcrição+copy+hook+outro), em ordem."""
    token, keys = None, []
    while True:
        kw = {"Bucket": BUCKET, "Prefix": f"{CHANNEL_PREFIX}/", "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        res = s3.list_objects_v2(**kw)
        keys += [o["Key"] for o in res.get("Contents", [])]
        if not res.get("IsTruncated"):
            break
        token = res.get("NextContinuationToken")
    import re
    # 🧨 MINA MEDIDA EM 09/09/2026 (o 0036 falhou no upload sem motivo aparente).
    # A versão antiga agrupava os arquivos pelo NÚMERO (`m.group(1)[:4]`), e o
    # acervo do Spurgeon tem 77 números com DUAS pastas (0036_-_the_first_
    # resurrection e 0036_-_..., 0001_-_consolation_in_christ e 0001_-_the_
    # immutability_of_god, etc). Os arquivos das duas viravam UM conjunto só, e
    # o número passava no teste pela UNIÃO: uma pasta tinha o áudio, a outra
    # tinha o copy, e nenhuma das duas estava pronta de verdade. O agendador
    # prometia o slot e o publicador quebrava lá na frente.
    # Conserto: avaliar POR PASTA, e olhar exatamente a pasta que o publicador
    # vai pegar. O `find_sermon_folder` do build_job usa `keys[0]` de um list
    # por prefixo, ou seja, a PRIMEIRA em ordem lexicográfica. Aqui é a mesma
    # regra, senão o agendador aprova uma pasta e o publicador abre outra.
    pastas = {}
    for k in keys:
        m = re.match(rf"{CHANNEL_PREFIX}/((\d[\d-]*)_-_[^/]+)/(.+)$", k)
        if m:
            pastas.setdefault(m.group(1), set()).add(m.group(3))

    def ok(f):
        has = lambda rx: any(re.match(rx, x) for x in f)
        return (has(r"sermon_\d+\.(wav|mp3)$") and "transcript.json" in f and "marketing_meta.json" in f
                and has(r"hook\.(wav|mp3)$") and "hook.json" in f
                and has(r"cta_narration\.(wav|mp3)$") and "cta_narration.json" in f)

    escolhida = {}
    for nome in sorted(pastas):            # lexicográfica = a mesma do build_job
        escolhida.setdefault(nome[:4], nome)
    return sorted(n for n, nome in escolhida.items() if ok(pastas[nome]))


def video_rendered(s3, nnnn):
    try:
        s3.head_object(Bucket=BUCKET, Key=f"{RENDERS_PREFIX}/{nnnn}.mp4")
        return True
    except Exception:
        return False


# CTAs/áudios fixos que ficam EMBUTIDOS no vídeo. Se um deles muda no R2, todo
# render feito ANTES dessa troca fica velho (voz/fala desatualizada) e precisa refazer.
# (a lista concreta vem de canais.py e é montada em aplicar_canal())


def assets_cutoff(s3):
    """LastModified mais recente entre os CTAs fixos. Render mais antigo que isso = velho."""
    latest = None
    for k in CTA_ASSET_KEYS:
        try:
            lm = s3.head_object(Bucket=BUCKET, Key=k)["LastModified"]
            if latest is None or lm > latest:
                latest = lm
        except Exception:
            pass
    return latest


def video_fresh(s3, nnnn, cutoff):
    """True só se o mp4 existe E é mais novo que os CTAs fixos (não precisa refazer)."""
    try:
        lm = s3.head_object(Bucket=BUCKET, Key=f"{RENDERS_PREFIX}/{nnnn}.mp4")["LastModified"]
    except Exception:
        return False
    return cutoff is None or lm >= cutoff


def schedule_existing(env, video_id, publish_at, token):
    """Só define o publishAt de um vídeo já subido (privado → agendado)."""
    body = json.dumps({"id": video_id, "status": {"privacyStatus": "private",
                       "publishAt": publish_at, "selfDeclaredMadeForKids": False}}).encode()
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status",
                                 data=body, method="PUT",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=40).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=None)
    canais.add_arg_canal(ap)
    args = ap.parse_args()

    # tem que vir ANTES de qualquer uso das globais (BUCKET, STATE_KEY, cota...)
    aplicar_canal(args.canal)
    if args.max is None:
        args.max = MAX_UPLOADS_PER_RUN
    print(f"🏷️  canal: {C['slug']} ({C['nome']})")

    env = load_env()
    s3 = s3c(env)

    # estado
    try:
        state = json.loads(s3.get_object(Bucket=BUCKET, Key=STATE_KEY)["Body"].read())
    except Exception:
        state = {}
    if "channel_start" not in state:
        # primeiro slot = amanhã (dá buffer)
        state["channel_start"] = (dt.date.today() + dt.timedelta(days=1)).isoformat()
    if "scheduled" not in state:
        state["scheduled"] = {}   # sermao -> {videoId, publishAt}
    channel_start = dt.date.fromisoformat(state["channel_start"])

    ready = list_ready_sermons(s3)
    now = dt.datetime.now(dt.timezone.utc)
    horizon = now + dt.timedelta(days=BUFFER_DAYS)

    print(f"📅 channel_start={channel_start} | sermões prontos: {len(ready)} | horizonte: {horizon.date()}")
    print(f"   já agendados: {len(state['scheduled'])}\n")

    cutoff = assets_cutoff(s3)   # renders mais antigos que os CTAs fixos = velhos, não sobem
    token = None if args.dry_run else yt_token(env)
    uploads = 0   # TENTATIVAS de upload (é isso que gasta cota e é isso que o teto corta)
    ok = 0        # tentativas que terminaram com videoId e estado salvo
    to_render = []

    # ── O CALENDÁRIO ANDA A PARTIR DO PRIMEIRO BURACO, NÃO DE UM ÍNDICE ─────
    #
    # 🧨 MINA MEDIDA EM 09/09/2026 (o Spurgeon parou de publicar por 14 dias).
    # A regra antiga era `slot = channel_start + índice_do_sermão_no_ready`, com
    # um "rebase" que reancorava o channel_start quando o slot calculado caía no
    # passado. Duas coisas envenenam essa fórmula ao longo da vida do canal:
    #   1. o `ready` CRESCE (acervo novo entra na lista e empurra os índices);
    #   2. cada rebase reancora o channel_start.
    # Depois de um rebase, os índices dos sermões JÁ AGENDADOS passam a apontar
    # pra datas futuras que ninguém vai usar (eles já têm data própria, anterior),
    # e essas datas viram BURACO. Medido: o 0034 saiu em 07/09 e o 0035 foi parar
    # em 22/09, com 09/09 a 21/09 vazios. O canal parecia morto com 164 sermões
    # prontos na prateleira.
    # E o rebase não pegava, porque ele só conserta slot no PASSADO; slot longe
    # demais no FUTURO passava batido.
    #
    # Conserto: fórmula não é registro. O agendador anda com um CURSOR que começa
    # no próximo horário alcançável e pula o que já foi prometido (`tomados`).
    # Assim ele PREENCHE buraco em vez de criar, sem nunca empilhar dois no mesmo
    # minuto, e não depende mais de índice nem de channel_start em regime.
    #
    # Próximo slot ainda alcançável (2h de folga pro upload). MINA (10/08): mirar
    # sempre em "amanhã" furava um dia inteiro quando o cron das 06:00 rodava e o
    # slot das 12:00 do MESMO dia ainda dava tempo.
    base = now + dt.timedelta(hours=2)
    pd = base.date() if base.hour < MORNING_UTC else (base + dt.timedelta(days=1)).date()
    primeiro = dt.datetime(pd.year, pd.month, pd.day,
                           MORNING_UTC, 0, 0, tzinfo=dt.timezone.utc)

    # ⚠️ SLOTS JÁ TOMADOS (mina de 26/08: DOIS vídeos públicos no mesmo minuto).
    # A fórmula dá o slot pelo par (índice, channel_start), mas o channel_start
    # MUDA ao longo da vida do canal (rebase de 10/08). Um retardatário — o 0008,
    # que falhou na época dos vizinhos e só subiu semanas depois — ganhou slot
    # calculado com uma base, e o 0022 ganhou o MESMO horário calculado com outra.
    # Ninguém conferia o que o estado já tinha prometido. Fórmula não é registro:
    # o conjunto de horários ocupados é dos vídeos, não da equação.
    tomados = {v["publishAt"] for v in state["scheduled"].values() if v.get("publishAt")}

    cursor = primeiro
    for nnnn in ready:
        if nnnn in state["scheduled"]:
            continue                   # já agendado: tem data própria, não mexe
        # Anda até o primeiro horário livre. Como `tomados` já traz TODOS os
        # horários prometidos (inclusive os do futuro), isto preenche buraco.
        while cursor.strftime("%Y-%m-%dT%H:%M:%SZ") in tomados:
            cursor = proximo_slot(cursor, len(state["scheduled"]))
        when = cursor
        if when > horizon:
            break                      # além do buffer — fica pro próximo run
        pa = when.strftime("%Y-%m-%dT%H:%M:%SZ")
        tomados.add(pa)
        cursor = proximo_slot(when, len(state["scheduled"]))

        # já existe vídeo subido (seed) → só agenda
        if nnnn in SEEDED:
            print(f"  🗓️  {nnnn} (já subido) → {pa}")
            if not args.dry_run:
                schedule_existing(env, SEEDED[nnnn], pa, token)
                state["scheduled"][nnnn] = {"videoId": SEEDED[nnnn], "publishAt": pa}
            continue

        # precisa estar renderizado E fresco (mp4 mais novo que os CTAs fixos)
        if not video_fresh(s3, nnnn, cutoff):
            to_render.append(nnnn)
            print(f"  ⏳ {nnnn} → {pa} (SEM RENDER FRESCO — pula neste run)")
            continue

        if uploads >= args.max:
            print(f"  ⛔ {nnnn} → {pa} (cota do run atingida, fica pro próximo)")
            continue

        # ⚠️ Conta TENTATIVA, não sucesso (corrigido 24/08).
        # A cota do YouTube (1600 unidades por upload) é gasta na TENTATIVA, e o
        # vídeo pode ter subido mesmo quando o script devolve erro — era o caso
        # da capa: o upload ia, o set_thumbnail estourava, o script morria.
        # Como `uploads` só crescia no sucesso, o teto do run NUNCA chegava: o
        # laço seguia pro próximo sermão e repetia. Foi assim que a inauguração
        # do Moody deixou 7 uploads órfãos numa tacada.
        # Teto de segurança que só conta acerto não é teto de segurança.
        uploads += 1
        print(f"  ⬆️  {nnnn} → agenda pra {pa}")
        if not args.dry_run:
            r = subprocess.run(
                ["docker", "run", "--rm", "--env-file", "/srv/factorio/.env",
                 "-v", "/srv/factorio/data/public:/app/public",
                 "-v", "/srv/factorio/data/hybrid:/app/_hybrid",
                 "-v", "/app/_factorio/remotion/publish_sermon.py:/app/publish_sermon.py",
                 "-v", "/app/_factorio/remotion/publish_youtube.py:/app/publish_youtube.py",
                 # MINA: canais.py também precisa entrar no container, senão o
                 # publish_sermon lá dentro cai no default e publica no canal errado.
                 "-v", "/app/_factorio/remotion/canais.py:/app/canais.py",
                 "factorio-render:v5", "python3", "-u", "publish_sermon.py",
                 "--canal", C["slug"],
                 "--sermon", str(int(nnnn)), "--publish-at", pa],
                capture_output=True, text=True)
            out = r.stdout + r.stderr
            # extrai o videoId (11 chars) — regex evita colar lixo do JSON (ex: VID"})
            import re as _re
            vid = ""
            for m in _re.finditer(r"youtu\.be/([A-Za-z0-9_-]{11})", out):
                vid = m.group(1)
            if r.returncode == 0 and vid:
                state["scheduled"][nnnn] = {"videoId": vid, "publishAt": pa}
                ok += 1
                print(f"     ✅ https://youtu.be/{vid}")
            else:
                # Se saiu um videoId, o vídeo SUBIU mesmo com o script quebrando
                # depois. Registrar aqui é o que impede o próximo run de subir
                # de novo o mesmo sermão (o órfão que ninguém vê).
                if vid:
                    state["scheduled"][nnnn] = {"videoId": vid, "publishAt": pa,
                                                "parcial": True}
                    print(f"     ⚠️  subiu ({vid}) mas o script falhou DEPOIS — "
                          f"registrado como parcial pra não re-subir")
                print(f"     ❌ falhou: {out[-300:]}")

    if not args.dry_run:
        s3.put_object(Bucket=BUCKET, Key=STATE_KEY,
                      Body=json.dumps(state, indent=2).encode(), ContentType="application/json")

    falhas = uploads - ok if not args.dry_run else 0
    print(f"\n🏁 agendados neste run: {ok}"
          + (f" | ❌ FALHARAM: {falhas}" if falhas else "")
          + f" | total agendado: {len(state['scheduled'])}")
    if to_render:
        print(f"⚠️  precisam renderizar (rode o batch render): {' '.join(to_render[:20])}")


if __name__ == "__main__":
    main()
