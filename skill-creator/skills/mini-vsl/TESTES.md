# TESTES — mini-vsl

Rodar cada caso em sessão/subagente novo. Comparar com a barra de qualidade. Cada falha vira correção no SKILL.md ou par novo em exemplos.md.

## Teste de gatilho (dispara / não dispara)

**Deve disparar:**
- "escreve uma mini vsl pra minha oferta de mentoria"
- "preciso de um roteiro de vsl de uns 10 minutos"
- "faz uma vsl curta pra vender meu curso"
- "roteiro de mini vsl pra agendar call"

**NÃO deve disparar (skill vizinha):**
- "escreve um roteiro de anúncio de 30 segundos" → skill de ads/vídeo curto
- "faz um carrossel sobre isso" → carrossel
- "escreve a legenda desse post" → legenda-rede-social
- "monta um quiz pra segmentar meu público" → quiz-framework-*
- "escreve uma VSL de webinar de 45 minutos" → avisar que a skill mira 7–15 min e perguntar se quer seguir mesmo assim / usar outra abordagem

## Caso 1 — Contexto completo (caminho feliz)
**Input:** usuário fornece oferta (mentoria de IA pra freelancers, R$1.997, promessa "primeiros 3 clientes em 30 dias"), 2 cases reais com números, descrição de tom ("direto, informal, gírias de internet"), e ICP (freelancer travado em 3-5k/mês).
**Esperado:**
- Faz o priming (3 gatilhos + objeção + mecanismo nomeado) e confirma antes de escrever.
- Roteiro em 7 blocos na ordem, 900–1900 palavras.
- Usa os 2 cases reais com número/prazo — não inventa mais nenhum.
- "Você" o tempo todo; tom bate com o descrito; zero AI-slop.
- Entrega em formato teleprompter limpo.
**Rejeita se:** inventou case/estatística; passou de 1900 palavras; entregou 1º rascunho sem editar; falou "nossos clientes"/multidão.

## Caso 2 — Contexto faltando (testa a regra 1)
**Input:** "escreve uma mini vsl pra minha consultoria" — sem cases, sem voz, sem ICP.
**Esperado:**
- NÃO escreve o roteiro ainda. Levanta os 4 pilares e pergunta o que falta (marca lacunas como "falta", não preenche).
- Oferece rodar deep research pro ICP se ele estiver raso.
- Só avança pro roteiro quando tiver, no mínimo, oferta + uma prova real + noção de voz e ICP.
**Rejeita se:** escreveu a VSL inteira com cases/números fictícios pra "não travar".

## Caso 3 — Edição e específico (testa o passo 4)
**Input:** usuário cola um rascunho de VSL genérico ("cheio de 'transforme sua vida' e 'no mundo de hoje'") e pede pra deixar melhor no padrão mini-VSL.
**Esperado:**
- Roda as 7 correções: mata palavras polidas, quebra ritmo, concretiza abstrações, dor no modo nós-contra-eles, aperta transições.
- Aplica o score-hack (pontua, lista o que falta pra 100, itera).
- Devolve versão específica, com pedido de dados reais onde faltar número/case.
**Rejeita se:** só reescreveu mantendo o tom de IA; manteve promessas abstratas; não pediu os dados reais que faltavam.

## Barra de qualidade (resumo)
Um roteiro só passa se: tudo real e travado com prova · fala com uma pessoa · concreto · dor sem humilhar · 7–15 min · editado (não 1º rascunho) · teleprompter limpo.
