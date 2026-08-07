---
name: planilha-google-sheets
description: Cria e atualiza planilhas no Google Sheets usando o MCP gdrive-custom, já formatadas no padrão do Pedro (aba Resumo + aba de dados, cabeçalho congelado com filtro, números e R$ formatados, cores por relevância) e salvas em pasta do cliente. Documenta exatamente quais tools chamar e com quais parâmetros, sem precisar explorar o MCP. TRIGGER quando o usuário pedir "joga isso num Google Sheets", "monta uma planilha", "quero esse relatório no Sheets", "põe no Sheets", "cria uma planilha com esses dados", ou quando um pipeline precisar entregar dados tabulares. NÃO usar para subir vídeo/arquivo binário no Drive (é a skill gdrive-entrega) nem para Docs/Slides.
---

# Planilha Google Sheets

Entregável = planilha formatada no Drive, na pasta do cliente, com o link devolvido ao Pedro.
Nunca entregue um dump cru de dados: dado sem formatação é dado ilegível.

## Regras duras (checklist — toda planilha, sempre)

1. **Aba "Resumo" primeiro** (index 0): cliente, fonte dos dados, data, metodologia, totais.
   Depois a(s) aba(s) de dados.
2. **Cabeçalho congelado** (`frozenRowCount: 1`), negrito, fundo escuro, texto branco + **filtro ligado**.
3. **Números são números.** Envie `1234` (número JSON), nunca `"1.234"` (string). Moeda sempre
   em **R$** — se a fonte vier em USD, converta ANTES de escrever (cotação: `economia.awesomeapi.com.br/last/USD-BRL`).
4. **Destaque visual por relevância**: gradiente na coluna que importa e/ou cores condicionais.
5. **Uma única chamada `gsheets_batch_update`** com todas as requests de formatação. Não gaste
   uma chamada por ajuste.
6. **Pasta do cliente**: procure/crie a pasta antes e passe o `parent_id` no `create_file`.

## Workflow

1. **Pasta**: a raiz é sempre `Planejamento de Keywords — Google Ads/<Cliente>/`.
   `search_files` por essa raiz → se não existir, `create_folder`; depois a subpasta do cliente.
   **Nunca** jogue a planilha numa pasta só porque o nome do cliente bateu no `search_files` —
   o Drive do Pedro tem várias pastas homônimas de outros contextos (Instagram, vídeos, campanhas).
2. **Criar**: `create_file` com `mime_type: application/vnd.google-apps.spreadsheet`,
   `content: ""` e `parent_id` da pasta. Guarde o `id` da planilha.
3. **Escrever os dados** com `gsheets_update_values` (`value_input_option: USER_ENTERED`).
   Escreva SEMPRE antes de formatar — formatação em célula vazia se perde.
4. **Aba Resumo**: `gsheets_add_sheet` com `index: 0`. Ela devolve o `sheet_id` novo — guarde.
   Preencha com `gsheets_update_values` usando range com nome da aba (`Resumo!A1:B20`).
5. **Pegar os ids**: `gsheets_get_metadata` → confirma o `sheet_id` de cada aba.
   **Nunca chute o sheet_id.** A aba original é `0` e se chama `Sheet1` (renomeie); abas novas
   têm id aleatório (ex.: `1052237401`).
6. **Formatar**: UM `gsheets_batch_update` com todas as requests. Receitas prontas (copie e adapte)
   em `references/receitas-formatacao.md`.
7. **Entregar**: devolva o link (`https://docs.google.com/spreadsheets/d/<id>/edit`) + 3-5 leituras
   do que os dados dizem. Planilha entregue sem interpretação é trabalho pela metade.

## Atualizar planilha existente

Para reprocessar um cliente sem perder o histórico:
- Ache a planilha com `search_files` → pegue o `spreadsheet_id`.
- `gsheets_get_metadata` para ver as abas existentes.
- Crie uma aba nova datada (`gsheets_add_sheet`, título `Dados AAAA-MM-DD`) em vez de sobrescrever.
- Atualize os totais/data na aba Resumo com `gsheets_update_values`.

## Tools do gdrive-custom (as que importam)

| Tool | Para quê |
|---|---|
| `create_file` | criar a planilha (mime nativo + content vazio) |
| `create_folder` / `search_files` | pasta do cliente |
| `gsheets_update_values` | escrever valores (use `USER_ENTERED`) |
| `gsheets_add_sheet` | nova aba (devolve o `sheet_id`) |
| `gsheets_get_metadata` | **obrigatório** antes de formatar: dá os `sheet_id` |
| `gsheets_batch_update` | toda a formatação, numa chamada só |
| `share_file` | só se o Pedro pedir link compartilhável |

**Nunca** use `upload_binary_file` para planilha — ele manda base64 no payload e estoura.

## Muitas linhas (> ~500): use o script, não o MCP

O `gsheets_update_values` recebe as linhas DENTRO do payload da tool — com milhares de linhas
isso estoura o contexto do agente antes de terminar. Para volumes grandes, use:

```bash
uv run --directory /Volumes/KINGSTON/claude/tools/mcps python \
  <skill>/scripts/sheets_bulk.py <spreadsheet_id> "<Nome da aba>" <linhas.json> [--index N]
```

Ele reusa o mesmo token OAuth do MCP gdrive, cria a aba (ou limpa e reescreve), manda tudo numa
chamada da API e já congela o cabeçalho + liga o filtro. Depois é só formatar via
`gsheets_batch_update` (formatação tem payload pequeno — essa parte continua no MCP).

Já entregou 8.615 linhas numa aba sem engasgar.

## Graus de liberdade

- **Regra dura** (nunca mude): o checklist acima, os formatos numéricos, a aba Resumo.
- **Critério seu** (julgue caso a caso): quais colunas entram, como agrupar/ordenar as linhas,
  quais cores usam gradiente vs. condicional, o que destacar no Resumo.

Antes de escrever, leia `references/exemplos.md` (pares certo/errado) se for a primeira planilha da sessão.
