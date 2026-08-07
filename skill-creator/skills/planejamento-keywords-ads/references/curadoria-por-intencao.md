# Curadoria por intenção

A API devolve **milhares** de ideias (8.615 no Studio NGN, 5.214 no Festejou). A maioria não
serve para anunciar. Curar é o passo que transforma dado em plano — é onde está o seu valor.

## A pergunta que decide tudo

> **Quem digita isso no Google quer CONTRATAR/ALUGAR o que o cliente vende — ou quer outra coisa?**

Se quer outra coisa, corte. Não importa o volume de busca.

## Os dois eixos de intenção (identifique qual é o do cliente)

### Eixo 1 — Serviço vs. Produto (clínicas, salões, prestadores)
O cliente **presta um serviço**. A API traz junto quem quer **comprar produto**.

| Corte | Mantenha |
|---|---|
| `cerave gel de limpeza`, `óleo de banho nívea` | `limpeza de pele` |
| `hidratante facial` (produto) | `hidratação facial` (procedimento) |
| Marcas: nivea, cerave, la roche, vichy, principia, neutrogena, garnier, eucerin, adcos… | |
| Termos de produto: gel, sabonete, creme, sérum, óleo, protetor solar, ácido, hidratante… | |

### Eixo 2 — Aluguel vs. Compra (locadoras, aluguel de equipamento)
O cliente **aluga**. A API traz junto quem quer **comprar**.

| Corte | Mantenha |
|---|---|
| `tenda 3x3`, `tenda de praia` (quem quer comprar) | `aluguel de tendas`, `alugar tenda` |
| `comprar pula pula`, `pula pula preço de fábrica` | `aluguel de pula pula` |

> Genéricas (`pula pula`, `banheiro químico`) são **ambíguas**: têm volume enorme e CPC baixo,
> mas metade da intenção é compra. Mantenha, marque como "Genérica (produto)" e avise o Pedro
> para deixar "ALUGUEL" explícito no anúncio, filtrando quem quer comprar.

## Corte sempre (qualquer nicho)

- **Informacional**: `o que é`, `para que serve`, `benefícios`, `antes e depois`, `como usar`.
- **DIY / caseiro**: `caseiro`, `receita`, `em casa`, `como fazer`. Quem faz sozinho não contrata.
- **Educação**: `curso`, `apostila`, `faculdade`, `formação`, `pdf`.

## NÃO deduplique variantes (regra do Pedro, 2026-07-14)

Pode parecer que `aluguel de mesa e cadeira` e `alugar mesa e cadeira` são a mesma coisa. **Não são.**
No Google Ads viram **grupos de anúncio diferentes**, com correspondência, lance e anúncio próprios.
Quem digita "alugar" e quem digita "aluguel de" são buscas distintas — e o Pedro precisa das duas.

❌ **Errado:** agrupar por `(volume, cpc, concorrência)` e manter só uma variante.
Isso destrói a lista de dois jeitos: (a) descarta variações legítimas que viram grupos próprios;
(b) duas keywords **sem nenhuma relação** podem ter métricas idênticas por coincidência
(volumes vêm arredondados: 10, 20, 50…) — e uma delas é jogada fora sem motivo.

✅ **Certo:** manter **todas** as variações. Uma keyword por linha.

> Efeito real no Festejou: com dedup, 2.557 keywords. Sem dedup, **6.065**. A dedup estava
> escondendo mais da metade do mercado.

Se a lista ficar grande, **não corte por dedup** — corte por volume (remova as com volume zero
nos três níveis geográficos, que são inúteis para anunciar).

## Enriquecimento (o que a API não sugere e o Pedro precisa)

Some à lista, mesmo que a expansão não tenha trazido:
- `<serviço> <cidade>` e `<serviço> <sigla do estado>` — alta intenção local.
- `<serviço> perto de mim` — a mais quente do funil local.
- `<serviço> preço`, `quanto custa <serviço>` — fundo de funil.
- `<serviço> <contexto>` (ex.: `aluguel de mesas para casamento`).

## Categorize a lista final (vira coluna na planilha)

`Serviço/Aluguel (intenção certa)` · `Genérica (produto)` · `Local (Cidade/UF)` ·
`Perto de mim` · `Preço (fundo de funil)` · `Evento/Contexto`

Alvo: **60-80 keywords** no relatório final. Menos que isso é raso; mais vira ruído.
