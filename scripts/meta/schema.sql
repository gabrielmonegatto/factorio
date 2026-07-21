-- Atribuicao Meta -> criativos. Aplicar uma vez no D1 remoto:
--   python apps/br4nds/scripts/meta/apply_schema.py
-- (ou wrangler d1 execute br4nds --remote --file schema.sql --yes)

-- 1 linha por ad de qualquer uma das 5 contas.
CREATE TABLE IF NOT EXISTS meta_ads (
  ad_id            TEXT PRIMARY KEY,
  account_id       TEXT NOT NULL,
  account_name     TEXT,
  brand            TEXT,
  campaign_id      TEXT,
  campaign_name    TEXT,
  adset_id         TEXT,
  adset_name       TEXT,
  ad_name          TEXT,
  effective_status TEXT,
  creative_id      TEXT,
  creative_name    TEXT,
  image_hash       TEXT,          -- hash proprio do Meta (NAO e o nosso md5)
  image_url        TEXT,
  thumbnail_url    TEXT,
  dhash            TEXT,          -- perceptual da imagem do Meta
  r2_key           TEXT,          -- criativo casado (NULL ate casar)
  match_method     TEXT,          -- 'phash' | 'manual' | NULL
  match_distance   INTEGER,       -- distancia de Hamming do match
  match_confidence REAL,
  created_time     TEXT,
  updated_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_meta_ads_r2 ON meta_ads(r2_key);
CREATE INDEX IF NOT EXISTS idx_meta_ads_dhash ON meta_ads(dhash);
CREATE INDEX IF NOT EXISTS idx_meta_ads_account ON meta_ads(account_id);

-- 1 linha por ad por dia (upsert idempotente).
CREATE TABLE IF NOT EXISTS meta_insights (
  ad_id       TEXT NOT NULL,
  date        TEXT NOT NULL,
  account_id  TEXT,
  spend       REAL DEFAULT 0,
  impressions INTEGER DEFAULT 0,
  clicks      INTEGER DEFAULT 0,
  link_clicks INTEGER DEFAULT 0,
  ctr         REAL DEFAULT 0,
  purchases   INTEGER DEFAULT 0,   -- fb_pixel_purchase ate 30/04/26; custom 'p' depois
  revenue     REAL DEFAULT 0,
  atc         INTEGER DEFAULT 0,   -- add to cart (custom 'a_t_c')
  checkouts   INTEGER DEFAULT 0,   -- initiate checkout (custom 'i_c')
  leads       INTEGER DEFAULT 0,
  updated_at  TEXT,
  PRIMARY KEY (ad_id, date)
);
CREATE INDEX IF NOT EXISTS idx_meta_insights_date ON meta_insights(date);
