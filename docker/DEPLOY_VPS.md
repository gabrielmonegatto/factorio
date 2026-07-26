# 🚀 DEPLOY — Fábrica de vídeo na VPS

> Como transformar a VPS (hoje só banco) na fábrica de vídeo.
> **Ordem importa.** Especialmente o passo 2 (Kokoro) antes do passo 5 (limpeza).

---

## O desenho final

```
FICA:   factorio_teable · factorio_teable_db · factorio_teable_cache · factorio_proxy
ENTRA:  factorio-tts (Kokoro)  ·  spurgeon-render (Remotion+ffmpeg)   ← jobs sob demanda
SAI:    outline x2 · outline_db · outline_redis · minio · mcp_universal
        · agent_memory · factorio_agents · redis órfão
```

Os dois containers novos **não ficam ligados** — sobem, fazem o trabalho e morrem. VPS leve o tempo todo.

---

## ⚠️ PASSO 0 — BACKUP (não pule)

Todo o banco da fábrica mora nessa máquina. Antes de mexer em qualquer coisa:

```bash
# dump do Teable
docker exec factorio_teable_db pg_dump -U teable teable | gzip > /root/teable_$(date +%F).sql.gz

# manda pro R2 (ou baixa pro teu PC via scp)
ls -lh /root/teable_*.sql.gz
```

Confere que o arquivo tem tamanho razoável **antes** de seguir.

---

## PASSO 1 — Preparar a pasta da fábrica

```bash
mkdir -p /srv/factorio/{data/public,data/hybrid,hfcache}
cd /srv/factorio

# copie o .env com as credenciais R2 (R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
# R2_ENDPOINT, R2_PUBLIC_URL) — NUNCA commitar este arquivo
nano /srv/factorio/.env
```

---

## PASSO 2 — Kokoro em container próprio (ANTES de matar o legado)

> 🚨 Hoje o Kokoro roda **dentro** do `factorio_agents`. Se você desligar aquele container
> antes disto, perde a narração. Faça este passo primeiro.

```bash
# no diretório do repo _factorio na VPS
docker build -f docker/Dockerfile.tts -t factorio-tts .

# teste: narra um texto curto
echo "Grace and peace to you." > /srv/factorio/data/teste.txt
./docker/factory.sh narrate --input /data/teste.txt --output /data/teste.wav --voice bm_george

# confere que gerou áudio
ls -lh /srv/factorio/data/teste.wav
```

✅ Só siga adiante quando o `teste.wav` existir e tocar corretamente.

---

## PASSO 3 — Imagem de render

```bash
docker pull monegatto/spurgeon-render:v5

# sanity check da fonte (a legenda depende da Georgia)
docker run --rm monegatto/spurgeon-render:v5 bash -c "fc-list | grep -i georgia"
```

Se **não** listar Georgia, pare — a legenda sairia com fonte errada.

---

## PASSO 4 — Primeiro vídeo na VPS

```bash
chmod +x docker/factory.sh
./docker/factory.sh render 3      # renderiza o sermão 0003

# acompanhe; ao final ele sobe pro R2 em renders/spurgeon/0003.mp4
```

⏱️ **Meça o tempo.** Numa KVM2 esperamos ~35-40 min. É esse número que decide se vale
o upgrade pra KVM4.

---

## PASSO 5 — Limpeza do legado (só depois que os passos acima passaram)

```bash
# para (não apaga volumes — reversível)
docker stop outline_holding outline_br4nds outline_db outline_redis outline_minio \
            factorio_mcp_universal factorio_agent_memory factorio_agents factorio_redis

# 7 dias depois, se nada fez falta:
# docker rm <containers>   (volumes continuam intactos)
```

Depois: limpar as rotas mortas do Caddyfile (`agents.`, `memory.`, `mcp.`, `minio.`).

---

## 🛡️ Proteção do Teable

O `factory.sh` roda todo job com **teto de CPU e memória**:

| Máquina | `FACTORY_CPUS` | Por quê |
|---|---|---|
| KVM 2 (2 núcleos) | `1.5` (padrão) | Deixa meio núcleo reservado pro banco |
| KVM 4 (4 núcleos) | `3` | Deixa 1 núcleo pro banco |

```bash
FACTORY_CPUS=3 ./docker/factory.sh render 4
```

Mesmo que o render surte, ele **não consegue** passar do teto — o Teable nunca cai por causa disso.

---

## Próximo passo depois disso

Automatizar a fila: um cron chamando `factory.sh render N` para o próximo sermão pendente,
lendo a fila do Teable.
