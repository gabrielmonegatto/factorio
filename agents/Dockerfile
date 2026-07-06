FROM python:3.11-slim

WORKDIR /app

# Instala dependências de sistema (Git, xz-utils para descompressão de pacotes e ca-certificates)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    xz-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala Hermes Agent
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Copia os códigos dos agentes
COPY . .

# Copia profile do Diretor VPS
RUN mkdir -p /root/.hermes/profiles/diretor-vps
COPY diretor-vps/config.yaml /root/.hermes/profiles/diretor-vps/config.yaml
COPY diretor-vps/.env /root/.hermes/profiles/diretor-vps/.env

# Portas
EXPOSE 8001 3111

# Entrypoint: sobe webhook listener + gateway Discord
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]