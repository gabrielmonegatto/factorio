# Casos de teste — quiz-framework-xisto

(arquivo de desenvolvimento; não instalar em ~/.claude/skills)

## Caso 1 — Clássico Better Me
**Input:** "Monta um quiz pro meu produto: app de treino em casa pra mulheres 30-50 que querem emagrecer, ticket R$27, sem expert ainda."
**Esperado:** blueprint completo de 20–25 etapas nas 5 fases (Avatar → Dores e Desejos → Consciência → Cálculo → Personalização da Oferta); identidade clara/clean; matriz com toda dor→benefício; pares dor→alívio fechados (sem empilhamento); motivo urgente de mudança presente; plano único com preço/dia; order bump derivado de dor comum (ex.: dor nas costas); zero pitch nem preço antes da fase 5; copy pronta pra colar.

## Caso 2 — Modelagem de VSL
**Input:** "Tenho uma oferta de nutra de VSL validada na gringa (mecanismo: metabolismo travado em mulheres 40+). Quero transformar em quiz low ticket no Brasil."
**Esperado:** a skill mantém o mecanismo, TROCA o nome chiclete (propõe 5–10 opções), entregável vira app/plano (não ebook), e registra na seção "Origem" o que manteve/trocou. Perguntas do quiz construídas em volta do mecanismo (sintomas de metabolismo travado → alívios).

## Caso 3 — Armadilha: produto que não é de quiz
**Input:** "Monta um quiz pro meu SaaS de páginas de presente personalizadas pra namorados, R$19."
**Esperado:** a skill RECUSA educadamente citando a regra do formato (produto SaaS simples → página de vendas; o próprio Xisto rodou esse produto exato em página de vendas) e oferece ajudar na página de vendas em vez do quiz. Não gera blueprint.

## Teste de gatilho
- Deve disparar: "quiz framework xisto", "monta um quiz pra vender meu curso de Enem", "transforma essa VSL em quiz".
- NÃO deve disparar: "cria um quiz divertido pros meus stories" (engajamento, sem venda), "estrutura de campanha ABO pro meu low ticket" (tráfego).
