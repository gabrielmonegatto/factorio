#!/usr/bin/env node
// PLAYBOOKS v2 — playbook vira linha-RAIZ da hierarquia:
// Playbook (raiz) → Etapas macro → Tarefas. + campo Nível + renomeia categoria.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const DB_PB = '3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2';
const NOME_NOVO = 'Perpétuo Lucrativo';
const NOME_VELHO = 'Implementação Funil Perpétuo';

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, body, method = 'POST') {
  for (let t = 1; ; t++) {
    await sleep(360);
    try {
      const res = await fetch(`https://api.notion.com/v1/${path}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const json = await res.json();
      if (!res.ok) { console.error(`✗ ${method} ${path}:`, JSON.stringify(json).slice(0, 300)); throw new Error(json.message); }
      return json;
    } catch (e) {
      if (t >= 4 || e.message !== 'fetch failed') throw e;
      await sleep(t * 3000);
    }
  }
}
const txt = c => [{ type: 'text', text: { content: c } }];
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const sel = n => ({ select: { name: n } });

// ═══ 1. schema: renomear opção do select + adicionar Nível ═══
console.log('▸ 1/4 schema (renomear categoria + campo Nível)...');
const db = await api(`databases/${DB_PB}`, null, 'GET');
const opt = db.properties['Playbook'].select.options.find(o => o.name === NOME_VELHO);
if (opt) {
  await api(`databases/${DB_PB}`, { properties: {
    'Playbook': { select: { options: db.properties['Playbook'].select.options.map(o =>
      o.id === opt.id ? { id: o.id, name: NOME_NOVO, color: o.color } : { id: o.id, name: o.name, color: o.color }) } },
  }}, 'PATCH');
  console.log(`  ✓ categoria: "${NOME_VELHO}" → "${NOME_NOVO}"`);
} else console.log('  (categoria já renomeada)');
await api(`databases/${DB_PB}`, { properties: {
  'Nível': { select: { options: [
    { name: 'Playbook', color: 'blue' },
    { name: 'Etapa', color: 'purple' },
    { name: 'Tarefa', color: 'gray' },
  ]}},
}}, 'PATCH');
console.log('  ✓ campo Nível');

// ═══ 2. ler linhas ═══
console.log('▸ 2/4 lendo etapas...');
let all = [], cursor;
do {
  const j = await api(`databases/${DB_PB}/query`, { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
  all.push(...j.results);
  cursor = j.has_more ? j.next_cursor : null;
} while (cursor);
const raizes = all.filter(r => !(r.properties['Etapa principal']?.relation || []).length);
const filhas = all.filter(r => (r.properties['Etapa principal']?.relation || []).length);
console.log(`  ${all.length} linhas: ${raizes.length} etapas macro, ${filhas.length} tarefas`);

// ═══ 3. criar a linha-raiz do playbook ═══
console.log('▸ 3/4 criando raiz "Perpétuo Lucrativo"...');
const root = await api('pages', {
  parent: { database_id: DB_PB },
  icon: { type: 'external', external: { url: 'https://www.notion.so/icons/playback-play_green.svg' } },
  properties: {
    'Etapa': { title: txt(NOME_NOVO) },
    'Playbook': sel(NOME_NOVO),
    'Nível': sel('Playbook'),
    'Notas': { rich_text: txt('Raiz do playbook. Etapas macro penduradas aqui; instanciar via notion-instanciar-playbook.mjs.') },
  },
});
console.log(`  ✓ ${root.id}`);

// ═══ 4. classificar níveis + pendurar etapas macro na raiz ═══
console.log('▸ 4/4 organizando a árvore...');
let n = 0;
for (const r of raizes) {
  await api(`pages/${r.id}`, { properties: {
    'Nível': sel('Etapa'),
    'Etapa principal': rel([root.id]),
  }}, 'PATCH');
  n++;
}
console.log(`  ✓ ${n} etapas macro penduradas na raiz`);
for (const r of filhas) {
  await api(`pages/${r.id}`, { properties: { 'Nível': sel('Tarefa') } }, 'PATCH');
  n++;
  if (n % 15 === 0) console.log(`  … ${n}/${all.length}`);
}
console.log(`  ✓ ${filhas.length} tarefas classificadas`);

console.log('\n✅ Playbooks v2: Playbook (raiz) → Etapa → Tarefa');
console.log('   view de catálogo: filtro Nível = Playbook');
