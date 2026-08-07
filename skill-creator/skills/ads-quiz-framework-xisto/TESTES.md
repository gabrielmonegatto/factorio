# Casos de teste — ads-quiz-framework-xisto

(arquivo de desenvolvimento; não instalar em ~/.claude/skills)

## Caso 1 — Leva pro Método Corpo Leve
**Input:** "Cria a leva de anúncios pro meu quiz" + blueprint resumido do Método Corpo Leve (mulheres 30–50, R$27, dores: joelho/costas/tempo/vergonha/desistência; motivo urgente: casamento/viagem/aniversário/verão; nome chiclete: Método Corpo Leve; CTA sugerido: "faça o teste gratuito e descubra seu plano Corpo Leve").
**Esperado:** 6 estruturas com ângulos distintos × 3 hooks = 18 variações; roteiros cena a cena ≤50s com 3 antes/depois (mesma pessoa); prompts de IA com persona de referência única; copy Meta Ads sem menção a preço; mapa gancho↔porta do quiz preenchido (ex.: ângulo casamento → opção casamento da etapa de motivo urgente); CTA "teste gratuito" em tudo.

## Caso 2 — Leva pro Reset Metabólico 40+
**Input:** "Quero os criativos" + blueprint resumido do Reset Metabólico 40+ (mulheres 40+, R$19,90, mecanismo metabolismo travado, dores: barriga/inchaço/efeito sanfona/energia/frio/doce à noite).
**Esperado:** ângulo "dor desconhecida" usa o sintoma (frio/mãos geladas) em UMA frase de curiosidade, sem virar aula de mecanismo; persona dos vídeos é mulher 40+; compliance herdado (sem promessa de cura); nome chiclete idêntico ao blueprint em todas as 18 peças.

## Caso 3 — Armadilha: sem blueprint
**Input:** "Monta uns criativos de anúncio pro meu produto de emagrecimento low ticket, R$27."
**Esperado:** a skill RECUSA e explica a regra dura 1 (criativo herda nome chiclete, dores e motivo urgente do quiz — sem blueprint, gancho órfão quebra o funil), oferecendo rodar a quiz-framework-xisto primeiro. Não gera nenhum roteiro.

## Teste de gatilho
- Deve disparar: "ads quiz framework xisto", "cria os criativos pro quiz do Corpo Leve", "leva de criativos pro funil".
- NÃO deve disparar: "estrutura de campanha ABO pro low ticket" (tráfego), "roteiro de VSL" (formato errado), "criativo pro meu e-commerce" (sem quiz).
