// Converte o backup NDJSON de volta em SQL de restauração.
//
// Backup que ninguém sabe restaurar não é backup, é sensação de segurança.
// Este script existe pra que o caminho de volta seja um comando, não uma tarde
// de improviso no dia em que o banco já está perdido.
//
// USO
//   1. baixar o backup do R2 (uma pasta por dia):
//      npx wrangler r2 object get {{PROJECT}}-backups/d1/{{PROJECT}}/2026-07-31/manifest.json --remote --file manifest.json
//      (repetir pros .ndjson listados no manifest, ou usar `rclone` no bucket)
//   2. gerar o SQL:
//      node restore.mjs ./backup-2026-07-31 > restore.sql
//   3. conferir o SQL e SÓ ENTÃO aplicar:
//      npx wrangler d1 execute {{D1_NAME}} --remote --file restore.sql
//
// O SQL gerado usa INSERT OR REPLACE: rodar duas vezes não duplica.
// NÃO apaga nada — restaurar por cima de um banco com dado novo é decisão humana,
// não efeito colateral de script.

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2];
if (!dir) {
  console.error('uso: node restore.mjs <pasta-do-backup> > restore.sql');
  process.exit(1);
}

function sqlValue(v) {
  if (v === null || v === undefined) return 'NULL';
  if (typeof v === 'number') return Number.isFinite(v) ? String(v) : 'NULL';
  if (typeof v === 'boolean') return v ? '1' : '0';
  return `'${String(v).replace(/'/g, "''")}'`;
}

const tables = readdirSync(dir).filter((n) => statSync(join(dir, n)).isDirectory());
if (!tables.length) {
  console.error(`nenhuma pasta de tabela em ${dir} — o backup baixou completo?`);
  process.exit(1);
}

let total = 0;

for (const table of tables) {
  const files = readdirSync(join(dir, table)).filter((f) => f.endsWith('.ndjson')).sort();

  for (const file of files) {
    const lines = readFileSync(join(dir, table, file), 'utf8').split('\n').filter(Boolean);

    for (const line of lines) {
      const row = JSON.parse(line);
      const cols = Object.keys(row);
      if (!cols.length) continue;
      const colList = cols.map((c) => `"${c}"`).join(', ');
      const valList = cols.map((c) => sqlValue(row[c])).join(', ');
      console.log(`INSERT OR REPLACE INTO "${table}" (${colList}) VALUES (${valList});`);
      total += 1;
    }
  }
  console.error(`${table}: ${files.length} arquivo(s)`);
}

console.error(`total: ${total} linhas`);
