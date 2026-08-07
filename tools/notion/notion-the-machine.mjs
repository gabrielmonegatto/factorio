#!/usr/bin/env node
// THE MACHINE — sobe os emails da Bluue pro Notion.
// 1 linha = 1 email. Campanhas multi-email são explodidas em linhas separadas.
// Corpo do email vai como conteúdo da página.
import fs from 'node:fs';
import path from 'node:path';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const SRC = 'C:/Users/Monegatto/Desktop/EternalL/apps/br4nds/_wiki/Bluue/emails';
const BS_PAGE = '33d6bf27-9f65-4043-8a5d-c53fe0b241a3';
const DB_UNIDADES = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';
const DB_ICON = { type: 'external', external: { url: 'https://www.notion.so/icons/database_green.svg' } };

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(pathUrl, body, method = 'POST') {
  for (let t = 1; ; t++) {
    await sleep(360);
    try {
      const res = await fetch(`https://api.notion.com/v1/${pathUrl}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const json = await res.json();
      if (!res.ok) { console.error(`✗ ${method} ${pathUrl}:`, JSON.stringify(json).slice(0, 400)); throw new Error(json.message); }
      return json;
    } catch (e) { if (t >= 4 || e.message !== 'fetch failed') throw e; await sleep(t * 3000); }
  }
}

// ── markdown mínimo → rich text (negrito) ──────────────────────────────
function rt(texto) {
  const out = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0, m;
  while ((m = re.exec(texto))) {
    if (m.index > last) out.push({ type: 'text', text: { content: texto.slice(last, m.index) } });
    out.push({ type: 'text', text: { content: m[1] }, annotations: { bold: true } });
    last = m.index + m[0].length;
  }
  if (last < texto.length) out.push({ type: 'text', text: { content: texto.slice(last) } });
  return out.length ? out.map(r => ({ ...r, text: { ...r.text, content: r.text.content.slice(0, 2000) } })) : [{ type: 'text', text: { content: '' } }];
}

// ── markdown → blocos do Notion ────────────────────────────────────────
function blocos(md) {
  const out = [];
  for (const linha of md.split(/\r?\n/)) {
    const l = linha.trim();
    if (!l) continue;
    if (l === '---') { out.push({ object: 'block', type: 'divider', divider: {} }); continue; }
    let m;
    if ((m = l.match(/^###\s+(.*)/))) { out.push({ object: 'block', type: 'heading_3', heading_3: { rich_text: rt(m[1]) } }); continue; }
    if ((m = l.match(/^##\s+(.*)/)))  { out.push({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(m[1]) } }); continue; }
    if ((m = l.match(/^#\s+(.*)/)))   { out.push({ object: 'block', type: 'heading_2', heading_2: { rich_text: rt(m[1]) } }); continue; }
    if ((m = l.match(/^[-*]\s+(.*)/))) { out.push({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(m[1]) } }); continue; }
    if ((m = l.match(/^(\d+)\.\s+(.*)/))) { out.push({ object: 'block', type: 'numbered_list_item', numbered_list_item: { rich_text: rt(m[2]) } }); continue; }
    out.push({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(l) } });
  }
  return out.slice(0, 100); // limite da API por request
}

// ── nomes bonitos a partir do slug ─────────────────────────────────────
const MIN = new Set(['de', 'da', 'do', 'e', 'a', 'o', 'na', 'no', 'em', 'pos', 'nao', 'se']);
const titulo = s => s.split(/[-_]/).filter(Boolean)
  .map((w, i) => (i > 0 && MIN.has(w.toLowerCase())) ? w.toLowerCase() : w.charAt(0).toUpperCase() + w.slice(1))
  .join(' ');

const ESTAGIOS = {
  segmentacao:   { nome: 'Segmentação',   cor: 'orange' },
  doutrinacao:   { nome: 'Doutrinação',   cor: 'yellow' },
  conversao:     { nome: 'Conversão',     cor: 'blue' },
  ascensao:      { nome: 'Ascensão',      cor: 'green' },
  reengajamento: { nome: 'Reengajamento', cor: 'purple' },
};

// ── parse dos arquivos ─────────────────────────────────────────────────
const registros = [];
for (const est of Object.keys(ESTAGIOS)) {
  const dir = path.join(SRC, est);
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.md')).sort()) {
    const raw = fs.readFileSync(path.join(dir, f), 'utf8');
    const slug = f.replace(/\.md$/, '');
    const ehMeta = /^(READY|00-)/i.test(slug);

    // campanha + produto
    let campanha, produto = null, ordemArq = null;
    let m;
    if ((m = slug.match(/^(fm2em1|testo)_(.+)$/))) {
      produto = m[1] === 'fm2em1' ? 'FM 2em1' : 'Testo';
      campanha = produto;
    } else if ((m = slug.match(/^(\d+)-(.+)$/))) {
      ordemArq = parseInt(m[1], 10);
      campanha = titulo(m[2]).replace(/\s+\d+$/, '');
    } else {
      campanha = titulo(slug);
    }

    if (ehMeta) {
      registros.push({
        nome: `[Doc] ${titulo(slug.replace(/^00-/, ''))}`,
        estagio: ESTAGIOS[est].nome, campanha: 'Documentação', produto, ordem: null,
        assunto: null, tipo: 'Doc', origem: `${est}/${f}`, corpo: raw,
      });
      continue;
    }

    // multi-email?
    const partes = [...raw.matchAll(/^##\s*Email\s*(\d+)\s*[—\-:]?\s*(.*)$/gim)];
    if (partes.length) {
      for (let i = 0; i < partes.length; i++) {
        const num = parseInt(partes[i][1], 10);
        const desc = (partes[i][2] || '').trim();
        const ini = partes[i].index + partes[i][0].length;
        const fim = i + 1 < partes.length ? partes[i + 1].index : raw.length;
        const corpo = raw.slice(ini, fim).trim();
        const hl = corpo.match(/^Headlines?:\s*(.*(?:\n[-*].*)*)/im);
        registros.push({
          nome: desc ? `${campanha}: ${desc}` : `${campanha}: Email ${num}`,
          estagio: ESTAGIOS[est].nome, campanha, produto, ordem: num,
          assunto: hl ? hl[1].replace(/\n?[-*]\s*/g, ' | ').replace(/"/g, '').trim().slice(0, 1900) : null,
          tipo: 'Email', origem: `${est}/${f}`, corpo,
        });
      }
      continue;
    }

    // email único: **Assunto:** ou Headlines:
    const mAss = raw.match(/^\*\*Assunto:\*\*\s*(.+)$/im);
    const mHl = raw.match(/^Headlines?:\s*((?:\n?[-*].*)+)/im);
    let assunto = null;
    if (mAss) assunto = mAss[1].trim();
    else if (mHl) assunto = mHl[1].replace(/\n?[-*]\s*/g, ' | ').replace(/"/g, '').replace(/^\s*\|\s*/, '').trim();
    registros.push({
      nome: titulo(slug.replace(/^(fm2em1|testo)_/, '').replace(/^\d+-/, '')),
      estagio: ESTAGIOS[est].nome, campanha, produto, ordem: ordemArq,
      assunto: assunto ? assunto.slice(0, 1900) : null,
      tipo: 'Email', origem: `${est}/${f}`, corpo: raw,
    });
  }
}

console.log(`▸ parse: ${registros.length} linhas (${registros.filter(r => r.tipo === 'Email').length} emails, ${registros.filter(r => r.tipo === 'Doc').length} docs)`);
const campanhas = [...new Set(registros.map(r => r.campanha))];
console.log(`  campanhas: ${campanhas.length}`);

// ── achar a marca BLUUE ────────────────────────────────────────────────
const marcas = await api(`databases/${DB_UNIDADES}/query`, { filter: { property: 'Nome', title: { equals: 'BLUUE' } } });
const bluueId = marcas.results[0]?.id;
console.log(`▸ marca BLUUE: ${bluueId ? 'ok' : 'NAO ACHEI (vai subir sem relation)'}`);

// ── criar o banco ──────────────────────────────────────────────────────
console.log('▸ criando banco "The Machine"...');
const db = await api('databases', {
  parent: { type: 'page_id', page_id: BS_PAGE },
  icon: DB_ICON,
  title: [{ type: 'text', text: { content: 'The Machine' } }],
  description: [{ type: 'text', text: { content: 'Emails do Machine (Customer Value Optimization) escritos para a Bluue. 1 linha = 1 email; o corpo vive no conteúdo da página. Fonte: apps/br4nds/_wiki/Bluue/emails.' } }],
  properties: {
    'Email': { title: {} },
    'Estágio': { select: { options: Object.values(ESTAGIOS).map(e => ({ name: e.nome, color: e.cor })) } },
    'Campanha': { select: { options: campanhas.slice(0, 100).map(c => ({ name: c })) } },
    'Produto': { select: { options: [{ name: 'FM 2em1', color: 'pink' }, { name: 'Testo', color: 'blue' }] } },
    'Ordem': { number: {} },
    'Assunto / Headlines': { rich_text: {} },
    'Tipo': { select: { options: [{ name: 'Email', color: 'default' }, { name: 'Doc', color: 'gray' }] } },
    'Status': { select: { options: [
      { name: 'Escrito', color: 'yellow' }, { name: 'Revisado', color: 'blue' }, { name: 'No ar', color: 'green' },
    ]}},
    'Marca': { relation: { database_id: DB_UNIDADES, type: 'dual_property', dual_property: {} } },
    'Origem': { rich_text: {} },
  },
});
console.log(`  ✓ ${db.id}`);

// ── subir ──────────────────────────────────────────────────────────────
console.log(`▸ subindo ${registros.length} linhas...`);
let n = 0, erros = [];
for (const r of registros) {
  const props = {
    'Email': { title: [{ type: 'text', text: { content: r.nome.slice(0, 200) } }] },
    'Estágio': { select: { name: r.estagio } },
    'Campanha': { select: { name: r.campanha } },
    'Tipo': { select: { name: r.tipo } },
    'Status': { select: { name: 'Escrito' } },
    'Origem': { rich_text: [{ type: 'text', text: { content: r.origem } }] },
  };
  if (r.produto) props['Produto'] = { select: { name: r.produto } };
  if (r.ordem != null) props['Ordem'] = { number: r.ordem };
  if (r.assunto) props['Assunto / Headlines'] = { rich_text: [{ type: 'text', text: { content: r.assunto } }] };
  if (bluueId) props['Marca'] = { relation: [{ id: bluueId }] };
  try {
    await api('pages', { parent: { database_id: db.id }, properties: props, children: blocos(r.corpo) });
    n++;
    if (n % 20 === 0) console.log(`  … ${n}/${registros.length}`);
  } catch (e) { erros.push(`${r.origem} :: ${r.nome} :: ${e.message}`); }
}

console.log(`\n✅ The Machine no ar: ${n}/${registros.length} linhas`);
if (erros.length) { console.log(`⚠️ ${erros.length} falhas:`); erros.forEach(e => console.log('   ', e)); }
console.log(`   ${db.url}`);
fs.writeFileSync(new URL('./notion-machine-ids.json', import.meta.url).pathname.replace(/^\//, ''), JSON.stringify({ db: db.id }, null, 2));
