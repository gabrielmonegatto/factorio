#!/usr/bin/env node
// Export COMPLETO do Teable → NDJSON.gz local (e depois R2).
// Parte da aposentadoria do Teable (19/08/2026): antes de migrar o que é vivo,
// garante que NADA se perde. Read-only no Teable.
//
//   node scripts/migracao/teable_export.mjs [--saida <dir>]
//
// Gotcha: o cert TLS de db.markeologia.com.br está VENCIDO. Desligamos a validação
// só neste script (leitura de dado nosso, host conhecido). Não copiar esse padrão
// pra código que fala com terceiros.

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const ENV_PATH = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const get = k => (env.find(l => l.startsWith(k + '=')) || '').slice(k.length + 1).trim();
const BASE_URL = get('TEABLE_URL').replace(/\/$/, '');
const TOKEN = get('TEABLE_TOKEN');

const argIdx = process.argv.indexOf('--saida');
const OUT = argIdx > -1 ? process.argv[argIdx + 1]
  : path.join(process.env.TEMP || '.', 'teable-export');
fs.mkdirSync(OUT, { recursive: true });

const PAGE = 800;
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function api(p) {
  for (let tent = 1; ; tent++) {
    try {
      const res = await fetch(`${BASE_URL}${p}`, { headers: { Authorization: `Bearer ${TOKEN}` } });
      if (res.status === 429 || res.status >= 500) throw new Error(`HTTP ${res.status}`);
      if (!res.ok) return { __err: `HTTP ${res.status}` };
      return await res.json();
    } catch (e) {
      if (tent >= 4) return { __err: e.message };
      await sleep(tent * 2000);
    }
  }
}

const manifesto = { exportadoEm: new Date().toISOString(), origem: BASE_URL, bases: [] };

const bases = await api('/api/base/access/all');
if (!Array.isArray(bases)) { console.error('não listou bases:', JSON.stringify(bases).slice(0, 200)); process.exit(1); }

for (const base of bases) {
  console.log(`\n■ BASE ${base.name} [${base.id}]`);
  const entradaBase = { id: base.id, nome: base.name, tabelas: [] };
  const tables = await api(`/api/base/${base.id}/table`);
  if (!Array.isArray(tables)) {
    console.log(`  ⚠️ listing de tabelas quebrado: ${tables?.__err}`);
    entradaBase.erro = tables?.__err;
    manifesto.bases.push(entradaBase);
    continue;
  }
  for (const t of tables) {
    const slug = `${base.name}__${t.name}`.replace(/[^\w.-]+/g, '_');
    const arquivo = path.join(OUT, `${slug}.ndjson.gz`);
    const campos = await api(`/api/table/${t.id}/field`);

    const gz = zlib.createGzip();
    const ws = fs.createWriteStream(arquivo);
    gz.pipe(ws);
    const escreve = linha => new Promise(r => { gz.write(linha) ? r() : gz.once('drain', r); });

    let skip = 0, total = 0, erro = null;
    for (;;) {
      const j = await api(`/api/table/${t.id}/record?take=${PAGE}&skip=${skip}&fieldKeyType=name`);
      if (j?.__err) { erro = j.__err; break; }
      const recs = j.records || [];
      // 🧨 U+2028/U+2029 são JSON válido e JSON.stringify não os escapa, mas o
      // readline do Node quebra linha neles → NDJSON corrompido. Escapamos na fonte.
      for (const r of recs) {
        const linha = JSON.stringify({ id: r.id, fields: r.fields })
          .replace(/ /g, '\\u2028').replace(/ /g, '\\u2029');
        await escreve(linha + '\n');
      }
      total += recs.length;
      if (recs.length < PAGE) break;
      skip += PAGE;
      if (total % 4000 === 0) console.log(`    … ${total}`);
      await sleep(60);
    }
    await new Promise(r => { gz.end(r); });
    await new Promise(r => ws.on('close', r));

    const bytes = fs.statSync(arquivo).size;
    console.log(`  · ${t.name}: ${total} linhas → ${(bytes / 1024).toFixed(0)} KB${erro ? ` ⚠️ ${erro}` : ''}`);
    entradaBase.tabelas.push({
      id: t.id, nome: t.name, linhas: total, arquivo: path.basename(arquivo), bytes,
      campos: Array.isArray(campos) ? campos.map(f => ({ nome: f.name, tipo: f.type })) : null,
      erro,
    });
  }
  manifesto.bases.push(entradaBase);
}

fs.writeFileSync(path.join(OUT, 'MANIFESTO.json'), JSON.stringify(manifesto, null, 2));
const totalLinhas = manifesto.bases.flatMap(b => b.tabelas || []).reduce((a, t) => a + t.linhas, 0);
console.log(`\n✅ Export completo: ${totalLinhas} linhas em ${OUT}`);
