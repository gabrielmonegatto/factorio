#!/usr/bin/env node
// Health check da fábrica → webhook do Discord (#fabrica).
// Item P0.5 do 11_ROADMAP_ATIVO.md, criado em 19/08/2026.
//
// A lição que gerou este script: a esteira do Spurgeon quebrou em 30/07 e ninguém
// descobriu até 04/08, porque o Gabriel notou o canal parado. SEIS DIAS DE SILÊNCIO.
// Health check não é enfeite: é o que transforma "esteira que roda" em "esteira confiável".
//
//   node scripts/org/health_check.mjs [--seco] [--verboso]
//
// Cadência alvo: diária, pelo cron da VPS. Sem alarme falso: só grita quando há problema,
// e manda 1 resumo verde por semana (segunda) pra provar que o próprio check está vivo.

import fs from 'node:fs';

const ENV_PATH = process.env.FABRICA_ENV || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const get = k => {
  const l = env.find(x => x.startsWith(k + '=')) || '';
  return l.slice(k.length + 1).trim();
};
const ACCOUNT = get('CLOUDFLARE_ACCOUNT_ID');
const CF_TOKEN = get('CLOUDFLARE_API_TOKEN');
const WEBHOOK = get('DISCORD_WEBHOOK_FABRICA');
const YT_CLIENT_ID = get('YT_CLIENT_ID');
const YT_CLIENT_SECRET = get('YT_CLIENT_SECRET');
const YT_REFRESH = get('YT_REFRESH_TOKEN');
const CANAL_ESPERADO = 'UCXqp7wuorli1uLZKJM96T6Q'; // Charles Spurgeon Treasures

const SECO = process.argv.includes('--seco');
const VERBOSO = process.argv.includes('--verboso');
const HORAS_SEM_PUBLICAR = 48;

const DB = {
  'mananciall-db': 'ddae6874-2058-4aa1-927e-0e7887e2cba6',
  'mananciall-mining': 'b08c9fae-3692-409a-aebd-e9630ca66f1d',
  'eternall-intel': 'd2e1bda6-9202-4b27-a1ef-a590e689b80a',
};

const achados = []; // {nivel: 'erro'|'alerta'|'ok', titulo, detalhe}
const ok = (t, d) => achados.push({ nivel: 'ok', titulo: t, detalhe: d });
const alerta = (t, d) => achados.push({ nivel: 'alerta', titulo: t, detalhe: d });
const erro = (t, d) => achados.push({ nivel: 'erro', titulo: t, detalhe: d });

async function d1(dbId, sql) {
  const res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${dbId}/query`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${CF_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql }),
  });
  const j = await res.json().catch(() => ({}));
  if (!j.success) throw new Error((j.errors || []).map(e => e.message).join('; ') || `HTTP ${res.status}`);
  return j.result[0].results;
}

// ————— 1. Canal do YouTube publicou nas últimas 48h? —————
async function checaYoutube() {
  if (!YT_REFRESH) { alerta('YouTube', 'sem YT_REFRESH_TOKEN no .env: não dá pra checar'); return; }
  try {
    const tk = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ client_id: YT_CLIENT_ID, client_secret: YT_CLIENT_SECRET, refresh_token: YT_REFRESH, grant_type: 'refresh_token' }),
    }).then(r => r.json());
    if (!tk.access_token) { erro('YouTube: token morto', `refresh falhou (${tk.error || '?'}). Publicação parada até re-auth`); return; }

    // A lição do incidente I1: token válido NÃO prova canal certo.
    const meu = await fetch('https://www.googleapis.com/youtube/v3/channels?part=contentDetails,snippet&mine=true', {
      headers: { Authorization: `Bearer ${tk.access_token}` },
    }).then(r => r.json());
    const canal = meu.items?.[0];
    if (!canal) { erro('YouTube', 'token não devolve canal'); return; }
    if (canal.id !== CANAL_ESPERADO) {
      erro('YouTube: CANAL ERRADO', `token aponta pra "${canal.snippet?.title}" (${canal.id}), esperado ${CANAL_ESPERADO}. NÃO publicar.`);
      return;
    }
    const uploads = canal.contentDetails?.relatedPlaylists?.uploads;
    const itens = await fetch(`https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=1&playlistId=${uploads}`, {
      headers: { Authorization: `Bearer ${tk.access_token}` },
    }).then(r => r.json());
    const ultimo = itens.items?.[0]?.snippet;
    if (!ultimo) { alerta('YouTube', 'nenhum vídeo no canal'); return; }
    const horas = (Date.now() - new Date(ultimo.publishedAt)) / 36e5;
    const linha = `último: "${(ultimo.title || '').slice(0, 60)}" há ${horas.toFixed(0)}h`;
    if (horas > HORAS_SEM_PUBLICAR) erro(`YouTube parado há ${horas.toFixed(0)}h`, linha);
    else ok('YouTube publicando', linha);
  } catch (e) { erro('YouTube: check falhou', e.message.slice(0, 140)); }
}

// ————— 2. Bancos D1 respondem e têm dado? —————
async function checaBancos() {
  for (const [nome, id] of Object.entries(DB)) {
    try {
      const t = await d1(id, `SELECT COUNT(*) n FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`);
      const n = t[0].n;
      if (!n) erro(`D1 ${nome} vazio`, 'banco sem tabela: alguém apagou?');
      else if (VERBOSO) ok(`D1 ${nome}`, `${n} tabelas`);
    } catch (e) { erro(`D1 ${nome} não responde`, e.message.slice(0, 140)); }
  }
}

// ————— 3. Esteira de mineração andando? —————
async function checaMineracao() {
  try {
    const r = await d1(DB['mananciall-mining'], `SELECT status, COUNT(*) n FROM works GROUP BY status`);
    const porStatus = Object.fromEntries(r.map(x => [x.status, x.n]));
    const resumo = Object.entries(porStatus).map(([s, n]) => `${s}=${n}`).join(' ');
    if ((porStatus.queued || 0) + (porStatus.resolved || 0) === 0) alerta('Mineração: fila vazia', 'nada pra minerar: alimentar o plano no Notion');
    else if (VERBOSO) ok('Mineração', resumo);
  } catch (e) {
    if (/no such table/i.test(e.message)) return; // esteira ainda não criou a tabela
    alerta('Mineração: check falhou', e.message.slice(0, 120));
  }
}

// ————— 4. Loja viva? (site responde e catálogo tem livro) —————
async function checaLoja() {
  try {
    const res = await fetch('https://mananciall.org/', { redirect: 'follow' });
    if (!res.ok) erro('Site fora do ar', `mananciall.org devolveu ${res.status}`);
    else if (VERBOSO) ok('Site no ar', `HTTP ${res.status}`);
  } catch (e) { erro('Site fora do ar', e.message.slice(0, 120)); }
  try {
    const r = await d1(DB['mananciall-db'], `SELECT COUNT(*) n FROM books WHERE status='live'`);
    if (!r[0].n) erro('Catálogo vazio', 'nenhum livro com status live');
    else if (VERBOSO) ok('Catálogo', `${r[0].n} livros live`);
  } catch (e) { alerta('Catálogo: check falhou', e.message.slice(0, 120)); }
}

// ————— disparo —————
await Promise.all([checaYoutube(), checaBancos(), checaMineracao(), checaLoja()]);

const erros = achados.filter(a => a.nivel === 'erro');
const alertas = achados.filter(a => a.nivel === 'alerta');
const segunda = new Date().getDay() === 1;
const precisaFalar = erros.length || alertas.length || segunda || VERBOSO;

const icone = { erro: '🔴', alerta: '🟡', ok: '🟢' };
const linhas = achados
  .sort((a, b) => ['erro', 'alerta', 'ok'].indexOf(a.nivel) - ['erro', 'alerta', 'ok'].indexOf(b.nivel))
  .map(a => `${icone[a.nivel]} **${a.titulo}** — ${a.detalhe}`);

const cabeca = erros.length ? `🔴 Fábrica: ${erros.length} problema(s)`
  : alertas.length ? `🟡 Fábrica: ${alertas.length} alerta(s)`
  : '🟢 Fábrica: tudo em ordem';
const texto = [cabeca, ...linhas].join('\n');

console.log(texto);

if (!precisaFalar) { console.log('\n(sem novidade: não notifica)'); process.exit(0); }
if (SECO) { console.log('\n(seco: não envia)'); process.exit(erros.length ? 1 : 0); }
if (!WEBHOOK) {
  console.log('\n⚠️ DISCORD_WEBHOOK_FABRICA não está no .env: nada foi enviado.');
  process.exit(erros.length ? 1 : 0);
}
const env_res = await fetch(WEBHOOK, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'Fábrica', content: texto.slice(0, 1900) }),
});
console.log(env_res.ok ? '\n✅ enviado pro #fabrica' : `\n⚠️ webhook devolveu ${env_res.status}`);
process.exit(erros.length ? 1 : 0);
