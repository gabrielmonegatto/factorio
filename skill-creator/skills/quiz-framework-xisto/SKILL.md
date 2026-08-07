---
name: quiz-framework-xisto
description: >
  Cria o blueprint completo de um funil de quiz para produtos low ticket seguindo o
  framework do Victor Xisto (ASK Method + personalização 80/20): arquitetura etapa por
  etapa (20–35 steps) com a copy de cada tela, lógica de personalização resposta→benefício,
  diretrizes de design por público, página de plano final e order bump. Entrega em Markdown,
  pronto para montar no InLead ou em código. TRIGGER quando o usuário pedir "quiz framework
  xisto", "monta um quiz pra esse produto", "funil de quiz", "quiz de low ticket", "quiz
  estilo Better Me", ou quiser transformar uma oferta validada (VSL, nutra, landing page)
  em quiz. NÃO usar para quiz de engajamento/conteúdo sem venda, nem para estratégia de
  criativos ou tráfego. NÃO usar para quiz de pesquisa/segmentação de mercado (buckets,
  Ask Method canônico de Ryan Levesque) — para isso use quiz-framework-ask-method. NÃO
  usar para venda consultiva/high ticket, qualificação para call ou ticket médio-alto
  (R$97+) — para isso use quiz-framework-spin-selling. Se o pedido for de quiz sem
  definir o framework e sem sinal claro de venda low ticket por impulso (ticket R$17–27,
  oferta validada, Better Me), PERGUNTE qual dos três o usuário quer antes de começar.
---

# Quiz Framework Xisto

Constrói funis de quiz que vendem por perguntas: o lead entra por curiosidade ("teste gratuito"), fica consciente do problema respondendo, e no final recebe um plano tão personalizado e tão barato que comprar parece óbvio. Entregável: um blueprint em Markdown seguindo `references/template-blueprint.md`.

## Regras duras

1. **Cheque o formato antes de tudo.** Quiz é para produto personalizável (plano, desafio, teste, app). Produto simples/físico/SaaS → página de vendas; expert com promessa forte ou ticket R$67–97 → VSL. Se o produto não é caso de quiz, diga isso e pare — funil errado com produto errado é o erro nº 1 (a conversão só explode quando o formato encaixa na promessa).
2. **Nunca venda durante as perguntas.** Nada de pitch nem preço antes da fase 5; depoimento explícito só na página de plano (validações e "outros alunos conseguiram" podem aparecer como alívio a partir da fase 2). As perguntas vendem sozinhas; o lead quer ser compreendido, não vendido.
3. **Nunca abra com prova social.** O início é pesquisa. Prova social entra no meio e no final.
4. **Toda dor perguntada TEM que reaparecer no final** como benefício, bônus ou módulo nomeado. Dor coletada e ignorada quebra a promessa de personalização — que é o 80/20 do quiz.
5. **Toda etapa coleta uma dor OU entrega alívio/consciência.** Etapa que não faz nenhum dos dois sai do blueprint.
6. **Padrão dor → alívio imediato, em pares fechados**: depois de toda pergunta que expõe dor, a etapa seguinte tranquiliza com prova + solução. Ciclos nunca se empilham — toda dor fecha antes da próxima abrir.
7. **Preço só no final**, depois da ancoragem (percepção de R$200–300 → checkout de R$17–27). Preço por dia em destaque, plano único (3 planos só em recorrência).
8. **20 a 35 etapas.** 20–25 no padrão; até 35 só se o mecanismo exige mais explicação/coleta.
9. **Quiz masculino nunca em fundo branco** (ref. The Coach: escuro + cor de destaque). Feminino: claro e clean (ref. Better Me).
10. **A dor mais comum do público não vai na oferta principal — vai no order bump.**

## Workflow

### 1. Diagnóstico
Aplique a regra dura 1. Identifique: produto/mecanismo, ticket (padrão R$17–27), público (sexo/idade — define a identidade visual) e se é modelagem de oferta validada (VSL/nutra/gringa) ou oferta nova. Se for modelagem: manter o mecanismo, trocar o nome chiclete.

### 2. Mini-entrevista
Pergunte ao usuário o que faltar (não invente): 3–5 dores principais do público, o entregável (app/PWA? área de membros? plano em PDF?), promessa central e prazo, existência de evento/sazonalidade aproveitável (casamento, Enem, Páscoa...), nome chiclete (se não houver, proponha 5–10 opções e peça escolha).

### 3. Matriz de personalização (o coração do quiz)
Antes de desenhar etapas, leia `references/destilado-xisto.md` (seções 3–7) e monte a tabela: cada dor/resposta possível → o benefício, bônus ou módulo nomeado que ela vira no plano final → ou o order bump, se for a dor mais comum não coberta. Nenhuma linha da matriz pode ficar sem destino.

### 4. Arquitetura das etapas
Leia `references/anatomia-do-quiz.md` e distribua as etapas nas 5 fases (1 Avatar → 2 Dores e Desejos → 3 Consciência → 4 Cálculo para Personalização → 5 Personalização da Oferta), usando os arquétipos de etapa de lá. Respeite a regra de intercalação (pares dor→alívio) e a escada de intimidade (fase 2 = dores que o lead já sabe; fase 3 = dores que o quiz revela). Valide cada etapa contra as regras duras 5 e 6.

### 5. Copy de cada etapa
Escreva o texto de cada tela: pergunta, alternativas (com indicação de imagem real, nunca IA/desenho), interlúdios de alívio, validações ("você bebe mais água que 50% dos usuários"), cálculos e projeções com data. Tom: conversa de pesquisa, nunca de venda. Antes de escrever, leia `references/exemplos.md`.

### 6. Plano final + order bump
Monte a página de plano com o checklist de design do `anatomia-do-quiz.md` (preço por dia, plano único, cupom animado, timer, CTA fixo, 6–10 provas sociais, bônus riscados "de R$99 por R$0", garantia 90 dias). Defina o order bump pela matriz do passo 3. Upsell só se o usuário pedir — e no formato quiz/página, nunca VSL.

Formate tudo em `references/template-blueprint.md` e entregue como arquivo `.md` (pergunte onde salvar se não houver contexto de projeto).

## Graus de liberdade

- **Fixo**: ordem das 3 fases, regras duras, elementos da página final, formato do entregável.
- **Livre**: quantidade exata de etapas dentro da faixa, criatividade da copy, quais validações/curiosidades usar no meio, nomes de bônus e do plano, proposta de nome chiclete.

## Ponteiros

- `references/destilado-xisto.md` — o framework completo; leia as seções 1–8 no passo 3.
- `references/anatomia-do-quiz.md` — arquétipos de etapa + checklist de design; leia no passo 4.
- `references/template-blueprint.md` — formato do entregável; leia antes de formatar.
- `references/exemplos.md` — pares certo/errado; leia antes de escrever copy (passo 5).
