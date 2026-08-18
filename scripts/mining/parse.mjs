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
