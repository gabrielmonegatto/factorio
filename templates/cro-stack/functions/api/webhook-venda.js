// Receptor de webhook/postback do gateway: a CAMPAINHA, não o processador.
//
// ARQUITETURA (decisão 07/08/2026): webhook dá velocidade, cron dá garantia.
// Webhook sozinho PERDE venda (endpoint fora do ar no segundo do disparo, retry
// esgotado = venda sumiu). Polling nunca perde, só atrasa. Então os dois convivem:
//
//   gateway --webhook--> este endpoint --"toca a campainha"--> worker purchase-check
//   gateway <--polling (cron 5min)----- worker purchase-check   (a vassoura)
//
// Este endpoint NÃO parseia a venda nem fala com a Meta. Ele só:
//   1. autentica o chamado (WEBHOOK_SECRET na query `?s=`)
//   2. guarda o payload cru no D1 (auditoria: o que o gateway disse, quando)
//   3. dispara UMA rodada imediata do worker (que busca no gateway, casa a sessão
//      e envia o Purchase — com o dedup do ledger `purchases_sent` já embutido)
//
// POR QUE ASSIM: se o receptor processasse a venda, a lógica de CAPI/EMQ/dedup
// existiria em DOIS lugares e divergiria na primeira manutenção. Como campainha,
// o caminho da venda continua ÚNICO (o worker), e o webhook só antecipa o relógio.
// Latência real: segundos em vez de até 5 min. Pra Meta tanto faz; pro nosso
// tempo real e pro upsell por timing, importa.
//
// SETUP
//   - Migration d1/006_webhook.sql (tabela webhook_log)
//   - Vars:    PURCHASE_WORKER_URL = https://<projeto>-purchase-check.<conta>.workers.dev
//   - Secrets: WEBHOOK_SECRET (gerar: openssl rand -hex 16) e o worker precisa
//              do CRON_SECRET dele (o mesmo usado no disparo manual)
//   - No painel do gateway, apontar o postback pra:
//              https://<dominio>/api/webhook-venda?s=<WEBHOOK_SECRET>
//
// ⚠️ Falha fechado: sem WEBHOOK_SECRET configurado o endpoint não existe (403).
// Endpoint de webhook aberto vira vetor de lixo no banco.

export async function onRequestPost(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  if (!env.WEBHOOK_SECRET) return resposta({ error: 'webhook desabilitado' }, 403);
  if (url.searchParams.get('s') !== env.WEBHOOK_SECRET) {
    return resposta({ error: 'unauthorized' }, 401);
  }

  // Payload cru, com teto: auditoria não pode virar porta de estouro de banco.
  let payload = '';
  try {
    payload = (await request.text()).slice(0, 32_000);
  } catch {
    payload = '';
  }

  try {
    await env.CRO_DB.prepare(
      'INSERT INTO webhook_log (source, payload) VALUES (?, ?)'
    ).bind(url.searchParams.get('source') || 'gateway', payload).run();
  } catch (err) {
    // Auditoria falhou, campainha continua: gravar o log não é pré-condição
    // pra processar a venda. O erro aparece na observability do Pages.
    console.log('webhook_log falhou:', err.message);
  }

  // Toca a campainha SEM segurar a resposta: gateway com timeout curto marca
  // webhook lento como falho e para de enviar.
  if (env.PURCHASE_WORKER_URL && env.CRON_SECRET) {
    context.waitUntil(
      fetch(env.PURCHASE_WORKER_URL, {
        method: 'POST',
        headers: { Authorization: `Bearer ${env.CRON_SECRET}` },
      }).catch((err) => console.log('campainha falhou (cron cobre):', err.message))
    );
  }

  // 200 sempre que autenticado: gateway que recebe erro reenvia ou desativa o
  // webhook. A vassoura (cron) é quem garante; aqui não se sinaliza falha interna.
  return resposta({ ok: true }, 200);
}

function resposta(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
