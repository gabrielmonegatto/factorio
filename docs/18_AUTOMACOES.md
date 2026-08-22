# 18 — Catálogo de Automações da Fábrica

> Registro vivo de TODA automação (viva, armada ou manual). Formato padronizado de
> propósito: cada bloco é parseável pra semear a futura aba "Automações" do BI
> (visualização das etapas estilo n8n, só leitura). Atualize AQUI quando criar,
> mudar ou aposentar uma automação. Espelho humano no Notion (banco Automações).
>
> **Doutrina do motor (decisão 22/08/2026):** o motor de automação da fábrica é
> **Cloudflare Workers** (cron trigger, webhook, Queues/Workflows) pra tudo que é
> leve: HTTP, banco, notificação. O **pesado** (render de vídeo, yt-dlp, CPU longa,
> coisa que IP de datacenter não alcança) roda na **VPS** (cron + systemd + docker).
> Estado sempre no D1; log em arquivo ou tabela; health check vigia os dois braços.
> n8n, Prefect e trigger.dev estão mortos (carcaças em `_archives/factorio-legado-20260822`).

## Como criar automação nova (SOP resumido)

1. Escreva script idempotente (rodar 2x não duplica) que lê credenciais do `.env` via `FABRICA_ENV`.
2. Estado/fila no D1. Nunca em arquivo local, nunca na conversa.
3. Leve → Worker com cron/webhook. Pesado → VPS (`/srv/factorio/<área>/` + `/etc/cron.d/factory-*` com `flock`).
4. Log: `/var/log/<nome>.log` (VPS) ou `wrangler tail` (Worker).
5. Registre o bloco aqui + linha no Notion. Sem registro = não existe.
6. Espelho visual: aba **Automações** do bi.mananciall.org (vista de fluxo, só leitura).
   Mudou este doc → atualiza e roda `node scripts/seed-automacoes.mjs` no repo do BI.

---

## VIVAS (rodando sozinhas)

### intel-canais
- **projeto:** fábrica (intel) · **gatilho:** cron VPS `50 5 * * *` · **roda em:** VPS `/srv/factorio/intel/atualiza_canais.mjs` · **log:** `/var/log/intel_canais.log`
- **etapas:**
  1. Lê canais com `youtube_channel_id` no D1 `eternall-intel`
  2. Puxa stats (subs/views/vídeos) na YouTube Data API (~75 unidades de quota)
  3. Upsert em `canais` + grava `canais_historico`
  4. Varre playlist de uploads de cada canal atrás de vídeos novos
  5. Insere vídeos novos em `videos` com stats

### intel-transcricoes (ARMADA, gate: proxy residencial)
- **projeto:** fábrica (intel) · **gatilho:** cron VPS `15 */3 * * *`, só dispara se `YT_PROXY_URL` existir no `.env` · **roda em:** VPS `/srv/factorio/intel/transcreve.mjs` · **log:** `/var/log/intel_transc.log`
- **etapas:**
  1. Pega lote de 40 vídeos `transcrito=0` no `eternall-intel`
  2. Baixa caption via yt-dlp pelo proxy (1 idioma por vídeo; multi = 429 na hora)
  3. Grava em `transcricoes`, marca `transcrito=1` (ou `-1` se não tem caption)

### spurgeon-render
- **projeto:** canal Spurgeon · **gatilho:** serviço contínuo `factory-producer.service` · **roda em:** VPS (container `factorio-render:v5`) · **log:** `journalctl -u factory-producer`
- **etapas:**
  1. Lê fila de sermões pendentes
  2. Narra (TTS) e renderiza o vídeo (Remotion no container, CPU limitada)
  3. Mantém buffer de vídeos prontos cheio

### spurgeon-agendamento
- **projeto:** canal Spurgeon · **gatilho:** cron VPS `0 6 * * *` · **roda em:** VPS `/app/_factorio/remotion/schedule_channel.py` · **log:** `/var/log/factory_schedule.log`
- **etapas:**
  1. Lê buffer de vídeos renderizados
  2. Agenda no YouTube 1/dia no slot 12:00
  3. Reporta total agendado

### bi-snapshot
- **projeto:** fábrica (indicadores) · **gatilho:** cron VPS `20 6 * * *` · **roda em:** VPS `/srv/factorio/org/snapshot.mjs` · **log:** `/var/log/bi_snapshot.log`
- **etapas:**
  1. Mede indicadores nas fontes (D1s, YouTube API)
  2. Grava em `bi_snapshots` no `mananciall-db` (alimenta a tela Indicadores do BI)
  3. Espelha no Notion

### backup-semanal
- **projeto:** fábrica (org) · **gatilho:** cron VPS `0 7 * * 0` (domingo) · **roda em:** VPS `/srv/factorio/org/backup_semanal.mjs` · **log:** `/var/log/backup_semanal.log`
- **etapas:**
  1. Dump de todos os D1 (mananciall-db, mananciall-mining, eternall-intel) em NDJSON
  2. Dump dos bancos de gestão do Notion em JSON
  3. Comprime (gz) e sobe pro R2 `eternall-archives` com manifesto datado

### bluue-purchase-check
- **projeto:** Bluue (Br4nds, conta CF própria) · **gatilho:** Worker com cron · **roda em:** Cloudflare Worker (repo `apps/br4nds/bluuebr`)
- **etapas:**
  1. Puxa pedidos (B4You/Flow)
  2. Casa venda ↔ sessão first-party
  3. Grava atribuição no D1 `br4nds`

### bluue-backup-d1
- **projeto:** Bluue (Br4nds) · **gatilho:** Worker com cron · **roda em:** Cloudflare Worker
- **etapas:**
  1. Exporta o D1 `br4nds`
  2. Sobe pro R2 de backup

### zoac-vendas
- **projeto:** ZOAC (conta CF própria) · **gatilho:** webhook GHL · **roda em:** Cloudflare Worker (stack 0.3.1)
- **etapas:**
  1. Recebe webhook de venda do GoHighLevel
  2. Adapter normaliza o evento
  3. Grava no D1 + dispara pixel/CAPI

## MANUAIS (prontas, rodam sob comando)

### health-check (gate: DISCORD_WEBHOOK_FABRICA no .env)
- **projeto:** fábrica (org) · **como rodar:** `node scripts/org/health_check.mjs --seco --verboso`
- **etapas:** mede cada esteira nas fontes reais → compara com o esperado → alerta no Discord (quando o webhook existir; sem ele, só imprime). Ao destravar o gate: plugar cron diário na VPS.

### mineracao
- **projeto:** Mananciall · **como rodar:** `node scripts/mining/run.mjs` (fila em `works`/`runs` no `mananciall-mining`)
- **etapas:** resolve fonte (CCEL/Gutenberg/NewAdvent) → mina HTML → parseia/limpa → grava obra. Handoff pendente: repontar `queue.mjs` pra biblioteca do D1.

### meta-criativos
- **projeto:** Bluue (Br4nds) · **como rodar:** scripts em `scripts/meta/` (pull_ads, pull_insights, meta_match)
- **etapas:** puxa ads/insights da Meta API → casa anúncio ↔ criativo no R2 → grava atribuição por criativo.

### kit-notion
- **projeto:** fábrica (org) · **como rodar:** `node tools/notion/notion-tarefas.mjs "<Área>"` e afins
- **etapas:** leitura/escrita dos bancos de gestão no Notion (tasks, roadmap, entregas). É ferramenta de sessão, não cadência.

## APOSENTADAS

n8n (era 1) · Prefect (era 2, nunca rodou) · trigger.dev (era 3, 25+ scripts) · Hermes/agents (era 4) · Teable/Baserow + mcp_universal (era 5, containers somem 27/08/2026). Carcaças completas em `C:\Users\Monegatto\Desktop\_archives\factorio-legado-20260822\`.
