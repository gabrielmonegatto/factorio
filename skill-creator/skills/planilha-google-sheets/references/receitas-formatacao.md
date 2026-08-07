# Receitas de formatação — `gsheets_batch_update`

Todas as requests seguem o formato da API `spreadsheets.batchUpdate` do Sheets.
Monte um array com as que precisar e mande **numa única chamada**.

> `sheetId` vem de `gsheets_get_metadata` (ou do retorno de `gsheets_add_sheet`).
> Índices são **0-based** e o fim é **exclusivo**: `startRowIndex: 0, endRowIndex: 1` = só a linha 1.

---

## Renomear aba + congelar cabeçalho (e 1ª coluna)

```json
{"updateSheetProperties": {
  "properties": {"sheetId": 0, "title": "Palavras-chave",
    "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}},
  "fields": "title,gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}}
```

## Cabeçalho: fundo escuro, negrito, texto branco, centralizado

```json
{"repeatCell": {
  "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
  "cell": {"userEnteredFormat": {
    "backgroundColor": {"red": 0.16, "green": 0.24, "blue": 0.35},
    "textFormat": {"bold": true, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 10},
    "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP", "horizontalAlignment": "CENTER"}},
  "fields": "userEnteredFormat"}}
```

## Número com separador de milhar (colunas C-E, linhas 2-73)

```json
{"repeatCell": {
  "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 73, "startColumnIndex": 2, "endColumnIndex": 5},
  "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"},
                                  "horizontalAlignment": "RIGHT"}},
  "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment"}}
```

## Moeda em Reais

```json
{"repeatCell": {
  "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 73, "startColumnIndex": 7, "endColumnIndex": 10},
  "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "\"R$\" #,##0.00"},
                                  "horizontalAlignment": "RIGHT"}},
  "fields": "userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment"}}
```

## Linha de TOTAL destacada

```json
{"repeatCell": {
  "range": {"sheetId": 0, "startRowIndex": 73, "endRowIndex": 74},
  "cell": {"userEnteredFormat": {
    "backgroundColor": {"red": 0.91, "green": 0.94, "blue": 0.98},
    "textFormat": {"bold": true},
    "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
  "fields": "userEnteredFormat"}}
```

## Gradiente na coluna que importa (quanto maior, mais verde)

```json
{"addConditionalFormatRule": {"rule": {
  "ranges": [{"sheetId": 0, "startRowIndex": 1, "endRowIndex": 73, "startColumnIndex": 4, "endColumnIndex": 5}],
  "gradientRule": {
    "minpoint": {"color": {"red": 1, "green": 1, "blue": 1}, "type": "MIN"},
    "maxpoint": {"color": {"red": 0.29, "green": 0.68, "blue": 0.44}, "type": "MAX"}}},
  "index": 0}}
```

## Cor por valor de texto (ex.: concorrência Alta = vermelho, Baixa = verde)

```json
{"addConditionalFormatRule": {"rule": {
  "ranges": [{"sheetId": 0, "startRowIndex": 1, "endRowIndex": 73, "startColumnIndex": 5, "endColumnIndex": 6}],
  "booleanRule": {
    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Alta"}]},
    "format": {"backgroundColor": {"red": 0.99, "green": 0.87, "blue": 0.86},
               "textFormat": {"foregroundColor": {"red": 0.7, "green": 0.11, "blue": 0.11}}}}},
  "index": 0}}
```

## Largura de coluna

```json
{"updateDimensionProperties": {
  "range": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
  "properties": {"pixelSize": 260}, "fields": "pixelSize"}}
```

## Filtro automático no cabeçalho

```json
{"setBasicFilter": {"filter": {
  "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 73, "startColumnIndex": 0, "endColumnIndex": 10}}}}
```

> No filtro, o `endRowIndex` deve parar **antes** da linha de TOTAL — senão o total
> entra na ordenação e sobe/desce junto com os dados.

---

## Armadilhas (todas já custaram tempo)

| Sintoma | Causa | Correção |
|---|---|---|
| Números não somam / ficam à esquerda | valor enviado como string `"1.234"` | mande número JSON `1234` |
| Formatação não aparece | formatou antes de escrever os valores | escreva primeiro, formate depois |
| Erro de range / formata a aba errada | `sheetId` chutado | `gsheets_get_metadata` antes |
| Fórmula/data vira texto | `value_input_option: RAW` | use `USER_ENTERED` |
| Total sobe junto ao ordenar | filtro incluiu a linha de total | limite o `endRowIndex` do filtro |
| Só a 1ª aba é escrita | range sem nome da aba | use `Resumo!A1:B20` |
