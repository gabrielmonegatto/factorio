#!/usr/bin/env bash
# Páreo de vozes PT-BR na CPU da VPS. Roda destacado (nohup); tudo em $OUT/log.txt.
# Custo: zero dinheiro. Tempo: horas (CPU), por isso é overnight.
set -u
D=/app/_factorio/docker
OUT=/srv/factorio/data/bakeoff_pt
TXT=/tmp/voz_pt/trecho_pt.txt
mkdir -p "$OUT"; cp "$TXT" "$OUT/trecho_pt.txt"
log(){ echo "$(date -u +%FT%T) $*" >> "$OUT/log.txt"; }

log "== omnivoice (design, 3 candidatas) =="
docker run --rm --name factorio_bakeoff_omni --cpus=6 --memory=12g \
  -v "$OUT":/data -v "$D":/scripts -v /srv/factorio/hfcache:/cache \
  --entrypoint python3 factorio-omnivoice:v1 /scripts/omni_catalogo.py \
  --text-file /data/trecho_pt.txt --lang Portuguese --out-dir /data/omni >> "$OUT/log.txt" 2>&1
log "omni exit=$?"

log "== build chatterbox =="
docker build -q -f "$D/Dockerfile.vozes" --build-arg MOTOR=chatterbox -t factorio-vozes:chatterbox "$D" >> "$OUT/log.txt" 2>&1
log "build chatterbox exit=$?"
docker run --rm --name factorio_bakeoff_chatterbox --cpus=6 --memory=12g \
  -v "$OUT":/data -v /srv/factorio/hfcache:/cache factorio-vozes:chatterbox \
  --motor chatterbox --text-file /data/trecho_pt.txt --out-dir /data/chatterbox >> "$OUT/log.txt" 2>&1
log "chatterbox exit=$?"

log "== build qwen =="
docker build -q -f "$D/Dockerfile.vozes" --build-arg MOTOR=qwen -t factorio-vozes:qwen "$D" >> "$OUT/log.txt" 2>&1
log "build qwen exit=$?"
docker run --rm --name factorio_bakeoff_qwen --cpus=8 --memory=16g \
  -v "$OUT":/data -v /srv/factorio/hfcache:/cache factorio-vozes:qwen \
  --motor qwen --text-file /data/trecho_pt.txt --out-dir /data/qwen >> "$OUT/log.txt" 2>&1
log "qwen exit=$?"
log "== FIM =="
