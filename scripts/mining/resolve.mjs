// ETAPA 2: RESOLVER. Uma obra no plano é "título + autor"; minerar exige URL.
// Esta etapa descobre a URL, em três vias, da mais confiável pra menos:
//   1. content_index do Teable (543 URLs já catalogadas: CCEL e New Advent)
//   2. gutendex (API de busca do Project Gutenberg)
//   3. nada bateu -> fica sem resolver, com nota, pra decisão humana
//
// Cada casamento leva NOTA DE CONFIANÇA. Casar obra errada envenena o acervo,
// então abaixo do corte a obra não avança sozinha.
//
// Uso: node scripts/mining/resolve.mjs [--limite N] [--refazer]
import { d1, env, fetchPolido, log, sleep } from './lib.mjs';

const args = process.argv.slice(2);
const LIMITE = Number(args[args.indexOf('--limite') + 1]) || 500;
const REFAZER = args.includes('--refazer');
const CORTE = 0.55;

// ── normalização pra comparar título de livro (artigo e pontuação não contam)
const norm = (s) => (s || '').toLowerCase()
  .normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/[^a-z0-9 ]/g, ' ')
  .replace(/\b(the|a|an|of|on|to|in|and|or|st|saint)\b/g, ' ')
  .replace(/\s+/g, ' ').trim();

const tokens = (s) => new Set(norm(s).split(' ').filter((w) => w.length > 2));

// Similaridade por sobreposição de palavras, normalizada pelo MAIOR conjunto.
// Normalizar pelo menor (o erro da 1ª versão) faz título curto casar com tudo:
// "On Prayer" batia 1.00 com "With Christ in the School of Prayer" e a esteira
// minerou um documento dos Padres da Igreja achando que era Andrew Murray.
function similaridade(a, b) {
  const A = tokens(a), B = tokens(b);
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const w of A) if (B.has(w)) inter++;
  return inter / Math.max(A.size, B.size);
}

// Casamento só vale se o autor concordar, ou se o título for quase idêntico.
// Sem isso, obra de século errado entra no acervo sem ninguém perceber.
function aceitavel(sTitulo, sAutor) {
  return sAutor >= 0.3 || sTitulo >= 0.9;
}

// ── 1. catálogo de descoberta que já existe no Teable
async function carregarContentIndex() {
  const U = env.TEABLE_URL, T = env.TEABLE_TOKEN;
  let skip = 0, todos = [];
  while (true) {
    const r = await fetch(`${U}/api/table/tblD7Kxoc7gFTgEWoWo/record?take=1000&skip=${skip}&fieldKeyType=name`,
      { headers: { Authorization: `Bearer ${T}` } });
    const j = await r.json();
    if (!j.records?.length) break;
    todos.push(...j.records.map((x) => x.fields));
    skip += j.records.length;
    if (j.records.length < 1000) break;
  }
  return todos.filter((r) => r.source_url);
}

// A fonte é decidida pelo ENDEREÇO, nunca pelo rótulo do plano nem do catálogo.
// Confiar no rótulo fez URL da Wikipedia ser minerada com adapter do Gutenberg:
// 10 das 14 falhas da primeira rodada real vieram só disso.
function fonteDaUrl(url) {
  const h = (() => { try { return new URL(url).host; } catch { return ''; } })();
  if (h.includes('ccel.org')) return 'ccel';
  if (h.includes('gutenberg.org')) return 'gutenberg';
  if (h.includes('newadvent.org')) return 'newadvent';
  if (h.includes('archive.org')) return 'archive';
  return null; // inclusive Wikipedia: artigo SOBRE a obra não é a obra
}

function acharNoIndex(obra, indice) {
  let melhor = null;
  for (const c of indice) {
    const kind = fonteDaUrl(c.source_url);
    if (!kind) continue; // sem fonte minerável (Wikipedia e afins) não é candidato
    const s = similaridade(obra.title, c.title || c.Name);
    const sa = similaridade(obra.author, c.author);
    if (!aceitavel(s, sa)) continue;
    const nota = Math.min(1, s * 0.7 + sa * 0.3);
    if (nota > (melhor?.nota ?? 0)) melhor = { nota, s, sa, c, kind };
  }
  if (!melhor || melhor.nota < CORTE) return null;
  return {
    url: melhor.c.source_url,
    kind: melhor.kind,
    nota: melhor.nota,
    via: `content_index (${melhor.c.font_id})`,
  };
}

// ── 2. Project Gutenberg
async function acharNoGutenberg(obra) {
  const q = encodeURIComponent(`${obra.title} ${(obra.author || '').split(/[,(]/)[0]}`.slice(0, 120));
  const r = await fetchPolido(`https://gutendex.com/books?search=${q}`, { minIntervalo: 900 });
  if (!r.ok) return null;
  let j; try { j = JSON.parse(r.body); } catch { return null; }
  let melhor = null;
  for (const b of (j.results || []).slice(0, 10)) {
    // sem texto puro não há o que minerar (há registro só com áudio ou imagem)
    const temTxt = Object.keys(b.formats || {}).some((k) => k.startsWith('text/plain'));
    if (!temTxt) continue;
    const s = similaridade(obra.title, b.title);
    const sa = Math.max(0, ...(b.authors || []).map((a) => similaridade(obra.author, a.name)));
    if (!aceitavel(s, sa)) continue;
    // empate de título: fica a edição mais baixada, que é a canônica
    const nota = Math.min(1, s * 0.7 + sa * 0.3) + Math.min(0.05, (b.download_count || 0) / 2e6);
    if (nota > (melhor?.nota ?? 0)) melhor = { nota, b, s };
  }
  if (!melhor) return null;
  return {
    url: `https://www.gutenberg.org/ebooks/${melhor.b.id}`,
    kind: 'gutenberg',
    nota: Math.min(1, melhor.nota),
    via: `gutendex #${melhor.b.id}`,
  };
}

// ── execução
const t0 = Date.now();
// Retomável: obra já examinada tem resolve_note e não é reexaminada sem --refazer.
// Sem isso, uma rodada interrompida recomeça do zero e gasta o intervalo educado à toa.
const filtro = REFAZER ? "status IN ('queued','resolved')" : "status = 'queued' AND source_url IS NULL AND resolve_note IS NULL";
const fila = await d1(
  `SELECT id,title,author,source_kind FROM works WHERE ${filtro}
   ORDER BY launch DESC, CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, id LIMIT ?`, [LIMITE]);
console.log(`resolvendo ${fila.length} obras...`);

const indice = await carregarContentIndex();
console.log(`content_index: ${indice.length} URLs disponíveis`);

let ok = 0, semNada = 0, fracos = 0;
for (const obra of fila) {
  const candidatos = [acharNoIndex(obra, indice), await acharNoGutenberg(obra)].filter(Boolean);
  // fonte declarada no plano tem preferência em empate
  candidatos.sort((a, b) => (b.nota + (b.kind === obra.source_kind ? 0.1 : 0)) - (a.nota + (a.kind === obra.source_kind ? 0.1 : 0)));
  const escolha = candidatos[0];

  if (!escolha) {
    await d1(`UPDATE works SET resolve_note=?, updated_at=datetime('now') WHERE id=?`,
      ['sem candidato em content_index nem Gutenberg', obra.id]);
    semNada++;
    continue;
  }
  const forte = escolha.nota >= 0.7;
  if (!forte) fracos++; else ok++;
  await d1(
    `UPDATE works SET source_url=?, source_kind=COALESCE(?,source_kind), resolve_score=?, resolve_note=?,
     status=CASE WHEN ? THEN 'resolved' ELSE status END, updated_at=datetime('now') WHERE id=?`,
    [escolha.url, escolha.kind, escolha.nota, `${escolha.via} · conf ${escolha.nota.toFixed(2)}${forte ? '' : ' · FRACO: confirmar na mão'}`,
     forte ? 1 : 0, obra.id]
  );
}

console.log(`\nresolvidas: ${ok} confiáveis · ${fracos} fracas (marcadas, não avançam) · ${semNada} sem candidato`);
const porFonte = await d1(`SELECT source_kind, COUNT(*) n FROM works WHERE status='resolved' GROUP BY source_kind`);
for (const r of porFonte) console.log(`  ${r.source_kind || '(sem fonte)'}: ${r.n}`);
await log('resolve', null, true, `${ok} ok, ${fracos} fracas, ${semNada} sem candidato`, Date.now() - t0);
