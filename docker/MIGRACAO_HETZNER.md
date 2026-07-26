# 🚚 MIGRAÇÃO — Hostinger KVM2 → Hetzner CX53

> A fábrica é containerizada, então migrar = subir os mesmos containers em outra máquina.
> Tempo: ~1-2h, maior parte a máquina buildando sozinha.
> **Nada é apagado na origem até a nova estar 100% validada.**

---

## Alvo
**Hetzner CX53** — 16 vCPU · 32GB · 320GB · x86 · ~€30/mês (~R$189)
(x86 = imagens Docker rodam iguais, sem mexer em nada)

---

## O que migra
| Item | Como |
|---|---|
| Teable (o banco) | restaurar o `pg_dump` na máquina nova |
| Imagens Docker (render + tts) | rebuildar do código (git) |
| Código `_factorio` | git clone |
| `.env` | copiar (credenciais) |
| Assets/vídeos | JÁ estão no R2 — não migram, são externos |

---

## Passo a passo

### 1. Provisionar a Hetzner
- Criar conta (pode pedir verificação de identidade — fazer com antecedência)
- Criar servidor **CX53**, Ubuntu 24.04, adicionar a chave SSH `id_ed25519_factorio`
- Anotar o novo IP

### 2. Backup fresco da origem (Hostinger)
```bash
ssh root@187.127.44.153 "docker exec factorio_teable_db pg_dump -U teable teable | gzip > /root/teable_migracao.sql.gz"
scp root@187.127.44.153:/root/teable_migracao.sql.gz .
```

### 3. Preparar a Hetzner
```bash
# instalar docker
curl -fsSL https://get.docker.com | sh
# clonar o repo + copiar .env (via scp do teu PC)
git clone <repo> /app/_factorio    # ou rsync da Hostinger
mkdir -p /srv/factorio/{data/public,data/hybrid,hfcache}
# copiar o .env pra /srv/factorio/.env e /app/_factorio/.env
```

### 4. Subir o Teable (docker-compose SÓ com o banco)
> Usar um compose enxuto: teable + teable-db + teable-cache + caddy. (Outline/legado NÃO sobem.)
```bash
# restaurar o dump ANTES de subir o teable
# (subir só o postgres, restaurar, depois o resto)
gunzip < teable_migracao.sql.gz | docker exec -i <teable_db> psql -U teable teable
```

### 5. Buildar as imagens da fábrica
```bash
cd /app/_factorio
docker build -f docker/Dockerfile.tts -t factorio-tts .
cd remotion && docker build -t factorio-render:v5 .
```

### 6. Validar
```bash
# teable responde?
curl -sI localhost:3000
# render de 1 vídeo (com FACTORY_CPUS alto, agora tem 16 núcleos)
FACTORY_CPUS=8 ./docker/factory.sh render 4
```

### 7. Cortada (DNS/apps)
- Repontar o que apontava pra `187.127.44.153` (db.markeologia.com.br etc.) pro IP novo
- Rodar 7 dias em paralelo antes de desligar a Hostinger

### 8. Aproveitar os 16 núcleos (as LANES)
Com CX53, dá pra rodar em paralelo (cada um com teto de CPU):
- `FACTORY_CPUS=8` lane de vídeos longos
- `FACTORY_CPUS=4` lane de cortes/curtos
- narração (leve) + Teable sempre com folga

---

## ⚠️ Cuidados
- **Backup do Docker Hub:** subir `factorio-render` pro Docker Hub como seguro (uma sessão já apagou as imagens locais uma vez).
- **GPU:** Hetzner não tem. Modelos pesados (imagem/vídeo IA) continuam no RunPod.
- **Não apagar a Hostinger** até a Hetzner rodar 7 dias limpa.
