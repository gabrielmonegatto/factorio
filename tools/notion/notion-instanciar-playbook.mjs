#!/usr/bin/env node
// INSTANCIAR PLAYBOOK — clona a árvore de um playbook do catálogo pras Tasks
// da unidade de negócio. É a "linha de montagem".
//
// Estrutura esperada (v3): banco Playbooks = catálogo (1 linha por playbook);
// dentro da PÁGINA de cada playbook vive um banco inline "Etapas" com a árvore.
//
// Uso: node notion-instanciar-playbook.mjs "<Marca>" ["<Playbook>"]
// Ex.: node notion-instanciar-playbook.mjs "ZOAC"
//      node notion-instanciar-playbook.mjs "Tonaface" "Perpétuo Lucrativo"
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const DB_PLAYBOOKS = '3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2';
const DB_TASKS_BS  = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';
const DB_PROJ_BS   = '3a7f06f1-0ce3-81d2-9dd9-ddad8d16109c';
const DB_UNIDADES  = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';

const [marcaNome, playbookNome = 'Perpétuo Lucrativo'] = process.argv.slice(2);
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

// 1. marca
const marcas = await queryAll(DB_UNIDADES, { property: 'Nome', title: { equals: marcaNome } });
if (!marcas.length) { console.error(`marca "${marcaNome}" não existe no banco Unidades`); process.exit(1); }
const marcaId = marcas[0].id;
console.log(`▸ marca: ${marcaNome}`);

// 2. playbook no catálogo
const pbs = await queryAll(DB_PLAYBOOKS, { property: 'Playbook', title: { equals: playbookNome } });
if (!pbs.length) { console.error(`playbook "${playbookNome}" não existe no catálogo`); process.exit(1); }
const pbPage = pbs[0].id;

// 3. achar o banco inline "Etapas" dentro da página do playbook
const blocks = await api(`blocks/${pbPage}/children?page_size=100`, null, 'GET');
const inlineBlock = (blocks.results || []).find(b => b.type === 'child_database');
if (!inlineBlock) { console.error(`playbook "${playbookNome}" não tem banco inline de etapas`); process.exit(1); }
const etapas = await queryAll(inlineBlock.id);
if (!etapas.length) { console.error('banco de etapas vazio'); process.exit(1); }
console.log(`▸ playbook "${playbookNome}": ${etapas.length} linhas na árvore`);

// 4. projeto-contêiner na marca
const proj = await api('pages', {
  parent: { database_id: DB_PROJ_BS },
  properties: {
    'Nome': title(`${playbookNome} — ${marcaNome}`),
    'Marca': rel([marcaId]),
    'Status': sel('Em andamento'),
    'Notas': { rich_text: txt(`Instância do playbook "${playbookNome}".`) },
  },
});
console.log(`▸ projeto criado: ${playbookNome} — ${marcaNome}`);

// 5. clonar a árvore como tasks (2 passes: criar, depois religar hierarquia)
const macro = etapas.filter(e => !(e.properties['Etapa principal']?.relation || []).length)
  .sort((a, b) => (a.properties['Ordem']?.number ?? 999) - (b.properties['Ordem']?.number ?? 999));
const filhas = etapas.filter(e => (e.properties['Etapa principal']?.relation || []).length);
const map = {};
let n = 0;
for (const e of [...macro, ...filhas]) {
  const areas = e.properties['Área']?.multi_select?.map(o => o.name) || [];
  const props = {
    'Demanda': title(T(e.properties['Etapa'])),
    'Projeto': rel([proj.id]),
    'Marca': rel([marcaId]),
    'Status': sel('Iniciar'),
  };
  if (areas.length) props['Responsável'] = { multi_select: areas.map(name => ({ name })) };
  const nt = await api('pages', { parent: { database_id: DB_TASKS_BS }, properties: props });
  map[e.id.replace(/-/g, '')] = nt.id;
  n++;
  if (n % 15 === 0) console.log(`  … ${n}/${etapas.length}`);
}
let subs = 0;
for (const e of filhas) {
  const pais = (e.properties['Etapa principal'].relation || []).map(r => map[r.id.replace(/-/g, '')]).filter(Boolean);
  if (pais.length) { await api(`pages/${map[e.id.replace(/-/g, '')]}`, { properties: { 'Subtarefa de': rel(pais) } }, 'PATCH'); subs++; }
}

console.log(`\n✅ instância criada: ${n} tasks (${subs} aninhadas) na marca ${marcaNome}`);
console.log('   agente/humano marca progresso nas Tasks; o playbook do catálogo fica intacto.');
