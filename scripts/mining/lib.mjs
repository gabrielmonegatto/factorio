// Núcleo compartilhado do minerador: env, D1, Notion, HTTP educado.
import { readFileSync } from 'node:fs';
import path from 'node:path';

const ENV_PATH = path.resolve(import.meta.dirname, '..', '..', '.env');
export const env = (() => {
  const e = {};
  for (const l of readFileSync(ENV_PATH, 'utf8').split(/\r?\n/)) {
    const i = l.indexOf('=');
    if (i > 0 && !l.trimStart().startsWith('#')) e[l.slice(0, i).trim()] = l.slice(i + 1).trim();
  }
  return e;
})();

export const ACCOUNT = 'dca6b1af1352f500d6eabe544b9222a3'; // Eternall
export const MINING_DB = 'b08c9fae-3692-409a-aebd-e9630ca66f1d'; // D1 mananciall-mining

// ── D1 pela API HTTP: aceita parâmetro vinculado, então texto de livro entra
//    sem escapar aspas na mão (o caminho do wrangler --command quebraria).
export async function d1(sql, params = []) {
  const r = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${MINING_DB}/query`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.CLOUDFLARE_API_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql, params }),
    }
  );
  const j = await r.json();
  if (!j.success) throw new Error(`D1: ${JSON.stringify(j.errors)?.slice(0, 300)} :: ${sql.slice(0, 120)}`);
  return j.result[0].results || [];
}

// D1 tem teto de tamanho por requisição; capítulo entra um a um, com retry.
export async function d1Insert(sql, params, tentativas = 3) {
  for (let i = 1; i <= tentativas; i++) {
    try { return await d1(sql, params); }
    catch (err) {
      if (i === tentativas) throw err;
      await sleep(800 * i);
    }
  }
}

export async function notion(pathname, method = 'GET', body) {
  const r = await fetch(`https://api.notion.com/v1${pathname}`, {
    method,
    headers: {
      Authorization: `Bearer ${env.NOTION_TOKEN}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json();
  if (!r.ok) throw new Error(`Notion ${method} ${pathname}: ${j.message || r.status}`);
  return j;
}

export const BIBLIOTECA_DB = '3bef06f1-0ce3-81d0-8ce6-daa092972b00';

export const plain = (p) => {
  if (!p) return '';
  if (p.type === 'title' || p.type === 'rich_text') return p[p.type].map((t) => t.plain_text).join('');
  if (p.type === 'select') return p.select?.name || '';
  if (p.type === 'multi_select') return p.multi_select.map((s) => s.name).join('|');
  if (p.type === 'number') return p.number ?? 0;
  if (p.type === 'checkbox') return p.checkbox;
  return '';
};

export async function notionRows(dbId) {
  let cursor, rows = [];
  do {
    const q = await notion(`/databases/${dbId}/query`, 'POST', { page_size: 100, start_cursor: cursor });
    rows.push(...q.results);
    cursor = q.has_more ? q.next_cursor : null;
  } while (cursor);
  return rows;
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ── HTTP educado: identifica quem somos e não martela a fonte.
//    As fontes são acervos sem fins lucrativos; sair batendo em paralelo é
//    o jeito rápido de tomar bloqueio e queimar a única via de acesso.
const ULTIMO = new Map();
export async function fetchPolido(url, { minIntervalo = 1500, tentativas = 3 } = {}) {
  const host = new URL(url).host;
  for (let i = 1; i <= tentativas; i++) {
    const espera = (ULTIMO.get(host) || 0) + minIntervalo - Date.now();
    if (espera > 0) await sleep(espera);
    ULTIMO.set(host, Date.now());
    try {
      const r = await fetch(url, {
        redirect: 'follow',
        headers: {
          'User-Agent': 'Mananciall-Miner/1.0 (+https://mananciall.org; acervo de domínio público)',
          'Accept-Language': 'en',
        },
      });
      if (r.status === 429 || r.status >= 500) throw new Error(`HTTP ${r.status}`);
      if (!r.ok) return { ok: false, status: r.status, body: '' };
      return { ok: true, status: r.status, body: await r.text() };
    } catch (err) {
      if (i === tentativas) return { ok: false, status: 0, body: '', erro: err.message };
      await sleep(2000 * i);
    }
  }
}

export async function log(stage, workId, ok, detail, ms) {
  try {
    await d1('INSERT INTO runs (stage, work_id, ok, detail, ms) VALUES (?,?,?,?,?)',
      [stage, workId ?? null, ok ? 1 : 0, String(detail ?? '').slice(0, 500), ms ?? null]);
  } catch { /* diário nunca derruba a esteira */ }
}
