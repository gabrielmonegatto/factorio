#!/usr/bin/env node
// Snapshot do BI: coleta os números da fábrica das fontes reais e grava fatos
// datados no D1 (tabela bi_snapshots), depois espelha o valor atual no Notion.
// W0 da área Inteligência do Negócio (19/08/2026). O painel visual (mananciall-bi)
// vem na W1 e vai LER desta tabela, nunca do Notion.
//
//   node scripts/bi/snapshot.mjs [--seco] [--sem-notion]
//
// Cadência alvo: semanal (cron da VPS). Rodar mais de uma vez no mesmo dia é seguro:
// a chave é (data, metrica), então repetir atualiza em vez de duplicar.

import fs from 'node:fs';

const ENV_PATH = process.env.FABRICA_ENV || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const get = k => { const l = env.find(x => x.startsWith(k + '=')) || ''; return l.slice(k.length + 1).trim(); };
const ACCOUNT = get('CLOUDFLARE_ACCOUNT_ID');
const CF_TOKEN = get('CLOUDFLARE_API_TOKEN');
const NOTION_TOKEN = get('NOTION_TOKEN');

const SECO = process.argv.includes('--seco');
const SEM_NOTION = process.argv.includes('--sem-notion');
const HOJE = new Date().toISOString().slice(0, 10);

const DB = {
  prod: 'ddae6874-2058-4aa1-927e-0e7887e2cba6',
  mining: 'b08c9fae-3692-409a-aebd-e9630ca66f1d',
  intel: 'd2e1bda6-9202-4b27-a1ef-a590e689b80a',
};

async function d1(dbId, sql, params = []) {
  const res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${dbId}/query`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${CF_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, params }),
  });
  const j = await res.json().catch(() => ({}));
  if (!j.success) throw new Error((j.errors || []).map(e => e.message).join('; ') || `HTTP ${res.status}`);
  return j.result[0].results;
}
const um = async (dbId, sql) => { try { const r = await d1(dbId, sql); return Object.values(r[0] || {})[0] ?? null; } catch { return null; } };

const fatos = []; // {metrica, area, valor, unidade, detalhe}
const anota = (metrica, area, valor, unidade = '', detalhe = '') => {
  fatos.push({ metrica, area, valor, unidade, detalhe });
  console.log(`  ${String(valor ?? '?').padStart(8)} ${unidade.padEnd(9)} ${metrica}${detalhe ? `  (${detalhe})` : ''}`);
};

// ————————————————————— PRODUTO —————————————————————
console.log('\n■ Productz');
anota('livros_live', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM books WHERE status='live'`), 'livros');
anota('livros_total', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM books`), 'livros');
anota('capitulos_total', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM chapters`), 'caps');
anota('capitulos_com_audio', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM chapters WHERE audio_url IS NOT NULL AND audio_url<>''`), 'faixas');
anota('leads', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM leads`), 'leads');
anota('pedidos', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM orders`), 'pedidos');
anota('pedidos_7d', 'Productz', await um(DB.prod, `SELECT COUNT(*) FROM orders WHERE created_at >= date('now','-7 day')`), 'pedidos', '7 dias');

// ————————————————————— MINERAÇÃO —————————————————————
console.log('\n■ Mineração');
try {
  const porStatus = await d1(DB.mining, `SELECT status, COUNT(*) n FROM works GROUP BY status`);
  for (const { status, n } of porStatus) anota(`mineracao_${status}`, 'Mineração', n, 'obras');
} catch { console.log('  (tabela works indisponível)'); }
anota('mineracao_capitulos', 'Mineração', await um(DB.mining, `SELECT COUNT(*) FROM chapters`), 'caps');
anota('content_index', 'Mineração', await um(DB.mining, `SELECT COUNT(*) FROM content_index`), 'obras', 'catálogo de fontes');

// ————————————————————— INTEL —————————————————————
console.log('\n■ Inteligência de Mercado');
anota('canais_monitorados', 'Inteligência de Mercado', await um(DB.intel, `SELECT COUNT(*) FROM channels`), 'canais');
anota('videos_concorrentes', 'Inteligência de Mercado', await um(DB.intel, `SELECT COUNT(*) FROM channel_videos`), 'vídeos');
anota('players', 'Inteligência de Mercado', await um(DB.intel, `SELECT COUNT(*) FROM players`), 'players');
anota('criativos_concorrentes', 'Inteligência de Mercado', await um(DB.intel, `SELECT COUNT(*) FROM player_creatives`), 'anúncios');

// ————————————————————— CANAL (YouTube) —————————————————————
console.log('\n■ Content');
try {
  const tk = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: get('YT_CLIENT_ID'), client_secret: get('YT_CLIENT_SECRET'), refresh_token: get('YT_REFRESH_TOKEN'), grant_type: 'refresh_token' }),
  }).then(r => r.json());
  if (!tk.access_token) throw new Error(tk.error || 'sem token');
  const ch = await fetch('https://www.googleapis.com/youtube/v3/channels?part=statistics,contentDetails,snippet&mine=true', {
    headers: { Authorization: `Bearer ${tk.access_token}` },
  }).then(r => r.json());
  const c = ch.items?.[0];
  anota('canal_inscritos', 'Content', Number(c.statistics.subscriberCount), 'inscritos', c.snippet.title);
  anota('canal_videos', 'Content', Number(c.statistics.videoCount), 'vídeos');
  anota('canal_views', 'Content', Number(c.statistics.viewCount), 'views');

  // publicados nos últimos 7 dias: mede cadência real, que é a meta da área
  const pl = c.contentDetails.relatedPlaylists.uploads;
  const itens = await fetch(`https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=${pl}`, {
    headers: { Authorization: `Bearer ${tk.access_token}` },
  }).then(r => r.json());
  const corte = Date.now() - 7 * 864e5;
  const recentes = (itens.items || []).filter(i => new Date(i.snippet.publishedAt).getTime() >= corte);
  anota('publicados_7d', 'Content', recentes.length, 'vídeos', 'últimos 7 dias');
  const shorts = recentes.filter(i => /#shorts/i.test(i.snippet.title)).length;
  anota('shorts_7d', 'Content', shorts, 'shorts', 'últimos 7 dias');
  anota('longos_7d', 'Content', recentes.length - shorts, 'longos', 'últimos 7 dias');
} catch (e) { console.log(`  ⚠️ YouTube indisponível: ${e.message}`); }

// ————————————————————— GRAVA —————————————————————
if (SECO) { console.log('\n(seco: nada gravado)'); process.exit(0); }

await d1(DB.prod, `CREATE TABLE IF NOT EXISTS bi_snapshots (
  data TEXT NOT NULL, metrica TEXT NOT NULL, area TEXT, valor REAL, unidade TEXT,
  detalhe TEXT, criado_em TEXT DEFAULT (datetime('now')), PRIMARY KEY (data, metrica))`.replace(/\s+/g, ' '));

for (const f of fatos) {
  if (f.valor == null) continue;
  await d1(DB.prod,
    `INSERT OR REPLACE INTO bi_snapshots (data, metrica, area, valor, unidade, detalhe) VALUES (?,?,?,?,?,?)`,
    [HOJE, f.metrica, f.area, Number(f.valor), f.unidade, f.detalhe]);
}
console.log(`\n✅ ${fatos.filter(f => f.valor != null).length} fatos gravados em bi_snapshots (${HOJE})`);

// ————————————————————— ESPELHA NO NOTION —————————————————————
if (SEM_NOTION) process.exit(0);
const ESPELHO = {
  'Livros live na loja': f => `${f.livros_live} live de ${f.livros_total}`,
  'Inscritos do canal': f => `${f.canal_inscritos}`,
  'Views/semana': f => `${f.canal_views} no total do canal`,
  'Longos publicados/semana': f => `${f.longos_7d ?? '?'}`,
  'Shorts publicados/semana': f => `${f.shorts_7d ?? '?'}`,
  'Obras mineradas (total)': f => `${f.mineracao_mined ?? 0}`,
  'Obras sem URL na fila': f => `${f.mineracao_queued ?? 0}`,
  'Leads capturados': f => `${f.leads}`,
  'Vendas/semana': f => `${f.pedidos_7d} (total histórico: ${f.pedidos})`,
  'Canais concorrentes monitorados': f => `${f.canais_monitorados} canais / ${f.videos_concorrentes} vídeos`,
};
const mapa = Object.fromEntries(fatos.map(f => [f.metrica, f.valor]));
// na VPS o arquivo de ids vive ao lado do script (FABRICA_IDS aponta pra ele)
const idsFile = process.env.FABRICA_IDS || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/tools/notion/notion-fabrica-ids.json';
const ids = JSON.parse(fs.readFileSync(idsFile, 'utf8'));

const notion = async (p, m = 'GET', b) => {
  await new Promise(r => setTimeout(r, 340));
  const res = await fetch(`https://api.notion.com/v1/${p}`, {
    method: m, headers: { Authorization: `Bearer ${NOTION_TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: b ? JSON.stringify(b) : undefined,
  });
  return res.json();
};
const linhas = [];
let cursor;
do {
  const j = await notion(`databases/${ids.dbIndicadores}/query`, 'POST', { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
  if (j.object === 'error') { console.log(`⚠️ Notion: ${j.code}`); break; }
  linhas.push(...(j.results || [])); cursor = j.has_more ? j.next_cursor : null;
} while (cursor);

let espelhados = 0;
for (const l of linhas) {
  const t = Object.values(l.properties).find(p => p.type === 'title');
  const nome = (t?.title || []).map(x => x.plain_text).join('');
  const fn = ESPELHO[nome];
  if (!fn) continue;
  let valor;
  try { valor = fn(mapa); } catch { continue; }
  if (/undefined|NaN/.test(valor)) continue;
  await notion(`pages/${l.id}`, 'PATCH', {
    properties: {
      'Valor atual': { rich_text: [{ type: 'text', text: { content: valor } }] },
      'Atualizado em': { date: { start: HOJE } },
    },
  });
  espelhados++;
}
console.log(`✅ ${espelhados} indicadores espelhados no Notion`);
