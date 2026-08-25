#!/usr/bin/env python3
"""aplicar_capas_pendentes.py — põe a capa nos vídeos que subiram sem ela.

## Por que existe

A capa é ESSENCIAL: é ela que decide o clique. Mas em 24/08, na primeira
tentativa de inaugurar o Moody, o `set_thumbnail` derrubava a publicação
inteira (canal novo não podia subir capa própria: o YouTube exige verificação
por telefone e devolve 403). O vídeo SUBIA, o script morria logo depois e o
agendador achava que nada tinha sido publicado — sete uploads órfãos.

O `publish_youtube.py` passou a tratar a falha de capa como não-fatal, e a
anotar o vídeo numa fila. Isso só é aceitável porque ESTE script existe: sem
ele, "publicou sem capa" viraria um estado permanente e invisível.

Publicar sem capa é estado TEMPORÁRIO e rastreado. Este script é quem fecha
o ciclo.

## Uso

    python aplicar_capas_pendentes.py --canal moody            # mostra o que falta
    python aplicar_capas_pendentes.py --canal moody --aplicar  # aplica de verdade
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

import canais
import publish_youtube as P

HERE = os.path.dirname(os.path.abspath(__file__))

# A fila pode ter sido escrita de dois lugares: pelo script rodando no host, ou
# de dentro do container (que monta /srv/factorio/data/public em /app/public).
# Procurar nos dois é o que evita "a fila está vazia" quando ela só está noutro
# caminho — e fila que o dono não acha é igual a fila que não existe.
CANDIDATOS = [
    os.path.join(HERE, "public", "_capas_pendentes.json"),
    os.path.join(HERE, "_capas_pendentes.json"),
    "/srv/factorio/data/public/_capas_pendentes.json",
]


def filas():
    """Todos os arquivos de fila que existem, sem repetir o mesmo caminho."""
    vistos, achados = set(), []
    for c in CANDIDATOS:
        real = os.path.realpath(c)
        if real not in vistos and os.path.exists(real):
            vistos.add(real)
            achados.append(real)
    return achados


def ler(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  não deu pra ler {caminho}: {str(e)[:120]}")
        return []


def do_canal(token, video_id):
    """True se o vídeo é do canal autenticado. Não aplicar capa em vídeo alheio."""
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}",
        headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=40) as r:
        itens = json.loads(r.read()).get("items", [])
    if not itens:
        return None            # sumiu (deletado) — não é erro, é lixo pra limpar
    return itens[0]["snippet"]["channelId"]


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--aplicar", action="store_true",
                    help="sem isto, só mostra o que faria")
    args = ap.parse_args()

    C = canais.get(args.canal)
    P.C = C

    achadas = filas()
    if not achadas:
        print("✅ nenhuma fila de capas pendentes — todo vídeo saiu com capa.")
        return

    token = P.access_token(P.load_env())   # já aborta se o token for de outro canal
    total = feitos = sumidos = alheios = erros = 0

    for caminho in achadas:
        fila = ler(caminho)
        if not fila:
            continue
        print(f"\n📄 {caminho} · {len(fila)} na fila")
        restantes = []
        for item in fila:
            vid, thumb = item.get("video_id"), item.get("thumb")
            total += 1
            dono = do_canal(token, vid)
            if dono is None:
                print(f"   🗑️  {vid} não existe mais — tirando da fila")
                sumidos += 1
                continue
            if dono != C["youtube_channel_id"]:
                print(f"   ⛔ {vid} é do canal {dono}, não do {C['slug']} — deixando na fila")
                alheios += 1
                restantes.append(item)
                continue
            if not thumb or not os.path.exists(thumb):
                print(f"   ❌ {vid}: capa some do disco ({thumb}) — precisa re-renderizar")
                erros += 1
                restantes.append(item)
                continue
            if not args.aplicar:
                print(f"   👀 {vid} ← {os.path.basename(thumb)} (motivo: {item.get('motivo','?')})")
                restantes.append(item)
                continue
            try:
                dados = open(thumb, "rb").read()
                req = urllib.request.Request(
                    f"{P.THUMB_URL}?videoId={vid}", data=dados, method="POST",
                    headers={"Authorization": "Bearer " + token,
                             "Content-Type": "image/png"})
                urllib.request.urlopen(req, timeout=120)
                print(f"   ✅ {vid} recebeu a capa")
                feitos += 1
            except urllib.error.HTTPError as e:
                corpo = e.read().decode("utf-8", "replace")[:200]
                print(f"   ❌ {vid}: HTTP {e.code} — {corpo}")
                erros += 1
                restantes.append(item)

        # Só reescreve quando aplicou: um dry-run não pode mexer na fila.
        if args.aplicar:
            if restantes:
                json.dump(restantes, open(caminho, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            else:
                os.remove(caminho)
                print("   🧹 fila zerada, arquivo removido")

    print(f"\n🏁 na fila={total} · aplicadas={feitos} · sumidos={sumidos} "
          f"· de outro canal={alheios} · erros={erros}")
    if not args.aplicar and total:
        print("   (isto foi só a prévia — rode de novo com --aplicar)")
    if erros:
        sys.exit(1)


if __name__ == "__main__":
    main()
