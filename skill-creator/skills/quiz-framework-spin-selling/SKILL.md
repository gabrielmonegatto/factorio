---
name: quiz-framework-spin-selling
description: >
  Cria o blueprint de um quiz de venda consultiva seguindo o SPIN Selling de Neil Rackham:
  sequência Situação → Problema → Implicação → Need-payoff que faz o lead verbalizar as
  próprias necessidades explícitas e "se vender sozinho", terminando num avanço configurável
  (agendamento de call, aplicação ou checkout). Três modos: consultivo/high ticket,
  direto e híbrido-Xisto (ticket médio). Entrega blueprint em Markdown etapa por etapa
  com copy pronta. TRIGGER quando o usuário pedir "quiz spin selling", "quiz spin",
  "quiz de venda consultiva", "quiz pra high ticket/mentoria/consultoria", "quiz de
  qualificação pra call". NÃO usar para venda por impulso low ticket R$17–27 (estilo
  Better Me) — use quiz-framework-xisto; nem para segmentação de mercado em buckets —
  use quiz-framework-ask-method. Se o pedido for só "monta um quiz" sem framework
  definido, PERGUNTE qual dos três o usuário quer antes de começar.
---

# Quiz Framework SPIN Selling

Constrói quizzes onde **o lead se vende sozinho**: a sequência SPIN desenvolve necessidades implícitas em explícitas por perguntas, o lead verbaliza o valor de resolver (fase N), e a página final só espelha o que ELE disse — terminando num avanço realista, não num pedido. Base: pesquisa Huthwaite/Rackham (35.000 visitas) sobre por que venda grande é o oposto de venda pequena. Entregável: blueprint em Markdown seguindo `references/template-blueprint.md`.

## Regras duras

1. **Framework certo antes de tudo.** Venda por impulso R$17–27 → `quiz-framework-xisto`. Segmentação/pesquisa de mercado → `quiz-framework-ask-method`. SPIN é para quando a decisão exige consideração (ticket alto, serviço, mentoria, B2B) — onde pressão e feature-dump DERRUBAM a venda. Pedido ambíguo → pergunte.
2. **Defina modo e avanço no diagnóstico**: consultivo (→ agendamento/aplicação), direto (→ checkout) ou híbrido-Xisto (ticket médio ~R$97–297, espinha das 5 fases do Xisto com motor P→I→N). Todo quiz termina em UM avanço concreto proposto UMA única vez, AFIRMANDO — "no ponto do compromisso, os bem-sucedidos não perguntam, eles dizem" (curva da pesquisa: 1 proposta = 61% de sucesso; 2+ = despenca). Nunca "continuação" vaga.
3. **Ordem S→P→I→N→D como desenvolvimento, não como fórmula rígida.** Nunca Need-payoff antes de Implicação desenvolvida; nunca solução/benefício antes da fase N completa (apresentar cedo é a causa nº 1 de objeção — previna, não rebata). Exceção legítima do próprio Rackham: se o lead JÁ chega declarando necessidade explícita (ex.: veio de um anúncio de alta intenção), pode-se encurtar P/I e acelerar para N — "vender por fórmula fixa é receita para o fracasso".
4. **Situação no mínimo: 3–5 perguntas, cada uma com propósito declarado.** O que o anúncio/segmentação já entrega não vira pergunta. (Pesquisa: perguntas de situação não correlacionam com sucesso — entediam; beneficiam o vendedor, não o lead.)
5. **Implicação proporcional ao ticket (equação de valor).** A compra só acontece quando a gravidade percebida supera o custo. Ticket alto com pouca implicação = "tá caro". Quanto maior o preço do avanço, mais fundo o bloco I.
6. **Blocos I desaguam na fase N (Regra de Quincy): nunca termine em implicação.** Diferente do Xisto: implicações podem se ACUMULAR dentro do bloco (sem alívio par a par) — o alívio é a fase N inteira, onde o lead escolhe o futuro.
7. **Nunca faça pergunta N sobre o que a oferta não entrega.** O lead articula um benefício que você não tem = insatisfação garantida na entrega.
8. **Página final só com Benefícios Tipo B**: cada benefício ecoa uma necessidade explícita que o lead marcou na fase N, com as palavras dele. Necessidade PRESUMIDA ou apenas implícita ainda é Vantagem — Benefício exige a escolha verbalizada/marcada. Features soltas e vantagens genéricas proibidas (features → objeção de preço; vantagens → objeção de valor; "o valor está na sequência, não na frase").
9. **Cheque preocupações ANTES do avanço** (etapa própria, penúltima). A resposta vai pro material do closer/follow-up. Se a página final precisa "rebater objeção", faltou I/N — volte e aprofunde.
10. **Modo consultivo sem pressão de fechamento**: nada de timer, cupom, escassez fabricada (pesquisa: fechamento sob pressão derruba venda grande E satisfação pós-venda). No direto/híbrido, elementos de impulso entram com moderação — nunca na fase de perguntas.
11. **Toda resposta coletada é usada** — no eco das perguntas, na Cadeia SPIN, no diagnóstico final ou no material do closer. Pergunta sem destino sai.

## Workflow

### 1. Diagnóstico
Aplique as regras 1 e 2: framework certo? Modo (consultivo/direto/híbrido)? Ticket? Qual é o avanço e o que o lead recebe nele (ex.: call de 40 min com entregável próprio)? Público e identidade visual.

### 2. Mini-entrevista
Pergunte o que faltar (não invente): o que a oferta ENTREGA exatamente (limita as perguntas N — regra 7); os 3–5 problemas reais do público; o custo típico da inação (alimenta as implicações); critérios de qualificação (fatura mínima? nicho?); quem recebe o lead depois (closer? formulário?).

### 3. Cadeia SPIN (a peça central)
Leia `references/destilado-spin.md` (seções 2, 3 e 5) e monte a tabela: **Problema → Implicações a explorar → Pergunta N → Necessidade explícita esperada → Benefício Tipo B na página final.** Nenhuma linha sem as 5 colunas; nenhum benefício na página final sem linha de origem.

### 4. Arquitetura das etapas
Leia `references/anatomia-do-quiz-spin.md` e distribua nas 5 fases (S → P → I → N → D) conforme o modo. Valide contra as regras 3–6; marque em cada etapa qual linha da Cadeia ela serve.

### 5. Copy de cada etapa
Leia `references/exemplos.md` e `references/exemplo-canonico.md` antes. Tom: conversa de diagnóstico entre pares, nunca interrogatório nem pitch. Perguntas I são "tristes" mas nunca humilhantes; perguntas N deixam o lead ESCOLHER o benefício (alternativas = futuros possíveis).

### 6. Diagnóstico final + avanço
Monte a fase D: perfil calculado → resumo com as palavras do lead (espelho da fase N) → demonstração de capacidade só com Benefícios Tipo B → checagem de preocupações → avanço realista. Modo consultivo: inclua a seção "material do closer" no blueprint (respostas mapeadas por letra S/P/I/N + objeção declarada).

Formate em `references/template-blueprint.md` e entregue como arquivo `.md`.

## Graus de liberdade

- **Fixo**: ordem das fases, regras duras, Cadeia SPIN completa, um avanço concreto, formato do entregável.
- **Livre**: quantidade de etapas dentro das faixas do modo, criatividade da copy, quais implicações explorar (desde que venham dos problemas), identidade visual, nome do diagnóstico/perfil.

## Ponteiros

- `references/destilado-spin.md` — o método Rackham completo; leia no passo 3.
- `references/anatomia-do-quiz-spin.md` — as 5 fases, faixas por modo, arquétipos e checklist da página final; leia no passo 4.
- `references/exemplo-canonico.md` — quiz completo de referência (mentoria high ticket, 23 etapas); leia antes do passo 5.
- `references/exemplos.md` — pares certo/errado; leia antes do passo 5.
- `references/template-blueprint.md` — formato do entregável; leia antes de formatar.
