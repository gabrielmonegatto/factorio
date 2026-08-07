# Entrevista de criação de skill

Conduza como conversa, não como formulário — mas cubra os 8 blocos. Use AskUserQuestion quando houver opções claras; pergunta aberta quando precisar de história. Salve a síntese em `entrevistas/<nome-da-skill>.md`.

## Bloco 1 — O Job (o que ela faz)
1. Qual tarefa essa skill executa? Descreva uma execução completa: o que você me dá de input e o que sai de output.
2. Como é o "pronto"? Um arquivo? Um texto na conversa? Algo publicado em algum lugar?
3. Me dá um exemplo REAL da última vez que você fez essa tarefa manualmente (ou queria ter feito).

## Bloco 2 — Gatilho (quando ela dispara)
4. Que frases você diria para pedir isso? (Coletar 3-5 frases literais — elas vão direto pro TRIGGER da description.)
5. Existe pedido parecido em que essa skill NÃO deve disparar? Qual skill deveria atender nesse caso?

## Bloco 3 — Barra de qualidade (o mais importante)
6. Me mostra um exemplo de resultado EXCELENTE dessa tarefa (seu ou de outra pessoa). O que faz ele ser excelente?
7. Me mostra um exemplo mediano ou ruim. O que estragou?
8. Se a skill entregar 8/10 em tudo, qual dimensão te faria rejeitar mesmo assim? (Essa é a regra dura número 1.)

## Bloco 4 — Modos de falha
9. Quando você (ou uma IA) faz essa tarefa, quais são os erros mais comuns?
10. Tem algum erro que é INACEITÁVEL — que quebra confiança, compliance, ou a marca?

## Bloco 5 — Fontes de expertise
11. Tem livro, curso, criador ou material que define como essa tarefa deve ser feita? (Se sim → pipeline de livros.)
12. Tem exemplos seus antigos que eu possa usar como referência de voz/formato?

## Bloco 6 — Graus de liberdade
13. O que deve ser SEMPRE igual, execução após execução? (vira checklist)
14. Onde eu tenho liberdade criativa? (vira heurística)

## Bloco 7 — Contexto de execução
15. A skill precisa de ferramentas externas (MCP, APIs, scripts)? Precisa ler arquivos de algum lugar fixo?
16. Roda sozinha ou faz parte de um pipeline com outras skills? Qual vem antes/depois?

## Bloco 8 — Formato de output
17. Estrutura exata do entregável: seções, tamanho, idioma, onde salvar.
18. Existe template pronto? (Se sim, vira `references/template.md`.)

## Depois da entrevista
- Repita de volta em 5 linhas o que entendeu e peça confirmação antes da Fase 3.
- As respostas dos blocos 3 e 4 viram os pares certo/errado de `references/exemplos.md`.
- As frases do bloco 2 entram LITERALMENTE na description.
