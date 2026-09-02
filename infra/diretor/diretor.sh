#!/usr/bin/env bash
# Cadência do diretor-diário (piloto 01/09/2026). Roda por cron na VPS.
# Sem token, sai em silêncio: dá pra instalar o cron antes do gate da credencial.
#
# Segredos em /srv/fabrica/.diretor.env (NUNCA no git):
#   CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat...   (gerado pelo Gabriel: `claude setup-token`)
set -u
REPO=/srv/fabrica
LOG_DIR=$REPO/relatorios/logs
mkdir -p "$LOG_DIR"

[ -f /srv/fabrica/.diretor.env ] && . /srv/fabrica/.diretor.env
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  echo "$(date -u +%FT%T) sem token, cadência dormindo" >> "$LOG_DIR/diretor.log"
  exit 0
fi
export CLAUDE_CODE_OAUTH_TOKEN

cd "$REPO"
# fila local espelhada do bare (o desktop empurra pro bare a cada push)
git pull --ff-only -q origin master || true

STAMP=$(date -u +%F-%H%M)
"$HOME/.local/bin/claude" -p "/diretor-diario" \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
  --permission-mode acceptEdits \
  >> "$LOG_DIR/diretor-$STAMP.log" 2>&1
echo "$(date -u +%FT%T) cadência $STAMP exit=$?" >> "$LOG_DIR/diretor.log"
