# Exemplos certo/errado

Um par por modo de falha. Todos vieram de erros reais.

---

## 1. Número como texto

❌ **Errado**
```json
["drenagem linfática", "74.000", "R$ 2,91"]
```
✅ **Certo**
```json
["drenagem linfática", 74000, 2.91]
```
*Por quê:* string não soma, não ordena e não aceita formato numérico. O separador de
milhar e o "R$" são **formatação** (`numberFormat`), nunca conteúdo da célula.

---

## 2. Formatar antes de escrever

❌ **Errado:** `create_file` → `gsheets_batch_update` (formatação) → `gsheets_update_values`
✅ **Certo:** `create_file` → `gsheets_update_values` → `gsheets_get_metadata` → `gsheets_batch_update`

*Por quê:* formato aplicado em célula vazia se perde quando o valor entra depois. E o
`batch_update` precisa do `sheet_id` real, que só o `get_metadata` (ou o retorno do
`add_sheet`) garante — chutar `0` numa aba nova formata a aba errada.

---

## 3. Dump cru

❌ **Errado:** escrever as 70 linhas e devolver o link.
✅ **Certo:** escrever, formatar (congelar + filtro + R$ + cores), criar a aba Resumo e
devolver o link **com 3-5 leituras do que os dados dizem** ("keywords de bairro deram
volume zero — não vale segmentar por bairro").

*Por quê:* o Pedro pede planilha para **decidir**, não para arquivar. Dados sem
interpretação empurram o trabalho de volta para ele.

---

## 4. Moeda em dólar

❌ **Errado:** coluna "CPC (US$) 0.57" porque a API devolveu em dólar.
✅ **Certo:** converter na cotação do dia e escrever `2.91` com formato `"R$" #,##0.00`,
registrando a taxa usada na aba Resumo.

*Por quê:* o Pedro planeja campanha em reais. Número em dólar obriga ele a converter de
cabeça e abre espaço para erro de decisão de lance.

---

## 5. Uma chamada por ajuste

❌ **Errado:** um `gsheets_batch_update` para congelar, outro para o negrito, outro para a
moeda, outro para as cores.
✅ **Certo:** um único `gsheets_batch_update` com o array de todas as requests.

*Por quê:* cada chamada é um round-trip. A API foi feita para receber o lote inteiro de
uma vez — é para isso que ela se chama *batch*.
