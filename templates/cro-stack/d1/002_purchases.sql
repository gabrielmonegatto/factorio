-- ============================================================
-- cro-stack :: migration 002: ledger de vendas (purchase-check)
-- 1 linha por transação paga avaliada.
--   - Dedup: sale_id PRIMARY KEY (nunca envia 2x; Meta dedup via event_id=sale_id)
--   - Auditoria de paridade: "vendas no gateway == Purchases enviados"
--   - Venda sem match fica 'unmatched' e NÃO é enviada ao pixel
--     (não poluir a medição com venda de funil legado/fora do escopo)
-- (equivale ao 004_purchases.sql do bluue)
-- ============================================================

CREATE TABLE IF NOT EXISTS purchases_sent (
    sale_id            TEXT PRIMARY KEY,          -- id da transação no gateway
    brand              TEXT,
    domain             TEXT,
    session_id         TEXT,                      -- sessão casada via session param (ex: sck)
    lead_id            INTEGER,                   -- quizzes.id (fallback email/telefone)
    match_type         TEXT NOT NULL,             -- 'session' | 'lead_email' | 'lead_phone' | 'none'
    send_status        TEXT NOT NULL,             -- 'sent' | 'unmatched' | 'error'
    attempts           INTEGER DEFAULT 1,
    value              REAL,
    currency           TEXT DEFAULT 'BRL',
    offer_price        INTEGER,                   -- centavos (original do gateway)
    product_id         TEXT,
    product_name       TEXT,
    payment_method     TEXT,
    customer_email     TEXT,
    sck                TEXT,                      -- valor cru do session param
    src                TEXT,
    utm_source         TEXT,
    utm_campaign       TEXT,
    transaction_date   TEXT,                      -- ISO UTC
    paid_date          TEXT,                      -- ISO UTC
    meta_pixel_id      TEXT,
    meta_status_code   INTEGER,
    meta_response_ok   INTEGER DEFAULT 0,
    meta_response      TEXT,
    created_at         TEXT DEFAULT (datetime('now')),
    updated_at         TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases_sent(send_status);
CREATE INDEX IF NOT EXISTS idx_purchases_brand ON purchases_sent(brand);
CREATE INDEX IF NOT EXISTS idx_purchases_paid ON purchases_sent(paid_date);
CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases_sent(customer_email);
