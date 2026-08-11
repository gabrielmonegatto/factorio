#!/usr/bin/env node
// DOJO (parte 2) — completa a faixa Marrom com drills e registra as fontes escritas
// (livros/manuais/glossários verificados) no banco Recursos do Bloom.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const IDS = JSON.parse(fs.readFileSync(new URL('./notion-dojo-ids.json', import.meta.url).pathname.replace(/^\//, ''), 'utf8'));
const DB_RECURSOS = '3a7f06f1-0ce3-8177-950e-e703ebb71da3';
const META_AM = '3a7f06f1-0ce3-8191-9734-f277e55092b0';

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, body, method = 'POST') {
  await sleep(360);
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) { console.error(`✗ ${method} ${path}:`, JSON.stringify(json).slice(0, 400)); throw new Error(json.message); }
  return json;
}
const txt = c => [{ type: 'text', text: { content: String(c).slice(0, 1900) } }];
const title = c => ({ title: txt(c) });
const sel = n => ({ select: { name: n } });
const rtx = c => ({ rich_text: txt(c) });
const rel = ids => ({ relation: ids.filter(Boolean).map(id => ({ id })) });
const yt = v => `https://www.youtube.com/watch?v=${v}`;

// ── mapear ids de faixas e técnicas existentes ─────────────────────────
async function mapear(dbId, prop) {
  const out = {}; let cursor;
  do {
    const q = await api(`databases/${dbId}/query`, { start_cursor: cursor, page_size: 100 });
    for (const r of q.results) out[r.properties[prop].title.map(t => t.plain_text).join('')] = r.id;
    cursor = q.has_more ? q.next_cursor : null;
  } while (cursor);
  return out;
}
const F = await mapear(IDS.faixas, 'Faixa');
const T = await mapear(IDS.tecnicas, 'Técnica');
console.log(`▸ mapeado: ${Object.keys(F).length} faixas, ${Object.keys(T).length} técnicas`);

// ── drills que faltavam (faixa Marrom estava sem nenhum) ───────────────
const NOVOS = [
  ['Entrar e sair no saco', 'Saco', 'Marrom', '3 rounds',
   'Fica fora do alcance do saco, entra com a combinação e sai imediatamente pra fora do alcance de novo. Nunca fica parado na distância média. Treina a leitura de distância que separa quem bate de quem apanha.',
   ['Entrar e sair', 'Sair depois de atacar', 'Passo frente e trás'], yt('U_J2ZkpjRAU')],
  ['Rounds contínuos', 'Condicionamento', 'Marrom', '8 rounds sem quebrar técnica',
   'Oito rounds seguidos de 3/1. A régua não é aguentar: é o oitavo round ter a mesma técnica do primeiro. No momento em que a guarda cai ou o pé cruza, o treino acabou.',
   ['Velocidade'], yt('yugiN3PQaFM')],
  ['Sombra recuando', 'Sombra', 'Marrom', '3 rounds',
   'Round inteiro andando pra trás e pros lados, golpeando enquanto recua, sem nunca cruzar os pés. Impede que a pressão do oponente saia de graça.',
   ['Golpear recuando', 'Shift / switch step', 'Movimento lateral'], yt('j_ibqwbloBE')],
];

console.log(`▸ inserindo ${NOVOS.length} drills na faixa Marrom...`);
for (const [nome, tipo, faixa, formato, como, tecs, video] of NOVOS) {
  await api('pages', { parent: { database_id: IDS.drills }, properties: {
    'Drill': title(nome), 'Tipo': sel(tipo), 'Faixa': rel([F[faixa]]),
    'Formato': rtx(formato), 'Como fazer': rtx(como),
    'Técnicas': rel(tecs.map(t => T[t])), 'Vídeo': { url: video },
  }});
}
console.log('  ✓ ok');

// ── fontes escritas (pesquisa verificada) → banco Recursos ─────────────
// [nome, tipo, link, notas]
const FONTES = [
  ['Championship Fighting (Jack Dempsey, 1950)', 'Livro',
   'https://archive.org/details/Championship_Fighting_Explosive_Punching_and_Aggressive_Defense_1950_Jack_Dempse/',
   'PDF aberto no Internet Archive (4,9 MB). A FÍSICA do soco: falling step, shoulder whirl, power line. É a melhor explicação escrita de por que um soco gera força. Ressalva: a página não declara domínio público — o consenso é que o copyright de 1950 não foi renovado, mas não é PD comprovado.'],
  ['Boxing (Edwin L. Haislet, 1940)', 'Livro',
   'https://archive.org/details/Boxing',
   'PDF aberto no Internet Archive (2,1 MB). A TAXONOMIA: cada golpe, defesa, contragolpe e combinação catalogado de forma sistemática. É o mais próximo de um dicionário pronto entre os clássicos — a referência natural pra expandir o banco Técnicas. Mesma ressalva de copyright do Dempsey.'],
  ['Physical Fitness Manual for the U.S. Navy (1943)', 'Livro',
   'https://archive.org/details/PhysicalFitnessNavy1943',
   'DOMÍNIO PÚBLICO comprovado (obra do governo dos EUA, Public Domain Mark 1.0) — a única fonte da lista com status legal 100% limpo. Capítulo VIII é boxe (lições fundamentais, shadow boxing, posições); o resto é condicionamento progressivo sem equipamento, que é exatamente o caso de treinar em casa.'],
  ['Muay Thai Basics (Christoph Delp, 2005)', 'Livro',
   'https://www.penguinrandomhouse.com/books/39136/muay-thai-basics-by-christoph-delp/',
   'PAGO, ~US$ 33 de lista. Nomenclatura e mecânica dos golpes que o boxe não tem: joelho, cotovelo, clinch, com foto passo a passo e seção de erros comuns. É a fonte pra completar o lado Muay Thai do dicionário.'],
  ['Muay Thai Training Exercises (Christoph Delp, 2013)', 'Livro',
   'https://www.penguinrandomhouse.com/books/226414/muay-thai-training-exercises-by-christoph-delp/',
   'PAGO, ~US$ 27 de lista. A camada de DRILLS: 300+ ilustrações de exercícios, fintas, contras e combinações, com planos de treino por nível. Alimenta o banco Drills. Aviso: o "PDFy mirror" no archive.org é upload pirata — não usar.'],
  ['ExpertBoxing — lista de combinações', 'Artigo',
   'https://expertboxing.com/johnnys-punching-combinations-list',
   'Grátis. Fixa a NOTAÇÃO numérica (1 jab, 2 direto, 3 hook esq., 4 hook dir., 5 e 6 uppercuts, sufixo b = corpo) e traz centenas de combinações já escritas nela, incluindo defesa e footwork. É o padrão de escrita do campo Nº do banco Técnicas.'],
  ['Muay Thailand — glossário tailandês', 'Artigo',
   'https://www.muaythailand.co.uk/en-us/blogs/muay-thai-tips/muay-thai-glossary',
   'Grátis. 60+ termos com romanização E escrita tailandesa (teep/ถีบ, kao/เข่า, sok/ศอก, chap kho/จับคอ) + comandos de treino. Fonte pro campo "Também chamado" das técnicas de Muay Thai.'],
  ['Evolve MMA — glossário de técnicas', 'Artigo',
   'https://evolve-mma.com/blog/the-complete-glossary-of-muay-thai-strikes-moves-and-techniques/',
   'Grátis. Cobertura por categoria em inglês (8 socos, 6 cotovelos, 4 joelhos, 11 chutes, 5 de footwork, 8 de defesa, 4 posições de clinch). Usar em par com o Muay Thailand: este tem mais técnicas, o outro tem os termos em tailandês. É o checklist do que ainda falta no dicionário.'],
  ['MAGNVS / IKS — Shane Fazen (FIGHTTIPS)', 'Curso',
   'https://magnvs.io/pages/daily-kickboxing-program',
   'A REFERÊNCIA do sistema de faixas do Dojo. Sistema de graduação de striking inspirado no IBJJF: a faixa branca se GANHA em 10 semanas (70 lesson plans de 60min: shadowboxing, drills, condicionamento, film study) + teste no fim. US$ 49/mês ou US$ 529/ano. Não assinado — o Dojo replica a LÓGICA (progressão com critério de passagem) com material já indexado.'],
];

console.log(`▸ registrando ${FONTES.length} fontes no banco Recursos...`);
let n = 0;
for (const [nome, tipo, link, notas] of FONTES) {
  await api('pages', { parent: { database_id: DB_RECURSOS }, properties: {
    'Nome': title(nome), 'Tipo': sel(tipo), 'Estado': sel('📥 Fila'),
    'Meta': rel([META_AM]), 'Link': { url: link }, 'Notas': rtx(notas),
  }});
  n++;
}
console.log(`  ✓ ${n} fontes`);
console.log('\n✅ pronto.');
