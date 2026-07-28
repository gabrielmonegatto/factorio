#!/usr/bin/env node
// MIGRAÇÃO ADITIVA: funde Business System + Life System na espinha do Newsystem.
// NÃO deleta nem altera nada nos sistemas antigos — só cria no novo.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const NEWSYSTEM_PAGE = '3a5f06f1-0ce3-80c3-9b15-c486acb05b67';
const DB_MARCAS   = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';
const DB_PROJETOS = '3a6f06f1-0ce3-81c7-bb20-c668d4d85c38';
const DB_TASKS    = '3a6f06f1-0ce3-817a-9068-de47ac0b3b11';
const BLUUE_ID    = '3a6f06f1-0ce3-81ee-8729-f72fe0b02bc2';

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
const date = d => (d ? { date: { start: d } } : { date: null });
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const multi = ns => ({ multi_select: ns.map(name => ({ name })) });

// ═══ 1. evoluir 🏢 Marcas → 🏢 Unidades (+ Âmbito) ═══
console.log('▸ 1/6 Marcas → Unidades (+ campo Âmbito)...');
await api(`databases/${DB_MARCAS}`, {
  title: txt('🏢 Unidades'),
  description: txt('Índice mestre: marcas, negócios e áreas da vida. Âmbito separa Business de Life.'),
  properties: {
    'Âmbito': { select: { options: [
      { name: 'Business', color: 'blue' },
      { name: 'Life', color: 'purple' },
    ]}},
  },
}, 'PATCH');
await api(`pages/${BLUUE_ID}`, { properties: { 'Âmbito': sel('Business') } }, 'PATCH');
console.log('  ✓ renomeado + Âmbito criado + BLUUE=Business');

// ═══ 2. status "Pausado" em Projetos + self-relation e Notas em Tasks ═══
console.log('▸ 2/6 upgrades de schema (Pausado, Subtarefa de, Notas)...');
await api(`databases/${DB_PROJETOS}`, {
  properties: {
    'Status': { select: { options: [
      { name: 'Iniciar', color: 'gray' },
      { name: 'Em andamento', color: 'blue' },
      { name: 'Pausado', color: 'yellow' },
      { name: 'Finalizado', color: 'green' },
    ]}},
  },
}, 'PATCH');
await api(`databases/${DB_TASKS}`, {
  properties: {
    'Subtarefa de': { relation: { database_id: DB_TASKS, type: 'dual_property', dual_property: {} } },
    'Notas': { rich_text: {} },
  },
}, 'PATCH');
console.log('  ✓');

// ═══ 3. novas unidades ═══
console.log('▸ 3/6 unidades...');
const UNIDADES = [
  ['Markeologia', '🧲', 'Própria', 'Business'],
  ['Trevvo', '💸', 'Própria', 'Life'],
  ['Entelekkia', '🧠', 'Própria', 'Life'],
  ['Pessoal', '🏠', 'Interno', 'Life'],
];
const U = { BLUUE: BLUUE_ID };
for (const [nome, emoji, tipo, ambito] of UNIDADES) {
  const p = await api('pages', {
    parent: { database_id: DB_MARCAS },
    icon: { type: 'emoji', emoji },
    properties: { 'Nome': title(nome), 'Tipo': sel(tipo), 'Status': sel('Ativa'), 'Âmbito': sel(ambito) },
  });
  U[nome] = p.id;
  console.log(`  ✓ ${emoji} ${nome}`);
}

// ═══ 4. banco 📝 Notas ═══
console.log('▸ 4/6 banco 📝 Notas...');
const notasDb = await api('databases', {
  parent: { type: 'page_id', page_id: NEWSYSTEM_PAGE },
  icon: { type: 'emoji', emoji: '📝' },
  title: txt('📝 Notas'),
  description: txt('Notas e documentos. Um banco só — Área e Unidade separam.'),
  properties: {
    'Nome': { title: {} },
    'Área': { select: { options: [
      { name: 'Business', color: 'blue' }, { name: 'Marketing', color: 'orange' },
      { name: 'Operations', color: 'green' }, { name: 'Compass', color: 'purple' },
      { name: 'Trevvo', color: 'yellow' }, { name: 'Entelekkia', color: 'pink' },
    ]}},
    'Unidade': { relation: { database_id: DB_MARCAS, type: 'dual_property', dual_property: {} } },
    'Origem': { rich_text: {} },
  },
});
console.log(`  ✓ ${notasDb.id}`);

const NOTAS = [
  // [nome, área, unidade, origem]
  ['Inteligência ⏳', 'Business', 'Markeologia'], ['Holding ⏳', 'Business', 'Markeologia'], ['Financeiro 🏗️', 'Business', 'Markeologia'],
  ['Conteúdo 🏗️', 'Marketing', 'Markeologia'], ['Estratégia 🏗️', 'Marketing', 'Markeologia'], ['Conversão ⏳', 'Marketing', 'Markeologia'],
  ['Metas 🏗️', 'Operations', 'Markeologia'], ['Projetos 🏗️', 'Operations', 'Markeologia'], ['Sprints 🏗️', 'Operations', 'Markeologia'],
  ['Metas', 'Compass', 'Pessoal'], ['Navegação', 'Compass', 'Pessoal'], ['Tarefas', 'Compass', 'Pessoal'], ['Projetos', 'Compass', 'Pessoal'], ['Polaris', 'Compass', 'Pessoal'],
  ['Mapa', 'Trevvo', 'Trevvo'], ['Sabedoria', 'Trevvo', 'Trevvo'], ['Orçamento', 'Trevvo', 'Trevvo'], ['Patrimônio', 'Trevvo', 'Trevvo'], ['Fluxo', 'Trevvo', 'Trevvo'],
];
for (const [nome, area, unidade] of NOTAS) {
  await api('pages', {
    parent: { database_id: notasDb.id },
    properties: {
      'Nome': title(nome), 'Área': sel(area), 'Unidade': rel([U[unidade]]),
      'Origem': { rich_text: txt(`migrado de "${area} [${area === 'Compass' || area === 'Trevvo' || area === 'Entelekkia' ? 'LifeSystem' : 'B.S.'}]" em 23/07/2026`) },
    },
  });
}
console.log(`  ✓ ${NOTAS.length} notas migradas`);

// ═══ 5. projetos (Metas do Life + Projetos do Life) ═══
console.log('▸ 5/6 projetos...');
const PROJS = [
  // [nome, emoji, unidade, status, deadline]
  ['Construir Life System 1.0', '🧭', 'Pessoal', 'Em andamento', '2024-07-19'],
  ['Construir Business System 1.0', '🏭', 'Markeologia', 'Em andamento', '2024-07-31'],
  ['Lançar Holding', '🚀', 'Markeologia', 'Em andamento', null],
  ['Ler a Bíblia NTLH', '📖', 'Pessoal', 'Em andamento', null],
  ['Segundo Cérebro', '🧠', 'Pessoal', 'Iniciar', null],
  ['Biblioteca', '📚', 'Pessoal', 'Iniciar', null],
  ['Guarda-Roupa', '👔', 'Pessoal', 'Iniciar', null],
  ['Cenário', '🎬', 'Pessoal', 'Iniciar', null],
  ['Começar a Treinar Artes Sociais', '🗣️', 'Pessoal', 'Pausado', null],
  ['Começar a Treinar Artes Marciais', '🥋', 'Pessoal', 'Pausado', null],
  ['Dominar Flexibilidade p/ Chutes', '🦵', 'Pessoal', 'Pausado', null],
  ['Dominar Handstand', '🤸', 'Pessoal', 'Pausado', null],
  ['Passar no Bar Brothers Requiriments', '💪', 'Pessoal', 'Pausado', null],
  ['Tirar Cidadania Italiana', '🇮🇹', 'Pessoal', 'Pausado', null],
  ['Entrar no Modo Sem Limites', '⚡', 'Pessoal', 'Pausado', null],
];
const P = {};
for (const [nome, emoji, unidade, status, dl] of PROJS) {
  const p = await api('pages', {
    parent: { database_id: DB_PROJETOS },
    icon: { type: 'emoji', emoji },
    properties: { 'Nome': title(nome), 'Marca': rel([U[unidade]]), 'Status': sel(status), 'Deadline': date(dl) },
  });
  P[nome] = p.id;
  console.log(`  ✓ ${emoji} ${nome}`);
}

// ═══ 6. tasks ═══
console.log('▸ 6/6 tasks...');
// [nome, unidade, projeto|null, status, deadline, parentKey|null, notas|null]
const TASKS = [
  // Cenário
  ['terminar cenário', 'Pessoal', 'Cenário', 'Iniciar', null, null],
  ['sacar betano', 'Pessoal', 'Cenário', 'Iniciar', null, 'terminar cenário'],
  ['cancelar vivo', 'Pessoal', 'Cenário', 'Iniciar', null, 'terminar cenário'],
  ['verificar tio/vó camiseta azul', 'Pessoal', 'Cenário', 'Iniciar', null, 'terminar cenário'],
  ['pegar minha jaqueta no Japa', 'Pessoal', 'Cenário', 'Iniciar', null, 'terminar cenário'],
  ['quadro jace mindsculpter', 'Pessoal', 'Cenário', 'Iniciar', null, 'terminar cenário'],
  ['desenho padrão parede', 'Pessoal', 'Cenário', 'Iniciar', null, 'terminar cenário'],
  // Life System 1.0
  ['Construir Compass 1.0', 'Pessoal', 'Construir Life System 1.0', 'Iniciar', null, null],
  ['Construir Trevvo 1.0', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, null],
  ['Construir Entelekkia 1.0', 'Entelekkia', 'Construir Life System 1.0', 'Iniciar', null, null],
  ['Patrimônio/Carteira', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, 'Construir Trevvo 1.0'],
  ['Contas a Pagar/Receber', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, 'Construir Trevvo 1.0'],
  ['Entradas/Saídas Mensal', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, 'Construir Trevvo 1.0'],
  ['Previsões/Projeções', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, 'Construir Trevvo 1.0'],
  ['Orçamento', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, 'Construir Trevvo 1.0'],
  ['Caixa Atual', 'Trevvo', 'Construir Life System 1.0', 'Iniciar', null, 'Construir Trevvo 1.0'],
  // Segundo Cérebro
  ['Curadoria dos livros ainda não lidos', 'Pessoal', 'Segundo Cérebro', 'Iniciar', null, null],
  ['Extração dos livros já lidos', 'Pessoal', 'Segundo Cérebro', 'Iniciar', null, null],
  ['Planejamento para construir 2C', 'Pessoal', 'Segundo Cérebro', 'Iniciar', null, null],
  ['Pesquisa para construir 2C', 'Pessoal', 'Segundo Cérebro', 'Finalizado', null, null],
  ['organizar arquivos segundo cérebro', 'Pessoal', 'Segundo Cérebro', 'Iniciar', null, null],
  // Markeologia avulsas
  ['conectar Chipak na operação', 'Markeologia', null, 'Iniciar', null, null],
  ['encerrar empresa atual ou mudar quadro', 'Markeologia', null, 'Iniciar', null, null],
  ['contratar um designer', 'Markeologia', null, 'Iniciar', null, null],
  ['montar organograma markeologia', 'Markeologia', null, 'Iniciar', null, null],
  ['revisitar material de consultoria Frank Kern', 'Markeologia', null, 'Iniciar', null, null],
  ['situação coworking', 'Markeologia', null, 'Iniciar', null, null],
  ['email cactus', 'Markeologia', null, 'Iniciar', null, null],
  ['Lançar Negócio', 'Markeologia', null, 'Iniciar', '2024-08-12', null],
  // Trevvo avulsas
  ['terminar orçamento', 'Trevvo', null, 'Iniciar', null, null],
  ['construção plano financeiro', 'Trevvo', null, 'Iniciar', null, null],
  ['construir a página trevvo 1.0', 'Trevvo', null, 'Iniciar', null, null],
  // Pessoal avulsas
  ['Falar com treinador Andre sobre a condição especial inbox', 'Pessoal', null, 'Iniciar', null, null],
  ['verificar contas ENEL e COMGÁS', 'Pessoal', null, 'Iniciar', null, null],
  ['tirar visto', 'Pessoal', null, 'Iniciar', null, null],
  ['tirar passaporte', 'Pessoal', null, 'Iniciar', null, null],
  ['trocar o óculos', 'Pessoal', null, 'Iniciar', null, null],
  ['comprar livros martins', 'Pessoal', null, 'Iniciar', null, null],
  ['mapeamento miss right e plano de atração', 'Pessoal', null, 'Iniciar', null, null],
  ['criar caderno de oração', 'Pessoal', null, 'Iniciar', null, null],
  ['compras Hezion', 'Pessoal', null, 'Iniciar', null, null],
  ['passar meus vídeos para canal yt', 'Pessoal', null, 'Iniciar', '2024-07-13', null, 'liberar espaço drive'],
  ['passar os favoritos pruma lista e limpar navegador', 'Pessoal', null, 'Iniciar', null, null],
  ['preparar para viajar ao exterior', 'Pessoal', null, 'Iniciar', null, null],
  ['falar com Douglas Dale Carnegie', 'Pessoal', null, 'Iniciar', null, null],
  ['terminar de traçar minhas metas', 'Pessoal', null, 'Iniciar', null, null],
  ['criação dos planos de desenvolvimento', 'Pessoal', null, 'Iniciar', null, null],
];

const T = {};
let n = 0;
for (const [nome, unidade, projeto, status, dl, parentKey, obs] of TASKS) {
  const props = {
    'Demanda': title(nome),
    'Marca': rel([U[unidade]]),
    'Responsável': multi(['Monegatto']),
    'Status': sel(status),
    'Deadline': date(dl),
  };
  if (projeto) props['Projeto'] = rel([P[projeto]]);
  if (parentKey && T[parentKey]) props['Subtarefa de'] = rel([T[parentKey]]);
  if (obs) props['Notas'] = { rich_text: txt(obs) };
  const p = await api('pages', { parent: { database_id: DB_TASKS }, properties: props });
  T[nome] = p.id;
  n++;
  if (n % 10 === 0) console.log(`  … ${n}/${TASKS.length}`);
}
console.log(`  ✓ ${n} tasks migradas`);

fs.writeFileSync(new URL('./notion-migrate-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ unidades: U, projetos: P, notasDb: notasDb.id }, null, 2));

console.log('\n✅ MIGRAÇÃO COMPLETA (aditiva — nada foi tocado nos sistemas antigos)');
console.log(`   Unidades: ${Object.keys(U).length} | Projetos novos: ${PROJS.length} | Tasks novas: ${n} | Notas: ${NOTAS.length}`);
console.log(`   📝 Notas: ${notasDb.url}`);
