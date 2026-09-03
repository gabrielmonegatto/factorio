#!/usr/bin/env python3
"""
novo_canal.py — o BERÇÁRIO: abre um canal Treasures novo com um comando.

## Por que existe

Pedido do Gabriel em 27/08/2026: "porque não montamos uma automação pra ir
minerando e criando o que dá pra criar de forma automatizada em vez de você
ficar criando na mão a porra toda?". Ele tem razão: o molde foi provado duas
vezes (Moody, Maclaren) e replicar molde é trabalho de código, não de sessão.

## O que isto É e o que NÃO é

É um script determinístico e idempotente. NÃO é agente: nenhuma IA decide nada
aqui. Ele encadeia peças que já existem e param nas mesmas leis de sempre:

  1. DESCOBRIR  página de autor do CCEL, probe HTTP em cada obra (via VPS,
                porque o bundle de CAs do Windows do Gabriel recusa o ccel.org)
  2. REGISTRAR  obras verificadas entram no D1 como `resolved`
  3. MINERAR    scripts/mining/mine.mjs (o seletor de nível já sabe descer)
  4. CONFIG     entrada nova no canais.py a partir do template Treasures
  5. CTAs       intro/final gravados na voz do canal e subidos pro R2
  6. FILA       narrar_sermao --enfileirar + cron de PRÉ-ESTREIA na VPS
                (narrar + copy; produtor e agendador só entram no
                 esteira_canal.sh ligar, quando houver assets e credenciais)
  7. CHECKLIST  imprime o que sobrou pra humano (gates do Gabriel)

Rodar duas vezes não duplica nada: cada etapa olha o estado real antes de agir.

## Vozes

Decisão do Gabriel (27/08): repetir voz entre canais é aceitável, resultado
acima de preciosismo. O pool abaixo atribui primeiro as vozes livres; esgotou,
recicla. `--voz` na chamada vence o pool.

Uso:
  python scripts/novo_canal.py --slug murray --pregador "Andrew Murray" \
      --ccel murray --cadencia 0.5
  python scripts/novo_canal.py --slug murray ... --etapas descobrir   # só olhar
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(HERE, ".."))
CANAIS_PY = os.path.join(RAIZ, "remotion", "canais.py")

ACCOUNT = "dca6b1af1352f500d6eabe544b9222a3"
MINING_DB = "b08c9fae-3692-409a-aebd-e9630ca66f1d"
VPS = "root@167.233.236.209"
CHAVE = os.path.expanduser("~/.ssh/id_ed25519_factorio")

# Ordem de preferência; repetição liberada quando esgotar (decisão de 27/08).
POOL_VOZES = ["bm_daniel", "bm_fable", "am_michael", "am_echo", "am_eric",
              "am_liam", "am_fenrir", "am_puck",
              "bm_lewis", "bm_george", "am_adam", "am_onyx"]


def env_local():
    e = {}
    for line in open(os.path.join(RAIZ, ".env"), encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "").strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            e.setdefault(k, v)
    return e


def d1(sql, params=None):
    corpo = json.dumps({"sql": sql, "params": params or []}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/d1/database/{MINING_DB}/query",
        data=corpo, method="POST",
        headers={"Authorization": "Bearer " + env_local()["CLOUDFLARE_API_TOKEN"],
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            j = json.loads(r.read())
    except urllib.error.HTTPError as e:
        # O corpo do erro é onde a Cloudflare diz o MOTIVO. Sem isto, um 400
        # vira "Bad Request" pelado e o diagnóstico vira adivinhação (30/08).
        corpo = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"❌ D1 HTTP {e.code}: {corpo}\n   sql: {sql[:120]}")
    if not j.get("success"):
        raise SystemExit(f"❌ D1: {json.dumps(j.get('errors'))[:250]}")
    return j["result"][0].get("results") or []


def ssh(cmd, timeout=900):
    r = subprocess.run(["ssh", "-i", CHAVE, "-o", "StrictHostKeyChecking=no", VPS, cmd],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 and not r.stdout.strip():
        raise SystemExit(f"❌ ssh rc={r.returncode}: {r.stderr[:300]}")
    return r.stdout


# ── 1. DESCOBRIR ───────────────────────────────────────────────────────────
def descobrir_ccel(autor_ccel):
    """Página de autor -> slugs -> probe do .xml de cada obra.

    ⚠️ A página lista as obras como /ccel/<autor>/<slug>/<slug> (slug DOBRADO),
    mas o ThML mora em /ccel/<autor>/<slug>.xml (slug ÚNICO). Errar isso dá 404
    em tudo, foi a primeira coisa que quebrou no Maclaren.
    O probe roda NA VPS: o Python local do Windows recusa o TLS do ccel.org.
    """
    print(f"🔎 descobrindo obras de ccel.org/ccel/{autor_ccel} ...")
    saida = ssh(
        f"curl -sS -L https://ccel.org/ccel/{autor_ccel} -o /tmp/nc.html && "
        f"grep -oE 'href=\"https://ccel.org/ccel/{autor_ccel}/[a-z0-9_]+/' /tmp/nc.html "
        f"| sed -E 's#.*/{autor_ccel}/([a-z0-9_]+)/#\\1#' | sort -u | while read w; do "
        f"  code=$(curl -sS -L https://ccel.org/ccel/{autor_ccel}/$w.xml -o /tmp/nc.xml -w '%{{http_code}}'); "
        f"  tit=$(grep -oP '(?<=<DC.Title>)[^<]*' /tmp/nc.xml | head -1); "
        f"  sz=$(stat -c%s /tmp/nc.xml); "
        f"  echo \"$w|$code|$sz|$tit\"; done")
    obras = []
    for linha in saida.strip().splitlines():
        partes = linha.split("|", 3)
        if len(partes) != 4:
            continue
        slug, code, sz, titulo = partes
        titulo = titulo.strip() or slug
        if code != "200" or int(sz) < 20000:
            print(f"   ⚠️  {slug}: HTTP {code}, {sz} bytes. FICA DE FORA.")
            continue
        obras.append({"slug": slug, "titulo": titulo, "bytes": int(sz),
                      "url": f"https://ccel.org/ccel/{autor_ccel}/{slug}"})
        print(f"   ✅ {slug:22} {int(sz)//1024:5}k  {titulo[:58]}")
    if not obras:
        raise SystemExit("❌ nenhuma obra passou no probe. Autor errado no CCEL?")
    print(f"   {len(obras)} obras verificadas")
    return obras


# ── 2. REGISTRAR ───────────────────────────────────────────────────────────
def registrar(obras, autor_nome, era):
    urls_existentes = {w["source_url"] for w in
                       d1("SELECT source_url FROM works WHERE author = ?", [autor_nome])}
    novos = 0
    for o in obras:
        if o["url"] in urls_existentes:
            continue
        d1("""INSERT INTO works (title, author, era, priority, source_kind, source_url,
                resolve_score, resolve_note, status, chapters_n, chars_n, attempts, updated_at)
              VALUES (?, ?, ?, 2, 'ccel', ?, 1.0,
                'berçário novo_canal: URL verificada por probe HTTP', 'resolved',
                0, 0, 0, datetime('now'))""",
           [o["titulo"], autor_nome, era, o["url"]])
        novos += 1
    print(f"📚 registradas {novos} obras novas ({len(obras) - novos} já existiam)")


# ── 3. MINERAR ─────────────────────────────────────────────────────────────
def minerar():
    """mine.mjs pega tudo que está `resolved`; as recém-registradas são as únicas."""
    r = subprocess.run(["node", os.path.join(RAIZ, "scripts", "mining", "mine.mjs"),
                        "--limite", "60", "--fonte", "ccel"],
                       cwd=RAIZ, capture_output=True, text=True, timeout=3600)
    print(r.stdout[-1200:] if r.stdout else r.stderr[-400:])
    if "falhas" in r.stdout and " 0 falhas" not in r.stdout:
        print("⚠️  houve falha de mineração acima. Conferir antes de seguir.")


# ── 4. CONFIG ──────────────────────────────────────────────────────────────
TEMPLATE = '''    # ─────────────────────────────────────────────────────────────────────
    # Canal Treasures gerado pelo BERÇÁRIO (scripts/novo_canal.py) em {data}.
    # ⬜ GATES DO GABRIEL: canal no YouTube -> verificar por TELEFONE ->
    #    auth_youtube.py ({env_prefix}_*) -> preencher youtube_channel_id ->
    #    coleção "{colecao}" na livraria. Sem o ID o publish ABORTA (guardião).
    "{slug}": {{
        "nome": "{nome}",
        "bucket": "mananciall",
        "prefix": "channels/channels_youtube/treasures_{slug}",
        "renders_prefix": "renders/{slug}",
        "state_key": "schedule/{slug}_schedule.json",
        "youtube_channel_id": "",
        "env_prefix": "{env_prefix}",
        "idioma": "en",
        "voz": "{voz}",
        "voz_speed": "0.9",
        "videos_por_dia": {cadencia},
        "morning_utc": 12,
        "evening_utc": 23,
        "warmup_days": 14,
        "buffer_days": 14,
        "max_uploads_per_run": 5,
        "chars_max": 55000,
        "cta_assets": ["_assets/introfixed.mp3", "_assets/finalfixed.mp3"],
        "cta_intro_texto": (
            "So take this opportunity to subscribe to the channel, turn on notifications, "
            "and visit our collection with the best books and writings by {pregador} "
            "to enrich your soul. Link in the description below. God bless you, and let us begin."),
        "cta_outro_texto": (
            "If you enjoyed this message, consider subscribing to the channel, turning on "
            "notifications, and visiting our collection with the best books and writings by "
            "{pregador} to enrich your soul. God bless you."),
        "pregador": "{pregador}",
        "autor_mineracao": "{autor_like}",
        "asr_modelo": "small.en",
        "pausa_frase_s": 0.75,
        "titulo_sufixo": " ({pregador})",
        "tags": "{tags}",
        "hashtags": "{hashtags}",
        "cta_livro": "{colecao}",
        "cta_texto": "📖 {pregador}'s books & writings: {{link}}",
        "colecao_titulo": "{colecao}",
        "link_label": "mananciall.org/go/{slug}",
        "redirect_base": "https://mananciall.org/go/{slug}?v=",
        "link_canal": "https://mananciall.org/go/{slug}treasures",
        "assets": None,                    # ⬜ busto e fundo ainda não gerados
    }},
'''


def vozes_em_uso():
    s = open(CANAIS_PY, encoding="utf-8").read()
    return re.findall(r'"voz":\s*"([a-z_]+)"', s)


def escolher_voz(pedida):
    if pedida:
        return pedida
    usadas = set(vozes_em_uso())
    for v in POOL_VOZES:
        if v not in usadas:
            return v
    return POOL_VOZES[0]      # esgotou: repete (decisão do Gabriel, 27/08)


def gerar_config(a, voz):
    s = open(CANAIS_PY, encoding="utf-8").read()
    if f'"{a.slug}": {{' in s:
        print(f"⏭️  canais.py já tem '{a.slug}'")
        return
    import datetime as dt
    ultimo = a.pregador.split()[-1].lower()
    entrada = TEMPLATE.format(
        data=dt.date.today().strftime("%d/%m/%Y"), slug=a.slug,
        nome=f"{a.pregador} Treasures", env_prefix=f"YT_{a.slug.upper()}",
        voz=voz, cadencia=a.cadencia, pregador=a.pregador,
        autor_like=f"%{a.pregador.split()[-1]}%",
        colecao=f"The Best of {a.pregador}",
        tags=f"{a.pregador},{ultimo},sermon,christian,gospel,preaching",
        hashtags=f"#{a.pregador.replace(' ', '')} #Christian #Gospel #Faith")
    marcador = '}\n\nPADRAO = "spurgeon"'
    assert marcador in s, "âncora do canais.py mudou; berçário precisa de ajuste"
    s = s.replace(marcador, entrada + marcador, 1)
    open(CANAIS_PY, "w", encoding="utf-8", newline="").write(s)
    r = subprocess.run([sys.executable, "-c",
                        f"import sys; sys.path.insert(0, r'{os.path.join(RAIZ, 'remotion')}'); "
                        f"import canais; c = canais.get('{a.slug}'); print(c['nome'], c['voz'])"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"❌ canais.py quebrou depois da inserção:\n{r.stderr[-400:]}")
    print(f"⚙️  canais.py: '{a.slug}' criado e importável ({r.stdout.strip()})")


# ── 5. CTAs ────────────────────────────────────────────────────────────────
def gravar_ctas(a, voz):
    """Grava intro/final com a voz do canal e sobe pro R2 do canal."""
    prefixo = f"channels/channels_youtube/treasures_{a.slug}"
    ja = ssh(f"cd /app/_factorio/remotion && python3 - <<'PY'\n"
             f"import narrar_sermao as N\n"
             f"env = N.load_env(); s3 = N.s3c(env)\n"
             f"try:\n"
             f"    s3.head_object(Bucket='mananciall', Key='{prefixo}/_assets/introfixed.mp3')\n"
             f"    print('EXISTE')\n"
             f"except Exception:\n"
             f"    print('FALTA')\n"
             f"PY")
    if "EXISTE" in ja:
        print("⏭️  CTAs já estão no R2")
        return
    sys.path.insert(0, os.path.join(RAIZ, "remotion"))
    import canais
    c = canais.get(a.slug)
    remoto = f"/srv/factorio/data/ctas/{a.slug}"
    script = (
        f"mkdir -p {remoto} && cd {remoto} && "
        f"cat > intro.txt <<'TXT'\n{c['cta_intro_texto']}\nTXT\n"
        f"cat > final.txt <<'TXT'\n{c['cta_outro_texto']}\nTXT\n"
        f"for p in intro final; do "
        f"docker run --rm --name factorio_tts_cta_{a.slug}_$p --memory=8g --cpus=5 "
        f"-v {remoto}:/data -v /srv/factorio/hfcache:/cache factorio-tts "
        f"--input /data/$p.txt --output /data/$p.wav --voice {voz} --speed 0.9 "
        f"--split sentence --silence 0.75 --trim >/dev/null 2>&1; "
        f"docker run --rm -v {remoto}:/data --entrypoint ffmpeg factorio-tts "
        f"-y -loglevel error -i /data/$p.wav -ac 1 -b:a 96k "
        # 1,7s de silêncio na cauda: é a 'pausa natural' pós-CTA do Spurgeon,
        # medida e aprovada de ouvido (02/09). O --trim do Kokoro tira a cauda;
        # sem este pad o sermão atropela o CTA. Ver ajustar_cauda_cta.py.
        f"-af apad=pad_dur=1.7 /data/$p.mp3; done && "
        f"cd /app/_factorio/remotion && python3 - <<'PY'\n"
        f"import narrar_sermao as N\n"
        f"env = N.load_env(); s3 = N.s3c(env)\n"
        f"s3.upload_file('{remoto}/intro.mp3', 'mananciall', '{prefixo}/_assets/introfixed.mp3')\n"
        f"s3.upload_file('{remoto}/final.mp3', 'mananciall', '{prefixo}/_assets/finalfixed.mp3')\n"
        f"print('CTAs no R2')\n"
        f"PY")
    print(f"🎙️  gravando CTAs ({voz}) e subindo pro R2 ...")
    print("   " + ssh(script, timeout=1200).strip().splitlines()[-1])


# ── 6. FILA + cron de pré-estreia ─────────────────────────────────────────
def enfileirar(a):
    # o deploy já aconteceu na etapa config; aqui a VPS só monta a fila
    print(ssh("cd /app/_factorio/remotion && "
              f"python3 narrar_sermao.py --canal {a.slug} --enfileirar 2>&1 | tail -2").strip())
    # minuto do preparo espalhado por canal: hora cheia é de quem narra
    minuto = 5 + (sum(ord(ch) for ch in a.slug) % 10) * 5
    ssh(f"cat > /etc/cron.d/factory-{a.slug}-preestreia <<'CRON'\n"
        f"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
        f"SHELL=/bin/bash\n"
        f"# PRE-ESTREIA (berçário): só narrar + copy. O producer e o agendador\n"
        f"# entram com 'esteira_canal.sh ligar {a.slug}', que substitui este arquivo.\n"
        f"0 */4 * * * root cd /app/_factorio/remotion && flock -n /tmp/narrar_{a.slug}.lock "
        f"python3 narrar_sermao.py --canal {a.slug} --limite 20 --minutos 200 "
        f">> /var/log/factory_narrar_{a.slug}.log 2>&1\n"
        f"{minuto} * * * * root cd /app/_factorio/remotion && flock -n /tmp/prep_{a.slug}.lock "
        f"bash -c 'python3 generate_marketing.py --canal {a.slug} --all --limit 6 && "
        f"python3 narrate_marketing.py --canal {a.slug} --all --limit 6' "
        f">> /var/log/factory_prep_{a.slug}.log 2>&1\n"
        f"CRON")
    print(f"⏱️  cron de pré-estreia instalado (narrar 0 */4, preparo min {minuto})")


def checklist(a):
    print(f"""
────────────────────────────────────────────────────────
✅ máquina rodando pro canal '{a.slug}'. FALTA (humano):
   1. [Gabriel] criar canal YouTube "{a.pregador} Treasures"
   2. [Gabriel] verificar por TELEFONE (youtube.com/verify) ANTES de publicar
   3. [Gabriel+eu] auth_youtube.py -> YT_{a.slug.upper()}_* no .env
   4. [eu] preencher youtube_channel_id no canais.py
   5. [eu] busto (Gemini) -> aprovação do Gabriel -> assets no R2
   6. [Gabriel] coleção "The Best of {a.pregador}" na livraria
   7. [eu] esteira_canal.sh ligar {a.slug}  (produtor + agendador)
────────────────────────────────────────────────────────""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--pregador", required=True, help='ex: "Andrew Murray"')
    ap.add_argument("--ccel", required=True, help="slug do autor no CCEL, ex: murray")
    ap.add_argument("--cadencia", default="1.0", help="videos_por_dia: 0.5, 1 ou 2")
    ap.add_argument("--voz", default=None, help="força uma voz; padrão: pool")
    ap.add_argument("--era", default="vitoriana")
    ap.add_argument("--etapas", default="descobrir,registrar,minerar,config,cta,fila",
                    help="quais rodar, em ordem")
    a = ap.parse_args()
    etapas = a.etapas.split(",")

    obras = descobrir_ccel(a.ccel) if "descobrir" in etapas else []
    if "registrar" in etapas:
        registrar(obras, a.pregador, a.era)
    if "minerar" in etapas:
        minerar()
    voz = escolher_voz(a.voz)
    if "config" in etapas:
        gerar_config(a, voz)
        # ⚠️ "bash" pelado no Windows resolve pro bash do WSL, que nem existe
        # configurado nesta máquina: o deploy falhava mudo ("execvpe failed")
        # e a VPS ficava sem conhecer o canal recém-criado. Git Bash explícito.
        # ⚠️ NÃO chamar o deploy_vps.sh daqui. Já tentei, duas mortes diferentes:
        # 1) "bash" pelado resolve pro WSL e morre em execvpe;
        # 2) via Git Bash explícito, o ssh aninhado do passo "conferindo"
        #    (docker run dentro de ssh dentro de bash dentro de subprocess)
        #    pendura sem stdin/tty e estoura timeout DEPOIS de já ter sincronizado.
        # O que a VPS precisa AGORA é um arquivo: o canais.py com o canal novo.
        # scp direto é atômico e sem pipe aninhado. O deploy completo continua
        # sendo o caminho oficial e roda na próxima rodada normal da sessão.
        r = subprocess.run(
            ["scp", "-i", CHAVE, "-o", "StrictHostKeyChecking=no",
             CANAIS_PY, f"{VPS}:/app/_factorio/remotion/canais.py"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise SystemExit(f"❌ scp do canais.py falhou: {r.stderr[:200]}")
        conferido = ssh(f"cd /app/_factorio/remotion && python3 -c "
                        f"\"import canais; print(canais.get('{a.slug}')['nome'])\"").strip()
        print(f"🚚 canais.py na VPS confere: {conferido}")
        print("   (rodar `bash scripts/deploy_vps.sh --sem-imagem` na próxima folga)")
    if "cta" in etapas:
        gravar_ctas(a, voz)
    if "fila" in etapas:
        enfileirar(a)
    checklist(a)


if __name__ == "__main__":
    main()
