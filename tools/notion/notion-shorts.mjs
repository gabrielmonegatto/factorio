#!/usr/bin/env node
// Builder do banco "Shorts" no Business System (23/08/2026).
//
// POR QUE ESTE BANCO EXISTE
// O roteiro de um short (qual trecho do sermão, qual gancho, por que foi escolhido)
// só vive no clips_meta.json dentro do R2. Isso serve pra máquina e é inútil pro
// humano: o Gabriel não consegue ver o que foi escolhido, corrigir um gancho ruim,
// nem decidir o que publica. Este banco é a VITRINE dessa mineração — a mesma
// regra do resto da fábrica: o banco é da máquina, o Notion é onde o estado fica
// visível pra quem decide.
//
// SYNC DE MÃO ÚNICA (R2 -> Notion). A máquina escreve FATO (trecho, tempo, gancho
// minerado, nota). O Gabriel escreve DECISÃO (Status, Plataformas, Publicar em).
// Rodar de novo atualiza os fatos e NÃO toca nas colunas de decisão.
//
// Uso:
//   node notion-shorts.mjs           todos os sermões com clipes minerados
//   node notion-shorts.mjs 0001      só as pastas que começam com isso

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(HERE, '..', '..');
const IDS_FILE = path.join(HERE, 'notion-shorts-ids.json');
const envLinha = (k) => fs.readFileSync(path.join(RAIZ, '.env'), 'utf8')
  .split(/\r?\n/).find((l) => l.startsWith(k + '='))?.slice(k.length + 1).trim();
const TOKEN = envLinha('NOTION_TOKEN');
const BS_PAGE = '33d6bf27-9f65-4043-8a5d-c53fe0b241a3';

const ids = fs.existsSync(IDS_FILE) ? JSON.parse(fs.readFileSync(IDS_FILE, 'utf8')) : { shorts: {} };
const save = () => fs.writeFileSync(IDS_FILE, JSON.stringify(ids, null, 2));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function api(p, method = 'GET', body) {
  for (let tent = 1; ; tent++) {
    await sleep(320); // o Notion limita perto de 3 req/s
    try {
      const res = await fetch('https://api.notion.com/v1/' + p, {
        method,
        headers: {
          Authorization: 'Bearer ' + TOKEN,
          'Notion-Version': '2022-06-28',
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const j = await res.json();
      if (j.object === 'error' && j.code === 'rate_limited') { await sleep(2500); continue; }
      return j;
    } catch (e) {
      if (tent >= 4) throw e;
      await sleep(tent * 3000);
    }
  }
}
function die(j, ctx) {
  if (j && j.object === 'error') {
    console.error('ERRO em ' + ctx + ': ' + j.code + ' ' + j.message);
    process.exit(1);
  }
  return j;
}

// 🧨 O Notion RECUSA rich_text acima de 2000 caracteres (erro, não truncagem).
const chunk = (s) => { const o = []; for (let i = 0; i < s.length; i += 1900) o.push(s.slice(i, i + 1900)); return o; };
const rt = (s) => chunk(String(s === undefined || s === null ? '' : s)).map((c) => ({ type: 'text', text: { content: c } }));
const P = (s) => ({ paragraph: { rich_text: rt(s) } });
const H3 = (s) => ({ heading_3: { rich_text: rt(s) } });
const QUOTE = (s) => ({ quote: { rich_text: rt(s) } });

// ── lê o R2 pelo Python, que já tem credencial e cliente prontos ──────────────
const filtro = process.argv[2] || '';
const py = [
  'import sys, os, json',
  'sys.path.insert(0, os.path.abspath("scripts/ancoras"))',
  'import casar_ancora as ca',
  'cli = ca.s3()',
  'pag = cli.get_paginator("list_objects_v2")',
  'PREFIXO = "channels/channels_youtube/treasures_charlesspurgeon"',
  'FILTRO = ' + JSON.stringify(filtro),
  'saida = []',
  'for pg in pag.paginate(Bucket="mananciall", Prefix=PREFIXO + "/"):',
  '    for o in pg.get("Contents", []):',
  '        if not o["Key"].endswith("clips_meta.json"): continue',
  '        pasta = o["Key"].split("/")[3]',
  '        if FILTRO and not pasta.startswith(FILTRO): continue',
  '        m = json.loads(cli.get_object(Bucket="mananciall", Key=o["Key"])["Body"].read())',
  '        m["pasta"] = pasta',
  '        saida.append(m)',
  'print(json.dumps(saida, ensure_ascii=False))',
].join('\n');

const metas = JSON.parse(execFileSync('python', ['-c', py], {
  cwd: RAIZ, encoding: 'utf8', maxBuffer: 128 * 1024 * 1024,
}));
console.log('R2: ' + metas.length + ' sermao(s) com clipes minerados');

// ── o banco ───────────────────────────────────────────────────────────────────
if (!ids.db) {
  const db = die(await api('databases', 'POST', {
    parent: { page_id: BS_PAGE },
    icon: { type: 'emoji', emoji: '🎬' },
    title: rt('Shorts'),
    description: rt('Roteiros minerados dos sermoes. A maquina escreve o fato; voce decide o status e onde publica.'),
    properties: {
      Short: { title: {} },
      'Sermao': { rich_text: {} },
      'No': { number: { format: 'number' } },
      Gancho: { rich_text: {} },
      'Duracao (s)': { number: { format: 'number' } },
      'Inicio (s)': { number: { format: 'number' } },
      'Nota da IA': { number: { format: 'number' } },
      Status: {
        select: {
          options: [
            { name: 'Minerado', color: 'gray' },
            { name: 'Aprovado', color: 'blue' },
            { name: 'Renderizado', color: 'purple' },
            { name: 'Publicado', color: 'green' },
            { name: 'Descartado', color: 'red' },
          ],
        },
      },
      Plataformas: {
        multi_select: {
          options: [
            { name: 'YouTube', color: 'red' },
            { name: 'TikTok', color: 'default' },
            { name: 'Instagram', color: 'pink' },
            { name: 'Facebook', color: 'blue' },
          ],
        },
      },
      'Publicar em': { date: {} },
      'Por que a IA escolheu': { rich_text: {} },
    },
  }), 'criar db Shorts');
  ids.db = db.id;
  save();
  console.log('banco Shorts criado');
}

// ── uma linha por clipe ───────────────────────────────────────────────────────
let novos = 0;
let atualizados = 0;
for (const m of metas) {
  const clips = m.clips || [];
  for (let i = 0; i < clips.length; i++) {
    const c = clips[i];
    const chave = m.pasta + '#' + (i + 1);
    const dur = Math.round((c.end_ms - c.start_ms) / 1000);
    const nnnn = m.pasta.split('_')[0];
    const props = {
      Short: { title: rt(nnnn + '_c' + String(i + 1).padStart(2, '0') + ' — ' + (c.hook_text || '')) },
      'Sermao': { rich_text: rt(m.title || m.pasta) },
      'No': { number: i + 1 },
      Gancho: { rich_text: rt(c.hook_text || '') },
      'Duracao (s)': { number: dur },
      'Inicio (s)': { number: Math.round(c.start_ms / 1000) },
      'Nota da IA': { number: typeof c.score === 'number' ? c.score : null },
      'Por que a IA escolheu': { rich_text: rt(c.reason || '') },
    };

    if (ids.shorts[chave]) {
      // 🧨 NUNCA reescrever Status / Plataformas / Publicar em: são as colunas do
      // Gabriel. Sync de mão única move fato, não atropela decisão humana.
      die(await api('pages/' + ids.shorts[chave], 'PATCH', { properties: props }), 'atualizar ' + chave);
      atualizados++;
      continue;
    }

    props.Status = { select: { name: 'Minerado' } };
    const texto = (c.words || []).map((w) => w.text).join(' ');
    const pagina = die(await api('pages', 'POST', {
      parent: { database_id: ids.db },
      properties: props,
      children: [
        H3('Transcricao do trecho'),
        QUOTE(texto.slice(0, 1900)),
        P('Sermao: ' + (m.title || m.pasta)),
        P('Trecho: ' + Math.round(c.start_ms / 1000) + 's ate ' + Math.round(c.end_ms / 1000) + 's (' + dur + 's)'),
        P('Minerado por: ' + (m.model || '?')),
      ],
    }), 'criar ' + chave);
    ids.shorts[chave] = pagina.id;
    novos++;
    if (novos % 25 === 0) { save(); console.log('  ' + novos + ' criados...'); }
  }
}
save();
console.log('');
console.log('OK ' + novos + ' novos, ' + atualizados + ' atualizados');
console.log('banco: https://www.notion.so/' + String(ids.db).replace(/-/g, ''));
