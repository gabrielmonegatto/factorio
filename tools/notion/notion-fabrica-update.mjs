#!/usr/bin/env node
// Atualiza a página 🏭 Fábrica com o ESTADO REAL medido em 19/08/2026 (noite):
//  - gates do Content que já estavam resolvidos (canal publicando 1/dia no canal certo)
//  - entregas da unificação de dados (Teable → D1/R2, trigger.dev fora)
//  - metas candidatas na página de cada área (o Gabriel escolhe)
//  - indicadores com valor medido
// Idempotente: acha a linha pelo título e faz PATCH; só cria o que não existe.
//
//   node tools/notion/notion-fabrica-update.mjs

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();
const ids = JSON.parse(fs.readFileSync(path.join(HERE, 'notion-fabrica-ids.json'), 'utf8'));
const TASKS_DB = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(p, method = 'GET', body) {
  for (let t = 1; ; t++) {
    await sleep(330);
    const res = await fetch(`https://api.notion.com/v1/${p}`, {
      method,
      headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    const j = await res.json();
    if (j.object === 'error' && j.code === 'rate_limited' && t < 4) { await sleep(2500); continue; }
    return j;
  }
}
const chunk = s => { const o = []; for (let i = 0; i < s.length; i += 1900) o.push(s.slice(i, i + 1900)); return o; };
const rt = s => chunk(s).map(c => ({ type: 'text', text: { content: c } }));
const P = s => ({ paragraph: { rich_text: rt(s) } });
const H3 = s => ({ heading_3: { rich_text: rt(s) } });
const B = s => ({ bulleted_list_item: { rich_text: rt(s) } });
const CALL = (e, s) => ({ callout: { icon: { type: 'emoji', emoji: e }, rich_text: rt(s) } });
const tituloDe = pg => { const t = Object.values(pg.properties).find(p => p.type === 'title'); return (t?.title || []).map(x => x.plain_text).join(''); };

async function todasLinhas(dbId) {
  const out = []; let cursor;
  do {
    const j = await api(`databases/${dbId}/query`, 'POST', { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
    out.push(...(j.results || [])); cursor = j.has_more ? j.next_cursor : null;
  } while (cursor);
  return out;
}

// ————————————————————— 1. ROADMAP: estado real —————————————————————
const ROADMAP_PATCH = {
  'GATE I1: re-auth YouTube no canal do projeto': { Status: 'Entregue', Gate: 'Nenhum', Detalhe: 'RESOLVIDO: verificado 19/08 por API — token aponta pra Charles Spurgeon Treasures (UCXqp7…T6Q)' },
  'GATE P0.4: autorizar run do agendador (1/dia)': { Status: 'Entregue', Gate: 'Nenhum', Detalhe: 'RESOLVIDO: canal publica 1/dia às 12:00 desde 13/08' },
  'I3+I4: limpar estado R2 + religar cron (1 longo/dia)': { Status: 'Entregue', Detalhe: 'Cron religado: 15 vídeos no canal certo, cadência diária confirmada' },
  'GATE: aprovar piloto de 5 shorts': { Status: 'Entregue', Gate: 'Nenhum', Detalhe: 'Piloto aprovado: 1º Short publicado 18/08 ("Drown Your Cares in God")' },
  'F4.5: fila de shorts publicando diário': { Status: 'Em construção', Detalhe: 'Publicação de Short provada (1 no ar); falta a CADÊNCIA diária automática' },
  'GATE: Paddle Website Approval + Asaas docs + CNAME www': { Detalhe: 'CNAME www ✅ (www.mananciall.org responde 200). Asaas ❌ ainda PENDING em bankAccountInfo/documentation/general. Paddle: API responde, aprovação a confirmar no painel' },
  'Rota /go + log de scan (funil dos vídeos)': { Status: 'Pronta', Detalhe: '🔴 VIROU URGENTE: 15 vídeos publicados com QR apontando pra /go, que devolve 404 hoje (verificado 19/08)' },
};

const ROADMAP_NOVAS = [
  ['Organização', 'W0 Ligar', 'Entregue', 'Nenhum', 'Unificação: Teable exportado (119.356 linhas) → R2', 'scripts/migracao/teable_export.mjs · doc 17'],
  ['Organização', 'W0 Ligar', 'Entregue', 'Nenhum', 'Unificação: tabelas vivas migradas pro D1', 'eternall-intel criado + content_index no mananciall-mining'],
  ['Organização', 'W0 Ligar', 'Entregue', 'Nenhum', 'Health check da fábrica construído e verificado', 'scripts/org/health_check.mjs — falta só a URL do webhook'],
  ['Organização', 'W0 Ligar', 'Entregue', 'Nenhum', 'Backup semanal D1 + Notion → R2', 'scripts/backup/backup_semanal.mjs · bucket eternall-archives'],
  ['Organização', 'W0 Ligar', 'Aguardando gate', 'Gabriel', 'GATE: criar webhook do Discord #fabrica', 'Colar a URL no .env como DISCORD_WEBHOOK_FABRICA'],
  ['Organização', 'W1 Consistência', 'Fila', 'Nenhum', 'Congelar containers do Teable na VPS (após 7 dias)', 'docker stop + restart=no, sem apagar volume'],
  ['Inteligência de Mercado', 'W0 Ligar', 'Entregue', 'Nenhum', 'Acervo de intel resgatado pro D1 eternall-intel', '50 canais, 36.739 vídeos, 17 players, 1.421 criativos, 293 páginas'],
  ['Inteligência de Mercado', 'W0 Ligar', 'Pronta', 'Nenhum', 'Reativar a mineração de canais (parada desde abril)', 'YouTube API → channels/channel_videos no D1'],
];

// ————————————————————— 2. TASKS: fechar as resolvidas —————————————————————
const TASKS_FECHAR = {
  'GATE: I1 re-auth YouTube (canal Charles Spurgeon Treasures)': 'Finalizado',
  'GATE: P0.4 autorizar agendador (1/dia)': 'Finalizado',
  'Religar cron I4 + 1 longo/dia (pós I1/P0.4)': 'Finalizado',
  'GATE: aprovar piloto de 5 shorts': 'Finalizado',
  'GATE: apagar CNAME www da Vercel': 'Finalizado',
  'Preparar I3 limpeza do estado R2 (rodar pós-I1)': 'Finalizado',
};
const TASKS_NOVAS = [
  ['GATE: criar webhook Discord #fabrica e colar no .env', 'Organização', ['Monegatto'], 'Variável DISCORD_WEBHOOK_FABRICA; o health check já está pronto e testado'],
  ['GATE: corrigir linha malformada no .env (PADDLE_WEBHOOK_SECRET usa ":" em vez de "=")', 'Organização', ['Monegatto'], 'Nenhum leitor de .env acha a variável hoje'],
  ['GATE: revogar token do Teable e chave factorio_secret ao desligar', 'Organização', ['Monegatto'], 'Estavam em texto plano no STACK.md commitado; histórico do git guarda'],
  ['Congelar containers do Teable na VPS', 'Organização', ['Claude'], 'Depois de 7 dias sem falta: docker stop + restart=no'],
  ['Reativar mineração de canais concorrentes (parada desde abril)', 'Inteligência de Mercado', ['Claude'], 'Atualizar channels/channel_videos no eternall-intel via YouTube API'],
  ['Mover wiki_articles_staging pro mananciall-db (F1 da wiki)', 'Content', ['Claude'], '8 verbetes golden migrados do Teable como staging'],
];

console.log('— 1. Roadmap');
{
  const linhas = await todasLinhas(ids.dbRoadmap);
  const porTitulo = Object.fromEntries(linhas.map(l => [tituloDe(l), l]));
  for (const [titulo, patch] of Object.entries(ROADMAP_PATCH)) {
    const linha = porTitulo[titulo];
    if (!linha) { console.log(`   (não achei: ${titulo})`); continue; }
    const props = {};
    if (patch.Status) props['Status'] = { select: { name: patch.Status } };
    if (patch.Gate) props['Gate'] = { select: { name: patch.Gate } };
    if (patch.Detalhe) props['Detalhe'] = { rich_text: rt(patch.Detalhe) };
    await api(`pages/${linha.id}`, 'PATCH', { properties: props });
    console.log(`   ✓ ${titulo.slice(0, 60)}`);
  }
  for (const [area, onda, status, gate, entrega, detalhe] of ROADMAP_NOVAS) {
    if (porTitulo[entrega]) continue;
    await api('pages', 'POST', {
      parent: { database_id: ids.dbRoadmap },
      properties: {
        'Entrega': { title: rt(entrega) },
        'Área': { relation: [{ id: ids.rows[area] }] },
        'Onda': { select: { name: onda } },
        'Status': { select: { name: status } },
        'Gate': { select: { name: gate } },
        'Detalhe': { rich_text: rt(detalhe) },
      },
    });
    console.log(`   + ${entrega.slice(0, 60)}`);
  }
}

console.log('— 2. Tasks');
{
  const linhas = await todasLinhas(TASKS_DB);
  const porTitulo = Object.fromEntries(linhas.map(l => [tituloDe(l), l]));
  for (const [titulo, status] of Object.entries(TASKS_FECHAR)) {
    const linha = porTitulo[titulo];
    if (!linha) { console.log(`   (não achei: ${titulo.slice(0, 50)})`); continue; }
    await api(`pages/${linha.id}`, 'PATCH', { properties: { 'Status': { select: { name: status } } } });
    console.log(`   ✓ fechada: ${titulo.slice(0, 55)}`);
  }
  for (const [demanda, area, resp, notas] of TASKS_NOVAS) {
    if (porTitulo[demanda]) continue;
    await api('pages', 'POST', {
      parent: { database_id: TASKS_DB },
      properties: {
        'Demanda': { title: rt(demanda) },
        'Status': { select: { name: 'Iniciar' } },
        'Responsável': { multi_select: resp.map(name => ({ name })) },
        'Área': { relation: [{ id: ids.rows[area] }] },
        'Notas': { rich_text: rt(notas) },
      },
    });
    console.log(`   + ${demanda.slice(0, 55)}`);
  }
}

console.log('— 3. Esteiras (estado real + peças novas)');
{
  const linhas = await todasLinhas(ids.dbEsteiras);
  const porTitulo = Object.fromEntries(linhas.map(l => [tituloDe(l), l]));
  const PATCH = {
    'Agendador YouTube': { Status: 'Rodando', Notas: 'Religado: publica 1 vídeo/dia às 12:00 desde 13/08. Guardião de canal ativo' },
    'Publicação YouTube': { Status: 'Rodando', Notas: '15 vídeos no canal certo (verificado por API 19/08)' },
    'Fábrica de shorts': { Status: 'Rodando', Notas: 'Piloto aprovado; 1º Short publicado 18/08. Falta a cadência diária automática' },
  };
  for (const [titulo, patch] of Object.entries(PATCH)) {
    const l = porTitulo[titulo];
    if (!l) continue;
    await api(`pages/${l.id}`, 'PATCH', {
      properties: {
        'Status': { select: { name: patch.Status } },
        'Notas': { rich_text: rt(patch.Notas) },
      },
    });
    console.log(`   ✓ ${titulo}`);
  }
  const NOVAS = [
    ['Health check da fábrica', 'Organização', 'Construída', 'cron VPS', 'scripts/org/health_check.mjs', 'Diária', 'Checa canal (48h + identidade), D1, mineração, loja. Falta a URL do webhook'],
    ['Backup semanal (D1 + Notion)', 'Organização', 'Construída', 'cron VPS', 'scripts/backup/backup_semanal.mjs', 'Semanal', 'Destino: r2://eternall-archives'],
    ['Export/migração do Teable', 'Organização', 'Rodando', 'script manual', 'scripts/migracao/', 'Uma vez', 'Aposentadoria do Teable: 119.356 linhas exportadas'],
  ];
  for (const [nome, area, status, camada, codigo, cadencia, notas] of NOVAS) {
    if (porTitulo[nome]) continue;
    await api('pages', 'POST', {
      parent: { database_id: ids.dbEsteiras },
      properties: {
        'Esteira': { title: rt(nome) },
        'Área': { relation: [{ id: ids.rows[area] }] },
        'Status': { select: { name: status } },
        'Camada': { select: { name: camada } },
        'Código': { rich_text: rt(codigo) },
        'Cadência': { rich_text: rt(cadencia) },
        'Notas': { rich_text: rt(notas) },
      },
    });
    console.log(`   + ${nome}`);
  }
}

console.log('— 4. Indicadores: valores medidos hoje');
{
  const linhas = await todasLinhas(ids.dbIndicadores);
  const porTitulo = Object.fromEntries(linhas.map(l => [tituloDe(l), l]));
  const HOJE = new Date().toISOString().slice(0, 10);
  const VALORES = {
    'Livros live na loja': '28 (D1 produção)',
    'Inscritos do canal': '4',
    'Views/semana': '91 no total do canal',
    'Longos publicados/semana': '7 (1/dia desde 13/08)',
    'Shorts publicados/semana': '1 (piloto; falta cadência)',
    'Obras mineradas (total)': '24',
    'Obras sem URL na fila': '149',
    'Bloqueadas por copyright': '1',
    'Scans do QR (/go)': '0 — rota /go devolve 404',
    'Players EN mapeados': '0 EN · 17 players no total (BR) no eternall-intel',
  };
  for (const [titulo, valor] of Object.entries(VALORES)) {
    const l = porTitulo[titulo];
    if (!l) { console.log(`   (não achei: ${titulo})`); continue; }
    await api(`pages/${l.id}`, 'PATCH', {
      properties: { 'Valor atual': { rich_text: rt(valor) }, 'Atualizado em': { date: { start: HOJE } } },
    });
  }
  console.log('   ✓ valores gravados');
  // indicador novo que a intel ganhou
  if (!porTitulo['Canais concorrentes monitorados']) {
    await api('pages', 'POST', {
      parent: { database_id: ids.dbIndicadores },
      properties: {
        'Indicador': { title: rt('Canais concorrentes monitorados') },
        'Área': { relation: [{ id: ids.rows['Inteligência de Mercado'] }] },
        'Fonte': { select: { name: 'YouTube API' } },
        'Cadência': { select: { name: 'Semanal' } },
        'Meta': { rich_text: rt('50+ atualizados no mês') },
        'Valor atual': { rich_text: rt('50 canais / 36.739 vídeos no D1 (última coleta: abril/2026)') },
        'Atualizado em': { date: { start: HOJE } },
        'Como ler': { rich_text: rt('Raio-X do que performa no nicho: tabela channel_videos do eternall-intel') },
      },
    });
    console.log('   + Canais concorrentes monitorados');
  }
}

// ————————————————————— 5. METAS CANDIDATAS nas páginas das áreas —————————————————————
const METAS = {
  'Organização': ['★ Nada roda sem alarme: 100% das esteiras em produção com health check avisando em menos de 24h', 'Fábrica auto-orientável: frente nova se orienta sozinha em menos de 5 min, zero pergunta repetida', 'Aprendizado vira arquivo: 3 skills promovidas a 🟢 até dezembro'],
  'Inteligência de Mercado': ['★ Mercado EN mapeado: 3 segmentos (livraria, app, canal) com players fichados e síntese escrita até fim de setembro', 'Rotina que muda decisão: intel semanal 4+ semanas seguidas e ao menos 1 decisão/mês citando intel', '10 gaps de concorrente identificados (obra cara/física/inexistente que a gente publica barato)'],
  'Inteligência do Negócio': ['★ Fim do escuro: snapshot semanal com 100% das métricas núcleo coletadas', 'BI no ar: mananciall-bi com abas Canais/Loja/Acervo/Esteiras e rebuild noturno', 'Números que avisam: 5 alarmes ligados no #fabrica'],
  'Mineração': ['★ Ponte viva: Notion → fila → minerado → produção rodando ponta a ponta, 30 obras promovidas até outubro', 'Fila resolvida: 149 sem-URL zerados (resolvidos ou classificados como sem fonte DP)', 'Proveniência 100%: toda obra com snapshot cru no R2 e verificação de DP registrada'],
  'Content': ['★ Cadência sagrada: 30 dias corridos de 1 longo/dia + 1 short/dia sem furo', 'Segundo canal no ar: canal Bíblia publicando (F1 completo) até novembro', 'Wiki de estreia: cluster Oração público puxando orgânico'],
  'Productz': ['Loja completa: checkout live nas 2 moedas + 1ª venda orgânica real', '★ Catálogo 50: 50+ obras publicadas com capa v1 e edição aprovada até dezembro', 'Produto diário: /today como porta de entrada (SEO + destino dos canais) com captura de lead'],
  'i18n': ['★ Esteira provada: tradução EN→PT com portão de qualidade validada num piloto vendável', 'PT que vende: 10 livros PT vendáveis até dezembro (hoje 2)', 'Voz decidida: locutor PT contratado (F2.4) + 1 piloto de audiolivro/canal PT'],
};

console.log('— 5. Metas candidatas nas páginas das áreas');
if (!ids.metasCandidatas) ids.metasCandidatas = {};
for (const [area, metas] of Object.entries(METAS)) {
  if (ids.metasCandidatas[area] || !ids.rows[area]) continue;
  await api(`blocks/${ids.rows[area]}/children`, 'PATCH', {
    children: [
      H3('🎯 Metas de 90 dias (candidatas)'),
      CALL('👉', 'Escolha UMA como principal (ou reescreva). A marcada com ★ é a minha recomendação. Depois de escolhida, ela vira o Norte 90 dias da área.'),
      ...metas.map(B),
    ],
  });
  ids.metasCandidatas[area] = true;
  fs.writeFileSync(path.join(HERE, 'notion-fabrica-ids.json'), JSON.stringify(ids, null, 2));
  console.log(`   + ${area}`);
}

// ————————————————————— 6. Nota de estado no hub —————————————————————
if (!ids.notaEstado) {
  await api(`blocks/${ids.hubPage}/children`, 'PATCH', {
    children: [
      { divider: {} },
      H3('📌 Estado real medido em 19/08/2026 (noite)'),
      CALL('✅', 'O canal ESTÁ publicando: 15 vídeos no Charles Spurgeon Treasures (o certo), 1/dia às 12:00 desde 13/08, e o 1º Short saiu em 18/08. Os gates I1, P0.4, I4 e o piloto de shorts estavam resolvidos e o roadmap escrito em 11/08 é que estava velho.'),
      CALL('🔴', 'Urgência descoberta: os 15 vídeos no ar carregam QR pra mananciall.org/go, que devolve 404 hoje. Cada vídeo publicado sem essa rota é tráfego jogado fora. É a entrega nº 1 da frente Productz.'),
      CALL('🗄️', 'Unificação de dados feita: Teable exportado inteiro (119.356 linhas → r2://eternall-archives) e as tabelas vivas migradas pro D1. Nasceu o banco eternall-intel com o ouro abandonado desde abril: 50 canais, 36.739 vídeos, 17 players, 1.421 criativos e 293 páginas de concorrente. trigger.dev saiu da stack: nada em produção usava.'),
      P('Ainda pendente do lado do Gabriel: webhook do Discord (#fabrica), documentos do Asaas, confirmação do Website Approval no Paddle, voz PT (F2.4), golden set da wiki e apps TikTok/Meta.'),
    ],
  });
  ids.notaEstado = true;
  fs.writeFileSync(path.join(HERE, 'notion-fabrica-ids.json'), JSON.stringify(ids, null, 2));
  console.log('— 6. Nota de estado no hub ✓');
}

console.log('\n✅ Notion atualizado com o estado real.');
