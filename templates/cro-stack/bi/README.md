# Peça BI: painel Evidence + tranca de acesso

O BI não é um template copiável inteiro (o Evidence gera projeto próprio); esta
pasta guarda o que É reaproveitável e a receita. Modelo vivo: `apps/br4nds/bi`
servindo em `bi.br4nds.com.br`.

## Receita (~1h com dados já no D1)

1. **Projeto Evidence**: `npx degit evidence-dev/template <holding>-bi` e conectar
   no D1 via export (o conector direto não existe; o build lê um SQLite local
   gerado do backup NDJSON ou de `wrangler d1 export`).
   ⚠️ Gotcha de deploy: o wasm do DuckDB passa de 25MB — no Cloudflare Pages,
   buildar com `EVIDENCE_BUILD_DIR` limpo e conferir o limite de arquivo.
2. **Consultas padrão** (as que toda marca quer no dia 1):
   - Funil tela a tela (pageviews por rota + quedas)
   - R$/sessão por rota e por experimento (JOIN com `experiment_assignments`)
   - Vendas por dia/campanha (ledger `purchases_sent` + `campaign_insights`)
   ⚠️ Fan-out: JOIN de sessões com vendas multiplica linhas (já vimos 398% de
   "conversão"). Use EXISTS/subconsulta correlacionada e valide contra o total
   do ledger antes de publicar qualquer número.
3. **Guarda de domínio**: copiar `functions/_middleware.js` desta pasta pro
   projeto Evidence e trocar o domínio. Sem isso o `*.pages.dev` fica aberto.
4. **Cloudflare Access** (na ZONA da holding):
   - App Access cobrindo `bi.<holding>` com policy de e-mails permitidos
   - IdP **One-time PIN**: NÃO existe por padrão — criar via
     `POST /accounts/{id}/access/identity_providers` com `type: "onetimepin"`.
     Sem ele, o login só oferece "entrar com Cloudflare", que é péssimo pro time.
   - API por ZONA funciona com permissão Zone Access (`/zones/{id}/access/apps`);
     a de conta exige permissão account-level.
5. **Backup alimenta o BI**: o worker `backup-d1` (pasta vizinha) exporta o D1
   pra R2 em NDJSON; o rebuild do Evidence pode ler dali (dado de ontem é
   suficiente pra BI; tempo real é papel do admin do funil, não do Evidence).

## Regras que não se negocia

- **Domínio da HOLDING**, nunca de marca (marca é descartável).
- **Dados individuais de saúde NUNCA entram no BI**, nem trancado. Agregado só.
- Sem PII em nenhuma consulta: o BI mostra contagens e somas, não pessoas.
