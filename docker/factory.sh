#!/usr/bin/env bash
# ─── factory.sh — roda os jobs da fábrica na VPS ────────────────────────────
# Todo job roda com TETO de CPU e memória. Isso garante que um render pesado
# NUNCA consiga derrubar o Teable (o banco tem sempre folga reservada).
#
# Uso:
#   ./factory.sh narrate --input /data/texto.txt --output /data/audio.wav
#   ./factory.sh render 3 moody    # renderiza o sermão 0003 do canal moody
#   ./factory.sh shell             # abre um shell no container de render (debug)
set -euo pipefail

ROOT=${FACTORY_ROOT:-/srv/factorio}
DATA="$ROOT/data"
ENVFILE="$ROOT/.env"
# imagem buildada NA PRÓPRIA VPS (evita transferir 5.5GB do Docker Hub).
# Pra usar a do Hub: RENDER_IMAGE=monegatto/spurgeon-render:v5 ./factory.sh render N
RENDER_IMAGE=${RENDER_IMAGE:-factorio-render:v5}
TTS_IMAGE=${TTS_IMAGE:-factorio-tts}

# Numa KVM2 (2 núcleos), 1.5 deixa meio núcleo reservado pro Teable.
# Numa KVM4, pode subir pra 3. Ajuste via env: FACTORY_CPUS=3 ./factory.sh render 3
CPUS=${FACTORY_CPUS:-1.5}
MEM=${FACTORY_MEM:-4g}

LIMITS=(--cpus="$CPUS" --memory="$MEM" --memory-swap="$MEM")

# ── Container com NOME e morte garantida ───────────────────────────────────
#
# `docker run` é CLIENTE. Matar o cliente não mata o container: o daemon segue
# rodando aquilo. Em 25/08, um `systemctl restart factory-producer@moody`
# deixou um `factorio-render` a 401% de CPU vivo, e o produtor novo subiu OUTRO
# por cima. Nome aleatório do Docker (`confident_margulis`), impossível saber
# olhando o que era trabalho e o que era lixo.
#
# Pior: o semáforo de CPU (`remotion/vaga_cpu.py`) fica CEGO, porque zumbi não
# pede vaga. A máquina enche e o painel jura que está livre.
#
# `--rm` não resolve: ele limpa depois que o container PARA, e o problema é
# justamente o container que não para.
matar_container() { docker rm -f "$1" >/dev/null 2>&1 || true; }

rodar_nomeado() {
  local nome=$1; shift
  matar_container "$nome"                       # sobra de execução morta
  trap 'matar_container '"$nome"'' EXIT INT TERM
  docker run --rm --name "$nome" "$@"
}

case "${1:-}" in
  narrate)
    shift
    rodar_nomeado "factorio_narrate_$$" "${LIMITS[@]}" \
      -v "$DATA":/data -v "$ROOT/hfcache":/cache \
      "$TTS_IMAGE" "$@"
    ;;
  render)
    SERMON=${2:?informe o número do sermão, ex: ./factory.sh render 3}
    # ⚠️ O CANAL É OBRIGATÓRIO passar. Sem ele o hybrid_render cai no default
    # (spurgeon) e renderiza o vídeo do canal errado, sem erro nenhum.
    CANAL=${3:?informe o canal, ex: ./factory.sh render 3 moody}
    rodar_nomeado "factorio_render_${CANAL}_${SERMON}" "${LIMITS[@]}" \
      --env-file "$ENVFILE" \
      -v "$DATA/public":/app/public \
      -v "$DATA/hybrid":/app/_hybrid \
      "$RENDER_IMAGE" python3 -u hybrid_render.py --canal "$CANAL" --sermon "$SERMON"
    ;;
  shell)
    docker run --rm -it "${LIMITS[@]}" --env-file "$ENVFILE" \
      -v "$DATA/public":/app/public "$RENDER_IMAGE" bash
    ;;
  *)
    echo "uso: $0 {narrate|render <N> <canal>|shell}"; exit 1
    ;;
esac
