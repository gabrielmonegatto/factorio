#!/usr/bin/env node
// Levanta a estrutura de 3 bancos (Marcas / Projetos / Tasks) no Notion
// e popula a unidade BLUUE como piloto.
//
// Estrutura como CÓDIGO: rodar de novo em outro workspace recria tudo
// com as relations intactas (resolve o problema de relation quebrar na migração).

import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const PARENT_PAGE = '3a5f06f1-0ce3-80c3-9b15-c486acb05b67'; // página BS2
const OUT = new URL('./notion-ids.json', import.meta.url).pathname.replace(/^\//, '');

const TOKEN = fs.readFileSync(ENV, 'utf8')
  .split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN='))
  .slice('NOTION_TOKEN='.length)
  .trim();

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function api(path, body, method = 'POST') {
  await sleep(360); // rate limit do Notion ~3 req/s
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) {
    console.error(`\n✗ ${method} ${path}\n`, JSON.stringify(json, null, 2));
    throw new Error(json.message || 'erro na API');
  }
  return json;
}

const txt = content => [{ type: 'text', text: { content } }];
const title = content => ({ title: txt(content) });
const sel = name => (name ? { select: { name } } : { select: null });
const date = d => (d ? { date: { start: d } } : { date: null });
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const multi = names => ({ multi_select: names.map(name => ({ name })) });

const STATUS_OPTS = [
  { name: 'Iniciar', color: 'gray' },
  { name: 'Em andamento', color: 'blue' },
  { name: 'Finalizado', color: 'green' },
];

const PESSOAS = [
  ['Monegatto', 'purple'], ['Bruno', 'blue'], ['Bruno Web', 'green'],
  ['Alma', 'pink'], ['Rafa', 'orange'], ['Mota', 'yellow'],
  ['Natã', 'brown'], ['Japa', 'red'], ['Givas', 'default'],
  ['Garrido', 'blue'], ['Almeida', 'green'], ['Quantum', 'purple'], ['Time', 'gray'],
].map(([name, color]) => ({ name, color }));

// ─────────────────────────────────────────────────────────── dados do board BLUUE

const FRENTES = [
  { nome: 'Máquina de Criativos', emoji: '🎨', tasks: [
    ['Desenho do processo de gestão', ['Bruno'], 'Em andamento', '2026-07-24'],
    ['Encerramento do contrato do Jerry (copy)', ['Bruno'], 'Iniciar', '2026-07-24'],
    ['Aprovação com o Juans (editor)', ['Bruno'], 'Iniciar', '2026-07-24'],
    ['Alinhamento entre o time envolvido dos processos', ['Bruno', 'Time'], 'Iniciar', '2026-07-28'],
    ['Organização da nuvem de criativos', ['Bruno', 'Monegatto', 'Rafa'], 'Iniciar', '2026-07-28'],
  ]},
  { nome: 'Estrutura Alternativa de Performance', emoji: '📈', tasks: [
    ['Safe page', ['Bruno Web', 'Monegatto'], 'Finalizado', null],
    ['Teste popcicle', ['Mota', 'Rafa'], 'Em andamento', '2026-07-31'],
    ['Teste Monegatto campanhas (initiate checkout)', ['Monegatto', 'Rafa'], 'Em andamento', '2026-07-27'],
    ['Teste Monegatto campanhas (compra)', ['Monegatto', 'Alma', 'Bruno Web'], 'Em andamento', '2026-07-27'],
    ['Validação final / migração estrutura', ['Mota', 'Monegatto', 'Rafa'], 'Iniciar', '2026-07-31'],
  ]},
  { nome: 'Estrutura de Back-end', emoji: '🛠️', tasks: [
    ['Call com o Vilmárc (estrutura de e-mail paralela)', ['Monegatto', 'Natã'], 'Em andamento', '2026-07-29'],
    ['Otimização Quantum - plano', ['Alma', 'Natã', 'Quantum'], 'Iniciar', '2026-07-24'],
    ['Link: UTM conversão de e-mail', ['Alma', 'Quantum'], 'Em andamento', '2026-07-24'],
    ['Revisão da estrutura Revi', ['Monegatto', 'Natã'], 'Iniciar', '2026-07-24'],
    ['Copys Revi', ['Monegatto', 'Natã'], 'Iniciar', '2026-07-24'],
  ]},
  { nome: 'Texto Bluue', emoji: '✍️', tasks: [
    ['Revisão da estrutura atual / comparação Mars', ['Monegatto', 'Alma', 'Bruno'], 'Iniciar', '2026-07-31'],
    ['Otimização de design system', ['Alma', 'Bruno Web', 'Japa'], 'Iniciar', '2026-07-31'],
    ['Cabeamento / estrutura de trackeamento', ['Bruno Web'], 'Iniciar', '2026-07-31'],
    ['B4You - checkout / orderbump', ['Alma', 'Bruno Web'], 'Iniciar', '2026-07-31'],
    ['LP - upsell pastilha Bluue', ['Monegatto', 'Alma', 'Bruno Web'], 'Iniciar', '2026-07-31'],
    ['Leva de criativos - copy', ['Monegatto'], 'Iniciar', '2026-07-31'],
    ['Leva de criativos - imagem', ['Japa'], 'Iniciar', '2026-07-31'],
    ['Leva de criativos - produção e edição', ['Mota', 'Givas'], 'Iniciar', '2026-07-31'],
  ]},
  { nome: 'Estrutura de Remarketing — Pastilha', emoji: '🔁', tasks: [
    ['Advertorial X passos - copy', ['Monegatto', 'Alma', 'Bruno'], 'Iniciar', '2026-07-31'],
    ['Advertorial X passos - design & web', ['Bruno Web', 'Japa'], 'Iniciar', '2026-07-31'],
    ['Revisão estrutura', ['Alma'], 'Iniciar', '2026-07-31'],
    ['Ciclo de teste - tráfego', ['Rafa'], 'Iniciar', '2026-07-31'],
  ]},
  { nome: 'Canal de Influenciadores', emoji: '📣', tasks: [
    ['Funil específico', ['Monegatto', 'Bruno Web', 'Alma', 'Bruno'], 'Finalizado', null],
    ['Direcionamento de CTAs', ['Bruno'], 'Finalizado', null],
    ['Processo de armazenamento de criativos', ['Garrido', 'Alma'], 'Iniciar', '2026-07-24'],
    ['Processo de campanha na conta do influencer', ['Rafa', 'Garrido', 'Alma'], 'Iniciar', '2026-07-24'],
  ]},
  { nome: 'Dashboard e Controle de Dados', emoji: '📊', tasks: [
    ['Documento do KPIs e métricas', ['Bruno'], 'Finalizado', null],
    ['Estrutura de dados', ['Bruno Web', 'Monegatto'], 'Em andamento', null],
    ['Dashboard conectada com as fontes', ['Bruno Web'], 'Iniciar', '2026-07-31'],
  ]},
  { nome: 'Processo Semanal de Análise de Performance', emoji: '🗓️', tasks: [
    ['Call growth / terça', ['Bruno', 'Monegatto'], 'Finalizado', null],
    ['Modelo de relatório dados tráfego / vendas', ['Rafa'], 'Em andamento', '2026-07-28'],
    ['Modelo de relatório dados comportamento funil', ['Monegatto', 'Alma'], 'Em andamento', null],
    ['Preenchimento da planilha de backlog', ['Alma'], 'Finalizado', null],
  ]},
  { nome: 'Otimização Up Sell — Pastilha', emoji: '💰', tasks: [
    ['Análise da VSL atual', ['Monegatto'], 'Iniciar', null],
    ['Escrever nova copy da VSL de upsell', ['Monegatto'], 'Iniciar', null],
    ['Gravação da VSL', ['Monegatto', 'Garrido'], 'Iniciar', null],
    ['Edição da VSL', ['Givas'], 'Iniciar', null],
    ['Implementação web / VSL', ['Bruno Web'], 'Iniciar', null],
    ['Revisão da oferta', ['Almeida'], 'Iniciar', null],
  ]},
  { nome: 'Site / Adequações Jurídico', emoji: '⚖️', tasks: [
    ['Call de alinhamento e checklist execuções', ['Alma', 'Bruno Web', 'Garrido'], 'Iniciar', '2026-07-27'],
    ['Implementação dos ajustes', ['Alma', 'Bruno Web', 'Garrido'], 'Iniciar', '2026-07-27'],
  ]},
];

// status/deadline do projeto derivados das tasks
const derive = tasks => {
  const st = tasks.map(t => t[2]);
  const status = st.every(s => s === 'Finalizado') ? 'Finalizado'
    : st.some(s => s === 'Em andamento') ? 'Em andamento' : 'Iniciar';
  const ds = tasks.map(t => t[3]).filter(Boolean).sort();
  return { status, deadline: ds.length ? ds[ds.length - 1] : null };
};

// ─────────────────────────────────────────────────────────── build

console.log('▸ criando banco 🏢 Marcas...');
const marcas = await api('databases', {
  parent: { type: 'page_id', page_id: PARENT_PAGE },
  icon: { type: 'emoji', emoji: '🏢' },
  title: txt('🏢 Marcas'),
  description: txt('Índice mestre de marcas e unidades de negócio.'),
  properties: {
    'Nome': { title: {} },
    'Tipo': { select: { options: [
      { name: 'Cliente', color: 'blue' },
      { name: 'Própria', color: 'green' },
      { name: 'Interno', color: 'gray' },
    ]}},
    'Status': { select: { options: [
      { name: 'Ativa', color: 'green' },
      { name: 'Pausada', color: 'yellow' },
      { name: 'Encerrada', color: 'red' },
    ]}},
    'Notas': { rich_text: {} },
  },
});
console.log(`  ✓ ${marcas.id}`);

console.log('▸ criando banco 📁 Projetos...');
const projetos = await api('databases', {
  parent: { type: 'page_id', page_id: PARENT_PAGE },
  icon: { type: 'emoji', emoji: '📁' },
  title: txt('📁 Projetos'),
  description: txt('Frentes de trabalho, sempre atreladas a uma marca.'),
  properties: {
    'Nome': { title: {} },
    'Marca': { relation: { database_id: marcas.id, type: 'dual_property', dual_property: {} } },
    'Status': { select: { options: STATUS_OPTS } },
    'Deadline': { date: {} },
    'Notas': { rich_text: {} },
  },
});
console.log(`  ✓ ${projetos.id}`);

console.log('▸ criando banco ✅ Tasks...');
const tasks = await api('databases', {
  parent: { type: 'page_id', page_id: PARENT_PAGE },
  icon: { type: 'emoji', emoji: '✅' },
  title: txt('✅ Tasks'),
  description: txt('Demandas. Ligadas a um projeto — ou avulsas, ligadas direto à marca.'),
  properties: {
    'Demanda': { title: {} },
    'Projeto': { relation: { database_id: projetos.id, type: 'dual_property', dual_property: {} } },
    'Marca': { relation: { database_id: marcas.id, type: 'dual_property', dual_property: {} } },
    'Responsável': { multi_select: { options: PESSOAS } },
    'Status': { select: { options: STATUS_OPTS } },
    'Deadline': { date: {} },
  },
});
console.log(`  ✓ ${tasks.id}`);

// ── popular BLUUE
console.log('\n▸ criando marca BLUUE...');
const bluue = await api('pages', {
  parent: { database_id: marcas.id },
  icon: { type: 'emoji', emoji: '💧' },
  properties: {
    'Nome': title('BLUUE'),
    'Tipo': sel('Cliente'),
    'Status': sel('Ativa'),
    'Notas': { rich_text: txt('Piloto — board migrado da planilha em 23/07/2026.') },
  },
});
console.log(`  ✓ ${bluue.id}`);

let nTasks = 0;
for (const f of FRENTES) {
  const d = derive(f.tasks);
  const proj = await api('pages', {
    parent: { database_id: projetos.id },
    icon: { type: 'emoji', emoji: f.emoji },
    properties: {
      'Nome': title(f.nome),
      'Marca': rel([bluue.id]),
      'Status': sel(d.status),
      'Deadline': date(d.deadline),
    },
  });
  console.log(`▸ ${f.emoji} ${f.nome}`);

  for (const [demanda, resp, status, dl] of f.tasks) {
    await api('pages', {
      parent: { database_id: tasks.id },
      properties: {
        'Demanda': title(demanda),
        'Projeto': rel([proj.id]),
        'Marca': rel([bluue.id]),
        'Responsável': multi(resp),
        'Status': sel(status),
        'Deadline': date(dl),
      },
    });
    nTasks++;
    console.log(`    · ${demanda}`);
  }
}

fs.writeFileSync(OUT, JSON.stringify({
  parent_page: PARENT_PAGE,
  databases: { marcas: marcas.id, projetos: projetos.id, tasks: tasks.id },
  marcas: { BLUUE: bluue.id },
}, null, 2));

console.log(`\n✅ pronto — 3 bancos, 1 marca, ${FRENTES.length} projetos, ${nTasks} tasks`);
console.log(`   ids salvos em ${OUT}`);
console.log(`   Marcas:   ${marcas.url}`);
console.log(`   Projetos: ${projetos.url}`);
console.log(`   Tasks:    ${tasks.url}`);
