#!/usr/bin/env python3
"""
auth_youtube.py — Gera o REFRESH TOKEN de UM canal (roda na máquina do Gabriel).

Por que existe: o upload precisa de um token que não expira. Este script faz o
login uma única vez e cospe um `refresh_token` que a fábrica usa pra sempre.

⚠️ RODE VOCÊ MESMO — envolve login na sua conta Google. Eu não faço isso por você.

## UM projeto do GCP pra fábrica inteira, não um por canal

Corrigido em 21/08/2026. A versão anterior deste arquivo mandava criar "um
projeto POR CANAL, pra ter cota separada". Isso é exatamente o que os Termos
da API do YouTube tratam como burlar cota, e a punição documentada é suspensão
de TODOS os projetos, não só dos extras: perderíamos os 10 canais de uma vez.

O Client ID identifica o APLICATIVO. Quem identifica o canal é o refresh_token.
Então canal novo NÃO precisa de projeto novo nem de credencial nova: roda este
script com o MESMO client-id/secret, logando na conta do canal novo.

O limite de verdade é a cota: 10.000 unidades/dia por projeto, e um upload
custa 1.600. Dá ~5 vídeos por dia somando TODOS os canais. Ao encostar nisso,
o caminho legítimo é pedir aumento pelo formulário de auditoria do YouTube.

Antes de rodar, no Google Cloud Console (UMA vez, não por canal):
  1. Crie ou escolha o projeto da fábrica
  2. Ative a "YouTube Data API v3"
  3. Tela de consentimento OAuth -> PUBLIQUE
     (em "Testing" o refresh_token morre em 7 dias; já nos mordeu)
  4. Credenciais -> Criar -> ID do cliente OAuth -> tipo "App para computador"
  5. Guarde o Client ID e o Client Secret; servem pra todos os canais

Uso:
  python auth_youtube.py --canal moody --client-id XXX --client-secret YYY

No fim ele CONFERE em qual canal você acabou de logar e só então imprime as
3 linhas, já com o prefixo de env do canal certo.
"""
import argparse
import http.server
import json
import os
import socketserver
import threading
import urllib.parse
import urllib.request
import webbrowser

import canais

# force-ssl posta comentario (o link no 1º comentário); upload sobe vídeo;
# yt-analytics.readonly libera METRICA DIARIA (views, minutos assistidos,
# duração média, inscritos ganhos por dia). Sem ele a API responde 403
# "insufficient authentication scopes".
SCOPE = " ".join([
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
])
PORT = 8765
REDIRECT = f"http://localhost:{PORT}"
_code = {}
_pronto = threading.Event()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        _code.update(urllib.parse.parse_qs(q))
        _pronto.set()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in _code
        self.wfile.write(
            ("<h2>✅ Autorizado! Pode fechar esta aba e voltar pro terminal.</h2>"
             if ok else "<h2>❌ Falhou. Veja o terminal.</h2>").encode())

    def log_message(self, *a):
        pass


def canal_do_token(token):
    """Em qual canal esse token acabou de logar? Pergunta pra API, não adivinha."""
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
        headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=40) as r:
        itens = json.loads(r.read()).get("items", [])
    if not itens:
        return None, None
    return itens[0]["id"], itens[0]["snippet"]["title"]


def gravar_env(caminho, valores):
    """Escreve as chaves no .env sem passar por tela nenhuma.

    Existe porque o refresh_token é senha: imprimir no terminal é imprimir na
    janela de quem estiver olhando (inclusive numa sessão de agente). Aqui ele
    vai do Google direto pro arquivo.

    Atualiza a linha se a chave já existe, senão acrescenta no fim. O arquivo é
    CRLF (regra da fábrica) e a terminação existente é preservada.
    """
    bruto = open(caminho, "rb").read() if os.path.exists(caminho) else b""
    fim = b"\r\n" if b"\r\n" in bruto else b"\n"
    linhas = bruto.split(fim)
    for chave, valor in valores.items():
        nova = f"{chave}={valor}".encode()
        for i, ln in enumerate(linhas):
            if ln.startswith(chave.encode() + b"="):
                linhas[i] = nova
                break
        else:
            if linhas and linhas[-1] == b"":
                linhas.insert(len(linhas) - 1, nova)
            else:
                linhas.append(nova)
    open(caminho, "wb").write(fim.join(linhas))


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    ap.add_argument("--gravar-env", action="store_true",
                    help="grava direto no ../.env em vez de imprimir o token")
    args = ap.parse_args()

    C = canais.get(args.canal)
    print(f"\n🎯 Autorizando: {C['nome']}   (as linhas sairão com prefixo {C['env_prefix']}_)")

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": args.client_id,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",      # <- sem isso não vem refresh_token
        "prompt": "consent",           # <- força vir o refresh_token mesmo se já autorizou antes
    })

    print("\n🔗 Abrindo o navegador. Faça login com a conta DONA DO CANAL e,")
    print(f"   na tela de escolha, selecione {C['nome']!r}:\n")
    print(auth_url, "\n")

    httpd = socketserver.TCPServer(("", PORT), Handler)
    threading.Thread(target=httpd.handle_request, daemon=True).start()
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("⏳ Aguardando autorização no navegador...")
    # Event em vez de `while "code" not in _code: pass` — o busy-wait fritava
    # um núcleo inteiro enquanto a tela de escolha de conta ficava aberta.
    if not _pronto.wait(timeout=300):
        raise SystemExit("❌ Ninguém autorizou em 5 minutos. Rode de novo.")
    code = _code["code"][0]

    data = urllib.parse.urlencode({
        "code": code,
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=data, method="POST")) as r:
        tok = json.loads(r.read())

    rt = tok.get("refresh_token")
    if not rt:
        print("❌ Não veio refresh_token. Reautorize removendo o acesso em "
              "https://myaccount.google.com/permissions e rode de novo.")
        return

    # ⚠️ INCIDENTE 11/08/2026: a re-auth foi feita na conta pessoal do Gabriel e
    # 18 vídeos foram publicados no canal errado sem UM erro sequer. O guardião
    # do publish pega isso, mas só na hora do upload. Aqui é o lugar barato:
    # perguntar à API em qual canal acabamos de entrar, antes de salvar nada.
    cid, nome = canal_do_token(tok["access_token"])
    print(f"\n🔎 Este token é do canal: {nome} ({cid})")

    esperado = C.get("youtube_channel_id")
    if esperado and cid != esperado:
        raise SystemExit(
            f"❌ CANAL ERRADO. Esperado {esperado} ({C['nome']}).\n"
            f"   Nada foi impresso. Rode de novo e escolha o canal certo na tela do Google.")
    if not esperado:
        print(f"   ⬜ canais.py ainda está sem `youtube_channel_id` pra {C['slug']!r}."
              f" Preencha com: {cid}")

    p = C["env_prefix"]
    valores = {
        f"{p}_CLIENT_ID": args.client_id,
        f"{p}_CLIENT_SECRET": args.client_secret,
        f"{p}_REFRESH_TOKEN": rt,
    }
    print("\n" + "=" * 60)
    if args.gravar_env:
        destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
        gravar_env(os.path.abspath(destino), valores)
        print(f"✅ PRONTO. 3 chaves gravadas em {os.path.abspath(destino)}:\n")
        for k, v in valores.items():
            print(f"   {k} = {v[:6]}...{v[-4:]}  ({len(v)} caracteres)")
    else:
        print("✅ PRONTO. Cole estas 3 linhas no seu .env:\n")
        for k, v in valores.items():
            print(f"{k}={v}")
    print("=" * 60)
    print("\n⚠️ Trate como senha. Nunca commitar.")


if __name__ == "__main__":
    main()
