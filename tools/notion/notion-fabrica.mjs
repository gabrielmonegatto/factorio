#!/usr/bin/env node
// Builder da página 🏭 Fábrica no Business System (19/08/2026).
// Fonte do desenho: _factorio/docs/16_BLUEPRINT_AREAS.md. Rodar de novo é seguro:
// tudo que já foi criado fica registrado em notion-fabrica-ids.json e é pulado.
//
// O que monta:
//  1. Upgrade in place do db "Mananciall Roadmap" do Gabriel -> db "Áreas" (nada apagado)
//  2. Página-hub "🏭 Fábrica" sob Business System (residência de dados, ordem, gates)
//  3. Bancos novos Roadmap / Esteiras / Indicadores (relation Área, semeados)
//  4. Relation "Área" no banco Tasks existente + tasks da 1ª onda (incl. GATEs do Gabriel)
//  5. Blueprint completo + prompt de abertura na página de cada área

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const IDS_FILE = path.join(HERE, 'notion-fabrica-ids.json');
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const BS_PAGE = '33d6bf27-9f65-4043-8a5d-c53fe0b241a3';       // página Business System
const AREAS_DB = '3c1f06f1-0ce3-8076-908b-fbcb7b67294c';      // ex "Mananciall Roadmap" (do Gabriel)
const TASKS_DB = '3a7f06f1-0ce3-81cd-8696-cc002c44f430';      // banco Tasks existente
const UNIDADES_DB = '3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f';   // banco Unidades
const BIBLIOTECA_DB = '3bef06f1-0ce3-81d0-8ce6-daa092972b00';
const REFERENCIAS_DB = '3c0f06f1-0ce3-813b-94a4-c436be12ede0';
const DB_ICON = { type: 'external', external: { url: 'https://www.notion.so/icons/database_green.svg' } };

const ids = fs.existsSync(IDS_FILE) ? JSON.parse(fs.readFileSync(IDS_FILE, 'utf8')) : {};
const save = () => fs.writeFileSync(IDS_FILE, JSON.stringify(ids, null, 2));

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(p, method = 'GET', body) {
  for (let tent = 1; ; tent++) {
    await sleep(320);
    try {
      const res = await fetch(`https://api.notion.com/v1/${p}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const j = await res.json();
      if (j.object === 'error' && j.code === 'rate_limited') { await sleep(2500); continue; }
      return j;
    } catch (e) {
      if (tent >= 4) throw e;
      await sleep(tent * 3000);
    }
  }
}
const die = (j, ctx) => { if (j?.object === 'error') { console.error(`ERRO em ${ctx}: ${j.code} ${j.message}`); process.exit(1); } return j; };

// helpers de conteúdo
const chunk = s => { const out = []; for (let i = 0; i < s.length; i += 1900) out.push(s.slice(i, i + 1900)); return out; };
const rt = s => chunk(s).map(c => ({ type: 'text', text: { content: c } }));
const H2 = s => ({ heading_2: { rich_text: rt(s) } });
const H3 = s => ({ heading_3: { rich_text: rt(s) } });
const P = s => ({ paragraph: { rich_text: rt(s) } });
const B = s => ({ bulleted_list_item: { rich_text: rt(s) } });
const N = s => ({ numbered_list_item: { rich_text: rt(s) } });
const CALL = (emoji, s) => ({ callout: { icon: { type: 'emoji', emoji }, rich_text: rt(s) } });
const CODE = s => ({ code: { language: 'plain text', rich_text: rt(s) } });
const LINKDB = id => ({ link_to_page: { type: 'database_id', database_id: id } });
const DIV = () => ({ divider: {} });
const sel = name => ({ select: { name } });
const num = n => ({ number: n });
const rich = s => ({ rich_text: rt(s) });
const relOne = id => ({ relation: [{ id }] });
const titleOf = page => { const t = Object.values(page.properties).find(p => p.type === 'title'); return (t?.title || []).map(x => x.plain_text).join(''); };

// ————————————————————————————————————————————————————————————————
// DADOS DAS ÁREAS (espelho do doc 16 §6)
// ————————————————————————————————————————————————————————————————
const PROMPTS = {
  'Organização': `Você é a frente ORGANIZAÇÃO da fábrica Eternall (piloto Mananciall).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.1 e §7) e docs/04_ROADMAP.md (itens 1.3 e 1.6).
Missão W0, nesta ordem:
1. Webhook Discord #fabrica + health check das esteiras (erro OU 48h sem vídeo novo
   agendado → aviso). Item P0.5 do docs/11_ROADMAP_ATIVO.md.
2. Skill /frente: abre sessão de qualquer área carregando doc 16 + tasks do Notion.
3. Preparar /diretor-diario (skill draft; primeira execução manual é W1).
Tarefas: Notion, banco Tasks, filtro Área=Organização (kit tools/notion, NOTION_TOKEN no .env).
Território: docs/, .claude/skills/, tools/notion/, scripts/org/. Fora disso: /handoff-frente.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,

  'Inteligência de Mercado': `Você é a frente INTELIGÊNCIA DE MERCADO da fábrica Eternall (piloto Mananciall).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.2 e §7), docs/13_CATALOGO_ESTRATEGICO_MANANCIALL.md
e, no repo do site (só leitura), docs/DOSSIE-FRONTEND-2026.md e docs/capas/HANDOFF-CAPAS.md.
Missão W0: mapear o mercado EN no banco "Referências de Editoras" do Notion (campo
Mercado=EN): Standard Ebooks, Monergism, Banner of Truth, Crossway, Ligonier,
YouVersion/Logos/Olive Tree (apps) e 10+ canais YouTube de sermão/audiobook EN.
Por player: catálogo, preço, formato, modelo (free/pago/assinatura), capa, o que copiar.
Entrega: síntese "Mapa do Mercado EN" na página da área Inteligência de Mercado no Notion.
Tarefas: banco Tasks, filtro Área=Inteligência de Mercado.
Território: _factorio/scripts/intel/ (criar) + Notion. Não edita repo de app.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,

  'Inteligência do Negócio': `Você é a frente INTELIGÊNCIA DO NEGÓCIO (BI) da fábrica Eternall (piloto Mananciall).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.3 e §7). Padrão a seguir: memória br4nds-bi
(bi.br4nds.com.br) e o banco "📏 Catálogo de Métricas — BI" no Notion.
Missão W0:
1. Revisar o banco Indicadores no Notion (semeado 19/08) e propor ajustes ao Gabriel.
2. Construir _factorio/scripts/bi/snapshot.mjs: YouTube API + D1 mananciall-db +
   D1 mananciall-mining + Paddle/Asaas → tabela bi_snapshots (D1) → espelhar "Valor
   atual"/"Atualizado em" no banco Indicadores. Rodar e conferir números à mão.
3. Documentar a rodada semanal (por ora manual) na página da área.
W1 (não começar sem W0 verificado): repo apps/eternall/mananciall-bi no padrão Br4nds.
Tarefas: banco Tasks, filtro Área=Inteligência do Negócio.
Território: _factorio/scripts/bi/. Credenciais no .env (CRLF: tr -d '\\r').
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,

  'Mineração': `Você é a frente MINERAÇÃO da fábrica Eternall (piloto Mananciall).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.4 e §7) e docs/15_ESTEIRA_DE_MINERACAO.md inteiro.
Estado: 24 obras mineradas; gargalo é resolver (149 sem URL); ponte pra produção não existe.
Missão W0, nesta ordem:
1. PONTE minerado→produção: promover obra mined do D1 mananciall-mining pra books +
   chapters.source_md do D1 mananciall-db (formato: conferir com a frente Productz via
   handoff; a esteira de edição de lá assume depois). Piloto com 1 obra, conferida.
2. Adapter Archive.org (21 obras esperam) + ampliar content_index até zerar os 149.
3. Snapshot cru no R2 (raw_key): prova de proveniência, evita re-raspar.
Respeite as 3 travas do doc 15 (similaridade, autor, copyright). Fontes com fetch educado.
Tarefas: banco Tasks, filtro Área=Mineração. O painel humano é a Biblioteca Mananciall.
Território: _factorio/scripts/mining/ + docs/15. Escrita no D1 de produção SÓ pela ponte.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,

  'Content': `Você é a frente CONTENT da fábrica Eternall (sub-frentes longz e shortz).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.5 e §7), docs/11_ROADMAP_ATIVO.md (incidente I1 +
P0), docs/12_FABRICA_SHORTS.md e docs/10_CHECKLIST_CANAL_BIBLIA.md.
Estado: 113 longos renderizados e 112 narrados; publicação parada nos gates I1/P0.4;
piloto de 5 shorts no R2 aguardando aprovação.
Missão W0 (é destravar, não construir):
1. Preparar tudo que NÃO depende de gate: F4.5 (fila de publicação de shorts), I3
   (limpeza do estado do R2 dos 18 vídeos do canal errado) pronto pra rodar pós-I1.
2. Assim que o Gabriel fizer I1/P0.4/aprovar shorts: executar I3, reativar cron (I4),
   ligar fila de shorts. Meta: 1 longo/dia + shorts diários no automático.
3. Com publicação girando: iniciar W1 = canal Bíblia (F1.4 a F1.7 do doc 10; OAuth novo
   JÁ com app em produção, lição do I1: token tem que provar IDENTIDADE de canal).
Gates seus (cobrar no report, nunca contornar): I1, I2, P0.4, piloto shorts, F4.2, F4.3.
Tarefas: banco Tasks, filtro Área=Content.
Território: remotion/, trigger/, scripts/ (canais), docs 06/07/10/11/12.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,

  'Productz': `Você é a frente PRODUCTZ da fábrica Eternall (Mananciall).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\apps\\eternall\\mananciall-site (repo próprio;
git pull antes: a frente i18n divide este repo).
Leia: CLAUDE.md do repo, docs/ACERVO.md, docs/capas/HANDOFF-CAPAS.md e, na fábrica (só
leitura), _factorio/docs/16_BLUEPRINT_AREAS.md (§6.6 e §7).
Estado: site EN+PT no ar em mananciall.org; Paddle e Asaas integrados mas travados em
aprovação de conta (gates do Gabriel); 27 livros live; 9 audiolivros; QR dos vídeos
aponta pra /go que hoje é 404.
Missão W0, nesta ordem:
1. Rota /go (s=yt&v=NNNN): loga scan em D1 + redireciona com UTMs pro destino
   (/en/treasures-spurgeon quando existir; por ora home EN com UTM). Desbloqueia o funil
   dos vídeos JÁ publicados.
2. Página /today: leitura diária do Morning and Evening (731 prontas no banco),
   indexável, CTA pro livro. Destino diário dos canais + SEO.
3. Capas v1: renderer programático por coleção (retrato duotone + 1 cor por coleção,
   caminho barato do HANDOFF-CAPAS) aplicado aos 27 live.
4. Quando os gates Paddle/Asaas/www saírem: 1 venda de teste ponta a ponta por moeda.
Gates seus: Paddle Website Approval, Asaas docs, CNAME www, decisão Jornada mensal.
Tarefas: banco Tasks, filtro Área=Productz. Preço/lançamento: Gabriel manda na
Biblioteca Mananciall.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,

  'i18n': `Você é a frente I18N da fábrica Eternall (Mananciall).
Abra em C:\\Users\\Monegatto\\Desktop\\EternalL\\apps\\eternall\\mananciall-site (repo
compartilhado com a frente Productz: git pull antes, commits pequenos, seu território é
scripts/i18n/ + conteúdo PT).
Leia: CLAUDE.md do repo, src/lib/i18n.ts, a esteira de edição (scripts/editoria/) e, na
fábrica (só leitura), _factorio/docs/16_BLUEPRINT_AREAS.md (§6.7 e §7).
Missão W0: esteira de tradução de livro EN→PT como LLM-função com portão de qualidade
no molde da edição: não muda sentido (amostragem com juiz), glossário teológico
consistente (criar docs/GLOSSARIO-PT.md no repo), grafia de época opt-in por livro.
Piloto: All of Grace (curto, Spurgeon, já tem áudio EN) publicado vendável em /pt,
revisão por amostragem antes de ir live.
Depois do piloto aprovado: fila = próximos 5 livros curtos do catálogo.
Gate seu: voz PT (F2.4) é decisão do Gabriel; não iniciar audiolivro PT antes.
Tarefas: banco Tasks, filtro Área=i18n.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.`,
};

const AREAS = [
  {
    nome: 'Organização', ordem: 1, nivel: 'Área', status: 'Ligando', frente: '_factorio/',
    missao: 'Toda sessão se orienta sozinha em minutos; aprendizado vira arquivo na hora; alarme cobre o que roda sozinho.',
    norte: '7 frentes rodando sem colisão, docs confiáveis, esteiras com health check.',
    existe: ['Docs 00 a 16 + constituição (_factorio/CLAUDE.md)', 'Skills /fabrica, /nova-skill, /handoff-frente', 'Kit Notion (tools/notion, 30 scripts)', 'backlog_skills_seed.md (catálogo futuro)'],
    w0: ['Blueprint no git + Notion montado (feito 19/08)', 'Webhook Discord #fabrica + health check: erro OU 48h sem vídeo agendado → aviso (P0.5)', 'Skill /frente (abre sessão de área com doc 16 + tasks)', 'Índice e Operating Model atualizados (feito 19/08)'],
    w1: ['/diretor-diario manual 3x (briefing de 10 linhas)', 'Conserto da tabela tasks do Teable (item 1.6)', 'Backup git: push remoto dos repos sem remote'],
    w2: ['Cadências agendadas (diretor diário, revisão semanal de esteiras)', 'Promoção de skills 🟡→🟠→🟢'],
    dados: 'Docs/skills em git; tasks humanas no Notion; estado de esteira em Teable/D1.',
    indicadores: ['Skills por nível de confiança', 'Colisões de frente no mês (meta 0)'],
    gates: [],
    territorio: '_factorio: docs/, .claude/skills/, tools/notion/, scripts/org/',
  },
  {
    nome: 'Inteligência de Mercado', ordem: 6, nivel: 'Área', status: 'Desenhada', frente: '_factorio/',
    missao: 'Mapa vivo de quem vende o quê no nosso espaço (livraria digital, app de Bíblia, canais dark), com síntese que muda decisão de catálogo, preço, capa e copy.',
    norte: 'Mercado EN mapeado no nível do BR + rotina semanal de intel.',
    existe: ['Banco Referências de Editoras (609 produtos BR: Heziom + Biblioteca Católica)', 'Dossiês de conversão no repo do site (Stripe Press etc)', 'Docs 13/14 (catálogo estratégico)', 'Benchmark GotQuestions (wiki)'],
    w0: ['Mapear mercado EN: Standard Ebooks, Monergism, Banner of Truth, Crossway, Ligonier, apps (YouVersion/Logos/Olive Tree), 10+ canais YouTube EN', 'Campo Mercado (BR/EN) no banco Referências', 'Síntese "Mapa do Mercado EN" na página da área'],
    w1: ['/intel-semanal: 3 edições úteis seguidas', 'Monitor de canais concorrentes via YouTube API (números no Teable)'],
    w2: ['Data lake no Teable (estruturado→Teable, síntese→Notion)', 'Alertas de movimento (player novo, preço mudou)'],
    dados: 'Curadoria no Notion; scrape/volume no Teable; binários no R2.',
    indicadores: ['Players EN mapeados', 'Relatórios de intel entregues'],
    gates: [],
    territorio: '_factorio/scripts/intel/ (criar) + Notion',
  },
  {
    nome: 'Inteligência do Negócio', ordem: 5, nivel: 'Área', status: 'Desenhada', frente: '_factorio/ → repo mananciall-bi (W1)',
    missao: 'Todos os números relevantes (canais, loja, esteiras, custos) num painel diário confiável; nenhuma decisão no escuro.',
    norte: 'BI Mananciall no ar no padrão bi.br4nds.com.br, com alarmes no #fabrica.',
    existe: ['Padrão pronto do Br4nds (repo + rebuild noturno + Catálogo de Métricas + vigia)', 'Dados espalhados: YouTube Studio, D1 produção, Paddle, Asaas, D1 mineração, R2'],
    w0: ['Catálogo de indicadores no banco Indicadores (semeado 19/08: validar com o Gabriel)', 'scripts/bi/snapshot.mjs: YouTube API + D1 + gateways → bi_snapshots (D1) → espelho no Notion', 'Rodada semanal manual documentada'],
    w1: ['Repo apps/eternall/mananciall-bi (padrão Br4nds; abas Canais/Loja/Acervo/Esteiras)', 'Rebuild noturno na VPS'],
    w2: ['Alarmes de negócio no #fabrica (venda zerada, publicação parada, esteira morta)', 'Atribuição do funil /go (scan → visita → venda)'],
    dados: 'Fatos em D1 (bi_snapshots); Notion Indicadores é vitrine; app BI lê do D1, nunca do Notion.',
    indicadores: ['Freshness do snapshot (dias)', '% métricas com coleta automática'],
    gates: [],
    territorio: '_factorio/scripts/bi/ (criar); W1: repo apps/eternall/mananciall-bi (git init)',
  },
  {
    nome: 'Mineração', ordem: 3, nivel: 'Área', status: 'Ligando', frente: '_factorio/scripts/mining/',
    missao: 'Matéria-prima (texto DP, dados, referências) entrando no banco em volume, com proveniência e domínio público provados.',
    norte: 'Fila nunca vazia, 149 sem-URL zerados, ponte pra produção rodando.',
    existe: ['Esteira completa (queue/resolve/mine/status, doc 15)', '24 obras / 231 caps / 14M chars minerados', '3 travas (similaridade, autor, copyright: pegou a Outler 1955)', 'content_index com 545 obras'],
    w0: ['PONTE minerado→produção (mined → books + chapters.source_md), piloto 1 obra conferida', 'Adapter Archive.org (21 obras esperam) + ampliar content_index (zerar 149 sem URL)', 'Snapshot cru no R2 (raw_key): proveniência + evita re-raspar'],
    w1: ['Corte de capítulo do New Advent', 'Obras compostas (volumes editoriais montados peça a peça)', 'Cron de mineração (fila anda sozinha)'],
    w2: ['Minerar além de livro: sermões avulsos (51 volumes Spurgeon), comentários bíblicos pro app, FAQ, gravuras DP pra capas'],
    dados: 'Fila/estado/texto em D1 mananciall-mining; plano na Biblioteca (Notion); cru no R2.',
    indicadores: ['Obras mineradas/semana', '% da fila sem URL', 'Bloqueadas por copyright', 'Capítulos promovidos pra produção'],
    gates: [],
    territorio: '_factorio/scripts/mining/ + docs/15. D1 de produção SÓ pela ponte (handoff com Productz)',
  },
  {
    nome: 'Content', ordem: 2, nivel: 'Área', status: 'Ligando', frente: '_factorio/ (remotion, trigger)',
    missao: 'Publicar todo dia, em todos os formatos, com qualidade estável e custo marginal ~zero. Sub-frentes: longz e shortz.',
    norte: '1 longo/dia + shorts diários sem furo, canal Bíblia no ar, wiki com cluster Oração público.',
    existe: ['113 longos renderizados (só 6 no canal certo: resto travado em gate)', 'Pipeline híbrido validado (~$0,10/vídeo) + guardião de canal', 'Shorts F4.4: piloto de 5 no R2', 'Canal Bíblia desenhado (doc 10)', 'Wiki F0 (manual + 5 verbetes golden)', '731 leituras diárias prontas no banco'],
    w0: ['Preparar F4.5 (fila de shorts) e I3 (limpeza R2) pra rodar pós-gates', 'Pós I1/P0.4/aprovação: I3 + religar cron (I4) + fila de shorts = publicação diária no automático'],
    w1: ['Canal Bíblia no ar (F1.4 a F1.7; OAuth novo já em produção, token prova IDENTIDADE)', 'Wiki F1/F2: schema D1 + rotas reais + cluster Oração público'],
    w2: ['Cortes TikTok/Meta (gate F4.3)', 'Blog SEO por clusters', 'Carrossel/imagem (esteira nova)', 'Canais PT/ES (depende voz i18n)', '2º canal dark pelo template'],
    dados: 'Assets/renders no R2; estado do agendador em JSON no R2 (migrar pra Teable na W1); wiki editorial no Teable; métricas → BI.',
    indicadores: ['Longos publicados/semana (meta 7)', 'Shorts/semana', 'Dias sem furo', 'Inscritos e views', 'Scans do QR /go'],
    gates: ['I1 re-auth YouTube', 'I2 destino dos 5 vídeos', 'P0.4 autorizar agendador', 'Aprovar piloto de 5 shorts', 'F4.2 gates do canal de shorts', 'F4.3 credenciais TikTok/Meta', 'Golden set da wiki', 'F3.1 billing Lightning'],
    territorio: '_factorio: remotion/, trigger/, scripts/ (canais), docs 06/07/10/11/12',
  },
  {
    nome: 'Productz', ordem: 4, nivel: 'Área', status: 'Ligando', frente: 'apps/eternall/mananciall-site',
    missao: 'Catálogo digno de assinatura: loja + leitor + audiolivro + app de estudo; do "Texto pronto" ao vendável sem fricção.',
    norte: 'Checkout live nas 2 moedas, 50+ obras publicadas com capa v1, /today no ar, membros v1.',
    existe: ['mananciall.org no ar (EN + PT completos, 27 livros, leitor com amostra pública)', 'Paddle (26 produtos) e Asaas (Pix) integrados, travados em aprovação de conta', '9 audiolivros completos (1.214 faixas)', 'Esteira de edição (portão letra a letra, 3.326 caps)', 'Frente de capas aberta (spec v0.2 + 609 referências)', 'App Bíblia fases 0/1 no ar', 'Bíblia Jornada legada (10 assinantes Stripe)'],
    w0: ['Rota /go + log de scan em D1 (QR dos vídeos hoje cai em 404!)', '/today no ar (731 leituras Morning and Evening)', 'Capas v1: renderer por coleção (duotone barato) nos 27', 'Pós-gates: 1 venda de teste ponta a ponta por moeda'],
    w1: ['Lote de publicação: mineração → edição → live (+20 obras)', 'Audiolivros novos (esteira TTS com voz EN)', 'Membros v1 (Clerk) + migração Bíblia Jornada (vitalício)'],
    w2: ['App Bíblia fases 2 a 4 (Strong\'s, referências, comentários)', 'Coleções/bundles + assinatura estilo clube (modelo Biblioteca Católica)'],
    dados: 'Produto no D1 mananciall-db; plano na Biblioteca (Notion); capas/áudio no R2; vendas espelhadas em orders.',
    indicadores: ['Livros live', 'Vendas e receita/semana', 'Leads', '% catálogo com capa v1', 'Conversão PDP (quando BI medir)'],
    gates: ['Paddle Website Approval', 'Asaas conta bancária + docs', 'Apagar CNAME www da Vercel', 'Decisão assinatura mensal Jornada', 'Preços (campo do Gabriel na Biblioteca)'],
    territorio: 'repo apps/eternall/mananciall-site (+ mananciallbible quando reabrir). _factorio só leitura',
  },
  {
    nome: 'i18n', ordem: 7, nivel: 'Área', status: 'Desenhada', frente: 'apps/eternall/mananciall-site',
    missao: 'Cada ativo (livro, página, verbete, vídeo) existe em EN e PT (ES na fila) sem retrabalho manual.',
    norte: 'Esteira de tradução EN→PT validada em livros vendáveis + decisão de voz PT tomada.',
    existe: ['Site bilíngue com hreflang e rotas PT', '2 livros PT vendáveis + 26 "em breve"', '4 Bíblias PT em JSON', 'Pesquisa de voz PT/ES (F2: recomendação = locutor contratado)', 'Wiki desenhada PT mestre → EN gêmeo'],
    w0: ['Esteira de tradução EN→PT: LLM-função + portão de qualidade (não muda sentido, glossário teológico, grafia de época opt-in)', 'Piloto: All of Grace publicado vendável em /pt'],
    w1: ['Todo livro novo EN entra na fila PT', 'Verbetes wiki PT→EN', 'Voz PT (gate F2.4) → piloto audiolivro/canal PT'],
    w2: ['ES (site + livros)', 'Canais PT/ES com a voz definida', 'Metadados/legendas em lote'],
    dados: 'Tradução vira chapters PT no D1 produção; glossário em git; fila em D1.',
    indicadores: ['Livros PT vendáveis', 'Verbetes EN', '% catálogo bilíngue'],
    gates: ['F2.4 voz PT/ES (locutor)', 'Preço BRL'],
    territorio: 'repo do site: scripts/i18n/ + conteúdo PT (repo dividido com Productz: pull antes, commits pequenos)',
  },
  {
    nome: 'Growth', ordem: 8, nivel: 'Área', status: 'Futura', frente: '(não abre chat ainda)',
    missao: 'Tráfego pago, CRO, SEO técnico, parcerias, e-mail (precedentes: Experimentos/ICE e The Machine da Bluue).',
    norte: 'Ativa quando: checkout live + BI medindo + 30 dias de publicação consistente.',
    existe: ['Banco Experimentos (ICE) no Notion', 'The Machine (e-mails) como precedente Bluue', 'Playbook CRO da holding (linha de montagem)'],
    w0: ['(definir na ativação)'], w1: [], w2: [],
    dados: 'A definir na ativação (seguirá o padrão: fatos na máquina, Notion vitrine).',
    indicadores: [], gates: [],
    territorio: '(a definir)',
  },
];

const SUBFRENTES = [
  { nome: 'longz', pertenceA: 'Content', desc: 'Sub-frente de Content: vídeos longos do YouTube (Spurgeon hoje; Bíblia na W1). Roadmap e tasks ficam na área Content.' },
  { nome: 'shortz', pertenceA: 'Content', desc: 'Sub-frente de Content: Shorts/TikTok/Reels (fábrica F4). Roadmap e tasks ficam na área Content.' },
];

// mapeamento das linhas que o Gabriel criou no esboço → nome oficial
const RENAME = {
  'inteligência': 'Inteligência de Mercado',
  'mineração': 'Mineração',
  'contentz': 'Content',
  'growth': 'Growth',
  'productz': 'Productz',
  'i18n': 'i18n',
  'longz': 'longz',
  'shortz': 'shortz',
};

// ————————————————————————————————————————————————————————————————
// SEEDS: Roadmap, Esteiras, Indicadores, Tasks
// ————————————————————————————————————————————————————————————————
const ROADMAP = [
  ['Organização', 'W0 Ligar', 'Entregue', 'Nenhum', 'Blueprint das 7 áreas no git + Notion', 'Doc 16 + página Fábrica (19/08)'],
  ['Organização', 'W0 Ligar', 'Pronta', 'Nenhum', 'Webhook #fabrica + health check 48h das esteiras', 'P0.5: erro OU 48h sem vídeo agendado → aviso'],
  ['Organização', 'W0 Ligar', 'Pronta', 'Nenhum', 'Skill /frente (abre sessão de área)', ''],
  ['Organização', 'W1 Consistência', 'Fila', 'Nenhum', '/diretor-diario rodado 3x manual', ''],
  ['Organização', 'W1 Consistência', 'Fila', 'Nenhum', 'Conserto da tabela tasks do Teable (F1.6)', 'UI/API quebradas; esteira fala psycopg2'],
  ['Organização', 'W2 Escala', 'Fila', 'Nenhum', 'Cadências agendadas (diretor, revisão de esteiras)', ''],
  ['Inteligência de Mercado', 'W0 Ligar', 'Pronta', 'Nenhum', 'Mapa do Mercado EN (players + síntese)', 'Standard Ebooks, Monergism, Crossway, apps, canais YT'],
  ['Inteligência de Mercado', 'W1 Consistência', 'Fila', 'Nenhum', '/intel-semanal: 3 edições úteis seguidas', ''],
  ['Inteligência de Mercado', 'W2 Escala', 'Fila', 'Nenhum', 'Data lake de concorrentes no Teable + alertas', ''],
  ['Inteligência do Negócio', 'W0 Ligar', 'Pronta', 'Nenhum', 'Catálogo de indicadores validado', 'Semeado 19/08; Gabriel revisa'],
  ['Inteligência do Negócio', 'W0 Ligar', 'Pronta', 'Nenhum', 'snapshot.mjs semanal → bi_snapshots (D1) + espelho no Notion', ''],
  ['Inteligência do Negócio', 'W1 Consistência', 'Fila', 'Nenhum', 'Repo mananciall-bi no ar (padrão Br4nds)', ''],
  ['Inteligência do Negócio', 'W2 Escala', 'Fila', 'Nenhum', 'Alarmes de negócio no #fabrica', ''],
  ['Mineração', 'W0 Ligar', 'Pronta', 'Nenhum', 'Ponte minerado→produção (piloto 1 obra)', 'mined → books + chapters.source_md'],
  ['Mineração', 'W0 Ligar', 'Pronta', 'Nenhum', 'Adapter Archive.org + content_index ampliado', 'Zerar os 149 sem URL'],
  ['Mineração', 'W0 Ligar', 'Pronta', 'Nenhum', 'Snapshot cru no R2 (raw_key)', ''],
  ['Mineração', 'W1 Consistência', 'Fila', 'Nenhum', 'Corte de capítulo New Advent + obras compostas', ''],
  ['Mineração', 'W1 Consistência', 'Fila', 'Nenhum', 'Cron de mineração (fila anda sozinha)', ''],
  ['Mineração', 'W2 Escala', 'Fila', 'Nenhum', 'Minerar além de livro (sermões, comentários, FAQ, gravuras)', ''],
  ['Content', 'W0 Ligar', 'Aguardando gate', 'Gabriel', 'GATE I1: re-auth YouTube no canal do projeto', 'auth_youtube.py escolhendo Charles Spurgeon Treasures'],
  ['Content', 'W0 Ligar', 'Aguardando gate', 'Gabriel', 'GATE: aprovar piloto de 5 shorts', 'R2 renders/spurgeon_shorts/'],
  ['Content', 'W0 Ligar', 'Aguardando gate', 'Gabriel', 'GATE P0.4: autorizar run do agendador (1/dia)', ''],
  ['Content', 'W0 Ligar', 'Fila', 'Nenhum', 'I3+I4: limpar estado R2 + religar cron (1 longo/dia)', 'Depois do I1'],
  ['Content', 'W0 Ligar', 'Fila', 'Nenhum', 'F4.5: fila de shorts publicando diário', 'Depois de I1 + aprovação do piloto'],
  ['Content', 'W1 Consistência', 'Fila', 'Nenhum', 'Canal Bíblia no ar (F1.4 a F1.7)', 'A/B Kokoro vs Chirp; OAuth já em produção'],
  ['Content', 'W1 Consistência', 'Aguardando gate', 'Gabriel', 'Wiki: cluster Oração público (F1+F2)', 'Aguarda golden set aprovado'],
  ['Content', 'W2 Escala', 'Aguardando gate', 'Gabriel', 'GATE F4.3: credenciais TikTok + Meta', 'Disparar cedo: review demora semanas'],
  ['Content', 'W2 Escala', 'Fila', 'Nenhum', 'Cortes TikTok/Reels + blog SEO + carrossel', ''],
  ['Productz', 'W0 Ligar', 'Aguardando gate', 'Gabriel', 'GATE: Paddle Website Approval + Asaas docs + CNAME www', ''],
  ['Productz', 'W0 Ligar', 'Pronta', 'Nenhum', 'Rota /go + log de scan (funil dos vídeos)', 'QR dos vídeos publicados hoje cai em 404'],
  ['Productz', 'W0 Ligar', 'Pronta', 'Nenhum', '/today no ar (731 leituras prontas)', ''],
  ['Productz', 'W0 Ligar', 'Pronta', 'Nenhum', 'Capas v1 nos 27 livros (renderer por coleção)', 'Caminho duotone barato do HANDOFF-CAPAS'],
  ['Productz', 'W0 Ligar', 'Fila', 'Nenhum', '1 venda de teste ponta a ponta (USD cupom + Pix R$1)', 'Depois dos gates'],
  ['Productz', 'W1 Consistência', 'Fila', 'Nenhum', '+20 obras publicadas (ponte → edição → loja)', ''],
  ['Productz', 'W1 Consistência', 'Fila', 'Nenhum', 'Membros v1 (Clerk) + migração Bíblia Jornada', ''],
  ['Productz', 'W2 Escala', 'Fila', 'Nenhum', 'App Bíblia F2+ (Strong\'s, refs, comentários) + assinatura clube', ''],
  ['i18n', 'W0 Ligar', 'Pronta', 'Nenhum', 'Esteira tradução EN→PT + piloto All of Grace em /pt', ''],
  ['i18n', 'W1 Consistência', 'Aguardando gate', 'Gabriel', 'GATE F2.4: decidir voz PT/ES', 'Locutor contratado ~$50-200 com cláusula'],
  ['i18n', 'W1 Consistência', 'Fila', 'Nenhum', 'Fila contínua: 5 livros PT + verbetes EN', ''],
  ['i18n', 'W2 Escala', 'Fila', 'Nenhum', 'ES (site + livros) + canais PT/ES', ''],
  ['Growth', 'W2 Escala', 'Fila', 'Nenhum', 'Ativar Growth', 'Critério: checkout live + BI + 30d de publicação consistente'],
];

const ESTEIRAS = [
  ['Render de longos Spurgeon', 'Content', 'Rodando', 'systemd VPS', '_factorio/remotion (factory-producer.service)', '24/7', '113/113 renderizados; dorme sem fila'],
  ['Agendador YouTube', 'Content', 'Pausada', 'cron VPS', 'remotion/schedule_channel.py', 'Diária 06:00 UTC', 'Pausado pelo incidente I1; guardião de canal instalado'],
  ['Publicação YouTube', 'Content', 'Construída', 'script VPS', 'remotion/publish_youtube.py', 'Sob demanda', 'Guardião confere EXPECTED_CHANNEL_ID'],
  ['Narração TTS (Kokoro)', 'Content', 'Rodando', 'container VPS', 'tts_kokoro', 'Sob demanda', '112 sermões narrados (~4 meses de acervo)'],
  ['Fábrica de shorts', 'Content', 'Construída', 'script manual', 'remotion/mine_clips.py + render_short.py', 'Manual', 'Piloto de 5 no R2 aguardando aprovação'],
  ['Render em lote (RunPods)', 'Content', 'Construída', 'RunPods', 'remotion/rp_handler.py', 'Sob demanda', 'Pra lotes; padrão diário é o híbrido na VPS'],
  ['Mineração de obras', 'Mineração', 'Rodando', 'script manual', 'scripts/mining/run.mjs', 'Sob demanda', '24 obras; gargalo é resolver URL'],
  ['Fila do plano (Notion → D1)', 'Mineração', 'Construída', 'script manual', 'scripts/mining/queue.mjs', 'Sob demanda', 'Biblioteca Mananciall → works'],
  ['Ponte minerado→produção', 'Mineração', 'Desenhada', 'script manual', '(criar em scripts/mining/)', 'Por lote', 'W0 da área'],
  ['Edição/tipografia', 'Productz', 'Rodando', 'script manual', 'mananciall-site scripts/editar.mjs', 'Por lote', '3.326 caps aprovados; portão letra a letra'],
  ['Sync acervo→Notion', 'Productz', 'Construída', 'script manual', 'mananciall-site scripts/sync-notion.mjs', 'Semanal', 'Upsert por Slug na Biblioteca'],
  ['Renderer de capas', 'Productz', 'Desenhada', 'script manual', '(criar no repo do site)', 'Por lote', 'Spec v0.2 em docs/capas'],
  ['Snapshot BI', 'Inteligência do Negócio', 'Desenhada', 'script manual', '(criar em scripts/bi/snapshot.mjs)', 'Semanal', 'W0 da área'],
  ['Health check #fabrica', 'Organização', 'Desenhada', 'cron VPS', '(criar)', 'Diária', 'P0.5: alarme de esteira parada'],
  ['/diretor-diario', 'Organização', 'Desenhada', 'skill', '(criar em .claude/skills/)', 'Diária', 'W1: 3x manual antes de agendar'],
  ['Intel semanal', 'Inteligência de Mercado', 'Desenhada', 'skill', '(criar)', 'Semanal', 'W1 da área'],
  ['Tradução EN→PT', 'i18n', 'Desenhada', 'script manual', '(criar no repo do site, scripts/i18n/)', 'Por livro', 'LLM-função + portão de qualidade'],
];

const INDICADORES = [
  ['Skills por nível (🟡/🟠/🟢)', 'Organização', 'Manual', 'Mensal', 'Mais 🟢 a cada mês', 'Catálogo em _factorio/.claude/skills'],
  ['Colisões de frente no mês', 'Organização', 'Manual', 'Mensal', '0', 'Handoff quebrado ou edição fora do território'],
  ['Players EN mapeados', 'Inteligência de Mercado', 'Manual', 'Semanal', 'Cobertura dos 3 segmentos', 'Livraria, app, canais'],
  ['Relatórios de intel entregues', 'Inteligência de Mercado', 'Manual', 'Semanal', '1/semana na W1', ''],
  ['Freshness do snapshot (dias)', 'Inteligência do Negócio', 'D1 produção', 'Semanal', '≤ 7', 'Dias desde a última coleta'],
  ['% métricas com coleta automática', 'Inteligência do Negócio', 'Manual', 'Mensal', 'Crescendo até 100%', ''],
  ['Obras mineradas (total)', 'Mineração', 'D1 mineração', 'Semanal', 'Fila nunca vazia', 'Hoje: 24'],
  ['Obras sem URL na fila', 'Mineração', 'D1 mineração', 'Semanal', '0', 'Hoje: 149'],
  ['Bloqueadas por copyright', 'Mineração', 'D1 mineração', 'Semanal', 'Honestidade > volume', 'Trava de DP'],
  ['Capítulos promovidos pra produção', 'Mineração', 'D1 produção', 'Semanal', 'Ponte rodando', ''],
  ['Longos publicados/semana', 'Content', 'YouTube API', 'Semanal', '7', ''],
  ['Shorts publicados/semana', 'Content', 'YouTube API', 'Semanal', '7+', ''],
  ['Dias sem furo de publicação', 'Content', 'YouTube API', 'Semanal', '0 furos', 'Furo = dia sem vídeo novo'],
  ['Inscritos do canal', 'Content', 'YouTube API', 'Semanal', 'Crescente', 'Charles Spurgeon Treasures'],
  ['Views/semana', 'Content', 'YouTube API', 'Semanal', 'Crescente', ''],
  ['Scans do QR (/go)', 'Content', 'D1 produção', 'Semanal', 'Ponte vídeo→loja viva', 'Depende da rota /go (Productz W0)'],
  ['Livros live na loja', 'Productz', 'D1 produção', 'Semanal', '50+ em 90d', 'Hoje: 27 EN + 2 PT'],
  ['Vendas/semana', 'Productz', 'Paddle', 'Semanal', 'Consistência > pico', 'Paddle + Asaas'],
  ['Receita/semana (USD+BRL)', 'Productz', 'Paddle', 'Semanal', 'Crescente', ''],
  ['Leads capturados', 'Productz', 'D1 produção', 'Semanal', '', 'Founding readers + em-breve PT'],
  ['% catálogo com capa v1', 'Productz', 'Manual', 'Semanal', '100% dos live', ''],
  ['Livros PT vendáveis', 'i18n', 'D1 produção', 'Semanal', '+1/semana na W1', 'Hoje: 2'],
  ['Verbetes EN publicados', 'i18n', 'Teable', 'Semanal', '', 'Wiki: PT mestre → EN'],
  ['% catálogo bilíngue', 'i18n', 'D1 produção', 'Mensal', 'Crescente', ''],
];

const TASKS = [
  // [demanda, área, responsáveis, notas]
  ['Webhook #fabrica + health check 48h (P0.5)', 'Organização', ['Claude'], 'Erro de esteira OU 48h sem vídeo agendado → aviso no Discord'],
  ['Skill /frente (abre sessão de área)', 'Organização', ['Claude'], 'Carrega doc 16 + tasks da área no Notion'],
  ['Preparar /diretor-diario (draft)', 'Organização', ['Claude'], 'Primeira execução manual é W1'],
  ['Mapear mercado EN no Referências de Editoras', 'Inteligência de Mercado', ['Claude'], 'Standard Ebooks, Monergism, Banner of Truth, Crossway, Ligonier, apps, canais YT'],
  ['Síntese Mapa do Mercado EN na página da área', 'Inteligência de Mercado', ['Claude'], '1 página por segmento: livraria, app, canal'],
  ['Revisar catálogo Indicadores com o Gabriel', 'Inteligência do Negócio', ['Claude', 'Monegatto'], 'Semeado 19/08: cortar/ajustar'],
  ['Construir scripts/bi/snapshot.mjs + 1ª rodada conferida', 'Inteligência do Negócio', ['Claude'], 'YouTube API + D1 + gateways → bi_snapshots → Notion'],
  ['Ponte minerado→produção (piloto 1 obra)', 'Mineração', ['Claude'], 'Formato combinado com Productz via handoff'],
  ['Adapter Archive.org', 'Mineração', ['Claude'], '21 obras da fila dependem dele'],
  ['Ampliar content_index (zerar 149 sem URL)', 'Mineração', ['Claude'], 'O gargalo é resolver, não minerar'],
  ['Snapshot cru no R2 (raw_key)', 'Mineração', ['Claude'], 'Proveniência de DP + evita re-raspar'],
  ['Preparar F4.5 fila de shorts (pós-gates)', 'Content', ['Claude'], 'Deixar pronto pra ligar quando I1 sair'],
  ['Preparar I3 limpeza do estado R2 (rodar pós-I1)', 'Content', ['Claude'], '18 vídeos do canal errado voltam à fila'],
  ['Religar cron I4 + 1 longo/dia (pós I1/P0.4)', 'Content', ['Claude'], ''],
  ['GATE: I1 re-auth YouTube (canal Charles Spurgeon Treasures)', 'Content', ['Monegatto'], 'auth_youtube.py; o guardião recusa canal errado'],
  ['GATE: aprovar piloto de 5 shorts', 'Content', ['Monegatto'], 'R2 renders/spurgeon_shorts/'],
  ['GATE: P0.4 autorizar agendador (1/dia)', 'Content', ['Monegatto'], ''],
  ['GATE: I2 decidir 5 vídeos públicos no canal pessoal', 'Content', ['Monegatto'], 'Apagar ou deixar privado'],
  ['GATE: F4.3 abrir apps TikTok + Meta', 'Content', ['Monegatto'], 'Review demora semanas: disparar cedo'],
  ['GATE: aprovar golden set da wiki (5 verbetes)', 'Content', ['Monegatto'], 'GOLDEN_REVIEW no Teable wiki_articles'],
  ['Rota /go + log de scan', 'Productz', ['Claude'], 'QR dos vídeos publicados hoje cai em 404'],
  ['/today no ar (leitura diária)', 'Productz', ['Claude'], '731 prontas no banco; SEO + destino dos canais'],
  ['Capas v1 nos 27 livros', 'Productz', ['Claude'], 'Renderer por coleção, caminho duotone'],
  ['Venda de teste ponta a ponta (pós-gates)', 'Productz', ['Claude'], 'Cupom MANANCIALLTESTE + Pix R$1'],
  ['GATE: Paddle Website Approval', 'Productz', ['Monegatto'], 'Checkout → Website Approval no painel'],
  ['GATE: Asaas conta bancária + documentos', 'Productz', ['Monegatto'], 'bankAccountInfo e documentation PENDING'],
  ['GATE: apagar CNAME www da Vercel', 'Productz', ['Monegatto'], 'Depois eu anexo o www ao Worker'],
  ['Esteira de tradução EN→PT (portão de qualidade)', 'i18n', ['Claude'], 'LLM-função; não muda sentido; glossário'],
  ['Piloto: All of Grace em /pt', 'i18n', ['Claude'], 'Revisão por amostragem antes de ir live'],
  ['GATE: F2.4 decidir voz PT/ES', 'i18n', ['Monegatto'], 'Locutor ~$50-200 com cláusula de uso sintético'],
];

// ————————————————————————————————————————————————————————————————
// EXECUÇÃO
// ————————————————————————————————————————————————————————————————
console.log('— 1. Upgrade do db do Gabriel → "Áreas"');
if (!ids.areasPatched) {
  die(await api(`databases/${AREAS_DB}`, 'PATCH', {
    title: [{ type: 'text', text: { content: 'Áreas' } }],
    icon: DB_ICON,
    properties: {
      'Missão': { rich_text: {} },
      'Norte 90 dias': { rich_text: {} },
      'Status': { select: { options: ['Futura', 'Desenhada', 'Ligando', 'Rodando', 'Consistente'].map(name => ({ name })) } },
      'Ordem': { number: { format: 'number' } },
      'Nível': { select: { options: ['Área', 'Sub-frente'].map(name => ({ name })) } },
      'Frente': { rich_text: {} },
      'Pertence a': { relation: { database_id: AREAS_DB, type: 'single_property', single_property: {} } },
    },
  }), 'patch Áreas');
  ids.areasPatched = true; save();
}

console.log('— 2. Linhas das áreas (upgrade in place + novas)');
if (!ids.rows) ids.rows = {};
{
  const q = die(await api(`databases/${AREAS_DB}/query`, 'POST', { page_size: 100 }), 'query Áreas');
  const byTitle = {};
  for (const r of q.results) byTitle[titleOf(r)] = r.id;
  // renomear as existentes
  for (const [antigo, novo] of Object.entries(RENAME)) {
    if (byTitle[antigo] && !byTitle[novo]) {
      die(await api(`pages/${byTitle[antigo]}`, 'PATCH', { properties: { 'Nome': { title: rt(novo) } } }), `rename ${antigo}`);
      byTitle[novo] = byTitle[antigo];
    }
  }
  // garantir todas as áreas
  for (const a of AREAS) {
    if (ids.rows[a.nome]) continue;
    let pageId = byTitle[a.nome];
    const props = {
      'Nome': { title: rt(a.nome) },
      'Missão': rich(a.missao),
      'Norte 90 dias': rich(a.norte),
      'Status': sel(a.status),
      'Ordem': num(a.ordem),
      'Nível': sel(a.nivel),
      'Frente': rich(a.frente),
    };
    if (!pageId) {
      const created = die(await api('pages', 'POST', { parent: { database_id: AREAS_DB }, properties: props }), `criar área ${a.nome}`);
      pageId = created.id;
    } else {
      die(await api(`pages/${pageId}`, 'PATCH', { properties: props }), `props área ${a.nome}`);
    }
    ids.rows[a.nome] = pageId; save();
  }
  // sub-frentes
  for (const s of SUBFRENTES) {
    if (ids.rows[s.nome]) continue;
    const pageId = byTitle[s.nome];
    if (!pageId) { console.log(`   (sub-frente ${s.nome} não achada, pulando)`); continue; }
    die(await api(`pages/${pageId}`, 'PATCH', {
      properties: {
        'Missão': rich(s.desc),
        'Nível': sel('Sub-frente'),
        'Status': sel('Ligando'),
        'Pertence a': relOne(ids.rows[s.pertenceA]),
      },
    }), `sub-frente ${s.nome}`);
    ids.rows[s.nome] = pageId; save();
  }
}

console.log('— 3. Página-hub 🏭 Fábrica');
if (!ids.hubPage) {
  const hub = die(await api('pages', 'POST', {
    parent: { type: 'page_id', page_id: BS_PAGE },
    icon: { type: 'emoji', emoji: '🏭' },
    properties: { title: { title: rt('Fábrica') } },
    children: [
      CALL('🏭', 'A fábrica em uma frase: Claude constrói a esteira, a esteira produz o volume, Claude supervisiona e melhora. Piloto: Mananciall. Fonte canônica do desenho: _factorio/docs/16_BLUEPRINT_AREAS.md (git). Esta página é a vitrine gerenciável.'),
      H2('Decisões de 19/08/2026'),
      B('Sem pressa de receita: todas as áreas em pé, ligando uma por uma, produzindo gradativamente mais com consistência.'),
      B('Escopo: fábrica toda; Mananciall é o piloto (Bluue/ZOAC herdam o molde).'),
      B('Notion é modelo/vitrine; um dia vira sistema próprio (estilo bi.br4nds.com.br). Dado NUNCA mora só no Notion.'),
      B('7 frentes (chats) em paralelo; prompt de abertura na página de cada área.'),
      H2('Onde mora cada dado (regra-mãe)'),
      CALL('🗄️', 'Máquina escreve na máquina; Notion é plano de controle humano + vitrine; sync de mão única máquina→Notion, exceto campos onde o Gabriel manda. O sistema próprio futuro lê da máquina, nunca do Notion: por isso o Notion é descartável por design.'),
      B('Plano de catálogo → Notion Biblioteca Mananciall (controle humano)'),
      B('Texto bruto minerado → D1 mananciall-mining · Produto → D1 mananciall-db'),
      B('Fatos de BI → D1 bi_snapshots (vitrine: banco Indicadores; depois app BI)'),
      B('Intel de mercado → Notion enquanto curadoria humana; volume/scrape → Teable'),
      B('Gestão da fábrica (áreas, roadmap, tasks humanas) → Notion · estado fino de esteira → Teable/D1'),
      B('Código/SOPs/docs → git · Binários → R2 · Credenciais → _factorio/.env'),
      H2('Ordem de ativação (uma vira "Rodando" por vez)'),
      N('Organização (ligando 19/08)'), N('Content (destravar gates: é a que mais rende por hora)'), N('Mineração'), N('Productz'), N('Inteligência do Negócio'), N('Inteligência de Mercado'), N('i18n'), N('Growth (futura: checkout + BI + 30d de publicação)'),
      H2('Gates do Gabriel (o que só você destrava)'),
      CALL('🚦', 'Cada gate existe como task sua no banco Tasks (Responsável=Monegatto, prefixo GATE). Sugestão de view: Tasks filtrado Responsável=Monegatto + Status≠Finalizado.'),
      B('Content: I1 re-auth YouTube · I2 destino dos 5 vídeos · P0.4 agendador · aprovar piloto de shorts · F4.2 canal de shorts · F4.3 apps TikTok/Meta · golden set da wiki · F3.1 billing Lightning'),
      B('Productz: Paddle Website Approval · Asaas conta+docs · apagar CNAME www · decisão assinatura Jornada'),
      B('i18n: F2.4 voz PT/ES (locutor)'),
      H2('Bancos e views'),
      P('Bancos novos moram nesta página (abaixo). Áreas segue ao lado da Biblioteca na página Business System (a API não move banco: se quiser, arraste pra cá).'),
      LINKDB(AREAS_DB),
      LINKDB(TASKS_DB),
      LINKDB(BIBLIOTECA_DB),
      LINKDB(REFERENCIAS_DB),
      P('Views são manuais na UI (a API não cria): sugestões: Áreas como board por Status ordenado por Ordem; Roadmap como board por Onda agrupado por Área; Tasks filtrado por Área; Indicadores agrupado por Área.'),
      H2('Como cada frente opera'),
      B('1 chat = 1 área = 1 território de arquivos (definido na página da área).'),
      B('Toda sessão termina com: commit no repo da frente + tasks atualizadas aqui + report de 10 linhas.'),
      B('Gate é do Gabriel: frente bloqueada cobra o gate no report e segue pra próxima entrega.'),
      B('Estado fino de esteira nunca vira task (1 task = 1 operação de alto nível).'),
    ],
  }), 'criar hub');
  ids.hubPage = hub.id; save();
}

console.log('— 4. Bancos Roadmap / Esteiras / Indicadores');
async function ensureDb(key, title, properties) {
  if (ids[key]) return ids[key];
  const db = die(await api('databases', 'POST', {
    parent: { type: 'page_id', page_id: ids.hubPage },
    icon: DB_ICON,
    title: [{ type: 'text', text: { content: title } }],
    properties,
  }), `criar db ${title}`);
  ids[key] = db.id; save();
  return db.id;
}
const areaRel = { relation: { database_id: AREAS_DB, type: 'dual_property', dual_property: {} } };
await ensureDb('dbRoadmap', 'Roadmap', {
  'Entrega': { title: {} },
  'Área': areaRel,
  'Onda': { select: { options: ['W0 Ligar', 'W1 Consistência', 'W2 Escala'].map(name => ({ name })) } },
  'Status': { select: { options: ['Fila', 'Pronta', 'Em construção', 'Aguardando gate', 'Entregue'].map(name => ({ name })) } },
  'Gate': { select: { options: ['Nenhum', 'Gabriel', 'Externo'].map(name => ({ name })) } },
  'Detalhe': { rich_text: {} },
});
await ensureDb('dbEsteiras', 'Esteiras', {
  'Esteira': { title: {} },
  'Área': areaRel,
  'Status': { select: { options: ['Rodando', 'Pausada', 'Construída', 'Em construção', 'Desenhada', 'Backlog'].map(name => ({ name })) } },
  'Camada': { select: { options: ['cron VPS', 'systemd VPS', 'container VPS', 'script VPS', 'script manual', 'trigger.dev', 'Worker', 'RunPods', 'skill'].map(name => ({ name })) } },
  'Código': { rich_text: {} },
  'Cadência': { rich_text: {} },
  'Notas': { rich_text: {} },
});
await ensureDb('dbIndicadores', 'Indicadores', {
  'Indicador': { title: {} },
  'Área': areaRel,
  'Fonte': { select: { options: ['YouTube API', 'D1 produção', 'D1 mineração', 'Paddle', 'Asaas', 'Teable', 'R2', 'Manual'].map(name => ({ name })) } },
  'Cadência': { select: { options: ['Diária', 'Semanal', 'Mensal'].map(name => ({ name })) } },
  'Meta': { rich_text: {} },
  'Valor atual': { rich_text: {} },
  'Atualizado em': { date: {} },
  'Como ler': { rich_text: {} },
});

console.log('— 5. Relation Área no banco Tasks');
if (!ids.tasksAreaProp) {
  const t = die(await api(`databases/${TASKS_DB}`), 'get Tasks');
  if (!t.properties['Área']) {
    die(await api(`databases/${TASKS_DB}`, 'PATCH', { properties: { 'Área': areaRel } }), 'patch Tasks Área');
  }
  ids.tasksAreaProp = true; save();
}

console.log('— 6. Renomear back-relations no db Áreas');
if (!ids.backRelsRenamed) {
  const areasDb = die(await api(`databases/${AREAS_DB}`), 'get Áreas');
  const wanted = { [ids.dbRoadmap]: 'Roadmap', [ids.dbEsteiras]: 'Esteiras', [ids.dbIndicadores]: 'Indicadores', [TASKS_DB]: 'Tasks' };
  const renames = {};
  for (const [name, p] of Object.entries(areasDb.properties)) {
    if (p.type !== 'relation') continue;
    const alvo = wanted[p.relation.database_id?.replace(/-/g, '')] ?? wanted[p.relation.database_id];
    if (alvo && name.startsWith('Related to') && !areasDb.properties[alvo]) renames[name] = { name: alvo };
  }
  if (Object.keys(renames).length) die(await api(`databases/${AREAS_DB}`, 'PATCH', { properties: renames }), 'rename back-relations');
  ids.backRelsRenamed = true; save();
}

console.log('— 7. Seeds: Roadmap');
if (!ids.seedRoadmap) {
  for (const [area, onda, status, gate, entrega, detalhe] of ROADMAP) {
    die(await api('pages', 'POST', {
      parent: { database_id: ids.dbRoadmap },
      properties: {
        'Entrega': { title: rt(entrega) },
        'Área': relOne(ids.rows[area]),
        'Onda': sel(onda),
        'Status': sel(status),
        'Gate': sel(gate),
        ...(detalhe ? { 'Detalhe': rich(detalhe) } : {}),
      },
    }), `roadmap ${entrega}`);
  }
  ids.seedRoadmap = true; save();
}

console.log('— 8. Seeds: Esteiras');
if (!ids.seedEsteiras) {
  for (const [nome, area, status, camada, codigo, cadencia, notas] of ESTEIRAS) {
    die(await api('pages', 'POST', {
      parent: { database_id: ids.dbEsteiras },
      properties: {
        'Esteira': { title: rt(nome) },
        'Área': relOne(ids.rows[area]),
        'Status': sel(status),
        'Camada': sel(camada),
        'Código': rich(codigo),
        'Cadência': rich(cadencia),
        ...(notas ? { 'Notas': rich(notas) } : {}),
      },
    }), `esteira ${nome}`);
  }
  ids.seedEsteiras = true; save();
}

console.log('— 9. Seeds: Indicadores');
if (!ids.seedIndicadores) {
  for (const [nome, area, fonte, cadencia, meta, comoLer] of INDICADORES) {
    die(await api('pages', 'POST', {
      parent: { database_id: ids.dbIndicadores },
      properties: {
        'Indicador': { title: rt(nome) },
        'Área': relOne(ids.rows[area]),
        'Fonte': sel(fonte),
        'Cadência': sel(cadencia),
        ...(meta ? { 'Meta': rich(meta) } : {}),
        ...(comoLer ? { 'Como ler': rich(comoLer) } : {}),
      },
    }), `indicador ${nome}`);
  }
  ids.seedIndicadores = true; save();
}

console.log('— 10. Seeds: Tasks (1ª onda + GATEs)');
if (!ids.seedTasks) {
  // achar a unidade Manancial
  let manancialId = ids.unidadeManancial;
  if (!manancialId) {
    const u = die(await api(`databases/${UNIDADES_DB}/query`, 'POST', { page_size: 100 }), 'query Unidades');
    const row = u.results.find(r => titleOf(r).toLowerCase().includes('manancial'));
    manancialId = row?.id;
    ids.unidadeManancial = manancialId; save();
  }
  for (const [demanda, area, resp, notas] of TASKS) {
    die(await api('pages', 'POST', {
      parent: { database_id: TASKS_DB },
      properties: {
        'Demanda': { title: rt(demanda) },
        'Status': sel('Iniciar'),
        'Responsável': { multi_select: resp.map(name => ({ name })) },
        'Área': relOne(ids.rows[area]),
        ...(manancialId && area !== 'Organização' ? { 'Unity': relOne(manancialId) } : {}),
        ...(notas ? { 'Notas': rich(notas) } : {}),
      },
    }), `task ${demanda}`);
  }
  ids.seedTasks = true; save();
}

console.log('— 11. Blueprint na página de cada área');
if (!ids.blueprints) ids.blueprints = {};
for (const a of AREAS) {
  if (ids.blueprints[a.nome]) continue;
  const blocks = [
    CALL('🎯', `Missão: ${a.missao}\nNorte 90 dias: ${a.norte}`),
    H3('O que já existe'), ...a.existe.map(B),
    H3('W0 · Ligar'), ...a.w0.map(B),
  ];
  if (a.w1.length) blocks.push(H3('W1 · Consistência'), ...a.w1.map(B));
  if (a.w2.length) blocks.push(H3('W2 · Escala'), ...a.w2.map(B));
  blocks.push(H3('Onde moram os dados'), P(a.dados));
  if (a.indicadores.length) blocks.push(H3('Indicadores'), ...a.indicadores.map(B));
  if (a.gates.length) blocks.push(H3('Gates do Gabriel'), ...a.gates.map(B));
  blocks.push(H3('Território de arquivos'), P(a.territorio));
  if (PROMPTS[a.nome]) blocks.push(DIV(), H3('Prompt de abertura da frente (colar num chat novo)'), CODE(PROMPTS[a.nome]));
  die(await api(`blocks/${ids.rows[a.nome]}/children`, 'PATCH', { children: blocks }), `blueprint ${a.nome}`);
  ids.blueprints[a.nome] = true; save();
}
for (const s of SUBFRENTES) {
  if (ids.blueprints[s.nome] || !ids.rows[s.nome]) continue;
  die(await api(`blocks/${ids.rows[s.nome]}/children`, 'PATCH', { children: [P(s.desc)] }), `blueprint ${s.nome}`);
  ids.blueprints[s.nome] = true; save();
}

console.log('\n✅ Fábrica montada. IDs em notion-fabrica-ids.json');
console.log(`   Hub: https://www.notion.so/${(ids.hubPage || '').replace(/-/g, '')}`);
