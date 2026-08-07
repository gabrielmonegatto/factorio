# Testes: quiz-framework-ask-method

> Rodar cada caso em subagente/sessão nova. Comparar com a barra de qualidade da entrevista (`entrevistas/quiz-framework-ask-method.md`). Falha = correção no SKILL.md ou novo par em exemplos.md.

## Caso 1 — Pedido com informação incompleta (testa regra 2: perguntar, não inventar)

**Input:** "quiz ask method pro meu mercado de consultoria financeira"

**Output esperado:**
- A skill NÃO gera o quiz direto. Pergunta antes: público, promessa do diagnóstico, se existem dados de pesquisa aberta, e o que acontece depois do quiz.
- Só depois das respostas propõe buckets — e, sem dados, marca todos como `[HIPÓTESE]` e aponta o "Outro" como termômetro.

**Falha se:** gerar quiz completo de primeira, com buckets inventados apresentados como fatos.

## Caso 2 — Execução completa com contexto dado (testa a barra de qualidade)

**Input:** "quiz de buckets para app de treino em casa para mulheres 40+. Promessa: 'descubra seu tipo de treino ideal'. Sem dados de pesquisa. Depois do quiz: captura pra lista + oferta do app."

**Output esperado (checar TODOS):**
- 6–8 telas; tela 1 binária e trivial; segmentação por último recapitulando respostas em colchetes + "Nenhuma das opções acima"; captura depois da última pergunta.
- 3–5 buckets por problema central (não por idade/demografia), cada um com prescrição distinta e página de resultado própria com rótulo nomeado.
- Zero pitch/preço/prova social nas perguntas.
- Tabela de arquitetura com uso declarado de toda variável.
- Blueprint no formato do template, com checklist preenchida.

**Falha se:** qualquer pergunta vender; resultado igual entre buckets; mais de 8 telas; variável coletada sem uso.

## Caso 3 — Gatilho e fronteira (testa a description)

**Input A (deve disparar):** "monta um quiz rayan levasque pra segmentar minha audiência"
**Input B (NÃO deve disparar esta skill):** "monta um funil de quiz pra vender meu curso de R$27, estilo Better Me"
**Input C (ambíguo — deve perguntar):** "monta um quiz pro meu produto"

**Output esperado:**
- A → skill dispara e segue o workflow.
- B → quiz-framework-xisto atende; esta skill não dispara.
- C → antes de qualquer coisa, perguntar: "quiz de segmentação de mercado (Ask Method) ou quiz de venda low ticket (Xisto)?"

**Falha se:** A não disparar; B disparar esta skill; C seguir direto sem perguntar.

## Resultado das rodadas

| Data | Caso | Resultado | Correção aplicada |
|---|---|---|---|
| 2026-07-04 | 1 (input incompleto) | ✅ PASSOU — perguntou público, promessa, dados, pós-quiz; não inventou buckets | — |
| 2026-07-04 | 2 (execução completa) | ✅ PASSOU — 7 telas, 4 buckets-hipótese marcados, prescrições distintas, rótulos próprios, zero venda, parou pra aprovação dos buckets | — |
| 2026-07-04 | 3 (gatilhos) | ⚠️ 4/5 — input C ("monta um quiz pro meu produto") disparou a xisto direto em vez de perguntar, por causa do trigger genérico "monta um quiz pra esse produto" na description dela | Adicionada à description da quiz-framework-xisto a fronteira reversa + regra de perguntar quando não há sinal de low ticket; reinstalada |
| 2026-07-04 | 3 (re-teste pós-correção) | ✅ PASSOU — ambíguo pergunta; venda low ticket → xisto; buckets → ask-method | — |
