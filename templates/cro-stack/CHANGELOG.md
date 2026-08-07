# Changelog: cro-stack

Regra de manutenção: **bug corrige no template PRIMEIRO**, depois desce pras cópias.
Cada projeto que usa o kit anota no seu `CLAUDE.md` de qual `VERSION` nasceu.

## 0.1.2: 25/07/2026

**Fix crítico de dados: middleware marca crawler como bot.**

Sintoma (achado no ZOAC em campanha real): o PageView do funil vinha inflado.
Um dia mostrou 557 "visitantes", dos quais ~439 eram o crawler de preview do
Facebook (`facebookexternalhit`), que bate na página a cada anúncio renderizado.
Tráfego humano real: ~68. Isso faz o funil parecer que "todo mundo abandona"
quando na verdade a maioria nunca foi gente.

Causa: o `_middleware.js` gravava o PageView com `is_bot=0` hardcoded, sem checar
o user-agent (só o `/api/tracker` rodava `detectBot`). Fix: middleware agora roda
`detectBot()` também. Padrão `meta-externalads` adicionado em ambos.

**Regra ao ler o funil**: sempre filtrar `is_bot=0`. Melhor ainda, filtrar por
user-agent de device real (iPhone/Android/Windows/Mac), porque bot novo sempre aparece.

## 0.1.1: 22/07/2026

**`d1/003_capi_debug.sql`**: `data_tracker` passa a guardar `meta_response` e `ga4_response`.

Motivo (falha real na estreia do ZOAC): a Meta devolveu 400 e o banco só tinha
`meta_status_code`. Sem o corpo da resposta, foi preciso reproduzir a chamada na
mão contra a Graph API pra descobrir a causa (token com escopo de leitura).
Agora o diagnóstico é uma query:

```sql
SELECT event_name, meta_status_code, substr(meta_response,1,300)
FROM data_tracker WHERE meta_response_ok = 0 AND meta_status_code IS NOT NULL
ORDER BY created_at DESC LIMIT 5;
```

**Gotcha de credencial documentado**: token de CAPI precisa de escopo de ESCRITA
no dataset. Um token com só `read_ads_dataset_quality` **lê** o nome do pixel
normalmente (parece válido!) e é rejeitado com 400 ao enviar evento. Sempre
validar com um POST de teste, nunca só com GET.

**Gotcha de deploy**: após `pages deploy`, esperar ~15s antes de testar: o alias
de produção continua servindo a versão anterior por alguns segundos.

## 0.1.0: 21/07/2026

Extração inicial do motor do `apps/br4nds/bluue` (laboratório mais maduro).

**Incluído:**
- `functions/_middleware.js`: sessão `_bnd_sid`/`_bnd_eid`, síntese fbc/fbp, salto de domínio via `?_sid=`, PageView server-side no D1
- `functions/api/tracker.js`: Meta CAPI + GA4, bot-detection, hash SHA-256 de PII
- `functions/api/lead.js`: captura de lead
- `snippets/tracking-head.astro`: `window.croTrack()`
- `d1/001_core.sql` + `d1/002_purchases.sql`
- `wrangler.template.jsonc`

**Mudanças em relação ao bluue (limpeza de acoplamento):**
- Binding D1 `BR4NDS_DB` → **`CRO_DB`** (nome de cliente não vive no template)
- `window.bluueTrack` → **`window.croTrack`**
- `/api/lead`: removido o default `brand='bluue'`; marca resolvida pelo `domain_config` do host, `body.brand` só como fallback, erro 400 se nenhum resolver
- Migrations renumeradas: `001_init`+`004_purchases` do bluue → `001_core`+`002_purchases`

**Dívidas do motor corrigidas na extração:**
- **PageView contado em dobro na Meta**: no bluue o `fbq('track','PageView')` disparava sem `eventID` e o CAPI mandava um id aleatório: dois eventos distintos para a Meta. Agora `croTrack` gera UM id e usa nos dois canais (`{eventID}` no fbq + `event_id` no CAPI), que é o padrão de dedup da Meta.
- `keepalive: true` no fetch do CAPI (evento não se perde quando a navegação acontece antes da resposta).

**Deixado de fora de propósito** (identificado como acoplado/quebrado no bluue):
- Stack legado Supabase (`TestoQuiz.tsx`, `integrations/supabase/*`, DiscountPopups)
- `webhook/hotmart.js`: secret lido mas **nunca validado** + `event_id` com `Date.now()` (não idempotente)
- `lp-ponte/index.html`: pixel ID cravado no HTML
- `sync-ads.js` / `setup-dashboard.js` / `read-sheet.js`: listas `act_*` e `SHEET_ID` hardcoded (fase 2, reescrever por config)

**Pendente pra 0.2.0:**
- Worker `purchase-check` com adapters de gateway (`b4you.js` pronto no bluue, `ghl.js` a nascer)
- Fábrica de páginas (componentes + tokens de design)

## 0.3.1: 07/08/2026 (estreia na ZOAC: 1º adapter GHL + 2 regressões pegas)

Instalação real na ZOAC (2ª marca, conta CF própria) no mesmo dia do 0.3.0:

- **`workers/purchase-check/adapters/ghl.index.js`**: adapter GHL/Conversion
  Goat DE PRATELEIRA, validado com venda real (match por sck + fbp/fbc). O que
  ele sabe: API é `services.leadconnectorHQ.com` (sem "hq" = NXDOMAIN); o pedido
  NÃO carrega o sck, o CONTATO carrega (`attributionSource.url` preserva a query
  `?_sid=` do order form); `amount` vem em unidades da moeda, não centavos;
  filtro por `sourceId` é obrigatório (location compartilhada tinha 8.504
  pedidos de outros produtos); gênero SEM fallback (público misto).
- **Regressão corrigida: middleware gravava `is_bot=0` chumbado.** O fix 0.1.2
  se perdeu quando o middleware foi ressincronizado da bluue no 0.2.0 (a bluue
  nunca teve o fix). `detectBot()` de volta no PageView server-side; filtro por
  status < 400 NÃO cobre crawler (ele acessa página real com 200).
- **Gap corrigido: 004 não criava `event_map`** (a bluue tinha de migration
  própria; o worker consulta a coluna e quebraria em projeto novo).
- `__BLUUE_CONTENT__` → `__CRO_CONTENT__` no middleware (nome de marca vazou).
- Gotcha novo: conta CF nova não tem subdomínio workers.dev (registrar via
  `PUT /accounts/{id}/workers/subdomain`; o comando do wrangler morreu no v4) e
  R2 precisa ser ATIVADO no dashboard (gate humano, pode pedir cartão).

## 0.3.0: 07/08/2026 (velocidade + memória fora da Cloudflare)

Decisões de pesquisa registradas no `LINHA_DE_MONTAGEM_CRO.md` (raiz do
EternalL): Astro CONFIRMADO como stack (HTML puro + porteiro dependem dele;
adapter mata `functions/`), e a fábrica de páginas vira **registry shadcn**
(`funnel-matrix`, template vizinho) em vez de pasta de copiar.

- **functions/api/webhook-venda.js + d1/006_webhook.sql**: venda quase
  instantânea SEM segundo caminho de código. O webhook do gateway é CAMPAINHA:
  autentica, loga o payload cru (auditoria) e dispara uma rodada imediata do
  purchase-check. Toda a lógica de venda (casamento, EMQ, dedup) continua só no
  worker. O cron NUNCA sai: webhook perde venda quando o endpoint pisca,
  polling só atrasa.
- **workers/backup-d1/**: extraído do bluue e generalizado (`CRO_DB` +
  `PROJECT_SLUG`). NDJSON fatiado por rowid + manifest + ponteiro `latest.json`
  + `restore.mjs` (INSERT OR REPLACE, idempotente). Retenção desligada por
  padrão: apagar dado é gate humano.
- **bi/**: guarda de domínio (`Access não cobre *.pages.dev`) + receita
  Evidence completa (consultas padrão, gotcha do fan-out em JOIN de vendas,
  gotcha do wasm >25MB, One-time PIN criado via API, endereço é da HOLDING).

## 0.2.0 — 04/08/2026 (a semana da virada do bluue.io)

Sincroniza o kit com tudo que a operação real ensinou entre 31/07 e 04/08:

- **SKILL.md**: playbook de instalação completo (Fases 0-8), carregável por
  agente. Inclui a tabela dos 12 erros já cometidos e como detectá-los.
- **d1/004_routing_scripts.sql**: `root_route` (fato, não categoria — a
  categoria quase mandou 16 anúncios pra página errada), `scripts` (tags de
  terceiro por domínio, agnóstica), `bridge_target`, `checkout_embed`,
  `clarity_id`, `pool_status`.
- **d1/005_experiments.sql**: motor de A/B com CHECKs (recusa teste sem
  hipótese e encerramento sem decisão).
- **functions/_middleware.js**: sincronizado com o do bluue. Ganhou: motor de
  A/B (sorteio FNV-1a, cache 60s, falha aberta), injeção de conteúdo de
  variante no HTML pré-renderizado, injeção de scripts por domínio, config em
  cache no isolado (falha não entra no cache), pageview só de resposta < 400.
- **functions/content.base.mjs**: arquivo-base de textos testáveis (lido pelo
  porteiro E pelo navegador; chave sem base = variante que nunca aparece).
- **workers/purchase-check/**: o elo que fecha a atribuição. Casamento por sck,
  livro-caixa com dedup, EMQ completo (em/ph/fn/ln/external_id/fbp/fbc/ip/ua +
  zp/ct/st/country normalizados + ge inferido e declarado como inferência),
  espelhamento de nome de evento na saída, test_event_code pra ensaio seco.

Regras novas que o kit passa a carregar (ver SKILL.md):
- 404 real é obrigatório (200-fallback + immutable = cache envenenado por 1 ano)
- comparação de página é por conteúdo RENDERIZADO, nunca título/arquivo
- nome interno de chunk sem "adv" (adblock)
- fuso do gateway conferido antes de janelas de busca
- API da Meta: paginar sempre, conferir effective_status linha a linha
