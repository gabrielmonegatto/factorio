// ETAPA 3: MINERAR. Pega obra resolvida, busca na fonte, extrai capítulo e grava
// no D1 de mineração. É a etapa que produz o ativo: texto bruto no nosso banco.
//
// Princípios:
//   - idempotente: re-minerar a mesma obra substitui os capítulos dela, não duplica
//   - educado: intervalo entre requisições por host (as fontes são acervos sem fins lucrativos)
//   - honesto: obra que falha vira 'failed' com o motivo, não some da fila
//   - o Notion reflete o resultado (Estado -> Limpando), então o painel humano não mente
//
// Uso: node scripts/mining/mine.mjs [--limite N] [--obra ID] [--fonte ccel]
import { d1, d1Insert, notion, log, sleep } from './lib.mjs';
import * as ccel from './sources/ccel.mjs';
import * as gutenberg from './sources/gutenberg.mjs';
import * as newadvent from './sources/newadvent.mjs';

const ADAPTERS = { ccel, gutenberg, newadvent };

const args = process.argv.slice(2);
const arg = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const LIMITE = Number(arg('--limite')) || 10;
const SO_OBRA = arg('--obra');
const SO_FONTE = arg('--fonte');

// Sinais de tradução moderna: CCEL hospeda edições protegidas (as Confissões de
// lá são a tradução Outler de 1955). Minerar isso seria publicar obra alheia.
const SUSPEITA_TRADUCAO = /newly translated|translated and edited by|copyright\s*(?:©|\(c\))?\s*(19[3-9]\d|20\d\d)|all rights reserved/i;

// Piso de qualidade: obra minerada com quase nada é quase sempre página índice
// ou extração quebrada. Melhor falhar visível do que gravar mentira no banco.
const PISO_CHARS = 3000;

// D1 recusa valor gigante (SQLITE_TOOBIG). Capítulo acima do teto é fatiado em
// partes, cortando em parágrafo pra não partir frase no meio.
const TETO_CAP = 480000;
const PARAGRAFO = String.fromCharCode(10, 10); // escape em string literal não sobrevive ao heredoc

const where = SO_OBRA ? 'id = ?' : SO_FONTE ? "status='resolved' AND source_kind=?" : "status='resolved'";
const params = SO_OBRA ? [SO_OBRA] : SO_FONTE ? [SO_FONTE] : [];
const fila = await d1(
  `SELECT id,notion_id,title,author,source_url,source_kind FROM works WHERE ${where}
   ORDER BY launch DESC, CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, id LIMIT ${LIMITE}`,
  params
);
console.log(`minerando ${fila.length} obras\n`);

let mineradas = 0, falhas = 0, suspeitas = 0, totalCaps = 0;

for (const obra of fila) {
  const t0 = Date.now();
  const adapter = ADAPTERS[obra.source_kind];
  const rotulo = `${obra.title.slice(0, 46)}`.padEnd(48);

  if (!adapter) {
    await marcarFalha(obra, `sem adapter pra fonte "${obra.source_kind}"`);
    console.log(`${rotulo} SEM ADAPTER (${obra.source_kind})`);
    falhas++; continue;
  }

  try {
    const r = await adapter.buscar(obra.source_url);
    if (!r.ok) { await marcarFalha(obra, r.erro); console.log(`${rotulo} FALHOU: ${r.erro}`); falhas++; continue; }

    // Trava de direito autoral, antes de gravar qualquer coisa.
    // No Gutenberg ela NÃO se aplica ao texto cru: todo arquivo de lá carrega o
    // aviso de licença da própria PG ("Copyright (C) 2002" da edição eletrônica),
    // e o acervo deles é domínio público nos EUA por definição. Checar o cru ali
    // barrava obra legítima (foi o que aconteceu com Brother Lawrence).
    const paraChecar = obra.source_kind === 'gutenberg' ? '' : r.bruto.slice(0, 60000);
    if (paraChecar && SUSPEITA_TRADUCAO.test(paraChecar)) {
      const trecho = paraChecar.match(SUSPEITA_TRADUCAO)[0].slice(0, 80);
      await d1(`UPDATE works SET status='blocked', last_error=?, updated_at=datetime('now') WHERE id=?`,
        [`tradução possivelmente protegida ("${trecho}") - conferir edição antes de minerar`, obra.id]);
      await log('mine', obra.id, false, 'bloqueada por suspeita de tradução protegida', Date.now() - t0);
      console.log(`${rotulo} BLOQUEADA: suspeita de tradução protegida ("${trecho.slice(0, 40)}")`);
      suspeitas++; continue;
    }

    const { meta, capitulos } = adapter.extrair(r.bruto);
    if (!capitulos.length) { await marcarFalha(obra, 'nenhum capítulo extraído'); console.log(`${rotulo} FALHOU: 0 capítulos`); falhas++; continue; }

    const totalChars = capitulos.reduce((a, c) => a + c.corpo.length, 0);
    if (totalChars < PISO_CHARS) {
      await marcarFalha(obra, `só ${totalChars} chars extraídos: provável página índice ou extração quebrada`);
      console.log(`${rotulo} FALHOU: texto curto demais (${totalChars} chars)`);
      falhas++; continue;
    }

    // substitui: re-minerar não duplica
    await d1('DELETE FROM chapters WHERE work_id = ?', [obra.id]);
    let chars = 0, n = 0;
    for (const c of capitulos) {
      for (const pedaco of fatiarSePreciso(c)) {
        await d1Insert('INSERT INTO chapters (work_id,number,title,body,chars) VALUES (?,?,?,?,?)',
          [obra.id, ++n, pedaco.titulo.slice(0, 300), pedaco.corpo, pedaco.corpo.length]);
        chars += pedaco.corpo.length;
      }
    }

    await d1(
      `UPDATE works SET status='mined', chapters_n=?, chars_n=?, last_error=NULL, updated_at=datetime('now') WHERE id=?`,
      [n, chars, obra.id]
    );
    await avisarNotion(obra, 'Limpando');
    await log('mine', obra.id, true, `${capitulos.length} caps, ${chars} chars`, Date.now() - t0);
    console.log(`${rotulo} OK  ${String(n).padStart(3)} caps  ${(chars / 1000).toFixed(0).padStart(4)}k chars  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    mineradas++; totalCaps += n;
  } catch (err) {
    await marcarFalha(obra, err.message);
    console.log(`${rotulo} ERRO: ${err.message.slice(0, 70)}`);
    falhas++;
  }
}


function fatiarSePreciso(c) {
  if (c.corpo.length <= TETO_CAP) return [c];
  const paragrafos = c.corpo.split(/\n\n/);
  const partes = [];
  let atual = '';
  for (const p of paragrafos) {
    if (atual.length + p.length > TETO_CAP && atual) { partes.push(atual); atual = ''; }
    atual += (atual ? PARAGRAFO : '') + p;
  }
  if (atual) partes.push(atual);
  return partes.map((corpo, i) => ({ titulo: `${c.titulo} (parte ${i + 1}/${partes.length})`, corpo }));
}

async function marcarFalha(obra, motivo) {
  await d1(
    `UPDATE works SET status='failed', attempts=attempts+1, last_error=?, updated_at=datetime('now') WHERE id=?`,
    [String(motivo || '').slice(0, 400), obra.id]
  );
  await log('mine', obra.id, false, motivo, null);
}

// O painel humano tem que refletir a esteira, senão ele mente pro Gabriel.
async function avisarNotion(obra, estado) {
  if (!obra.notion_id) return;
  try {
    await notion(`/pages/${obra.notion_id}`, 'PATCH', { properties: { Estado: { select: { name: estado } } } });
    await sleep(200);
  } catch { /* Notion fora do ar não invalida a mineração */ }
}

console.log(`\nresultado: ${mineradas} mineradas (${totalCaps} capítulos) · ${falhas} falhas · ${suspeitas} bloqueadas por direito autoral`);
const t = await d1(`SELECT status, COUNT(*) n FROM works GROUP BY status ORDER BY n DESC`);
console.log('fila agora: ' + t.map((r) => `${r.status}=${r.n}`).join(' · '));
