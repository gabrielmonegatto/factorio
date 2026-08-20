#!/usr/bin/env python3
"""
auth_youtube.py — Gera o REFRESH TOKEN do canal (roda UMA vez, na máquina do Gabriel).

Por que existe: o upload precisa de um token que não expira. Este script faz o login
uma única vez e cospe um `refresh_token` que a fábrica usa pra sempre.

⚠️ RODE VOCÊ MESMO — envolve login na sua conta Google. Eu não faço isso por você.

Antes de rodar, no Google Cloud Console:
  1. Crie (ou escolha) um projeto  ← um projeto POR CANAL, pra ter cota separada
  2. Ative a "YouTube Data API v3"
  3. Tela de consentimento OAuth → publique (senão o token expira em 7 dias!)
  4. Credenciais → Criar → ID do cliente OAuth → tipo "App para computador"
  5. Copie o Client ID e o Client Secret

Uso:
  python auth_youtube.py --client-id XXX --client-secret YYY

No fim ele imprime as 3 linhas pra você colar no .env.
"""
import argparse
import http.server
import json
import socketserver
import threading
import urllib.parse
import urllib.request
import webbrowser

# force-ssl é necessário pra POSTAR comentário (o link no 1º comentário). upload = subir vídeo.
# force-ssl posta comentario; yt-analytics.readonly libera METRICA DIARIA
# (views, minutos assistidos, duracao media, inscritos ganhos por dia).
# Sem o de analytics a API responde 403 "insufficient authentication scopes".
SCOPE = " ".join([
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
])
PORT = 8765
REDIRECT = f"http://localhost:{PORT}"
_code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        _code.update(urllib.parse.parse_qs(q))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in _code
        self.wfile.write(
            ("<h2>✅ Autorizado! Pode fechar esta aba e voltar pro terminal.</h2>"
             if ok else "<h2>❌ Falhou. Veja o terminal.</h2>").encode())

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    args = ap.parse_args()

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": args.client_id,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",      # <- sem isso não vem refresh_token
        "prompt": "consent",           # <- força vir o refresh_token mesmo se já autorizou antes
    })

    print("\n🔗 Abrindo o navegador. Faça login com a conta DONA DO CANAL:\n")
    print(auth_url, "\n")

    httpd = socketserver.TCPServer(("", PORT), Handler)
    threading.Thread(target=httpd.handle_request, daemon=True).start()
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("⏳ Aguardando autorização no navegador...")
    while "code" not in _code:
        pass
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

    print("\n" + "=" * 60)
    print("✅ PRONTO. Cole estas 3 linhas no seu .env:\n")
    print(f"YT_CLIENT_ID={args.client_id}")
    print(f"YT_CLIENT_SECRET={args.client_secret}")
    print(f"YT_REFRESH_TOKEN={rt}")
    print("=" * 60)
    print("\n⚠️ Trate como senha. Nunca commitar.")


if __name__ == "__main__":
    main()
