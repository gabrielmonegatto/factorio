# Roadmap — Data lake de criativos

> Escrito 2026-07-21. Objetivo: integridade total do inventário de criativos —
> saber **o que temos**, **o que rodou**, **por quanto tempo**, **quanto custou**,
> **quanto voltou** e **em qual campanha**.

## As 5 perguntas e onde estamos hoje

| Pergunta | Estado | Onde |
|---|---|---|
| Quais criativos rodaram? | 🟠 **parcial — 63 de 2505** (4,2% do gasto) | `meta_ads.r2_key` |
| Por quanto tempo? | 🟢 **já derivável, não exposto** | `meta_insights` (data por ad-dia) |
| Quanta grana? | 🟢 pronto — R$1,73M mapeado | `meta_insights.spend` |
| Qual o resultado? | 🟢 pronto, com ressalva do pixel | `meta_insights.purchases/revenue` |
| Quais campanhas? | 🟢 **já no banco, não exposto** — 297 campanhas, 1180 conjuntos | `meta_ads.campaign_*` |
| O que é de cada produto? | 🔴 **97% sem produto** — só 81 de 2505 classificados | `creatives.product` |
| O que ainda NÃO rodou? | 🔴 **não confiável** enquanto o match for 4% | derivado |

Exemplo do que já sai hoje, para os que casaram:
`BLU-0100-FEED` — rodou 01/01 a 06/05, **115 dias**, R$31.162, 293 compras, ROAS 1,85.

A máquina está pronta. O problema é **cobertura de estoque e classificação**, não capacidade.

---

## F1 — Encher o lago 🔴 desbloqueia todo o resto

Sem isso, qualquer painel em cima disso mente por omissão: mostra 4% do dinheiro
como se fosse o todo.

1. **Vídeos** — 12,4% do gasto, zero no acervo. Achar a pasta no Drive, inventariar
   (contagem + GB) **antes** de baixar, e decidir a janela de upload.
2. **Criativos de 2025** — 59,5% do gasto. Convenção diferente (`ADS 19 - IMG 19`,
   `Ad - 17 - I.A`), não a `748 - Feed`. Provavelmente outra pasta.
3. Rodar `creatives_dhash.py` + `meta_match.py` de novo. Nenhuma linha de código muda.

**DoD:** cobertura do gasto sai de 4,2% e passa de 60%. Medida com a query de
cobertura mês a mês (§0.1 do `handoff_criativos.md`).

## F2 — Fechar a malha de atribuição 🟠

Enquanto o match for baixo, **"não rodou" é indistinguível de "não casou"** — e essa
é a pergunta mais valiosa do inventário (o que produzimos e nunca testamos).

1. Vídeo precisa de match por **frames** (dHash de N frames), não da thumb do Meta.
   Desenhar antes de baixar.
2. Reconciliação manual do resto em `/admin/meta-match` — já no ar, ranqueia
   candidatos por distância perceptual.
3. Marcar explicitamente os **sem-match legítimo** (criativo de terceiro, ad de
   parceiro) para não ficarem contaminando a fila para sempre.

**DoD:** todo ad com gasto relevante ou tem `r2_key` ou tem motivo registrado.

## F3 — Classificação 🔴

1. **Produto** — hoje 97% em branco. Sem isso não existe "o que é de cada produto".
   Deriva do `drive_path` e do nome da campanha; o que sobrar vai para curadoria.
2. **Marca** — o acervo é 100% Bluue. Tonaface e Milagrosa fora.
3. **Ângulo / hook / avatar** — curadoria humana no Teable, colunas já criadas e
   protegidas do sync.

**DoD:** `product` preenchido em >90%; filtro por produto no Teable devolve número
que bate com o gasto da campanha correspondente.

## F4 — Expor o que já existe 🟢 barato

O banco já sabe, o humano não vê:

1. Colunas no Teable: **Campanha**, **Conjunto**, **Dias em veiculação**,
   **Primeira/Última veiculação**, **Já rodou? (sim/não)**.
2. View "Nunca rodou" — o inventário ocioso, que é metade do valor da pergunta.
3. Página narrativa no Outline apontando para as views (o "como se lê").

**DoD:** as 5 perguntas respondidas sem escrever SQL.

## F5 — Automação 🟠

Hoje tudo é manual. Cron diário no trigger.dev:
`meta_pull_insights --days 7` → `meta_pull_ads --from-insights` → `meta_match` →
`sync_criativos`. Reprocessar 7 dias é proposital: o Meta reatribui por ~72h.

**DoD:** roda sozinho por 3 dias, com log e alerta de falha.

## F6 — Receita real (não só pixel) 🟠

O ROAS atual é **atribuição do pixel do Meta** — imperfeita, e ainda por cima
refém do evento custom ofuscado (ver `scripts/meta/README.md`). A receita real
(Flow/B4You) só resolve por **campanha**, via UTM em `data_tracker`.

Caminho: bater total por campanha (pixel × Flow) para medir o desvio, e usar esse
fator como régua de confiança do ROAS por criativo. Não dá para fingir que o pixel
é faturamento.

**DoD:** relatório de desvio pixel × Flow por campanha, atualizado no ciclo diário.

---

## Ordem e dependência

```
F1 (estoque) ──┬──> F2 (match) ──> F3 (classificação) ──> F4 (exposição)
               └──> F5 (automação, independente)
                    F6 (receita real, independente)
```

F1 é o gargalo real. F4 e F5 podem andar em paralelo desde já — F4 porque o dado
já existe, F5 porque independe de cobertura.

## Onde as coisas moram

| Camada | Casa |
|---|---|
| Fatos de máquina (acervo, ads, insights, atribuição) | **D1 `br4nds`** — fonte |
| Arquivos originais | **R2 `br4nds-creatives`** |
| Navegação humana + curadoria | **Teable `br4nds_criativos`** — espelho + dado próprio |
| Narrativa (como se lê, convenções, gotchas) | **Outline** |
| Esteira | **`_factorio/scripts/{meta,teable}/`** |

Atenção: o Teable é espelho **exceto** nas colunas de curadoria — aquilo não existe
em nenhum outro lugar e é o único dado ali que não dá para regenerar.
