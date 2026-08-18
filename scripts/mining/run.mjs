// A esteira inteira numa chamada: fila -> resolve -> minera -> painel.
// É este o comando do dia a dia. Cada etapa é idempotente, então repetir é seguro.
//
// Uso: node scripts/mining/run.mjs [--limite N]   (N = quantas obras minerar nesta rodada)
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const aqui = import.meta.dirname;
const limite = process.argv[process.argv.indexOf('--limite') + 1] || '15';

const etapas = [
  ['fila (Notion -> D1)', 'queue.mjs', []],
  ['resolve (descobrir URL)', 'resolve.mjs', ['--limite', '200']],
  ['minerar', 'mine.mjs', ['--limite', limite]],
  ['painel', 'status.mjs', []],
];

for (const [rotulo, script, args] of etapas) {
  console.log(`\n${'='.repeat(60)}\n▶ ${rotulo}\n${'='.repeat(60)}`);
  const r = spawnSync(process.execPath, [path.join(aqui, script), ...args], { stdio: 'inherit' });
  if (r.status !== 0) { console.error(`\n✗ etapa "${rotulo}" falhou; parando aqui`); process.exit(r.status || 1); }
}
