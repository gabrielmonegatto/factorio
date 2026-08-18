// New Advent: tradução ANF/NPNF dos Padres da Igreja, em HTML.
// Duas formas de página:
//   1. obra inteira numa página só  -> vira 1 capítulo (corte fino fica pra limpeza)
//   2. página ÍNDICE, com a obra dividida em partes -> seguimos as partes
// A forma 2 é comum em obra longa (Homilias, História Eclesiástica, Sacerdócio):
// sem seguir os links, essas obras falhavam como "0 capítulos".
import { fetchPolido } from '../lib.mjs';
import { limparHtml, texto } from '../parse.mjs';

export const nome = 'newadvent';
const MIN_CORPO = 400;
const MAX_PARTES = 60;
const LIMIAR_OBRA_INTEIRA = 60000; // acima disso a própria página já é a obra

export async function buscar(sourceUrl) {
  const r = await fetchPolido(sourceUrl);
  if (!r.ok) return { ok: false, erro: `New Advent HTTP ${r.status}${r.erro ? ' ' + r.erro : ''}` };

  const corpo = corpoDaPagina(r.body);
  const partes = linksDeParte(r.body, sourceUrl);

  // Página grande e sem partes: é a obra inteira, acabou.
  // Página pequena COM partes: quase certamente índice. Mas não decidimos no
  // olho: baixamos as partes e ficamos com o lado que tiver mais texto. Foi essa
  // checagem que pegou "The City of God" entrando no banco com 8 KB (era o índice)
  // quando a obra tem mais de um milhão de caracteres.
  if (!partes.length || corpo.length >= LIMIAR_OBRA_INTEIRA) {
    if (corpo.length >= MIN_CORPO) return { ok: true, bruto: r.body, contentType: 'text/html' };
    return { ok: false, erro: 'página sem corpo e sem links de parte' };
  }

  const baixadas = [];
  for (const url of partes.slice(0, MAX_PARTES)) {
    const p = await fetchPolido(url);
    if (!p.ok) continue;
    const c = corpoDaPagina(p.body);
    if (c.length >= MIN_CORPO) baixadas.push({ url, titulo: tituloDaPagina(p.body), corpo: c });
  }

  const totalPartes = baixadas.reduce((a, p) => a + p.corpo.length, 0);
  if (totalPartes <= corpo.length) {
    if (corpo.length >= MIN_CORPO) return { ok: true, bruto: r.body, contentType: 'text/html' };
    return { ok: false, erro: `índice com ${partes.length} links, nenhuma parte com texto` };
  }

  return {
    ok: true,
    bruto: JSON.stringify({ indice: true, titulo: tituloDaPagina(r.body), partes: baixadas }),
    contentType: 'application/json',
  };
}

export function extrair(bruto) {
  if (bruto.startsWith('{')) {
    const pacote = JSON.parse(bruto);
    return {
      meta: { titulo: pacote.titulo, autor: '' },
      capitulos: pacote.partes.map((p, i) => ({ numero: i + 1, titulo: p.titulo || `Parte ${i + 1}`, corpo: p.corpo })),
    };
  }
  const titulo = tituloDaPagina(bruto);
  const corpo = corpoDaPagina(bruto);
  return { meta: { titulo, autor: '' }, capitulos: corpo.length >= MIN_CORPO ? [{ numero: 1, titulo, corpo }] : [] };
}

function tituloDaPagina(html) {
  return texto(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1])
    .replace(/\s*\|\s*New Advent.*$/i, '')
    .replace(/^CHURCH FATHERS:\s*/i, '');
}

function corpoDaPagina(html) {
  let corpo = html;
  const ini = corpo.search(/<h1\b/i);
  if (ini > 0) corpo = corpo.slice(ini);
  corpo = corpo.split(/<div[^>]*(?:id|class)="(?:footer|copyright)"/i)[0];
  return limparHtml(corpo)
    .replace(/^\s*(?:Home|Encyclopedia|Fathers|Summa|Bible|Library)\b.*$/gim, '')
    .replace(/About this page\b[\s\S]*$/i, '')
    .replace(/Please help support the mission of New Advent[\s\S]*?\.\s*/gi, '')
    .trim();
}

// Links pras partes da mesma obra: /fathers/NNNNXX.htm, ordenados e sem repetição.
function linksDeParte(html, base) {
  const raiz = new URL(base);
  const meuId = raiz.pathname.match(/\/fathers\/(\d{4})/)?.[1];
  const vistos = new Set();
  const out = [];
  for (const m of html.matchAll(/href="([^"]*\/?fathers\/(\d{4,6})[a-z]?\.htm)"/gi)) {
    const url = new URL(m[1], base).href;
    const id = m[2];
    if (url === base || vistos.has(url)) continue;
    // Parte da MESMA obra: o id da parte ESTENDE o id do índice (2601 -> 260101).
    // Comparar só os 2 primeiros dígitos juntava obras diferentes no mesmo livro.
    if (!meuId || id.length <= meuId.length || !id.startsWith(meuId)) continue;
    vistos.add(url);
    out.push(url);
  }
  return out.sort();
}
