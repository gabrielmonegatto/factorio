#!/usr/bin/env node
// PLAYBOOKS v3 — catálogo de verdade:
//   banco Playbooks = 1 LINHA POR PLAYBOOK (só isso).
//   dentro da PÁGINA de cada playbook = banco inline "Etapas" com a árvore própria
//   (etapas macro → tarefas), independente dos outros playbooks.
// Duplicar a página do playbook copia o banco inline junto = template pronto.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const DB_PB = '3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2';
const ROOT_PAGE = '3acf06f1-0ce3-81d7-83b2-d28d2b0c72eb'; // linha "Perpétuo Lucrativo"
const DB_ICON = { type: 'external', external: { url: 'https://www.notion.so/icons/database_green.svg' } };

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
      if (!res.ok) { console.error(`✗ ${method} ${path}:`, JSON.stringify(json).slice(0, 400)); throw new Error(json.message); }
      return json;
    } catch (e) { if (t >= 4 || e.message !== 'fetch failed') throw e; await sleep(t * 3000); }
  }
}
async function queryAll(dbId) {
  let all = [], cursor;
  do {
    const j = await api(`databases/${dbId}/query`, { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
    all.push(...j.results);
    cursor = j.has_more ? j.next_cursor : null;
  } while (cursor);
  return all;
}
const txt = c => [{ type: 'text', text: { content: c } }];
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const sel = n => ({ select: { name: n } });
const T = p => p?.title?.map(t => t.plain_text).join('') || '';

const AREAS = [
  { name: 'Especialista', color: 'purple' }, { name: 'Tráfego', color: 'orange' },
  { name: 'Design', color: 'pink' }, { name: 'Copy', color: 'yellow' },
  { name: 'Webdesign', color: 'blue' }, { name: 'Edição de Vídeos', color: 'red' },
  { name: 'Infra', color: 'gray' }, { name: 'Estrategista', color: 'green' },
];

// ═══ 1. ler a árvore atual ═══
console.log('▸ 1/5 lendo árvore atual...');
const todas = await queryAll(DB_PB);
const rootId = ROOT_PAGE.replace(/-/g, '');
const conteudo = todas.filter(r => r.id.replace(/-/g, '') !== rootId);
const etapas = conteudo.filter(r => r.properties['Nível']?.select?.name === 'Etapa');
const tarefas = conteudo.filter(r => r.properties['Nível']?.select?.name === 'Tarefa');
console.log(`  ${etapas.length} etapas macro, ${tarefas.length} tarefas`);

// ═══ 2. criar banco inline dentro da página do playbook ═══
console.log('▸ 2/5 criando banco inline "Etapas" dentro do playbook...');
const inline = await api('databases', {
  parent: { type: 'page_id', page_id: ROOT_PAGE },
  is_inline: true,
  icon: DB_ICON,
  title: txt('Etapas'),
  description: txt('Árvore deste playbook: etapas macro → tarefas. Duplicar a página do playbook copia tudo junto.'),
  properties: {
    'Etapa': { title: {} },
    'Ordem': { number: {} },
    'Área': { multi_select: { options: AREAS } },
    'Notas': { rich_text: {} },
  },
});
await api(`databases/${inline.id}`, {
  properties: { 'Etapa principal': { relation: { database_id: inline.id, type: 'dual_property', dual_property: {} } } },
}, 'PATCH');
{
  const d = await api(`databases/${inline.id}`, null, 'GET');
  const r = {};
  for (const [name, p] of Object.entries(d.properties))
    if (p.type === 'relation' && name.startsWith('Related to') && name.includes('(Etapa principal)')) r[name] = { name: 'Subetapas' };
  if (Object.keys(r).length) await api(`databases/${inline.id}`, { properties: r }, 'PATCH');
}
console.log(`  ✓ ${inline.id}`);

// ═══ 3. copiar etapas + tarefas pro inline ═══
console.log('▸ 3/5 copiando a árvore...');
const map = {};
let ordem = 0;
for (const e of etapas) {
  ordem++;
  const areas = e.properties['Área']?.multi_select?.map(o => o.name) || [];
  const props = { 'Etapa': { title: txt(T(e.properties['Etapa'])) }, 'Ordem': { number: ordem } };
  if (areas.length) props['Área'] = { multi_select: areas.map(name => ({ name })) };
  const np = await api('pages', { parent: { database_id: inline.id }, properties: props });
  map[e.id.replace(/-/g, '')] = np.id;
  console.log(`  ▪ ${T(e.properties['Etapa'])}`);
}
for (const t of tarefas) {
  const areas = t.properties['Área']?.multi_select?.map(o => o.name) || [];
  const props = { 'Etapa': { title: txt(T(t.properties['Etapa'])) } };
  if (areas.length) props['Área'] = { multi_select: areas.map(name => ({ name })) };
  const pais = (t.properties['Etapa principal']?.relation || []).map(r => map[r.id.replace(/-/g, '')]).filter(Boolean);
  if (pais.length) props['Etapa principal'] = rel(pais);
  const np = await api('pages', { parent: { database_id: inline.id }, properties: props });
  map[t.id.replace(/-/g, '')] = np.id;
}
console.log(`  ✓ ${etapas.length + tarefas.length} linhas copiadas pro inline`);

// ═══ 4. arquivar as 57 linhas do banco Playbooks ═══
console.log('▸ 4/5 limpando o banco Playbooks (arquivando as linhas de conteúdo)...');
let a = 0;
for (const r of conteudo) {
  await api(`pages/${r.id}`, { archived: true }, 'PATCH');
  a++;
  if (a % 20 === 0) console.log(`  … ${a}/${conteudo.length}`);
}
console.log(`  ✓ ${a} arquivadas (lixeira) — sobra só a linha do playbook`);

// ═══ 5. enxugar o schema do banco Playbooks ═══
console.log('▸ 5/5 enxugando schema do catálogo...');
await api(`databases/${DB_PB}`, {
  description: txt('Catálogo de playbooks. 1 linha = 1 playbook. A árvore de etapas/tarefas vive DENTRO da página de cada linha (banco inline "Etapas").'),
  properties: {
    'Etapa': { name: 'Playbook' },
    'Nível': null,
    'Etapa principal': null,
    'Subetapas': null,
    'Área': null,
    'Playbook': null,
    'Descrição': { rich_text: {} },
    'Tipo': { select: { options: [
      { name: 'Funil', color: 'blue' }, { name: 'Operação', color: 'green' },
      { name: 'Lançamento', color: 'orange' }, { name: 'Onboarding', color: 'purple' },
    ]}},
    'Status': { select: { options: [
      { name: 'Ativo', color: 'green' }, { name: 'Rascunho', color: 'yellow' }, { name: 'Arquivado', color: 'gray' },
    ]}},
  },
}, 'PATCH');
await api(`pages/${ROOT_PAGE}`, { properties: {
  'Tipo': sel('Funil'), 'Status': sel('Ativo'),
  'Descrição': { rich_text: txt('Funil perpétuo completo: produto → página de vendas → checkout → anúncios → recuperação → upsell/downsell → obrigado. 8 etapas macro, 49 tarefas.') },
  'Notas': { rich_text: [] },
}}, 'PATCH');

const final = await queryAll(DB_PB);
console.log(`\n✅ Playbooks agora é catálogo: ${final.length} linha(s)`);
final.forEach(r => console.log(`   • ${T(r.properties['Playbook'])}`));
console.log(`   árvore dentro da página → banco inline "Etapas" (${inline.id})`);
fs.writeFileSync(new URL('./notion-playbook-inline-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ catalogo: DB_PB, 'Perpétuo Lucrativo': { page: ROOT_PAGE, inlineDb: inline.id } }, null, 2));
