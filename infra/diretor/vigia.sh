#!/usr/bin/env bash
# O VIGIA: sensação de webhook sem webhook. Cron de 10 em 10 min, ZERO LLM:
# só olha a fila (script puro). Apareceu task auto executável, dispara o
# diretor na hora. flock garante que nunca há dois diretores ao mesmo tempo.
set -u
REPO=/srv/fabrica
[ -f "$REPO/.diretor.env" ] && . "$REPO/.diretor.env"
[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && exit 0

N=$(cd "$REPO" && node tools/notion/fila.mjs --listar 2>/dev/null \
  | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).executaveis.length)}catch{console.log(0)}})")
[ "${N:-0}" -gt 0 ] || exit 0

echo "$(date -u +%FT%T) vigia: $N executaveis, disparando diretor" >> "$REPO/relatorios/logs/diretor.log"
exec flock -n "$REPO/.diretor.lock" "$REPO/infra/diretor/diretor.sh"
