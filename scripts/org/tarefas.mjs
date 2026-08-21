#!/usr/bin/env node
// A gestão do Mananciall pela linha de comando: mesmas tabelas que o Gabriel vê
// em bi.mananciall.org (tarefas/projetos no D1 mananciall-db). Toda sessão de
// fábrica usa ISTO, não o Notion (decisão de 20/08/2026).
//
//   node scripts/org/tarefas.mjs                     → resumo por área
//   node scripts/org/tarefas.mjs "Content"           → tarefas + projetos da área
//   node scripts/org/tarefas.mjs --nova "titulo" --area "Content" [--notas "..."] [--gate]
//   node scripts/org/tarefas.mjs --status <id> Fazendo|Feita|Travada|Fazer
//
// Mudanças feitas por aqui também são auditadas? NÃO: bi_edicoes registra só o
// que passa pelo painel. Sessão que muda status relevante avisa no report.

import fs from 'node:fs';

const ENV_PATH = process.env.FABRICA_ENV || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const g = (k) => (env.find((l) => l.startsWith(k + '=')) || '').slice(k.length + 1).trim();
const PROD = 'ddae6874-2058-4aa1-927e-0e7887e2cba6';

async function d1(sql, params = []) {
  const r = await fetch(`https://api.cloudflare.com/client/v4/accounts/${g('CLOUDFLARE_ACCOUNT_ID')}/d1/database/${PROD}/query`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${g('CLOUDFLARE_API_TOKEN')}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, params }),
  });
  const j = await r.json().catch(() => ({}));
  if (!j.success) throw new Error((j.errors || []).map((e) => e.message).join('; '));
  return j.result[0].results;
}

const AREAS = ['Organização', 'Inteligência de Mercado', 'Inteligência do Negócio', 'Mineração', 'Content', 'Productz', 'i18n', 'Growth'];
const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); return i > -1 ? argv[i + 1] : null; };

if (argv.includes('--nova')) {
  const titulo = flag('--nova');
  const area = flag('--area');
  if (!titulo || !AREAS.includes(area)) { console.error(`uso: --nova "titulo" --area "${AREAS.join('|')}"`); process.exit(1); }
  const id = `cli-${crypto.randomUUID()}`;
  await d1(
    `INSERT INTO tarefas (id, tarefa, area, status, responsavel, gate, notas) VALUES (?,?,?,?,?,?,?)`,
    [id, titulo, area, 'Fazer', argv.includes('--gate') ? 'Gabriel' : 'Claude', argv.includes('--gate') ? 1 : 0, flag('--notas')]
  );
  console.log(`✓ criada [${id}] ${titulo}`);
  process.exit(0);
}

if (argv.includes('--status')) {
  const i = argv.indexOf('--status');
  const [id, status] = [argv[i + 1], argv[i + 2]];
  if (!id || !['Backlog', 'Fazer', 'Fazendo', 'Feita', 'Travada'].includes(status)) {
    console.error('uso: --status <id> Backlog|Fazer|Fazendo|Feita|Travada'); process.exit(1);
  }
  await d1(`UPDATE tarefas SET status = ?, atualizado_em = datetime('now') WHERE id = ?`, [status, id]);
  console.log(`✓ ${id} → ${status}`);
  process.exit(0);
}

const alvo = argv[0] ? AREAS.find((a) => a.toLowerCase().includes(argv[0].toLowerCase())) : null;

if (!alvo) {
  console.log('Gestão do Mananciall (bi.mananciall.org · D1 mananciall-db)\n');
  const r = await d1(`SELECT area, SUM(status NOT IN ('Feita')) abertas, SUM(gate = 1 AND status NOT IN ('Feita')) gates FROM tarefas GROUP BY area ORDER BY abertas DESC`);
  for (const l of r) console.log(`  ${String(l.area || '(sem área)').padEnd(26)} ${String(l.abertas).padStart(3)} abertas${l.gates > 0 ? `  (${l.gates} no gate do Gabriel)` : ''}`);
  console.log('\nuso: tarefas.mjs "Área" · --nova · --status (cabeçalho do arquivo)');
  process.exit(0);
}

console.log(`\n═══ ${alvo} ═══`);
const projetos = await d1(`SELECT id, entrega, fase, status, gate, detalhe FROM projetos WHERE area = ? ORDER BY fase, status`, [alvo]);
console.log(`\n── PROJETOS (${projetos.length}) ──`);
for (const p of projetos) {
  const marca = p.status === 'Entregue' ? '✅' : p.status === 'Aguardando gate' ? '🚦' : p.status === 'Em construção' ? '🔨' : '⬜';
  console.log(` ${marca} [${p.fase}] ${p.entrega}`);
  if (p.detalhe && p.status !== 'Entregue') console.log(`      ${p.detalhe.slice(0, 130)}`);
}
const tarefas = await d1(`SELECT id, tarefa, status, gate, responsavel, notas FROM tarefas WHERE area = ? AND status != 'Feita' ORDER BY gate DESC, atualizado_em DESC`, [alvo]);
console.log(`\n── TAREFAS ABERTAS (${tarefas.length}) ──`);
for (const t of tarefas) {
  console.log(` ${t.gate ? '🚦 GABRIEL' : '🤖'} [${t.status}] ${t.tarefa}   {${t.id.slice(0, 13)}…}`);
  if (t.notas) console.log(`      ${t.notas.slice(0, 130)}`);
}
console.log();
