---
name: ads-quiz-framework-ask-method
description: >
  Cria a leva completa de anúncios (6 estruturas × 3 ganchos = 18 variações) para quizzes
  de segmentação do Ask Method: anúncios-diagnóstico que vendem a curiosidade do "descubra
  qual dos N tipos você é", com gancho sempre em forma de pergunta, no tom de especialista
  que diagnostica ("brincar de médico"). Cada variação com roteiro cena a cena, briefing,
  prompts de IA e copy de Meta Ads. EXIGE o blueprint gerado pela quiz-framework-ask-method
  (herda buckets, rótulos de diagnóstico e linguagem do mercado). TRIGGER quando o usuário
  pedir "ads ask method", "anúncios pro quiz de buckets", "criativos pro bucket survey",
  "anúncio de diagnóstico", ou tiver um blueprint ask-method pronto e quiser os anúncios.
  NÃO usar para anúncios de quiz de venda low ticket (use ads-quiz-framework-xisto) nem de
  quiz consultivo/high ticket (use ads-quiz-framework-spin-selling). Blueprint de outro
  framework → redirecione para a skill de ads correspondente.
---

# Ads Quiz Framework Ask Method

Produz anúncios que vendem UMA coisa: a curiosidade do diagnóstico. O lead não clica pra comprar nem pra ganhar presente — clica porque quer saber **qual dos N tipos ele é**. O anúncio é a versão paga da landing de autodescoberta do Levesque: pergunta que desperta curiosidade, número finito de possibilidades, e um especialista "brincando de médico". Entregável: documento de leva em Markdown seguindo `references/template-leva.md`.

## Regras duras

1. **Sem blueprint da quiz-framework-ask-method, não roda.** O anúncio herda os buckets, os rótulos de diagnóstico e a linguagem do mercado (colhida no Deep Dive) — anúncio com buckets inventados promete um diagnóstico que o quiz não entrega. Sem blueprint → pare e ofereça rodar a skill do quiz. Blueprint de OUTRO framework → redirecione pra skill de ads correspondente.
2. **Gancho SEMPRE em forma de pergunta.** "É possível dobrar sua memória em 3 dias?" e nunca "Dobre sua memória em 3 dias" — pergunta desperta curiosidade; afirmação dispara o detector de mentira (regra literal do Levesque).
3. **O anúncio vende o DIAGNÓSTICO, nunca o produto.** Zero menção a oferta, preço, curso ou método de venda — a venda começa na página de resultado, DEPOIS do quiz. O que se promete é "descubra seu tipo/gargalo/perfil".
4. **Número finito de possibilidades**: "existem basicamente N tipos de..." onde N = o número de buckets do blueprint. Reduz a ansiedade do infinito ao administrável — e cria o loop de curiosidade ("qual é o meu?").
5. **A linguagem de cada bucket vem do blueprint, nunca inventada.** Os anúncios bucket-específicos usam as palavras que o próprio mercado usou no Deep Dive — a reação-alvo é "é como se você lesse meu diário".
6. **O anúncio guarda-chuva cobre TODOS os buckets** com declarações se-então inclusivas ("se você luta com X... se você tem Y... então...") — ninguém do mercado pode se sentir de fora.
7. **Descarte o tamanho-único**: todo anúncio carrega (explícita ou implicitamente) o "não existe resposta única para todos" — é o que justifica o quiz existir.
8. **Tom de médico, nunca de vendedor.** Especialista diagnosticando; credibilidade como fato informado ("se você não acompanha X, talvez não saiba que..."), nunca vanglória. Sem hype, sem urgência, sem escassez.
9. **Leva = 6 estruturas × 3 ganchos**, ângulos DIFERENTES entre estruturas; mapa anúncio↔bucket/porta preenchido. Ganchos da mesma estrutura variam a entrada, não o body.
10. **A promessa do anúncio = a promessa do diagnóstico do blueprint.** Nunca inflar ("descubra seu gargalo" vira "resolva seu gargalo" ❌).

## Workflow

### 1. Ingestão do blueprint
Localize o blueprint da quiz-framework-ask-method e extraia: os 3–5 buckets (nomes, problema central, % estimado, linguagem do mercado), os rótulos de diagnóstico das páginas de resultado, a promessa do quiz ("descubra seu tipo de X"), o público e a primeira pergunta (Engraxar as Rodas). Sem blueprint → regra 1.

### 2. Estruturas da leva
Leia `references/destilado-ask.md` (seção "Landing page de autodescoberta" + "Regras operacionais") e `references/anatomia-do-anuncio-ask.md`. Defina as 6 estruturas: 1 guarda-chuva (os N tipos, se-então inclusivas) + bucket-específicas para os maiores buckets + curiosidade do rótulo + as demais da anatomia. Anote qual bucket/porta cada uma mira.

### 3. Ganchos
3 por estrutura (18 no total), TODOS em forma de pergunta (regra 2), específicos e na linguagem do mercado. Leia `references/exemplos.md` antes.

### 4. Roteiros cena a cena
Tabela tempo × cena × fala × texto de tela × edição por criativo, seguindo a estrutura da anatomia (pergunta-gancho → possibilidades finitas → descarte do tamanho-único → CTA do teste). ≤60s.

### 5. Produção: briefing + prompts de IA
Briefing de gravação (expert ou UGC de descoberta, conforme a estrutura) + prompts de IA com persona de referência única.

### 6. Copy de Meta Ads
Primary text (com a pergunta-gancho e o número finito), headline ("Descubra qual dos N..."), descrição. Zero preço/oferta.

### 7. Montagem da leva
Formate em `references/template-leva.md` com o mapa anúncio↔bucket e o checklist de conformidade. Entregue como arquivo `.md`.

## Graus de liberdade

- **Fixo**: 6×3, regras duras, gancho-pergunta, venda do diagnóstico, formato do entregável.
- **Livre**: escolha de quais buckets ganham anúncio próprio (priorize os de maior %), criatividade das perguntas, formato por estrutura (expert vs UGC de descoberta vs estático), cenários.

## Ponteiros

- `references/destilado-ask.md` — o método Levesque; leia a seção da landing de autodescoberta no passo 2.
- `references/anatomia-do-anuncio-ask.md` — estruturas, blocos do anúncio-diagnóstico, formatos; leia no passo 2.
- `references/exemplos.md` — pares certo/errado; leia antes do passo 3.
- `references/template-leva.md` — formato do entregável; leia antes do passo 7.
