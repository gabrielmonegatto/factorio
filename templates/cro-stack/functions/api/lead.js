// cro-stack :: captura de lead -> tabela `quizzes`
// GENÉRICO. `brand` é OBRIGATÓRIO (sem default de marca: o template não conhece cliente).

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
    const cookies = parseCookies(request.headers.get('Cookie') || '');
    const host = request.headers.get('host') || '';

    const fbp = cookies['_fbp'] || body.fbp || '';
    const fbc = cookies['_fbc'] || body.fbc || '';
    const fbclid = body.fbclid || cookies['_fbclid'] || '';
    const gclid = body.gclid || '';
    const ip = request.headers.get('cf-connecting-ip') || '';
    const ua = request.headers.get('user-agent') || '';
    const referrer = request.headers.get('referer') || '';
    const landingUrl = body.landing_url || '';

    // Marca resolvida pelo domínio (fonte de verdade), com `body.brand` só como fallback.
    const config = await env.CRO_DB.prepare(
      'SELECT brand FROM domain_config WHERE domain = ? AND active = 1'
    ).bind(host).first();

    const brand = config?.brand || body.brand || '';
    if (!brand) {
      return new Response(JSON.stringify({ error: 'domain not configured and no brand provided' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const product = body.product || '';
    const quizId = body.quiz_id || '';
    const name = body.name || '';
    const email = (body.email || '').toLowerCase().trim();
    const phone = (body.phone || '').replace(/\D/g, '');
    const answers = typeof body.answers === 'object' ? JSON.stringify(body.answers) : (body.answers || '{}');
    const consentStatus = body.consent_status || 'unknown';

    const result = await env.CRO_DB.prepare(`
      INSERT INTO quizzes (brand, product, domain, quiz_id, name, email, phone, answers,
        utm_source, utm_medium, utm_campaign, utm_content, utm_term,
        fbclid, gclid, fbp, fbc, ip_address, user_agent, referrer, landing_url, consent_status)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      brand, product, host, quizId, name, email, phone, answers,
      body.utm_source || '', body.utm_medium || '', body.utm_campaign || '',
      body.utm_content || '', body.utm_term || '',
      fbclid, gclid, fbp, fbc, ip, ua, referrer, landingUrl, consentStatus
    ).run();

    return new Response(JSON.stringify({ ok: true, lead_id: result.meta?.last_row_id }), {
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

function parseCookies(cookieHeader) {
  const cookies = {};
  cookieHeader.split(';').forEach(cookie => {
    const [name, ...rest] = cookie.trim().split('=');
    if (name) cookies[name.trim()] = rest.join('=');
  });
  return cookies;
}
