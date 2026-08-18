// Project Gutenberg: texto puro, e a busca (gutendex) resolve título -> id,
// então esta é a única fonte que se auto-resolve sem catálogo prévio.
// O texto vem com cabeçalho/rodapé de licença que precisa sair antes de tudo.
import { fetchPolido } from '../lib.mjs';
import { texto } from '../parse.mjs';

export const nome = 'gutenberg';

export async function buscar(sourceUrl) {
  const id = sourceUrl.match(/(?:ebooks\/|epub\/|pg)(\d+)/)?.[1];
  if (!id) return { ok: false, erro: `URL do Gutenberg sem id: ${sourceUrl}` };
  for (const u of [
    `https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt`,
    `https://www.gutenberg.org/files/${id}/${id}-0.txt`,
  ]) {
    const r = await fetchPolido(u);
    if (r.ok && r.body.length > 2000) return { ok: true, bruto: r.body, contentType: 'text/plain' };
  }
  return { ok: false, erro: 'nenhum .txt disponível pra esse id' };
}

export function extrair(txt) {
  // Corta o boilerplate legal do Gutenberg (fica fora do produto).
  let corpo = txt;
  const ini = corpo.match(/\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[\s\S]*?\*\*\*/i);
  if (ini) corpo = corpo.slice(ini.index + ini[0].length);
  const fim = corpo.match(/\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK/i);
  if (fim) corpo = corpo.slice(0, fim.index);

  const titulo = texto(txt.match(/^\s*Title:\s*(.+)$/im)?.[1]);
  const autor = texto(txt.match(/^\s*Author:\s*(.+)$/im)?.[1]);

  // Capítulo em texto puro só existe como convenção tipográfica. Reconhecemos
  // as formas comuns e, se nada bater, entregamos documento único: melhor um
  // bloco honesto do que um corte inventado.
  const linhas = corpo.split(/\r?\n/);
  const CABECA = /^\s{0,20}(CHAPTER|Chapter|LETTER|Letter|SERMON|Sermon|BOOK|Book|PART|Part|SECTION|Section|MEDITATION|DISCOURSE)\s+([IVXLCDM]+|\d+|[A-Z][a-z]+)\b[.:]?\s*$/;
  const cortes = [];
  for (let i = 0; i < linhas.length; i++) if (CABECA.test(linhas[i])) cortes.push(i);

  if (cortes.length < 2) {
    const limpo = normalizar(corpo);
    return { meta: { titulo, autor }, capitulos: limpo.length > 400 ? [{ numero: 1, titulo, corpo: limpo }] : [] };
  }

  const caps = [];
  for (let i = 0; i < cortes.length; i++) {
    const de = cortes[i];
    const ate = i + 1 < cortes.length ? cortes[i + 1] : linhas.length;
    let tituloCap = linhas[de].trim();
    // linha seguinte não-vazia costuma ser o nome do capítulo
    const prox = linhas.slice(de + 1, de + 4).find((l) => l.trim());
    if (prox && prox.trim().length < 90 && !/[.!?]$/.test(prox.trim())) tituloCap += `. ${prox.trim()}`;
    const bloco = normalizar(linhas.slice(de + 1, ate).join('\n'));
    if (bloco.length > 400) caps.push({ numero: caps.length + 1, titulo: tituloCap, corpo: bloco });
  }
  return { meta: { titulo, autor }, capitulos: caps };
}

function normalizar(s) {
  return s.replace(/\r/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n\n').map((p) => p.split('\n').map((l) => l.trim()).join(' ').trim())
    .filter(Boolean).join('\n\n').trim();
}
