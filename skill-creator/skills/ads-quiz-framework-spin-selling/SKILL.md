---
name: ads-quiz-framework-spin-selling
description: >
  Cria a leva completa de anúncios (6 estruturas × 3 ganchos = 18 variações) para quizzes
  de venda consultiva SPIN: anúncios de problema e implicação que fazem o decisor se
  reconhecer e clicar pro diagnóstico — sem pressão, sem features, sem promessa inflada.
  Mix de formatos consultivos (talking head de autoridade, case estruturado, UGC sóbrio,
  estático de implicação), cada variação com roteiro, briefing, prompts de IA e copy de
  Meta Ads. EXIGE o blueprint gerado pela quiz-framework-spin-selling (herda Cadeia SPIN,
  modo, qualificação e avanço). TRIGGER quando o usuário pedir "ads spin selling",
  "anúncios pro quiz consultivo", "criativos pra quiz de mentoria/consultoria/high ticket",
  "anúncio de qualificação pra call", ou tiver um blueprint spin pronto e quiser os
  anúncios. NÃO usar para anúncios de quiz low ticket por impulso (use
  ads-quiz-framework-xisto) nem de quiz de buckets (use ads-quiz-framework-ask-method).
  Blueprint de outro framework → redirecione para a skill de ads correspondente.
---

# Ads Quiz Framework SPIN Selling

Produz anúncios que fazem o decisor se RECONHECER num problema e nas suas implicações — e clicar pro diagnóstico querendo entender o próprio caso. O anúncio SPIN nunca vende a solução (isso é trabalho da fase N do quiz e da call): ele abre a ferida certa, no tom certo, pro lead certo. Menos volume, mais qualificação. Entregável: documento de leva em Markdown seguindo `references/template-leva.md`.

## Regras duras

1. **Sem blueprint da quiz-framework-spin-selling, não roda.** O anúncio herda a Cadeia SPIN (problemas + implicações), o modo, os critérios de qualificação e o avanço. Sem blueprint → pare e ofereça rodar a skill do quiz. Blueprint de OUTRO framework → redirecione pra skill de ads correspondente.
2. **O anúncio fala de PROBLEMA e IMPLICAÇÃO — nunca de solução, método ou features.** Features geram objeção de preço antes mesmo do clique; vantagem genérica gera objeção de valor. A solução só aparece depois que o quiz desenvolveu a necessidade (é a prevenção de objeções aplicada ao tráfego).
3. **Zero pressão no modo consultivo**: sem cupom, timer, escassez, "últimas vagas". A pesquisa é inequívoca — pressão derruba venda grande e satisfação. No modo híbrido, elementos de impulso ficam na PÁGINA do quiz, nunca no anúncio.
4. **Todo gancho mapeia uma linha da Cadeia SPIN do blueprint** (um problema ou uma implicação que o quiz explora). Gancho órfão atrai lead que o quiz não desenvolve — clique caro que morre no meio.
5. **Implicação é a linguagem do decisor**: os ganchos mais fortes dimensionam consequência ("quanto custa cada avaliação que não fecha?"), não sintoma. Usuários respondem a problema; quem ASSINA responde a implicação.
6. **Qualifique no próprio anúncio.** Nomeie o perfil ("dentista dono de clínica", "quem fatura acima de X") — high ticket quer o lead certo, não volume. CPL mais alto com lead qualificado vence CPL barato com curioso.
7. **CTA = o diagnóstico com entregável próprio, proposto UMA vez, afirmando** ("Faça o diagnóstico — você sai com o mapa de X"). Nunca "saiba mais", nunca CTA em cascata.
8. **A promessa do anúncio nunca excede o que o quiz + avanço entregam.** O lead que clicou por uma promessa inflada chega na call desconfiado — e a venda consultiva morre na confiança.
9. **Credibilidade como fato, nunca vanglória** ("nos últimos 3 anos analisamos 200 clínicas" ✅ / "sou o maior especialista do Brasil" ❌). Autoridade serve pra ganhar o direito de perguntar — igual à abertura da visita do Rackham.
10. **Leva = 6 estruturas × 3 ganchos**, ângulos DIFERENTES, formatos do mix consultivo distribuídos por estrutura (talking head, case, UGC sóbrio, estático). Ganchos da mesma estrutura variam a entrada, não o body.

## Workflow

### 1. Ingestão do blueprint
Localize o blueprint da quiz-framework-spin-selling e extraia: a Cadeia SPIN completa (problemas, implicações, necessidades explícitas), o modo (consultivo/direto/híbrido), o público + critérios de qualificação, o avanço e seu entregável, e o custo da inação. Sem blueprint → regra 1.

### 2. Estruturas da leva
Leia `references/destilado-spin.md` (seções 3, 6 e 7) e `references/anatomia-do-anuncio-spin.md`. Defina as 6 estruturas a partir da Cadeia (problema declarado, conta dolorosa, projeção de inércia, case estruturado, contra-intuitivo de autoridade, comparação incômoda) e atribua o formato de cada uma. Anote qual linha da Cadeia cada estrutura mira.

### 3. Ganchos
3 por estrutura (18), priorizando implicações dimensionáveis (regra 5), com a qualificação embutida (regra 6). Leia `references/exemplos.md` antes.

### 4. Roteiros cena a cena
Tabela tempo × cena × fala × texto de tela × edição, seguindo a estrutura da anatomia (reconhecimento → implicação → ponte pro diagnóstico → CTA com entregável). ≤60s (estático: 1 card).

### 5. Produção: briefing + prompts de IA
Briefing por formato (talking head: enquadramento/tom de consultório; case: takes do cliente; UGC sóbrio) + prompts de IA com persona de referência única.

### 6. Copy de Meta Ads
Primary text no tom consultivo (problema + implicação + convite ao diagnóstico), headline com o entregável do avanço, descrição. Zero preço, zero urgência fabricada.

### 7. Montagem da leva
Formate em `references/template-leva.md` com o mapa anúncio↔linha da Cadeia e o checklist. Entregue como arquivo `.md`.

## Graus de liberdade

- **Fixo**: 6×3, regras duras, mapa pra Cadeia, formato do entregável.
- **Livre**: quais linhas da Cadeia priorizar, distribuição dos formatos entre estruturas, criatividade dos ganchos e cases, cenários. No modo híbrido: tom pode aquecer em direção ao padrão Xisto (mantendo as regras 2, 4 e 8).

## Ponteiros

- `references/destilado-spin.md` — o método Rackham; leia as seções 3 (SPIN), 6 (FAB) e 7 (prevenção de objeções) no passo 2.
- `references/anatomia-do-anuncio-spin.md` — estruturas, formatos do mix consultivo, blocos; leia no passo 2.
- `references/exemplos.md` — pares certo/errado; leia antes do passo 3.
- `references/template-leva.md` — formato do entregável; leia antes do passo 7.
