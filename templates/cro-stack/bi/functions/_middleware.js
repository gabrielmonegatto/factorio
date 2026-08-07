// Guarda de domínio do BI: só serve no(s) domínio(s) próprio(s). Resto = 403.
//
// POR QUE ISTO EXISTE: o Cloudflare Access NÃO consegue proteger um endereço
// `*.pages.dev` — essa zona é da Cloudflare, não sua. Access só cobre hostname
// em zona que você controla. Sem este guarda, o resultado é uma porta trancada
// (bi.suaholding.com, com Access) ao lado de uma porta escancarada
// (<projeto>.pages.dev, sem nada), servindo os MESMOS dados: faturamento, CPA,
// desempenho de criativo. Proteção com desvio conhecido não é proteção.
//
// Efeito colateral aceito: as URLs de conferência de deploy (`<hash>.pages.dev`)
// também respondem 403. Conferência de versão nova é no domínio próprio.
//
// REGRA DE ENDEREÇO: o BI lê dados de TODAS as marcas, então o domínio é da
// HOLDING (bi.suaholding.com), nunca de uma marca — domínio de marca é
// descartável e dá a impressão errada de escopo.

const DOMINIOS_PERMITIDOS = new Set([
  'bi.SUAHOLDING.com.br', // TROCAR: domínio real do BI
]);

export async function onRequest(context) {
  const { request, next } = context;
  const host = (request.headers.get('host') || '').toLowerCase().split(':')[0];

  if (DOMINIOS_PERMITIDOS.has(host)) return next();

  return new Response('Painel disponível apenas no endereço oficial.\n', {
    status: 403,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      // Não indexar, não cachear: endereço bloqueado não vira resultado de
      // busca nem fica preso no navegador de quem tentou.
      'X-Robots-Tag': 'noindex, nofollow',
      'Cache-Control': 'no-store',
    },
  });
}
