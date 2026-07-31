// utils/universalCron.ts — APOSENTADO em 31/07/2026. Substituído por `trigger/esteiras.ts`.
//
// POR QUE MORREU (autópsia, pra não repetir):
//   1. Rodava Python via execFile (`auto_cure_tasks.py`, `reconcile_factory.py`,
//      `get_pending_tasks.py`). O container do Trigger.dev é Node puro → `spawn python ENOENT`.
//      Funcionava em `trigger dev` (roda na máquina do Gabriel, que tem Python) e morreu
//      no deploy pra nuvem.
//   2. Falava SQL bruto com `postgresql://...@localhost:42345`. A nuvem nunca alcança a VPS.
//      Além disso, DDL por SQL dentro dos schemas `bse*` corrompe a metadata do Teable —
//      foi o que gerou os fantasmas `mcp` e `content_chunks` e as colunas invisíveis.
//   3. Capturava o erro e o devolvia como VALOR (`return { processed: 0, error }`), então o
//      status ficava `completed`. Rodou ~2.300 vezes em 24 dias sem produzir nada e sem
//      NUNCA disparar alerta.
//
// O substituto (`esteiras.ts`) é TS puro + REST, e FALHA ALTO (throw) de propósito.
//
// A lógica de negócio boa foi preservada:
//   • nomenclatura canônica `brand/area/project/task` (validateTaskNames.ts)
//   • auto-cura de tasks presas >20min em "Em Processamento" e re-tentativa de "Erro"
//   • uma fila por esteira, com concorrência própria
//
// Este arquivo fica só como registro. NÃO reintroduzir `schedules.task` aqui.
export {};
