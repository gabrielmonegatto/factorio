#!/usr/bin/env bash
# ─── esteira_canal.sh — liga/desliga a esteira de UM canal na VPS ───────────
#
# ## O modelo (corrigido em 24/08 pelo Gabriel)
#
# Cada canal é uma ESTEIRA ISOLADA, com fila própria e estoque próprio,
# chamando serviços compartilhados (narrar, legendar, renderizar). Não é um
# pipeline gigante que atende N canais: são N pipelines iguais, cada um
# cuidando do seu.
#
# Antes disso existia um `factory-producer.service` único, cravado no Spurgeon.
# Canal novo não tinha onde nascer, e foi por isso que o Moody ficou pronto no
# código e parado no runtime.
#
# ## O que uma esteira tem
#
#   cron  factory-<canal>  (de hora em hora)
#       PREPARO: narrado -> pronto (gera copy e narra hook/outro)
#   factory-producer@<canal>.service  (24/7)
#       RENDER: pronto -> mp4, mantendo estoque à frente do calendário
#   cron  factory-<canal>  (1x/dia)
#       AGENDA: mp4 -> calendário do YouTube
#
# As três etapas são independentes e idempotentes: cada uma olha o estado no R2
# e faz o que falta. Não existe orquestrador segurando a mão de ninguém.
#
# O `@` do systemd é de propósito: UM arquivo de unidade serve todos os canais,
# e o slug entra como instância. Canal novo é `ligar <slug>`, não copiar arquivo.
#
# Uso (na VPS, ou por ssh):
#   ./esteira_canal.sh ligar moody
#   ./esteira_canal.sh estado
#   ./esteira_canal.sh desligar moody
#   ./esteira_canal.sh logs moody
set -euo pipefail

APP=${APP:-/app/_factorio}
UNIDADE=/etc/systemd/system/factory-producer@.service

instalar_unidade() {
  cat > "$UNIDADE" <<'UNIT'
[Unit]
Description=Esteira de render 24/7 do canal %i
After=docker.service network-online.target
Wants=docker.service

[Service]
Type=simple
WorkingDirectory=/app/_factorio/remotion
# --cpus 8 e não 16: o narrador (factorio-tts) e o ASR dividem a mesma máquina.
# Render sozinho comendo tudo faz a narração de outro canal rastejar.
ExecStart=/usr/bin/python3 -u render_buffer.py --canal %i --loop --cpus 8 --sleep 1800
Restart=always
RestartSec=30
StandardOutput=append:/var/log/factory_producer_%i.log
StandardError=append:/var/log/factory_producer_%i.log

[Install]
WantedBy=multi-user.target
UNIT
  systemctl daemon-reload
}

cron_do_canal() {
  local canal=$1 hora=$2 min=$3
  cat > "/etc/cron.d/factory-$canal" <<CRON
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SHELL=/bin/bash

# ── NARRAR: capítulo minerado -> sermão narrado ────────────────────────────
# ⚠️ ESTA ETAPA FALTAVA e é o motivo do Spurgeon ter travado em 113 vídeos
# tendo 3.541 capítulos minerados no D1: a narração era um comando MANUAL,
# fora da esteira. Acervo grande não vale nada se ninguém puxa dele.
# ORÇAMENTO, não lote fixo (corrigido 25/08 depois de MEDIR).
# ⚠️ Sem crases aqui dentro: o heredoc CRON é NÃO-quotado (precisa expandir
# \$canal e \$APP), então crase vira substituição de comando e o bash TENTA
# EXECUTAR o texto do comentário. Foi o "--limite: command not found" de 25/08.
# Era --limite 2: 2 sermões x ~23 min = 47 min de trabalho numa janela de
# 240 min. A VPS (16 vCPU) ficava com load 0.03 e o Spurgeon precisaria de
# 294 DIAS pra vencer 3.533 capítulos que já estavam minerados e parados.
# Agora a janela é usada de verdade: narra até 200 min (sobra folga pro último
# terminar dentro das 4h) e nunca corta um sermão no meio. ~48/dia, 4x mais.
0 */4 * * * root cd $APP/remotion && flock -n /tmp/narrar_$canal.lock python3 narrar_sermao.py --canal $canal --limite 20 --minutos 200 --cpus 8 >> /var/log/factory_narrar_$canal.log 2>&1

# ── PREPARO: sermão narrado -> sermão PRONTO PRA RENDER ────────────────────
# Sem esta etapa o produtor fica dormindo com a fila cheia: o narrado não é
# "pronto" enquanto não tiver copy e hook. Foi o que aconteceu com o Moody,
# 74 narrados e só 1 renderizável.
# De hora em hora, em lotes pequenos, pra dividir a máquina com a narração.
$min * * * * root cd $APP/remotion && flock -n /tmp/prep_$canal.lock bash -c 'python3 generate_marketing.py --canal $canal --all --limit 6 && python3 narrate_marketing.py --canal $canal --all --limit 6' >> /var/log/factory_prep_$canal.log 2>&1

# ── AGENDA: renderizado -> calendário do YouTube ───────────────────────────
# lock POR CANAL: duas esteiras podem agendar ao mesmo tempo sem se atrapalhar
$hora root cd $APP/remotion && flock -n /tmp/sched_$canal.lock python3 schedule_channel.py --canal $canal >> /var/log/factory_schedule_$canal.log 2>&1
CRON
}

case "${1:-}" in
  ligar)
    CANAL=${2:?informe o canal, ex: ./esteira_canal.sh ligar moody}
    # erra cedo: canal que o canais.py não conhece não vira serviço
    cd "$APP/remotion" && python3 -c "import canais; canais.get('$CANAL')"
    instalar_unidade
    # Minutos diferentes por canal, de propósito: agendar é upload pro YouTube,
    # e a cota da API é do PROJETO inteiro, compartilhada entre os canais.
    # Empilhar tudo no mesmo minuto é a receita pra estourar a cota junto.
    case "$CANAL" in
      spurgeon) HORA="0 6 * * *";  MIN="5"  ;;
      moody)    HORA="20 6 * * *"; MIN="25" ;;
      *)        HORA="40 6 * * *"; MIN="45" ;;
    esac
    cron_do_canal "$CANAL" "$HORA" "$MIN"
    systemctl enable --now "factory-producer@$CANAL"
    echo "✅ esteira do $CANAL ligada: preparo (min $MIN de cada hora) + produtor 24/7 + agendador '$HORA'"
    ;;
  desligar)
    CANAL=${2:?informe o canal}
    systemctl disable --now "factory-producer@$CANAL" 2>/dev/null || true
    rm -f "/etc/cron.d/factory-$CANAL"
    echo "🛑 esteira do $CANAL desligada (nada foi apagado do R2 nem do D1)"
    ;;
  estado)
    echo "── produtores"
    systemctl list-units 'factory-producer@*' --no-pager --no-legend 2>/dev/null \
      | awk '{printf "   %-34s %s %s\n", $1, $3, $4}' || echo "   (nenhum)"
    echo "── agendadores"
    ls /etc/cron.d/ 2>/dev/null | grep '^factory-' | sed 's/^/   /' || echo "   (nenhum)"
    ;;
  logs)
    CANAL=${2:?informe o canal}
    tail -n "${3:-30}" "/var/log/factory_producer_$CANAL.log"
    ;;
  *)
    echo "uso: $0 {ligar <canal>|desligar <canal>|estado|logs <canal> [n]}"; exit 1
    ;;
esac
