#!/usr/bin/env python3
"""
narrar_sermao.py — o elo que faltava: texto minerado ➜ pasta de sermão no R2.

## O buraco que isto tapa

A esteira tinha seis etapas vivas e uma órfã. Minerar põe o TEXTO no D1; o
`build_job` espera encontrar no R2 uma pasta `NNNN_-_slug/` com o áudio e a
transcrição. Quem fazia essa ponte no Spurgeon vivia em `scratch/`, lia de um
Postgres local que a fábrica aposentou e escrevia num caminho que não existe
mais. Ou seja: o Spurgeon publica de um acervo narrado no passado por um
script que não roda mais, e canal novo não tinha como nascer.

## O que ele produz (contrato com o build_job, não invente)

    <prefix>/NNNN_-_slug/sermon_NNNN.mp3   ← `pick_first` casa r"^sermon_\\d+\\.(wav|mp3)$"
    <prefix>/NNNN_-_slug/transcript.json   ← precisa de `text` e `words[]` em MILISSEGUNDOS

MP3 e não WAV porque o acervo já tem os dois e o build_job preserva a extensão:
o mesmo sermão dá 69MB em wav e ~20MB em mp3. Vezes 77 capítulos, isso é 3,5GB
de R2 e de download dentro do container de render.

## Onde roda

Na VPS, que é onde mora o container do Kokoro. Não tente rodar isto no Windows:
ele chama `docker run factorio-tts`.

## Estado no banco, não na pasta

A fila vive na tabela `sermons` do D1 de mineração. É ela que decide qual
capítulo vira qual número de sermão, e é ela que torna o script idempotente:
matar no meio e rodar de novo continua de onde parou, sem duplicar nem pular.

Uso:
  python3 narrar_sermao.py --canal moody --enfileirar          # só monta a fila
  python3 narrar_sermao.py --canal moody --limite 1            # narra 1 e para
  python3 narrar_sermao.py --canal moody --limite 99           # o lote todo
  python3 narrar_sermao.py --canal moody --so 3 --forcar       # refaz o sermão 3
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request

import boto3
from botocore.config import Config

import canais
import vaga_cpu
import docker_nomeado

ACCOUNT = "dca6b1af1352f500d6eabe544b9222a3"
MINING_DB = "b08c9fae-3692-409a-aebd-e9630ca66f1d"
TTS_IMAGE = os.environ.get("TTS_IMAGE", "factorio-tts")
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "/srv/factorio/data/narrar" if os.path.isdir("/srv/factorio/data") else os.path.join(HERE, "_narrar")
# Teto de CPU: a narração divide a máquina com os produtores de render.
#
# ⚠️ Teto por processo NÃO É teto de máquina, e essa confusão custou caro.
# Aqui pedia 8 e cada produtor pedia 8; com dois canais ligados a conta dava 32
# numa VPS de 16 vCPU. O sistema não recusa, ele engasga: em 25/08, com load 20,
# um sermão que levava 1.400s levou 9.700s.
# Agora quem decide o número é o `vaga_cpu`, que olha a máquina inteira.
CPUS = os.environ.get("NARRAR_CPUS") or vaga_cpu.CPUS
# Só pra nomear o container do ASR (transcrever_local não recebe o canal).
CANAL_ATUAL = "?"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sermons (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  canal      TEXT NOT NULL,
  numero     INTEGER NOT NULL,
  work_id    INTEGER NOT NULL,
  chapter_id INTEGER NOT NULL,
  titulo     TEXT NOT NULL,
  slug       TEXT NOT NULL,
  chars      INTEGER NOT NULL DEFAULT 0,
  obra       TEXT,
  cap_n      INTEGER,
  status     TEXT NOT NULL DEFAULT 'fila',   -- fila | narrado | falhou
  dur_s      REAL,
  audio_key  TEXT,
  erro       TEXT,
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE (canal, numero),
  UNIQUE (canal, chapter_id)
);
"""


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


def d1(env, sql, params=None):
    """D1 pela API HTTP com parâmetro vinculado: texto de livro entra sem
    escapar aspas na mão (o caminho do `wrangler --command` quebraria)."""
    corpo = json.dumps({"sql": sql, "params": params or []}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/d1/database/{MINING_DB}/query",
        data=corpo, method="POST",
        headers={"Authorization": "Bearer " + env["CLOUDFLARE_API_TOKEN"],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read())
    if not j.get("success"):
        raise SystemExit(f"❌ D1: {json.dumps(j.get('errors'))[:300]} :: {sql[:110]}")
    return j["result"][0].get("results") or []


def s3c(env):
    return boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
                        config=Config(signature_version="s3v4"), region_name="auto")


def slugificar(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return re.sub(r"_+", "_", s)[:60] or "sermon"


# Marcas de PÁGINA DE ROSTO e de COLOFÃO. Não cortam sozinhas: decidem SE vale
# cortar. O corte em si é por "já virou prosa?", que não depende de enumerar
# toda frase de copyright que existe no mundo.
GRAFICA = re.compile(
    r"copyright|act of congress|all rights reserved|librarian of congress|"
    r"publishers?\s+of|\bpublishers\b|printed (and bound )?by|press of|colportage|"
    r"revell|scribner|harper\s*&|entered according|paper covers|postpaid|"
    # crédito de quem digitalizou pro Gutenberg: "Produced by Keith G. Richardson"
    r"produced by|transcriber|proofreading team|"
    # catálogo da editora: encadernação, formato, preço, "Ask for descriptive folder"
    r"\bcloth\b|12mo|16mo|\bcents\b|descriptive folder|\bBy Rev\.", re.I)
PROSA_MIN = 25       # palavras. Linha de folha de rosto não chega perto disso.
# Janela proporcional, não fixa: em alguns livros o miolo de rosto + sumário
# passa de 22 parágrafos, e a janela curta desistia e deixava tudo passar.
# 40% é seguro porque folha de rosto nunca é 40% de um capítulo de verdade.
def _janela(paras):
    return max(22, min(60, int(len(paras) * 0.4)))


def _prosa(p):
    return len(p.split()) >= PROSA_MIN


def cortar_bordas(paras):
    """Tira folha de rosto e catálogo da editora, que não são sermão.

    Na primeira rodada o sermão 0001 do Moody abria narrando "Fleming H. Revell
    Company, Chicago New York Toronto, Publishers of Evangelical Literature" e
    seguia pelo registro de copyright. Um outro virou 30 minutos de ANÚNCIO de
    livros da editora.

    Só engata quando há marca de gráfica na ponta, então o versículo curto que
    abre um sermão de verdade ("Except a man be born again...") fica em paz.
    """
    # `_limpo`, e não só `_prosa`: o registro de copyright antigo é uma frase
    # LONGA ("Entered according to act of Congress, in the year 1877, by...")
    # e passava no teste de prosa, travando o corte no primeiro parágrafo.
    def _limpo(p):
        return _prosa(p) and not GRAFICA.search(p)

    j = _janela(paras)
    if any(GRAFICA.search(p) for p in paras[:j]):
        corte = next((i for i, p in enumerate(paras[:j]) if _limpo(p)), j)
        paras = paras[corte:]
    j = _janela(paras)
    if any(GRAFICA.search(p) for p in paras[-j:]):
        fim = next((i for i in range(len(paras) - 1, max(-1, len(paras) - j - 1), -1)
                    if _limpo(paras[i])), None)
        if fim is not None:
            paras = paras[:fim + 1]
    return paras


CAP = re.compile(r"^\s*(chapter|sermon|part|book|section)\s+([ivxlcdm]+|\d+)\b[.:]?\s*", re.I)
PARTE = re.compile(r"\s*\((\d+/\d+)\)\s*$")
LIXO = " .,;:\"'`-–—"


def limpar_titulo(bruto, paras, obra=None, numero=None):
    """'CHAPTER I.. "_LOVE THAT PASSETH KNOWLEDGE_."' → 'Love That Passeth Knowledge'.

    Esse texto vai pro título do vídeo e pro nome da pasta no R2, então marcação
    de itálico e número de página do sumário não podem sobreviver. Quando sobra
    só "CHAPTER II", o nome real está na primeira linha curta do corpo: foi
    assim que o livro foi diagramado.
    """
    t = (bruto or "").strip()
    parte = PARTE.search(t)
    if parte:
        t = PARTE.sub("", t)
    t = CAP.sub("", t).replace("_", "").replace("*", "")
    t = re.sub(r"\s{2,}\d{1,4}\s*$", "", t).strip(LIXO)
    if len(t) < 4 and paras:
        cand = paras[0].replace("_", "").replace("*", "")
        cand = re.sub(r"\s{2,}\d{1,4}\s*$", "", cand).strip(LIXO)
        if 3 < len(cand) < 80:
            t = cand
    if len(t) < 5 and obra:
        # "CHAPTER IX" sem subtítulo e com corpo em prosa: melhor "The Way to
        # God, Chapter 9" do que o genérico "Sermon" repetido em 4 vídeos.
        t = f"{obra}, Chapter {numero}" if numero else obra
    if t and (t.isupper() or t.islower()):
        t = t.title()
    t = t or "Sermon"
    return f"{t} ({parte.group(1)})" if parte else t


def preparar_texto(bruto):
    """Tira do texto o que é marca de página, não fala.

    O corpo minerado é "markdown-ish" e vem de digitalização: sobra nota de
    transcritor entre colchetes, marcação de itálico com asterisco e número de
    nota de rodapé grudado na palavra. Nada disso deve virar som.
    """
    t = re.sub(r"\[[^\]]{0,120}\]", " ", bruto)      # [Illustration: ...], [1], [Transcriber's Note]
    t = re.sub(r"\{[^}]{0,120}\}", " ", t)
    t = t.replace("*", "").replace("_", " ").replace("=", " ")
    t = re.sub(r"[“”]", '"', t).replace("’", "'").replace("‘", "'")
    t = re.sub(r"-{2,}", ", ", t)                     # travessão datilografado vira respiro
    t = re.sub(r"[ \t]+", " ", t)
    # parágrafo de 1 ou 2 palavras é resíduo de cabeçalho de página
    paras = [p.strip() for p in t.split("\n\n")]
    return [p for p in paras if len(p.split()) > 2]


def folego_dias(env, s3, c):
    """Dias de estoque à frente: (narrados - publicados) / cadência.

    É o que torna a esteira INTELIGENTE sem orquestrador (pedido do Gabriel,
    01/09): cada canal mede o próprio fôlego e cede vaga sozinho. Spurgeon com
    ~80 dias de estoque não tem por que disputar CPU com a Bíblia que tem zero.
    A prioridade EMERGE, canal continua ilha: quebrou um, nada mais quebra.
    """
    narrados = d1(env, "SELECT COUNT(*) n FROM sermons WHERE canal=? AND status='narrado'",
                  [c["slug"]])[0]["n"]
    try:
        est = json.loads(s3.get_object(Bucket=c["bucket"],
                                       Key=c["state_key"])["Body"].read())
        publicados = len(est.get("scheduled", {}))
    except Exception:
        publicados = 0                      # canal ainda não estreou: fome máxima
    cadencia = float(c.get("videos_por_dia") or 1.0)
    return max(0.0, (narrados - publicados) / cadencia)


def regime_do_folego(folego, limite, minutos):
    """Traduz fôlego em apetite. Os args do cron viram TETO, nunca piso."""
    if folego < 15:
        return limite, minutos, "FOME (estoque < 15 dias): apetite cheio"
    if folego < 45:
        return min(limite, 6), min(minutos or 60, 60), "confortável: apetite reduzido"
    return min(limite, 1), min(minutos or 20, 20), "farto (45+ dias): só goteja e cede as vagas"


def enfileirar(env, c):
    """Capítulo minerado ainda sem sermão vira linha na fila, em ordem de obra."""
    d1(env, SCHEMA)
    caps = d1(env, """
        SELECT ch.id AS chapter_id, ch.work_id, ch.number, ch.title, ch.chars, w.title AS obra
        FROM chapters ch JOIN works w ON w.id = ch.work_id
        WHERE w.author LIKE ? AND w.status = 'mined'
        ORDER BY ch.work_id, ch.number
    """, [c["autor_mineracao"]])
    ja = {r["chapter_id"] for r in
          d1(env, "SELECT chapter_id FROM sermons WHERE canal = ?", [c["slug"]])}
    prox = (d1(env, "SELECT COALESCE(MAX(numero), 0) AS m FROM sermons WHERE canal = ?",
               [c["slug"]])[0]["m"]) + 1

    novos = 0
    for ch in caps:
        if ch["chapter_id"] in ja:
            continue
        titulo = (ch["title"] or ch["obra"] or "Sermon").strip()
        d1(env, """INSERT INTO sermons (canal, numero, work_id, chapter_id, titulo,
                       slug, chars, obra, cap_n) VALUES (?,?,?,?,?,?,?,?,?)""",
           [c["slug"], prox, ch["work_id"], ch["chapter_id"], titulo,
            slugificar(titulo), ch["chars"], ch["obra"], ch["number"]])
        prox += 1
        novos += 1
    return novos, len(caps)


def narrar(c, texto, wav):
    """Chama o container do Kokoro com a receita de voz DO CANAL.

    `--trim` é o que impede a narração de soar arrastada: sem ele o Kokoro cola
    ~1,1s no fim de cada pedaço e o intervalo real vira ~2,1s. Medido em 22/08:
    com trim + 0,75s o intervalo fica em 0,83s e o áudio encolhe 25%.

    `--cpus` sem limite de propósito: o `--cpus=1.5` do narrate_marketing custa
    8x o tempo de parede (RTF 3,51 contra 0,42 com os 16 vCPU). Num hook de 25s
    não importava; num sermão de 45min importa muito.
    """
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    txt = wav.replace(".wav", ".txt")
    open(txt, "w", encoding="utf-8").write(texto)
    d = os.path.dirname(os.path.abspath(wav))
    docker_nomeado.rodar(
        "tts", c["slug"], os.path.basename(wav).replace(".wav", ""),
        ["--memory=8g", f"--cpus={CPUS}",
         "-v", f"{d}:/data", "-v", "/srv/factorio/hfcache:/cache"],
        TTS_IMAGE,
        ["--input", f"/data/{os.path.basename(txt)}",
         "--output", f"/data/{os.path.basename(wav)}",
         "--voice", c["voz"], "--speed", str(c["voz_speed"]),
         "--split", "sentence", "--silence", str(c.get("pausa_frase_s", 0.75)),
         "--trim", "--progresso", "200"])
    os.remove(txt)


def para_mp3(wav, mp3):
    """64k mono: é narração falada, não música. Corta o arquivo em ~3,5x."""
    d = os.path.dirname(os.path.abspath(wav))
    subprocess.run([
        "docker", "run", "--rm", "-v", f"{d}:/data", "--entrypoint", "ffmpeg", TTS_IMAGE,
        "-y", "-loglevel", "error", "-i", f"/data/{os.path.basename(wav)}",
        "-ac", "1", "-b:a", "64k", f"/data/{os.path.basename(mp3)}",
    ], check=True)


ASR_IMAGE = os.environ.get("ASR_IMAGE", "factorio-asr")


def transcrever_local(caminho, modelo="small.en", idioma="en"):
    """faster-whisper na CPU da própria VPS. É o caminho padrão.

    Medido em 22/08 no mesmo sermão de 33min, sempre contra o TEXTO FONTE que
    mandamos narrar, que é a única verdade disponível:

      AssemblyAI          US$ 0,15/h   minutos   99,2%    0 fora de ordem
      Groq whisper-turbo  US$ 0,04/h        3s   98,9%   64 fora de ordem
      small.en aqui       grátis          284s   98,8%    0 fora de ordem

    Empata com a API paga, devolve timing em ordem e não custa nada. Mandar 53
    horas de áudio pra fora pra ganhar 0,1% de fidelidade não se paga.
    """
    # splitext e não replace(".mp3"): o hook do narrate_marketing chega como
    # .wav, o replace não casava, `saida` ficava IGUAL a `caminho`, o container
    # escrevia o JSON por cima do áudio e o os.remove no fim apagava o áudio.
    saida = os.path.splitext(caminho)[0] + ".words.json"
    d = os.path.dirname(os.path.abspath(caminho))
    docker_nomeado.rodar(
        "asr", CANAL_ATUAL, os.path.basename(caminho).rsplit(".", 1)[0],
        ["--memory=12g", f"--cpus={CPUS}",
         "-v", f"{d}:/data", "-v", "/srv/factorio/hfcache:/cache"],
        ASR_IMAGE,
        ["--audio", f"/data/{os.path.basename(caminho)}",
         "--out", f"/data/{os.path.basename(saida)}",
         "--modelo", modelo, "--idioma", idioma])
    tr = json.load(open(saida, encoding="utf-8"))
    os.remove(saida)
    return tr


def transcrever(caminho, env, c):
    """Local por padrão. As APIs ficam como rede de segurança, nesta ordem."""
    if os.environ.get("ASR_REMOTO") != "1":
        try:
            return transcrever_local(caminho, c.get("asr_modelo", "small.en"),
                                     c.get("idioma", "en"))
        except Exception as e:
            print(f"     ⚠️ ASR local falhou ({str(e)[:90]}); tentando API", flush=True)
    if env.get("GROQ_API_KEY") and os.path.getsize(caminho) <= 24 * 1024 * 1024:
        return transcrever_groq(caminho, env["GROQ_API_KEY"])
    if not env.get("ASSEMBLYAI_API_KEY"):
        raise RuntimeError("ASR local falhou, arquivo grande pro Groq e sem AssemblyAI")
    return transcrever_assemblyai(caminho, env["ASSEMBLYAI_API_KEY"])


def endireitar(palavras):
    """Força os tempos a só andarem pra frente.

    O Whisper devolve ~1% das palavras com o início ANTES da anterior (80 a
    460ms, sempre em fronteira de segmento). Medido no sermão 0001: 64 de 5604.
    Parece pouco, mas a legenda desta esteira destaca PALAVRA POR PALAVRA, e
    tempo andando pra trás faz o destaque pular. O AssemblyAI não tem isso; é o
    preço de usar um motor 4x mais barato e 60x mais rápido.

    O conserto é o mínimo possível: empurra o início pra frente quando ele
    regride e garante fim depois do início. Sobreposição entre palavras
    vizinhas é normal na fala e fica como está.
    """
    ant = 0
    for w in palavras:
        if w["start"] < ant:
            w["start"] = ant
        if w["end"] <= w["start"]:
            w["end"] = w["start"] + 30
        ant = w["start"]
    return palavras


def transcrever_groq(caminho, chave):
    """Groq (whisper-large-v3-turbo), palavra a palavra. É o caminho padrão.

    Por que transcrever um áudio que NÓS sintetizamos e cujo texto já sabemos:
    o Kokoro não devolve alinhamento, e a legenda precisa do tempo de cada
    palavra. Sai mais barato pedir pra ASR do que construir alinhamento forçado.

    ⚠️ Eu tinha escrito aqui que o Groq não servia "porque tem teto de tamanho
    e o áudio tem 45 minutos", SEM medir. Errado: a 64kbps um sermão de 37min
    dá 17MB e o teto é 25MB. A diferença de preço não é pequena — US$ 0,04/h
    contra US$ 0,15/h do AssemblyAI, ou seja US$ 2 contra US$ 8 no acervo do
    Moody inteiro. Medir antes de escolher.

    Devolve no formato do AssemblyAI porque é ele que o resto da esteira lê:
    `words[].text` e tempos em MILISSEGUNDOS (o Groq responde em segundos).
    """
    limite = 24 * 1024 * 1024
    if os.path.getsize(caminho) > limite:
        raise RuntimeError(
            f"{os.path.getsize(caminho)//1024//1024}MB passa do teto de 25MB do Groq. "
            f"Baixe o bitrate do MP3 ou parta o áudio.")

    lim = "----" + os.urandom(16).hex()
    corpo = b""
    for campo, valor in (("model", "whisper-large-v3-turbo"),
                         ("response_format", "verbose_json"),
                         ("timestamp_granularities[]", "word"),
                         ("timestamp_granularities[]", "segment"),
                         ("language", "en")):
        corpo += (f"--{lim}\r\nContent-Disposition: form-data; name=\"{campo}\"\r\n\r\n"
                  f"{valor}\r\n").encode()
    corpo += (f"--{lim}\r\nContent-Disposition: form-data; name=\"file\"; "
              f"filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode()
    corpo += open(caminho, "rb").read() + f"\r\n--{lim}--\r\n".encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/audio/transcriptions", data=corpo, method="POST",
        headers={"Authorization": "Bearer " + chave,
                 "Content-Type": f"multipart/form-data; boundary={lim}",
                 # MINA: sem User-Agent proprio a borda da Cloudflare na frente
                 # do Groq responde 403 codigo 1010 (bloqueio de bot) ao
                 # User-Agent padrao do urllib. Mesma pegadinha do workers.dev.
                 "User-Agent": "factorio-narrador/1.0"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.loads(r.read())

    palavras = [{"text": w["word"].strip(),
                 "start": int(round(w["start"] * 1000)),
                 "end": int(round(w["end"] * 1000)),
                 "confidence": 1.0, "speaker": None}
                for w in (d.get("words") or []) if w.get("word", "").strip()]
    if not palavras:
        raise RuntimeError("Groq não devolveu palavras (timestamp_granularities ignorado?)")
    endireitar(palavras)
    return {"text": d.get("text", "").strip(),
            "words": palavras,
            "audio_duration": round(d.get("duration") or palavras[-1]["end"] / 1000, 2),
            "confidence": 1.0,
            "language_code": "en_us",
            "motor": "groq/whisper-large-v3-turbo"}


def transcrever_assemblyai(caminho, chave):
    """Reserva: aguenta arquivo grande, mas custa ~4x o Groq."""
    with open(caminho, "rb") as f:
        req = urllib.request.Request("https://api.assemblyai.com/v2/upload", data=f.read(),
                                     headers={"authorization": chave}, method="POST")
        with urllib.request.urlopen(req, timeout=900) as r:
            url = json.loads(r.read())["upload_url"]
    corpo = json.dumps({"audio_url": url, "punctuate": True, "format_text": True}).encode()
    req = urllib.request.Request("https://api.assemblyai.com/v2/transcript", data=corpo,
                                 headers={"authorization": chave, "content-type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        tid = json.loads(r.read())["id"]
    while True:
        req = urllib.request.Request(f"https://api.assemblyai.com/v2/transcript/{tid}",
                                     headers={"authorization": chave})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
        if d["status"] == "completed":
            return d
        if d["status"] == "error":
            raise RuntimeError(f"AssemblyAI: {d.get('error')}")
        time.sleep(10)


def processar(env, s3, c, s, forcar=False):
    nnnn = f"{s['numero']:04d}"
    pasta = f"{c['prefix']}/{nnnn}_-_{s['slug']}"
    mp3_key = f"{pasta}/sermon_{nnnn}.mp3"

    if not forcar:
        try:
            s3.head_object(Bucket=c["bucket"], Key=mp3_key)
            print(f"  ⏭️  {nnnn} já está no R2")
            return "pulado"
        except Exception:
            pass

    cap = d1(env, "SELECT body FROM chapters WHERE id = ?", [s["chapter_id"]])
    if not cap:
        raise RuntimeError(f"capítulo {s['chapter_id']} sumiu do D1")
    paras = preparar_texto(cap[0]["body"])
    titulo = limpar_titulo(s["titulo"], paras, s.get("obra"), s.get("cap_n"))
    paras = cortar_bordas(paras)
    texto = "\n\n".join(paras)
    # Capítulo que era SÓ folha de rosto e sumário sobra vazio depois da
    # limpeza. Isso não é falha de execução, é material que nunca deveria
    # virar vídeo: sai da fila como `descartado` e não volta a ser tentado.
    if len(texto) < 2000:
        d1(env, """UPDATE sermons SET status='descartado',
                   erro=?, updated_at=datetime('now') WHERE canal=? AND numero=?""",
           [f"só {len(texto)} chars após limpar rosto/catálogo", c["slug"], s["numero"]])
        print(f"  🗑️  {nnnn} descartado: sobrou {len(texto)} chars (era folha de rosto)")
        return "descartado"

    # TETO, o irmão que faltava do piso acima (aberto em 27/08, minerando o
    # Maclaren). Calibração medida: 7.271 palavras ≈ 40k chars ≈ 45min de vídeo.
    # O padrão de 55k (~60min) deixa folga pro maior sermão do Spurgeon (44k) e
    # ainda pega o que não é sermão: no Maclaren sobraram peças de 77k, 101k e
    # 145k chars que o seletor de nível não conseguiu repartir. 145k viraria
    # narração de ~2h45, fora do formato Treasures, segurando uma vaga de CPU a
    # tarde inteira.
    #
    # Status `longo` e NÃO `descartado`: isto não é lixo como folha de rosto, é
    # container que ainda pode virar 3 sermões quando alguém repartir. Descartar
    # em silêncio seria perder conteúdo bom sem ninguém ver.
    teto = c.get("chars_max", 55000)
    if len(texto) > teto:
        d1(env, """UPDATE sermons SET status='longo',
                   erro=?, updated_at=datetime('now') WHERE canal=? AND numero=?""",
           [f"{len(texto)} chars (teto {teto}): provável container de vários sermões",
            c["slug"], s["numero"]])
        print(f"  📏 {nnnn} PARADO por tamanho: {len(texto)} chars "
              f"(~{len(texto)//900}min) > teto {teto}. Precisa ser repartido.")
        return "descartado"
    # Título e slug podem mudar depois da limpeza; a pasta segue o slug limpo.
    slug_limpo = slugificar(titulo)
    if slug_limpo != s["slug"] or titulo != s["titulo"]:
        d1(env, """UPDATE sermons SET titulo=?, slug=?, updated_at=datetime('now')
                   WHERE canal=? AND numero=?""", [titulo, slug_limpo, c["slug"], s["numero"]])
        s = dict(s, titulo=titulo, slug=slug_limpo)
        pasta = f"{c['prefix']}/{nnnn}_-_{slug_limpo}"
        mp3_key = f"{pasta}/sermon_{nnnn}.mp3"

    base = os.path.join(WORK, nnnn)
    wav, mp3 = os.path.join(base, "s.wav"), os.path.join(base, "s.mp3")
    print(f"  🎙️  {nnnn} {titulo[:52]} · {len(texto)//1000}k chars", flush=True)

    t0 = time.time()
    narrar(c, texto, wav)
    para_mp3(wav, mp3)
    tam = os.path.getsize(mp3)

    print(f"  📝 transcrevendo ({tam//1024//1024}MB)...", flush=True)
    tr = transcrever(mp3, env, c)
    # `title` é o que o generate_marketing e o build_job leem pra nomear o vídeo
    tr["title"] = titulo
    dur = (tr.get("audio_duration") or 0)

    s3.upload_file(mp3, c["bucket"], mp3_key, ExtraArgs={"ContentType": "audio/mpeg"})
    s3.put_object(Bucket=c["bucket"], Key=f"{pasta}/transcript.json",
                  Body=json.dumps(tr, ensure_ascii=False).encode(),
                  ContentType="application/json")
    os.remove(wav)
    os.remove(mp3)

    d1(env, """UPDATE sermons SET status='narrado', dur_s=?, audio_key=?, erro=NULL,
               updated_at=datetime('now') WHERE canal=? AND numero=?""",
       [dur, mp3_key, c["slug"], s["numero"]])
    print(f"  ✅ {nnnn} · {dur/60:.0f}min · {tam//1024//1024}MB · "
          f"{len(tr.get('words') or [])} palavras · {time.time()-t0:.0f}s", flush=True)
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--enfileirar", action="store_true", help="monta a fila e para")
    ap.add_argument("--limite", type=int, default=1)
    ap.add_argument("--minutos", type=int, default=0,
                    help="orçamento de tempo: para de PEGAR sermão novo depois disso "
                         "(0 = sem orçamento, só o --limite manda)")
    ap.add_argument("--so", type=int, help="processa apenas este número de sermão")
    ap.add_argument("--forcar", action="store_true", help="refaz mesmo se já existe no R2")
    ap.add_argument("--cpus", default=None, help="teto de CPU dos containers (padrão 8)")
    args = ap.parse_args()

    global CPUS, CANAL_ATUAL
    CANAL_ATUAL = args.canal or "?"
    if args.cpus:
        CPUS = args.cpus

    c = canais.get(args.canal)
    if not c.get("autor_mineracao"):
        raise SystemExit(f"❌ canal {c['slug']!r} sem `autor_mineracao` em canais.py.")
    env = load_env()
    for k in ("CLOUDFLARE_API_TOKEN", "R2_ENDPOINT"):
        if not env.get(k):
            raise SystemExit(f"❌ falta {k} no .env")


    novos, total = enfileirar(env, c)
    print(f"📋 {c['nome']}: {total} capítulos minerados, {novos} entraram na fila agora")
    if args.enfileirar:
        est = d1(env, "SELECT status, COUNT(*) n FROM sermons WHERE canal=? GROUP BY status",
                 [c["slug"]])
        print("   " + " · ".join(f"{r['status']}={r['n']}" for r in est))
        return

    s3 = s3c(env)
    # Idem: um run morto por pkill/timeout deixa o Kokoro e o Whisper vivos.
    for etapa in ("tts", "asr"):
        docker_nomeado.varrer(etapa, c["slug"])
    # 'longo' entra na lista de parados junto com 'descartado': sem isso o
    # container de 145k chars voltaria pra fila em TODO run, seria limpo,
    # medido, barrado de novo, pra sempre. Fila que retenta o que já decidiu
    # não processar é a mesma doença do `list_pending` do generate_marketing.
    onde = "AND numero = ?" if args.so else "AND status NOT IN ('narrado','descartado','longo')"
    par = [c["slug"]] + ([args.so] if args.so else [])
    fila = d1(env, f"""SELECT numero, chapter_id, titulo, slug, obra, cap_n FROM sermons
                       WHERE canal = ? {onde} ORDER BY numero LIMIT ?""",
              par + [args.limite])
    if not fila:
        print("nada na fila.")
        return

    # ORÇAMENTO DE TEMPO em vez de número mágico.
    #
    # Até 25/08 o cron era `--limite 2` a cada 4h. Medido: cada sermão leva
    # ~1400s com 8 CPUs, ou seja 47 min de trabalho num intervalo de 240 min.
    # A VPS (16 vCPU) ficava com load 0.03 e o Spurgeon levaria 294 DIAS pra
    # vencer os 3.533 capítulos que já estavam minerados.
    #
    # Lote fixo é chute: sermão de 20 min e de 45 min contam igual, e o número
    # certo muda se a máquina mudar. O orçamento não chuta — só começa um
    # sermão novo se ainda houver tempo na janela, e nunca corta um pela metade
    # (interromper no meio deixaria áudio parcial no R2).
    folego = folego_dias(env, s3, c)
    args.limite, args.minutos, regime = regime_do_folego(folego, args.limite, args.minutos)
    fila = fila[: args.limite]
    print(f"🌡️  fôlego: {folego:.0f} dias de estoque → {regime}")
    print(f"🎬 processando até {len(fila)}"
          + (f" ou {args.minutos} min, o que vier primeiro" if args.minutos else "") + "\n")
    t0 = time.monotonic()
    ok = falha = pulado = 0
    for s in fila:
        gasto = (time.monotonic() - t0) / 60
        feitos = ok + falha + pulado
        # ⚠️ Olhar só o gasto PASSADO não segura nada: o corte é feito antes de
        # começar, e o sermão começado vai até o fim. Em 25/08 isso deixou um run
        # de orçamento 200 terminar em 341 min, porque a máquina engasgou e cada
        # sermão passou de 23 min pra 160. Agora o teste é "o PRÓXIMO cabe?",
        # usando a média MEDIDA neste run e não uma expectativa fixa.
        if args.minutos:
            media = gasto / feitos if feitos else 0
            if gasto >= args.minutos:
                print(f"⏳ orçamento de {args.minutos} min esgotado ({gasto:.0f} min) "
                      f"— o resto fica pro próximo run")
                break
            if media and gasto + media > args.minutos:
                print(f"⏳ o próximo sermão não cabe ({gasto:.0f} min gastos + "
                      f"~{media:.0f} min de média > {args.minutos}) — parando inteiro")
                break
        try:
            # A vaga é por SERMÃO, não pelo run inteiro: segurar a vaga durante
            # as consultas ao D1 e os uploads (que não gastam CPU) desperdiçaria
            # a máquina, e é justamente ela que estamos tentando não desperdiçar.
            with vaga_cpu.vaga(f"narrar {c['slug']} {s['numero']:04d}",
                               espera_max_s=1200):
                r = processar(env, s3, c, s, args.forcar)
            ok += r == "ok"
            pulado += r in ("pulado", "descartado")
        except TimeoutError as e:
            # Máquina cheia não é falha do sermão: nada de marcar 'falhou' no D1,
            # senão a fila se envenena sozinha num dia de pico.
            print(f"⏸️  {e} — encerrando o run, o cron volta em 4h")
            break
        except Exception as e:
            falha += 1
            msg = str(e)[:400]
            print(f"  ❌ {s['numero']:04d}: {msg}", flush=True)
            d1(env, """UPDATE sermons SET status='falhou', erro=?, updated_at=datetime('now')
                       WHERE canal=? AND numero=?""", [msg, c["slug"], s["numero"]])
    print(f"\n🏁 narrados={ok} pulados={pulado} falhas={falha}")


if __name__ == "__main__":
    main()
