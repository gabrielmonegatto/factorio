# Entrevista — skill `planilha-google-sheets`

Data: 2026-07-14 · Origem: projeto planejador-google-ads (relatório do Studio NGN)

## Bloco 1 — O Job
Criar planilhas no Google Sheets via MCP `gdrive-custom`, sem precisar reaprender a
API do `batchUpdate` a cada uso. Input: dados tabulares (ex.: keywords + volumes).
Output: planilha formatada no Drive + link entregue ao Pedro.
Escopo: **só Google Sheets** (Docs/Slides ficam de fora).
Operações: **criar novas E atualizar existentes** (reprocessar cliente sem perder histórico).

## Bloco 2 — Gatilho
"joga isso num Google Sheets", "monta uma planilha", "quero esse relatório no Sheets",
"põe no Sheets", "cria uma planilha com esses dados".
**NÃO disparar** para subir vídeo/arquivo binário no Drive → isso é a skill `gdrive-entrega`.

## Bloco 3 — Barra de qualidade
Referência de EXCELENTE aprovada pelo Pedro: a planilha do Studio NGN
(https://docs.google.com/spreadsheets/d/1Mq_enDh8drTaUhKq5bRihdIYST_FYv6Gqn4Xm-Tv8GI/edit)
— aba Resumo + aba de dados, cabeçalho congelado, filtro, R$ formatado, cores por relevância.
Ele confirmou: **"esse é o padrão"**.

## Bloco 4 — Modos de falha (observados na prática)
1. Número enviado como string → vira texto, não soma nem formata.
2. Chamar `batch_update` sem pegar o `sheet_id` real antes (aba nova tem id aleatório).
3. Formatar antes de escrever os valores.
4. Entregar dump cru sem formatação — ilegível.
5. Deixar valor em USD quando o Pedro trabalha em BRL.
6. Gastar N chamadas de formatação em vez de um único `batch_update`.

## Bloco 6 — Regras duras (o que é SEMPRE igual)
- Aba "Resumo" (contexto/metodologia/totais) + aba(s) de dados.
- Cabeçalho congelado, em negrito, fundo escuro, com filtro ligado.
- Formato numérico correto: milhar separado, moeda em **R$** (nunca USD, nunca texto).
- Destaque visual por relevância (gradiente/cores condicionais).

## Bloco 7 — Contexto de execução
MCP `gdrive-custom`. Pode rodar sozinha ou no fim de um pipeline (ex.: planejador de keywords).

## Bloco 8 — Output
Planilha no Drive, dentro de **pasta por cliente/projeto**. Entregar o link no fim.
