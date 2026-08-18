// Painel da esteira: onde a mineração está, sem precisar abrir o banco.
// Uso: node scripts/mining/status.mjs [--falhas] [--fracas]
import { d1 } from './lib.mjs';

const args = process.argv.slice(2);

const [tot] = await d1('SELECT COUNT(*) n FROM works');
const [cap] = await d1('SELECT COUNT(*) n, COALESCE(SUM(chars),0) c FROM chapters');
console.log(`\nFILA: ${tot.n} obras · MINERADO: ${cap.n} capítulos, ${(cap.c / 1e6).toFixed(1)}M chars\n`);

const st = await d1('SELECT status, COUNT(*) n FROM works GROUP BY status ORDER BY n DESC');
for (const r of st) console.log(`  ${r.status.padEnd(10)} ${String(r.n).padStart(4)}`);

console.log('\npor fonte:');
const f = await d1(`SELECT COALESCE(source_kind,'(não resolvida)') k, COUNT(*) n,
  SUM(CASE WHEN status='mined' THEN 1 ELSE 0 END) m FROM works GROUP BY k ORDER BY n DESC`);
for (const r of f) console.log(`  ${r.k.padEnd(16)} ${String(r.n).padStart(4)} obras · ${r.m} mineradas`);

console.log('\npor era (mineradas / total):');
const e = await d1(`SELECT COALESCE(era,'?') era, COUNT(*) n, SUM(CASE WHEN status='mined' THEN 1 ELSE 0 END) m
  FROM works GROUP BY era ORDER BY era`);
for (const r of e) console.log(`  ${r.era.padEnd(26)} ${String(r.m).padStart(3)}/${String(r.n).padEnd(4)}`);

const [top] = await d1(`SELECT COUNT(*) n FROM works WHERE launch=1 AND status='mined'`);
const [tl] = await d1('SELECT COUNT(*) n FROM works WHERE launch=1');
console.log(`\ncatálogo de estreia: ${top.n}/${tl.n} mineradas`);

if (args.includes('--falhas')) {
  console.log('\nFALHAS:');
  for (const r of await d1(`SELECT title, source_kind, substr(last_error,1,80) e FROM works WHERE status IN ('failed','blocked') ORDER BY title`))
    console.log(`  ${(r.title || '').slice(0, 40).padEnd(42)} ${(r.source_kind || '?').padEnd(11)} ${r.e || ''}`);
}
if (args.includes('--fracas')) {
  console.log('\nCASAMENTOS FRACOS (precisam de olho humano):');
  for (const r of await d1(`SELECT title, round(resolve_score,2) s, substr(resolve_note,1,70) n FROM works
    WHERE resolve_score IS NOT NULL AND resolve_score < 0.7 ORDER BY resolve_score DESC`))
    console.log(`  ${String(r.s).padEnd(5)} ${(r.title || '').slice(0, 40).padEnd(42)} ${r.n || ''}`);
}
if (!args.includes('--falhas') && !args.includes('--fracas'))
  console.log('\n(--falhas e --fracas mostram o que precisa de decisão)\n');
