#!/usr/bin/env python3
"""
tts_nuvem.py — narração em TTS de nuvem COM TRAVA DE GASTO NOSSA.

## Por que a trava mora aqui, e não no Google

O Gabriel já levou prejuízo estourando cota do Google (trauma citado em 07/09).
Investigando o console: a cota editável do Text-to-Speech é de REQUISIÇÕES POR
MINUTO (RequestsPerMinutePerProject = 1000, Chirp3 = 200), não de caracteres por
mês. Ou seja, NÃO EXISTE no Google um botão "trave em 1 milhão de caracteres".
Baixar as requisições por minuto limita a velocidade, não o total do mês.

Então a trava real é esta aqui: o contador conta os caracteres ANTES de chamar a
API, guarda o acumulado do mês no D1 e RECUSA passar do teto. Mesma lei que
nasceu do incidente do Magnific (doc 21): custo se confere no nosso painel, nunca
no rótulo do plano.

Camadas de defesa, da que impede à que só avisa:
  1. ESTE contador (impede: não chama a API se estourar o teto do mês)
  2. Projeto GCP SEPARADO só pra TTS (se algo surtar, não derruba o YouTube)
  3. Chave de API restrita à API de TTS (chave vazada não vira fatura de outra coisa)
  4. Orçamento + alerta no Cloud Billing (avisa depois; rede de segurança)
  5. Requisições por minuto baixas no console (limita a velocidade do estrago)

## Tetos (90% do free tier de cada provedor, medido em 07/09/2026)

  google  1.000.000 chars/mês (Chirp 3 HD / Neural2 / WaveNet)  -> teto 900.000
  azure     500.000 chars/mês (Neural, tier F0)                 -> teto 450.000
  polly   1.000.000 chars/mês (Neural, 12 primeiros meses)      -> teto 900.000

Uso:
  python3 scripts/tts_nuvem.py --vozes                  # lista vozes pt-BR do Google
  python3 scripts/tts_nuvem.py --uso                    # quanto já gastamos no mês
  python3 scripts/tts_nuvem.py --texto arquivo.txt --voz pt-BR-Chirp3-HD-Charon \\
      --saida /tmp/amostra.mp3
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "remotion"))
import narrar_sermao as N  # noqa: E402

TETOS = {"google": 900_000, "azure": 450_000, "polly": 900_000}
MAX_BYTES = 4500          # limite duro do Google é 5000 bytes por requisição
API = "https://texttospeech.googleapis.com/v1"


def mes():
    return dt.date.today().strftime("%Y-%m")


def uso_do_mes(env, provedor):
    r = N.d1(env, "SELECT COALESCE(SUM(chars),0) n FROM tts_uso WHERE provedor=? AND mes=?",
             [provedor, mes()])
    return r[0]["n"] if r else 0


def reservar(env, provedor, chars, nota=""):
    """Só devolve True se couber no teto do mês. Registra o gasto ANTES de chamar."""
    teto = TETOS[provedor]
    ja = uso_do_mes(env, provedor)
    if ja + chars > teto:
        raise SystemExit(
            f"🛑 TRAVA: {provedor} já usou {ja:,} chars neste mês; mais {chars:,} passaria "
            f"do teto de {teto:,}. Nada foi chamado, nada foi cobrado.")
    N.d1(env, "INSERT INTO tts_uso (provedor, mes, chars, nota, criado_em) "
              "VALUES (?, ?, ?, ?, datetime('now'))", [provedor, mes(), chars, nota[:200]])
    print(f"💳 {provedor}: +{chars:,} chars · mês {ja + chars:,}/{teto:,}", flush=True)
    return True


def http(url, corpo=None):
    req = urllib.request.Request(url, method="POST" if corpo is not None else "GET",
                                 data=json.dumps(corpo).encode() if corpo is not None else None)
    if corpo is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"❌ {e.code}: {e.read()[:500].decode('utf-8', 'ignore')}")


def listar_vozes(chave, idioma="pt-BR"):
    j = http(f"{API}/voices?languageCode={idioma}&key={chave}")
    vs = sorted(j.get("voices", []), key=lambda v: v["name"])
    for v in vs:
        print(f"  {v['name']:38} {v.get('ssmlGender', '?'):8} {v.get('naturalSampleRateHertz','')}")
    print(f"\n{len(vs)} vozes em {idioma}")
    return vs


def pedacos(texto, limite=MAX_BYTES):
    """Corta em fronteira de FRASE respeitando o limite de bytes da requisição."""
    out, buf = [], ""
    for f in re.split(r"(?<=[.!?])\s+", texto.strip()):
        if len((buf + " " + f).encode()) > limite and buf:
            out.append(buf.strip())
            buf = f
        else:
            buf = (buf + " " + f).strip()
    if buf:
        out.append(buf)
    return out


def sintetizar(env, chave, texto, voz, saida, idioma="pt-BR", velocidade=0.92):
    partes = pedacos(texto)
    total = sum(len(p) for p in partes)
    reservar(env, "google", total, f"{voz} -> {os.path.basename(saida)}")
    audio = b""
    for i, p in enumerate(partes, 1):
        j = http(f"{API}/text:synthesize?key={chave}", {
            "input": {"text": p},
            "voice": {"languageCode": idioma, "name": voz},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": velocidade},
        })
        audio += base64.b64decode(j["audioContent"])
        print(f"   parte {i}/{len(partes)} ok", flush=True)
    open(saida, "wb").write(audio)
    print(f"✅ {saida} ({len(audio)//1000} KB)")
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vozes", action="store_true")
    ap.add_argument("--uso", action="store_true")
    ap.add_argument("--texto", help="arquivo de texto a narrar")
    ap.add_argument("--voz", help="ex: pt-BR-Chirp3-HD-Charon")
    ap.add_argument("--saida", default="/tmp/tts_amostra.mp3")
    ap.add_argument("--idioma", default="pt-BR")
    ap.add_argument("--velocidade", type=float, default=0.92)
    a = ap.parse_args()

    env = N.load_env()
    if a.uso:
        for p, teto in TETOS.items():
            print(f"  {p:8} {uso_do_mes(env, p):>9,} / {teto:,} chars em {mes()}")
        return
    chave = env.get("GOOGLE_TTS_API_KEY")
    if not chave:
        sys.exit("❌ falta GOOGLE_TTS_API_KEY no .env")
    if a.vozes:
        listar_vozes(chave, a.idioma)
        return
    if not (a.texto and a.voz):
        sys.exit("informe --texto e --voz (ou --vozes / --uso)")
    sintetizar(env, chave, open(a.texto, encoding="utf-8").read(), a.voz, a.saida,
               a.idioma, a.velocidade)


if __name__ == "__main__":
    main()
