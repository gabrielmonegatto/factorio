# Casos de teste — quiz-framework-spin-selling

(arquivo de desenvolvimento; não instalar em ~/.claude/skills)

## Caso 1 — Consultivo high ticket
**Input:** "Monta um quiz SPIN pra minha consultoria de posicionamento pra clínicas odontológicas, ticket R$15k, quero que termine agendando uma call comigo."
**Esperado:** modo consultivo; 18–26 etapas nas 5 fases S→P→I→N→D; Cadeia SPIN completa (5 colunas); situação ≤5 perguntas com propósito; bloco I proporcional ao ticket alto; fase N só com o que consultoria entrega; fase D com espelho literal das escolhas N, checagem de preocupações e avanço sem timer/cupom; material do closer incluído.

## Caso 2 — Híbrido-Xisto ticket médio
**Input:** "Quero um quiz pro meu curso de R$197 de precificação pra designers — algo entre o impulso e o consultivo."
**Esperado:** modo híbrido reconhecido; espinha do Xisto com motor P→I→N; página final com elementos de conversão moderados MAS benefícios só Tipo B (ecoando as escolhas N); nada de feature-dump; mini-entrevista antes de inventar dores.

## Caso 3 — Armadilha: impulso low ticket
**Input:** "Faz um quiz spin selling pro meu ebook de receitas fit de R$17."
**Esperado:** a skill explica que compra por impulso de R$17 é caso da quiz-framework-xisto (implicação em decisão trivial mata o ímpeto — venda pequena pede mecânica de venda pequena) e redireciona, SEM montar o quiz SPIN. Aceita montar via Xisto se o usuário quiser.

## Teste de gatilho
- Deve disparar: "quiz spin selling", "quiz de venda consultiva pra minha mentoria", "quiz de qualificação pra call".
- NÃO deve disparar: "monta um quiz estilo Better Me" (Xisto), "quiz de buckets pra segmentar minha lista" (Ask Method), "roteiro de call de vendas SPIN" (não é quiz).
- Ambíguo ("monta um quiz pro meu produto"): deve perguntar qual dos três frameworks.
