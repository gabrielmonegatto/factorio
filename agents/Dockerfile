FROM python:3.11-slim

WORKDIR /app

# Instala dependências globais
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os códigos dos agentes
COPY . .

# Porta do FastAPI (se tivermos um listener genérico)
EXPOSE 8001

# Comando de inicialização para manter o container vivo e/ou escutando webhooks
CMD ["uvicorn", "agente_minerador.webhook_listener:app", "--host", "0.0.0.0", "--port", "8001"]
