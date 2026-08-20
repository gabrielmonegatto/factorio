#!/usr/bin/env node
// Transcrição dos vídeos concorrentes, EM FILA LENTA e por prioridade de views.
// Usa as legendas do próprio YouTube via yt-dlp (auto ou manuais), sem baixar
// vídeo. Salva o texto plano em video_transcripts (D1 eternall-intel).
//
//   node scripts/intel/transcreve.mjs [--lote 40] [--pausa 20] [--canal "Nome"]
//
// ⚠️ AS DUAS LIÇÕES QUE MANDAM AQUI:
// 1. (memória treino-boxe) transcrição em massa contra o YouTube = bloqueio de
//    IP. Por isso: lote pequeno, pausa com jitter, e a PRIMEIRO sinal real de
//    bloqueio (HTTP 429 / bot-check) a rodada ABORTA. Insistir = perder o IP.
//    IP de DATACENTER (VPS/RunPods) já nasce bloqueado ("sign in to confirm"):
//    este script só funciona de IP residencial ou atrás de proxy residencial.
// 2. (aprendida em 19/08) pedir VÁRIAS línguas de legenda num vídeo só dispara
//    429 do endpoint timedtext na hora. Então: UMA língua por vídeo (a do
//    canal), com UM fallback pra outra. Nunca "en.*,pt.*,es.*".
//
// Estados em channel_videos.transcrito: 0 pendente · 1 ok · -1 sem legenda · -2 erro.

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';

const ENV_PATH = process.env.FABRICA_ENV || 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const env = fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/);
const g = (k) => { const l = env.find((x) => x.startsWith(k + '=')) || ''; return l.slice(k.length + 1).trim(); };
const ACCOUNT = g('CLOUDFLARE_ACCOUNT_ID');
const CF_TOKEN = g('CLOUDFLARE_API_TOKEN');
const INTEL = 'd2e1bda6-9202-4b27-a1ef-a590e689b80a';

const arg = (n, padrao) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : padrao; };
const LOTE = Number(arg('--lote', 40));
const PAUSA = Number(arg('--pausa', 20));
const CANAL = arg('--canal', null);
const TETO_TEXTO = 400_000;
const BLOQUEIO = /HTTP Error 429|too many requests|not a bot|sign in to confirm/i;

async function d1(sql, params = []) {
  const r = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${INTEL}/query`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${CF_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, params }),
  });
  const j = await r.json().catch(() => ({}));
  if (!j.success) throw new Error((j.errors || []).map((e) => e.message).join('; '));
  return j.result[0].results;
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// VTT de legenda automática vem com timestamps inline e linhas repetidas em
// janela rolante; isto extrai texto corrido sem repetições.
function vttParaTexto(vtt) {
  const linhas = vtt
    .replace(/<[^>]+>/g, '')
    .split(/\r?\n/)
    .filter((l) => l.trim() && !/^WEBVTT|^Kind:|^Language:|^NOTE|-->|^\d+$/.test(l))
    .map((l) => l.trim());
  const out = [];
  for (const l of linhas) if (out[out.length - 1] !== l) out.push(l);
  return out.join(' ').replace(/\s+/g, ' ').trim();
}

// baixa legenda de UMA língua; devolve {arquivos, saida, bloqueado}
// YT_PROXY_URL no .env (proxy residencial) destrava rodar isto na VPS: sem ele,
// IP de datacenter é bloqueado e o cron da VPS nem tenta (condicional no cron.d).
const PROXY = g('YT_PROXY_URL');

function baixaLegenda(tmp, videoId, lang) {
  let saida = '';
  try {
    execFileSync('yt-dlp', [
      '--skip-download', '--write-auto-subs', '--write-subs',
      '--sub-langs', `${lang}.*`, '--sub-format', 'vtt',
      '--no-warnings', '--no-playlist', '--socket-timeout', '30',
      ...(PROXY ? ['--proxy', PROXY] : []),
      '-o', path.join(tmp, videoId), `https://www.youtube.com/watch?v=${videoId}`,
    ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 150_000 });
  } catch (e) {
    saida = [e.stdout, e.stderr].map((b) => (b ? b.toString() : '')).join('\n');
  }
  const arquivos = fs.readdirSync(tmp).filter((f) => f.startsWith(videoId) && f.endsWith('.vtt'));
  return { arquivos, saida, bloqueado: BLOQUEIO.test(saida) };
}

// fila por prioridade de views, com a língua do canal
const fila = await d1(
  `SELECT v.youtube_id, v.canal, v.views, c.lingua
   FROM channel_videos v LEFT JOIN channels c ON c.nome = v.canal
   WHERE v.transcrito = 0 AND v.youtube_id IS NOT NULL ${CANAL ? 'AND v.canal = ?' : ''}
   ORDER BY v.views DESC LIMIT ?`,
  CANAL ? [CANAL, LOTE] : [LOTE]
);
if (!fila.length) { console.log('fila vazia: nada pendente'); process.exit(0); }
console.log(`— ${fila.length} vídeos na rodada (prioridade: views)`);

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'transcricao-'));
let ok = 0, semLegenda = 0, erro = 0;

for (const v of fila) {
  const principal = (v.lingua || '').toLowerCase().startsWith('pt') ? 'pt' : 'en';
  const reserva = principal === 'pt' ? 'en' : 'pt';

  let r = baixaLegenda(tmp, v.youtube_id, principal);
  if (r.bloqueado) {
    console.error(`\n🔴 bloqueio real do YouTube em ${v.youtube_id}: abortando a rodada.`);
    console.error(r.saida.slice(-300));
    process.exit(2);
  }
  let lingua = principal;
  if (!r.arquivos.length) {
    await sleep(4000);
    r = baixaLegenda(tmp, v.youtube_id, reserva);
    if (r.bloqueado) { console.error(`\n🔴 bloqueio real em ${v.youtube_id}: abortando.`); process.exit(2); }
    lingua = reserva;
  }

  if (!r.arquivos.length) {
    const indisponivel = /private|unavailable|removed|deleted/i.test(r.saida);
    await d1(`UPDATE channel_videos SET transcrito = ? WHERE youtube_id = ?`, [indisponivel ? -2 : -1, v.youtube_id]);
    indisponivel ? erro++ : semLegenda++;
  } else {
    // manual (.pt.vtt / .en.vtt) vence a automática (.pt-orig etc); qualquer uma serve
    r.arquivos.sort((a, b) => a.length - b.length);
    const escolhido = r.arquivos[0];
    const texto = vttParaTexto(fs.readFileSync(path.join(tmp, escolhido), 'utf8')).slice(0, TETO_TEXTO);
    if (texto.length < 50) {
      await d1(`UPDATE channel_videos SET transcrito = -1 WHERE youtube_id = ?`, [v.youtube_id]);
      semLegenda++;
    } else {
      await d1(
        `INSERT OR REPLACE INTO video_transcripts (video_id, canal, lingua, fonte, chars, texto) VALUES (?,?,?,?,?,?)`,
        [v.youtube_id, v.canal, lingua, 'youtube-legendas', texto.length, texto]
      );
      await d1(`UPDATE channel_videos SET transcrito = 1 WHERE youtube_id = ?`, [v.youtube_id]);
      ok++;
    }
    for (const f of r.arquivos) fs.unlinkSync(path.join(tmp, f));
  }
  process.stdout.write(`   ${ok + semLegenda + erro}/${fila.length} (ok=${ok} sem=${semLegenda} erro=${erro})\n`);
  await sleep((PAUSA + Math.random() * 10) * 1000);
}

fs.rmSync(tmp, { recursive: true, force: true });
const [{ n: total }] = await d1(`SELECT COUNT(*) n FROM video_transcripts`);
console.log(`✅ rodada: ${ok} transcritos · ${semLegenda} sem legenda · ${erro} indisponíveis · acervo total: ${total}`);
