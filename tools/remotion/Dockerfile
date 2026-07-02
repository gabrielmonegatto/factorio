# Imagem base oficial do Node.js (Debian Bookworm)
FROM node:20-bookworm

# Instala o Chromium e as dependências de fontes e áudio, mais o Python para o RunPod
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    libglu1-mesa \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Instala as bibliotecas de Python necessárias para o RunPod Serverless
RUN pip3 install --no-cache-dir --break-system-packages runpod boto3

# Configura o Puppeteer para usar o Chromium instalado no sistema
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Diretório de trabalho no container
WORKDIR /app

# Copia dependências primeiro para cachear as camadas do Docker
COPY package.json package-lock.json ./
RUN npm ci

# Copia o restante do código do Remotion
COPY . .

# Comando de boot do container: inicia o handler do RunPod
CMD ["python3", "-u", "rp_handler.py"]
