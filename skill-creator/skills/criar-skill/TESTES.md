# Testes — criar-skill

## Caso 1 (típico): pedido de skill nova
**Input:** "quero uma skill que transforma os release notes do meu app em post de changelog pro blog, num tom mais leve"
**Output esperado:** NÃO rascunha nada de imediato. Detecta o ambiente (Passo 0), inicia a entrevista de 8 blocos como conversa (não formulário), pede exemplos reais bons E ruins, e só rascunha depois da síntese confirmada. O rascunho segue a anatomia (description com frases literais + [QUANDO NÃO], ≤150 linhas, regras com porquê).
**Resultado:** _pendente_

## Caso 2 (borda): modo standalone + livro como fonte
**Input:** (numa pasta qualquer, sem a fábrica montada) "cria uma skill de headlines baseada no livro do John Caples que está em ~/Downloads/tested-advertising-methods.pdf"
**Output esperado:** Detecta que a fábrica não está disponível e segue standalone SEM perguntar o modo. Aplica o pipeline de livros: destila (não cola o livro), destilado vai para references/ da skill, avisa que não ficará arquivado para reúso. Valida o destilado com a pergunta "o que desse livro você usa que não está aqui?".
**Resultado:** _pendente_

## Caso 3 (erro inaceitável): conserto de skill em produção
**Input:** "a skill legenda-rede-social errou de novo: colocou hashtag no meio da legenda, era pra ser só no final"
**Output esperado:** Localiza a cópia dev (fábrica se existir, senão a instalada), REPRODUZ o erro em subagente antes de mexer, corrige, transforma o erro em par ❌/✅ em references/exemplos.md, re-roda o caso novo + os casos existentes do TESTES.md da skill, reinstala. Não corrige às cegas.
**Resultado:** _pendente_

## Teste de gatilho
**Should-trigger:** "cria uma skill pra...", "transforma esse processo que a gente acabou de fazer numa skill", "vira skill", "a skill formato-teleprompter tá errando o tempo de leitura", "melhora a description da skill carrossel"
**Near-misses (NÃO disparar):** "adiciona uma permissão pro npm no settings" (→ update-config), "cria um hook que roda depois de cada edit" (→ update-config), "cria um subagente revisor em .claude/agents/", "instala a skill do repo da Anthropic" (instalação ≠ criação), "cria um projeto novo pro cliente X" (→ novo-projeto)
**Resultado:** _pendente_
