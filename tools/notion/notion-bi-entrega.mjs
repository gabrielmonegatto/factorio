#!/usr/bin/env node
// Registra no Notion a entrega do painel bi.mananciall.org (19/08/2026, noite)
// e os handoffs da transição Notion → D1 biblioteca. Idempotente por título.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const TOKEN = fs.readFileSync('C:/Users/Monegatto/Desktop/EternalL/_factorio/.env', 'utf8')
  .split(/\r?\n/).find((l) => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();
const ids = JSON.parse(fs.readFileSync(path.join(HERE, 'notion-fabrica-ids.json'), 'utf8'));
const TASKS_DB = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function api(p, m = 'GET', b) {
  await sleep(330);
  const r = await fetch(`https://api.notion.com/v1/${p}`, {
    method: m,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: b ? JSON.stringify(b) : undefined,
  });
  return r.json();
}
const rt = (s) => [{ type: 'text', text: { content: s } }];
const tituloDe = (pg) => { const t = Object.values(pg.properties).find((p) => p.type === 'title'); return (t?.title || []).map((x) => x.plain_text).join(''); };
async function todas(dbId) {
  const out = []; let c;
  do { const j = await api(`databases/${dbId}/query`, 'POST', { page_size: 100, ...(c ? { start_cursor: c } : {}) }); out.push(...(j.results || [])); c = j.has_more ? j.next_cursor : null; } while (c);
  return out;
}

// ——— Roadmap ———
const rd = await todas(ids.dbRoadmap);
const rdPor = Object.fromEntries(rd.map((l) => [tituloDe(l), l]));
const alvo = rdPor['Repo mananciall-bi no ar (padrão Br4nds)'];
if (alvo) {
  await api(`pages/${alvo.id}`, 'PATCH', { properties: {
    Status: { select: { name: 'Entregue' } },
    Detalhe: { rich_text: rt('bi.mananciall.org NO AR 19/08 (Worker + React, tema Vercel): 7 tabelas, views salvas, filtros, board, edição inline auditada. Repo apps/eternall/mananciall-bi') },
  } });
  console.log('✓ roadmap: mananciall-bi entregue');
}
const NOVAS_RD = [
  ['Inteligência do Negócio', 'W1 Consistência', 'Entregue', 'Nenhum', 'Painel editável no ar: Biblioteca no BI (202 obras)', 'Tabela biblioteca criada no D1 e semeada do Notion; edição de curadoria com auditoria (bi_edicoes)'],
  ['Mineração', 'W1 Consistência', 'Pronta', 'Nenhum', 'Repontar queue.mjs: plano lido da biblioteca (D1), não do Notion', 'Handoff da transição; tabela pronta no mananciall-db'],
  ['Productz', 'W1 Consistência', 'Pronta', 'Nenhum', 'sync do site escreve campos de máquina na biblioteca (D1)', 'slug/capítulos/faixas/sincronizado; espelho pro Notion vira opcional'],
  ['Inteligência do Negócio', 'W1 Consistência', 'Aguardando gate', 'Gabriel', 'GATE: validar bi.mananciall.org e aposentar a Biblioteca do Notion', 'Usar o painel por ~2 semanas; validou, o banco do Notion vira [APOSENTADO]'],
];
for (const [area, onda, status, gate, entrega, detalhe] of NOVAS_RD) {
  if (rdPor[entrega]) continue;
  await api('pages', 'POST', { parent: { database_id: ids.dbRoadmap }, properties: {
    Entrega: { title: rt(entrega) },
    'Área': { relation: [{ id: ids.rows[area] }] },
    Onda: { select: { name: onda } },
    Status: { select: { name: status } },
    Gate: { select: { name: gate } },
    Detalhe: { rich_text: rt(detalhe) },
  } });
  console.log(`+ roadmap: ${entrega.slice(0, 55)}`);
}

// ——— Tasks ———
const ts = await todas(TASKS_DB);
const tsPor = Object.fromEntries(ts.map((l) => [tituloDe(l), l]));
const FECHAR = ['Construir scripts/bi/snapshot.mjs + 1ª rodada conferida'];
for (const t of FECHAR) {
  if (!tsPor[t]) continue;
  await api(`pages/${tsPor[t].id}`, 'PATCH', { properties: { Status: { select: { name: 'Finalizado' } } } });
  console.log(`✓ task fechada: ${t.slice(0, 50)}`);
}
const NOVAS_TS = [
  ['Repontar mining/queue.mjs pro D1 biblioteca', 'Mineração', ['Claude'], 'O plano agora mora na tabela biblioteca do mananciall-db (editada em bi.mananciall.org)'],
  ['sync-notion do site → escrever campos de máquina na biblioteca (D1)', 'Productz', ['Claude'], 'slug, capítulos, faixas, sincronizado; Notion vira espelho opcional'],
  ['GATE: validar bi.mananciall.org (usar 2 semanas) e aposentar Biblioteca do Notion', 'Inteligência do Negócio', ['Monegatto'], 'Senha = a do superadmin do site. Edição já auditada em bi_edicoes'],
];
for (const [demanda, area, resp, notas] of NOVAS_TS) {
  if (tsPor[demanda]) continue;
  await api('pages', 'POST', { parent: { database_id: TASKS_DB }, properties: {
    Demanda: { title: rt(demanda) },
    Status: { select: { name: 'Iniciar' } },
    'Responsável': { multi_select: resp.map((name) => ({ name })) },
    'Área': { relation: [{ id: ids.rows[area] }] },
    Notas: { rich_text: rt(notas) },
  } });
  console.log(`+ task: ${demanda.slice(0, 55)}`);
}

// ——— nota no hub ———
if (!ids.notaBi) {
  await api(`blocks/${ids.hubPage}/children`, 'PATCH', { children: [
    { callout: { icon: { type: 'emoji', emoji: '📊' }, rich_text: rt(
      'BI NO AR (19/08, noite): bi.mananciall.org — tabelas estilo Notion sobre os D1, com views salvas, filtros, board e edição inline auditada. Senha = a do superadmin do site. Primeira tela: Biblioteca (202 obras). Quando você validar, a Biblioteca do Notion aposenta e acaba o cérebro dividido.'
    ) } },
  ] });
  ids.notaBi = true;
  fs.writeFileSync(path.join(HERE, 'notion-fabrica-ids.json'), JSON.stringify(ids, null, 2));
  console.log('✓ nota no hub');
}
console.log('fim.');
