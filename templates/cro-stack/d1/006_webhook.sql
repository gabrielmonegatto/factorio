-- ============================================================
-- cro-stack :: migration 006: auditoria de webhook do gateway
-- Par do functions/api/webhook-venda.js (a "campainha").
-- ============================================================

-- Cada disparo de postback do gateway, cru, como chegou. NÃO é a fonte da
-- verdade de venda (essa é o ledger purchases_sent, alimentado pelo worker);
-- é o registro de "o gateway disse X às HH:MM" pra investigar divergência.
CREATE TABLE IF NOT EXISTS webhook_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  received_at TEXT NOT NULL DEFAULT (datetime('now')),
  source TEXT,             -- etiqueta livre (?source= na URL do postback)
  payload TEXT             -- corpo cru, teto de 32KB aplicado no receptor
);

CREATE INDEX IF NOT EXISTS idx_webhook_log_received ON webhook_log (received_at);
