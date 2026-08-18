-- Banco de MINERAÇÃO (D1 `mananciall-mining`). Não é produção.
-- Aqui mora o texto BRUTO extraído das fontes, antes de limpeza e edição.
-- Produção (livros à venda) continua em `mananciall-db`, intocada.

-- A fila. Uma linha por obra do plano (Biblioteca Mananciall no Notion).
CREATE TABLE IF NOT EXISTS works (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  notion_id     TEXT UNIQUE,           -- casa com a linha do Notion
  title         TEXT NOT NULL,
  author        TEXT,
  era           TEXT,
  priority      TEXT,                  -- P1/P2/P3
  launch        INTEGER DEFAULT 0,     -- marcado como catálogo de estreia
  source_kind   TEXT,                  -- ccel | gutenberg | newadvent | archive
  source_url    TEXT,                  -- preenchido pelo resolve
  resolve_score REAL,                  -- confiança do casamento (0..1)
  resolve_note  TEXT,
  status        TEXT NOT NULL DEFAULT 'queued',
    -- queued -> resolved -> mined | failed | skipped
    -- 'blocked' = domínio público não verificado, não mina
  chapters_n    INTEGER DEFAULT 0,
  chars_n       INTEGER DEFAULT 0,
  attempts      INTEGER DEFAULT 0,
  last_error    TEXT,
  raw_key       TEXT,                  -- caminho do snapshot cru no R2
  updated_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_works_status ON works (status, priority);

-- O texto minerado, um registro por capítulo.
CREATE TABLE IF NOT EXISTS chapters (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id    INTEGER NOT NULL,
  number     INTEGER NOT NULL,
  title      TEXT,
  body       TEXT NOT NULL,           -- texto bruto (markdown-ish), pré-limpeza
  chars      INTEGER NOT NULL DEFAULT 0,
  mined_at   TEXT DEFAULT (datetime('now')),
  UNIQUE (work_id, number)
);
CREATE INDEX IF NOT EXISTS idx_chapters_work ON chapters (work_id, number);

-- Diário de execução: toda rodada deixa rastro, pra saber o que aconteceu sem adivinhar.
CREATE TABLE IF NOT EXISTS runs (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  stage     TEXT NOT NULL,            -- queue | resolve | mine
  work_id   INTEGER,
  ok        INTEGER NOT NULL,
  detail    TEXT,
  ms        INTEGER,
  at        TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_runs_at ON runs (at DESC);
