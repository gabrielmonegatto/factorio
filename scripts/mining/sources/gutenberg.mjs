// Project Gutenberg: texto puro, e a busca (gutendex) resolve título -> id,
// então esta é a única fonte que se auto-resolve sem catálogo prévio.
// O texto vem com cabeçalho/rodapé de licença que precisa sair antes de tudo.
import { fetchPolido } from '../lib.mjs';
import { texto, fatiarPorTamanho, CHARS_POR_MINUTO } from '../parse.mjs';

export const nome = 'gutenberg';

export async function buscar(sourceUrl) {
  const id = sourceUrl.match(/(?:ebooks\/|epub\/|pg)(\d+)/)?.[1];
  if (!id) return { ok: false, erro: `URL do Gutenberg sem id: ${sourceUrl}` };
  // Quatro padrões porque o Gutenberg nunca migrou os antigos: obras novas
  // vivem em cache/epub, as dos anos 2000 em files/{id}/{id}-0.txt, e as mais
  // antigas ainda em files/{id}/{id}.txt (sem o "-0"). Faltava esse último, e
  // era ele que escondia "Sovereign Grace" do Moody — a obra existia, tinha
  // texto puro, e a esteira reportava "nenhum .txt disponível".
  for (const u of [
    `https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt`,
    `https://www.gutenberg.org/files/${id}/${id}-0.txt`,
    `https://www.gutenberg.org/files/${id}/${id}.txt`,
    `https://www.gutenberg.org/ebooks/${id}.txt.utf-8`,
  ]) {
    const r = await fetchPolido(u);
    if (!r.ok) continue;
    // ⚠️ "tem mais de 2000 caracteres" NÃO prova que é o livro. Sob carga o
    // Gutenberg derruba a conexão no meio e devolve um pedaço, que passava
    // por texto completo e virava capítulo picado no banco, silenciosamente.
    // O marcador de FIM é a prova barata de que o download chegou ao fim.
    if (/\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK/i.test(r.body)) {
      return { ok: true, bruto: r.body, contentType: 'text/plain' };
    }
  }
  return { ok: false, erro: 'nenhum .txt COMPLETO disponível (sem marcador de fim)' };
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
  const NOMEADO = /^\s{0,20}(CHAPTER|Chapter|LETTER|Letter|SERMON|Sermon|BOOK|Book|PART|Part|SECTION|Section|MEDITATION|DISCOURSE)\s+([IVXLCDM]+|\d+|[A-Z][a-z]+)\b[.:]?\s*$/;
  // "I. ABRAHAM'S FOUR SURRENDERS" — numeral e título na MESMA linha, sem a
  // palavra "chapter". É como "Men of the Bible" e vários vitorianos dividem,
  // e era o que fazia 7 obras do Moody virarem um bloco único de até 8 horas.
  const NUMERADO = /^\s{0,20}([IVXLCDM]{1,7}|\d{1,3})\.\s+\S.{2,70}$/;

  // Achar candidato é fácil; o difícil é não confundir com lista numerada
  // DENTRO do sermão ("1. Primeiro, o pecado...") ou com número de versículo.
  // O que distingue divisão real é ser uma SEQUÊNCIA: I, II, III em ordem, sem
  // pular. Então coletamos candidatos com o número que declaram e ficamos só
  // com a corrida consecutiva a partir do 1. Sem isso, "Moody's Anecdotes"
  // virava centenas de pedacinhos e perdia 99% do texto no filtro de tamanho.
  const candidatos = [];
  for (let i = 0; i < linhas.length; i++) {
    const m = NOMEADO.exec(linhas[i]) || NUMERADO.exec(linhas[i]);
    if (!m) continue;
    const cru = (NOMEADO.test(linhas[i]) ? m[2] : m[1]).toUpperCase();
    const n = /^\d+$/.test(cru) ? +cru : deRomano(cru);
    if (n) candidatos.push({ linha: i, n });
  }
  let cortes = [];
  let esperado = 1;
  for (const c of candidatos) {
    if (c.n === esperado) { cortes.push(c.linha); esperado++; }
  }

  // TRAVA: divisão de verdade começa perto do início. Quando a sequência só
  // aparece no fim, ela é a LISTA DE ANÚNCIOS da editora ("1. God Reaching
  // Down... 2. ..."), e tratá-la como capítulo jogava o livro inteiro fora
  // como se fosse folha de rosto. Aconteceu com "Moody's Stories" (218k -> 5k).
  if (cortes.length && cortes[0] > linhas.length * 0.4) cortes = [];

  const MIN_CHARS = Math.round(8 * CHARS_POR_MINUTO);   // menos que isso não vira vídeo
  const blocos = [];
  const juntar = (tituloBloco, bruto) => {
    const limpo = normalizar(bruto);
    if (limpo.length <= 400) return;
    // Capítulo achado ainda pode ser grande demais (uma "parte" de 3 horas).
    // Fatiar aqui é o mesmo cuidado, um nível abaixo.
    const partes = fatiarPorTamanho(limpo);
    partes.forEach((p, k) => blocos.push({
      titulo: partes.length > 1 ? `${tituloBloco} (${k + 1}/${partes.length})` : tituloBloco,
      corpo: p,
    }));
  };

  if (cortes.length < 2) {
    // Sem divisão: coletânea de historietas, sermão avulso, prefácio longo.
    // Corta por tamanho em vez de entregar um arquivo innarrável.
    juntar(titulo || 'Parte', corpo);
  } else {
    // O que vem antes do 1º cabeçalho costuma ser rosto de livro e sumário.
    // Só entra se for substancial: prefácio de verdade não pode sumir.
    juntar(`${titulo || 'Obra'}: abertura`, linhas.slice(0, cortes[0]).join('\n'));
    for (let i = 0; i < cortes.length; i++) {
      const de = cortes[i];
      const ate = i + 1 < cortes.length ? cortes[i + 1] : linhas.length;
      let tituloCap = linhas[de].trim();
      // linha seguinte não-vazia costuma completar o nome do capítulo
      const prox = linhas.slice(de + 1, de + 4).find((l) => l.trim());
      if (prox && prox.trim().length < 90 && !/[.!?]$/.test(prox.trim())) tituloCap += `. ${prox.trim()}`;
      juntar(tituloCap, linhas.slice(de + 1, ate).join('\n'));
    }
  }

  // Consolidação: nada abaixo do mínimo sobrevive sozinho, e NADA é descartado.
  // Gruda no bloco anterior; sendo o primeiro, gruda no seguinte.
  const caps = [];
  for (const b of blocos) {
    if (b.corpo.length < MIN_CHARS && caps.length) {
      caps[caps.length - 1].corpo += '\n\n' + b.corpo;
    } else {
      caps.push({ numero: 0, titulo: b.titulo, corpo: b.corpo });
    }
  }
  if (caps.length > 1 && caps[0].corpo.length < MIN_CHARS) {
    caps[1].corpo = caps[0].corpo + '\n\n' + caps[1].corpo;
    caps.shift();
  }
  caps.forEach((c, i) => { c.numero = i + 1; });
  return { meta: { titulo, autor }, capitulos: caps };
}

function normalizar(s) {
  return s.replace(/\r/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n\n').map((p) => p.split('\n').map((l) => l.trim()).join(' ').trim())
    .filter(Boolean).join('\n\n').trim();
}

// Romano -> inteiro. Só serve pra validar sequência de capítulo, então rejeita
// o que não for romano bem-formado (devolve 0) em vez de tentar adivinhar.
function deRomano(s) {
  const V = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
  if (!/^[IVXLCDM]+$/.test(s)) return 0;
  let n = 0;
  for (let i = 0; i < s.length; i++) {
    const a = V[s[i]], b = V[s[i + 1]] || 0;
    n += a < b ? -a : a;
  }
  return n;
}
