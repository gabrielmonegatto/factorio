#!/usr/bin/env node
// CÂNONE DO BUSINESS SYSTEM (03/09/2026). Constrói os bancos-base e faz as
// fusões, de forma IDEMPOTENTE e NÃO DESTRUTIVA: nada é deletado, banco
// superado é renomeado com prefixo [APOSENTADO] e o Gabriel apaga se quiser.
//
// Fonte do desenho: docs/24_CANONE_NOTION.md. Ids em notion-canone-ids.json.
//   node tools/notion/notion-canone.mjs             simula (não escreve)
//   node tools/notion/notion-canone.mjs --aplicar
//
// Rename PRESERVA o id: script que já aponta pro banco continua funcionando.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV = path.resolve(HERE, '..', '..', '.env');
const IDS_FILE = path.join(HERE, 'notion-canone-ids.json');
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN='))?.slice('NOTION_TOKEN='.length).trim();
const APLICAR = process.argv.includes('--aplicar');

// endereços levantados por API em 03/09/2026
const HUB = '3c1f06f1-0ce3-8117-87df-d894ffd804f9';        // página Factorio
const ECOMMERCE = '3c4f06f1-0ce3-81a7-83be-e16a3ce25e3b';  // página Ecommerce
const AREAS = '3c1f06f1-0ce3-8076-908b-fbcb7b67294c';
const UNIDADES = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';
const AREA_NEGOCIO = '3c1f06f1-0ce3-8195-8fe5-f5ae0374007b';
const AREA_MINERACAO = '3c1f06f1-0ce3-802d-967f-e11713d2ef74';

const EXISTENTES = {
  workflows: '3c7f06f1-0ce3-811c-a6fc-cacd3439ca95',      // vira Esteiras (canônico)
  esteirasV1: '3c1f06f1-0ce3-8167-989b-d56a4207f266',     // aposenta
  metricas: '3c3f06f1-0ce3-81ae-a447-c8ea2f0dbee3',       // funde em Indicadores
  indicadores: '3c1f06f1-0ce3-8196-9da9-e8c5895d2e4d',
  backlogCanais: '3cff06f1-0ce3-8193-84b7-d3202c0a0875',  // vira Canais
  refEditoras: '3c0f06f1-0ce3-813b-94a4-c436be12ede0',    // vira Referências
  experimentos: '45cf06f1-0ce3-8240-a7ac-81ec37f4d89b',   // adotado
};

const ids = fs.existsSync(IDS_FILE) ? JSON.parse(fs.readFileSync(IDS_FILE, 'utf8')) : {};
const save = () => { if (APLICAR) fs.writeFileSync(IDS_FILE, JSON.stringify(ids, null, 2)); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function api(p, method = 'GET', body) {
  for (let tent = 1; ; tent++) {
    await sleep(340);
    try {
      const res = await fetch(`https://api.notion.com/v1/${p}`, {
        method,
        headers: {
          Authorization: `Bearer ${TOKEN}`,
          'Notion-Version': '2022-06-28',
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const j = await res.json();
      if (j.object === 'error' && j.code === 'rate_limited') { await sleep(2500); continue; }
      if (j.object === 'error') { console.error(`  ERRO ${method} ${p}: ${j.code} ${j.message}`); return null; }
      return j;
    } catch (e) {
      if (tent >= 4) { console.error(`  FALHA de rede em ${p}: ${e.message}`); return null; }
      await sleep(tent * 2500);
    }
  }
}

const rt = (s) => [{ type: 'text', text: { content: String(s ?? '').slice(0, 1900) } }];
const tituloDb = (o) => (o.title || []).map((x) => x.plain_text).join('');
const tituloPag = (p) => {
  const t = Object.values(p.properties || {}).find((x) => x.type === 'title');
  return (t?.title || []).map((x) => x.plain_text).join('');
};
const REL = (db) => ({ relation: { database_id: db, single_property: {} } });
const SEL = (...opts) => ({ select: { options: opts.map((o) => (typeof o === 'string' ? { name: o } : o)) } });
const NUM = { number: {} };
const DATE = { date: {} };
const URLP = { url: {} };
const TXT = { rich_text: {} };

// 1. BANCOS NOVOS. Esqueleto mínimo de propósito: coluna se ganha no uso.
const NOVOS = [
  {
    chave: 'fontes', pai: HUB, icone: '⛏️', nome: 'Fontes',
    desc: 'Fontes de mineração. Espelho de AGREGADO: a linha é a fonte; as milhares de obras vivem no D1 e se olham no bi.mananciall.org.',
    props: {
      Fonte: { title: {} },
      Tipo: SEL('site', 'API', 'arquivo', 'parceria'),
      Legalidade: SEL('domínio público', 'licença própria', 'a negociar', 'proibida'),
      'robots.txt': SEL('obedece', 'sem restrição', 'bloqueia'),
      'Obras descobertas': NUM,
      Mineradas: NUM,
      'Na fila': NUM,
      'Última varredura': DATE,
      Painel: URLP,
      'Área': REL(AREAS),
      Notas: TXT,
    },
  },
  {
    chave: 'conteudos', pai: HUB, icone: '🎬', nome: 'Conteúdos',
    desc: 'Peças publicadas em qualquer formato. Macro: o volume e as métricas diárias vivem no D1.',
    props: {
      'Peça': { title: {} },
      Formato: SEL('vídeo longo', 'short', 'post', 'artigo', 'e-mail', 'página'),
      Estado: SEL('ideia', 'produção', 'agendado', 'publicado', 'arquivado'),
      'Publicado em': DATE,
      URL: URLP,
      Unidade: REL(UNIDADES),
      'Área': REL(AREAS),
      Notas: TXT,
    },
  },
  {
    chave: 'pops', pai: HUB, icone: '📗', nome: 'POPs',
    desc: 'Procedimentos padrão: vitrine do catálogo de skills do git (_factorio/.claude/skills). O git é a fonte.',
    props: {
      POP: { title: {} },
      'Quando usar': TXT,
      'Onde vive': TXT,
      'Confiança': SEL({ name: 'nova', color: 'yellow' }, { name: 'provada', color: 'orange' }, { name: 'madura', color: 'green' }),
      Estado: SEL('ativa', 'rascunho', 'aposentada'),
      'Área': REL(AREAS),
    },
  },
  {
    chave: 'recursos', pai: HUB, icone: '🧰', nome: 'Recursos',
    desc: 'Ferramentas, contas e infra: pra que serve, quanto custa, ONDE vive a credencial. Senha nunca entra aqui.',
    props: {
      Recurso: { title: {} },
      Tipo: SEL('SaaS', 'infra', 'API', 'domínio', 'gateway', 'banco'),
      'Pra que serve': TXT,
      'Custo mensal': NUM,
      Moeda: SEL('BRL', 'USD', 'EUR'),
      'Credencial vive em': TXT,
      Estado: SEL('ativo', 'avaliando', 'aposentado'),
      Unidade: REL(UNIDADES),
    },
  },
  {
    // O "Backlog de Canais" (criado e jogado na LIXEIRA em 02/09) NÃO é ressuscitado:
    // banco no lixo é decisão do Gabriel. Nasce limpo, herdando a taxonomia de
    // arquétipo dele. Importar as linhas antigas é um pedido dele, não iniciativa minha.
    chave: 'canais', pai: HUB, icone: '📺', nome: 'Canais',
    desc: 'Canais próprios por marca e plataforma. Espelho de agregado: vídeos e métricas diárias vivem no D1 (eternall-intel).',
    props: {
      Canal: { title: {} },
      Plataforma: SEL('YouTube', 'TikTok', 'Instagram', 'Spotify', 'site'),
      Estado: SEL('no ar', 'esteira', 'backlog', 'P&D', 'encerrado'),
      'Arquétipo': SEL('Treasures', 'Bíblia', 'Best Of', 'Vault', 'Histórias', 'Autoridade'),
      'Cadência': SEL('2/dia', '1/dia', '0.5/dia', 'sem cadência'),
      Publicados: NUM,
      Inscritos: NUM,
      'Atualizado em': DATE,
      Slug: TXT,
      Unidade: REL(UNIDADES),
      Notas: TXT,
    },
  },
  {
    chave: 'ofertas', pai: ECOMMERCE, icone: '🏷️', nome: 'Ofertas',
    desc: 'O que é vendável: produto, preço, página, gateway. Pedidos e visitas ficam no D1.',
    props: {
      Oferta: { title: {} },
      Estado: SEL('rascunho', 'no ar', 'pausada', 'encerrada'),
      'Preço': NUM,
      Moeda: SEL('BRL', 'USD'),
      Gateway: SEL('Mercado Pago', 'Stripe', 'Asaas', 'PayPal', 'B4You', 'lista de espera'),
      'Página': URLP,
      'Vendas 7d': NUM,
      Unidade: REL(UNIDADES),
      Notas: TXT,
    },
  },
];

async function criarNovos() {
  console.log('\n-- 1. bancos novos --');
  for (const b of NOVOS) {
    if (ids[b.chave]) { console.log(`  = ${b.nome} ja existe (${ids[b.chave].slice(0, 8)})`); continue; }
    if (!APLICAR) { console.log(`  + criaria ${b.nome} sob ${b.pai.slice(0, 8)} (${Object.keys(b.props).length} colunas)`); continue; }
    const r = await api('databases', 'POST', {
      parent: { type: 'page_id', page_id: b.pai },
      icon: { type: 'emoji', emoji: b.icone },
      title: rt(b.nome),
      description: rt(b.desc),
      properties: b.props,
    });
    if (!r) continue;
    ids[b.chave] = r.id;
    save();
    console.log(`  + ${b.nome} criado (${r.id.slice(0, 8)})`);
  }
}

async function renomear(id, novoNome, rotulo) {
  const db = await api(`databases/${id}`);
  if (!db) return;
  const atual = tituloDb(db);
  if (atual === novoNome) { console.log(`  = ${rotulo}: ja se chama "${novoNome}"`); return; }
  if (!APLICAR) { console.log(`  ~ ${rotulo}: "${atual}" -> "${novoNome}"`); return; }
  const r = await api(`databases/${id}`, 'PATCH', { title: rt(novoNome) });
  if (r) console.log(`  ~ ${rotulo}: "${atual}" -> "${novoNome}"`);
}

async function addProps(id, props, rotulo) {
  const db = await api(`databases/${id}`);
  if (!db) return;
  const faltando = Object.fromEntries(Object.entries(props).filter(([k]) => !db.properties[k]));
  if (!Object.keys(faltando).length) { console.log(`  = ${rotulo}: colunas ok`); return; }
  if (!APLICAR) { console.log(`  + ${rotulo}: colunas ${Object.keys(faltando).join(', ')}`); return; }
  const r = await api(`databases/${id}`, 'PATCH', { properties: faltando });
  if (r) console.log(`  + ${rotulo}: colunas ${Object.keys(faltando).join(', ')}`);
}

async function fusoes() {
  console.log('\n-- 2. fusoes e adocoes --');
  // 2.1 Esteiras: o banco alimentado pela máquina (ex-Workflows) é o canônico
  await renomear(EXISTENTES.esteirasV1, '[APOSENTADO] Esteiras v1 (fundido em Esteiras)', 'Esteiras v1');
  await renomear(EXISTENTES.workflows, 'Esteiras', 'Workflows');
  await addProps(EXISTENTES.workflows, { 'Área': REL(AREAS) }, 'Esteiras');
  ids.esteiras = EXISTENTES.workflows;

  // 2.2 Canais: sem fusão. Medido em 03/09: o "Backlog de Canais" está na LIXEIRA
  // do Notion (foi criado e descartado em 02/09), e banco no lixo não se ressuscita
  // por iniciativa da máquina. O banco Canais nasce limpo na lista NOVOS.

  // 2.3 Referências
  await renomear(EXISTENTES.refEditoras, 'Referências', 'Referências de Editoras');
  await addProps(EXISTENTES.refEditoras, {
    'Tipo de referência': SEL('obra', 'página', 'criativo', 'canal', 'oferta'),
    Unidade: REL(UNIDADES),
    'Área': REL(AREAS),
  }, 'Referências');
  ids.referencias = EXISTENTES.refEditoras;

  // 2.4 Experimentos: adotado como está, só ganha a costura da casa
  await addProps(EXISTENTES.experimentos, { Unidade: REL(UNIDADES), 'Área': REL(AREAS) }, 'Experimentos');
  ids.experimentos = EXISTENTES.experimentos;

  // 2.5 Indicadores recebe as colunas pra absorver Métricas
  await addProps(EXISTENTES.indicadores, { 'Fórmula': TXT, Notas: TXT }, 'Indicadores');
  ids.indicadores = EXISTENTES.indicadores;
  save();
}

// 3. Métricas -> Indicadores: CÓPIA, o banco original fica intacto
async function migrarMetricas() {
  console.log('\n-- 3. Metricas -> Indicadores --');
  const origem = await api(`databases/${EXISTENTES.metricas}/query`, 'POST', { page_size: 100 });
  const destino = await api(`databases/${EXISTENTES.indicadores}/query`, 'POST', { page_size: 100 });
  if (!origem || !destino) return;
  const jaLa = new Set(destino.results.map(tituloPag));
  const texto = (p) => (p?.rich_text || p?.title || []).map((x) => x.plain_text).join('') || (p?.select?.name ?? '');

  let n = 0;
  for (const linha of origem.results) {
    const nome = tituloPag(linha);
    if (!nome || jaLa.has(nome)) continue;
    const P = linha.properties;
    const notas = [
      texto(P['Por quê']) && `Por que: ${texto(P['Por quê'])}`,
      texto(P['Aba']) && `Aba: ${texto(P['Aba'])}`,
      texto(P['Confiança']) && `Confianca: ${texto(P['Confiança'])}`,
      'migrado do banco Metricas em 03/09/2026',
    ].filter(Boolean).join(' | ');
    if (!APLICAR) { console.log(`  + migraria "${nome}"`); n++; continue; }
    const r = await api('pages', 'POST', {
      parent: { database_id: EXISTENTES.indicadores },
      properties: {
        Indicador: { title: rt(nome) },
        'Como ler': { rich_text: rt(texto(P['Como ler'])) },
        'Fórmula': { rich_text: rt(texto(P['Fórmula'])) },
        Fonte: { rich_text: rt(texto(P['Fontes de dados'])) },
        Notas: { rich_text: rt(notas) },
        'Área': { relation: [{ id: AREA_NEGOCIO }] },
      },
    });
    if (r) { n++; console.log(`  + "${nome}"`); }
  }
  if (n && APLICAR) {
    await renomear(EXISTENTES.metricas, '[APOSENTADO] Métricas (fundido em Indicadores)', 'Métricas');
    ids.metricasMigradas = true;
    save();
  } else if (!n) {
    console.log('  = nada a migrar');
  }
}

// 4. SEMEADURA: banco vazio não é sistema. Só o que a máquina sabe preencher
// sozinha; o resto (Ofertas, Conteúdos, Recursos) nasce vazio e enche no uso.
async function semear() {
  console.log('\n-- 4. semeadura --');

  // 4.1 POPs = vitrine do catálogo de skills do git (a fonte continua sendo o git)
  if (ids.pops) {
    const dir = path.resolve(HERE, '..', '..', '.claude', 'skills');
    const atuais = await api(`databases/${ids.pops}/query`, 'POST', { page_size: 100 });
    const jaLa = new Set((atuais?.results || []).map(tituloPag));
    for (const nome of fs.readdirSync(dir)) {
      const arq = path.join(dir, nome, 'SKILL.md');
      if (!fs.existsSync(arq) || jaLa.has(`/${nome}`)) continue;
      const md = fs.readFileSync(arq, 'utf8');
      const desc = (md.match(/^description:\s*(.+)$/m)?.[1] || '').replace(/^["']|["']$/g, '');
      const conf = /🟢/.test(md) ? 'madura' : /🟠/.test(md) ? 'provada' : 'nova';
      if (!APLICAR) { console.log(`  + POP /${nome}`); continue; }
      const r = await api('pages', 'POST', {
        parent: { database_id: ids.pops },
        properties: {
          POP: { title: rt(`/${nome}`) },
          'Quando usar': { rich_text: rt(desc) },
          'Onde vive': { rich_text: rt(`_factorio/.claude/skills/${nome}/SKILL.md`) },
          'Confiança': { select: { name: conf } },
          Estado: { select: { name: 'ativa' } },
        },
      });
      if (r) console.log(`  + POP /${nome}`);
    }
  }

  // 4.2 Fontes: as fontes de mineração conhecidas. Contadores ficam em branco de
  // propósito: quem preenche é a esteira, não o humano (senão o número mente).
  const FONTES = [
    { nome: 'STEM Publishing', tipo: 'site', legal: 'domínio público', robots: 'obedece',
      nota: 'Acervo dos Brethren. 5.980 obras de 48 autores, 38,4M de palavras EM CASA (mine/stem). Serve de catálogo futuro e de léxico da E5.' },
    { nome: 'CCEL', tipo: 'site', legal: 'domínio público', robots: 'obedece',
      nota: 'Christian Classics Ethereal Library. ThML com referência bíblica marcada (scripRef), que é matéria-prima da fase 2 de enriquecimento.' },
    { nome: 'Acervo Banzoli', tipo: 'parceria', legal: 'a negociar', robots: 'sem restrição',
      nota: '19 livros, 1.114 capítulos importados de PDF. Licença em negociação com o autor; hoje status private no site.' },
  ];
  if (ids.fontes) {
    const atuais = await api(`databases/${ids.fontes}/query`, 'POST', { page_size: 100 });
    const jaLa = new Set((atuais?.results || []).map(tituloPag));
    for (const f of FONTES) {
      if (jaLa.has(f.nome)) continue;
      if (!APLICAR) { console.log(`  + Fonte ${f.nome}`); continue; }
      const r = await api('pages', 'POST', {
        parent: { database_id: ids.fontes },
        properties: {
          Fonte: { title: rt(f.nome) },
          Tipo: { select: { name: f.tipo } },
          Legalidade: { select: { name: f.legal } },
          'robots.txt': { select: { name: f.robots } },
          Painel: { url: 'https://bi.mananciall.org' },
          'Área': { relation: [{ id: AREA_MINERACAO }] },
          Notas: { rich_text: rt(f.nota) },
        },
      });
      if (r) console.log(`  + Fonte ${f.nome}`);
    }
  }
}

async function main() {
  if (!TOKEN) { console.error('NOTION_TOKEN ausente no .env'); process.exit(1); }
  console.log(APLICAR ? '=== CANONE: APLICANDO ===' : '=== CANONE: SIMULACAO (use --aplicar) ===');
  await criarNovos();
  await fusoes();
  await semear();
  // migrarMetricas() NAO roda: medido em 03/09, o banco Metricas tem 40 linhas do
  // Br4nds (MER, ROAS Meta, CPM, fadiga de criativo) e vive na pagina "Catalogo de
  // Metricas". E o catalogo de OUTRO espaco, nao duplicata do Indicadores da fabrica.
  // Fica intocado. A funcao segue no arquivo como referencia de migracao.
  console.log('\nids em', path.relative(process.cwd(), IDS_FILE));
}
main();
