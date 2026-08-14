# Padrões de Tráfego Bluue — hora, dia e região

> Gerado 14/08/2026 · base 01/01–14/08 (226 dias, 6 contas Meta) · scripts em
> `scripts/meta/` (`meta_pull_breakdowns.py` + `report_patterns.py`) · relatório
> visual: artifact "Padrões de Tráfego Bluue"

## Números do período

| | Valor |
|---|---|
| Investido (BRL normalizado, USD a 5,40) | R$ 2,33M |
| Receita (pixel) | R$ 3,79M · ROAS 1,62 |
| Ritmo atual (últimos 28d) | R$ 306k/mês · ROAS **1,85** |

## Os 3 achados (validados nas duas fontes: pixel + checkout)

1. **Madrugada queima.** 2h–6h: R$ 190.675 investidos a ROAS 0,86 (0,72× a média
   do dia). Só 4% das compras reais acontecem nessa janela.
2. **13h–17h é o motor.** ROAS 1,46 no bloco (pico 14h: 1,61 = 1,22× a média),
   mas a verba concentra nas 7h–12h (R$ 792k a 1,17). Dinheiro no horário errado.
3. **Fim de semana rende 11% menos.** Sáb+dom ROAS 1,49 vs 1,67 úteis, verba
   quase igual. Compras reais caem junto (~75/dia vs 85-89).

Bônus: pico **real** de compra é 21h, alimentado por cliques da tarde. Dayparting
mira a hora do clique, não a da compra.

## A conta: quanto dá pra ganhar só realocando

Método: multiplicador relativo de cada janela (medido em 7 meses) aplicado ao
ROAS atual de 1,85, movendo verba da janela fraca pra forte. Faixa conservadora
assume que o real realocado rende só a média; otimista assume que rende como o
bloco da tarde. **Mesmo gasto total, zero real a mais.**

| Alavanca | Verba movida/mês | Ganho conservador | Ganho otimista |
|---|---|---|---|
| H1 · cortar 80% da madrugada → tarde | R$ 20k | +R$ 10k | +R$ 19k |
| H2 · deslocar 15% da manhã → tarde | R$ 16k | +R$ 1k | +R$ 7k |
| H3 · −25% fim de semana → úteis | R$ 21k | +R$ 4k | +R$ 6k |
| **Total** | **R$ 57k realocados** | **+R$ 15k/mês** | **+R$ 32k/mês** |

**Resultado projetado: ROAS 1,85 → 1,90 a 1,96** · **+R$ 180k a 380k/ano** de
receita com o mesmo orçamento.

Ressalvas da projeção: (a) assume que o padrão de 7 meses se mantém; (b) ROAS
marginal de verba adicional tende a ser menor que o observado (por isso a faixa);
(c) no ritmo atual a madrugada provavelmente roda ~1,3, acima de 1,0 mas ainda a
pior janela — cortar continua certo porque o real tem casa melhor. **A projeção
não é promessa: é o tamanho do prêmio que justifica rodar os testes.**

## Hipóteses (loop do cookbook)

`padrão (28d) → repete em 2 janelas? → hipótese → teste com controle → 7-14d → decisão`

| # | Hipótese | Teste |
|---|---|---|
| H1 | Cortar madrugada não derruba o dia | Regra automatizada −80% budget 1h30–6h em 1 campanha; espelho sem regra; 14d |
| H2 | A tarde aguenta mais verba | Regra +budget ao meio-dia, devolve às 18h (máx +20%/dia p/ não resetar aprendizado) |
| H3 | Fds pede outra dose | Sexta à noite −25%; segunda restaura. Alternativa: criativo/oferta de fds |
| H4 | Vale das 20h é leilão caro, não desinteresse | Comparar CPM por hora; compras reais às 20-21h são altas |
| H5 | Há estado queimando verba escondido | Geolocalizar first-party por IP e cruzar com gasto regional antes de qualquer split |

## Gotchas de dado (pra não repetir dor)

- **`paid_date` da Flow é lote noturno** (~4h40 UTC): usar `transaction_date`,
  senão nasce falso pico de compra à 1h.
- **Região não devolve conversão custom** na API → ROAS regional via Meta
  impossível pro pixel da Bluue. Caminho: IP do first-party.
- **Fusos mistos**: LF1/LF10 em São Paulo; CA1/CA2/Tonaface em Los Angeles
  (+4h após 08/03, +5h antes). **Moedas mistas**: USD convertido a 5,40.
- **Quebra horária captura ~78% das conversões** do diário: padrão relativo vale,
  nível absoluto não.
