import { CONTENT_BASE } from './content.base.mjs';

export async function onRequest(context) {
  const { request, next, env } = context;
  const url = new URL(request.url);
  const host = request.headers.get('host') || '';

  const isPageRequest = !url.pathname.match(
    /\.(js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|map|json|webp|avif|mp4|webm|pdf|xml|txt|robots)$/i
  ) && !url.pathname.startsWith('/api/')
    && !url.pathname.startsWith('/webhook/');

  if (!isPageRequest) return next();

  const fbclid = getRawParam(url.search, 'fbclid');
  const gclid = getRawParam(url.search, 'gclid');
  const msclkid = getRawParam(url.search, 'msclkid');
  const ttclid = getRawParam(url.search, 'ttclid');

  const utmSource = url.searchParams.get('utm_source') || '';
  const utmMedium = url.searchParams.get('utm_medium') || '';
  const utmCampaign = url.searchParams.get('utm_campaign') || '';
  const utmContent = url.searchParams.get('utm_content') || '';
  const utmTerm = url.searchParams.get('utm_term') || '';

  const cookies = parseCookies(request.headers.get('Cookie') || '');
  let sessionId = cookies['_bnd_sid'] || '';
  let externalId = cookies['_bnd_eid'] || '';
  let existingFbc = cookies['_fbc'] || '';
  let existingFbp = cookies['_fbp'] || '';

  // Salto de domínio (LP-ponte -> funil): cookie não atravessa domínio, então a ponte
  // manda a sessão em `?_sid=`. Adotamos aqui pra não abrir uma sessão órfã e perder
  // o vínculo clique->venda. Só aceita UUID — parâmetro é entrada não confiável.
  const carriedSid = url.searchParams.get('_sid') || '';
  if (!sessionId && isUuid(carriedSid)) sessionId = carriedSid;

  const isNewSession = !sessionId;
  if (!sessionId) sessionId = crypto.randomUUID();
  if (!externalId) externalId = crypto.randomUUID();

  const SUB_DOMAIN_INDEX = computeSubDomainIndex(host);

  let fbc = existingFbc;
  if (fbclid) {
    const existingPayload = existingFbc ? extractFbcPayload(existingFbc) : '';
    if (!existingFbc || existingPayload !== fbclid) {
      fbc = `fb.${SUB_DOMAIN_INDEX}.${Date.now()}.${fbclid}`;
    }
  }

  let fbp = existingFbp;
  if (!fbp) {
    fbp = `fb.${SUB_DOMAIN_INDEX}.${Date.now()}.${Math.floor(Math.random() * 9000000000) + 1000000000}`;
  }

  const clientIp = request.headers.get('cf-connecting-ip') || '';
  const userAgent = request.headers.get('user-agent') || '';
  const referrer = request.headers.get('referer') || '';
  const landingUrl = url.toString();

  // Lição 0.1.2 (crawler do FB inflou o funil da ZOAC em 8x): o PageView
  // server-side também classifica bot, não só o /api/tracker. O filtro por
  // status < 400 lá embaixo NÃO cobre isso — crawler acessa página real com 200.
  const { isBot, botReason } = detectBot(userAgent);

  // Config do domínio: uma leitura só, reaproveitada pelo rewrite e pelo log.
  const config = await loadDomainConfig(env, host);

  // Porta de entrada por domínio: cada domínio que já roda tráfego tem a sua
  // (ex.: bluue.io/ serve o quiz). Sem isso, plugar um domínio de produção aqui
  // cairia na home institucional e queimaria o clique do anúncio.
  let effectivePath = url.pathname;
  if (url.pathname === '/') {
    const rootRoute = resolveRootRoute(config);
    if (rootRoute && rootRoute !== '/') effectivePath = rootRoute;
  }

  // Sorteio de variante. Roda DEPOIS do papel do domínio: o experimento enxerga a
  // rota que o visitante realmente vai ver, não a barra que ele digitou.
  const experiment = await assignExperiments(env, host, effectivePath, sessionId);
  const targetPath = experiment.route || effectivePath;

  let response;
  if (targetPath !== url.pathname) {
    const rewritten = new URL(url.toString());
    rewritten.pathname = targetPath;
    response = await next(new Request(rewritten.toString(), request));
  }
  if (!response) response = await next();

  const maxAge = 34560000;
  const cookieBase = `Path=/; Max-Age=${maxAge}; SameSite=Lax; Secure`;

  const newHeaders = new Headers(response.headers);
  newHeaders.append('Set-Cookie', `_bnd_sid=${sessionId}; ${cookieBase}`);
  newHeaders.append('Set-Cookie', `_bnd_eid=${externalId}; ${cookieBase}`);
  newHeaders.append('Set-Cookie', `_fbp=${fbp}; ${cookieBase}`);
  if (fbc) newHeaders.append('Set-Cookie', `_fbc=${fbc}; ${cookieBase}`);

  // A variante vai num cookie legível pela página: é assim que um teste de headline
  // ou preço acontece SEM rota nova e sem deploy. Teste desligado = cookie apagado,
  // pra página nunca renderizar variante de experimento que já morreu.
  if (experiment.label) {
    newHeaders.append('Set-Cookie', `_bnd_var=${experiment.label}; ${cookieBase}`);
  } else if (cookies['_bnd_var']) {
    newHeaders.append('Set-Cookie', '_bnd_var=; Path=/; Max-Age=0; SameSite=Lax; Secure');
  }

  let newResponse = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });

  // Conteúdo da variante injetado no <head>, antes de qualquer script da página.
  // É isto que permite testar headline e preço SEM deploy e SEM piscada: o HTML
  // já sai do servidor com o texto certo. Só roda quando existe teste ativo com
  // substituição de conteúdo; fora disso o custo é zero.
  //
  // No mesmo passe vão os scripts extras do domínio (ver `parseScripts`), que
  // entram no FIM do <head>, depois do conteúdo da variante.
  const domainScripts = parseScripts(config?.scripts);

  if (experiment.content || domainScripts.length) {
    // De chave -> texto novo para texto BASE -> texto novo. O HTML da primeira
    // tela é gerado no build, então trocar só no navegador faria o React manter o
    // texto do build na hidratação (pego em ensaio) ou o texto piscar na cara de
    // quem chegou pelo anúncio. Trocando aqui, a variante já sai correta do servidor.
    const swaps = new Map();
    if (experiment.content) {
      for (const [key, value] of Object.entries(experiment.content)) {
        const base = CONTENT_BASE[key];
        if (base && value && base !== value) swaps.set(base, value);
      }
    }

    const rewriter = new HTMLRewriter().on('head', {
      element(el) {
        if (experiment.content) {
          el.prepend(
            `<script>window.__CRO_CONTENT__=${safeJsonForScript(experiment.content)}</script>`,
            { html: true }
          );
        }
        for (const script of domainScripts) {
          const tag = scriptTag(script);
          if (tag) el.append(tag, { html: true });
        }
      },
    });

    if (swaps.size) {
      rewriter.on('*', {
        text(chunk) {
          const trimmed = chunk.text.trim();
          if (!trimmed) return;
          const replacement = swaps.get(trimmed);
          if (replacement) chunk.replace(replacement);
        },
      });
    }

    newResponse = rewriter.transform(newResponse);
  }

  // Só grava pageview de resposta que deu certo. Com o 404 real no ar
  // (src/pages/404.astro), robô varrendo /.env, /wp-admin e afins cai aqui com
  // status 404 e NÃO vira PageView — antes cada varredura sujava o funil.
  if (env.CRO_DB && response.status < 400) {
    context.waitUntil((async () => {
      try {
        if (config) {
          await env.CRO_DB.prepare(`
            INSERT INTO data_tracker (session_id, brand, product, domain, event_name, fbclid, gclid, fbp, fbc, utm_source, utm_medium, utm_campaign, utm_content, utm_term, ip_address, user_agent, referrer, landing_url, external_id, is_bot, bot_reason, consent_status, variant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            sessionId, config.brand, '', host, 'PageView',
            fbclid, gclid, fbp, fbc,
            utmSource, utmMedium, utmCampaign, utmContent, utmTerm,
            clientIp, userAgent, referrer, landingUrl, externalId,
            isBot ? 1 : 0, botReason, 'unknown', experiment.label || null
          ).run();
        }
      } catch (e) {
        console.error('Middleware D1 error:', e.message);
      }
    })());
  }

  return newResponse;
}

// ---------------------------------------------------------------------------
// Config do domínio
// ---------------------------------------------------------------------------
//
// Cache no isolado, 60s, mesmo padrão e mesmo motivo do cache de experimentos.
// Antes a config só era esperada na raiz (pra resolver a porta de entrada) e nas
// demais rotas ia solta pro log. Agora ela está no caminho crítico de TODA página,
// porque é dela que saem os scripts do domínio — e um script de rastreio que chega
// depois do HTML não serve pra nada.
//
// Preço: mudar `domain_config` leva até 60s pra valer em todo lugar. É o mesmo
// atraso que já se aceita pra ligar e desligar experimento.
const configCache = new Map();

async function loadDomainConfig(env, host) {
  if (!env.CRO_DB) return null;

  const cached = configCache.get(host);
  if (cached && Date.now() - cached.at < 60000) return cached.row;

  try {
    const row = await env.CRO_DB.prepare(
      'SELECT brand, meta_pixel_id, ga4_id, root_route, scripts FROM domain_config WHERE domain = ? AND active = 1'
    ).bind(host).first();

    configCache.set(host, { at: Date.now(), row: row || null });
    return row || null;
  } catch {
    // Falha de leitura NÃO entra no cache. Se entrasse, um soluço de 1 segundo no
    // banco apagaria a config do domínio pelos 60s seguintes: página caindo na home
    // errada e pageview sem marca. Vale o último valor bom, se houver.
    return cached ? cached.row : null;
  }
}

// ---------------------------------------------------------------------------
// Scripts extras por domínio
// ---------------------------------------------------------------------------
//
// Existe porque unificar os repositórios significa herdar domínio que já roda com
// ferramenta de terceiro instalada. O `bluue.men` carrega a tag da Popsixle, e é
// ELA quem injeta o pixel e manda os eventos do servidor. Trazer o domínio pra cá
// sem carregar a tag não seria unificar: seria desligar o rastreio de quem opera.
//
// Agnóstica de propósito. Uma coluna `popsixle_tag` envelheceria na primeira vez
// que entrasse um Hotjar ou um pixel de TikTok. Aqui é `[{"src":...}]` no banco,
// sem migração nova e sem `if` de fornecedor no código.
//
// Injeção é no SERVIDOR, no fim do <head>: mesma posição que a tag ocupa no HTML
// de origem, já sai pronta no documento, sem esperar fetch e sem depender do JS
// da página.
function parseScripts(raw) {
  if (!raw) return [];
  let list;
  try {
    list = JSON.parse(raw);
  } catch {
    return [];
  }
  if (!Array.isArray(list)) return [];
  return list.filter((s) => s && (typeof s.src === 'string' || typeof s.code === 'string'));
}

function scriptTag(script) {
  if (script.src) {
    // Só https. Barra `javascript:`, `data:` e http em claro — o conteúdo vem do
    // banco, e banco é lugar onde alguém digita errado às 2 da manhã.
    if (!/^https:\/\//i.test(script.src)) return '';
    const attrs = [`src="${escapeAttr(script.src)}"`];
    if (script.type) attrs.push(`type="${escapeAttr(script.type)}"`);
    if (script.async) attrs.push('async');
    if (script.defer) attrs.push('defer');
    return `<script ${attrs.join(' ')}></script>`;
  }
  // Inline: só precisa garantir que o próprio conteúdo não feche a tag antes da hora.
  return `<script>${String(script.code).replace(/<\/script/gi, '<\\/script')}</script>`;
}

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// A raiz do domínio é `root_route`, e SÓ `root_route`. NULL/vazio = home do app.
//
// Já foi diferente: existia uma tabelinha `role -> rota` aqui (`funil` mandava a
// raiz pro /quiz/v1/). Ou seja, a config declarava uma CATEGORIA e o código
// deduzia o fato. Categoria envelhece: o bluue.io estava marcado `funil`, mas os
// 16 anúncios ativos da raiz dele apontam pra HOME — a virada teria mandado 16
// anúncios pro lugar errado. Pego em auditoria (03/08), antes de virar.
//
// Regra desde a migração 014: config declara fato ("a raiz deste domínio serve
// /ps"), nunca intenção. `role` sobrevive no banco como etiqueta de inventário
// (Notion, BI), mas roteamento não lê etiqueta.
function resolveRootRoute(config) {
  if (!config) return '';
  return normalizeRoute(config.root_route || '');
}

// O site é estático: `/pastilha` (sem barra) responde 308 pra `/pastilha/`. Numa
// REESCRITA isso é grave — o 308 vaza pro visitante e a URL do anúncio muda, que é
// exatamente o que a reescrita existe pra evitar. Normalizar aqui é o que impede
// uma linha de configuração digitada sem barra de virar redirect em produção.
// Pego em ensaio, com o experimento de fumaça, antes de qualquer campanha.
function normalizeRoute(route) {
  if (!route || route === '/') return route || '';
  if (route.endsWith('/')) return route;
  const lastSegment = route.split('/').pop() || '';
  if (lastSegment.includes('.')) return route; // arquivo (ex.: /algo.html): não mexer
  return `${route}/`;
}

// ---------------------------------------------------------------------------
// Motor de teste A/B
// ---------------------------------------------------------------------------
//
// Três decisões que fazem esse motor valer alguma coisa:
//
// 1. SORTEIO POR HASH, não por moeda. A variante é uma função pura da sessão e da
//    chave do teste. Consequências: a mesma pessoa vê a mesma variante em todas as
//    páginas e em todas as visitas, não existe piscada (a decisão é tomada no
//    servidor, antes do HTML sair), e não precisa gravar sorteio nenhum.
//
// 2. CACHE NO ISOLADO, 60s. Sem isso, todo pageview pagaria uma leitura no banco
//    só pra descobrir que não tem teste rodando. Com ele, o custo do motor com
//    zero experimentos é zero. O preço: ligar/desligar leva até 60s pra valer em
//    todo lugar — o mesmo atraso que já existe na config do domínio.
//
// 3. FALHA ABERTA. Qualquer erro (banco fora, JSON torto, peso zerado) devolve
//    "sem experimento": o visitante vê a página normal. Um teste A/B nunca pode
//    ser o motivo de uma página não abrir — quem paga a conta é o anúncio.

let expCache = { at: 0, rows: null };

async function loadRunningExperiments(env) {
  const now = Date.now();
  if (expCache.rows && now - expCache.at < 60000) return expCache.rows;

  let rows = [];
  try {
    const res = await env.CRO_DB.prepare(
      "SELECT exp_key, domain, path_prefix, variants FROM experiments WHERE status = 'running'"
    ).all();
    rows = res.results || [];
  } catch {
    rows = [];
  }

  expCache = { at: now, rows };
  return rows;
}

async function assignExperiments(env, host, path, sessionId) {
  const empty = { label: '', route: '', content: null };
  if (!env.CRO_DB || !sessionId) return empty;

  try {
    const running = await loadRunningExperiments(env);
    if (!running.length) return empty;

    const labels = [];
    const content = {};
    let route = '';

    for (const exp of running) {
      if (exp.domain && exp.domain !== host) continue;

      const prefix = exp.path_prefix || '/';
      if (!path.startsWith(prefix)) continue;

      const variant = pickVariant(exp.variants, bucketOf(`${sessionId}:${exp.exp_key}`));
      if (!variant || !variant.name) continue;

      labels.push(`${exp.exp_key}:${variant.name}`);

      // Substituições de texto/preço da variante. Vão injetadas no HTML, então a
      // página nasce com o conteúdo certo: sem requisição extra e sem piscada.
      if (variant.content && typeof variant.content === 'object') {
        Object.assign(content, variant.content);
      }

      // Variante com rota própria só reescreve quando o visitante está EXATAMENTE
      // na página em teste. Sem isso, um teste em '/quiz' sequestraria '/quiz/obrigado'.
      if (variant.route && samePath(path, prefix) && !route) route = normalizeRoute(variant.route);
    }

    return {
      label: labels.join(','),
      route,
      content: Object.keys(content).length ? content : null,
    };
  } catch {
    return empty;
  }
}

// O conteúdo da variante é escrito por nós no banco, mas ainda assim vai pra
// dentro de uma tag <script>: `</script>` no meio de um texto encerraria a tag e
// o resto viraria HTML. Escapar aqui é o que impede um erro de digitação numa
// headline de quebrar a página inteira.
function safeJsonForScript(obj) {
  return JSON.stringify(obj)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

function samePath(a, b) {
  const norm = (p) => (p.length > 1 && p.endsWith('/') ? p.slice(0, -1) : p);
  return norm(a) === norm(b);
}

// FNV-1a: barato, sem dependência e bem distribuído para o que precisamos aqui
// (repartir sessões em 100 baldes). Não é hash criptográfico e não precisa ser.
function bucketOf(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) % 100;
}

function pickVariant(variantsJson, bucket) {
  let list;
  try {
    list = JSON.parse(variantsJson);
  } catch {
    return null;
  }
  if (!Array.isArray(list) || !list.length) return null;

  // Pesos que não somam 100 são normalizados: 70/30, 1/1 e 50/50 funcionam igual,
  // e ninguém perde tráfego por erro de digitação na configuração.
  const total = list.reduce((sum, v) => sum + (Number(v.weight) || 0), 0);
  if (total <= 0) return null;

  let acc = 0;
  for (const v of list) {
    acc += ((Number(v.weight) || 0) / total) * 100;
    if (bucket < acc) return v;
  }
  return list[list.length - 1];
}

function isUuid(v) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v || '');
}

function parseCookies(cookieHeader) {
  const cookies = {};
  cookieHeader.split(';').forEach(cookie => {
    const [name, ...rest] = cookie.trim().split('=');
    if (name) cookies[name.trim()] = rest.join('=');
  });
  return cookies;
}

function getRawParam(search, name) {
  const match = (search || '').match(new RegExp('[?&]' + name + '=([^&]*)'));
  return match ? match[1] : '';
}

function extractFbcPayload(fbc) {
  if (!fbc) return '';
  const parts = fbc.split('.');
  return parts.length >= 4 ? parts[3] : '';
}

const CC_TLDS = new Set([
  'com.br', 'com.ar', 'com.mx', 'com.co', 'com.pe', 'com.ve', 'com.ec',
  'com.au', 'com.pt', 'com.pl', 'com.tr', 'com.ua', 'com.ru',
  'co.uk', 'co.jp', 'co.kr', 'co.nz', 'co.za', 'co.in', 'co.id',
]);

function computeSubDomainIndex(host) {
  if (!host) return 1;
  const hostname = host.split(':')[0].toLowerCase();
  const parts = hostname.split('.');
  if (parts.length < 2) return 0;
  const lastTwo = parts.slice(-2).join('.');
  if (CC_TLDS.has(lastTwo)) return 2;
  return 1;
}
// ---------------------------------------------------------------------------
// Bot / crawler (lição 0.1.2). Ao ler o funil: SEMPRE filtrar is_bot = 0.
// ---------------------------------------------------------------------------
function detectBot(userAgent) {
  if (!userAgent || userAgent.length < 10) return { isBot: true, botReason: 'Missing or short user-agent' };
  const patterns = [
    { p: /facebookexternalhit|facebot|meta-externalads/i, r: 'Facebook crawler' },
    { p: /googlebot|google-inspectiontool/i, r: 'Googlebot' },
    { p: /whatsapp/i, r: 'WhatsApp preview' },
    { p: /slackbot|telegrambot|twitterbot|linkedinbot|discordbot/i, r: 'Social crawler' },
    { p: /bot|crawler|spider|scraper|headless/i, r: 'Generic bot' },
    { p: /python-requests|axios|node-fetch|curl|wget|httpie|go-http/i, r: 'HTTP library' },
  ];
  for (const { p, r } of patterns) {
    if (p.test(userAgent)) return { isBot: true, botReason: r };
  }
  return { isBot: false, botReason: '' };
}
