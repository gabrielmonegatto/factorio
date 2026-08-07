---
name: ads-quiz-framework-xisto
description: >
  Cria a leva completa de criativos de anúncio para funis de quiz low ticket no padrão
  Victor Xisto: 6 estruturas × 3 ganchos = 18 variações em formato UGC/TikTok de até 50s,
  cada uma com roteiro cena a cena, briefing de filmagem, prompts de IA para gerar o vídeo
  e copy de Meta Ads (primary text + headline). EXIGE como input o blueprint gerado pela
  skill quiz-framework-xisto — o criativo herda nome chiclete, dores e motivo urgente do
  quiz. TRIGGER quando o usuário pedir "ads quiz framework xisto", "criativos pro quiz",
  "anúncios pro quiz", "leva de criativos", "criativo pro funil de quiz", ou tiver um
  blueprint de quiz pronto e quiser os anúncios. NÃO usar para estrutura de campanha/
  tráfego (ABO/CBO/orçamento) nem para criativos de VSL. NÃO usar para anúncios de quiz
  de buckets/segmentação — use ads-quiz-framework-ask-method; nem de quiz consultivo/high
  ticket — use ads-quiz-framework-spin-selling. Blueprint de outro framework recebido →
  redirecione para a skill de ads correspondente.
---

# Ads Quiz Framework Xisto

Produz a leva de anúncios que joga volume pro quiz: criativos UGC de ≤50s cujo único trabalho é parar o scroll e mandar o lead pro "teste gratuito" — quem conscientiza é o quiz, não o anúncio. Entregável: um documento de leva em Markdown seguindo `references/template-leva.md`, com 18 variações prontas para gravar (briefing UGC), gerar (prompts de IA) e subir (copy Meta Ads).

## Regras duras

1. **Sem blueprint, não roda.** Esta skill EXIGE o blueprint da `quiz-framework-xisto` (nome chiclete, matriz de dores, motivo urgente, identidade visual). Se o usuário não tiver, pare e ofereça rodar a quiz-framework-xisto primeiro — criativo desalinhado do quiz quebra o funil inteiro (o gancho promete o que o quiz não pergunta).
2. **≤50 segundos, UGC orgânico.** Nunca parecer anúncio: sem estúdio, sem produto físico na mão, sem cara de comercial. O padrão que escala é o vídeo que parece post de influencer comum.
3. **O criativo não conscientiza — joga volume.** Nada de provar mecanismo, empilhar argumentos ou mini-aula. Uma dor, uma virada, um CTA. O quiz faz a conscientização em 20–35 etapas.
4. **CTA sempre "teste gratuito" + recompensa.** O quiz é grátis (o plano é pago) — nunca mencionar preço, compra ou "oferta" no criativo. É o CTA gratuito que infla o CTR e derruba CPC/CPM.
5. **Antes/depois: mesma pessoa, 3x, curto.** Aparece no início, meio e fim (quantidade), nunca em bloco longo (duração). Pessoas diferentes no antes e no depois quebram o contexto — erro clássico do mercado.
6. **Prévia do entregável = pessoa usando o app fisicamente.** Nunca tela gravada/screencast.
7. **Nome chiclete idêntico ao do blueprint**, falado e/ou em texto de tela. Nome do criativo ≠ nome do quiz confunde o lead na transição.
8. **Todo gancho mapeia uma porta de entrada do quiz**: um objetivo da etapa 1 ou uma opção do motivo urgente. Quem clicou pelo casamento precisa encontrar "casamento" nas opções — é isso que fecha o loop de personalização.
9. **Edição dopaminérgica**: corte a cada ~3s, transições, música viral do momento — mantendo cara de orgânico.
10. **Leva = 6 estruturas × 3 ganchos**, com ângulos DIFERENTES entre as estruturas (dois criativos do mesmo ângulo = deletar um). Ganchos da mesma estrutura variam o ângulo de entrada, não o body.

## Workflow

### 1. Ingestão do blueprint
Peça/localize o blueprint da quiz-framework-xisto e extraia: nome chiclete, público + identidade visual, promessa central, matriz de personalização (dores e desejos), opções do motivo urgente, entregável, CTA de anúncio sugerido nas notas. Sem blueprint → regra dura 1.

### 2. Ângulos da leva
Leia `references/destilado-xisto.md` (seções 1–3 e 9) e `references/anatomia-do-criativo.md`, e defina os 6 ângulos a partir da matriz do quiz (ex.: motivo urgente, dor principal, curiosidade do teste, prova antes/depois, demo do app, dor desconhecida em 1 frase). Cada ângulo vira uma estrutura; anote qual porta do quiz cada um mapeia (regra 8).

### 3. Ganchos
Escreva 3 ganchos por estrutura (18 no total), no padrão TikTok: primeira frase que para o scroll em até 3s, falada em primeira pessoa, específica e visual. Antes de escrever, leia `references/exemplos.md`.

### 4. Roteiros cena a cena
Para cada criativo: tabela tempo × cena × fala × texto de tela × nota de edição, seguindo a estrutura invisível da anatomia (gancho → história/dor → virada com prévia do app → CTA teste gratuito) e pontuando os 3 antes/depois.

### 5. Produção: briefing + prompts de IA
Para cada criativo: briefing de filmagem UGC (quem, onde, figurino, luz, tom) E prompts de geração por IA (com instrução de consistência de personagem — o antes/depois de IA precisa da MESMA pessoa gerada, via imagem de referência).

### 6. Copy de Meta Ads
Primary text (2–4 linhas, mesmo frame do gancho, CTA teste gratuito), headline (nome chiclete + promessa curta) e descrição para cada criativo.

### 7. Montagem da leva
Formate tudo em `references/template-leva.md`, incluindo o mapa gancho↔porta do quiz e o checklist de conformidade. Entregue como arquivo `.md`.

## Graus de liberdade

- **Fixo**: 6×3, regras duras, estrutura invisível base, CTA teste gratuito, formato do entregável.
- **Livre**: escolha dos ângulos (desde que venham da matriz do quiz), criatividade dos ganchos e das histórias, cenários/persona do UGC, estilo dos prompts de IA. Leva enxuta (3×3) ou leva de iteração (variações de um vencedor) apenas se o usuário pedir explicitamente.

## Ponteiros

- `references/destilado-xisto.md` — o framework (seções 1–3 e 9); leia no passo 2.
- `references/anatomia-do-criativo.md` — estrutura invisível, tipos de gancho, regras de edição; leia no passo 2.
- `references/exemplos.md` — pares certo/errado; leia antes de escrever ganchos (passo 3).
- `references/template-leva.md` — formato do entregável; leia antes de formatar (passo 7).
