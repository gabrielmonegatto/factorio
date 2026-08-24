#!/usr/bin/env bash
# ─── deploy_vps.sh — leva o repo pra produção na VPS ────────────────────────
#
# ## Por que existe
#
# Até 24/08/2026 não existia deploy. Alguém copiou os arquivos na mão em
# 15/08 e pronto. O resultado apareceu quando o agendador do Spurgeon passou
# DIAS agendando ZERO vídeos: o `schedule_channel.py` do host já passava
# `--canal`, mas o `build_job.py` de dentro da imagem Docker era de 15/08 e
# não conhecia o argumento. Duas cópias do mesmo código, divergindo em
# silêncio, e o canal só não parou porque tinha 23 vídeos já agendados.
#
# ## O que este script assume
#
# A VERDADE é o repo. A VPS é um espelho. Nada de editar arquivo direto lá.
#
# Dois destinos, e os dois importam:
#   /app/_factorio/          → os orquestradores que rodam NO HOST
#                              (render_buffer, schedule_channel, cron)
#   factorio-render:vN       → a imagem onde roda o que precisa de Remotion
#                              (hybrid_render, build_job, publish_sermon)
#
# Esquecer o segundo foi exatamente o que quebrou a produção.
#
# Uso:
#   scripts/deploy_vps.sh              # sincroniza + rebuild se o código mudou
#   scripts/deploy_vps.sh --sem-imagem # só os scripts do host (mais rápido)
#   scripts/deploy_vps.sh --so-imagem  # só a imagem
set -euo pipefail

VPS=${VPS:-root@167.233.236.209}
CHAVE=${CHAVE:-$HOME/.ssh/id_ed25519_factorio}
DESTINO=/app/_factorio
IMAGEM=${IMAGEM:-factorio-render:v5}
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH="ssh -i $CHAVE -o StrictHostKeyChecking=no $VPS"
sem_imagem=0; so_imagem=0
for a in "$@"; do
  [ "$a" = "--sem-imagem" ] && sem_imagem=1
  [ "$a" = "--so-imagem" ] && so_imagem=1
done

# ── 1. código ──────────────────────────────────────────────────────────────
# `public/` e `_hybrid/` NÃO entram: são dados de produção (assets baixados e
# renders em andamento). Apagar isso obrigaria a rebaixar tudo do R2.
if [ "$so_imagem" = 0 ]; then
  echo "── sincronizando código → $DESTINO"
  rsync -az --delete -e "ssh -i $CHAVE -o StrictHostKeyChecking=no" \
    --exclude 'public/' --exclude '_hybrid/' --exclude '_narrate/' \
    --exclude '_narrar/' --exclude '_ctas/' --exclude 'node_modules/' \
    --exclude '__pycache__/' --exclude 'out/' --exclude '.remotion/' \
    "$AQUI/remotion/" "$VPS:$DESTINO/remotion/"
  rsync -az --delete -e "ssh -i $CHAVE -o StrictHostKeyChecking=no" \
    "$AQUI/docker/" "$VPS:$DESTINO/docker/"
  rsync -az -e "ssh -i $CHAVE -o StrictHostKeyChecking=no" \
    "$AQUI/scripts/" "$VPS:$DESTINO/scripts/"
  $SSH "chmod +x $DESTINO/docker/*.sh $DESTINO/scripts/*.sh 2>/dev/null || true"
fi

# ── 2. imagem ──────────────────────────────────────────────────────────────
# O `npm ci` e o `remotion browser ensure` ficam em camadas ANTES do COPY do
# código, então mudança de .py ou .tsx reconstrói só as camadas finais.
if [ "$sem_imagem" = 0 ]; then
  echo "── reconstruindo $IMAGEM (o código de render mora AQUI DENTRO)"
  $SSH "cd $DESTINO/remotion && docker build -f Dockerfile -t $IMAGEM . 2>&1 | tail -3"
fi

# ── 3. prova de que chegou ─────────────────────────────────────────────────
echo "── conferindo"
$SSH "docker run --rm --entrypoint python3 $IMAGEM /app/build_job.py --help 2>&1 | grep -q -- --canal \
      && echo '   ✅ a imagem aceita --canal' \
      || { echo '   ❌ a imagem AINDA não aceita --canal'; exit 1; }"
$SSH "grep -q add_arg_canal $DESTINO/remotion/render_buffer.py \
      && echo '   ✅ render_buffer do host está por canal' \
      || echo '   ⚠️  render_buffer do host ainda não é por canal'"
echo "── pronto"
