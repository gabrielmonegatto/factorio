// Backup do D1 -> R2.
//
// Por que existe: o D1 tem Time Travel (volta o banco a qualquer ponto dos
// últimos 30 dias), e isso resolve acidente operacional. NÃO resolve dois casos:
// perder a conta e querer o dado fora da Cloudflare. Este worker resolve esses.
//
// ⚠️ Backup que ninguém sabe restaurar não é backup, é sensação de segurança.
// O caminho de volta é o restore.mjs ao lado — TESTE a restauração uma vez
// antes de considerar esta peça instalada.
//
// Formato: NDJSON (uma linha = uma linha da tabela), fatiado em arquivos de
// CHUNK_SIZE linhas. Fatiar em vez de gerar um arquivão é o que mantém o backup
// dentro da memória do Worker e o que permite reprocessar um pedaço sozinho na
// restauração. Cada rodada escreve um manifest.json com a contagem por tabela:
// é por ele que se confere se o backup ficou íntegro, sem baixar nada.
//
// Chave no bucket: d1/<PROJECT_SLUG>/AAAA-MM-DD/<tabela>/000.ndjson

const SKIP_TABLES = new Set(['_cf_KV', 'sqlite_sequence']);

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runBackup(env));
  },

  // Disparo manual (POST). Útil pra rodar um backup antes de uma migração de risco.
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return json({ error: 'use POST' }, 405);
    }
    // Falha fechado: sem segredo configurado o disparo manual não existe. O endpoint
    // é público (workers.dev), e backup é operação cara — não pode ficar aberto.
    if (!env.CRON_SECRET) return json({ error: 'manual trigger disabled' }, 403);
    const auth = request.headers.get('authorization') || '';
    if (auth !== `Bearer ${env.CRON_SECRET}`) return json({ error: 'unauthorized' }, 401);
    const result = await runBackup(env);
    return json(result, result.ok ? 200 : 500);
  },
};

async function runBackup(env) {
  const project = env.PROJECT_SLUG || 'projeto';
  const startedAt = new Date();
  const stamp = startedAt.toISOString().slice(0, 10);
  const prefix = `d1/${project}/${stamp}`;
  const chunkSize = Math.max(100, Math.min(10000, Number(env.CHUNK_SIZE) || 2000));

  const manifest = {
    database: project,
    started_at: startedAt.toISOString(),
    finished_at: null,
    chunk_size: chunkSize,
    tables: {},
    errors: [],
  };

  try {
    const tables = await listTables(env);

    for (const table of tables) {
      try {
        manifest.tables[table] = await dumpTable(env, table, prefix, chunkSize);
      } catch (err) {
        manifest.errors.push(`${table}: ${err.message}`);
      }
    }
  } catch (err) {
    manifest.errors.push(`listTables: ${err.message}`);
  }

  manifest.finished_at = new Date().toISOString();
  manifest.ok = manifest.errors.length === 0;

  await env.BACKUPS.put(`${prefix}/manifest.json`, JSON.stringify(manifest, null, 2), {
    httpMetadata: { contentType: 'application/json' },
  });
  // Ponteiro fixo pro último backup: quem for restaurar não precisa adivinhar a data.
  await env.BACKUPS.put(`d1/${project}/latest.json`, JSON.stringify(manifest, null, 2), {
    httpMetadata: { contentType: 'application/json' },
  });

  if (manifest.ok) await applyRetention(env, project);

  return manifest;
}

async function listTables(env) {
  const res = await env.CRO_DB.prepare(
    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
  ).all();
  return (res.results || []).map((r) => r.name).filter((n) => n && !SKIP_TABLES.has(n));
}

// Paginação por rowid: é estável mesmo com escrita acontecendo durante o backup
// (o cron roda de madrugada, mas o site não para). Paginar por OFFSET pularia ou
// repetiria linhas quando algo fosse inserido no meio da varredura.
async function dumpTable(env, table, prefix, chunkSize) {
  let lastRowId = 0;
  let fileIndex = 0;
  let rowCount = 0;
  const files = [];

  for (;;) {
    const res = await env.CRO_DB.prepare(
      `SELECT rowid AS __rowid, * FROM "${table}" WHERE rowid > ? ORDER BY rowid LIMIT ?`
    ).bind(lastRowId, chunkSize).all();

    const rows = res.results || [];
    if (!rows.length) break;

    lastRowId = rows[rows.length - 1].__rowid;

    const body = rows
      .map((row) => {
        const { __rowid, ...rest } = row;
        return JSON.stringify(rest);
      })
      .join('\n');

    const key = `${prefix}/${table}/${String(fileIndex).padStart(3, '0')}.ndjson`;
    await env.BACKUPS.put(key, body, {
      httpMetadata: { contentType: 'application/x-ndjson' },
    });

    files.push({ key, rows: rows.length });
    rowCount += rows.length;
    fileIndex += 1;

    if (rows.length < chunkSize) break;
  }

  return { rows: rowCount, files };
}

// Rotação. Desligada por padrão (RETENTION_DAYS vazio): apagar dado é gate humano.
async function applyRetention(env, project) {
  const days = Number(env.RETENTION_DAYS);
  if (!Number.isFinite(days) || days <= 0) return;

  const cutoff = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const listed = await env.BACKUPS.list({ prefix: `d1/${project}/`, delimiter: '/' });

  for (const folder of listed.delimitedPrefixes || []) {
    const date = folder.replace(`d1/${project}/`, '').replace('/', '');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || date >= cutoff) continue;

    let cursor;
    do {
      const page = await env.BACKUPS.list({ prefix: folder, cursor });
      const keys = page.objects.map((o) => o.key);
      if (keys.length) await env.BACKUPS.delete(keys);
      cursor = page.truncated ? page.cursor : undefined;
    } while (cursor);
  }
}

function json(data, status) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
