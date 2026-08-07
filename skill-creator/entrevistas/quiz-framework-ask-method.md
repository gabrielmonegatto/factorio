# Entrevista: quiz-framework-ask-method

> Data: 2026-07-04. Conduzida antes do rascunho, conforme processo.

## Bloco 1 — O Job
- A skill entrega **só o quiz de segmentação** (Micro-Commitment Bucket Survey) do Ask Method. O restante do método (Deep Dive, prescrição, e-mails) fica como contexto no destilado, não como entregável.
- Input: **o que o Pedro tiver** — a skill deve perguntar tudo que faltar antes de continuar (nunca inventar mercado, buckets ou oferta).
- Pronto = **Blueprint em Markdown**: perguntas na ordem, opções de resposta, lógica de buckets, página de resultado por bucket. Pronto para montar em qualquer ferramenta.

## Bloco 2 — Gatilhos
Frases literais do Pedro:
- "quiz ask method"
- "quiz de buckets"
- "quiz rayan levasque" (incluir variações de grafia: Ryan Levesque)

NÃO disparar: pedidos da `quiz-framework-xisto` ("quiz de low ticket", "quiz estilo Better Me", "funil de quiz" para vender produto).
**Regra de ambiguidade**: se o pedido for só "monta um quiz" sem definir framework, PERGUNTAR qual dos dois o usuário quer (Ask Method = segmentar mercado; Xisto = vender low ticket). Essa regra vale para as duas skills.

## Bloco 3 — Barra de qualidade
- Rejeição mesmo com 8/10 em tudo: **perguntas que vendem**. Quiz que parece pesquisa de vendedor em vez de diagnóstico genuíno quebra a confiança que faz o método funcionar. → Regra dura nº 1.

## Bloco 4 — Modos de falha (todos confirmados pelo Pedro)
1. Perguntas que vendem (inaceitável — regra dura nº 1)
2. Buckets demais/genéricos — segmentação que não muda a prescrição
3. Quiz longo demais — abandono antes do fim
4. Começar com pergunta difícil/ameaçadora — mata o micro-compromisso
5. Resultado igual pra todos os buckets — segmentação vira teatro

→ Cada um vira um par certo/errado em `references/exemplos.md`.

## Bloco 5 — Fontes de expertise
- Livro: **Ask — Ryan Levesque (PT)**, `/Volumes/KINGSTON/books/Ask-Ryan-Levesque-PT.pdf`. Aplicação **canônica** do livro, sem adaptação própria.
- Destilar capítulos 11–18 + glossário; casos 19–20 (tênis, ionizadores) só como exemplos canônicos.
- Exemplos: só os do livro (Pedro não tem quizzes próprios para referência).

## Bloco 6 — Graus de liberdade
- **Fixo**: arquitetura Ask — ordem das perguntas, tipos de pergunta, lógica de buckets, contato só no fim.
- **Livre**: texto das perguntas e tom, adaptados ao mercado.

## Bloco 7 — Contexto de execução
- Roda **sozinha**. Sem MCP, sem pipeline com outras skills. Output usado manualmente depois.

## Bloco 8 — Formato de output
- Blueprint Markdown (template a criar em `references/template-blueprint.md`).
- Idioma: português.

## Síntese confirmada
Skill que monta o quiz de segmentação (bucket survey) do Ask Method canônico: recebe o que o Pedro tiver sobre mercado/oferta, pergunta o que faltar, e entrega blueprint Markdown com perguntas ordenadas (micro-compromisso → progressivo), buckets (3–5, acionáveis) e página de resultado distinta por bucket. Nunca vende dentro do quiz. Coexiste com a quiz-framework-xisto; ambiguidade se resolve perguntando.
