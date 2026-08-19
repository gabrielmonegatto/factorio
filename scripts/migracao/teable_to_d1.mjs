#!/usr/bin/env node
// Migra as tabelas VIVAS do export do Teable para o D1 (19/08/2026).
// Lê os NDJSON.gz gerados por teable_export.mjs (não rebate no Teable: mais rápido,
// e o export é a prova de que nada se perdeu).
//
//   node scripts/migracao/teable_to_d1.mjs --entrada <dir-do-export> [--so <tabela>] [--secar]
//
// Desenho: cada tabela ganha COLUNAS ÚTEIS (as que a gente consulta) + coluna `raw`
// com o JSON original inteiro. Preserva 100% do dado sem gastar dias modelando.

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import readline from 'node:readline';

const ENV_PATH = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const get = k => (env.find(l => l.startsWith(k + '=')) || '').slice(k.length + 1).trim();
const ACCOUNT = get('CLOUDFLARE_ACCOUNT_ID');
const CF_TOKEN = get('CLOUDFLARE_API_TOKEN');

const DB = { intel: 'd2e1bda6-9202-4b27-a1ef-a590e689b80a', mining: 'b08c9fae-3692-409a-aebd-e9630ca66f1d' };
const DB_NOME = { intel: 'eternall-intel', mining: 'mananciall-mining' };

const arg = n => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : null; };
const ENTRADA = arg('--entrada') || path.join(process.env.TEMP || '.', 'teable-export');
const SO = arg('--so');
const SECAR = process.argv.includes('--secar');

async function d1(dbId, sql, params = []) {
  for (let tent = 1; ; tent++) {
    const res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${dbId}/query`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${CF_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql, params }),
    });
    const j = await res.json().catch(() => ({}));
    if (j.success) return j.result;
    const msg = (j.errors || []).map(e => e.message).join('; ') || `HTTP ${res.status}`;
    if (tent >= 3 || !/timeout|rate|429|internal/i.test(msg)) throw new Error(`D1: ${msg}\n   SQL: ${sql.slice(0, 160)}`);
    await new Promise(r => setTimeout(r, tent * 1500));
  }
}

// ————————————————————————————————————————————————————————————
// O QUE MIGRA (o resto fica só no arquivo do R2)
// ————————————————————————————————————————————————————————————
const S = (f, ...nomes) => { for (const n of nomes) { const v = f[n]; if (v != null && v !== '') return typeof v === 'object' ? JSON.stringify(v) : String(v); } return null; };
const NUM = (f, ...nomes) => { const v = S(f, ...nomes); if (v == null) return null; const n = Number(String(v).replace(/[^\d.-]/g, '')); return Number.isFinite(n) ? n : null; };

const PLANO = [
  {
    tabela: 'channels', banco: 'intel', arquivos: ['Eternall__channels_index'],
    schema: `CREATE TABLE IF NOT EXISTS channels (
      id TEXT PRIMARY KEY, nome TEXT, handle TEXT, plataforma TEXT, lingua TEXT,
      inscritos INTEGER, videos INTEGER, views INTEGER, url TEXT, descricao TEXT,
      thumbnail_url TEXT, minerado_em TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'nome', 'handle', 'plataforma', 'lingua', 'inscritos', 'videos', 'views', 'url', 'descricao', 'thumbnail_url', 'minerado_em', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'channel_name'), S(r.fields, 'handle'), S(r.fields, 'plataforma'), S(r.fields, 'língua', 'lingua'),
      NUM(r.fields, 'subscriber_count'), NUM(r.fields, 'video_count'), NUM(r.fields, 'view_count'), S(r.fields, 'URL'),
      S(r.fields, 'description'), S(r.fields, 'thumbnail_url'), S(r.fields, 'last_mined_at'), o, JSON.stringify(r.fields)],
  },
  {
    tabela: 'channel_videos', banco: 'intel', arquivos: ['Eternall__channels_videos'],
    schema: `CREATE TABLE IF NOT EXISTS channel_videos (
      id TEXT PRIMARY KEY, youtube_id TEXT, canal TEXT, titulo TEXT, publicado_em TEXT,
      duracao TEXT, views INTEGER, likes INTEGER, comentarios INTEGER, engajamento REAL,
      tier TEXT, categoria TEXT, assuntos TEXT, tags TEXT, descricao TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'youtube_id', 'canal', 'titulo', 'publicado_em', 'duracao', 'views', 'likes', 'comentarios', 'engajamento', 'tier', 'categoria', 'assuntos', 'tags', 'descricao', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'youtube_id'), S(r.fields, 'channel_name'), S(r.fields, 'title'), S(r.fields, 'publish_date'),
      S(r.fields, 'duration'), NUM(r.fields, 'view_count'), NUM(r.fields, 'like_count'), NUM(r.fields, 'comment_count'),
      NUM(r.fields, 'engagement_rate'), S(r.fields, 'performance_tier'), S(r.fields, 'content_category'),
      S(r.fields, 'main_subjects'), S(r.fields, 'tags'), S(r.fields, 'description'), o, JSON.stringify(r.fields)],
    indices: ['CREATE INDEX IF NOT EXISTS idx_cv_canal ON channel_videos(canal)', 'CREATE INDEX IF NOT EXISTS idx_cv_views ON channel_videos(views DESC)'],
  },
  {
    tabela: 'players', banco: 'intel',
    arquivos: ['Eternall__players_index', 'Br4nds__players_index', 'Zoac__players_index'],
    schema: `CREATE TABLE IF NOT EXISTS players (
      id TEXT PRIMARY KEY, nome TEXT, marca_alvo TEXT, dominio TEXT, categoria TEXT, nicho TEXT,
      descricao TEXT, ativo TEXT, ads_ativos INTEGER, ads_inativos INTEGER, ad_library_id TEXT,
      foreplay_id TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'nome', 'marca_alvo', 'dominio', 'categoria', 'nicho', 'descricao', 'ativo', 'ads_ativos', 'ads_inativos', 'ad_library_id', 'foreplay_id', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'Nome do Player', 'Name'), S(r.fields, 'Marca Alvo'), S(r.fields, 'Domínio Principal', 'URL'),
      S(r.fields, 'Categoria'), S(r.fields, 'Nicho'), S(r.fields, 'Descrição', 'Notes'), S(r.fields, 'Status de Monitoramento', 'Active'),
      NUM(r.fields, 'Total Anúncios Ativos'), NUM(r.fields, 'Total Anúncios Inativos'), S(r.fields, 'Ad Library ID'),
      S(r.fields, 'Foreplay Brand ID'), o, JSON.stringify(r.fields)],
  },
  {
    tabela: 'player_creatives', banco: 'intel',
    arquivos: ['Eternall__players_criativos', 'Br4nds__players_criativos'],
    schema: `CREATE TABLE IF NOT EXISTS player_creatives (
      id TEXT PRIMARY KEY, player TEXT, copy_principal TEXT, headline TEXT, formato TEXT,
      dias_no_ar INTEGER, landing_page TEXT, inicio TEXT, status TEXT, midia_url TEXT,
      etapa_funil TEXT, oferta TEXT, gancho TEXT, avatar TEXT, gatilho TEXT, cta TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'player', 'copy_principal', 'headline', 'formato', 'dias_no_ar', 'landing_page', 'inicio', 'status', 'midia_url', 'etapa_funil', 'oferta', 'gancho', 'avatar', 'gatilho', 'cta', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'Player'), S(r.fields, 'Copy Principal', 'Copy_Principal'), S(r.fields, 'Headline'),
      S(r.fields, 'Formato'), NUM(r.fields, 'Duração (Dias)', 'Duracao_Dias'), S(r.fields, 'Landing Page URL', 'Landing_Page_URL'),
      S(r.fields, 'Data de Início', 'Data_de_Inicio'), S(r.fields, 'Status'), S(r.fields, 'Mídia URL Original', 'Midia_URL_Original'),
      S(r.fields, 'Etapa do Funil'), S(r.fields, 'Oferta'), S(r.fields, 'Gancho'), S(r.fields, 'Avatar'),
      S(r.fields, 'Gatilho Emocional', 'Gatilhos Mentais'), S(r.fields, 'CTA'), o, JSON.stringify(r.fields)],
    indices: ['CREATE INDEX IF NOT EXISTS idx_pc_player ON player_creatives(player)'],
  },
  {
    tabela: 'player_pages', banco: 'intel',
    arquivos: ['Eternall__players_pages', 'Br4nds__players_pages', 'Zoac__players_pages'],
    schema: `CREATE TABLE IF NOT EXISTS player_pages (
      id TEXT PRIMARY KEY, url TEXT, player TEXT, tipo TEXT, status TEXT, qtd_anuncios INTEGER,
      copy_extraida TEXT, estrutura_json TEXT, checkout_url TEXT, plataforma_checkout TEXT,
      cta TEXT, order_bump TEXT, trust TEXT, prints TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'url', 'player', 'tipo', 'status', 'qtd_anuncios', 'copy_extraida', 'estrutura_json', 'checkout_url', 'plataforma_checkout', 'cta', 'order_bump', 'trust', 'prints', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'URL Resolvida', 'URL_Resolvida'), S(r.fields, 'Player'), S(r.fields, 'Tipo de Página', 'Tipo_de_Pagina'),
      S(r.fields, 'Status'), NUM(r.fields, 'Qtd. Anúncios'), S(r.fields, 'Copy Extraída', 'Copy_Extraida'),
      S(r.fields, 'Estrutura_JSON'), S(r.fields, 'Checkout_URL'), S(r.fields, 'Plataforma_Checkout'),
      S(r.fields, 'CTA_Texto'), S(r.fields, 'Order_Bump'), S(r.fields, 'Trust_Elements'), S(r.fields, 'Prints'), o, JSON.stringify(r.fields)],
  },
  {
    tabela: 'authors', banco: 'intel', arquivos: ['Eternall__authors_index'],
    schema: `CREATE TABLE IF NOT EXISTS authors (id TEXT PRIMARY KEY, nome TEXT, notas TEXT, url TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'nome', 'notas', 'url', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'Name', 'Nome'), S(r.fields, 'Notes'), S(r.fields, 'URL'), o, JSON.stringify(r.fields)],
  },
  {
    tabela: 'research', banco: 'intel', arquivos: ['Eternall__research_index', 'Eternall__research_content'],
    schema: `CREATE TABLE IF NOT EXISTS research (id TEXT PRIMARY KEY, titulo TEXT, url TEXT, status TEXT, conteudo TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'titulo', 'url', 'status', 'conteudo', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'Name', 'Nome', 'title', 'Field 1'), S(r.fields, 'URL'), S(r.fields, 'Status', 'pipeline_status'),
      S(r.fields, 'content', 'Notes'), o, JSON.stringify(r.fields)],
  },
  {
    tabela: 'sources', banco: 'intel', arquivos: ['Eternall__fonts_index', 'Eternall__research_fonts'],
    schema: `CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, nome TEXT, url TEXT, status TEXT, notas TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'nome', 'url', 'status', 'notas', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'Name', 'Label'), S(r.fields, 'URL'), S(r.fields, 'pipeline_status', 'Status'), S(r.fields, 'Notes'), o, JSON.stringify(r.fields)],
  },
  {
    tabela: 'wiki_articles_staging', banco: 'intel', arquivos: ['Eternall__wiki_articles'],
    schema: `CREATE TABLE IF NOT EXISTS wiki_articles_staging (id TEXT PRIMARY KEY, slug TEXT, titulo TEXT, tipo TEXT, status TEXT, conteudo TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'slug', 'titulo', 'tipo', 'status', 'conteudo', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'slug'), S(r.fields, 'title', 'titulo'), S(r.fields, 'type', 'tipo'), S(r.fields, 'status'),
      S(r.fields, 'content', 'conteudo'), o, JSON.stringify(r.fields)],
  },
  // content_index é a fonte da mineração: vai pro banco de mineração, não pro intel
  {
    tabela: 'content_index', banco: 'mining', arquivos: ['Eternall__content_index'],
    schema: `CREATE TABLE IF NOT EXISTS content_index (
      id TEXT PRIMARY KEY, titulo TEXT, autor TEXT, url TEXT, fonte TEXT, status TEXT,
      idioma TEXT, categoria TEXT, origem TEXT, raw TEXT)`,
    cols: ['id', 'titulo', 'autor', 'url', 'fonte', 'status', 'idioma', 'categoria', 'origem', 'raw'],
    map: (r, o) => [r.id, S(r.fields, 'Name', 'title', 'titulo', 'Field 1'), S(r.fields, 'author', 'autor', 'Author'),
      S(r.fields, 'URL', 'url', 'source_url'), S(r.fields, 'source', 'fonte', 'Source'),
      S(r.fields, 'status', 'pipeline_status', 'Status'), S(r.fields, 'language', 'idioma'),
      S(r.fields, 'category', 'categoria'), o, JSON.stringify(r.fields)],
    indices: ['CREATE INDEX IF NOT EXISTS idx_ci_titulo ON content_index(titulo)'],
  },
];

// 🧨 MINA: não usar `readline` aqui. O Node quebra linha também em U+2028/U+2029,
// que JSON.stringify NÃO escapa (são JSON válido) e aparecem em descrição de vídeo
// do YouTube. Resultado: linha partida ao meio e "Unterminated string in JSON".
// Quebramos só em \n de verdade.
async function lerNdjson(arquivo) {
  const cru = zlib.gunzipSync(fs.readFileSync(arquivo)).toString('utf8');
  const linhas = [];
  for (const l of cru.split('\n')) {
    const t = l.trim();
    if (t) linhas.push(JSON.parse(t));
  }
  return linhas;
}

// A API HTTP do D1 aceita no máximo 100 parâmetros vinculados por query, o que
// tornaria 36 mil vídeos uma eternidade de requests. Então geramos SQL literal
// fatiado e mandamos pelo wrangler, que já faz lote. Escape: aspa simples dobrada
// e remoção de caracteres de controle (quebram o parser do wrangler).
// Teto por campo: o D1 recusa statement grande demais (SQLITE_TOOBIG), e uma página
// de concorrente com copy extraída + JSON de prints passa disso numa linha só.
// O export íntegro no R2 continua sendo a fonte; no D1 fica o operacionalmente útil.
const TETO_CAMPO = 30000;
const LIT = v => {
  if (v == null) return 'NULL';
  if (typeof v === 'number') return Number.isFinite(v) ? String(v) : 'NULL';
  let s = String(v);
  if (s.length > TETO_CAMPO) s = s.slice(0, TETO_CAMPO) + '…[truncado de ' + s.length + ' chars — íntegro em r2://eternall-archives/teable/]';
  return "'" + s.replace(/'/g, "''").replace(/[\u0000-\u001f]/g, ' ') + "'";
};

const TEMPO = () => new Date().toISOString().slice(11, 19);

async function executaSql(dbName, sql, rotulo) {
  const arq = path.join(process.env.TEMP || '.', `d1-${dbName}-${rotulo}.sql`);
  fs.writeFileSync(arq, sql, 'utf8');
  const { execFileSync } = await import('node:child_process');
  try {
    execFileSync('npx', ['--yes', 'wrangler@latest', 'd1', 'execute', dbName, '--remote', '--file', arq, '-y'], {
      env: { ...process.env, CLOUDFLARE_API_TOKEN: CF_TOKEN, CLOUDFLARE_ACCOUNT_ID: ACCOUNT },
      stdio: ['ignore', 'pipe', 'pipe'], shell: true, maxBuffer: 32 * 1024 * 1024,
    });
  } catch (e) {
    // execFileSync devolve stdout/stderr como Buffer: sem decodificar, o erro vira
    // uma parede de bytes e a sessão perde tempo adivinhando.
    const saida = [e.stdout, e.stderr].map(b => (b ? b.toString('utf8') : '')).join('\n');
    const arqErro = `${arq}.erro`;
    fs.copyFileSync(arq, arqErro);
    throw new Error(`wrangler falhou em ${rotulo} (SQL preservado em ${arqErro}):\n${saida.replace(/\[[0-9;]*m/g, '').slice(-2500)}`);
  } finally { try { fs.unlinkSync(arq); } catch {} }
}

const resumo = [];
for (const p of PLANO) {
  if (SO && p.tabela !== SO) continue;
  const dbId = DB[p.banco];
  if (SECAR) await d1(dbId, `DROP TABLE IF EXISTS ${p.tabela}`);
  await d1(dbId, p.schema.replace(/\s+/g, ' '));
  for (const ix of p.indices || []) await d1(dbId, ix);

  let total = 0;
  for (const nomeArq of p.arquivos) {
    const arquivo = path.join(ENTRADA, `${nomeArq}.ndjson.gz`);
    if (!fs.existsSync(arquivo)) { console.log(`  (sem arquivo: ${nomeArq})`); continue; }
    const registros = await lerNdjson(arquivo);
    const origem = nomeArq;
    const cabeca = `INSERT OR REPLACE INTO ${p.tabela} (${p.cols.join(',')}) VALUES `;
    let buffer = [], bytes = 0, fatiaN = 0;
    const descarrega = async () => {
      if (!buffer.length) return;
      await executaSql(DB_NOME[p.banco], buffer.join(''), `${p.tabela}-${fatiaN++}`);
      buffer = []; bytes = 0;
    };
    for (const r of registros) {
      const valores = p.map(r, origem).map(LIT).join(',');
      const stmt = `${cabeca}(${valores});\n`;
      if (bytes + stmt.length > 3_500_000) await descarrega();
      buffer.push(stmt); bytes += stmt.length;
    }
    await descarrega();
    total += registros.length;
    console.log(`  · [${TEMPO()}] ${p.tabela} ← ${nomeArq}: ${registros.length}`);
  }
  const [{ results }] = await d1(dbId, `SELECT COUNT(*) AS n FROM ${p.tabela}`);
  console.log(`✅ ${p.banco}.${p.tabela}: ${results[0].n} linhas no D1 (migradas nesta rodada: ${total})`);
  resumo.push({ banco: p.banco, tabela: p.tabela, noD1: results[0].n, migradas: total });
}

console.log('\n' + JSON.stringify(resumo, null, 2));
