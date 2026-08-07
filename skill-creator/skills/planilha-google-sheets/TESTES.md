# Testes — `planilha-google-sheets`

## Teste de gatilho

| Frase | Deve disparar? |
|---|---|
| "joga isso num Google Sheets" | ✅ sim |
| "monta uma planilha com esses dados" | ✅ sim |
| "quero esse relatório no Sheets" | ✅ sim |
| "sobe esse corte pro Drive" | ❌ não → `gdrive-entrega` |
| "lê essa planilha e me diz o total" | ❌ não → só usar o MCP direto (leitura) |
| "faz um documento no Google Docs" | ❌ não → fora do escopo |

## Caso 1 — Criar do zero (caso real: Festejou)

**Input:** planejamento de keywords do festejou.com.br (keywords + volume Brasil/Estado/Cidade + CPC).
**Esperado:**
- [ ] Pasta do cliente criada/encontrada no Drive; planilha dentro dela.
- [ ] Aba "Resumo" em index 0, com cliente, site, data, fonte, taxa USD→BRL e totais.
- [ ] Aba de dados: cabeçalho congelado, negrito, fundo escuro, filtro ligado.
- [ ] Volumes como número (somam) com separador de milhar; CPC em `R$ 0,00`.
- [ ] Gradiente na coluna de volume da cidade; cor por concorrência.
- [ ] Linha de TOTAL destacada e FORA do range do filtro.
- [ ] Resposta traz o link + 3-5 leituras dos dados.
- [ ] Formatação feita em **uma** chamada de `gsheets_batch_update`.

## Caso 2 — Atualizar existente

**Input:** "roda o Studio NGN de novo e atualiza a planilha dele".
**Esperado:**
- [ ] Acha a planilha por `search_files` (não cria uma nova).
- [ ] Cria aba nova `Dados AAAA-MM-DD` em vez de sobrescrever a antiga.
- [ ] Atualiza data e totais na aba Resumo.

## Caso 3 — Anti-dump

**Input:** "põe essas 200 linhas num Sheets" (dados sem contexto).
**Esperado:**
- [ ] NÃO entrega dump cru: mesmo sem pedido explícito, formata e cria a aba Resumo.
- [ ] Se faltar contexto para o Resumo (cliente/fonte), pergunta antes de criar.

---

## Resultado do Caso 1 — Festejou (executado em 2026-07-14)

Planilha: https://docs.google.com/spreadsheets/d/1ZskjxZ9raDgm4GI_KSbWXDE21G36yGmE3iVHCL2Emjo/edit

- [x] Pasta do cliente (`Planejamento de Keywords — Google Ads/Festejou`) criada; planilha dentro.
- [x] Aba "Resumo" em index 0, com cliente, site, data, fonte, taxa USD→BRL, totais e curadoria.
- [x] Cabeçalho congelado, negrito, fundo escuro, filtro ligado.
- [x] Volumes como número com milhar; CPC em `R$ 0,00`.
- [x] Gradiente na coluna Cidade + cor por concorrência + destaque na categoria "Aluguel".
- [x] TOTAL destacado e fora do range do filtro (`endRowIndex: 67`).
- [x] Formatação em UMA chamada de `gsheets_batch_update` (19 requests).
- [x] Entrega com link + leituras dos dados.

**Aprendizado incorporado:** `search_files` por nome de cliente pode devolver muitas pastas
homônimas de outros contextos (Instagram, vídeos). Não jogar a planilha em qualquer pasta que
"bate" o nome — usar a raiz dedicada `Planejamento de Keywords — Google Ads/<Cliente>/`.
