# Protocolo de teste — os 3 testes antes de instalar

Uma skill não está pronta quando compila — está pronta quando passa nos três testes abaixo, nesta ordem. Cada falha vira uma correção no SKILL.md ou um novo par certo/errado em `references/exemplos.md`; depois re-rode o teste que falhou.

## Antes de tudo: escreva o TESTES.md

3 casos mínimos em `<skill>/TESTES.md`, cada um com:

```markdown
## Caso N: <o que este caso testa>
**Input:** <pedido realista, como o usuário digitaria — com contexto, nome de arquivo, informalidade>
**Output esperado:** <critérios verificáveis, extraídos da barra de qualidade da entrevista (bloco 3)>
**Resultado:** <preencher após rodar: PASSOU/FALHOU + o quê>
```

Cubra: 1 caso típico, 1 caso de borda, 1 caso que toca o erro inaceitável do bloco 4.

## Teste 1 — Qualidade cega

Rode cada caso num **subagente que recebe SÓ o input do caso + o caminho da skill** — nada da conversa de criação. Você escreveu a skill; se você mesmo rodar o teste, seu contexto contamina o resultado.

Prompt do subagente:
```
Leia a skill em <caminho>/SKILL.md e siga suas instruções para executar esta tarefa:
<input do caso>
Salve o output em <pasta-de-teste>/caso-N/.
```

Compare cada output com a barra de qualidade da entrevista. A pergunta do bloco 3.8 ("o que te faria rejeitar mesmo com 8/10 em tudo?") é o critério de corte.

## Teste 2 — Baseline (a skill agrega?)

Rode **pelo menos 1 dos casos SEM a skill**: mesmo prompt, mesmo subagente, sem o caminho da skill. Compare com o output com-skill do mesmo caso.

- Output com skill claramente melhor → a skill agrega; siga.
- Outputs equivalentes → a skill está inchando contexto sem retorno. Duas saídas: (a) a skill carrega expertise que o caso não exercitou — troque por um caso que exercite; (b) o Claude já faz isso bem sozinho — **reescreva a skill para cobrir só o delta, ou aborte a criação e diga isso ao usuário**. Instalar skill que não agrega é custo permanente sem benefício.

Ao melhorar skill existente, o baseline é a versão antiga (snapshot antes de editar), não "sem skill".

## Teste 3 — Gatilho com near-misses

Monte ~10 queries realistas (como o usuário digitaria de verdade: minúsculas, typos, contexto pessoal, nome de arquivo) e teste cada uma num subagente que recebe a lista de descriptions das skills instaladas relevantes + a query, perguntando: "qual skill você usaria para este pedido, ou nenhuma?"

- **5 should-trigger**: variações das frases literais do bloco 2 + pelo menos 1 que expressa a intenção SEM usar as palavras-chave da description.
- **5 near-misses (should-NOT-trigger)**: pedidos que compartilham palavras-chave com a skill mas pertencem a skill vizinha ou a nenhuma. Os melhores near-misses vêm da pergunta 5 do bloco 2. Near-miss óbvio demais ("escreve uma função fibonacci" para uma skill de legendas) não testa nada — o near-miss bom é o que um match ingênuo de palavra-chave erraria.

Critério: 10/10. Uma falha de should-trigger → fortalecer o TRIGGER com a frase que falhou. Uma falha de near-miss → adicionar/afiar o bloco [QUANDO NÃO] na description (da skill nova E, se preciso, da vizinha).

## Registro

Preencha o campo **Resultado** de cada caso no TESTES.md, incluindo o baseline e o placar do gatilho. O TESTES.md é a memória de regressão da skill: ao consertá-la no futuro, re-rode os casos existentes além do novo.
