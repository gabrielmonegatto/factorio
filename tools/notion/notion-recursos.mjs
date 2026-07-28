#!/usr/bin/env node
// 📚 RECURSOS — biblioteca de aprendizado do Bloom, ligada às Maestrias do 🎯 Metas.
// Populada com os índices de treino reais (bateria/boxe/chutes/corda/calistenia).
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const COFRE = '3a5f06f1-0ce3-80c3-9b15-c486acb05b67';
const METAS = JSON.parse(fs.readFileSync(new URL('./notion-metas-ids.json', import.meta.url).pathname.replace(/^\//, ''), 'utf8'));
const DB_METAS = METAS.db;
const M = METAS.metas;

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

const txt = c => [{ type: 'text', text: { content: c } }];
const title = c => ({ title: txt(c) });
const sel = n => ({ select: { name: n } });
const rel = ids => ({ relation: ids.map(id => ({ id })) });

console.log('▸ criando 📚 Recursos...');
const db = await api('databases', {
  parent: { type: 'page_id', page_id: COFRE },
  icon: { type: 'emoji', emoji: '📚' },
  title: txt('📚 Recursos'),
  description: txt('Biblioteca de aprendizado do Bloom. Recurso não é "lido" — é MINERADO (estado Extraído). Ligado às Maestrias do 🎯 Metas.'),
  properties: {
    'Nome': { title: {} },
    'Tipo': { select: { options: [
      { name: 'Livro', color: 'brown' },
      { name: 'Curso', color: 'purple' },
      { name: 'Canal', color: 'red' },
      { name: 'Vídeo', color: 'orange' },
      { name: 'Artigo', color: 'blue' },
      { name: 'Planilha', color: 'green' },
    ]}},
    'Estado': { select: { options: [
      { name: '📥 Fila', color: 'gray' },
      { name: '👁️ Consumindo', color: 'blue' },
      { name: '⛏️ Extraído', color: 'green' },
    ]}},
    'Meta': { relation: { database_id: DB_METAS, type: 'dual_property', dual_property: {} } },
    'Link': { url: {} },
    'Notas': { rich_text: {} },
  },
});
console.log(`  ✓ ${db.id}`);

// renomear back-relation no Metas
const metasDb = await api(`databases/${DB_METAS}`, null, 'GET');
const renames = {};
for (const [name, p] of Object.entries(metasDb.properties))
  if (p.type === 'relation' && name.includes('📚') && name.includes('(Meta)')) renames[name] = { name: 'Recursos' };
if (Object.keys(renames).length) await api(`databases/${DB_METAS}`, { properties: renames }, 'PATCH');
console.log('  ✓ back-relation "Recursos" no 🎯 Metas');

const AM = 'Maestria: Artes Marciais (Brazillian Taijutsu)';
const SHAPE = 'Maestria: Shape e Condicionamento';
const MUS = 'Maestria: Musical';

// [nome, tipo, estado, meta, link, notas]
const ROWS = [
  // 🥁 bateria (treinando agora)
  ['Dimitri Fantini', 'Canal', '👁️ Consumindo', MUS,
    'https://www.youtube.com/channel/UCTJvq6a47JNStIyU2cTAWKw',
    '129 vídeos indexados em Desktop\\treino-bateria\\bateria.db (com transcrições). Progressão: pegada → single → mão fraca → double → paradiddle → BPM.'],
  ['How To Build Hand Speed FAST! (BPM 50→200)', 'Vídeo', '👁️ Consumindo', MUS,
    'https://www.youtube.com/watch?v=wUSPBp4rp18',
    'Vídeo-fonte dos treinos de BPM loopados (ffmpeg). Loops gerados em Desktop\\treino-bateria\\.'],
  // 🥊 boxe
  ['Precision Striking', 'Canal', '📥 Fila', AM,
    'https://www.youtube.com/channel/UC4PwJo76WpTOk-3N8dazt1A',
    'O mais sistemático (656 vídeos em boxe.db). Séries Development, Training Camps e Virtual Padwork (follow-along).'],
  ['Beginner Boxer\'s Portal (Precision Striking)', 'Curso', '📥 Fila', AM,
    'https://www.youtube.com/channel/UC4PwJo76WpTOk-3N8dazt1A',
    'A progressão pronta do boxe: 26 lições, #1 postura/jab → #25 sparring.'],
  ['Tony Jeffries', 'Canal', '📥 Fila', AM,
    'https://www.youtube.com/channel/UCT_8YwHmACxpUootXe7yKjA',
    '826 vídeos avulsos, didáticos pra iniciante.'],
  ['Currículo Boxe (próprio)', 'Artigo', '📥 Fila', AM, null,
    'Desktop\\treino-boxe\\docs\\curriculo_boxe.md — numeração de golpes (1-6) + progressão Portal + drills. Round timer 3min/1min = o metrônomo do boxe.'],
  ['Boxing Canada — Beginners Manual', 'Artigo', '📥 Fila', AM, null,
    'PDF em Desktop\\treino-boxe\\docs\\.'],
  // 🦵 chutes
  ['Sean "Muay Thai Guy" Fagan', 'Canal', '📥 Fila', AM,
    'https://www.youtube.com/channel/UCpRyzlMgSv7_9eMhq-l3DAw',
    'BASE dos chutes pro kickboxing (quadril+canela, teep, low kick). Âncora: "Muay Thai 101" (23min). 523 vídeos em chutes.db.'],
  ['Ginger Ninja Trickster (GNT)', 'Canal', '📥 Fila', AM,
    'https://www.youtube.com/channel/UCAGlOxmYbmXMifHpB43P2XQ',
    'COMPLEMENTO: TKD pra soltar a perna — stretching follow-along pra high kicks e splits. 546 vídeos em chutes.db.'],
  ['Currículo Chutes (próprio)', 'Artigo', '📥 Fila', AM, null,
    'Desktop\\treino-chutes\\docs\\curriculo_chutes.md — 3 trilhas: BASE Muay Thai / SOLTAR A PERNA (GNT) / FOLLOW-ALONG. Set curado baixado em fontes\\.'],
  // 🪢 corda
  ['Jump Rope Dudes', 'Canal', '📥 Fila', SHAPE,
    'https://www.youtube.com/@jumpropedudes',
    '1.156 vídeos em corda.db. Trilha: fundamentos → boxer skip → criss cross → double under + 2 workouts.'],
  ['Currículo Corda (próprio)', 'Artigo', '📥 Fila', SHAPE, null,
    'Desktop\\treino-corda\\docs\\curriculo_corda.md. Adendo footwork_danca.md: freestyle + shuffle + house/jacking ("dançar pulando corda").'],
  // 🤸 calistenia
  ['Geek Climber', 'Canal', '📥 Fila', SHAPE,
    'https://www.youtube.com/@GeekClimber',
    'Calistenia analítica (série "Math Guy" quantifica dificuldade). 160 vídeos em calistenia.db. Falta: escolher canal-tutorial base + currículo.'],
  ['Calisthenics Skill Tree (planilhas de dificuldade)', 'Planilha', '📥 Fila', SHAPE, null,
    'Equivalentes achados em Desktop\\treino-calistenia\\docs\\planilhas_dificuldade.md (Google Sheet Skill Tree, Titans Grip). A planilha EXATA do Geek Climber tá em descrição de vídeo — pendente (bot check).'],
  ['Overcoming Gravity (Steven Low)', 'Livro', '📥 Fila', SHAPE, null,
    'Bíblia da progressão calistênica. Steven Low colabora com o Geek Climber.'],
];

console.log(`▸ inserindo ${ROWS.length} recursos...`);
let n = 0;
for (const [nome, tipo, estado, meta, link, notas] of ROWS) {
  const props = {
    'Nome': title(nome), 'Tipo': sel(tipo), 'Estado': sel(estado),
    'Meta': rel([M[meta]]),
  };
  if (link) props['Link'] = { url: link };
  if (notas) props['Notas'] = { rich_text: txt(notas) };
  await api('pages', { parent: { database_id: db.id }, properties: props });
  n++;
}
console.log(`  ✓ ${n} recursos`);

fs.writeFileSync(new URL('./notion-recursos-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ db: db.id }, null, 2));
console.log(`\n✅ 📚 Recursos no ar: ${db.url}`);
