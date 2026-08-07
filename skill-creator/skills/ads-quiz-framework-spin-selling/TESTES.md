# Casos de teste — ads-quiz-framework-spin-selling

(arquivo de desenvolvimento; não instalar)

## Caso 1 — Leva com blueprint fornecido
**Input:** "Cria os anúncios pro meu quiz consultivo" + blueprint resumido do quiz da consultoria odonto (R$15k, modo consultivo, avanço = Sessão de Diagnóstico 45 min + mapa de reposicionamento; Cadeia: competindo por preço com franquia / avaliação que não fecha / dono preso na cadeira / marketing que atrai curioso, com implicações quantificadas; qualificação: dentista dono, R$50k+/mês).
**Esperado:** 6 estruturas × 3 hooks = 18, todas mapeadas em linhas reais da Cadeia; qualificação embutida nos ganchos; mix de formatos distribuído (talking head, case, UGC sóbrio, estático); ZERO solução/método/features/cupom/timer; CTA afirmado uma vez com o entregável ("mapa de reposicionamento"); case terminando na descoberta, não na compra; métrica de custo por avanço qualificado nas notas.

## Caso 2 — Armadilha: sem blueprint
**Input:** "Quero anúncios estilo SPIN pra minha mentoria de 10k."
**Esperado:** RECUSA pela regra 1 — sem blueprint não há Cadeia SPIN nem avanço definidos; gancho órfão atrai lead que o quiz não desenvolve. Oferece rodar a quiz-framework-spin-selling primeiro.

## Caso 3 — Armadilha: blueprint do framework errado
**Input:** "Faz a leva de anúncios do meu quiz" + blueprint do "Qual é o seu gargalo de agência?" (quiz ASK METHOD com 4 buckets e páginas de diagnóstico).
**Esperado:** identifica que o blueprint é da quiz-framework-ask-method (buckets + diagnóstico ≠ Cadeia SPIN + avanço) e REDIRECIONA para ads-quiz-framework-ask-method, sem gerar leva com o framework errado.

## Teste de gatilho
- Deve disparar: "ads spin selling", "anúncios pro quiz da minha consultoria", "criativos de qualificação pra call".
- NÃO deve disparar: "criativos pro quiz de emagrecimento R$27" (ads-xisto), "anúncios pro bucket survey" (ads-ask), "roteiro de call" (não é anúncio).
