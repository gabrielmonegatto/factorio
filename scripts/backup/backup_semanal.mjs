#!/usr/bin/env node
// Backup semanal da fábrica: todos os bancos D1 + os bancos de gestão do Notion → R2.
// Criado em 19/08/2026 (item 2.5 do roadmap) junto com a unificação de dados.
//
//   node scripts/backup/backup_semanal.mjs [--so d1|notion] [--seco]
//
// Destino: bucket R2 `eternall-archives`, prefixo `d1/<AAAA-MM-DD>/` e `notion/<AAAA-MM-DD>/`.
// Cadência alvo: 1x/semana pelo cron da VPS (o Time Travel do D1 cobre 30 dias como
// primeira linha; isto aqui é a segunda, e é o que cobre o Notion, que não tem nenhuma).

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { execFileSync } from 'node:child_process';

const ENV_PATH = process.env.FABRICA_ENV || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const get = k => (env.find(l => l.startsWith(k + '=')) || '').slice(k.length + 1).trim();
const ACCOUNT = get('CLOUDFLARE_ACCOUNT_ID');
const CF_TOKEN = get('CLOUDFLARE_API_TOKEN');
const NOTION_TOKEN = get('NOTION_TOKEN');

const BUCKET = 'eternall-archives';
const HOJE = new Date().toISOString().slice(0, 10);
const TMP = fs.mkdtempSync(path.join(process.env.TEMP || '.', 'backup-'));
const SO = (() => { const i = process.argv.indexOf('--so'); return i > -1 ? process.argv[i + 1] : null; })();
const SECO = process.argv.includes('--seco');

const wrangler = (args, silencioso = true) => execFileSync('npx', ['--yes', 'wrangler@latest', ...args], {
  env: { ...process.env, CLOUDFLARE_API_TOKEN: CF_TOKEN, CLOUDFLARE_ACCOUNT_ID: ACCOUNT },
  encoding: 'utf8', shell: true, maxBuffer: 256 * 1024 * 1024,
  stdio: silencioso ? ['ignore', 'pipe', 'pipe'] : 'inherit',
});

async function subirR2(arquivoLocal, chave) {
  if (SECO) { console.log(`   (seco) subiria ${chave}`); return; }
  wrangler(['r2', 'object', 'put', `${BUCKET}/${chave}`, '--file', arquivoLocal, '--remote']);
}

// ————————————————————————————— D1 —————————————————————————————
// Estratégia: dump de dados via API HTTP (SELECT por tabela) em vez de `d1 export`,
// porque o export nativo falha em banco grande e a gente quer JSON legível pra restore
// seletivo. Uma linha por registro (NDJSON) mantém o arquivo streamável.
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

async function backupD1() {
  const res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database?per_page=100`, {
    headers: { Authorization: `Bearer ${CF_TOKEN}` },
  });
  const { result: bancos } = await res.json();
  const relatorio = [];
  for (const b of bancos) {
    const tabelas = await d1(b.uuid, `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%'`);
    let linhasTotal = 0;
    const partes = [];
    for (const { name } of tabelas) {
      const linhas = [];
      const PAG = 2000;
      for (let off = 0; ; off += PAG) {
        const r = await d1(b.uuid, `SELECT * FROM "${name}" LIMIT ${PAG} OFFSET ${off}`);
        linhas.push(...r);
        if (r.length < PAG) break;
      }
      linhasTotal += linhas.length;
      partes.push(`--TABELA:${name}\n` + linhas.map(l => JSON.stringify(l)
        .replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029')).join('\n') + '\n');
    }
    const arq = path.join(TMP, `${b.name}.ndjson.gz`);
    fs.writeFileSync(arq, zlib.gzipSync(Buffer.from(partes.join(''), 'utf8')));
    await subirR2(arq, `d1/${HOJE}/${b.name}.ndjson.gz`);
    const kb = (fs.statSync(arq).size / 1024).toFixed(0);
    console.log(`  · D1 ${b.name}: ${tabelas.length} tabelas, ${linhasTotal} linhas → ${kb} KB`);
    relatorio.push({ banco: b.name, tabelas: tabelas.length, linhas: linhasTotal, kb: Number(kb) });
    fs.unlinkSync(arq);
  }
  return relatorio;
}

// ————————————————————————————— NOTION —————————————————————————————
const NOTION_DBS = {
  'areas': '3c1f06f1-0ce3-8076-908b-fbcb7b67294c',
  'roadmap': '3c1f06f1-0ce3-81ff-bdba-f04376322409',
  'esteiras': '3c1f06f1-0ce3-8167-989b-d56a4207f266',
  'indicadores': '3c1f06f1-0ce3-8196-9da9-e8c5895d2e4d',
  'tasks': '3a7f06f1-0ce3-81cd-8696-cc002c44f430',
  'unidades': '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f',
  'metas': '3a7f06f1-0ce3-8153-a258-ebbff106eab9',
  'biblioteca-mananciall': '3bef06f1-0ce3-81d0-8ce6-daa092972b00',
  'referencias-editoras': '3c0f06f1-0ce3-813b-94a4-c436be12ede0',
};

async function notion(p, method = 'GET', body) {
  await new Promise(r => setTimeout(r, 340)); // ~3 req/s é o teto da API
  const res = await fetch(`https://api.notion.com/v1/${p}`, {
    method,
    headers: { Authorization: `Bearer ${NOTION_TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

async function backupNotion() {
  const relatorio = [];
  for (const [nome, id] of Object.entries(NOTION_DBS)) {
    const linhas = [];
    let cursor;
    do {
      const j = await notion(`databases/${id}/query`, 'POST', { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
      if (j.object === 'error') { console.log(`  ⚠️ Notion ${nome}: ${j.code}`); break; }
      linhas.push(...j.results);
      cursor = j.has_more ? j.next_cursor : null;
    } while (cursor);
    if (!linhas.length) continue;
    const esquema = await notion(`databases/${id}`);
    const conteudo = JSON.stringify({ id, nome, esquema, linhas }, null, 1)
      .replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
    const arq = path.join(TMP, `${nome}.json.gz`);
    fs.writeFileSync(arq, zlib.gzipSync(Buffer.from(conteudo, 'utf8')));
    await subirR2(arq, `notion/${HOJE}/${nome}.json.gz`);
    console.log(`  · Notion ${nome}: ${linhas.length} linhas`);
    relatorio.push({ banco: nome, linhas: linhas.length });
    fs.unlinkSync(arq);
  }
  return relatorio;
}

const resultado = { data: HOJE };
if (!SO || SO === 'd1') resultado.d1 = await backupD1();
if (!SO || SO === 'notion') resultado.notion = await backupNotion();

const manifesto = path.join(TMP, 'MANIFESTO.json');
fs.writeFileSync(manifesto, JSON.stringify(resultado, null, 2));
await subirR2(manifesto, `MANIFESTO-${HOJE}.json`);
fs.rmSync(TMP, { recursive: true, force: true });

const totalD1 = (resultado.d1 || []).reduce((a, b) => a + b.linhas, 0);
const totalNotion = (resultado.notion || []).reduce((a, b) => a + b.linhas, 0);
console.log(`\n✅ Backup ${HOJE}: ${totalD1} linhas de D1 + ${totalNotion} de Notion → r2://${BUCKET}/`);
