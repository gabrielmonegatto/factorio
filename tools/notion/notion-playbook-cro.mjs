#!/usr/bin/env node
// PLAYBOOK "Stack de Conversão" — sobe o ecossistema de conversão pro catálogo Playbooks.
// Fonte: .claude/skills/stack-conversao/SKILL.md (extraída da operação real da Bluue).
// Formato v3: linha no catálogo + banco inline "Etapas" (fases macro -> tarefas).
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const DB_PB = '3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2';
const DB_ICON = { type: 'external', external: { url: 'https://www.notion.so/icons/database_green.svg' } };

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(p, body, method = 'POST') {
  for (let t = 1; ; t++) {
    await sleep(360);
    try {
      const res = await fetch(`https://api.notion.com/v1/${p}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const j = await res.json();
      if (!res.ok) { console.error(`✗ ${method} ${p}:`, JSON.stringify(j).slice(0, 400)); throw new Error(j.message); }
      return j;
    } catch (e) { if (t >= 4 || e.message !== 'fetch failed') throw e; await sleep(t * 3000); }
  }
}
const txt = c => [{ type: 'text', text: { content: c } }];
const rt = s => {
  const out = []; const re = /\*\*(.+?)\*\*/g; let last = 0, m;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push({ type: 'text', text: { content: s.slice(last, m.index) } });
    out.push({ type: 'text', text: { content: m[1] }, annotations: { bold: true } });
    last = m.index + m[0].length;
  }
  if (last < s.length) out.push({ type: 'text', text: { content: s.slice(last) } });
  return out.length ? out : txt(s);
};
const p = s => ({ object: 'block', type: 'paragraph', paragraph: { rich_text: rt(s) } });
const h2 = s => ({ object: 'block', type: 'heading_2', heading_2: { rich_text: txt(s) } });
const bullet = s => ({ object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: rt(s) } });
const num = s => ({ object: 'block', type: 'numbered_list_item', numbered_list_item: { rich_text: rt(s) } });
const code = (s, lang = 'plain text') => ({ object: 'block', type: 'code', code: { rich_text: txt(s), language: lang } });
const callout = (s, emoji, color) => ({ object: 'block', type: 'callout', callout: { rich_text: rt(s), icon: { type: 'emoji', emoji }, color } });
const divider = () => ({ object: 'block', type: 'divider', divider: {} });

const AREAS = [
  { name: 'Infra', color: 'gray' }, { name: 'Dados', color: 'blue' },
  { name: 'Tráfego', color: 'orange' }, { name: 'Webdesign', color: 'purple' },
  { name: 'Estrategista', color: 'green' }, { name: 'QA', color: 'red' },
];

// ── conteúdo da PÁGINA do playbook (a doutrina) ────────────────────────
const CICLO = `anúncio ─→ clique (fbclid) ─→ PORTEIRO cria sessão + crachá (_fbp/_fbc)
                                   │
                              páginas do funil ─→ eventos internos (etapas)
                                   │                e canônicos (Lead, IC) → CAPI
                              checkout leva sck = id da sessão
                                   │
                       venda PAGA volta do caixa (webhook/API)
                                   │
                       WORKER casa venda ↔ sessão pelo sck
                                   │
              Purchase no pixel certo, com o NOME certo e 14 parâmetros`;

const PRINCIPIOS = [
  '**Sessão nasce no servidor.** O porteiro cria `_bnd_sid`, `_fbp` e `_fbc` antes de qualquer JS rodar. Bloqueador não alcança, e 100% das visitas têm identidade.',
  '**Config declara FATO, não categoria.** "A raiz deste domínio serve /quiz/v1/", nunca "este domínio é do tipo funil". Categoria envelhece e o código deduz errado.',
  '**1 venda = 1 evento.** `event_id = sale_id`, com livro-caixa (`purchases_sent`) que registra cada envio e recusa duplicata.',
  '**Falha abre.** Motor de A/B, scripts de terceiro, config: qualquer erro devolve a página normal. Quem paga a página quebrada é o anúncio.',
  '**O pixel recebe hoje o que recebia ontem.** Nome de evento E parâmetros. Conjunto ativo otimiza num evento custom com nome herdado; EMQ alto vem de mandar TODOS os parâmetros.',
  '**Compare conteúdo RENDERIZADO, nunca título ou nome de arquivo.** Páginas do mesmo site herdam o title do layout; SPA serve casca vazia.',
  '**Anúncio ativo é intocável.** URL de anúncio não se edita (volta pra revisão e zera aprendizado). A estrutura muda POR BAIXO do anúncio: DNS, rotas, config.',
];

const ERROS = [
  ['Comparar página por título/arquivo', 'rota "igual" com conteúdo diferente', 'renderizar e comparar texto'],
  ['Categoria roteando (role=funil)', 'raiz servindo página errada', 'root_route explícito (fato)'],
  ['200-fallback + immutable', 'tela branca permanente pra alguns visitantes', '404 real + BUILD_TAG'],
  ['Nome canônico em conjunto treinado no custom', 'conversões zeram no Ads Manager', 'event_map por domínio'],
  ['EMQ regredindo na troca de rastreador', 'nota cai, CPA sobe dias depois', 'paridade parâmetro a parâmetro'],
  ['Venda da tela de obrigado', 'pix invisível, algoritmo aprende só cartão', 'worker no caixa + sck'],
  ['Fuso do gateway', 'janelas curtas voltam vazias', 'comparar NOW() com venda recente'],
  ['API da Meta paginada/filtro frouxo', 'inventário e contagens subestimados', 'paginar sempre, conferir status'],
  ['Chunk com nome "adv"', 'página em branco só pra quem tem adblock', 'nome interno neutro'],
  ['Framer-motion em botão de entrada (React 19)', 'clique morto, funil congela', 'botão nativo, sem exit no switcher'],
  ['Editar URL de anúncio ativo', 'revisão + aprendizado zerado', 'duplicar, nunca editar'],
  ['Prova social com números divergentes', '4 números diferentes no mesmo funil', 'um número, o do anúncio'],
];

// ── as 9 fases e suas tarefas ──────────────────────────────────────────
const FASES = [
  ['Fase 0 · Coleta', 'Estrategista', 'Antes de tocar em qualquer código. Respostas erradas aqui viram erro silencioso depois. Colete por API e por RENDERIZAÇÃO, nunca por suposição.', [
    ['Mapear domínios e papéis (o que a RAIZ de cada um serve, abrindo no navegador)', 'Estrategista'],
    ['Listar anúncios ativos via API da Meta COM paginação e conferindo effective_status linha a linha', 'Tráfego'],
    ['Levantar pixel e evento de otimização por conjunto ativo (promoted_object.pixel_id + custom_event_str)', 'Tráfego'],
    ['Registrar EMQ atual (print do painel do pixel) como linha de base da Fase 3', 'Tráfego'],
    ['Mapear checkout: plataforma, campo de repasse (sck/src/custom_id), como a venda paga volta, e o FUSO do banco deles', 'Dados'],
    ['Mapear rastreio atual (Stape/GTM/pixel) e quem alimenta o pixel hoje. Só morre depois da paridade provada na Fase 8', 'Tráfego'],
  ]],
  ['Fase 1 · Banco (D1)', 'Dados', 'Aplicar d1/*.sql na ordem. Cada tabela tem um papel único.', [
    ['domain_config: 1 linha por domínio (pixel, event_map, root_route, scripts, checkout, Clarity). É o que torna domínio descartável', 'Dados'],
    ['data_tracker: todo evento (PageView, etapas, canônicos) com sessão, crachás e variante de A/B', 'Dados'],
    ['quizzes/leads: respostas capturadas COM session_id (sem ele a venda não chega nas respostas)', 'Dados'],
    ['purchases_sent: livro-caixa de vendas (casamento, envio, resposta da Meta). Dedup e auditoria', 'Dados'],
    ['experiments: testes A/B. O banco RECUSA teste sem hipótese e encerramento sem decisão (CHECKs)', 'Dados'],
  ]],
  ['Fase 2 · Porteiro (middleware)', 'Infra', 'O coração. Em cada requisição: cria/renova sessão e crachás, resolve root_route, sorteia variante de A/B, injeta conteúdo e scripts, grava PageView.', [
    ['404 real obrigatório (src/pages/404.astro). Sem ele + immutable, chunk vira HTML cacheado por 1 ano = tela branca permanente', 'Infra'],
    ['Só gravar pageview de resposta < 400 (robô varrendo /.env não vira funil)', 'Infra'],
    ['Coluna scripts agnóstica (JSON por domínio). Tag de terceiro entra por config, sem nome de fornecedor no código', 'Infra'],
    ['Cache de config de 60s no isolado, e falha de leitura NÃO entra no cache', 'Infra'],
    ['Astro em output static, SEM adapter Cloudflare (adapter gera _worker.js e o Pages ignora functions/ em silêncio)', 'Infra'],
    ['Nome de chunk sem "adv" (bloqueador derruba script cujo nome casa com adv/advert)', 'Webdesign'],
    ['BUILD_TAG no DOM de componentes críticos, pra girar o hash do chunk quando cache for envenenado', 'Webdesign'],
  ]],
  ['Fase 3 · Eventos (CAPI)', 'Tráfego', 'functions/api/tracker.js. No banco fica sempre o canônico; só a Meta recebe o espelhado.', [
    ['event_map por domínio traduz o nome NA SAÍDA (Purchase → p)', 'Tráfego'],
    ['internal_only: etapas do funil ficam SÓ no banco (subir isso polui painel e aprendizado)', 'Tráfego'],
    ['Paridade de EMQ: enviar TODOS os 14 parâmetros com SHA-256, normalizando zp/ct/st/country antes do hash', 'Tráfego'],
    ['ge é INFERÊNCIA pelo primeiro nome: declarar no código, calibrar com nomes reais, fallback é decisão de PÚBLICO', 'Tráfego'],
    ['Dedup navegador+servidor: o MESMO id nos dois canais (eventID no fbq, event_id no CAPI)', 'Tráfego'],
  ]],
  ['Fase 4 · Vendas (purchase-check)', 'Dados', 'Cron de 5min: busca vendas PAGAS no caixa, dedup no livro-caixa, casa pelo sck, envia Purchase, registra resposta.', [
    ['Checkout precisa levar ?sck=<session_id>. É o fio que volta na venda e fecha o ciclo', 'Dados'],
    ['Adapter por gateway: a consulta de vendas é a única parte acoplada (outra plataforma = reescrever só fetchPaidSales)', 'Dados'],
    ['Conferir o fuso: NOW() do banco do gateway contra date_update de uma venda recém-paga ANTES de confiar em janelas', 'Dados'],
    ['Venda sem casamento fica unmatched e NÃO sobe (venda de funil alheio não pode sujar o pixel)', 'Dados'],
    ['Se o gateway devolver endereço, é daqui que saem zp/ct/st/country: hash, envia, descarta (não grava)', 'Dados'],
    ['Opcional: webhook como CAMPAINHA (autentica, loga, dispara rodada imediata). O cron NUNCA sai', 'Infra'],
  ]],
  ['Fase 5 · Teste A/B', 'Estrategista', 'Motor no porteiro (sorteio FNV-1a por sessão, cache 60s, falha aberta). Operação completa na skill teste-ab-bluue.', [
    ['Texto testável precisa existir num arquivo-base lido pelo porteiro E pelo navegador (chave sem base = variante que nunca aparece)', 'Webdesign'],
    ['Conferência do sorteio é EM PAR: mesma sessão sempre na mesma variante E sessões diferentes se dividindo', 'QA'],
  ]],
  ['Fase 6 · Backup e BI', 'Dados', 'Backup sem restore provado não é backup.', [
    ['Backup semanal D1 → R2 com restauração TESTADA (workers/backup-d1: NDJSON fatiado + manifest + restore.mjs)', 'Infra'],
    ['BI (Evidence) é da HOLDING, não da marca: domínio neutro, atrás de Cloudflare Access com provedor One-time PIN CRIADO', 'Dados'],
    ['Guarda de host do BI muda JUNTO com o DNS (Access não cobre *.pages.dev)', 'Infra'],
    ['Dado individual de saúde NUNCA no BI público: exportação local sob demanda', 'Dados'],
  ]],
  ['Fase 7 · QA antes de tráfego', 'QA', 'Bateria automatizada (modelo: bluue/scripts/qa-virada.mjs).', [
    ['Rodar bateria: roteamento por domínio sem vazar redirect, sessão e crachás, nomes de evento, scripts, dedup, sorteio em par, 404, painéis', 'QA'],
    ['Se houver triagem/gate: testar cada bloqueio E o teste de CONTROLE (a combinação que NÃO pode bloquear)', 'QA'],
    ['Compra real no cartão E no pix: gerar o código, FECHAR a aba, pagar depois. É o caso que estrutura antiga perde', 'QA'],
    ['Conferir upsell abrindo a oferta certa', 'QA'],
  ]],
  ['Fase 8 · A virada (domínio com anúncio ativo)', 'Tráfego', 'Uma variável por vez. Leitura limpa só com 24h completas.', [
    ['Ensaio seco: Purchase fictício com test_event_code no pixel de produção, nome espelhado e user_data completo', 'Tráfego'],
    ['Paridade de EMQ provada ANTES de desligar o rastreio antigo', 'Tráfego'],
    ['Anotar o rollback antes de ir: registro DNS atual, id, destino. Volta em 2 minutos sem tocar em anúncio', 'Infra'],
    ['Virar no vale de tráfego (um domínio vive em UM projeto Pages; a troca tem janela de certificado)', 'Infra'],
    ['Primeira hora olhando o livro-caixa: primeira venda real tem que gravar o pixel certo + HTTP 200', 'Tráfego'],
    ['Segurar TODAS as outras variáveis por 24h (orçamento, criativo, página)', 'Tráfego'],
  ]],
];

// ═══ 1. garantir opção "Infraestrutura" no Tipo ═══
console.log('▸ 1/4 preparando catálogo...');
const cat = await api(`databases/${DB_PB}`, null, 'GET');
const tipos = cat.properties['Tipo'].select.options.map(o => ({ id: o.id, name: o.name, color: o.color }));
if (!tipos.some(o => o.name === 'Infraestrutura')) {
  tipos.push({ name: 'Infraestrutura', color: 'gray' });
  await api(`databases/${DB_PB}`, { properties: { 'Tipo': { select: { options: tipos } } } }, 'PATCH');
  console.log('  ✓ tipo "Infraestrutura" criado');
}

// ═══ 2. criar a linha do playbook com a doutrina na página ═══
console.log('▸ 2/4 criando o playbook...');
const corpo = [
  callout('Fonte: skill stack-conversao, extraída da operação real da Bluue (R$40k+/semana em tráfego). Cada regra aqui custou dinheiro ou quase custou. Kit de arquivos em _factorio/templates/cro-stack/; implementação-modelo em apps/br4nds/bluue (sempre mais viva que o kit).', '📌', 'gray_background'),
  h2('O ciclo que ela fecha'),
  code(CICLO),
  p('O que faz esta stack valer mais que um pixel no navegador: **a venda sobe do caixa, não da tela de obrigado** (metade das vendas é pix pago com a aba fechada), e **cada venda casa deterministicamente com a sessão que a gerou** (pelo sck, não por email, que falha quando a pessoa compra com outro email).'),
  h2('Os 7 princípios (o porquê antes do como)'),
  ...PRINCIPIOS.map(num),
  h2('Nível de instalação'),
  bullet('**Marca nova na MESMA conta Cloudflare**: 1 INSERT em domain_config + secret META_TOKEN_<MARCA> + domínio no projeto Pages. Custo: minutos.'),
  bullet('**Projeto novo (outra conta, cliente, parceiro)**: as Fases 0 a 8. Custo: 1 a 2 dias de encanamento.'),
  divider(),
  h2('Os erros que esta stack já cometeu'),
  ...ERROS.map(([erro, sintoma, antidoto]) => bullet(`**${erro}** → ${sintoma}. Antídoto: ${antidoto}.`)),
];
const pb = await api('pages', {
  parent: { database_id: DB_PB },
  icon: { type: 'external', external: { url: 'https://www.notion.so/icons/link_gray.svg' } },
  properties: {
    'Playbook': { title: txt('Stack de Conversão') },
    'Tipo': { select: { name: 'Infraestrutura' } },
    'Status': { select: { name: 'Ativo' } },
    'Descrição': { rich_text: txt('Ecossistema de conversão completo: sessão first-party, eventos server-side, casamento de venda pelo sck, teste A/B, backup, QA e virada de domínio. 9 fases, do levantamento à virada com anúncio ativo.') },
  },
  children: corpo,
});
console.log(`  ✓ ${pb.id}`);

// ═══ 3. banco inline "Etapas" ═══
console.log('▸ 3/4 criando banco inline Etapas...');
const inline = await api('databases', {
  parent: { type: 'page_id', page_id: pb.id },
  is_inline: true,
  icon: DB_ICON,
  title: txt('Etapas'),
  description: txt('Fases 0 a 8 da instalação. Duplicar a página do playbook copia esta árvore junto.'),
  properties: {
    'Etapa': { title: {} },
    'Ordem': { number: {} },
    'Área': { multi_select: { options: AREAS } },
    'Notas': { rich_text: {} },
  },
});
await api(`databases/${inline.id}`, {
  properties: { 'Etapa principal': { relation: { database_id: inline.id, type: 'dual_property', dual_property: {} } } },
}, 'PATCH');
{
  const d = await api(`databases/${inline.id}`, null, 'GET');
  const r = {};
  for (const [n, pr] of Object.entries(d.properties))
    if (pr.type === 'relation' && n.startsWith('Related to') && n.includes('(Etapa principal)')) r[n] = { name: 'Subetapas' };
  if (Object.keys(r).length) await api(`databases/${inline.id}`, { properties: r }, 'PATCH');
}
console.log(`  ✓ ${inline.id}`);

// ═══ 4. popular fases e tarefas ═══
console.log('▸ 4/4 populando...');
let nF = 0, nT = 0;
for (let i = 0; i < FASES.length; i++) {
  const [nome, area, nota, tarefas] = FASES[i];
  const fase = await api('pages', {
    parent: { database_id: inline.id },
    properties: {
      'Etapa': { title: txt(nome) },
      'Ordem': { number: i },
      'Área': { multi_select: [{ name: area }] },
      'Notas': { rich_text: txt(nota) },
    },
  });
  nF++;
  console.log(`  ▪ ${nome} (${tarefas.length} tarefas)`);
  for (const [t, a] of tarefas) {
    await api('pages', {
      parent: { database_id: inline.id },
      properties: {
        'Etapa': { title: txt(t.slice(0, 200)) },
        'Área': { multi_select: [{ name: a }] },
        'Etapa principal': { relation: [{ id: fase.id }] },
      },
    });
    nT++;
  }
}

console.log(`\n✅ playbook "Stack de Conversão": ${nF} fases, ${nT} tarefas`);
console.log(`   ${pb.url}`);
fs.writeFileSync(new URL('./notion-playbook-cro-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ page: pb.id, inlineDb: inline.id }, null, 2));
