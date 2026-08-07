// Textos BASE do funil: a variante de controle de cada texto testável por A/B.
//
// POR QUE ESTE ARQUIVO EXISTE (e por que é .mjs sem tipos): ele é lido pelos
// DOIS lados. O navegador usa pra renderizar; o PORTEIRO usa pra corrigir o HTML
// pré-renderizado. A primeira tela do funil sai pronta do build: se a variante
// só trocasse o texto no navegador, o React manteria o texto do build na
// hidratação, ou o visitante veria a troca piscar. Sabendo o texto base, o
// porteiro troca no próprio HTML e a variante já chega correta no primeiro byte.
//
// ⚠️ Toda chave testável nasce AQUI. Chave que só existe no experimento não tem
// o que substituir no HTML: a variante nunca aparece e o teste roda vazio, SEM
// ERRO. É o defeito mais caro do motor porque é invisível.
//
// No projeto real, importe estas chaves nos componentes via um helper `txt()`
// que prefere `window.__CRO_CONTENT__` (injetado pelo porteiro) e cai pro base.
// Modelo completo: apps/br4nds/bluue/src/content/{quiz.base.mjs,quiz.ts}.

export const CONTENT_BASE = {
  // 'funil.tela1.titulo': 'Texto exatamente como aparece na página',
};
