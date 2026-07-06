#!/bin/bash
# Entrypoint do container factorio_agents
# Sobe o webhook listener + gateway do Hermes (Diretor VPS)

set -e

echo "🚀 Iniciando Fábrica EternalL - Diretor VPS"
echo "============================================"

# 1. Sobe o webhook listener (FastAPI) em background
echo "📡 Iniciando webhook listener na porta 8001..."
cd /app
uvicorn agente_minerador.webhook_listener:app --host 0.0.0.0 --port 8001 &
WEBHOOK_PID=$!
echo "   Webhook PID: $WEBHOOK_PID"

# Aguarda webhook ficar pronto
sleep 3

# Verifica se webhook subiu
if kill -0 $WEBHOOK_PID 2>/dev/null; then
    echo "✅ Webhook listener OK"
else
    echo "❌ Webhook listener falhou"
    exit 1
fi

# 2. Sobe o Hermes Gateway (Diretor VPS) 
echo "🤖 Iniciando Hermes Gateway (profile: diretor-vps)..."
cd /root/.hermes

# Define o profile ativo para o gateway
export HERMES_PROFILE=diretor-vps

# Gateway roda em foreground (container fica vivo)
echo "   Gateway Discord conectando..."
hermes gateway run --profile diretor-vps