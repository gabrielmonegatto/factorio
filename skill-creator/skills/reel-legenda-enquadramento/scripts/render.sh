#!/usr/bin/env bash
# Renderiza a camada de legenda com ALPHA e compõe sobre o vídeo reenquadrado.
#
#   bash render.sh <projdir> <reframed.mp4> <final.mp4>
#
# O vídeo NUNCA passa pelo Chrome: renderiza-se só a legenda (WebM/VP9 com alpha) e
# o ffmpeg sobrepõe. Assim a imagem não sofre um segundo reencode de geração.
set -euo pipefail

PROJ="${1:?uso: render.sh <projdir> <reframed.mp4> <final.mp4>}"
SRC="${2:?falta o vídeo reenquadrado}"
OUT="${3:?falta o caminho de saída}"

FPS="$(ffprobe -v error -select_streams v -show_entries stream=r_frame_rate \
        -of csv=p=0 "$SRC" | awk -F/ '{printf "%d", ($2 ? $1/$2 : $1)}')"

export PRODUCER_BROWSER_GPU_MODE="${PRODUCER_BROWSER_GPU_MODE:-hardware}"
( cd "$PROJ" && npx hyperframes render . --format webm -f "$FPS" -o cap.webm --quiet )

# -c:v libvpx-vp9 vem ANTES do -i da legenda: é o DECODER daquele input.
# (Se cair depois, o ffmpeg tenta decodificar o webm com o codec errado e morre
#  com "Decoder not found" — parece falta de suporte, mas é ordem de argumento.)
ffmpeg -y -loglevel error -i "$SRC" -c:v libvpx-vp9 -i "$PROJ/cap.webm" \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto[v]" -map "[v]" -map 0:a \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a copy "$OUT"

echo "  -> $OUT"
