#!/usr/bin/env node
// Mapeia a árvore de páginas/databases dos sistemas do Notion (estrutura, não conteúdo)
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, method = 'GET', body) {
  for (let tent = 1; ; tent++) {
    await sleep(300);
    try {
      const res = await fetch(`https://api.notion.com/v1/${path}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      return res.json();
    } catch (e) {
      if (tent >= 4) throw e;
      console.log(`   (rede falhou, retry ${tent}/3 em ${tent * 3}s...)`);
      await sleep(tent * 3000);
    }
  }
}

async function children(blockId) {
  let all = [], cursor;
  do {
    const j = await api(`blocks/${blockId}/children?page_size=100${cursor ? `&start_cursor=${cursor}` : ''}`);
    if (j.object === 'error') { console.log(`   [erro: ${j.code}]`); return all; }
    all.push(...(j.results || []));
    cursor = j.has_more ? j.next_cursor : null;
  } while (cursor);
  return all;
}

function dbSummary(db) {
  const props = Object.entries(db.properties || {}).map(([name, p]) => {
    let extra = '';
    if (p.type === 'select' || p.type === 'multi_select')
      extra = `(${(p[p.type].options || []).map(o => o.name).slice(0, 8).join('|')})`;
    if (p.type === 'relation') extra = `→db:${(p.relation.database_id || '').slice(0, 8)}`;
    if (p.type === 'rollup') extra = `(rollup)`;
    if (p.type === 'formula') extra = `(formula)`;
    if (p.type === 'status') extra = `(${(p.status.options||[]).map(o=>o.name).join('|')})`;
    return `${name}:${p.type}${extra}`;
  });
  return props;
}

async function dbRowCount(dbId) {
  const j = await api(`databases/${dbId}/query`, 'POST', { page_size: 100 });
  if (j.object === 'error') return '?';
  return j.has_more ? `${j.results.length}+` : `${j.results.length}`;
}

async function walk(id, type, name, depth, maxDepth) {
  const pad = '  '.repeat(depth);
  if (type === 'database') {
    const db = await api(`databases/${id}`);
    if (db.object === 'error') { console.log(`${pad}🗄️ ${name} [inacessivel: ${db.code}]`); return; }
    const rows = await dbRowCount(id);
    console.log(`${pad}🗄️ DB: ${name}  (${rows} linhas, ${db.is_inline ? 'inline' : 'full-page'})  [${id.slice(0,8)}]`);
    for (const p of dbSummary(db)) console.log(`${pad}    · ${p}`);
    return;
  }
  console.log(`${pad}📄 ${name}  [${id.slice(0,8)}]`);
  if (depth >= maxDepth) return;
  await walkBlocks(id, depth, maxDepth);
}

// recursa em QUALQUER bloco-container (coluna, callout, toggle, synced...)
async function walkBlocks(blockId, depth, maxDepth) {
  const pad = '  '.repeat(depth);
  const kids = await children(blockId);
  for (const k of kids) {
    if (k.type === 'child_page') await walk(k.id, 'page', k.child_page.title, depth + 1, maxDepth);
    else if (k.type === 'child_database') await walk(k.id, 'database', k.child_database.title || '(sem titulo)', depth + 1, maxDepth);
    else if (k.type === 'link_to_page') {
      const tid = k.link_to_page.page_id || k.link_to_page.database_id;
      console.log(`${pad}  🔗 link_to_page → ${(tid||'').slice(0,8)}`);
    } else if (k.type === 'unsupported') {
      console.log(`${pad}  ⚠️ bloco unsupported (provável linked-view) [${k.id.slice(0,8)}]`);
    } else if (k.has_children) {
      console.log(`${pad}  ▾ ${k.type}`);
      await walkBlocks(k.id, depth + 1, maxDepth);
    }
  }
}

const ROOTS = [
  ['3aaf06f1-0ce3-8095-a189-db00bb8e9bba', 'modeling'],
];

for (const [id, name] of ROOTS) {
  console.log(`\n${'='.repeat(70)}\n${name}\n${'='.repeat(70)}`);
  await walk(id, 'page', name, 0, 4);
}
console.log('\nfim.');
