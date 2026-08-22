// expandir_moody.mjs — quebra o lote do Moody nas 14 obras dele no Gutenberg.
//
// ## O problema que isto conserta
//
// Mesmo padrão que travou o Spurgeon (ver expandir_spurgeon.mjs): a fila tinha
// UMA linha, "The Way to God + Prevailing Prayer + Secret Power", em `queued`
// pra sempre. Lote não é obra; nenhum resolvedor acha URL pra três títulos
// grudados por sinal de mais. E o `mine` só olha pra `status='resolved'`.
//
// Resultado: o canal do Moody não tinha UM sermão pra renderizar.
//
// ## O conserto
//
// Os ids do Gutenberg vieram da busca do gutendex por autor e cada um foi
// verificado por probe HTTP: 14 obras, todas com texto puro, ~2,7 MB no total.
// Como a URL é verificada, entram direto como `resolved` e pulam o resolvedor,
// que é justamente quem falhava.
//
// ## O que ficou de FORA, e por quê
//
//   - 54736 "Bible Characters": antologia com Talmage e Parker. Narrar isso
//     como Moody seria atribuir a ele texto de outro autor.
//   - 58161: biografia escrita pelo FILHO, William R. Moody, e em finlandês.
//
// A regra do arquétipo Treasures é o pregador falando com a própria voz. Obra
// sobre ele, ou de terceiros, não entra no acervo do canal.
//
// Uso:
//   node scripts/mining/expandir_moody.mjs --dry-run
//   node scripts/mining/expandir_moody.mjs

import { d1, d1Insert } from './lib.mjs';

const DRY = process.argv.includes('--dry-run');
const LOTE_ID = 15;               // "The Way to God + Prevailing Prayer + Secret Power"
const AUTOR = 'Dwight Lyman Moody';

// id do Gutenberg -> título. Todos verificados por probe HTTP em 21/08/2026.
const OBRAS = [
  [30449, 'The Way to God and How to Find It'],
  [61883, 'Prevailing Prayer: What Hinders It?'],
  [33341, 'Secret Power; or, The Secret of Success in Christian Life and Work'],
  [33015, 'The Overcoming Life, and Other Sermons'],
  [33340, 'Weighed and Wanting: Addresses on the Ten Commandments'],
  [33014, 'To The Work! To The Work! Exhortations to Christians'],
  [30740, 'Men of the Bible'],
  [30768, 'Sowing and Reaping'],
  [30657, 'Sovereign Grace: Its Source, Its Nature and Its Effects'],
  [36655, 'Pleasure & Profit in Bible Study'],
  [33520, 'Wondrous Love, and other Gospel addresses'],
  [27316, 'That Gospel Sermon on the Blessed Hope'],
  [33024, "Moody's Stories: Anecdotes, Incidents and Illustrations"],
  [19830, "Moody's Anecdotes and Illustrations"],
];

const url = (id) => `https://www.gutenberg.org/ebooks/${id}`;

const main = async () => {
  const existentes = await d1(
    "SELECT id, title, source_url, status FROM works WHERE author LIKE '%Moody%'"
  );
  const porUrl = new Map(existentes.map((w) => [w.source_url, w]));

  let inseridos = 0, adotados = 0, pulados = 0;

  for (const [id, titulo] of OBRAS) {
    const ja = porUrl.get(url(id));
    if (ja) {
      // ARMADILHA (custou uma correção em 21/08): a linha do lote NÃO tinha
      // source_url vazia, tinha a URL da primeira obra da lista. Tratar isso
      // como "já existe, pula" e depois bloquear o lote apagava justamente
      // essa obra do acervo. Aqui a linha é ADOTADA: vira a obra de verdade.
      if (ja.status === 'resolved' && ja.title === titulo) { pulados++; continue; }
      if (DRY) { console.log(`~ #${ja.id} adotada como "${titulo}"`); adotados++; continue; }
      await d1(
        `UPDATE works SET title=?, author=?, source_kind='gutenberg', status='resolved',
           resolve_score=1.0, resolve_note='linha do lote 15 adotada como obra individual (21/08)',
           updated_at=datetime('now') WHERE id=?`,
        [titulo, AUTOR, ja.id]
      );
      adotados++;
      continue;
    }
    if (DRY) { console.log(`+ ${titulo}  ->  ${url(id)}`); inseridos++; continue; }
    await d1Insert(
      `INSERT INTO works (title, author, era, priority, source_kind, source_url,
         resolve_score, resolve_note, status, chapters_n, chars_n, attempts, updated_at)
       VALUES (?, ?, 'vitoriana', 2, 'gutenberg', ?, 1.0,
         'expandido do lote 15; id do Gutenberg verificado por probe HTTP (21/08)',
         'resolved', 0, 0, 0, datetime('now'))`,
      [titulo, AUTOR, url(id)]
    );
    inseridos++;
  }

  // O lote só é bloqueado se NINGUÉM o adotou. Se ele virou obra de verdade
  // (foi o caso do 30449), bloquear aqui mataria a obra recém-nascida.
  const lote = (await d1('SELECT status, title FROM works WHERE id=?', [LOTE_ID]))[0];
  const virouObra = lote && OBRAS.some(([, t]) => t === lote.title);
  if (!DRY && !virouObra) {
    await d1(
      `UPDATE works SET status='blocked',
         resolve_note='SUPERSEDIDO: expandido em obras individuais (21/08). Não minerar.',
         updated_at=datetime('now') WHERE id=?`,
      [LOTE_ID]
    );
  }

  console.log(`\n${DRY ? '[dry-run] ' : ''}inseridas: ${inseridos} | `
    + `adotadas: ${adotados} | já estavam ok: ${pulados}`);
  if (!DRY) console.log(virouObra
    ? `lote ${LOTE_ID} virou obra individual (não foi bloqueado)`
    : `lote ${LOTE_ID} marcado como blocked (supersedido)`);
};

main().catch((e) => { console.error(e); process.exit(1); });
