// expandir_maclaren.mjs — põe as 19 obras de Alexander Maclaren na fila de mineração.
//
// ## Quem é e por que ele é o canal 3
//
// Alexander Maclaren (1826-1910), batista escocês, 45 anos na Union Chapel de
// Manchester, chamado na época de "príncipe dos expositores". O monumento dele
// são as *Expositions of Holy Scripture*, cobrindo quase a Bíblia inteira.
// Escolhido pelo Gabriel em 26/08/2026 como Treasures 3: é o maior volume em
// domínio público depois do Spurgeon, e passa no filtro doutrinário da casa
// (ver critério 6 do doc 18_REDE_TREASURES) — herança reformada branda, mas o
// púlpito é expositivo e devocional, sem pregação decretal.
//
// ## Volume MEDIDO (probe HTTP em 27/08/2026, não estimativa)
//
// 19 obras, ~1.344 capítulos contados pelos <divN> do ThML — e esse número é
// PISO: em `david` e nos três `expositorpsalms` o nível de capítulo é o div1,
// que a contagem grosseira do probe subestimou. O real fica perto de 1.490.
// A 1 vídeo/dia, isso é mais de QUATRO ANOS de canal sem repetir sermão.
//
// ## A URL, que é onde eu errei primeiro
//
// A página do autor lista as obras como `/ccel/maclaren/<slug>/<slug>` (slug
// DOBRADO). Mas o ThML não mora lá: `<slug>/<slug>.xml` dá 404. O XML está em
//
//     https://ccel.org/ccel/maclaren/<slug>.xml        (slug ÚNICO)
//
// Todas as 19 verificadas por probe, todas HTTP 200, ~1,5 MB cada. Como a URL
// é determinística e conferida, as obras entram direto como `resolved` e pulam
// o resolvedor — mesmo caminho do Spurgeon e do Moody.
//
// ## Sobreposição conhecida (decidir depois de minerar, não agora)
//
// `psalms` (Expositions of Holy Scripture) e `expositorpsalms1/2/3` (The
// Expositor's Bible) são DUAS edições do Maclaren sobre Salmos e devem repetir
// exposições. Entram as duas: a deduplicação honesta é por título de capítulo
// depois da mineração, com o texto na mão. Descartar uma agora, no escuro,
// jogaria fora ~150 capítulos que podem não ser duplicata nenhuma.
//
// ## O que fica de FORA
//
// Nada de terceiros. A regra do arquétipo Treasures é o pregador falando com a
// própria voz: obra SOBRE ele, ou antologia com outros autores, não entra
// (foi o caso do "Bible Characters" no Moody, que tinha Talmage e Parker).
// Todas as 19 daqui são autoria dele.
//
// Uso:
//   node scripts/mining/expandir_maclaren.mjs --dry-run
//   node scripts/mining/expandir_maclaren.mjs

import { d1, d1Insert } from './lib.mjs';

const DRY = process.argv.includes('--dry-run');
const AUTOR = 'Alexander Maclaren';

// slug do CCEL -> título. Os 19 verificados por probe HTTP em 27/08/2026.
// `caps` é a contagem observada no ThML: serve de EXPECTATIVA pra conferir a
// mineração depois (obra que render muito menos que isso minerou torto).
const OBRAS = [
  ['gen_num',          'Expositions of Holy Scripture: Genesis, Exodus, Leviticus and Numbers', 111],
  ['deut',             'Expositions of Holy Scripture: Deuteronomy, Joshua, Judges, Ruth and 1 Samuel', 115],
  ['2kings_eccl',      'Expositions of Holy Scripture: Second Kings to Ecclesiastes', 112],
  ['isa_jer',          'Expositions of Holy Scripture: Isaiah and Jeremiah', 123],
  ['ezek_matt1',       'Expositions of Holy Scripture: Ezekiel, Daniel, Minor Prophets and Matthew I to VIII', 72],
  ['matt2',            'Expositions of Holy Scripture: Matthew IX to XVIII', 87],
  ['mark',             'Expositions of Holy Scripture: Mark', 83],
  ['luke',             'Expositions of Holy Scripture: Luke', 103],
  ['john1',            'Expositions of Holy Scripture: St John Ch. I to XIV', 80],
  ['john2',            'Expositions of Holy Scripture: St John Chs. XV to XXI', 48],
  ['acts',             'Expositions of Holy Scripture: The Acts', 106],
  ['rom_cor',          'Expositions of Holy Scripture: Romans and Corinthians', 95],
  ['iicor_tim',        'Expositions of Holy Scripture: Second Corinthians, Galatians and Timothy', 87],
  ['psalms',           'Expositions of Holy Scripture: Psalms', 86],
  ['david',            'The Life of David as Reflected in His Psalms', 19],
  ['expositorpsalms1', "The Expositor's Bible: The Psalms, Volume I", 41],
  ['expositorpsalms2', "The Expositor's Bible: The Psalms, Volume II", 52],
  ['expositorpsalms3', "The Expositor's Bible: The Psalms, Volume III", 63],
  ['expositorcolphm',  "The Expositor's Bible: Colossians and Philemon", 26],
];

// ⚠️ slug ÚNICO. O adaptador ccel monta `${source_url}.xml`, então gravar a
// URL dobrada da página do autor produziria 404 em toda obra.
const url = (slug) => `https://ccel.org/ccel/maclaren/${slug}`;

const main = async () => {
  const existentes = await d1(
    "SELECT id, title, source_url, status FROM works WHERE author LIKE '%aclaren%'"
  );
  const porUrl = new Map(existentes.map((w) => [w.source_url, w]));

  let inseridos = 0, corrigidos = 0, pulados = 0, caps = 0;

  for (const [slug, titulo, esperados] of OBRAS) {
    caps += esperados;
    const ja = porUrl.get(url(slug));

    if (ja) {
      if (ja.status === 'resolved' && ja.title === titulo) { pulados++; continue; }
      if (DRY) { console.log(`~ #${ja.id} corrigida -> "${titulo}"`); corrigidos++; continue; }
      await d1(
        `UPDATE works SET title=?, author=?, source_kind='ccel', status='resolved',
           resolve_score=1.0, resolve_note='URL CCEL verificada por probe HTTP (27/08)',
           updated_at=datetime('now') WHERE id=?`,
        [titulo, AUTOR, ja.id]
      );
      corrigidos++;
      continue;
    }

    if (DRY) { console.log(`+ ${String(esperados).padStart(4)} caps  ${titulo}`); inseridos++; continue; }
    await d1Insert(
      `INSERT INTO works (title, author, era, priority, source_kind, source_url,
         resolve_score, resolve_note, status, chapters_n, chars_n, attempts, updated_at)
       VALUES (?, ?, 'vitoriana', 2, 'ccel', ?, 1.0,
         'Treasures 3 (Maclaren); URL CCEL verificada por probe HTTP (27/08)',
         'resolved', 0, 0, 0, datetime('now'))`,
      [titulo, AUTOR, url(slug)]
    );
    inseridos++;
  }

  console.log(`\n${DRY ? '[dry-run] ' : ''}inseridas: ${inseridos} | `
    + `corrigidas: ${corrigidos} | já estavam ok: ${pulados}`);
  console.log(`capítulos esperados no total: ~${caps}`);
};

main().catch((e) => { console.error(e); process.exit(1); });
