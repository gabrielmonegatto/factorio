#!/usr/bin/env node
// LIMPEZA DO LEGADO — apaga (lixeira) os bancos antigos que foram FUNDIDOS na geração nova.
// NÃO toca: Habit Tracker, Navegação [2024], Alimentos e Suplementos, Desafio Stylelife, HeroLabz.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, body, method = 'POST') {
  await sleep(360);
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { ok: res.ok, json: await res.json() };
}

// alvos: [nome-legível, id completo OU fragmento de 8 chars pra resolver via search]
const ALVOS = [
  // — Life System: pirâmide velha (fundida em Metas / Projetos+Tasks)
  ['Polaris',                 '7a2c3f80-59ad-4eaa-879a-fad6662453e2'],
  ['Metas (velho)',           'bf45bcc1-e142-4c11-a4aa-09fd93bfdee3'],
  ['Projetos (velho)',        '65598cba-60f0-4be8-ae39-e98330bf5d7c'],
  ['Tarefas (velho)',         '47f4f8cf-eeb2-4ea8-81da-ee379207b3f4'],
  ['Calendar - [L.S.]',       '7ff914cb-7f1f-4d2e-ad79-7cb1b791281b'],
  // — gêmeas de navegação (fundidas no Notas, que o Gabriel já deletou)
  ['Compass [LifeSystem]',    'e4229177-5473-460f-9e6a-d67308b52494'],
  ['Trevvo [LifeSystem]',     '34d36861-fd0a-4cc3-8bcd-2380a5f27467'],
  ['Entelekkia [LifeSystem]', '1425b1d6-013b-49ad-bc8a-bba2aca05ca6'],
  ['Business [B.S.]',         '52ab8509-80de-4cbb-9255-2338591ee976'],
  ['Marketing [B.S.]',        'fd2007f8-e4e8-4991-936b-cfc0c818300a'],
  ['Operations [B.S.]',       '68e8ed2d-053d-472f-b9d2-7dff9d8a80fa'],
  ['Calendar [B.S.]',         '00cd93ac-7e86-41e3-9462-46f8e86d1f92'],
  // — template default do Notion no Newsystem (3 linhas vazias)
  ['Controle de tarefas',     '3a5f06f1-0ce3-80fd-b83f-da983677a2e2'],
  // — stack financeiro velho (fundido no Trevvo 1.0) — fragmentos, resolver via search
  ['Cartões',                 '55d158c9'],
  ['Patrimônio',              'add463d0'],
  ['Entradas',                '9ed2bec6'],
  ['Saídas',                  'bdb9db76'],
  ['Assinaturas',             '96fd69e8'],
  ['Transações Bancárias',    '33c87986'],
  ['Fontes de Receita',       '978f1574'],
  ['Categorias de Gastos',    '2b53913a'],
  ['Metas Financeiras',       '0a1122cc'],
  ['RF Contas V3',            '81cf2a9a'],
  ['RF Investimentos V3',     '04b8d261'],
  ['RF Operações V3',         'c7b7f3c5'],
  ['RV Contas V3',            '095fbdef'],
  ['RV Ativos V3',            '64c2ea48'],
  ['RV Operações V3',         'f11cf6c5'],
  ['Proventos RV V3',         'de4d3ad4'],
];

// resolve fragmentos via search paginado
console.log('▸ resolvendo ids via search...');
let cursor, dbs = [];
do {
  const { json: j } = await api('search', { filter: { value: 'database', property: 'object' }, page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
  dbs.push(...(j.results || []));
  cursor = j.has_more ? j.next_cursor : null;
} while (cursor);
console.log(`  ${dbs.length} bancos visíveis`);

let del = 0, naoAchou = [], falhou = [];
for (const [nome, idOrFrag] of ALVOS) {
  let full = idOrFrag;
  if (idOrFrag.length === 8) {
    const hit = dbs.find(d => d.id.replace(/-/g, '').startsWith(idOrFrag));
    if (!hit) { naoAchou.push(nome); console.log(`  ⚠️ não achei: ${nome} (${idOrFrag}) — pode já ter sido deletado`); continue; }
    full = hit.id;
  }
  const { ok, json } = await api(`blocks/${full}`, null, 'DELETE');
  if (ok) { del++; console.log(`  🗑️ ${nome}`); }
  else { falhou.push([nome, json.code]); console.log(`  ✗ ${nome}: ${json.code}`); }
}

console.log(`\n✅ ${del} bancos velhos apagados (lixeira do Notion — restauráveis por 30 dias)`);
if (naoAchou.length) console.log(`   já não existiam: ${naoAchou.join(', ')}`);
if (falhou.length) console.log(`   falharam: ${falhou.map(f => f.join(':')).join(', ')}`);
console.log('   preservados de propósito: Habit Tracker, Navegação [2024], Alimentos e Suplementos, Desafio Stylelife, HeroLabz');
