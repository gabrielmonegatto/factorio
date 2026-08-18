// CCEL: a melhor fonte. Serve ThML (XML) em <url-da-obra>.xml, com capítulo
// delimitado por <divN title="..."> e metadado Dublin Core. Não precisa adivinhar
// onde começa capítulo, que é o que estraga scrape de HTML solto.
import { fetchPolido } from '../lib.mjs';
import { limparXml, texto } from '../parse.mjs';

export const nome = 'ccel';

export function urlBruta(sourceUrl) {
  const u = sourceUrl.replace(/\/+$/, '').replace(/\.xml$/, '');
  return `${u}.xml`;
}

export async function buscar(sourceUrl) {
  const r = await fetchPolido(urlBruta(sourceUrl));
  if (!r.ok) return { ok: false, erro: `CCEL HTTP ${r.status}${r.erro ? ' ' + r.erro : ''}` };
  if (!/<ThML|<div1|<DC\.Title/i.test(r.body)) return { ok: false, erro: 'resposta não é ThML' };
  return { ok: true, bruto: r.body, contentType: 'application/xml' };
}

export function extrair(xml) {
  const meta = {
    titulo: texto(xml.match(/<DC\.Title[^>]*>([\s\S]*?)<\/DC\.Title>/i)?.[1]),
    autor: texto(xml.match(/<DC\.Creator[^>]*sub="Author"[^>]*>([\s\S]*?)<\/DC\.Creator>/i)?.[1]),
  };

  // Escolhe o nível de divisão que corresponde a CAPÍTULO nesta obra.
  // Em obra simples o div1 já é o capítulo; em tomo com partes o div1 é "Livro I"
  // e o capítulo mora um ou dois níveis abaixo. Sinal de que erramos o nível:
  // poucas peças gigantes (A Imitação de Cristo saiu com 5 peças de 64k chars
  // antes deste ajuste, porque o div1 dela é o livro).
  let caps = [];
  for (const nivel of [1, 2, 3]) {
    const tentativa = fatiarPorDiv(xml, nivel);
    if (!tentativa.length) continue;
    if (!caps.length) { caps = tentativa; continue; }
    // desce de nível só enquanto as peças estiverem grandes demais pra um capítulo
    if (medianaTamanho(caps) > 25000 && tentativa.length > caps.length) caps = tentativa;
    else break;
  }

  const IGNORAR = /^(title page|indexes?|index|table of contents|contents|copyright|about this book|colophon|bibliography|endnotes?|footnotes?)$/i;
  return {
    meta,
    capitulos: caps
      .filter((c) => !IGNORAR.test(c.titulo.trim()))
      .filter((c) => c.corpo.length > 400) // fragmento não é capítulo
      .map((c, i) => ({ numero: i + 1, titulo: c.titulo, corpo: c.corpo })),
  };
}

function fatiarPorDiv(xml, nivel) {
  // regex literal com o nível capturado: montar por string exigiria escape,
  // e escape em template literal já nos custou uma sessão de depuração
  const marcas = [...xml.matchAll(/<div(\d)[^>]*>/gi)].filter((m) => Number(m[1]) === nivel);
  const out = [];
  for (let i = 0; i < marcas.length; i++) {
    const ini = marcas[i].index;
    const fim = i + 1 < marcas.length ? marcas[i + 1].index : xml.length;
    const bloco = xml.slice(ini, fim);
    const titulo = texto(marcas[i][0].match(/title="([^"]*)"/i)?.[1]) || `Seção ${i + 1}`;
    out.push({ titulo, corpo: limparXml(bloco) });
  }
  return out;
}

function medianaTamanho(caps) {
  if (!caps.length) return 0;
  const t = caps.map((c) => c.corpo.length).sort((a, b) => a - b);
  return t[Math.floor(t.length / 2)];
}
