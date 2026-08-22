// expandir_spurgeon.mjs — quebra o "lote de 57 volumes" em 63 obras mineráveis.
//
// ## O problema que isto conserta (diagnosticado em 20/08/2026)
//
// A fila tinha UMA linha chamada "Sermões: 57 volumes do backlog (lote)" com
// `resolve_note: "sem candidato em content_index nem Gutenberg"`. Óbvio: um lote
// não é uma obra, nenhum resolvedor acha URL pra "57 volumes". A linha ficou
// `queued` pra sempre, e o `mine` só olha pra `status='resolved'`.
//
// Resultado: o acervo do Spurgeon (~3.500 sermões em 63 volumes) nunca foi
// minerado além dos 113 iniciais, e o canal ficou refém disso.
//
// ## O conserto
//
// As URLs do CCEL são previsíveis e eu verifiquei uma a uma por probe HTTP:
//   https://ccel.org/ccel/spurgeon/sermonsNN   (NN de 01 a 63; 64 dá 404)
// O adaptador ccel busca `{source_url}.xml`, que devolve o ThML do volume
// inteiro (~2,7 MB no volume 07).
//
// Como a URL é verificada e determinística, estas obras entram direto como
// `resolved` — não passam pelo resolvedor, que é justamente quem falhou.
//
// Uso:
//   node scripts/mining/expandir_spurgeon.mjs --dry-run
//   node scripts/mining/expandir_spurgeon.mjs

import { d1, d1Insert } from './lib.mjs';

const DRY = process.argv.includes('--dry-run');
const PRIMEIRO = 1;
const ULTIMO = 63;                       // 64 responde 404 (verificado)
const LOTE_ID = 29;                      // a linha "57 volumes do backlog"
const base = (nn) => `https://ccel.org/ccel/spurgeon/sermons${String(nn).padStart(2, '0')}`;

const romano = (n) => {
  const t = [[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],
             [50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];
  let s = '';
  for (const [v, r] of t) while (n >= v) { s += r; n -= v; }
  return s;
};

const main = async () => {
  const existentes = await d1(
    "SELECT id, title, source_url, status FROM works WHERE author LIKE '%purgeon%'"
  );
  const porUrl = new Map(existentes.map((w) => [w.source_url, w]));
  const titulos = new Set(existentes.map((w) => (w.title || '').toLowerCase()));

  let inseridos = 0, atualizados = 0, pulados = 0;

  for (let nn = PRIMEIRO; nn <= ULTIMO; nn++) {
    const url = base(nn);
    const titulo = `Spurgeon's Sermons, Volume ${romano(nn)}`;
    const jaTemUrl = porUrl.get(url);

    if (jaTemUrl) {
      pulados++;
      continue;
    }

    // A obra 1 já existe como "Volume VII" mas aponta pra página da SÉRIE,
    // não pro volume. Aproveita a linha em vez de duplicar.
    const antiga = existentes.find(
      (w) => (w.title || '').toLowerCase() === titulo.toLowerCase()
    );

    if (antiga) {
      if (DRY) { console.log(`~ ${titulo} -> corrige URL pra ${url}`); atualizados++; continue; }
      await d1(
        `UPDATE works SET source_url=?, source_kind='ccel', status='resolved',
           resolve_score=1.0, resolve_note='URL do volume verificada por probe HTTP (20/08)',
           updated_at=datetime('now') WHERE id=?`,
        [url, antiga.id]
      );
      atualizados++;
      continue;
    }

    if (DRY) { console.log(`+ ${titulo} -> ${url}`); inseridos++; continue; }
    await d1Insert(
      `INSERT INTO works (title, author, era, priority, source_kind, source_url,
         resolve_score, resolve_note, status, chapters_n, chars_n, attempts, updated_at)
       VALUES (?, 'Charles Haddon Spurgeon', 'vitoriana', 2, 'ccel', ?, 1.0,
         'expandido do lote 29; URL verificada por probe HTTP (20/08)',
         'resolved', 0, 0, 0, datetime('now'))`,
      [titulo, url]
    );
    inseridos++;
  }

  if (!DRY) {
    await d1(
      `UPDATE works SET status='blocked',
         resolve_note='SUPERSEDIDO: expandido em 63 volumes individuais (20/08). Não minerar.',
         updated_at=datetime('now') WHERE id=?`,
      [LOTE_ID]
    );
  }

  console.log(
    `\n${DRY ? '[dry-run] ' : ''}volumes inseridos: ${inseridos} | corrigidos: ${atualizados} | já existiam: ${pulados}`
  );
  if (!DRY) console.log(`lote ${LOTE_ID} marcado como blocked (supersedido)`);
};

main().catch((e) => { console.error(e); process.exit(1); });
