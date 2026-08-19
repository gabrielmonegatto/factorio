#!/usr/bin/env node
// Lê as tarefas e entregas de uma área no Notion (leitura pura, zero escrita).
// Usado pela skill /frente pra abrir sessão de área já sabendo o que fazer.
//
//   node tools/notion/notion-tarefas.mjs "Content"
//   node tools/notion/notion-tarefas.mjs            → resumo de todas as áreas

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const TOKEN = fs.readFileSync('C:/Users/Monegatto/Desktop/EternalL/_factorio/.env', 'utf8')
  .split(/\r?\n/).find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();
const ids = JSON.parse(fs.readFileSync(path.join(HERE, 'notion-fabrica-ids.json'), 'utf8'));
const TASKS_DB = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(p, method = 'GET', body) {
  await sleep(330);
  const res = await fetch(`https://api.notion.com/v1/${p}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}
const txt = p => (p?.title || p?.rich_text || []).map(t => t.plain_text).join('');
const tituloDe = pg => txt(Object.values(pg.properties).find(p => p.type === 'title'));
const sel = (pg, n) => pg.properties[n]?.select?.name || '';
const multi = (pg, n) => (pg.properties[n]?.multi_select || []).map(o => o.name).join(', ');
const rich = (pg, n) => txt(pg.properties[n]);

async function linhas(dbId, areaId) {
  const out = []; let cursor;
  do {
    const j = await api(`databases/${dbId}/query`, 'POST', {
      page_size: 100,
      ...(areaId ? { filter: { property: 'Área', relation: { contains: areaId } } } : {}),
      ...(cursor ? { start_cursor: cursor } : {}),
    });
    if (j.object === 'error') { console.error(`erro: ${j.code} ${j.message}`); break; }
    out.push(...(j.results || [])); cursor = j.has_more ? j.next_cursor : null;
  } while (cursor);
  return out;
}

const alvo = process.argv[2];
const areas = Object.keys(ids.rows).filter(n => !['longz', 'shortz'].includes(n));

if (!alvo) {
  console.log('Áreas disponíveis:', areas.join(' · '));
  console.log('\nResumo (tasks abertas por área):');
  for (const a of areas) {
    const t = await linhas(TASKS_DB, ids.rows[a]);
    const abertas = t.filter(x => sel(x, 'Status') !== 'Finalizado');
    const gates = abertas.filter(x => multi(x, 'Responsável').includes('Monegatto'));
    console.log(`  ${a.padEnd(26)} ${String(abertas.length).padStart(2)} abertas${gates.length ? `  (${gates.length} no gate do Gabriel)` : ''}`);
  }
  process.exit(0);
}

const nome = areas.find(a => a.toLowerCase() === alvo.toLowerCase())
  || areas.find(a => a.toLowerCase().includes(alvo.toLowerCase()));
if (!nome) { console.error(`Área "${alvo}" não existe. Opções: ${areas.join(' · ')}`); process.exit(1); }
const areaId = ids.rows[nome];

console.log(`\n${'='.repeat(64)}\nÁREA: ${nome}\n${'='.repeat(64)}`);

// O Gabriel manda no schema da tabela Áreas (ele renomeou "Norte 90 dias" → "Meta"
// e converteu Indicadores em texto em 19/08). Lemos com tolerância: nome novo, nome
// velho, e segue sem quebrar se a coluna não existir.
const area = await api(`pages/${areaId}`);
const primeiro = (pg, ...nomes) => { for (const n of nomes) { const v = rich(pg, n); if (v) return v; } return ''; };
console.log(`Missão: ${primeiro(area, 'Missão')}`);
console.log(`Meta: ${primeiro(area, 'Meta', 'Norte 90 dias')}`);
const frente = primeiro(area, 'Frente');
console.log(`Status: ${sel(area, 'Status')}${frente ? ` · Frente: ${frente}` : ' · território: ver docs/16_BLUEPRINT_AREAS.md §6'}`);

const roadmap = await linhas(ids.dbRoadmap, areaId);
console.log(`\n── ROADMAP (${roadmap.length}) ──`);
for (const onda of ['W0 Ligar', 'W1 Consistência', 'W2 Escala']) {
  const daOnda = roadmap.filter(r => sel(r, 'Onda') === onda);
  if (!daOnda.length) continue;
  console.log(`\n  ${onda}`);
  for (const r of daOnda) {
    const st = sel(r, 'Status'), gate = sel(r, 'Gate');
    const marca = st === 'Entregue' ? '✅' : st === 'Aguardando gate' ? '🚦' : st === 'Em construção' ? '🔨' : '⬜';
    const d = rich(r, 'Detalhe');
    console.log(`   ${marca} ${tituloDe(r)}${gate !== 'Nenhum' && gate ? ` [gate: ${gate}]` : ''}`);
    if (d) console.log(`      ${d.slice(0, 150)}`);
  }
}

const tasks = await linhas(TASKS_DB, areaId);
const abertas = tasks.filter(t => sel(t, 'Status') !== 'Finalizado');
console.log(`\n── TASKS ABERTAS (${abertas.length} de ${tasks.length}) ──`);
for (const t of abertas) {
  const resp = multi(t, 'Responsável');
  const meu = resp.includes('Monegatto') ? '🚦 GABRIEL' : '🤖';
  console.log(`   ${meu} ${tituloDe(t)}`);
  const n = rich(t, 'Notas');
  if (n) console.log(`      ${n.slice(0, 140)}`);
}

const esteiras = await linhas(ids.dbEsteiras, areaId);
if (esteiras.length) {
  console.log(`\n── ESTEIRAS (${esteiras.length}) ──`);
  for (const e of esteiras) console.log(`   ${sel(e, 'Status').padEnd(14)} ${tituloDe(e).padEnd(34)} ${rich(e, 'Código')}`);
}

const inds = await linhas(ids.dbIndicadores, areaId);
if (inds.length) {
  console.log(`\n── INDICADORES (${inds.length}) ──`);
  for (const i of inds) {
    const v = rich(i, 'Valor atual');
    console.log(`   ${tituloDe(i).padEnd(38)} ${v || '(sem medição)'}`);
  }
}
console.log();
