// zoac-purchase-check — o elo que fecha a atribuição da ZOAC.
// Cron 5min: GHL Payments (orders pagas) -> dedup (purchases_sent) -> enriquece
// pelo CONTATO (o _sid mora na atribuição dele) -> match sck no D1 -> CAPI
// Purchase (event_id = order_id) -> ledger + data_tracker.
//
// ADAPTER GHL/Conversion Goat (1ª implementação, 07/08/2026). Diferenças vs B4You:
// - A venda vem de GET /payments/orders (services.leadconnectorHQ.com — o host
//   sem "hq" NÃO existe mais, NXDOMAIN).
// - O pedido NÃO carrega o sck. Quem carrega é o CONTATO: o order form preserva
//   a query string e o GHL grava attributionSource.url com ?_sid=... (validado
//   em venda real: pedido 6a64baa7 -> contato -> _sid presente). Por isso o
//   passo enrichSale() antes do match.
// - amount vem em UNIDADES da moeda (US$1 = 1), não em centavos. O adapter
//   multiplica por 100 pra manter o contrato interno (offer_price em centavos).
// - Moeda é dinâmica (USD hoje); nada de BRL cravado.
// - GÊNERO: SEM fallback 'm'. Aquilo é decisão de público da Bluue (80,5% M
//   medido); a ZOAC vende pra agências/creators, público misto. Aqui só entra
//   inferência segura (listas + sufixo); o resto fica sem o parâmetro.
//
// Vendas sem match ficam 'unmatched' e NÃO sobem (a conta GHL tem 8.500+ pedidos
// de outros produtos — GHL_SOURCE_IDS filtra o funil ZOAC, e o unmatched segura
// o resto que escapar).

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      run(env, {})
        .then(r => console.log('purchase-check:', JSON.stringify(r)))
        .catch(err => console.error('purchase-check FAILED:', err.message))
    );
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    const key = request.headers.get('x-cron-key') || url.searchParams.get('key') || '';
    const bearer = (request.headers.get('authorization') || '').replace(/^Bearer\s+/i, '');
    if (!env.CRON_SECRET || (key !== env.CRON_SECRET && bearer !== env.CRON_SECRET)) {
      return json({ error: 'unauthorized' }, 401);
    }
    const opts = {
      dryRun: url.searchParams.get('dry_run') === '1',
      lookbackHours: parseInt(url.searchParams.get('lookback') || '', 10) || null,
      verbose: url.searchParams.get('verbose') === '1',
    };
    try {
      return json(await run(env, opts));
    } catch (err) {
      return json({ error: err.message }, 500);
    }
  },
};

async function run(env, opts) {
  const lookback = opts.lookbackHours || parseInt(env.LOOKBACK_HOURS || '24', 10);
  const maxSends = parseInt(env.MAX_SENDS_PER_RUN || '50', 10);
  const maxProcess = parseInt(env.MAX_PROCESS_PER_RUN || '15', 10);
  const summary = {
    dry_run: !!opts.dryRun, lookback_hours: lookback,
    ghl_rows: 0, already_sent: 0, processed: 0, sent: 0, unmatched: 0, errors: 0,
    details: [],
  };

  const sales = await fetchPaidSales(env, lookback);
  summary.ghl_rows = sales.length;
  if (!sales.length) return summary;

  const ledger = await loadLedger(env, sales.map(s => s.sale_id));
  let sends = 0;

  for (const sale of sales) {
    const prev = ledger.get(sale.sale_id);
    if (prev && prev.send_status === 'sent') { summary.already_sent++; continue; }
    if (prev && prev.send_status === 'unmatched') {
      const age = hoursSince(prev.created_at);
      const sinceRetry = hoursSince(prev.updated_at || prev.created_at);
      if (age > 48 || sinceRetry < 2) { summary.unmatched++; continue; }
    }
    if (sends >= maxSends || summary.processed >= maxProcess) { summary.truncated = true; break; }
    summary.processed++;

    try {
      // O sck vem do contato, não do pedido — só busca pra venda ainda não resolvida.
      await enrichSale(env, sale);

      const match = await matchSale(env, sale);
      const detail = {
        sale_id: sale.sale_id, match: match.type, value: centsToValue(sale.offer_price),
        currency: sale.currency, sck: sale.sck || '', email: maskEmail(sale.customer_email),
      };

      if (match.type === 'none') {
        summary.unmatched++;
        if (!opts.dryRun) await upsertLedger(env, sale, match, prev, { send_status: 'unmatched' });
        if (opts.verbose) summary.details.push(detail);
        continue;
      }

      const config = await env.CRO_DB.prepare(
        'SELECT brand, meta_pixel_id, event_map FROM domain_config WHERE domain = ? AND active = 1'
      ).bind(match.domain).first();

      if (!config) {
        summary.errors++;
        if (!opts.dryRun) await upsertLedger(env, sale, match, prev, { send_status: 'error', meta_response: `domain not in domain_config: ${match.domain}` });
        summary.details.push({ ...detail, error: `domain not configured: ${match.domain}` });
        continue;
      }

      detail.brand = config.brand;
      detail.pixel = config.meta_pixel_id;

      if (opts.dryRun) {
        detail.would_send = true;
        detail.has_fbp = !!match.fbp; detail.has_fbc = !!match.fbc;
        summary.sent++;
        summary.details.push(detail);
        continue;
      }

      const meta = await sendPurchase(env, config, sale, match);
      sends++;
      const ok = meta.status === 200;
      if (ok) summary.sent++; else summary.errors++;

      await upsertLedger(env, sale, match, prev, {
        send_status: ok ? 'sent' : 'error',
        meta_pixel_id: config.meta_pixel_id,
        meta_status_code: meta.status,
        meta_response_ok: ok ? 1 : 0,
        meta_response: (meta.body || '').slice(0, 500),
        brand: config.brand,
      });
      if (ok) await logDataTracker(env, config, sale, match, meta);

      detail.meta_status = meta.status;
      summary.details.push(detail);
    } catch (err) {
      summary.errors++;
      summary.details.push({ sale_id: sale.sale_id, error: err.message });
      try {
        if (!opts.dryRun) await upsertLedger(env, sale, { type: 'none' }, prev, { send_status: 'error', meta_response: `exception: ${err.message}`.slice(0, 500) });
      } catch { /* ledger é best-effort no caminho de erro */ }
    }
  }

  return summary;
}

// ---------- GHL Payments API (o adapter) ----------

const GHL_BASE = 'https://services.leadconnectorhq.com';

function ghlHeaders(env) {
  return {
    Authorization: `Bearer ${env.GHL_API_TOKEN}`,
    Version: '2021-07-28',
    'Content-Type': 'application/json',
  };
}

async function fetchPaidSales(env, lookbackHours) {
  const cutoff = Date.now() - Math.max(1, lookbackHours) * 3600000;
  // Funis deste projeto (CSV de sourceId). A location tem 8.500+ pedidos de
  // outros produtos; sem o filtro, o run inteiro seria consumido por venda alheia.
  const sourceIds = new Set(String(env.GHL_SOURCE_IDS || '').split(',').map(s => s.trim()).filter(Boolean));

  const sales = [];
  let offset = 0;
  let lastFirstId = '';
  for (let page = 0; page < 5; page++) {
    const qs = new URLSearchParams({
      altId: env.GHL_LOCATION_ID, altType: 'location', limit: '100', offset: String(offset),
    });
    const res = await fetch(`${GHL_BASE}/payments/orders?${qs}`, { headers: ghlHeaders(env) });
    if (!res.ok) throw new Error(`GHL orders ${res.status}: ${(await res.text()).slice(0, 300)}`);
    const payload = await res.json();
    const rows = payload.data || [];
    if (!rows.length) break;
    // Se a API ignorar `offset`, a página repete — detecta e para em vez de loopar.
    if (rows[0]._id === lastFirstId) break;
    lastFirstId = rows[0]._id;

    let pastCutoff = false;
    for (const o of rows) {
      const createdMs = Date.parse(o.createdAt || '');
      if (Number.isNaN(createdMs) || createdMs < cutoff) { pastCutoff = true; continue; }
      if (o.liveMode !== true) continue;
      const paid = o.paymentStatus === 'paid' || o.status === 'completed';
      if (!paid) continue;
      if (sourceIds.size && !sourceIds.has(String(o.sourceId || ''))) continue;
      if (!(Number(o.amount) > 0)) continue;

      sales.push({
        sale_id: String(o._id),
        platform: 'ghl',
        date_create: o.createdAt, date_update: o.updatedAt || o.createdAt,
        status: 'paid', payment_method: str(o.sourceSubType || o.sourceType),
        product_id: str(o.sourceId), product_name: str(o.sourceName || 'ZOAC'),
        offer_id: '', offer_name: '',
        // Contrato interno é CENTAVOS; o GHL manda unidades da moeda (US$1 = 1).
        offer_price: Math.round(Number(o.amount) * 100),
        currency: str(o.currency || 'USD').toUpperCase(),
        customer_email: str(o.contactEmail).toLowerCase(),
        customer_name: str(o.contactName),
        customer_phone: '',
        contact_id: str(o.contactId),
        sck: '', src: '',
        zipcode: '', city: '', state: '', country: '',
        utm_source: '', utm_medium: '', utm_campaign: '', utm_content: '', utm_term: '',
      });
    }
    if (pastCutoff || rows.length < 100) break;
    offset += rows.length;
  }
  // Novas primeiro (a API já devolve desc, mas o contrato não promete).
  sales.sort((a, b) => String(b.date_update).localeCompare(String(a.date_update)));
  return sales;
}

// O pedido do GHL não carrega o _sid; o CONTATO carrega (attributionSource.url,
// gravada pelo order form que preserva a query string). Daqui também saem
// telefone, país e cidade/CEP quando existirem — direto pro EMQ, nada é gravado.
async function enrichSale(env, sale) {
  if (!sale.contact_id) return;
  const res = await fetch(`${GHL_BASE}/contacts/${sale.contact_id}`, { headers: ghlHeaders(env) });
  if (!res.ok) return; // enriquecimento é best-effort; o unmatched segura o resto
  const c = (await res.json()).contact || {};

  const attr = c.lastAttributionSource || c.attributionSource || {};
  const urls = [attr.url, (c.attributionSource || {}).url];
  for (const u of urls) {
    const sid = extractSid(u);
    if (sid) { sale.sck = sid; break; }
  }

  if (!sale.customer_email && c.email) sale.customer_email = String(c.email).toLowerCase();
  if (!sale.customer_name) sale.customer_name = [c.firstName, c.lastName].filter(Boolean).join(' ');
  if (c.phone) sale.customer_phone = String(c.phone);
  if (c.country) sale.country = String(c.country);
  if (c.city) sale.city = String(c.city);
  if (c.state) sale.state = String(c.state);
  if (c.postalCode) sale.zipcode = String(c.postalCode);
  // IP e user-agent REAIS do comprador, gravados pelo GHL na atribuição. Servem
  // de reserva quando a sessão do D1 não tiver (ex.: match por lead).
  sale.attr_ip = str(attr.ip);
  sale.attr_ua = str(attr.userAgent);
}

function extractSid(rawUrl) {
  if (!rawUrl) return '';
  try {
    const sid = new URL(rawUrl).searchParams.get('_sid') || '';
    return isUuid(sid) ? sid : '';
  } catch { return ''; }
}

function isUuid(v) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(v));
}

// ---------- Ledger (dedup + paridade) ----------

async function loadLedger(env, saleIds) {
  const map = new Map();
  for (let i = 0; i < saleIds.length; i += 50) {
    const chunk = saleIds.slice(i, i + 50);
    const placeholders = chunk.map(() => '?').join(',');
    const { results } = await env.CRO_DB.prepare(
      `SELECT sale_id, send_status, created_at, updated_at, attempts FROM purchases_sent WHERE sale_id IN (${placeholders})`
    ).bind(...chunk).all();
    for (const r of results || []) map.set(r.sale_id, r);
  }
  return map;
}

async function upsertLedger(env, sale, match, prev, extra) {
  const value = centsToValue(sale.offer_price);
  await env.CRO_DB.prepare(`
    INSERT INTO purchases_sent (sale_id, brand, domain, session_id, lead_id, match_type, send_status, attempts,
      value, currency, offer_price, product_id, product_name, payment_method, customer_email, sck, src,
      utm_source, utm_campaign, transaction_date, paid_date, meta_pixel_id, meta_status_code, meta_response_ok, meta_response)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(sale_id) DO UPDATE SET
      brand = excluded.brand, domain = excluded.domain, session_id = excluded.session_id,
      lead_id = excluded.lead_id, match_type = excluded.match_type, send_status = excluded.send_status,
      attempts = purchases_sent.attempts + 1,
      meta_pixel_id = excluded.meta_pixel_id, meta_status_code = excluded.meta_status_code,
      meta_response_ok = excluded.meta_response_ok, meta_response = excluded.meta_response,
      updated_at = datetime('now')
  `).bind(
    sale.sale_id, extra.brand || match.brand || null, match.domain || null, match.sessionId || null,
    match.leadId || null, match.type || 'none', extra.send_status,
    value, str(sale.currency || 'USD'), toInt(sale.offer_price), str(sale.product_id), str(sale.product_name), str(sale.payment_method),
    str(sale.customer_email).toLowerCase(), str(sale.sck), str(sale.src),
    str(sale.utm_source), str(sale.utm_campaign), str(sale.date_create), str(sale.date_update),
    extra.meta_pixel_id || null, extra.meta_status_code ?? null, extra.meta_response_ok ?? 0, extra.meta_response || null
  ).run();
}

// ---------- Match venda -> sessão/lead ----------

async function matchSale(env, sale) {
  const sck = str(sale.sck).trim();
  if (sck) {
    const { results } = await env.CRO_DB.prepare(
      'SELECT * FROM data_tracker WHERE session_id = ? ORDER BY id ASC LIMIT 10'
    ).bind(sck).all();
    if (results && results.length) {
      const merged = mergeSessionRows(results);
      return { type: 'sck', sessionId: sck, leadId: merged.lead_id || null, domain: merged.domain, ...merged };
    }
  }

  const email = str(sale.customer_email).toLowerCase().trim();
  if (email) {
    const lead = await env.CRO_DB.prepare(
      'SELECT * FROM quizzes WHERE email = ? ORDER BY created_at DESC LIMIT 1'
    ).bind(email).first();
    if (lead) return leadMatch('lead_email', lead);
  }

  const phoneDigits = str(sale.customer_phone).replace(/\D/g, '');
  if (phoneDigits.length >= 8) {
    const suffix = phoneDigits.slice(-8);
    const lead = await env.CRO_DB.prepare(
      "SELECT * FROM quizzes WHERE phone != '' AND phone LIKE '%' || ? ORDER BY created_at DESC LIMIT 1"
    ).bind(suffix).first();
    if (lead) return leadMatch('lead_phone', lead);
  }

  return { type: 'none' };
}

function leadMatch(type, lead) {
  return {
    type, leadId: lead.id, sessionId: null, domain: lead.domain,
    fbp: str(lead.fbp), fbc: str(lead.fbc), fbclid: str(lead.fbclid),
    ip_address: str(lead.ip_address), user_agent: str(lead.user_agent),
    landing_url: str(lead.landing_url), external_id: '',
    lead_name: str(lead.name), lead_email: str(lead.email), lead_phone: str(lead.phone),
    utm_source: str(lead.utm_source), utm_medium: str(lead.utm_medium), utm_campaign: str(lead.utm_campaign),
    utm_content: str(lead.utm_content), utm_term: str(lead.utm_term),
  };
}

function mergeSessionRows(rows) {
  const first = rows[0];
  const pick = (field) => { for (const r of rows) { if (r[field]) return r[field]; } return ''; };
  return {
    domain: first.domain, lead_id: pick('lead_id') || null,
    fbp: pick('fbp'), fbc: pick('fbc'), fbclid: pick('fbclid'),
    ip_address: pick('ip_address'), user_agent: pick('user_agent'),
    landing_url: pick('landing_url') || pick('event_source_url'), external_id: pick('external_id'),
    lead_name: '', lead_email: pick('raw_email'), lead_phone: '',
    utm_source: pick('utm_source'), utm_medium: pick('utm_medium'), utm_campaign: pick('utm_campaign'),
    utm_content: pick('utm_content'), utm_term: pick('utm_term'),
  };
}

// ---------- Meta CAPI ----------

async function sendPurchase(env, config, sale, match) {
  const token = env[`META_TOKEN_${config.brand.toUpperCase()}`] || env.META_TOKEN;
  if (!token) return { status: 0, body: `skipped: no META token for brand ${config.brand}` };

  const eventTime = clampEventTime(parseIsoDate(sale.date_update) || parseIsoDate(sale.date_create));

  const userData = {};
  const email = str(sale.customer_email).toLowerCase().trim() || str(match.lead_email).toLowerCase().trim();
  const phone = normalizePhone(str(sale.customer_phone) || str(match.lead_phone), env.DEFAULT_COUNTRY_CODE);
  const { fn, ln } = splitName(str(sale.customer_name) || str(match.lead_name));

  if (email) userData.em = [await sha256(email)];
  if (phone) userData.ph = [await sha256(phone)];
  if (fn) userData.fn = [await sha256(fn)];
  if (ln) userData.ln = [await sha256(ln)];
  if (match.external_id) userData.external_id = [await sha256(match.external_id)];

  // Endereço: o que o contato do GHL tiver. Nada é gravado no nosso banco:
  // hash, envia, descarta.
  const zip = str(sale.zipcode).replace(/[^0-9a-z]/gi, '');
  const city = normalizeLocal(sale.city);
  const state = normalizeLocal(sale.state);
  // País do CONTATO (público da ZOAC é LatAm inteira). Sem default 'br' — chutar
  // país erra em metade da base.
  const country = normalizeLocal(sale.country);

  if (zip) userData.zp = [await sha256(zip.toLowerCase())];
  if (city) userData.ct = [await sha256(city)];
  if (state) userData.st = [await sha256(state)];
  if (country) userData.country = [await sha256(country)];

  // Gênero: SÓ inferência segura (listas + sufixo). SEM fallback — público misto.
  const genero = inferGenero(fn ? str(sale.customer_name) : '');
  if (genero) userData.ge = [await sha256(genero)];

  const fbp = validateFbCookie(match.fbp);
  let fbc = validateFbCookie(match.fbc);
  if (!fbc && match.fbclid) fbc = `fb.1.${eventTime * 1000}.${match.fbclid}`;
  if (fbp) userData.fbp = fbp;
  if (fbc) userData.fbc = fbc;
  const ip = match.ip_address || sale.attr_ip || '';
  const ua = match.user_agent || sale.attr_ua || '';
  if (ip) userData.client_ip_address = ip;
  if (ua) userData.client_user_agent = ua;

  const payload = {
    data: [{
      event_name: mapEventName('Purchase', config.event_map),
      event_time: eventTime,
      event_id: sale.sale_id,
      event_source_url: match.landing_url || '',
      action_source: 'website',
      user_data: userData,
      custom_data: {
        value: centsToValue(sale.offer_price),
        currency: str(sale.currency || 'USD'),
        order_id: sale.sale_id,
        content_name: str(sale.product_name),
        content_ids: sale.product_id ? [String(sale.product_id)] : undefined,
      },
    }],
  };
  if (env.META_TEST_EVENT_CODE) payload.test_event_code = env.META_TEST_EVENT_CODE;

  const res = await fetch(`https://graph.facebook.com/v25.0/${config.meta_pixel_id}/events?access_token=${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return { status: res.status, body: await res.text() };
}

async function logDataTracker(env, config, sale, match, meta) {
  try {
    await env.CRO_DB.prepare(`
      INSERT OR IGNORE INTO data_tracker (session_id, lead_id, brand, product, domain, event_name, event_id,
        event_source_url, fbclid, fbp, fbc, utm_source, utm_medium, utm_campaign, utm_content, utm_term,
        ip_address, user_agent, landing_url, external_id, value, currency, transaction_id,
        meta_status_code, meta_response_ok, is_bot, consent_status, has_email, has_phone, has_name, raw_email)
      VALUES (?, ?, ?, ?, ?, 'Purchase', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'unknown', ?, ?, ?, ?)
    `).bind(
      match.sessionId || '', match.leadId || null, config.brand, str(sale.product_name), match.domain,
      sale.sale_id, match.landing_url || '', str(match.fbclid), str(match.fbp), str(match.fbc),
      str(sale.utm_source) || match.utm_source || '', str(sale.utm_medium) || match.utm_medium || '',
      str(sale.utm_campaign) || match.utm_campaign || '', str(sale.utm_content) || match.utm_content || '',
      str(sale.utm_term) || match.utm_term || '',
      str(match.ip_address || sale.attr_ip), str(match.user_agent || sale.attr_ua), match.landing_url || '', str(match.external_id),
      centsToValue(sale.offer_price), str(sale.currency || 'USD'), sale.sale_id,
      meta.status, meta.status === 200 ? 1 : 0,
      sale.customer_email ? 1 : 0, sale.customer_phone ? 1 : 0, sale.customer_name ? 1 : 0,
      str(sale.customer_email).toLowerCase()
    ).run();
  } catch (e) {
    console.error('data_tracker log error:', e.message);
  }
}

// ---------- Helpers ----------

async function sha256(value) {
  if (!value) return '';
  const encoded = new TextEncoder().encode(value.toLowerCase().trim());
  const buffer = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(buffer)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function normalizePhone(ph, countryCode) {
  if (!ph) return '';
  const cc = String(countryCode || '55');
  const digits = ph.replace(/\D/g, '').replace(/^0+/, '');
  if (!digits) return '';
  if (digits.startsWith(cc) && digits.length >= cc.length + 8 && digits.length <= cc.length + 11) return digits;
  if (digits.length >= 8 && digits.length <= 11) return cc + digits;
  return digits;
}

function normalizeLocal(value) {
  return str(value)
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z]/g, '');
}

const MASC_EM_A = new Set([
  'luca', 'juca', 'nicola', 'sacha', 'sasha', 'joshua', 'akira', 'costa', 'lima',
  'cosma', 'noa', 'dua',
  'ubirajara', 'ubiracema', 'guaracia', 'potira',
]);

const FEM_FORA_DA_REGRA = new Set([
  'beatriz', 'ester', 'esther', 'rute', 'ruth', 'raquel', 'rachel', 'isabel',
  'mabel', 'nicole', 'michele', 'michelle', 'adriane', 'eliane', 'simone',
  'ivone', 'ivete', 'elisabete', 'elizabete', 'doris', 'lais', 'thais', 'tais',
  'iris', 'ines', 'carmen', 'miriam', 'marilene', 'darlene', 'charlene',
  'jaqueline', 'jacqueline', 'evelyn', 'karen', 'kelen', 'lucielen', 'liz',
  'mercedes', 'lourdes', 'consuelo', 'agnes', 'solange', 'rosangela',
  'noeli', 'nadir', 'zenir', 'jandir', 'cleusa',
]);

// Gênero pelo primeiro nome, modo CONSERVADOR (diferente da Bluue): sem
// fallback. Público da ZOAC é misto; "não sei" custa um parâmetro, chute errado
// casa a venda com o público errado.
function inferGenero(nomeCompleto) {
  const primeiro = str(nomeCompleto)
    .trim()
    .split(/\s+/)[0]
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z]/g, '');

  if (primeiro.length < 3) return '';
  if (MASC_EM_A.has(primeiro)) return 'm';
  if (FEM_FORA_DA_REGRA.has(primeiro)) return 'f';
  if (primeiro.endsWith('a')) return 'f';
  return '';
}

function splitName(name) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return { fn: '', ln: '' };
  return { fn: parts[0].toLowerCase(), ln: parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '' };
}

function validateFbCookie(value) {
  if (!value) return '';
  const parts = value.split('.');
  if (parts.length < 4 || parts.length > 5) return '';
  if (parts[0] !== 'fb') return '';
  if (!/^\d+$/.test(parts[1])) return '';
  if (!/^\d+$/.test(parts[2])) return '';
  if (!parts[3]) return '';
  return value;
}

function parseIsoDate(value) {
  if (!value) return null;
  const ms = Date.parse(String(value).trim());
  return Number.isNaN(ms) ? null : Math.floor(ms / 1000);
}

function clampEventTime(ts) {
  const now = Math.floor(Date.now() / 1000);
  if (!ts) return now;
  const min = now - 6.5 * 24 * 3600;
  return Math.min(Math.max(ts, min), now);
}

export function mapEventName(eventName, eventMapJson) {
  if (!eventName || !eventMapJson) return eventName;
  try {
    const map = JSON.parse(eventMapJson);
    return map[eventName] || eventName;
  } catch {
    return eventName;
  }
}

function centsToValue(offerPrice) {
  const cents = toInt(offerPrice);
  return cents ? Math.round(cents) / 100 : 0;
}

function toInt(v) {
  const n = parseInt(v, 10);
  return Number.isNaN(n) ? 0 : n;
}

function str(v) {
  return v === null || v === undefined ? '' : String(v);
}

function maskEmail(email) {
  const e = str(email);
  const [user, dom] = e.split('@');
  if (!dom) return e ? '***' : '';
  return `${user.slice(0, 2)}***@${dom}`;
}

function hoursSince(sqliteUtc) {
  const ms = Date.parse(String(sqliteUtc).replace(' ', 'T') + 'Z');
  if (Number.isNaN(ms)) return 0;
  return (Date.now() - ms) / 3600000;
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj, null, 2), {
    status, headers: { 'Content-Type': 'application/json' },
  });
}
