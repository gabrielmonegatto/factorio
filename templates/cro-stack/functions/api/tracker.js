// cro-stack :: coração do tracking client -> server
// Recebe o evento do browser, resolve pixel/GA4 via `domain_config`, dispara
// Meta CAPI + GA4 em paralelo, hasheia PII e registra tudo no D1.
// GENÉRICO: token por marca via `META_TOKEN_<BRAND>` (fallback `META_TOKEN`).

export async function onRequestPost(context) {
  const { request, env } = context;

  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await request.json();
    const clientIp = request.headers.get('cf-connecting-ip') || '';
    const userAgent = request.headers.get('user-agent') || '';
    const cookies = parseCookies(request.headers.get('Cookie') || '');
    const host = request.headers.get('host') || '';

    const userData = body.user_data || {};
    const sessionId = cookies['_bnd_sid'] || body.session_id || '';
    const externalId = cookies['_bnd_eid'] || userData.external_id || '';

    const config = await env.CRO_DB.prepare(
      'SELECT brand, meta_pixel_id, ga4_id FROM domain_config WHERE domain = ? AND active = 1'
    ).bind(host).first();

    if (!config) {
      return new Response(JSON.stringify({ error: 'domain not configured' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const sessionData = sessionId ? await env.CRO_DB.prepare(
      'SELECT * FROM data_tracker WHERE session_id = ? LIMIT 1'
    ).bind(sessionId).first() : {};

    const fbp = validateFbCookie(userData.fbp) || validateFbCookie(cookies['_fbp']) || '';
    const fbc = validateFbCookie(cookies['_fbc']) || validateFbCookie(userData.fbc) || '';
    const fbclid = getFrom(sessionData, 'fbclid') || getRawParamFromUrl(body.event_source_url, 'fbclid') || '';
    const gclid = getFrom(sessionData, 'gclid') || '';

    const pixelWasBlocked = (!userData.fbp && !userData.fbc) ? 1 : 0;

    // O snippet SEMPRE manda event_id (mesmo valor usado no fbq do browser) pra
    // Meta deduplicar pixel x CAPI. O fallback só cobre chamada malformada.
    const eventId = body.event_id || `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    async function sha256(value) {
      if (!value) return '';
      const normalized = value.toLowerCase().trim();
      const encoded = new TextEncoder().encode(normalized);
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

    const hashedEm = await sha256(userData.em);
    const hashedFn = await sha256(userData.fn?.trim().toLowerCase() || '');
    const hashedLn = await sha256(userData.ln?.trim().toLowerCase() || '');
    const hashedPh = await sha256(normalizePhone(userData.ph, env.DEFAULT_COUNTRY_CODE));
    const hashedExternalId = await sha256(externalId);

    const { isBot, botReason } = detectBot(userAgent);

    let leadId = null;
    if (body.event_name === 'Lead' && userData.em) {
      const existing = await env.CRO_DB.prepare(
        'SELECT id FROM quizzes WHERE email = ? AND brand = ? ORDER BY created_at DESC LIMIT 1'
      ).bind(userData.em, config.brand).first();
      if (existing) leadId = existing.id;
    }

    const results = isBot ? [] : await Promise.allSettled([
      sendToMeta({ env, config, body, clientIp, userAgent, fbp, fbc, hashedEm, hashedFn, hashedLn, hashedPh, hashedExternalId, sessionData, eventId }),
      sendToGA4({ env, config, body, hashedEm, eventId }),
    ]);

    let metaStatusCode = 0, metaResponseOk = 0, metaResponseBody = '';
    if (results[0]?.status === 'fulfilled' && results[0].value) {
      const v = results[0].value;
      if (v.skipped) {
        metaResponseBody = `skipped: ${v.skipped}`;
      } else if (v.response) {
        metaStatusCode = v.response.status;
        metaResponseOk = v.response.ok ? 1 : 0;
        try { metaResponseBody = await v.response.text(); } catch (e) { metaResponseBody = `Read error: ${e.message}`; }
      }
    } else if (results[0]?.status === 'rejected') {
      metaResponseBody = `Fetch error: ${results[0].reason?.message || 'unknown'}`;
    }

    let ga4StatusCode = 0, ga4ResponseOk = 0, ga4ResponseBody = '';
    if (results[1]?.status === 'fulfilled' && results[1].value) {
      const v = results[1].value;
      if (v.skipped) {
        ga4ResponseBody = `skipped: ${v.skipped}`;
      } else if (v.response) {
        ga4StatusCode = v.response.status;
        ga4ResponseOk = v.response.ok ? 1 : 0;
        try { ga4ResponseBody = await v.response.text(); } catch (e) { ga4ResponseBody = `Read error: ${e.message}`; }
      }
    } else if (results[1]?.status === 'rejected') {
      ga4ResponseBody = `Fetch error: ${results[1].reason?.message || 'unknown'}`;
    }

    context.waitUntil((async () => {
      try {
        const utms = body.utm || {};
        await env.CRO_DB.prepare(`
          INSERT INTO data_tracker (session_id, lead_id, brand, product, domain, event_name, event_id, event_source_url, fbclid, gclid, fbp, fbc, utm_source, utm_medium, utm_campaign, utm_content, utm_term, ip_address, user_agent, referrer, landing_url, external_id, value, currency, transaction_id, meta_status_code, meta_response_ok, meta_response, ga4_status_code, ga4_response_ok, ga4_response, is_bot, bot_reason, consent_status, has_email, has_phone, has_name, pixel_was_blocked, raw_email)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          sessionId, leadId, config.brand, body.product || '', host, body.event_name, eventId, body.event_source_url || '',
          fbclid, gclid, fbp, fbc,
          utms.utm_source || '', utms.utm_medium || '', utms.utm_campaign || '', utms.utm_content || '', utms.utm_term || '',
          clientIp, userAgent, request.headers.get('referer') || '', body.event_source_url || '', externalId,
          body.value || null, body.currency || null, body.transaction_id || null,
          metaStatusCode, metaResponseOk, metaResponseBody.slice(0, 800),
          ga4StatusCode, ga4ResponseOk, ga4ResponseBody.slice(0, 400),
          isBot ? 1 : 0, botReason, body.consent_status || 'unknown',
          hashedEm ? 1 : 0, hashedPh ? 1 : 0, (hashedFn || hashedLn) ? 1 : 0,
          pixelWasBlocked, userData.em || ''
        ).run();
      } catch (e) {
        console.error('[cro] D1 log error:', e.message);
      }
    })());

    return new Response(JSON.stringify({ ok: true, event_id: eventId }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
    });
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}

async function sendToMeta({ env, config, body, clientIp, userAgent, fbp, fbc, hashedEm, hashedFn, hashedLn, hashedPh, hashedExternalId, sessionData, eventId }) {
  const metaToken = env[`META_TOKEN_${config.brand.toUpperCase()}`] || env.META_TOKEN;
  if (!config.meta_pixel_id || !metaToken) {
    return { skipped: 'missing meta config', payload: null, response: null };
  }

  const metaUserData = { client_ip_address: clientIp, client_user_agent: userAgent };
  if (hashedEm) metaUserData.em = [hashedEm];
  if (hashedFn) metaUserData.fn = [hashedFn];
  if (hashedLn) metaUserData.ln = [hashedLn];
  if (hashedPh) metaUserData.ph = [hashedPh];
  if (hashedExternalId) metaUserData.external_id = [hashedExternalId];
  if (fbp) metaUserData.fbp = fbp;
  if (fbc) metaUserData.fbc = fbc;

  const payload = {
    data: [{
      event_name: body.event_name,
      event_time: body.event_time || Math.floor(Date.now() / 1000),
      event_id: eventId,
      event_source_url: body.event_source_url || '',
      action_source: 'website',
      user_data: metaUserData,
    }],
  };

  if (body.value) payload.data[0].custom_data = { value: body.value, currency: body.currency || 'BRL' };

  if (env.META_TEST_EVENT_CODE) payload.test_event_code = env.META_TEST_EVENT_CODE;

  const response = await fetch(`https://graph.facebook.com/v25.0/${config.meta_pixel_id}/events?access_token=${metaToken}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return { payload: JSON.stringify(payload), response };
}

async function sendToGA4({ env, config, body, hashedEm, eventId }) {
  const ga4Secret = env[`GA4_SECRET_${config.brand.toUpperCase()}`] || env.GA4_API_SECRET;
  if (!config.ga4_id || !ga4Secret) {
    return { skipped: 'missing ga4 config', payload: null, response: null };
  }

  const eventName = (body.event_name || '').toLowerCase();
  if (eventName === 'pageview' || eventName === 'page_view') {
    return { skipped: 'pageview', payload: null, response: null };
  }

  const ga4EventName = eventName === 'lead' ? 'generate_lead'
    : eventName === 'purchase' ? 'purchase'
    : eventName === 'initiatecheckout' ? 'begin_checkout'
    : eventName;

  const payload = {
    client_id: body.ga_client_id || eventId,
    events: [{
      name: ga4EventName,
      params: {
        session_id: body.ga_session_id || '',
        engagement_time_msec: 100,
        page_location: body.event_source_url || '',
        value: body.value,
        currency: body.currency,
        transaction_id: body.transaction_id,
      },
    }],
  };

  if (hashedEm) payload.user_properties = { email: { value: hashedEm } };

  const response = await fetch(`https://www.google-analytics.com/mp/collect?measurement_id=${config.ga4_id}&api_secret=${ga4Secret}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return { payload: JSON.stringify(payload), response };
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

function parseCookies(cookieHeader) {
  const cookies = {};
  cookieHeader.split(';').forEach(cookie => {
    const [name, ...rest] = cookie.trim().split('=');
    if (name) cookies[name.trim()] = rest.join('=');
  });
  return cookies;
}

function getFrom(obj, key) {
  return (obj && obj[key]) || '';
}

function getRawParamFromUrl(urlString, name) {
  if (!urlString) return '';
  try {
    const url = new URL(urlString);
    const match = url.search.match(new RegExp('[?&]' + name + '=([^&]*)'));
    return match ? match[1] : '';
  } catch { return ''; }
}

function detectBot(userAgent) {
  if (!userAgent || userAgent.length < 10) return { isBot: true, botReason: 'Missing or short user-agent' };
  const patterns = [
    { p: /googlebot|google-inspectiontool/i, r: 'Googlebot' },
    { p: /facebookexternalhit|facebot|meta-externalads/i, r: 'Facebook crawler' },
    { p: /whatsapp/i, r: 'WhatsApp preview' },
    { p: /slackbot/i, r: 'Slackbot' },
    { p: /bot|crawler|spider|scraper|headless/i, r: 'Generic bot' },
    { p: /python-requests|axios|node-fetch|curl|wget|httpie/i, r: 'HTTP library' },
  ];
  for (const { p, r } of patterns) {
    if (p.test(userAgent)) return { isBot: true, botReason: r };
  }
  return { isBot: false, botReason: '' };
}
