#!/usr/bin/env node
// PLAYBOOKS + EXPERIMENTOS — absorve o ouro da página modeling pro Business System.
// 1) Playbooks: checklist-mestre (57 etapas do "Implementação" do Template Perpétuo Lucrativo)
// 2) Experimentos: framework ICE de growth (adaptado do Growth Experimentation Sheet)
// Aditivo: originais da modeling ficam intactos.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const BS_PAGE = '33d6bf27-9f65-4043-8a5d-c53fe0b241a3';
const DB_UNIDADES = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';
const FRAG_IMPL = '34af06f1';

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
    } catch (e) {
      if (t >= 4 || e.message !== 'fetch failed') throw e;
      console.log(`   (rede, retry ${t}/3...)`); await sleep(t * 3000);
    }
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
const title = c => ({ title: txt(c) });
const sel = n => ({ select: { name: n } });
const rel = ids => ({ relation: ids.map(id => ({ id })) });

// ═══ 1-3. Playbooks já criado e populado na 1ª execução ═══
const pb = { id: '3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2', url: 'https://app.notion.com/p/3aaf06f10ce381f0b2ddcf47760bd1b2' };
console.log('▸ 1-3/5 Playbooks já pronto (57 etapas), retomando...');

// ═══ 4. criar Experimentos (ICE) ═══
console.log('▸ 4/5 criando banco Experimentos...');
const exp = await api('databases', {
  parent: { type: 'page_id', page_id: BS_PAGE },
  icon: DB_ICON,
  title: txt('Experimentos'),
  description: txt('Experimentos de growth/CRO com priorização ICE. Adaptado do Growth Experimentation Sheet.'),
  properties: {
    'Nome': { title: {} },
    'Marca': { relation: { database_id: DB_UNIDADES, type: 'dual_property', dual_property: {} } },
    'Status': { select: { options: [
      { name: 'Não iniciado', color: 'gray' }, { name: 'Preparando', color: 'yellow' },
      { name: 'Pronto', color: 'purple' }, { name: 'Rodando', color: 'blue' }, { name: 'Concluído', color: 'green' },
    ]}},
    'Alavanca': { select: { options: [
      { name: 'Awareness', color: 'gray' }, { name: 'Acquisition', color: 'orange' },
      { name: 'Activation', color: 'yellow' }, { name: 'Retention', color: 'green' },
      { name: 'Revenue', color: 'blue' }, { name: 'Referral', color: 'purple' },
    ]}},
    'Métrica': { select: { options: [
      { name: 'Impressões', color: 'gray' }, { name: 'Conversões', color: 'green' },
      { name: 'CTR', color: 'blue' }, { name: 'Ticket', color: 'yellow' }, { name: 'Indicações', color: 'purple' },
    ]}},
    'Impact (1-10)': { number: {} },
    'Confidence (1-10)': { number: {} },
    'Ease (1-10)': { number: {} },
    'ICE': { formula: { expression:
      '(if(empty(prop("Impact (1-10)")), 0, prop("Impact (1-10)")) + if(empty(prop("Confidence (1-10)")), 0, prop("Confidence (1-10)")) + if(empty(prop("Ease (1-10)")), 0, prop("Ease (1-10)"))) / 3' } },
    'KPI inicial': { number: {} },
    'KPI alvo': { number: {} },
    'KPI final': { number: {} },
    'Resultado %': { formula: { expression:
      'if(or(or(empty(prop("KPI inicial")), prop("KPI inicial") == 0), empty(prop("KPI final"))), 0, (prop("KPI final") - prop("KPI inicial")) / prop("KPI inicial") * 100)' } },
    'Veredito': { select: { options: [
      { name: 'Winner 🏆', color: 'green' }, { name: 'Inconclusivo', color: 'gray' }, { name: 'Loser', color: 'red' },
    ]}},
    'Início': { date: {} },
    'Fim': { date: {} },
    'URL': { url: {} },
  },
});
console.log(`  ✓ ${exp.id}`);

// ═══ 5. verificação ═══
console.log('▸ 5/5 verificando...');
const check = await api(`databases/${pb.id}/query`, { page_size: 100 });
const comArea = check.results.filter(r => r.properties['Área'].multi_select.length).length;
console.log(`  Playbooks: ${check.results.length} etapas (${comArea} com área)`);

fs.writeFileSync(new URL('./notion-playbooks-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ playbooks: pb.id, experimentos: exp.id }, null, 2));
console.log(`\n✅ pronto`);
console.log(`   Playbooks:    ${pb.url}`);
console.log(`   Experimentos: ${exp.url}`);
