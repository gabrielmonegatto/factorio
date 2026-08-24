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

# FONTE GEORGIA — a legenda do canal usa Georgia (fonte da Microsoft, não vem no Linux).
# Sem ela o libass substitui por outra serif e a legenda sai DIFERENTE do Remotion.
# O `fc-list | grep -i georgia` no fim FALHA O BUILD se a fonte não instalar (melhor
# descobrir aqui do que num vídeo publicado com a fonte errada).
RUN echo "deb http://deb.debian.org/debian bookworm contrib non-free" > /etc/apt/sources.list.d/contrib.list && \
    apt-get update && \
    echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections && \
    apt-get install -y --no-install-recommends ttf-mscorefonts-installer fontconfig && \
    fc-cache -fv && \
    fc-list | grep -i georgia && \
    rm -rf /var/lib/apt/lists/*

# Instala as bibliotecas de Python necessárias para o RunPod Serverless + geração de QR
RUN pip3 install --no-cache-dir --break-system-packages runpod boto3 "qrcode[pil]"

# Configura o Puppeteer para usar o Chromium instalado no sistema
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Diretório de trabalho no container
WORKDIR /app

# Copia dependências primeiro para cachear as camadas do Docker
COPY package.json package-lock.json ./
RUN npm ci

# ⚠️ ORDEM IMPORTA. O `browser ensure` vem ANTES do COPY do código porque é um
# download de ~150MB: se ele ficasse depois, toda mudança de .py ou .tsx
# invalidaria a camada e o deploy baixaria o Chrome de novo. Como agora existe
# deploy de verdade (scripts/deploy_vps.sh) isso deixou de ser raro.
RUN npx remotion browser ensure

# Código por último: é a camada que muda a cada deploy.
COPY . .

# Comando de boot do container: inicia o handler do RunPod
CMD ["python3", "-u", "rp_handler.py"]
