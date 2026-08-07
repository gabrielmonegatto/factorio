# Entrevista — skill `planejamento-keywords-ads`

Data: 2026-07-14 · Fonte: o próprio Pedro descreveu o fluxo completo ao pedir o trabalho.

## Bloco 1 — O Job (palavras dele)
> "1. Eu te mandar um site. 2. Você vai entrar nesse site, olhar todo o conteúdo, entrar em todas
> as páginas, entender o que essa empresa vende. 3. Criar uma lista de palavras-chave interessantes
> que possivelmente são interessantes para anunciar no Google. 4. Montar um relatório com essas
> palavras-chave e a quantidade de buscas dela."

Input: uma URL. Output: planilha no Google Sheets + leitura estratégica dos dados.

## Bloco 2 — Gatilho
"analisa esse site pra Google Ads", "faz o planejamento de keywords desse site", "quais palavras-chave
esse cliente deveria anunciar", ou simplesmente **mandar uma URL de cliente** no contexto de tráfego pago.
**NÃO disparar** para: SEO de conteúdo/blog, análise de concorrente, auditoria de conta.

## Bloco 3 — Barra de qualidade
Referências aprovadas: Studio NGN (estética) e Festejou (aluguel de festas), ambos 2026-07-14.
O que torna excelente: **curadoria por intenção** (não despejar as 8 mil ideias da API) + os
**3 níveis geográficos** + **leituras acionáveis** no fim ("não anuncie por bairro: volume zero").

## Bloco 4 — Modos de falha (observados)
1. Entregar as ideias cruas da API (8.615 no NGN, 5.214 no Festejou) — 90% é lixo.
2. Não separar intenção: produto vs serviço (NGN), compra vs aluguel (Festejou).
3. Dar só o volume nacional para um negócio que atende uma cidade — número irreal.
4. Variantes duplicadas comendo as vagas ("massagem relaxante" = "massagens relaxamento").
5. Entregar link sem interpretação.
6. Deixar CPC em dólar.

## Bloco 6 — Regras duras (Pedro, palavras dele)
> "Se o site for de uma empresa local (...) você deve fazer a busca só na cidade (...) para que seja
> um número mais real para a localidade da pessoa. Deve trazer também, junto, a quantidade total.
> O Brasil tem que trazer Brasil, estado e cidade do negócio local para cada palavra-chave."
> "Usar a API para encontrar novas ideias de palavras-chave relacionadas."
> "O relatório tem que estar dentro de um Google Sheets." "Converte tudo para BRL."

## Bloco 7 — Contexto
CLI `planejador-google-ads` (DataForSEO) + skill `planilha-google-sheets` para a entrega.

## Bloco 8 — Output
Google Sheets em `Planejamento de Keywords — Google Ads/<Cliente>/` + leituras na conversa.
