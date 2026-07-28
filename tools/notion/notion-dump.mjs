#!/usr/bin/env node
// Dump do conteúdo dos bancos que serão migrados (leitura, zero escrita)
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, method = 'GET', body) {
  await sleep(300);
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

async function rows(dbId) {
  let all = [], cursor;
  do {
    const j = await api(`databases/${dbId}/query`, 'POST', { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
    if (j.object === 'error') return { error: j.code };
    all.push(...j.results);
    cursor = j.has_more ? j.next_cursor : null;
  } while (cursor);
  return all;
}

const val = p => {
  switch (p.type) {
    case 'title': return p.title.map(t => t.plain_text).join('');
    case 'rich_text': return p.rich_text.map(t => t.plain_text).join('');
    case 'select': return p.select?.name ?? null;
    case 'status': return p.status?.name ?? null;
    case 'multi_select': return p.multi_select.map(o => o.name);
    case 'date': return p.date?.start ?? null;
    case 'people': return p.people.map(u => u.name || u.id);
    case 'relation': return p.relation.map(r => r.id);
    case 'checkbox': return p.checkbox;
    case 'number': return p.number;
    case 'created_time': return p.created_time;
    default: return undefined;
  }
};

const DBS = {
  'bs-business':   '52ab8509', 'bs-marketing': 'fd2007f8', 'bs-operations': '68e8ed2d',
  'ls-compass':    'e4229177', 'ls-trevvo':    '34d36861', 'ls-entelekkia': '1425b1d6',
  'bs-calendar':   '00cd93ac', 'ls-calendar':  '7ff914cb',
  'metas':         'bf45bcc1', 'projetos':     '65598cba', 'tarefas': '47f4f8cf',
  'polaris':       '7a2c3f80',
};
// ids completos via busca dos primeiros 8 chars não rola — preciso dos ids reais:
const FULL = {
  'bs-business':   '52ab8509-4dfa-4bfc-b117-3adca21458f5',
};

// resolve ids completos pelo mapa anterior — mais simples: query via search não;
// vou usar os ids que o walk já retornou (guardados abaixo à mão)
const IDS = {
  'bs-business':   '52ab8509', // placeholder
};

// -- na prática o endpoint aceita id sem hífens? Não — precisa do id completo.
// Então: pego os databases via search e caso o título bata, dumpo.
const wanted = [
  ['Business [B.S.]', 'nota'], ['Marketing [B.S.]', 'nota'], ['Operations [B.S.]', 'nota'],
  ['Compass [LifeSystem] ', 'nota'], ['Trevvo [LifeSystem]', 'nota'], ['Entelekkia [LifeSystem]', 'nota'],
  ['Calendar [B.S.]', 'cal'], ['Calendar - [L.S.]', 'cal'],
  ['Metas', 'metas'], ['Projetos', 'projetos'], ['Tarefas', 'tarefas'], ['Polaris', 'polaris'],
];

let cursor, dbs = [];
do {
  const j = await api('search', 'POST', { filter: { value: 'database', property: 'object' }, page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
  dbs.push(...j.results);
  cursor = j.has_more ? j.next_cursor : null;
} while (cursor);

const out = {};
for (const [name] of wanted) {
  const db = dbs.find(d => (d.title?.[0]?.plain_text || '').trim() === name.trim());
  if (!db) { console.log(`✗ não achei DB "${name}"`); continue; }
  const rs = await rows(db.id);
  if (rs.error) { console.log(`✗ ${name}: ${rs.error}`); continue; }
  out[name.trim()] = { id: db.id, rows: rs.map(r => {
    const o = { _id: r.id };
    for (const [k, p] of Object.entries(r.properties)) {
      const v = val(p);
      if (v !== undefined && v !== null && !(Array.isArray(v) && v.length === 0) && v !== '') o[k] = v;
    }
    return o;
  })};
  console.log(`✓ ${name.trim()}: ${rs.length} linhas  [${db.id}]`);
}

fs.writeFileSync(new URL('./notion-dump.json', import.meta.url).pathname.replace(/^\//, ''), JSON.stringify(out, null, 2));
console.log('\nsalvo em notion-dump.json');
