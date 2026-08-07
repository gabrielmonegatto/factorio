---
name: quiz-framework-ask-method
description: >
  Cria o blueprint de um quiz de segmentação de mercado seguindo o Ask Method canônico de
  Ryan Levesque (Micro-Commitment Bucket Survey): perguntas em ordem de micro-compromisso
  (Engraxar as Rodas → personalização → segmentação), 3–5 buckets acionáveis e página de
  resultado com diagnóstico próprio por bucket. Entrega em Markdown, pronto para montar em
  qualquer ferramenta de quiz. TRIGGER quando o usuário pedir "quiz ask method", "quiz de
  buckets", "quiz ryan levesque", "bucket survey", ou quiser segmentar o público/mercado com
  um quiz de pesquisa. NÃO usar para quiz de venda de produto low ticket (estilo Better Me,
  ticket R$17–27) — para isso use quiz-framework-xisto. Se o pedido for só "monta um quiz"
  sem framework definido, PERGUNTE qual dos dois o usuário quer antes de começar.
---

# Quiz Framework Ask Method

Monta o quiz de segmentação do Ask Method: o lead responde perguntas de micro-compromisso crescente, cai num de 3–5 buckets definidos pelo problema central, deixa o contato e recebe um diagnóstico personalizado. O quiz simula um especialista fazendo perguntas pessoalmente antes de recomendar — se uma pergunta não soaria natural nessa conversa, ela está errada. Entregável: blueprint em Markdown seguindo `references/template-blueprint.md`.

## Regras duras

1. **Nunca venda dentro do quiz.** Nada de pitch, preço, oferta ou depoimento em nenhuma pergunta — quiz que cheira a vendedor quebra a confiança que faz o método funcionar. A venda começa só na página de resultado (prescrição), e mesmo lá o diagnóstico vem antes da oferta.
2. **Nunca invente o que não sabe.** Se faltar mercado, promessa do diagnóstico, dados ou oferta, pergunte ao usuário antes de continuar. Buckets sem dados de pesquisa são HIPÓTESES — marque-as como tal no blueprint e aponte o "Outro" como termômetro de validação.
3. **3–5 buckets, definidos por problema central, cobrindo ~80% do mercado.** Nunca por demografia (demografia personaliza, problema segmenta). Cada bucket tem que mudar a prescrição final; dois buckets com a mesma prescrição = um bucket.
4. **Ordem fixa das telas:** Engraxar as Rodas (binária, trivial) → personalização (2–4 perguntas, dificuldade crescente) → segmentação (última pergunta) → captura de nome/e-mail → resultado. Contato NUNCA antes da última pergunta (pedir cedo dispara fuga; micro-compromissos criam ímpeto).
5. **Toda variável coletada tem que ser usada** — na pergunta seguinte (colchetes), na página de resultado ou no follow-up. Pergunta cuja resposta não muda nada sai do quiz.
6. **A pergunta de segmentação recapitula as respostas anteriores** em linguagem coloquial ("Os [donos de negócio] que faturam [pelo menos 100 mil]...") e **sempre inclui "Nenhuma das opções acima"** — se >10% caírem nela, os buckets estão errados.
7. **6 a 8 telas no total** (1 engraxar rodas + 2–4 personalização + 1 segmentação + captura + resultado). Quiz de segmentação longo = abandono. (Se o usuário quer 20+ telas pra vender low ticket, ele quer a quiz-framework-xisto.)
8. **Cada bucket recebe página de resultado própria, com diagnóstico nomeado** (rótulo tipo "Maldição do Tráfego Frio"). Resultado igual pra todos = segmentação de teatro.
9. **Máximo de opções por pergunta: consolide 80/20.** Menos opções = mais respostas. Funda categorias pequenas (<5%) nas maiores. Randomize a ordem das opções (exceto "Outro", sempre por último).

## Workflow

### 1. Coleta de contexto
Verifique o que o usuário já deu e pergunte o que faltar (regra 2): mercado/nicho e público; a promessa do diagnóstico ("descubra seu tipo de X"); se existem dados de pesquisa aberta (Deep Dive, respostas de SMIQ, comentários, DMs); o que acontece depois do quiz (oferta? lista? follow-up?). Se o pedido for ambíguo entre Ask e Xisto, pergunte qual framework.
**Output verificável:** lista de contexto preenchida, sem lacunas inventadas.

### 2. Definição dos buckets
Leia `references/destilado-ask.md` (seções "Deep Dive Survey" e "Regras operacionais") antes deste passo.
- **Com dados abertos:** analise focando nos hiper-responsivos (respostas longas e engajadas), categorize, consolide em passadas até 3–5 temas cobrindo ~80%.
- **Sem dados:** proponha 3–5 buckets-hipótese a partir do conhecimento do mercado, declare que são hipóteses e recomende validação (Deep Dive rápido ou monitorar o "Outro").
Para cada bucket: nome, problema central na linguagem do mercado, % estimado, e qual prescrição muda.
**Output verificável:** tabela de buckets aprovada pelo usuário ANTES de escrever perguntas.

### 3. Arquitetura das perguntas
Monte a tabela de telas: nº, tipo (engraxar rodas / personalização / segmentação), pergunta, variável coletada e ONDE ela será usada. Aplique as regras 4, 5 e 7.
**Output verificável:** tabela em que nenhuma linha tem a coluna "uso da variável" vazia.

### 4. Copy das telas
Leia `references/exemplos.md` antes de escrever. Escreva cada tela: pergunta + opções + lógica condicional (colchetes ecoando respostas anteriores, com naturalidade — subestime a personalização). Tom coloquial, de conversa presencial.
**Output verificável:** todas as telas escritas, com a pergunta de segmentação recapitulando e com "Outro".

### 5. Captura e páginas de resultado
Tela de captura: nome + e-mail em troca do diagnóstico prometido. Uma página de resultado por bucket: rótulo do diagnóstico, explicação do que significa (demonstrando compreensão com a linguagem do próprio bucket), e ponte para o próximo passo definido no passo 1 (oferta, conteúdo, lista).
**Output verificável:** N buckets = N páginas de resultado, nenhuma copiada da outra.

### 6. Blueprint final
Monte o documento completo seguindo `references/template-blueprint.md`, incluindo a checklist de validação preenchida.
**Output verificável:** blueprint em Markdown com todas as seções do template.

## Graus de liberdade

- **Fixo (checklist):** ordem das telas; tipos de pergunta; 3–5 buckets por problema; "Outro" na segmentação; recapitulação; captura no fim; resultado por bucket; 6–8 telas; zero venda nas perguntas.
- **Livre (julgamento):** texto e tom das perguntas; qual variável trivial abre o quiz; quais variáveis de personalização coletar (desde que usadas); nomes/rótulos dos buckets e diagnósticos; copy das páginas de resultado.

## Ponteiros

- `references/destilado-ask.md` — o método canônico do livro. Leia as seções indicadas no passo 2; consulte "Prescrição" ao escrever páginas de resultado.
- `references/exemplos.md` — pares certo/errado, um por modo de falha. Leia antes do passo 4.
- `references/template-blueprint.md` — estrutura exata do entregável. Use no passo 6.
