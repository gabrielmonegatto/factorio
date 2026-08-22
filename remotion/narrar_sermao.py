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

ACCOUNT = "dca6b1af1352f500d6eabe544b9222a3"
MINING_DB = "b08c9fae-3692-409a-aebd-e9630ca66f1d"
TTS_IMAGE = os.environ.get("TTS_IMAGE", "factorio-tts")
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "/srv/factorio/data/narrar" if os.path.isdir("/srv/factorio/data") else os.path.join(HERE, "_narrar")

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


def preparar_texto(bruto):
    """Tira do texto o que é marca de página, não fala.

    O corpo minerado é "markdown-ish" e vem de digitalização: sobra nota de
    transcritor entre colchetes, marcação de itálico com asterisco e número de
    nota de rodapé grudado na palavra. Nada disso deve virar som.
    """
    t = bruto
    t = re.sub(r"\[[^\]]{0,120}\]", " ", t)          # [Illustration: ...], [1], [Transcriber's Note]
    t = re.sub(r"\{[^}]{0,120}\}", " ", t)
    t = t.replace("*", "").replace("_", " ")
    t = re.sub(r"[“”]", '"', t).replace("’", "'").replace("‘", "'")
    t = re.sub(r"-{2,}", ", ", t)                     # travessão datilografado vira respiro
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    # parágrafo de 1 ou 2 palavras é resíduo de cabeçalho de página
    linhas = [p.strip() for p in t.split("\n\n")]
    linhas = [p for p in linhas if len(p.split()) > 2]
    return "\n\n".join(linhas).strip()


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
        d1(env, """INSERT INTO sermons (canal, numero, work_id, chapter_id, titulo, slug, chars)
                   VALUES (?,?,?,?,?,?,?)""",
           [c["slug"], prox, ch["work_id"], ch["chapter_id"], titulo,
            slugificar(titulo), ch["chars"]])
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
    subprocess.run([
        "docker", "run", "--rm", "--memory=8g",
        "-v", f"{d}:/data", "-v", "/srv/factorio/hfcache:/cache", TTS_IMAGE,
        "--input", f"/data/{os.path.basename(txt)}",
        "--output", f"/data/{os.path.basename(wav)}",
        "--voice", c["voz"], "--speed", str(c["voz_speed"]),
        "--split", "sentence", "--silence", str(c.get("pausa_frase_s", 0.75)),
        "--trim", "--progresso", "200",
    ], check=True)
    os.remove(txt)


def para_mp3(wav, mp3):
    """64k mono: é narração falada, não música. Corta o arquivo em ~3,5x."""
    d = os.path.dirname(os.path.abspath(wav))
    subprocess.run([
        "docker", "run", "--rm", "-v", f"{d}:/data", "--entrypoint", "ffmpeg", TTS_IMAGE,
        "-y", "-loglevel", "error", "-i", f"/data/{os.path.basename(wav)}",
        "-ac", "1", "-b:a", "64k", f"/data/{os.path.basename(mp3)}",
    ], check=True)


def transcrever(caminho, chave):
    """AssemblyAI, palavra a palavra.

    Por que transcrever um áudio que NÓS sintetizamos e cujo texto já sabemos:
    o Kokoro não devolve alinhamento, e a legenda precisa do tempo de cada
    palavra. É mais barato pedir pra ASR do que construir alinhamento forçado.
    AssemblyAI e não Groq porque o Groq tem teto de tamanho de arquivo e aqui
    o áudio tem 45 minutos.
    """
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
    texto = preparar_texto(cap[0]["body"])
    if len(texto) < 2000:
        raise RuntimeError(f"texto curto demais depois da limpeza ({len(texto)} chars)")

    base = os.path.join(WORK, nnnn)
    wav, mp3 = os.path.join(base, "s.wav"), os.path.join(base, "s.mp3")
    print(f"  🎙️  {nnnn} {s['titulo'][:52]} · {len(texto)//1000}k chars", flush=True)

    t0 = time.time()
    narrar(c, texto, wav)
    para_mp3(wav, mp3)
    tam = os.path.getsize(mp3)

    print(f"  📝 transcrevendo ({tam//1024//1024}MB)...", flush=True)
    tr = transcrever(mp3, env["ASSEMBLYAI_API_KEY"])
    # `title` é o que o generate_marketing e o build_job leem pra nomear o vídeo
    tr["title"] = s["titulo"]
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
    ap.add_argument("--so", type=int, help="processa apenas este número de sermão")
    ap.add_argument("--forcar", action="store_true", help="refaz mesmo se já existe no R2")
    args = ap.parse_args()

    c = canais.get(args.canal)
    if not c.get("autor_mineracao"):
        raise SystemExit(f"❌ canal {c['slug']!r} sem `autor_mineracao` em canais.py.")
    env = load_env()
    for k in ("CLOUDFLARE_API_TOKEN", "R2_ENDPOINT", "ASSEMBLYAI_API_KEY"):
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
    onde = "AND numero = ?" if args.so else "AND status != 'narrado'"
    par = [c["slug"]] + ([args.so] if args.so else [])
    fila = d1(env, f"""SELECT numero, chapter_id, titulo, slug FROM sermons
                       WHERE canal = ? {onde} ORDER BY numero LIMIT ?""",
              par + [args.limite])
    if not fila:
        print("nada na fila.")
        return

    print(f"🎬 processando {len(fila)}\n")
    ok = falha = pulado = 0
    for s in fila:
        try:
            r = processar(env, s3, c, s, args.forcar)
            ok += r == "ok"
            pulado += r == "pulado"
        except Exception as e:
            falha += 1
            msg = str(e)[:400]
            print(f"  ❌ {s['numero']:04d}: {msg}", flush=True)
            d1(env, """UPDATE sermons SET status='falhou', erro=?, updated_at=datetime('now')
                       WHERE canal=? AND numero=?""", [msg, c["slug"], s["numero"]])
    print(f"\n🏁 narrados={ok} pulados={pulado} falhas={falha}")


if __name__ == "__main__":
    main()
