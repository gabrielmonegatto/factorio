#!/usr/bin/env node
// Esteira de inteligência de canais (W0 da área Int. de Mercado, 19/08/2026).
// Atualiza o D1 eternall-intel com o estado VIVO dos canais concorrentes:
//   1. resolve o UC id de cada canal (via 1 vídeo conhecido; fallback handle)
//   2. stats dos canais (inscritos/vídeos/views) + histórico diário (channel_stats)
//   3. vídeos novos (playlist de uploads, para quando encontra id conhecido)
//   4. stats dos vídeos (novos + últimos 60 dias; --completo refaz TODOS)
//
//   node scripts/intel/atualiza_canais.mjs [--completo] [--paginas N] [--seco]
//
// Cadência alvo: diária, cron da VPS. Custo de quota: rodada diária ~75 unidades,
// --completo ~1.500 (teto do projeto: 10.000/dia, dividido com a publicação).
// Credenciais: YT_CLIENT_ID/SECRET/REFRESH + CLOUDFLARE_API_TOKEN do .env.

import fs from 'node:fs';

const ENV_PATH = process.env.FABRICA_ENV || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const g = (k) => { const l = env.find((x) => x.startsWith(k + '=')) || ''; return l.slice(k.length + 1).trim(); };
const ACCOUNT = g('CLOUDFLARE_ACCOUNT_ID');
const CF_TOKEN = g('CLOUDFLARE_API_TOKEN');
const INTEL = 'd2e1bda6-9202-4b27-a1ef-a590e689b80a';

const COMPLETO = process.argv.includes('--completo');
const SECO = process.argv.includes('--seco');
const PAGINAS = (() => { const i = process.argv.indexOf('--paginas'); return i > -1 ? Number(process.argv[i + 1]) : (COMPLETO ? 400 : 2); })();
const HOJE = new Date().toISOString().slice(0, 10);

async function d1(sql, params = []) {
  for (let t = 1; ; t++) {
    const r = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${INTEL}/query`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${CF_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql, params }),
    });
    const j = await r.json().catch(() => ({}));
    if (j.success) return j.result[0].results;
    const msg = (j.errors || []).map((e) => e.message).join('; ');
    if (t >= 3 || !/timeout|rate|429/i.test(msg)) throw new Error(`D1: ${msg}`);
    await new Promise((res) => setTimeout(res, t * 1500));
  }
}

let quotaGasta = 0;
let ytToken = null;
async function yt(recurso, params) {
  if (!ytToken) {
    const tk = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ client_id: g('YT_CLIENT_ID'), client_secret: g('YT_CLIENT_SECRET'), refresh_token: g('YT_REFRESH_TOKEN'), grant_type: 'refresh_token' }),
    }).then((r) => r.json());
    if (!tk.access_token) throw new Error(`OAuth do YouTube falhou: ${tk.error || '?'}`);
    ytToken = tk.access_token;
  }
  quotaGasta += 1;
  const q = new URLSearchParams(params).toString();
  // rede oscila em rodada longa: ECONNRESET/timeout ganham retry com espera
  for (let t = 1; ; t++) {
    try {
      const r = await fetch(`https://www.googleapis.com/youtube/v3/${recurso}?${q}`, {
        headers: { Authorization: `Bearer ${ytToken}` },
      });
      const j = await r.json();
      if (j.error) {
        if (t < 4 && /quota|rate|backend|internal/i.test(j.error.message)) throw new Error(j.error.message);
        if (j.error) { const e = new Error(`YouTube ${recurso}: ${j.error.message}`); e.definitivo = true; throw e; }
      }
      return j;
    } catch (e) {
      if (e.definitivo || t >= 4) throw e;
      await new Promise((res) => setTimeout(res, t * 3000));
    }
  }
}
const lotes = (arr, n) => { const out = []; for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n)); return out; };

// ————— 0. migrações idempotentes —————
for (const sql of [
  `ALTER TABLE channels ADD COLUMN youtube_channel_id TEXT`,
  `ALTER TABLE channel_videos ADD COLUMN transcrito INTEGER DEFAULT 0`,
  `CREATE TABLE IF NOT EXISTS channel_stats (data TEXT NOT NULL, canal_id TEXT NOT NULL, nome TEXT, inscritos INTEGER, videos INTEGER, views INTEGER, PRIMARY KEY (data, canal_id))`,
  `CREATE TABLE IF NOT EXISTS video_transcripts (video_id TEXT PRIMARY KEY, canal TEXT, lingua TEXT, fonte TEXT, chars INTEGER, texto TEXT, em TEXT DEFAULT (datetime('now')))`,
]) {
  try { await d1(sql); } catch (e) { if (!/duplicate column/i.test(e.message)) throw e; }
}

// ————— 1. resolver UC ids que faltam —————
const semId = await d1(`SELECT id, nome, handle FROM channels WHERE youtube_channel_id IS NULL OR youtube_channel_id = ''`);
if (semId.length) {
  console.log(`— resolvendo UC id de ${semId.length} canais`);
  // duas amostras de vídeo por canal (uma pode ter sido removida); casar pelo
  // ID DO VÍDEO, nunca pelo nome: canal renomeia, id não
  const amostras = await d1(
    `SELECT canal, MAX(youtube_id) AS v1, MIN(youtube_id) AS v2 FROM channel_videos WHERE canal IN (${semId.map(() => '?').join(',')}) GROUP BY canal`,
    semId.map((c) => c.nome)
  );
  const canalDoVideo = {};
  for (const a of amostras) for (const v of [a.v1, a.v2]) if (v) canalDoVideo[v] = a.canal;
  const mapa = {}; // nome do canal (nosso) -> UC id
  for (const lote of lotes(Object.keys(canalDoVideo), 50)) {
    const r = await yt('videos', { part: 'snippet', id: lote.join(','), maxResults: 50 });
    for (const v of r.items || []) {
      const nosso = canalDoVideo[v.id];
      if (nosso && !mapa[nosso]) mapa[nosso] = v.snippet.channelId;
    }
  }
  for (const c of semId) {
    let ucid = mapa[c.nome] || null;
    let como = 'via vídeo';
    if (!ucid && c.handle) {
      const r = await yt('channels', { part: 'id', forHandle: c.handle.replace(/^@/, '') }).catch(() => null);
      ucid = r?.items?.[0]?.id || null;
      como = 'via handle';
    }
    // último recurso: busca pelo nome (100 unidades), conferindo pelo tamanho
    // do canal que a gente já conhecia (abril): evita casar homônimo errado
    if (!ucid) {
      const [ref] = await d1(`SELECT inscritos FROM channels WHERE id = ?`, [c.id]);
      const busca = await yt('search', { part: 'snippet', q: c.nome, type: 'channel', maxResults: 5 }).catch(() => null);
      quotaGasta += 99; // search custa 100
      const candidatos = (busca?.items || []).map((i) => i.snippet.channelId);
      if (candidatos.length) {
        const st = await yt('channels', { part: 'statistics,snippet', id: candidatos.join(',') });
        const alvo = Number(ref?.inscritos || 0);
        let melhor = null;
        for (const ch of st.items || []) {
          const subs = Number(ch.statistics?.subscriberCount || 0);
          const razao = alvo && subs ? Math.max(subs, alvo) / Math.max(1, Math.min(subs, alvo)) : 99;
          if (!melhor || razao < melhor.razao) melhor = { id: ch.id, nome: ch.snippet.title, subs, razao };
        }
        if (melhor && (melhor.razao <= 3 || !alvo)) {
          ucid = melhor.id;
          como = `via busca ("${melhor.nome}", ${melhor.subs} subs${melhor.razao > 3 ? ', SEM referência: conferir' : ''})`;
        } else if (melhor) {
          console.log(`   ⚠️ "${c.nome}": melhor candidato "${melhor.nome}" (${melhor.subs} subs) longe da referência (${alvo}); não gravei`);
        }
      }
    }
    if (ucid) { await d1(`UPDATE channels SET youtube_channel_id = ? WHERE id = ?`, [ucid, c.id]); console.log(`   ✓ ${c.nome} ${como}`); }
    else console.log(`   ⚠️ sem como resolver "${c.nome}"`);
  }
}

// ————— 2. stats dos canais + histórico diário —————
const canais = await d1(`SELECT id, nome, youtube_channel_id FROM channels WHERE youtube_channel_id IS NOT NULL AND youtube_channel_id != ''`);
console.log(`— ${canais.length} canais com UC id`);
const porUc = Object.fromEntries(canais.map((c) => [c.youtube_channel_id, c]));
let statsOk = 0;
for (const lote of lotes(canais.map((c) => c.youtube_channel_id), 50)) {
  const r = await yt('channels', { part: 'statistics,snippet', id: lote.join(','), maxResults: 50 });
  for (const ch of r.items || []) {
    const c = porUc[ch.id];
    const s = ch.statistics;
    if (SECO) { statsOk++; continue; }
    await d1(
      `UPDATE channels SET inscritos = ?, videos = ?, views = ?, minerado_em = ?, descricao = COALESCE(NULLIF(descricao,''), ?), thumbnail_url = COALESCE(NULLIF(thumbnail_url,''), ?) WHERE id = ?`,
      [Number(s.subscriberCount || 0), Number(s.videoCount || 0), Number(s.viewCount || 0), new Date().toISOString(),
        (ch.snippet.description || '').slice(0, 1500), ch.snippet.thumbnails?.default?.url || '', c.id]
    );
    await d1(
      `INSERT OR REPLACE INTO channel_stats (data, canal_id, nome, inscritos, videos, views) VALUES (?,?,?,?,?,?)`,
      [HOJE, ch.id, c.nome, Number(s.subscriberCount || 0), Number(s.videoCount || 0), Number(s.viewCount || 0)]
    );
    statsOk++;
  }
}
console.log(`   stats atualizados: ${statsOk}/${canais.length}`);

// ————— 3. vídeos novos (playlist de uploads) —————
const conhecidos = new Set((await d1(`SELECT youtube_id FROM channel_videos WHERE youtube_id IS NOT NULL`)).map((r) => r.youtube_id));
const novos = [];
for (const c of canais) {
  const playlist = 'UU' + c.youtube_channel_id.slice(2);
  let pagina = null;
  for (let p = 0; p < PAGINAS; p++) {
    let r;
    try {
      r = await yt('playlistItems', { part: 'contentDetails,snippet', playlistId: playlist, maxResults: 50, ...(pagina ? { pageToken: pagina } : {}) });
    } catch (e) {
      if (/playlist.*not.*found|não.*encontrada/i.test(e.message)) break; // canal sem uploads públicos
      throw e;
    }
    const itens = r.items || [];
    let inedito = 0;
    for (const it of itens) {
      const vid = it.contentDetails.videoId;
      if (conhecidos.has(vid)) continue;
      conhecidos.add(vid);
      inedito++;
      novos.push({ vid, canal: c.nome });
    }
    pagina = r.nextPageToken;
    // página inteira já conhecida = alcançamos o histórico; só continua no --completo
    if (!pagina || (!COMPLETO && inedito === 0)) break;
  }
}
console.log(`— vídeos novos descobertos: ${novos.length}`);

// ————— 4. stats de vídeos (novos + recentes; --completo = todos) —————
const corte = new Date(Date.now() - 60 * 864e5).toISOString();
const alvo = COMPLETO
  ? await d1(`SELECT youtube_id FROM channel_videos WHERE youtube_id IS NOT NULL`)
  : await d1(`SELECT youtube_id FROM channel_videos WHERE youtube_id IS NOT NULL AND publicado_em >= ?`, [corte]);
const ids = [...new Set([...novos.map((n) => n.vid), ...alvo.map((r) => r.youtube_id)])];
console.log(`— atualizando stats de ${ids.length} vídeos${COMPLETO ? ' (completo)' : ' (novos + 60 dias)'}`);

let atualizados = 0, inseridos = 0;
const ehNovo = new Set(novos.map((n) => n.vid));
for (const lote of lotes(ids, 50)) {
  const r = await yt('videos', { part: 'snippet,statistics,contentDetails', id: lote.join(','), maxResults: 50 });
  for (const v of r.items || []) {
    if (SECO) continue;
    const s = v.statistics || {};
    if (ehNovo.has(v.id)) {
      await d1(
        `INSERT OR REPLACE INTO channel_videos (id, youtube_id, canal, titulo, publicado_em, duracao, views, likes, comentarios, tags, descricao, origem)
         VALUES (?,?,?,?,?,?,?,?,?,?,?, 'youtube-api')`,
        [`yt-${v.id}`, v.id, v.snippet.channelTitle, v.snippet.title, v.snippet.publishedAt, v.contentDetails?.duration || null,
          Number(s.viewCount || 0), Number(s.likeCount || 0), Number(s.commentCount || 0),
          JSON.stringify(v.snippet.tags || []).slice(0, 2000), (v.snippet.description || '').slice(0, 2000)]
      );
      inseridos++;
    } else {
      // vídeo antigo (id rec… do Teable ou yt-…): atualiza pela chave natural
      await d1(
        `UPDATE channel_videos SET views = ?, likes = ?, comentarios = ?, titulo = ?, duracao = ? WHERE youtube_id = ?`,
        [Number(s.viewCount || 0), Number(s.likeCount || 0), Number(s.commentCount || 0), v.snippet.title, v.contentDetails?.duration || null, v.id]
      );
      atualizados++;
    }
  }
}
// Nota de custo: no --completo isso vira ~1 UPDATE por vídeo (36k queries, ~30-40min).
// É o preço de manter os ids rec… herdados do Teable. Rodada diária é pequena.

const [{ n: totalVideos }] = await d1(`SELECT COUNT(*) n FROM channel_videos`);
console.log(`\n✅ ${HOJE}: ${statsOk} canais · ${inseridos} vídeos novos · ${atualizados} atualizados · total na base: ${totalVideos} · quota ~${quotaGasta} unidades`);
