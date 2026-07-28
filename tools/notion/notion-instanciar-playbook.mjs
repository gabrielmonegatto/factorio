#!/usr/bin/env node
// INSTANCIAR PLAYBOOK — clona um checklist-mestre do banco Playbooks pra Tasks
// da unidade, com hierarquia e áreas preservadas. É a "linha de montagem".
//
// Uso: node notion-instanciar-playbook.mjs "<Marca>" ["<Nome do Playbook>"]
// Ex.: node notion-instanciar-playbook.mjs "ZOAC"
//      node notion-instanciar-playbook.mjs "Tonaface" "Implementação Funil Perpétuo"
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const DB_PLAYBOOKS = '3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2';
const DB_TASKS_BS  = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';
const DB_PROJ_BS   = '3a7f06f1-0ce3-81d2-9dd9-ddad8d16109c';
const DB_UNIDADES  = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';

const [marcaNome, playbookNome = 'Implementação Funil Perpétuo'] = process.argv.slice(2);
if (!marcaNome) { console.error('uso: node notion-instanciar-playbook.mjs "<Marca>" ["<Playbook>"]'); process.exit(1); }

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
async function queryAll(dbId, filter) {
  let all = [], cursor;
  do {
    const j = await api(`databases/${dbId}/query`, { page_size: 100, ...(filter ? { filter } : {}), ...(cursor ? { start_cursor: cursor } : {}) });
    all.push(...j.results);
    cursor = j.has_more ? j.next_cursor : null;
  } while (cursor);
  return all;
}
const txt = c => [{ type: 'text', text: { content: c } }];
const title = c => ({ title: txt(c) });
const sel = n => ({ select: { name: n } });
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const T = p => p?.title?.map(t => t.plain_text).join('') || '';

// 1. achar a marca
const marcas = await queryAll(DB_UNIDADES, { property: 'Nome', title: { equals: marcaNome } });
if (!marcas.length) { console.error(`marca "${marcaNome}" não existe no Unidades`); process.exit(1); }
const marcaId = marcas[0].id;
console.log(`▸ marca: ${marcaNome} (${marcaId.slice(0, 8)})`);

// 2. etapas do playbook
const etapas = await queryAll(DB_PLAYBOOKS, { property: 'Playbook', select: { equals: playbookNome } });
if (!etapas.length) { console.error(`playbook "${playbookNome}" vazio/não existe`); process.exit(1); }
console.log(`▸ playbook "${playbookNome}": ${etapas.length} etapas`);

// 3. criar o projeto-contêiner na marca
const proj = await api('pages', {
  parent: { database_id: DB_PROJ_BS },
  properties: {
    'Nome': title(`${playbookNome} — ${marcaNome}`),
    'Marca': rel([marcaId]),
    'Status': sel('Em andamento'),
    'Notas': { rich_text: txt(`Instância do playbook "${playbookNome}" criada em ${new Date().toISOString().slice(0, 10)}.`) },
  },
});
console.log(`▸ projeto criado: ${playbookNome} — ${marcaNome}`);

// 4. clonar etapas como tasks (2 passes p/ hierarquia)
const map = {};
let n = 0;
for (const e of etapas) {
  const p = e.properties;
  const areas = p['Área']?.multi_select?.map(o => o.name) || [];
  const props = {
    'Demanda': title(T(p['Etapa'])),
    'Projeto': rel([proj.id]),
    'Marca': rel([marcaId]),
    'Status': sel('Iniciar'),
  };
  if (areas.length) props['Responsável'] = { multi_select: areas.map(name => ({ name })) };
  const nt = await api('pages', { parent: { database_id: DB_TASKS_BS }, properties: props });
  map[e.id.replace(/-/g, '')] = nt.id;
  n++;
  if (n % 10 === 0) console.log(`  … ${n}/${etapas.length}`);
}
let subs = 0;
for (const e of etapas) {
  const pais = (e.properties['Etapa principal']?.relation || []).map(r => map[r.id.replace(/-/g, '')]).filter(Boolean);
  if (pais.length) { await api(`pages/${map[e.id.replace(/-/g, '')]}`, { properties: { 'Subtarefa de': rel(pais) } }, 'PATCH'); subs++; }
}

console.log(`\n✅ instância criada: ${n} tasks (${subs} com hierarquia) na marca ${marcaNome}`);
console.log('   agente/humano marca o progresso nas Tasks; o mestre em Playbooks fica intacto.');
