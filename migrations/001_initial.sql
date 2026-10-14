CREATE TABLE IF NOT EXISTS offers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL CHECK (source IN ('operator', 'manual')),
  provider TEXT NOT NULL,
  external_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('pacote', 'promo-voo', 'campanha')),
  title TEXT NOT NULL,
  destination TEXT NOT NULL DEFAULT '',
  origin_city TEXT NOT NULL DEFAULT '',
  origin_airport TEXT NOT NULL DEFAULT '',
  origin_bucket TEXT NOT NULL DEFAULT '',
  category_site TEXT NOT NULL DEFAULT '',
  offer_type TEXT NOT NULL DEFAULT '',
  departure_date TEXT NOT NULL DEFAULT '',
  sort_date TEXT NOT NULL DEFAULT '',
  sort_price REAL,
  currency TEXT NOT NULL DEFAULT 'BRL',
  status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
  is_highlight INTEGER NOT NULL DEFAULT 0 CHECK (is_highlight IN (0, 1)),
  display_order INTEGER NOT NULL DEFAULT 999999,
  data_json TEXT NOT NULL,
  rendered_html TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(provider, external_id)
);

CREATE INDEX IF NOT EXISTS idx_offers_public
  ON offers(kind, status, is_highlight, display_order, sort_date);
CREATE INDEX IF NOT EXISTS idx_offers_source
  ON offers(source, provider, external_id);

CREATE TABLE IF NOT EXISTS sync_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  source_reference TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('started', 'success', 'failed')),
  imported_count INTEGER NOT NULL DEFAULT 0,
  details_json TEXT NOT NULL DEFAULT '{}',
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT
);
