-- ============================================================
-- cro-stack :: migration 001: núcleo do tracking
-- Cria: domain_config · quizzes · data_tracker
-- (equivale ao 001_init.sql do bluue, sem os IDs do cliente)
-- ============================================================

-- Tabela: domain_config
-- Fonte única da verdade: domain -> brand + Pixel ID
-- ADICIONAR MARCA/DOMÍNIO NOVO = 1 INSERT, ZERO DEPLOY.
CREATE TABLE IF NOT EXISTS domain_config (
    domain        TEXT PRIMARY KEY,
    brand         TEXT NOT NULL,
    meta_pixel_id TEXT NOT NULL,
    ga4_id        TEXT,
    active        INTEGER DEFAULT 1,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_domain_brand ON domain_config(brand);

-- Tabela: quizzes
-- Leads capturados (quiz/formulário) + respostas em JSON.
CREATE TABLE IF NOT EXISTS quizzes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    brand       TEXT NOT NULL,
    product     TEXT NOT NULL,
    domain      TEXT NOT NULL,
    quiz_id     TEXT NOT NULL,
    name        TEXT,
    email       TEXT,
    phone       TEXT,
    answers     TEXT NOT NULL DEFAULT '{}',
    utm_source   TEXT,
    utm_medium   TEXT,
    utm_campaign TEXT,
    utm_content  TEXT,
    utm_term     TEXT,
    fbclid      TEXT,
    gclid       TEXT,
    fbp         TEXT,
    fbc         TEXT,
    ip_address  TEXT,
    user_agent  TEXT,
    referrer    TEXT,
    landing_url TEXT,
    consent_status TEXT DEFAULT 'unknown',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_quizzes_brand ON quizzes(brand);
CREATE INDEX IF NOT EXISTS idx_quizzes_product ON quizzes(product);
CREATE INDEX IF NOT EXISTS idx_quizzes_domain ON quizzes(domain);
CREATE INDEX IF NOT EXISTS idx_quizzes_brand_product ON quizzes(brand, product);
CREATE INDEX IF NOT EXISTS idx_quizzes_created ON quizzes(created_at);

-- Tabela: data_tracker
-- Cada linha = um evento server-side (PageView, Lead, InitiateCheckout, Purchase).
CREATE TABLE IF NOT EXISTS data_tracker (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL,
    lead_id           INTEGER,               -- FK -> quizzes.id
    brand             TEXT NOT NULL,
    product           TEXT NOT NULL,
    domain            TEXT NOT NULL,
    event_name        TEXT NOT NULL,
    event_id          TEXT,                  -- dedup com pixel client-side
    event_source_url  TEXT,
    fbclid            TEXT,
    gclid             TEXT,
    fbp               TEXT,
    fbc               TEXT,
    utm_source        TEXT,
    utm_medium        TEXT,
    utm_campaign      TEXT,
    utm_content       TEXT,
    utm_term          TEXT,
    ip_address        TEXT,
    user_agent        TEXT,
    referrer          TEXT,
    landing_url       TEXT,
    external_id       TEXT,
    value             REAL,
    currency          TEXT,
    transaction_id    TEXT,
    meta_status_code  INTEGER,
    meta_response_ok  INTEGER DEFAULT 0,
    ga4_status_code   INTEGER,
    ga4_response_ok   INTEGER DEFAULT 0,
    is_bot            INTEGER DEFAULT 0,
    bot_reason        TEXT,
    consent_status    TEXT DEFAULT 'unknown',
    has_email         INTEGER DEFAULT 0,
    has_phone         INTEGER DEFAULT 0,
    has_name          INTEGER DEFAULT 0,
    pixel_was_blocked INTEGER DEFAULT 0,
    raw_email         TEXT,
    created_at        TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tracker_session ON data_tracker(session_id);
CREATE INDEX IF NOT EXISTS idx_tracker_brand ON data_tracker(brand);
CREATE INDEX IF NOT EXISTS idx_tracker_event ON data_tracker(event_name);
CREATE INDEX IF NOT EXISTS idx_tracker_brand_event ON data_tracker(brand, event_name);
CREATE INDEX IF NOT EXISTS idx_tracker_lead ON data_tracker(lead_id);
CREATE INDEX IF NOT EXISTS idx_tracker_created ON data_tracker(created_at);

-- Dedup: mesmo event_id + brand não repete.
-- (linhas do middleware entram com event_id NULL: NULLs são distintos em SQLite)
CREATE UNIQUE INDEX IF NOT EXISTS idx_tracker_event_dedup ON data_tracker(event_id, brand);
