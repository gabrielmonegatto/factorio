#!/usr/bin/env node
// 🎯 METAS — fusão Polaris (50) + Metas (11), dedup, hierarquia preservada,
// relations → Unidades e → Projetos. Aditivo: originais intactos.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const COFRE = '3a5f06f1-0ce3-80c3-9b15-c486acb05b67';
const DB_UNIDADES = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';
const DB_PROJETOS = '3a6f06f1-0ce3-81c7-bb20-c668d4d85c38';
const IDS = JSON.parse(fs.readFileSync(new URL('./notion-migrate-ids.json', import.meta.url).pathname.replace(/^\//, ''), 'utf8'));
const U = IDS.unidades; // BLUUE, Markeologia, Trevvo, Entelekkia, Pessoal
const P = IDS.projetos;

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

const txt = c => [{ type: 'text', text: { content: c } }];
const title = c => ({ title: txt(c) });
const sel = n => (n ? { select: { name: n } } : { select: null });
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const multi = ns => ({ multi_select: ns.map(name => ({ name })) });

// ═══ 1. criar banco ═══
console.log('▸ 1/4 criando 🎯 Metas...');
const db = await api('databases', {
  parent: { type: 'page_id', page_id: COFRE },
  icon: { type: 'emoji', emoji: '🎯' },
  title: txt('🎯 Metas'),
  description: txt('Fusão Polaris + Metas (24/07/2026). Resultados que você quer alcançar, do sonho no baú à conquista. Hierarquia via Meta principal.'),
  properties: {
    'Nome': { title: {} },
    'Estado': { select: { options: [
      { name: '📦 Baú', color: 'gray' },
      { name: '🏹 Mirando', color: 'blue' },
      { name: '❄️ No Gelo', color: 'yellow' },
      { name: '✅ Alcançada', color: 'green' },
    ]}},
    'Tipo': { multi_select: { options: [
      { name: 'crescimento', color: 'green' },
      { name: 'construção', color: 'blue' },
      { name: 'realização', color: 'purple' },
    ]}},
    'Prioridade': { select: { options: [
      { name: 'Major', color: 'red' },
      { name: 'Minor', color: 'gray' },
    ]}},
    'Unidade': { relation: { database_id: DB_UNIDADES, type: 'dual_property', dual_property: {} } },
    'Projetos': { relation: { database_id: DB_PROJETOS, type: 'dual_property', dual_property: {} } },
  },
});
console.log(`  ✓ ${db.id}`);

// ═══ 2. self-relation + renomear backs + rollup âmbito ═══
console.log('▸ 2/4 hierarquia e rollups...');
await api(`databases/${db.id}`, {
  properties: { 'Meta principal': { relation: { database_id: db.id, type: 'dual_property', dual_property: {} } } },
}, 'PATCH');
const fresh = await api(`databases/${db.id}`, null, 'GET');
const renames = {};
for (const [name, p] of Object.entries(fresh.properties)) {
  if (p.type === 'relation' && name.includes('(Meta principal)')) renames[name] = { name: 'Submetas' };
}
if (Object.keys(renames).length) await api(`databases/${db.id}`, { properties: renames }, 'PATCH');
await api(`databases/${db.id}`, {
  properties: { 'Âmbito': { rollup: { relation_property_name: 'Unidade', rollup_property_name: 'Âmbito', function: 'show_original' } } },
}, 'PATCH');
// renomear backs nos bancos vizinhos
for (const [dbId, from, to] of [
  [DB_PROJETOS, '(Projetos)', 'Meta'],
  [DB_UNIDADES, '(Unidade)', 'Metas'],
]) {
  const d = await api(`databases/${dbId}`, null, 'GET');
  const r = {};
  for (const [name, p] of Object.entries(d.properties))
    if (p.type === 'relation' && name.includes('🎯') && name.includes(from)) r[name] = { name: to };
  if (Object.keys(r).length) await api(`databases/${dbId}`, { properties: r }, 'PATCH');
}
console.log('  ✓');

// ═══ 3. linhas ═══
// [nome, estado, tipos[], prioridade, unidade, metaPrincipal, projeto]
const B = '📦 Baú', M = '🏹 Mirando', G = '❄️ No Gelo';
const ROWS = [
  // ---- pais primeiro (hierarquia) ----
  ['Maestria: Artes Sociais', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Maestria: Artes Marciais (Brazillian Taijutsu)', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Maestria: Shape e Condicionamento', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Construir a DreamHouse', B, ['construção'], null, 'Pessoal', null, null],
  ['Consolidar: Markeologia', B, ['construção'], null, 'Markeologia', null, null],
  ['Independência Financeira', B, ['construção'], null, 'Trevvo', null, null],
  ['Casar com uma mulher virtuosa', B, ['construção'], null, 'Pessoal', null, null],
  // ---- ativas (🏹 Mirando) ----
  ['Transformação HighValueMan', M, [], null, 'Pessoal', null, null],
  ['Construir Marketing System 1.0', M, [], null, 'Markeologia', null, null],
  ['Construir Life System 1.0', M, [], 'Major', 'Pessoal', null, 'Construir Life System 1.0'],
  ['Lançar Novo Negócio', M, [], null, 'Markeologia', null, null],
  ['elaboração plano financeiro', M, [], null, 'Trevvo', 'Independência Financeira', null],
  ['Lançar Holding', M, [], 'Major', 'Markeologia', null, 'Lançar Holding'],
  ['Construir Business System 1.0', M, [], 'Major', 'Markeologia', null, 'Construir Business System 1.0'],
  ['Ler a Bíblia NTLH', M, [], 'Major', 'Pessoal', null, 'Ler a Bíblia NTLH'],
  // ---- no gelo (❄️) ----
  ['Entrar no Modo Sem Limites', G, ['construção'], null, 'Pessoal', null, 'Entrar no Modo Sem Limites'],
  ['Começar a Treinar Artes Sociais', G, [], null, 'Pessoal', 'Maestria: Artes Sociais', 'Começar a Treinar Artes Sociais'],
  ['Começar a Treinar Artes Marciais', G, [], null, 'Pessoal', 'Maestria: Artes Marciais (Brazillian Taijutsu)', 'Começar a Treinar Artes Marciais'],
  ['Dominar Flexibilidade p/ Chutes', G, [], null, 'Pessoal', 'Maestria: Shape e Condicionamento', 'Dominar Flexibilidade p/ Chutes'],
  ['Dominar Handstand', G, [], null, 'Pessoal', 'Maestria: Shape e Condicionamento', 'Dominar Handstand'],
  ['Passar no Bar Brothers Requiriments', G, [], null, 'Pessoal', 'Maestria: Shape e Condicionamento', 'Passar no Bar Brothers Requiriments'],
  ['Tirar Cidadania Italiana', G, ['realização'], null, 'Pessoal', null, 'Tirar Cidadania Italiana'],
  // ---- baú (📦) ----
  ['Maestria: Teologia', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Forjar a mente Entelekkia', B, ['crescimento'], null, 'Entelekkia', null, null],
  ['Construção: Laboratório Pessoal (Escritório)', B, ['construção'], null, 'Pessoal', 'Construir a DreamHouse', null],
  ['Maestria: Xadrez (MN)', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Impactar positivamente amigos e familiares', B, ['construção'], null, 'Pessoal', null, null],
  ['Mapa de Network', B, [], null, 'Pessoal', 'Maestria: Artes Sociais', null],
  ['Construir sistema pessoal: COMPASS', B, ['construção'], null, 'Pessoal', null, null],
  ['CRM Social e Profissional', B, [], null, 'Pessoal', 'Maestria: Artes Sociais', null],
  ['Construção: Sala de Jogos', B, ['construção'], null, 'Pessoal', 'Construir a DreamHouse', null],
  ['Maestria: Biblicismo', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Insígnia: Brazillian Traveller', B, ['realização'], null, 'Pessoal', null, null],
  ['Maestria: Marketing e Vendas', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Maestria: Liderança', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Desenvolver Modo Sherlock Holmes', B, [], null, 'Pessoal', 'Maestria: Artes Sociais', null],
  ['Consolidar: Entelekkia', B, ['construção'], null, 'Entelekkia', null, null],
  ['eliminação de todas as dívidas', B, [], null, 'Trevvo', 'Independência Financeira', null],
  ['Comprar uma Evoque', B, ['construção'], null, 'Trevvo', null, null],
  ['Comprar um Mustang', B, ['construção'], null, 'Trevvo', null, null],
  ['Construção: Adega e Bar', B, ['construção'], null, 'Pessoal', 'Construir a DreamHouse', null],
  ['Consolidar: Monegatto (Marca Pessoal)', B, ['construção'], null, 'Pessoal', null, null],
  ['Maestria: VSM’s', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Construção: Biblioteca', B, ['construção'], null, 'Pessoal', 'Construir a DreamHouse', null],
  ['Desenvolver Modo 12 Arqs', B, [], null, 'Pessoal', 'Maestria: Artes Sociais', null],
  ['Construir uma “família Gracie”', B, ['construção'], null, 'Pessoal', 'Casar com uma mulher virtuosa', null],
  ['Estar conectado com os maiores de diversos mercados', B, [], null, 'Pessoal', 'Maestria: Artes Sociais', null],
  ['Maestria: Musical', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Consolidar Hub de co-produção', B, [], null, 'Markeologia', 'Consolidar: Markeologia', null],
  ['Insígnia: 101 aventuras', B, ['realização'], null, 'Pessoal', null, null],
  ['Lançar Tactics Ogre Exodus', B, ['construção'], null, 'Pessoal', null, null],
  ['Construção: Estúdio e Cenários', B, ['construção'], null, 'Pessoal', 'Construir a DreamHouse', null],
  ['Maestria: Aparência', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Maestria: Business', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Insígnia: 196 Countries', B, ['realização'], null, 'Pessoal', null, null],
  ['Consolidar: Escola de Gaio', B, ['construção'], null, 'Pessoal', null, null],
  ['Maestria - Biohacking', B, ['crescimento'], null, 'Pessoal', null, null],
  ['Construir sistema de marketing: THE SYSTEM', B, ['construção'], null, 'Markeologia', null, null],
  ['Maestria: Memorização das Escrituras', B, ['crescimento'], null, 'Pessoal', null, null],
];

console.log(`▸ 3/4 inserindo ${ROWS.length} metas...`);
const ids = {};
let n = 0;
for (const [nome, estado, tipos, prio, unidade, pai, proj] of ROWS) {
  const props = { 'Nome': title(nome), 'Estado': sel(estado), 'Unidade': rel([U[unidade]]) };
  if (tipos.length) props['Tipo'] = multi(tipos);
  if (prio) props['Prioridade'] = sel(prio);
  if (pai && ids[pai]) props['Meta principal'] = rel([ids[pai]]);
  if (proj && P[proj]) props['Projetos'] = rel([P[proj]]);
  const p = await api('pages', { parent: { database_id: db.id }, properties: props });
  ids[nome] = p.id;
  n++;
  if (n % 10 === 0) console.log(`  … ${n}/${ROWS.length}`);
}
console.log(`  ✓ ${n} metas`);

// ═══ 4. verificação ═══
console.log('▸ 4/4 verificando...');
const q = await api(`databases/${db.id}/query`, { page_size: 100 });
const est = {};
q.results.forEach(r => { const k = r.properties.Estado.select?.name; est[k] = (est[k] || 0) + 1; });
console.log('  distribuição:', JSON.stringify(est));

fs.writeFileSync(new URL('./notion-metas-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ db: db.id, metas: ids }, null, 2));
console.log(`\n✅ 🎯 Metas no ar: ${db.url}`);
