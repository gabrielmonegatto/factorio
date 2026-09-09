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
API, guarda o acumulado do mês no D1 (tabela `tts_uso`) e RECUSA passar do teto.
Mesma lei que nasceu do incidente do Magnific (doc 21): custo se confere no nosso
painel, nunca no rótulo do plano.

Camadas de defesa, da que impede à que só avisa:
  1. ESTE contador (impede: não chama a API se estourar o teto do mês)
  2. Projeto/conta SEPARADA só pra TTS (se surtar, não derruba o YouTube)
  3. Chave restrita à API de TTS (chave vazada não vira fatura de outra coisa)
  4. Orçamento + alerta de billing (avisa depois; rede de segurança)
  5. Requisições por minuto baixas no console (limita a velocidade do estrago)

## Tetos (90% do free tier de cada provedor, conferido em 07/09/2026)

  google  1.000.000 chars/mês (Chirp 3 HD / Neural2 / WaveNet)  -> teto  900.000
  azure     500.000 chars/mês (Neural, tier F0)                 -> teto  450.000
  polly   1.000.000 chars/mês (Neural, 12 primeiros meses)      -> teto  900.000

Uso:
  python3 scripts/tts_nuvem.py --uso                       # quanto já gastamos
  python3 scripts/tts_nuvem.py --vozes --provedor google    # lista o que existe
  python3 scripts/tts_nuvem.py --amostras --provedor google --texto t.txt \\
      --saida-dir /tmp/vozes                                # todos os candidatos
  python3 scripts/tts_nuvem.py --provedor azure --voz pt-BR-AntonioNeural \\
      --texto t.txt --saida /tmp/antonio.mp3
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "remotion"))
import narrar_sermao as N  # noqa: E402

TETOS = {"google": 900_000, "azure": 450_000, "polly": 900_000}
MAX_BYTES = 4500          # limite duro do Google é 5000 bytes por requisição
GOOGLE_API = "https://texttospeech.googleapis.com/v1"

# ── CATÁLOGO DE CANDIDATOS pt-BR (masculinos: narrador de sermão) ───────────
# Fechado em 09/09/2026 a partir da doc de cada provedor. A escolha final é do
# OUVIDO do Gabriel: `--amostras` gera o mesmo trecho em todos e ele decide.
# Regra da casa (doc 10): 1 canal = 1 voz travada pra sempre; dois canais nunca
# compartilham voz, senão aos ouvidos de quem assiste os dois vira o mesmo canal.
CATALOGO = {
    "google": [   # Chirp 3 HD: mesma família de nomes em todos os idiomas
        ("pt-BR-Chirp3-HD-Charon", "grave, o mais 'locutor'"),
        ("pt-BR-Chirp3-HD-Fenrir", "encorpado, energia alta"),
        ("pt-BR-Chirp3-HD-Orus", "médio, neutro"),
        ("pt-BR-Chirp3-HD-Puck", "mais jovem, leve"),
    ],
    "azure": [    # Neural pt-BR masculinos
        ("pt-BR-AntonioNeural", "padrão da casa Azure, bem redondo"),
        ("pt-BR-DonatoNeural", "grave"),
        ("pt-BR-FabioNeural", "claro, dicção limpa"),
        ("pt-BR-JulioNeural", "médio"),
        ("pt-BR-NicolauNeural", "jovem"),
        ("pt-BR-ValerioNeural", "sério"),
        ("pt-BR-HumbertoNeural", "maduro"),
    ],
    "polly": [    # Neural pt-BR (Ricardo só existe em Standard: fora)
        ("Thiago", "neural masculino, o único pt-BR masculino neural da Polly"),
    ],
}


def mes():
    return dt.date.today().strftime("%Y-%m")


def uso_do_mes(env, provedor):
    r = N.d1(env, "SELECT COALESCE(SUM(chars),0) n FROM tts_uso WHERE provedor=? AND mes=?",
             [provedor, mes()])
    return r[0]["n"] if r else 0


def reservar(env, provedor, chars, nota=""):
    """Só passa se couber no teto do mês. Registra o gasto ANTES de chamar a API."""
    teto = TETOS[provedor]
    ja = uso_do_mes(env, provedor)
    if ja + chars > teto:
        raise SystemExit(
            f"🛑 TRAVA: {provedor} já usou {ja:,} chars neste mês; mais {chars:,} passaria "
            f"do teto de {teto:,}. Nada foi chamado, nada foi cobrado.")
    N.d1(env, "INSERT INTO tts_uso (provedor, mes, chars, nota, criado_em) "
              "VALUES (?, ?, ?, ?, datetime('now'))", [provedor, mes(), chars, nota[:200]])
    print(f"💳 {provedor}: +{chars:,} chars · mês {ja + chars:,}/{teto:,}", flush=True)


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


def _req(url, dados=None, cabecalhos=None, metodo=None):
    req = urllib.request.Request(url, data=dados, method=metodo)
    for k, v in (cabecalhos or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"❌ {e.code}: {e.read()[:500].decode('utf-8', 'ignore')}")


# ── Google ─────────────────────────────────────────────────────────────────
def google_vozes(env, idioma="pt-BR"):
    chave = env["GOOGLE_TTS_API_KEY"]
    j = json.loads(_req(f"{GOOGLE_API}/voices?languageCode={idioma}&key={chave}"))
    for v in sorted(j.get("voices", []), key=lambda v: v["name"]):
        print(f"  {v['name']:42} {v.get('ssmlGender', '?')}")
    print(f"\n{len(j.get('voices', []))} vozes em {idioma}")


def google_sintetizar(env, texto, voz, idioma, velocidade):
    chave = env["GOOGLE_TTS_API_KEY"]
    audio = b""
    for p in pedacos(texto):
        j = json.loads(_req(f"{GOOGLE_API}/text:synthesize?key={chave}",
                            json.dumps({
                                "input": {"text": p},
                                "voice": {"languageCode": idioma, "name": voz},
                                "audioConfig": {"audioEncoding": "MP3",
                                                "speakingRate": velocidade},
                            }).encode(), {"Content-Type": "application/json"}))
        audio += base64.b64decode(j["audioContent"])
    return audio


# ── Azure ──────────────────────────────────────────────────────────────────
def azure_vozes(env, idioma="pt-BR"):
    reg = env["AZURE_SPEECH_REGION"]
    j = json.loads(_req(f"https://{reg}.tts.speech.microsoft.com/cognitiveservices/voices/list",
                        cabecalhos={"Ocp-Apim-Subscription-Key": env["AZURE_SPEECH_KEY"]}))
    for v in sorted([x for x in j if x["Locale"] == idioma], key=lambda x: x["ShortName"]):
        print(f"  {v['ShortName']:34} {v['Gender']:7} {','.join(v.get('StyleList', []) or [])}")


def azure_sintetizar(env, texto, voz, idioma, velocidade):
    reg = env["AZURE_SPEECH_REGION"]
    pct = f"{int((velocidade - 1) * 100):+d}%"
    audio = b""
    for p in pedacos(texto):
        ssml = (f"<speak version='1.0' xml:lang='{idioma}'>"
                f"<voice name='{voz}'><prosody rate='{pct}'>"
                f"{p.replace('&', '&amp;').replace('<', '&lt;')}"
                f"</prosody></voice></speak>")
        audio += _req(f"https://{reg}.tts.speech.microsoft.com/cognitiveservices/v1",
                      ssml.encode("utf-8"),
                      {"Ocp-Apim-Subscription-Key": env["AZURE_SPEECH_KEY"],
                       "Content-Type": "application/ssml+xml",
                       "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3"},
                      "POST")
    return audio


# ── Polly ──────────────────────────────────────────────────────────────────
def _polly(env):
    import boto3
    return boto3.client("polly", region_name=env.get("AWS_REGION", "us-east-1"),
                        aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
                        aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"])


def polly_vozes(env, idioma="pt-BR"):
    for v in _polly(env).describe_voices(LanguageCode=idioma)["Voices"]:
        print(f"  {v['Id']:14} {v['Gender']:7} {','.join(v.get('SupportedEngines', []))}")


def polly_sintetizar(env, texto, voz, idioma, velocidade):
    cli = _polly(env)
    pct = f"{int(velocidade * 100)}%"
    audio = b""
    for p in pedacos(texto, 2800):     # Polly: 3000 chars de texto por chamada
        ssml = (f"<speak><prosody rate='{pct}'>"
                f"{p.replace('&', '&amp;').replace('<', '&lt;')}</prosody></speak>")
        r = cli.synthesize_speech(Text=ssml, TextType="ssml", VoiceId=voz,
                                  Engine="neural", OutputFormat="mp3")
        audio += r["AudioStream"].read()
    return audio


MOTORES = {"google": (google_vozes, google_sintetizar),
           "azure": (azure_vozes, azure_sintetizar),
           "polly": (polly_vozes, polly_sintetizar)}


def narrar(env, provedor, texto, voz, saida, idioma="pt-BR", velocidade=0.92):
    total = sum(len(p) for p in pedacos(texto))
    reservar(env, provedor, total, f"{voz} -> {os.path.basename(saida)}")
    audio = MOTORES[provedor][1](env, texto, voz, idioma, velocidade)
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    open(saida, "wb").write(audio)
    print(f"✅ {saida} ({len(audio)//1000} KB)")
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provedor", choices=list(MOTORES), default="google")
    ap.add_argument("--vozes", action="store_true", help="lista as vozes do provedor")
    ap.add_argument("--uso", action="store_true")
    ap.add_argument("--amostras", action="store_true",
                    help="gera o texto em TODOS os candidatos do catálogo")
    ap.add_argument("--texto", help="arquivo de texto a narrar")
    ap.add_argument("--voz")
    ap.add_argument("--saida", default="/tmp/tts_amostra.mp3")
    ap.add_argument("--saida-dir", dest="saida_dir", default="/tmp/vozes")
    ap.add_argument("--idioma", default="pt-BR")
    ap.add_argument("--velocidade", type=float, default=0.92)
    a = ap.parse_args()

    env = N.load_env()
    if a.uso:
        for p, teto in TETOS.items():
            print(f"  {p:8} {uso_do_mes(env, p):>9,} / {teto:,} chars em {mes()}")
        return
    if a.vozes:
        MOTORES[a.provedor][0](env, a.idioma)
        return
    if not a.texto:
        sys.exit("informe --texto (ou --vozes / --uso)")
    texto = open(a.texto, encoding="utf-8").read()
    if a.amostras:
        os.makedirs(a.saida_dir, exist_ok=True)
        for voz, nota in CATALOGO[a.provedor]:
            print(f"\n🎙️  {voz}: {nota}")
            narrar(env, a.provedor, texto, voz,
                   os.path.join(a.saida_dir, f"{a.provedor}_{voz}.mp3"),
                   a.idioma, a.velocidade)
        return
    if not a.voz:
        sys.exit("informe --voz (ou --amostras)")
    narrar(env, a.provedor, texto, a.voz, a.saida, a.idioma, a.velocidade)


if __name__ == "__main__":
    main()
