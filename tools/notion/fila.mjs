#!/usr/bin/env node
// A FILA DA FÁBRICA — braço determinístico do diretor-diário (piloto 01/09/2026).
//
// O banco Tasks do Notion é a fila (gestão humana, tarefa MACRO — constituição §3).
// Contrato de máquina, colunas adicionadas em 01/09:
//   Gate    = 'auto' (a cadência executa sozinha) | 'aprovação' (prepara e espera o Gabriel)
//   Prompt  = ordem de serviço autocontida (sem Prompt, a máquina não toca)
//   Exec    = última execução: data + resultado em 1 linha (SÓ a máquina escreve)
// A máquina só enxerga task com Responsável contendo 'Claude'.
//
// Uso (o diretor-diário chama; humano pode chamar pra depurar):
//   node tools/notion/fila.mjs --listar                 fila executável + gates parados (JSON)
//   node tools/notion/fila.mjs --pegar <page_id>        marca 'working' (claim, evita corrida)
//   node tools/notion/fila.mjs --concluir <page_id> --nota "..."   Finalizado + Exec
//   node tools/notion/fila.mjs --travar <page_id> --nota "..."     'aguardando' + Exec (bateu em gate)
//   node tools/notion/fila.mjs --reportar <page_id> --nota "..."   só atualiza Exec (progresso parcial)
//
// Portável de propósito: .env resolvido relativo ao repo (roda no Windows e na VPS).

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV = path.resolve(HERE, '..', '..', '.env');
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN='))?.slice('NOTION_TOKEN='.length).trim();
if (!TOKEN) { console.error('NOTION_TOKEN ausente no .env'); process.exit(1); }

const TASKS_DB = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(p, method = 'GET', body) {
  for (let tent = 1; ; tent++) {
    await sleep(320);
    try {
      const res = await fetch(`https://api.notion.com/v1/${p}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const j = await res.json();
      if (j.object === 'error' && j.code === 'rate_limited') { await sleep(2500); continue; }
      if (j.object === 'error') { console.error(`ERRO ${p}: ${j.code} ${j.message}`); process.exit(1); }
      return j;
    } catch (e) {
      if (tent >= 4) throw e;
      await sleep(tent * 3000);
    }
  }
}

const rt = s => [{ type: 'text', text: { content: String(s).slice(0, 1900) } }];
const texto = prop => (prop?.rich_text || prop?.title || []).map(x => x.plain_text).join('');
const hoje = () => new Date().toISOString().slice(0, 16).replace('T', ' ');

async function listar() {
  const paginas = [];
  let cursor;
  do {
    const q = await api(`databases/${TASKS_DB}/query`, 'POST', {
      page_size: 100,
      ...(cursor ? { start_cursor: cursor } : {}),
      filter: {
        and: [
          { property: 'Responsável', multi_select: { contains: 'Claude' } },
          { property: 'Status', select: { does_not_equal: 'Finalizado' } },
        ],
      },
    });
    paginas.push(...q.results);
    cursor = q.has_more ? q.next_cursor : null;
  } while (cursor);

  const linha = p => ({
    id: p.id,
    demanda: texto(p.properties['Demanda']),
    status: p.properties['Status']?.select?.name ?? null,
    gate: p.properties['Gate']?.select?.name ?? null,
    prompt: texto(p.properties['Prompt']),
    exec: texto(p.properties['Exec']),
    notas: texto(p.properties['Notas']),
  });
  const todas = paginas.map(linha);

  // executável = auto + prompt escrito + ninguém trabalhando nela
  const executaveis = todas.filter(t => t.gate === 'auto' && t.prompt && t.status !== 'working' && t.status !== 'aguardando');
  const aguardandoGabriel = todas.filter(t => t.gate === 'aprovação' || t.status === 'aguardando');
  const semContrato = todas.filter(t => !t.gate || (t.gate === 'auto' && !t.prompt));

  console.log(JSON.stringify({ executaveis, aguardandoGabriel, semContrato }, null, 1));
}

async function mudar(id, props) {
  await api(`pages/${id}`, 'PATCH', { properties: props });
  console.log('ok');
}

const args = process.argv.slice(2);
const flag = n => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const nota = flag('--nota') ?? '';

if (args.includes('--listar')) await listar();
else if (flag('--pegar')) await mudar(flag('--pegar'), { Status: { select: { name: 'working' } }, Exec: { rich_text: rt(`${hoje()} pegou`) } });
else if (flag('--concluir')) await mudar(flag('--concluir'), { Status: { select: { name: 'Finalizado' } }, Exec: { rich_text: rt(`${hoje()} ✓ ${nota}`) } });
else if (flag('--travar')) await mudar(flag('--travar'), { Status: { select: { name: 'aguardando' } }, Exec: { rich_text: rt(`${hoje()} ⛔ ${nota}`) } });
else if (flag('--reportar')) await mudar(flag('--reportar'), { Exec: { rich_text: rt(`${hoje()} … ${nota}`) } });
else { console.error('uso: --listar | --pegar <id> | --concluir <id> --nota "..." | --travar <id> --nota "..." | --reportar <id> --nota "..."'); process.exit(1); }
