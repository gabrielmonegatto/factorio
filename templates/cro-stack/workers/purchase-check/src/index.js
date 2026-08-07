// br4nds-purchase-check — o elo crítico do ciclo de atribuição.
// Cron 5min: Flow API (transacoes pagas) -> dedup (purchases_sent) -> match sck/lead no D1
// -> CAPI Purchase (event_id = sale_id) -> ledger + data_tracker.
// Vendas sem match (funil legado) são registradas como 'unmatched' e NÃO enviadas ao pixel.

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
    if (!env.CRON_SECRET || key !== env.CRON_SECRET) {
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
  // Cap por run: mantém a invocação dentro do limite de subrequests; o backlog drena em runs sucessivas (idempotente)
  const maxProcess = parseInt(env.MAX_PROCESS_PER_RUN || '15', 10);
  const summary = {
    dry_run: !!opts.dryRun, lookback_hours: lookback,
    flow_rows: 0, already_sent: 0, processed: 0, sent: 0, unmatched: 0, errors: 0,
    details: [],
  };

  const sales = await fetchPaidSales(env, lookback);
  summary.flow_rows = sales.length;
  if (!sales.length) return summary;

  // Estado no ledger: 'sent' pula; 'error' e 'unmatched' recentes re-tentam (lead pode chegar depois da venda)
  const ledger = await loadLedger(env, sales.map(s => s.sale_id));
  let sends = 0;

  for (const sale of sales) {
    const prev = ledger.get(sale.sale_id);
    if (prev && prev.send_status === 'sent') { summary.already_sent++; continue; }
    if (prev && prev.send_status === 'unmatched') {
      // Já desistiu (>48h) OU re-tentado há menos de 2h — não re-processa. Throttle evita
      // o backlog legado (~80/dia) consumir as vagas do run e afogar as vendas do funil novo.
      const age = hoursSince(prev.created_at);
      const sinceRetry = hoursSince(prev.updated_at || prev.created_at);
      if (age > 48 || sinceRetry < 2) { summary.already_sent += 0; summary.unmatched++; continue; }
    }
    if (sends >= maxSends || summary.processed >= maxProcess) { summary.truncated = true; break; }
    summary.processed++;

    try {
      const match = await matchSale(env, sale);
      const detail = {
        sale_id: sale.sale_id, match: match.type, value: centsToValue(sale.offer_price),
        sck: sale.sck || '', email: maskEmail(sale.customer_email),
      };

      if (match.type === 'none') {
        summary.unmatched++;
        if (!opts.dryRun) await upsertLedger(env, sale, match, prev, { send_status: 'unmatched' });
        if (opts.verbose) summary.details.push(detail);
        continue;
      }

      // Pixel/marca vêm do domínio da sessão/lead (domain_config = fonte da verdade)
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

// ---------- Flow API ----------

async function fetchPaidSales(env, lookbackHours) {
  // offer_price > 0: itens-bônus da venda pai (sale_id "kit-av-*"/"kit-bl-*") vêm com preço zero e não são Purchase
  // Banco é POSTGRES: intervalo é `INTERVAL '48 hours'`. Sintaxe MySQL (`INTERVAL 48 HOUR`, DATE_SUB) dá erro 400.
  // zipcode/city/state entram por causa da PARIDADE DE EMQ com o Stape: no pixel
  // `Test B` o evento `p` chega hoje com CEP, cidade, estado e país em 100% dos
  // envios, e é parte do 9,3/10 de qualidade. Sem eles a nota cai, o casamento
  // piora e o conjunto pode voltar pro aprendizado — sem ninguém ter tocado em
  // campanha. A B4You já devolvia esses campos; o worker é que os descartava.
  const sql = `SELECT sale_id, platform, date_create, date_update, status, payment_method,
      product_id, product_name, offer_id, offer_name, offer_price,
      customer_email, customer_name, customer_phone, sck, src,
      zipcode, city, state, country,
      utm_source, utm_medium, utm_campaign, utm_content, utm_term
    FROM transacoes
    WHERE status = 'paid' AND offer_price > 0 AND date_update >= NOW() - INTERVAL '${Math.max(1, lookbackHours)} hours'
    ORDER BY date_update DESC LIMIT 500`;
  // DESC: vendas NOVAS primeiro. Com ASC o backlog legado (~80 unmatched/dia < 48h)
  // enchia as 15 vagas/run e as vendas do funil novo (mais recentes) nunca eram alcançadas.

  const res = await fetch(env.FLOW_API_URL, {
    method: 'POST',
    headers: { 'x-api-token': env.FLOW_API_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: sql }),
  });
  if (!res.ok) throw new Error(`Flow API ${res.status}: ${(await res.text()).slice(0, 900)}`);
  // A Flow devolve CORPO VAZIO (não "[]") quando o resultado é pequeno/vazio — .json() num
  // vazio quebra com "Unexpected end of JSON input". Tratar como zero vendas.
  const text = await res.text();
  if (!text.trim()) return [];
  let payload;
  try { payload = JSON.parse(text); }
  catch (e) { throw new Error(`Flow API resposta inválida: ${text.slice(0, 200)}`); }
  // Resposta vem como [{"data":[...]}]
  const rows = Array.isArray(payload) ? (payload[0]?.data || []) : (payload?.data || []);
  return rows.filter(r => r && r.sale_id);
}

// ---------- Ledger (dedup + parity) ----------

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
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'BRL', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    value, toInt(sale.offer_price), str(sale.product_id), str(sale.product_name), str(sale.payment_method),
    str(sale.customer_email).toLowerCase(), str(sale.sck), str(sale.src),
    str(sale.utm_source), str(sale.utm_campaign), str(sale.date_create), str(sale.date_update),
    extra.meta_pixel_id || null, extra.meta_status_code ?? null, extra.meta_response_ok ?? 0, extra.meta_response || null
  ).run();
}

// ---------- Match venda -> sessão/lead ----------

async function matchSale(env, sale) {
  // 1) Determinístico: sck carrega o _bnd_sid da sessão
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

  // 2) Fallback: email/telefone contra leads do quiz
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

  const eventTime = clampEventTime(parseFlowDate(sale.date_update) || parseFlowDate(sale.date_create));

  const userData = {};
  const email = str(sale.customer_email).toLowerCase().trim() || str(match.lead_email).toLowerCase().trim();
  const phone = normalizePhone(str(sale.customer_phone) || str(match.lead_phone), env.DEFAULT_COUNTRY_CODE);
  const { fn, ln } = splitName(str(sale.customer_name) || str(match.lead_name));

  if (email) userData.em = [await sha256(email)];
  if (phone) userData.ph = [await sha256(phone)];
  if (fn) userData.fn = [await sha256(fn)];
  if (ln) userData.ln = [await sha256(ln)];
  if (match.external_id) userData.external_id = [await sha256(match.external_id)];

  // ENDEREÇO: paridade de EMQ com o Stape.
  //
  // No pixel `Test B`, o evento `p` chega hoje com CEP, cidade, estado e país em
  // 100% dos envios, e isso é parte da nota 9,3/10. Se o nosso CAPI assumir sem
  // esses campos, a qualidade cai, o casamento com usuário piora e o conjunto pode
  // cair abaixo do mínimo de conversões e voltar pro aprendizado — sem ninguém ter
  // editado campanha nenhuma. É o risco que a virada do bluue.io não pode correr.
  //
  // O dado sempre esteve na venda da B4You (conferido: zipcode/city/state em 3/3
  // das últimas vendas pagas). Quem descartava era este worker.
  //
  // NÃO GRAVAMOS nada disso no nosso banco: entra com hash, vai pra Meta e some.
  // Endereço de cliente é dado pessoal, e guardar o que não se usa é só risco.
  const zip = str(sale.zipcode).replace(/\D/g, '');
  const city = normalizeLocal(sale.city);
  const state = normalizeLocal(sale.state);
  // A B4You devolve `country` VAZIO (0/3 nas últimas vendas). Operação é só Brasil,
  // então cravamos 'br' em vez de mandar o campo em branco e perder o parâmetro.
  const country = normalizeLocal(sale.country) || 'br';

  if (zip) userData.zp = [await sha256(zip)];
  if (city) userData.ct = [await sha256(city)];
  if (state) userData.st = [await sha256(state)];
  if (country) userData.country = [await sha256(country)];

  // GÊNERO: último parâmetro que faltava pra igualar o Stape (100% no painel).
  //
  // ATENÇÃO, ISTO É INFERÊNCIA, NÃO DADO. A B4You não devolve gênero em campo
  // nenhum — conferido coluna por coluna. Os 100% do Stape só podem sair de
  // dedução pelo primeiro nome, e é o que fazemos aqui.
  //
  // Vale a pena porque o pixel foi treinado meses com esse parâmetro presente:
  // chegar sem ele muda o que a Meta está acostumada a receber, e o requisito da
  // virada é não mudar nada. Nome que a regra não reconhece fica DE FORA, em vez
  // de chutar: parâmetro errado é pior que parâmetro ausente, porque casa a venda
  // com o público errado.
  const genero = inferGenero(fn ? str(sale.customer_name) : '');
  if (genero) userData.ge = [await sha256(genero)];

  const fbp = validateFbCookie(match.fbp);
  let fbc = validateFbCookie(match.fbc);
  if (!fbc && match.fbclid) fbc = `fb.1.${eventTime * 1000}.${match.fbclid}`;
  if (fbp) userData.fbp = fbp;
  if (fbc) userData.fbc = fbc;
  if (match.ip_address) userData.client_ip_address = match.ip_address;
  if (match.user_agent) userData.client_user_agent = match.user_agent;

  const payload = {
    data: [{
      // Domínio que já roda tráfego tem adset otimizando num evento custom (ex.: "p",
      // herança do Stape). Traduz na saída; o ledger e o data_tracker seguem 'Purchase'.
      event_name: mapEventName('Purchase', config.event_map),
      event_time: eventTime,
      event_id: sale.sale_id,
      event_source_url: match.landing_url || '',
      action_source: 'website',
      user_data: userData,
      custom_data: {
        value: centsToValue(sale.offer_price),
        currency: 'BRL',
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
    // INSERT OR IGNORE: índice único (event_id, brand) protege contra duplicata
    await env.CRO_DB.prepare(`
      INSERT OR IGNORE INTO data_tracker (session_id, lead_id, brand, product, domain, event_name, event_id,
        event_source_url, fbclid, fbp, fbc, utm_source, utm_medium, utm_campaign, utm_content, utm_term,
        ip_address, user_agent, landing_url, external_id, value, currency, transaction_id,
        meta_status_code, meta_response_ok, is_bot, consent_status, has_email, has_phone, has_name, raw_email)
      VALUES (?, ?, ?, ?, ?, 'Purchase', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BRL', ?, ?, ?, 0, 'unknown', ?, ?, ?, ?)
    `).bind(
      match.sessionId || '', match.leadId || null, config.brand, str(sale.product_name), match.domain,
      sale.sale_id, match.landing_url || '', str(match.fbclid), str(match.fbp), str(match.fbc),
      str(sale.utm_source) || match.utm_source || '', str(sale.utm_medium) || match.utm_medium || '',
      str(sale.utm_campaign) || match.utm_campaign || '', str(sale.utm_content) || match.utm_content || '',
      str(sale.utm_term) || match.utm_term || '',
      str(match.ip_address), str(match.user_agent), match.landing_url || '', str(match.external_id),
      centsToValue(sale.offer_price), sale.sale_id,
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

// Normalização que a Meta exige para cidade, estado e país antes do hash:
// minúsculas, sem acento, sem espaço e sem pontuação. "São Paulo" e "sao paulo"
// TÊM que virar o mesmo hash, senão o casamento simplesmente não acontece e o
// parâmetro é enviado à toa.
function normalizeLocal(value) {
  return str(value)
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // marcas de acento por codigo: literal quebra ao editar arquivo
    .toLowerCase()
    .replace(/[^a-z]/g, '');
}

// Nomes masculinos terminados em -a. São a exceção que a regra do sufixo erraria,
// e erra sempre no mesmo sentido: marcaria homem como mulher.
// Nomes masculinos terminados em -a: a exceção que a regra do sufixo erraria, e
// erra sempre no mesmo sentido (marcaria homem como mulher).
//
// Os nomes tupi vieram de erro REAL: rodando a regra contra 400 clientes pagantes,
// os únicos 3 classificados como feminino eram todos "Ubirajara".
const MASC_EM_A = new Set([
  'luca', 'juca', 'nicola', 'sacha', 'sasha', 'joshua', 'akira', 'costa', 'lima',
  'cosma', 'noa', 'dua',
  // Tupi MASCULINOS terminados em -a. Só entram os masculinos: Iracema, Jandira,
  // Jurema e Moema também são tupi e também terminam em -a, mas são femininos —
  // a regra do sufixo já acerta neles, e colocá-los aqui os quebraria.
  'ubirajara', 'ubiracema', 'guaracia', 'potira',
]);

// Femininos que NÃO terminam em -a. Em português a maioria termina em -e
// (Simone, Adriane) ou é bíblico (Raquel, Ester, Rute).
const FEM_FORA_DA_REGRA = new Set([
  'beatriz', 'ester', 'esther', 'rute', 'ruth', 'raquel', 'rachel', 'isabel',
  'mabel', 'nicole', 'michele', 'michelle', 'adriane', 'eliane', 'simone',
  'ivone', 'ivete', 'elisabete', 'elizabete', 'doris', 'lais', 'thais', 'tais',
  'iris', 'ines', 'carmen', 'miriam', 'marilene', 'darlene', 'charlene',
  'jaqueline', 'jacqueline', 'evelyn', 'karen', 'kelen', 'lucielen', 'liz',
  'mercedes', 'lourdes', 'consuelo', 'esther', 'agnes', 'solange', 'rosangela',
  'noeli', 'nadir', 'zenir', 'jandir', 'cleusa',
]);

// Gênero a partir do primeiro nome, do jeito mais conservador possível:
// primeiro as exceções conhecidas, depois a regra do sufixo, e o que não encaixar
// volta vazio pra NÃO ser enviado. Um "não sei" custa um parâmetro; um chute
// errado casa a venda com o público errado e envenena a otimização.
function inferGenero(nomeCompleto) {
  const primeiro = str(nomeCompleto)
    .trim()
    .split(/\s+/)[0]
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z]/g, '');

  if (primeiro.length < 3) return '';

  // A ordem importa: exceção conhecida ganha da regra do sufixo, sempre.
  if (MASC_EM_A.has(primeiro)) return 'm';
  if (FEM_FORA_DA_REGRA.has(primeiro)) return 'f';
  if (primeiro.endsWith('a')) return 'f';

  // O QUE SOBRA VIRA MASCULINO, e isso é decisão de público, não de linguística.
  //
  // Medido em 400 clientes pagantes reais: 80,5% masculino, 0,8% feminino. É um
  // produto de performance masculina; mulher comprando é quase sempre presente.
  // A regra do sufixo sozinha deixava 18,8% sem inferir, e a inspeção desses 75
  // nomes mostrou TODOS masculinos (jose, luiz, andre, ian, david, jorge, wesley).
  //
  // Cair pra 'm' leva a cobertura a ~100% (que é o que o Stape entrega hoje) com
  // erro estimado abaixo de 1% neste público. A proteção contra o erro continua
  // sendo a ordem acima: quem termina em -a e quem está na lista feminina nunca
  // chega aqui.
  //
  // ⚠ Esta escolha é da BLUUE. Marca com público misto tem que rever isto antes
  // de reusar, ou vai marcar metade da base com o gênero errado.
  return 'm';
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

function parseFlowDate(value) {
  if (!value) return null;
  let s = String(value).trim();
  // Formatos: "2026-07-20T14:33:22.000Z" ou MySQL "2026-07-20 14:33:22" (UTC)
  if (s.includes(' ') && !s.includes('T')) s = s.replace(' ', 'T');
  if (!/Z|[+-]\d{2}:?\d{2}$/.test(s)) s += 'Z';
  const ms = Date.parse(s);
  return Number.isNaN(ms) ? null : Math.floor(ms / 1000);
}

function clampEventTime(ts) {
  const now = Math.floor(Date.now() / 1000);
  if (!ts) return now;
  const min = now - 6.5 * 24 * 3600; // CAPI aceita até 7 dias
  return Math.min(Math.max(ts, min), now);
}

// Espelho do nome do evento por domínio (domain_config.event_map).
// Mesma função do functions/api/tracker.js — se mudar aqui, mudar lá.
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
  // created_at vem de datetime('now') — UTC sem timezone
  const ms = Date.parse(String(sqliteUtc).replace(' ', 'T') + 'Z');
  if (Number.isNaN(ms)) return 0;
  return (Date.now() - ms) / 3600000;
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj, null, 2), {
    status, headers: { 'Content-Type': 'application/json' },
  });
}
