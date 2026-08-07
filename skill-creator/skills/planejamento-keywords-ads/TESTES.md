# Testes — `planejamento-keywords-ads`

## Teste de gatilho

| Frase | Deve disparar? |
|---|---|
| "analisa esse site pra Google Ads: <url>" | ✅ sim |
| "faz o planejamento de keywords desse site" | ✅ sim |
| "quais palavras-chave esse cliente deveria anunciar" | ✅ sim |
| URL de cliente solta, em contexto de tráfego pago | ✅ sim |
| "escreve um artigo de blog otimizado pra SEO" | ❌ não (SEO de conteúdo) |
| "audita a conta de Google Ads desse cliente" | ❌ não (auditoria) |
| "quanto tá o CPC do meu concorrente?" | ❌ não (análise de concorrente) |

## Caso 1 — Negócio local (regressão: Studio NGN)

**Input:** https://www.studiongn.com.br/ (clínica de estética, Flamengo/RJ)
**Esperado:**
- [ ] Identifica: clínica de estética, Rio de Janeiro, e lista os serviços reais do site.
- [ ] Sementes vêm dos serviços do site (não inventa botox/harmonização, que ele não faz).
- [ ] Corta keywords de PRODUTO (`cerave gel de limpeza`, `óleo de banho nívea`).
- [ ] Traz Brasil + Estado RJ + Cidade Rio para cada keyword.
- [ ] CPC em R$.
- [ ] Planilha via skill `planilha-google-sheets`, em `Planejamento de Keywords — Google Ads/<Cliente>/`.
- [ ] Reporta que keywords de BAIRRO deram volume zero (não anunciar por bairro).
- [ ] Aponta `design de sobrancelha` como oportunidade (volume alto, concorrência baixa, site não cobre).

## Caso 2 — Locadora (regressão: Festejou)

**Input:** https://festejou.com.br/ (aluguel de equipamento para festas, RJ)
**Esperado:**
- [ ] Corta keywords de COMPRA (`tenda 3x3`, `tenda de praia`).
- [ ] Mantém genéricas (`pula pula`) MAS avisa da ambiguidade compra × aluguel.
- [ ] Aponta a armadilha de CPC alto com volume baixo (`tendas rio de janeiro`, R$ 12,44).

## Caso 3 — Negócio nacional (fora do padrão local)

**Input:** um e-commerce que vende para todo o Brasil.
**Esperado:**
- [ ] NÃO força os 3 níveis geográficos: usa Brasil como principal.
- [ ] Não inventa variações "perto de mim"/cidade, que não fazem sentido aqui.

## Caso 4 — Saldo insuficiente

**Esperado:**
- [ ] Roda `planejar testar` antes; se o saldo não cobrir ~US$ 0,36, avisa o Pedro ANTES de gastar.
