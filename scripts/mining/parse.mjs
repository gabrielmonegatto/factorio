// Conversão de marcação pra texto de leitura. Continua sendo texto BRUTO:
// aqui só tiramos marcação, não editamos conteúdo (isso é a fase de limpeza).
const ENTIDADES = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', mdash: '—', ndash: '–',
  lsquo: '‘', rsquo: '’', ldquo: '“', rdquo: '”', hellip: '…', eacute: 'é', aelig: 'æ',
};

export function texto(s) {
  if (!s) return '';
  return desentidade(String(s).replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
}

function desentidade(s) {
  return s
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&([a-z]+);/gi, (m, n) => ENTIDADES[n.toLowerCase()] ?? m);
}

// Remove o que nunca deve virar corpo de livro, em qualquer marcação.
const FORA = /<(script|style|nav|header|footer|noscript|table|form|select)\b[\s\S]*?<\/\1>/gi;

export function limparHtml(html) {
  return blocos(html.replace(FORA, ''));
}

export function limparXml(xml) {
  // Nota de rodapé e aparato crítico do ThML não entram no corpo.
  const semAparato = xml
    .replace(/<note\b[\s\S]*?<\/note>/gi, '')
    .replace(/<pb\b[^>]*\/?>/gi, '')
    .replace(/<(scripCom|scripContext)\b[\s\S]*?<\/\1>/gi, '');
  return blocos(semAparato.replace(FORA, ''));
}

function blocos(marcado) {
  const comQuebra = marcado
    .replace(/<\/(p|div\d?|h[1-6]|li|tr|blockquote)>/gi, '\n\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/?(i|em)>/gi, '*')
    .replace(/<[^>]+>/g, '');
  return desentidade(comQuebra)
    .split('\n\n')
    .map((p) => p.replace(/\s+/g, ' ').trim())
    .filter((p) => p.length > 1)
    .join('\n\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// ── fatiamento por tamanho ───────────────────────────────────────────────────
// Existe porque coletânea não tem capítulo. "Moody's Anecdotes" são centenas
// de historietas em sequência: o extrator não achava divisão (correto, não há)
// e devolvia um bloco de 388k caracteres, quase 8 horas de narração num vídeo.
//
// Regra: nunca corta parágrafo no meio. Melhor um bloco de 55 minutos que
// termina onde o autor terminou um parágrafo do que um de 60 cortado na vírgula.
//
// ~5,6 caracteres por palavra e ~150 palavras por minuto: a conta que a esteira
// já usa pra estimar duração de narração.
export const CHARS_POR_MINUTO = 150 * 5.6;

export function fatiarPorTamanho(corpo, minutosAlvo = 55, minutosMinimo = 8) {
  const alvo = minutosAlvo * CHARS_POR_MINUTO;
  const minimo = minutosMinimo * CHARS_POR_MINUTO;
  if (corpo.length <= alvo * 1.35) return [corpo];

  const paras = corpo.split('\n\n');
  const fatias = [];
  let atual = [];
  let n = 0;
  for (const p of paras) {
    atual.push(p);
    n += p.length + 2;
    if (n >= alvo) { fatias.push(atual.join('\n\n')); atual = []; n = 0; }
  }
  if (atual.length) {
    const resto = atual.join('\n\n');
    // sobra curta demais pra virar vídeo: cola na fatia anterior
    if (resto.length < minimo && fatias.length) fatias[fatias.length - 1] += '\n\n' + resto;
    else fatias.push(resto);
  }
  return fatias;
}
