#!/usr/bin/env node
// BUSINESS SYSTEM — cria a instância Biz dentro da página Business System,
// migra (copia + arquiva origem) as linhas de negócio dos bancos unificados,
// padroniza nomenclatura de TODOS os bancos (nome limpo + ícone database verde),
// e adiciona o portfólio real de unidades.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const BS_PAGE = '33d6bf27-9f65-4043-8a5d-c53fe0b241a3'; // página Business System
const DB_UNIDADES = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';
const DB_PROJ_LS  = '3a6f06f1-0ce3-81c7-bb20-c668d4d85c38';
const DB_TASKS_LS = '3a6f06f1-0ce3-817a-9068-de47ac0b3b11';
const DB_NOTAS_LS = '3a6f06f1-0ce3-8159-b6b9-cbce44a717d8';
const DB_METAS    = '3a7f06f1-0ce3-8153-a258-ebbff106eab9';
const DB_CONTAS   = '3a7f06f1-0ce3-81c8-9414-c18cc156554f';
const DB_LANC     = '3a7f06f1-0ce3-8159-9ef2-dfc787cd4cc7';
const DB_CATEG    = '3a7f06f1-0ce3-81a6-831c-f8f43e0fedce';
const DB_RECURSOS = '3a7f06f1-0ce3-8177-950e-e703ebb71da3';
const U = JSON.parse(fs.readFileSync(new URL('./notion-migrate-ids.json', import.meta.url).pathname.replace(/^\//, ''), 'utf8')).unidades;
const METAS_IDS = JSON.parse(fs.readFileSync(new URL('./notion-metas-ids.json', import.meta.url).pathname.replace(/^\//, ''), 'utf8')).metas;

const DB_ICON = { type: 'external', external: { url: 'https://www.notion.so/icons/database_green.svg' } };

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, body, method = 'POST') {
  await sleep(360);
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) { console.error(`✗ ${method} ${path}:`, JSON.stringify(json).slice(0, 400)); throw new Error(json.message); }
  return json;
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
const title = c => ({ title: txt(c) });
const sel = n => (n ? { select: { name: n } } : { select: null });
const rel = ids => ({ relation: ids.map(id => ({ id })) });

const PESSOAS = [
  ['Monegatto', 'purple'], ['Bruno', 'blue'], ['Bruno Web', 'green'],
  ['Alma', 'pink'], ['Rafa', 'orange'], ['Mota', 'yellow'],
  ['Natã', 'brown'], ['Japa', 'red'], ['Givas', 'default'],
  ['Garrido', 'blue'], ['Almeida', 'green'], ['Quantum', 'purple'], ['Time', 'gray'],
].map(([name, color]) => ({ name, color }));

// ═══ 1. padronizar nomenclatura de todos os bancos existentes ═══
console.log('▸ 1/6 padronizando nomes + ícone database...');
const RENAMES = [
  // Unidades / Projetos [L.S.] / Tasks [L.S.] já renomeados na 1ª execução.
  // Notas foi DELETADO pelo Gabriel — fora do fluxo.
  [DB_METAS,    'Metas'],
  [DB_CONTAS,   'Contas [Trevvo]'],
  [DB_LANC,     'Lançamentos [Trevvo]'],
  [DB_CATEG,    'Categorias [Trevvo]'],
  [DB_RECURSOS, 'Recursos'],
];
for (const [id, nome] of RENAMES) {
  await api(`databases/${id}`, { title: txt(nome), icon: DB_ICON }, 'PATCH');
  console.log(`  ✓ ${nome}`);
}

// ═══ 2. novas unidades (portfólio real) ═══
console.log('▸ 2/6 portfólio de unidades...');
const NOVAS = [
  ['Br4nds', 'Cliente'], ['ZOAC', 'Própria'], ['Tonaface', 'Própria'], ['Manancial', 'Própria'],
];
for (const [nome, tipo] of NOVAS) {
  const p = await api('pages', {
    parent: { database_id: DB_UNIDADES },
    properties: { 'Nome': title(nome), 'Tipo': sel(tipo), 'Status': sel('Ativa'), 'Âmbito': sel('Business') },
  });
  U[nome] = p.id;
  console.log(`  ✓ ${nome} (${tipo})`);
}

// ═══ 3. criar bancos [B.S.] ═══
console.log('▸ 3/6 criando bancos [B.S.] na página Business System...');
const projBS = await api('databases', {
  parent: { type: 'page_id', page_id: BS_PAGE },
  icon: DB_ICON,
  title: txt('Projetos [B.S.]'),
  description: txt('Frentes de trabalho das unidades de negócio.'),
  properties: {
    'Nome': { title: {} },
    'Marca': { relation: { database_id: DB_UNIDADES, type: 'dual_property', dual_property: {} } },
    'Status': { select: { options: [
      { name: 'Iniciar', color: 'gray' }, { name: 'Em andamento', color: 'blue' },
      { name: 'Pausado', color: 'yellow' }, { name: 'Finalizado', color: 'green' },
    ]}},
    'Deadline': { date: {} },
    'Notas': { rich_text: {} },
  },
});
console.log(`  ✓ Projetos [B.S.] ${projBS.id}`);

const tasksBS = await api('databases', {
  parent: { type: 'page_id', page_id: BS_PAGE },
  icon: DB_ICON,
  title: txt('Tasks [B.S.]'),
  description: txt('Demandas das unidades de negócio. Ligadas a projeto ou avulsas (só marca).'),
  properties: {
    'Demanda': { title: {} },
    'Projeto': { relation: { database_id: projBS.id, type: 'dual_property', dual_property: {} } },
    'Marca': { relation: { database_id: DB_UNIDADES, type: 'dual_property', dual_property: {} } },
    'Responsável': { multi_select: { options: PESSOAS } },
    'Status': { select: { options: [
      { name: 'Iniciar', color: 'gray' }, { name: 'Em andamento', color: 'blue' }, { name: 'Finalizado', color: 'green' },
    ]}},
    'Deadline': { date: {} },
    'Notas': { rich_text: {} },
  },
});
await api(`databases/${tasksBS.id}`, {
  properties: { 'Subtarefa de': { relation: { database_id: tasksBS.id, type: 'dual_property', dual_property: {} } } },
}, 'PATCH');
console.log(`  ✓ Tasks [B.S.] ${tasksBS.id}`);

// renomear back-relations feias
for (const [dbId, marker, to] of [
  [projBS.id, '(Projeto)', null], // nada — back fica em tasksBS
  [tasksBS.id, '(Subtarefa de)', 'Subtarefas'],
]) {
  const d = await api(`databases/${dbId}`, null, 'GET');
  const r = {};
  for (const [name, p] of Object.entries(d.properties))
    if (p.type === 'relation' && name.startsWith('Related to') && name.includes(marker) && to) r[name] = { name: to };
  if (Object.keys(r).length) await api(`databases/${dbId}`, { properties: r }, 'PATCH');
}
const projBSfresh = await api(`databases/${projBS.id}`, null, 'GET');
{
  const r = {};
  for (const [name, p] of Object.entries(projBSfresh.properties))
    if (p.type === 'relation' && name.startsWith('Related to') && name.includes('(Projeto)')) r[name] = { name: 'Tarefas' };
  if (Object.keys(r).length) await api(`databases/${projBS.id}`, { properties: r }, 'PATCH');
}

// ═══ 4. dump fresco + copiar linhas business ═══
console.log('▸ 4/6 lendo estado ATUAL dos bancos unificados...');
const BIZ_UNITS = new Set([U.BLUUE, U.Markeologia].map(x => x.replace(/-/g, '')));
const isBiz = relProp => relProp.relation.some(r => BIZ_UNITS.has(r.id.replace(/-/g, '')));

const [projRows, taskRows] = [await queryAll(DB_PROJ_LS), await queryAll(DB_TASKS_LS)];
const bizProj = projRows.filter(r => isBiz(r.properties['Marca']));
const bizNotas = [];
const bizProjIds = new Set(bizProj.map(r => r.id.replace(/-/g, '')));
const bizTasks = taskRows.filter(r =>
  isBiz(r.properties['Marca']) ||
  r.properties['Projeto'].relation.some(p => bizProjIds.has(p.id.replace(/-/g, ''))));
console.log(`  projetos biz: ${bizProj.length} | tasks biz: ${bizTasks.length}`);
console.log(`  (ficam no L.S.: ${projRows.length - bizProj.length} proj, ${taskRows.length - bizTasks.length} tasks)`);

const V = {
  t: p => p?.title?.map(t => t.plain_text).join('') || '',
  rt: p => p?.rich_text?.map(t => t.plain_text).join('') || '',
  s: p => p?.select?.name || null,
  d: p => p?.date?.start || null,
  ms: p => p?.multi_select?.map(o => o.name) || [],
  r: p => p?.relation?.map(x => x.id) || [],
};

console.log('▸ 5/6 copiando pro [B.S.] e arquivando origem...');
// projetos
const projMap = {};
for (const row of bizProj) {
  const p = row.properties;
  const props = {
    'Nome': title(V.t(p['Nome'])),
    'Marca': rel(V.r(p['Marca'])),
    'Status': sel(V.s(p['Status'])),
  };
  if (V.d(p['Deadline'])) props['Deadline'] = { date: { start: V.d(p['Deadline']) } };
  if (V.rt(p['Notas'])) props['Notas'] = { rich_text: txt(V.rt(p['Notas'])) };
  const body = { parent: { database_id: projBS.id }, properties: props };
  if (row.icon?.type === 'emoji') body.icon = row.icon;
  const np = await api('pages', body);
  projMap[row.id.replace(/-/g, '')] = np.id;
}
console.log(`  ✓ ${bizProj.length} projetos copiados`);

// tasks (1º passe: criar; 2º passe: subtarefas)
const taskMap = {};
for (const row of bizTasks) {
  const p = row.properties;
  const props = {
    'Demanda': title(V.t(p['Demanda'])),
    'Status': sel(V.s(p['Status'])),
  };
  const marca = V.r(p['Marca']); if (marca.length) props['Marca'] = rel(marca);
  const proj = V.r(p['Projeto']).map(id => projMap[id.replace(/-/g, '')]).filter(Boolean);
  if (proj.length) props['Projeto'] = rel(proj);
  const resp = V.ms(p['Responsável']); if (resp.length) props['Responsável'] = { multi_select: resp.map(name => ({ name })) };
  if (V.d(p['Deadline'])) props['Deadline'] = { date: { start: V.d(p['Deadline']) } };
  if (V.rt(p['Notas'])) props['Notas'] = { rich_text: txt(V.rt(p['Notas'])) };
  const np = await api('pages', { parent: { database_id: tasksBS.id }, properties: props });
  taskMap[row.id.replace(/-/g, '')] = np.id;
}
let subs = 0;
for (const row of bizTasks) {
  const parents = V.r(row.properties['Subtarefa de']).map(id => taskMap[id.replace(/-/g, '')]).filter(Boolean);
  if (parents.length) {
    await api(`pages/${taskMap[row.id.replace(/-/g, '')]}`, { properties: { 'Subtarefa de': rel(parents) } }, 'PATCH');
    subs++;
  }
}
console.log(`  ✓ ${bizTasks.length} tasks copiadas (${subs} com subtarefa religada)`);

// arquivar originais
let arch = 0;
for (const row of [...bizProj, ...bizTasks, ...bizNotas]) {
  await api(`pages/${row.id}`, { archived: true }, 'PATCH');
  arch++;
  if (arch % 20 === 0) console.log(`  … arquivadas ${arch}`);
}
console.log(`  ✓ ${arch} originais arquivadas (lixeira, restaurável)`);

// ═══ 6. religar Metas de negócio nos projetos novos ═══
console.log('▸ 6/6 religando Metas → Projetos [B.S.]...');
await api(`databases/${DB_METAS}`, {
  properties: { 'Projetos [B.S.]': { relation: { database_id: projBS.id, type: 'dual_property', dual_property: {} } } },
}, 'PATCH');
const projBSrows = await queryAll(projBS.id);
const byName = {};
projBSrows.forEach(r => { byName[V.t(r.properties['Nome'])] = r.id; });
for (const metaName of ['Lançar Holding', 'Construir Business System 1.0']) {
  if (METAS_IDS[metaName] && byName[metaName]) {
    await api(`pages/${METAS_IDS[metaName]}`, { properties: { 'Projetos [B.S.]': rel([byName[metaName]]) } }, 'PATCH');
    console.log(`  ✓ ${metaName}`);
  }
}
// renomear back no projBS
{
  const d = await api(`databases/${projBS.id}`, null, 'GET');
  const r = {};
  for (const [name, p] of Object.entries(d.properties))
    if (p.type === 'relation' && name.startsWith('Related to Metas')) r[name] = { name: 'Meta' };
  if (Object.keys(r).length) await api(`databases/${projBS.id}`, { properties: r }, 'PATCH');
}

fs.writeFileSync(new URL('./notion-bs-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ projetosBS: projBS.id, tasksBS: tasksBS.id, unidadesNovas: NOVAS.map(n => n[0]).reduce((a, n) => ({ ...a, [n]: U[n] }), {}) }, null, 2));

console.log('\n✅ BUSINESS SYSTEM montado');
console.log(`   Projetos [B.S.]: ${projBS.url}`);
console.log(`   Tasks [B.S.]:    ${tasksBS.url}`);
