---
name: mini-vsl
description: >
  Escreve o roteiro de uma mini-VSL (Video Sales Letter de 7 a 15 minutos) seguindo o
  framework de venda direta do Luke Alexander: coleta os 4 pilares de contexto (oferta,
  voz da marca, ICP/pesquisa, provas), prima a análise, escreve em 7 blocos (Hook,
  Pain+Agitate, Story+Mechanism, Proof, Offer, Urgency, CTA) e edita com os passes de
  refino até o roteiro soar humano e específico. Entrega em português, formato teleprompter,
  pronto pra gravar. TRIGGER quando o usuário pedir "mini vsl", "escreve uma vsl",
  "roteiro de vsl", "vsl de 7 a 15 minutos", "vsl curta", "roteiro de mini vsl", ou quiser
  um vídeo de vendas roteirizado que agenda call / vende uma oferta. NÃO usar para roteiro
  de anúncio curto, carrossel, legenda ou quiz — para isso use as skills próprias. Se o
  usuário quiser uma VSL longa/webinar de 20+ min, avise que esta skill mira 7–15 min.
---

# Mini-VSL

Escreve o roteiro de uma VSL curta (7–15 min) que leva um espectador frio de "quem é você?" até "me pega o dinheiro" através de uma sequência psicológica. Job: pegar o contexto do negócio, escrever o roteiro em 7 blocos e editá-lo até parar de soar como IA. Entregável: roteiro em português, formato teleprompter, seguindo `references/template-roteiro.md`.

## Regras duras

1. **Tudo é real. Nunca invente prova, número, case ou história.** Se faltar um dado (resultado de cliente, estatística, história de origem), PERGUNTE ao usuário — nunca preencha com um case fictício ou número plausível. A VSL converte *porque* é verdade; um case inventado quebra confiança e compliance.
2. **Toda afirmação trava com prova.** Fez uma claim ("a IA vai tomar seu emprego", "dá pra faturar 15k")? Ancore com número, fonte ou case real na sequência. Claim solta = desconfiança.
3. **Escreva para UMA pessoa — o ICP.** "Você" o tempo todo. Nunca "vocês", "nossos clientes", "pessoas como você". VSL é uma conversa com um indivíduo, não um discurso pra plateia.
4. **Voz da marca, não voz de IA.** Se não houver perfil de voz, colete/pergunte antes de escrever (regra 8 do workflow). Mate as "palavras polidas" de IA (ver destilado) — elas denunciam o roteiro na hora.
5. **Dor no modo "nós contra eles", nunca humilhando o prospecto.** Você e ele do mesmo lado da mesa; o inimigo é externo (o mercado, a mudança, o método que falhou). Afie a dor sem chamar o espectador de burro.
6. **Concreto vence abstrato, sempre.** Toda promessa vaga vira cena específica. "Liberdade financeira" → "parar de conferir o saldo antes de comprar comida". Se não dá pra filmar, reescreva.
7. **Duração dura: 7–15 min (~900–1900 palavras).** Passou disso não é mini-VSL — corte. A ordem dos 7 blocos é fixa; só reordene com motivo real.
8. **Editar é parte do job, não opcional.** O 1º rascunho fica 60–75% pronto. Entregar rascunho cru = não entregar a skill. Rode os passes de edição + o score-hack (passo 4) antes de entregar.

## Workflow

### 1. Coleta dos 4 pilares de contexto
Verifique o que o usuário já deu e levante o que faltar — sem inventar (regra 1). Os 4 pilares:
- **Oferta:** o que é, pra quem, pra quem NÃO é, promessa central (de X a Y em Z tempo), o que inclui, preço, mecanismo único, garantia.
- **Voz da marca:** como o cliente fala. Se não houver, peça 3–10 transcrições (YouTube, calls, áudios) OU peça pra descrever o tom; extraia um mini-perfil de voz.
- **ICP / pesquisa:** dor nº1, frustrações diárias, o que já tentou e falhou, desejo secreto, objeções, crenças falsas, gatilhos emocionais. Se raso, ofereça rodar deep research (comando em `references/destilado-framework.md`).
- **Provas / cases:** resultados antes/depois com número, citações reais, transformações. Sem prova real → pergunte; não invente.

**Output verificável:** os 4 pilares preenchidos, com as lacunas explicitamente marcadas como "falta" (não preenchidas de mentira).

### 2. Priming / análise (antes de escrever uma linha)
Sintetize o contexto e devolva ao usuário: os **3 gatilhos emocionais mais fortes** pra liderar, a **maior objeção** a pré-tratar, e o **mecanismo único** já nomeado. Isso guia o roteiro inteiro.
**Output verificável:** análise de 3 gatilhos + objeção + mecanismo, aprovada pelo usuário.

### 3. Escrever o roteiro (7 blocos)
Leia `references/template-roteiro.md` e `references/destilado-framework.md` (seção "Estrutura dos 7 blocos") antes. Escreva na ordem: **Hook → Pain+Agitate → Story+Mechanism → Proof → Offer → Urgency → CTA**, na voz da marca, pra uma pessoa, com open loops entre blocos, mirando 900–1900 palavras.
**Output verificável:** rascunho completo dos 7 blocos, dentro da faixa de palavras.

### 4. Editar até parar de soar como IA
Leia `references/exemplos.md` e a seção "Edição" do destilado. Rode os passes: (1) ler em voz alta; (2) "um humano diria isso?"; (3) injetar cases/números/histórias reais no lugar do genérico; (4) as 7 correções (matar palavras polidas, quebrar ritmo, concretizar, dor afiada, apertar transições); (5) o **score-hack**: peça ao Claude pra pontuar o roteiro de 0–100 como copywriter de elite e listar o que falta pra chegar a 100 — itere até ~95+.
**Output verificável:** roteiro específico, sem AI-slop, todo case/número real.

### 5. Entregar em formato teleprompter
Formate a saída no padrão da skill `formato-teleprompter` (Markdown limpo, espaçado, marcações de pausa, sem comentário no meio do texto). Sem notas de seção no roteiro de gravação.
**Output verificável:** roteiro pronto pra gravar, sem meta-texto.

## Graus de liberdade

- **Fixo (checklist):** os 4 pilares antes de escrever; ordem dos 7 blocos; duração 7–15 min; "você"/uma pessoa; tudo real e travado com prova; editar antes de entregar; saída em teleprompter.
- **Livre (julgamento):** ângulo do hook; qual dor liderar; tom dentro da voz da marca; nome e analogia do mecanismo; quais cases entram; ritmo e palavras; onde abrir/fechar os open loops.

## Ponteiros

- `references/destilado-framework.md` — o framework completo do Luke: estrutura dos 7 blocos com timings, métodos de pesquisa (incl. o comando de deep research), os 4 arquivos de contexto, as 7 correções, os 5 passes de edição, o score-hack e os princípios de marketing. Leia antes dos passos 3 e 4.
- `references/exemplos.md` — pares certo/errado, um por modo de falha. Leia antes do passo 4.
- `references/template-roteiro.md` — estrutura exata do entregável (7 blocos + formatação teleprompter). Use no passo 3.
