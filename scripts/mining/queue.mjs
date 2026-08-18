// ETAPA 1: FILA. Lê o plano no Notion (Biblioteca Mananciall) e materializa a
// fila de mineração no D1. O Notion continua sendo o painel humano: quem decide
// o que entra é o Gabriel, marcando Prioridade/Lançamento lá.
//
// Roda quantas vezes quiser: casa por notion_id, atualiza, não duplica.
// Uso: node scripts/mining/queue.mjs
import { d1, notionRows, plain, BIBLIOTECA_DB, log } from './lib.mjs';

const FONTE = { CCEL: 'ccel', Gutenberg: 'gutenberg', 'New Advent': 'newadvent', 'Archive.org': 'archive' };

const t0 = Date.now();
const linhas = await notionRows(BIBLIOTECA_DB);
console.log(`Notion: ${linhas.length} obras no plano`);

let novas = 0, atualizadas = 0, ignoradas = 0;
for (const pg of linhas) {
  const p = pg.properties;
  const estado = plain(p.Estado);
  const statusDP = plain(p['Status DP']);

  // Já publicado não volta pra fila; cortado idem.
  if (estado === 'Publicado' || estado === 'Cortada') { ignoradas++; continue; }

  // Domínio público não verificado NÃO mina. Trava dura: o risco de publicar
  // tradução protegida é jurídico, não estético.
  const status = statusDP === 'blocked' ? 'blocked' : 'queued';

  const dados = {
    notion_id: pg.id,
    title: plain(p.Obra),
    author: plain(p.Autor),
    era: plain(p.Era),
    priority: plain(p.Prioridade) || 'P3',
    launch: plain(p['Lançamento']) ? 1 : 0,
    source_kind: FONTE[plain(p.Fonte)] || null,
  };

  const [existe] = await d1('SELECT id, status FROM works WHERE notion_id = ?', [pg.id]);
  if (existe) {
    // não mexe em status de obra já minerada: só reflete o plano
    await d1(
      `UPDATE works SET title=?, author=?, era=?, priority=?, launch=?, source_kind=COALESCE(?, source_kind),
       status=CASE WHEN status IN ('mined','failed') THEN status ELSE ? END, updated_at=datetime('now') WHERE id=?`,
      [dados.title, dados.author, dados.era, dados.priority, dados.launch, dados.source_kind, status, existe.id]
    );
    atualizadas++;
  } else {
    await d1(
      `INSERT INTO works (notion_id,title,author,era,priority,launch,source_kind,status)
       VALUES (?,?,?,?,?,?,?,?)`,
      [dados.notion_id, dados.title, dados.author, dados.era, dados.priority, dados.launch, dados.source_kind, status]
    );
    novas++;
  }
}

const [{ n: total }] = await d1('SELECT COUNT(*) n FROM works');
const porStatus = await d1('SELECT status, COUNT(*) n FROM works GROUP BY status ORDER BY n DESC');
console.log(`fila: ${novas} novas, ${atualizadas} atualizadas, ${ignoradas} ignoradas (publicadas/cortadas)`);
console.log(`total na fila: ${total}`);
for (const r of porStatus) console.log(`  ${r.status}: ${r.n}`);
await log('queue', null, true, `${novas} novas, ${atualizadas} atualizadas`, Date.now() - t0);
