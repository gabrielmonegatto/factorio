# Casos de teste — ads-quiz-framework-ask-method

(arquivo de desenvolvimento; não instalar)

## Caso 1 — Leva com blueprint fornecido
**Input:** "Cria os anúncios pro meu quiz de buckets" + blueprint resumido (quiz "Qual é o seu gargalo de agência?", 4 buckets: Tráfego que não converte 34% / Funil Furado 28% / Ticket Travado 22% / Recomeço Eterno 16%, com rótulos e 1 frase de linguagem do Deep Dive cada; promessa: "descubra seu gargalo nº 1").
**Esperado:** 6 estruturas × 3 hooks = 18, TODOS os ganchos em forma de pergunta; guarda-chuva com se-então cobrindo os 4 buckets; buckets dominantes (34% e 28%) com anúncio próprio; rótulos idênticos; zero preço/oferta/urgência; N=4 em todas as peças de "número finito"; mapa anúncio↔bucket completo.

## Caso 2 — Armadilha: sem blueprint
**Input:** "Faz uns anúncios de quiz de diagnóstico pro meu negócio de consultoria financeira."
**Esperado:** RECUSA pela regra 1 — sem blueprint não há buckets nem linguagem do Deep Dive; anúncio com buckets inventados promete diagnóstico que o quiz não entrega. Oferece rodar a quiz-framework-ask-method primeiro.

## Caso 3 — Armadilha: blueprint do framework errado
**Input:** "Cria os anúncios pro meu quiz" + blueprint do Método Corpo Leve (quiz XISTO de emagrecimento R$27, com matriz de personalização e página de plano).
**Esperado:** identifica que o blueprint é da quiz-framework-xisto (matriz de personalização + checkout ≠ buckets + diagnóstico) e REDIRECIONA para ads-quiz-framework-xisto, sem gerar leva com o framework errado.

## Teste de gatilho
- Deve disparar: "ads ask method", "anúncios pro quiz de buckets", "criativos pro meu bucket survey".
- NÃO deve disparar: "criativos pro quiz do Corpo Leve" (ads-xisto), "anúncios pro quiz da minha mentoria" (ads-spin), "estrutura de campanha" (tráfego).
