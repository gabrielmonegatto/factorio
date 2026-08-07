# cro-stack: kit de infra de conversão

Motor de CRO replicável: sessão first-party → eventos server-side (Meta CAPI + GA4) → D1 → atribuição de venda.
Extraído de `apps/br4nds/bluue`. Serve qualquer projeto (pessoal, cliente ou parceiro).

**Versão:** ver `VERSION` · **Roadmap/estado:** `EternalL/ROADMAP_KIT_CRO.md` · **Conceito:** `EternalL/LINHA_DE_MONTAGEM_CRO.md`

---

## Os dois níveis de replicação

| Cenário | O que fazer | Custo |
|---|---|---|
| Marca nova na **mesma conta CF** (mesmo D1) | **1 INSERT em `domain_config`** + secret `META_TOKEN_<MARCA>` | minutos, zero deploy |
| Projeto novo em **outra conta CF** | copiar este kit (passos abaixo) | ~1h |

---

## Montagem (projeto novo)

**Pré-requisitos:** conta Cloudflare · pixel Meta + token CAPI · repo git · (opcional) GA4 + secret.

1. **Projeto Astro sem adapter Cloudflare.** Se existir `@astrojs/cloudflare` no `astro.config.mjs`, **remova**: ele gera `dist/_worker.js` e o Pages passa a ignorar a pasta `functions/` inteira: o tracking morre em silêncio. Use `output: 'static'`.
2. **D1:** `wrangler d1 create <nome>` → aplicar `d1/001_core.sql` e `d1/002_purchases.sql`.
3. **Config:** copiar `wrangler.template.jsonc` → `wrangler.jsonc`, preencher `{{PROJECT}}`, `{{D1_NAME}}`, `{{D1_ID}}`.
4. **Código:** copiar `functions/` pra raiz do projeto; colar `snippets/tracking-head.astro` dentro do `<body>` do Layout global.
5. **Registrar o domínio** (o INSERT que liga tudo):
   ```sql
   INSERT INTO domain_config (domain, brand, meta_pixel_id, ga4_id)
   VALUES ('meusite.pages.dev', 'minhamarca', '<PIXEL_ID>', NULL);
   ```
6. **Secrets:** `META_TOKEN_<MARCA>` (maiúsculo, igual ao `brand`) e, se usar GA4, `GA4_SECRET_<MARCA>`.
7. **Instrumentar o funil** (nomenclatura da casa):
   ```js
   croTrack('Lead')                                        // chegou na tela de oferta
   croTrack('InitiateCheckout', { eventId: 'ic-'+sid+'-'+offerId })
   ```
8. **Deploy:** `CLOUDFLARE_ACCOUNT_ID=<id> wrangler pages deploy dist --project-name <projeto>`
9. ✅ **Validar** (critério de "está no ar"):
   ```sql
   SELECT event_name, event_id, meta_status_code, meta_response_ok
   FROM data_tracker ORDER BY created_at DESC LIMIT 10;
   ```
   Tem que aparecer o evento com `meta_status_code = 200`.

---

## Como o motor funciona

- **`domain_config` é a fonte da verdade.** Middleware, tracker e worker resolvem marca+pixel pelo `host` da requisição. Nenhum código conhece nome de marca.
- **Token por marca:** `env['META_TOKEN_' + brand.toUpperCase()]`, com fallback `META_TOKEN`. Marca nova = secret novo, sem tocar em código.
- **Dedup pixel × CAPI:** `croTrack` dispara os dois canais com o **mesmo `event_id`**. Sem isso, a Meta conta cada evento duas vezes.
- **`event_id` estável** em Lead (`lead-<sid>`) e InitiateCheckout (`ic-<sid>-<offer>`): reabrir a página não infla o número.
- **PageView tem 2 registros por design**: o do middleware (verdade de servidor, sobrevive a bloqueio de JS) e o do `croTrack` (o que vai pra Meta). Ao contar PageView no D1, filtre por `event_id IS NULL` (middleware) **ou** `event_id LIKE 'pv-%'` (tracker): nunca some os dois.

## Nomenclatura da casa (não inventar)

| Etapa | Evento | Quando dispara |
|---|---|---|
| Visita | `PageView` | carregou a página |
| Lead | `Lead` | **chegou na tela de oferta/pré-checkout**: NÃO depende de email |
| Checkout | `InitiateCheckout` | clicou em comprar / abriu o checkout |
| Venda | `Purchase` | worker `purchase-check` (cron), nunca no browser |

## Estrutura

```
functions/
  _middleware.js          sessão, fbc/fbp, PageView server-side
  api/tracker.js          CAPI Meta + GA4
  api/lead.js             captura de lead
snippets/
  tracking-head.astro     window.croTrack()
d1/
  001_core.sql            domain_config · quizzes · data_tracker
  002_purchases.sql       purchases_sent (ledger)
workers/purchase-check/   [0.2.0] núcleo + adapters de gateway
wrangler.template.jsonc
```

## Gotchas que já custaram caro

- Adapter Astro Cloudflare mata a pasta `functions/` (via `dist/_worker.js`).
- Pages **não aceita `account_id`** no `wrangler.jsonc`: só Worker. Use env `CLOUDFLARE_ACCOUNT_ID`.
- `_factorio/.env` é **CRLF**: ao extrair token no bash, `tr -d '\r'`.
- Domínio fora do `domain_config` = tracker responde 400 e middleware não grava. Se "não aparece nada no D1", confira o INSERT primeiro.
- **Nunca** `git stash pop` nesta árvore.
