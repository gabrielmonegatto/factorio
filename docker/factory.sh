#!/usr/bin/env bash
# ─── factory.sh — roda os jobs da fábrica na VPS ────────────────────────────
# Todo job roda com TETO de CPU e memória. Isso garante que um render pesado
# NUNCA consiga derrubar o Teable (o banco tem sempre folga reservada).
#
# Uso:
#   ./factory.sh narrate --input /data/texto.txt --output /data/audio.wav
#   ./factory.sh render 3          # renderiza o sermão 0003 (híbrido)
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

case "${1:-}" in
  narrate)
    shift
    docker run --rm "${LIMITS[@]}" \
      -v "$DATA":/data -v "$ROOT/hfcache":/cache \
      "$TTS_IMAGE" "$@"
    ;;
  render)
    SERMON=${2:?informe o número do sermão, ex: ./factory.sh render 3}
    docker run --rm "${LIMITS[@]}" \
      --env-file "$ENVFILE" \
      -v "$DATA/public":/app/public \
      -v "$DATA/hybrid":/app/_hybrid \
      "$RENDER_IMAGE" python3 -u hybrid_render.py --sermon "$SERMON"
    ;;
  shell)
    docker run --rm -it "${LIMITS[@]}" --env-file "$ENVFILE" \
      -v "$DATA/public":/app/public "$RENDER_IMAGE" bash
    ;;
  *)
    echo "uso: $0 {narrate|render <N>|shell}"; exit 1
    ;;
esac
