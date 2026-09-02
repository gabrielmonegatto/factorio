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
- **projeto:** Spurgeon (shorts) · **gatilho:** cron VPS `30 6 * * *` · **roda em:** VPS `/srv/factorio/remotion/schedule_shorts.py --confirm` · **log:** `/var/log/shorts_agenda.log`
  Agenda 1 short/dia às 15:00 UTC no canal existente. Fila de 673 clipes já minerados
  (160 sermões), ordenada por sermão e, dentro dele, pela nota do minerador. Renderiza
  só o que vai publicar e guarda no R2. Teto de 3 uploads por execução (cota do YouTube).
  Estado: `schedule/spurgeon_shorts_schedule.json` no R2.

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

### esteira-canal (MOLDE — vale pra TODO canal)

- **projeto:** fábrica (canais) · **gatilho:** ver as 3 etapas abaixo · **roda em:** VPS · **log:** `/var/log/factory_*_<canal>.log`
- **como nasce um canal novo:** entrada no `remotion/canais.py` + `scripts/esteira_canal.sh ligar <slug>`. Não se copia arquivo: a unidade do systemd é `factory-producer@<slug>` (template `@`), e o cron é gerado pelo mesmo script.
- **isolamento:** cada canal tem fila própria (`sermons.canal` no D1 `mananciall-mining`), estoque próprio (`renders/<canal>/` no R2), lock próprio (`/tmp/*_<canal>.lock`) e log próprio. Canal parado não trava outro; canal quebrado não contamina outro.
- **etapas:**
  1. **NARRAR** (cron `0 */4 * * *`, lote de 2) — capítulo minerado no D1 → `sermon_NNNN.mp3` + `transcript.json` no R2. Kokoro + faster-whisper, ambos em container com teto de 8 CPUs.
  2. **PREPARO** (cron de hora em hora, lote de 6) — narrado → PRONTO. Gera a copy (LLM) e narra hook/outro.
  3. **RENDER** (`factory-producer@<canal>.service`, 24/7) — pronto → `renders/<canal>/NNNN.mp4`. Mantém estoque à frente do calendário.
  4. **AGENDA** (cron 1x/dia, minuto próprio por canal) — mp4 → calendário do YouTube.
- **por que 4 etapas separadas e não um script só:** cada uma é idempotente e olha o estado real (D1 e R2) pra decidir o que falta. Nenhuma depende da anterior ter rodado agora. Matar qualquer uma no meio e rodar de novo continua de onde parou.

### esteira-spurgeon
- **projeto:** canal Charles Spurgeon Treasures · **gatilho:** narrar `0 */4`, preparo `5 * * * *`, agenda `0 6 * * *` · **roda em:** VPS · **log:** `/var/log/factory_{narrar,prep,schedule,producer}_spurgeon.log`
- **acervo:** 3.541 capítulos minerados (63 volumes do CCEL), fila cobrindo todos.
- ⚠️ **Ficou travado em 113 vídeos até 24/08** porque a narração era comando MANUAL, fora da esteira. Acervo grande não vale nada se nenhuma etapa puxa dele.

### esteira-moody
- **projeto:** canal Dwight Lyman Moody Treasures · **gatilho:** narrar `0 */4`, preparo `25 * * * *`, agenda `20 6 * * *` · **roda em:** VPS · **log:** `/var/log/factory_*_moody.log`
- **acervo:** 77 capítulos (14 obras do Gutenberg), todos narrados.
- **cadência:** 14 dias de warmup 1/dia, depois 1 a cada 2 dias (`videos_por_dia: 0.5` no `canais.py`). Com 77 capítulos dá ~4,6 meses de calendário.
- ✅ **INAUGURADO 25/08/2026** pelo próprio cron: 5 vídeos agendados (26 a 30/08), privados com `publishAt` e capa própria.

---

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

### diretor-diario (piloto 01/09/2026)
- **projeto:** fábrica (org) · **como rodar:** cron na VPS chama `infra/diretor/diretor.sh` (manual: `claude -p "/diretor-diario"` na raiz do repo)
- **etapas:** Claude Code headless acorda → `tools/notion/fila.mjs --listar` (banco Tasks do Notion, filtro Responsável=Claude) → executa até 3 tarefas `Gate=auto` com Prompt escrito → `--concluir`/`--travar` grava Exec na task → relatório em `relatorios/diretor-AAAA-MM-DD.md` commitado. Gate=aprovação NUNCA executa: prepara e espera o Gabriel.
- **contrato de máquina no banco Tasks:** colunas `Gate` (auto/aprovação), `Prompt` (ordem de serviço autocontida), `Exec` (só a máquina escreve). Task sem Gate+Prompt é invisível pro motor.
- **credencial:** `CLAUDE_CODE_OAUTH_TOKEN` em `/srv/fabrica/.diretor.env` na VPS (gerada por `claude setup-token`, conta Max do Gabriel). Sem token o cron dorme em silêncio.
- **cadência:** 10:00 e 20:00 UTC (07h/17h BRT).

## APOSENTADAS

n8n (era 1) · Prefect (era 2, nunca rodou) · trigger.dev (era 3, 25+ scripts) · Hermes/agents (era 4) · Teable/Baserow + mcp_universal (era 5, containers somem 27/08/2026). Carcaças completas em `C:\Users\Monegatto\Desktop\_archives\factorio-legado-20260822\`.

## Espelho no Notion

Tabela **Workflows ativos** (dentro da página Business System), gerada por
`scripts/notion_workflows.py --aplicar`.

O caminho do dado é sempre o mesmo, e só nesta direção:

    18_AUTOMACOES.md  →  seed-automacoes.mjs  →  D1 `automacoes`  →  Notion

Nenhum dos dois scripts tem lista própria, de propósito. Editar direto no Notion
é perda de tempo: some no próximo espelhamento. Mudou automação? Muda AQUI, roda
o seeder do BI, roda o do Notion. Quem sumir daqui é arquivado lá.
