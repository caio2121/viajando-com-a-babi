ALTER TABLE offers ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE offers ADD COLUMN deleted_at TEXT;

CREATE TABLE IF NOT EXISTS providers (
  code TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  adapter_version TEXT NOT NULL DEFAULT '1',
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'paused', 'disabled')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO providers(code, display_name)
VALUES ('cativa', 'Cativa'), ('manual', 'Manual');

CREATE TABLE IF NOT EXISTS media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  storage_key TEXT NOT NULL UNIQUE,
  media_type TEXT NOT NULL CHECK (media_type IN ('image', 'thumbnail')),
  mime_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL CHECK (byte_size > 0),
  width INTEGER NOT NULL CHECK (width > 0),
  height INTEGER NOT NULL CHECK (height > 0),
  checksum TEXT NOT NULL,
  alt_text TEXT NOT NULL DEFAULT '',
  rights_status TEXT NOT NULL DEFAULT 'unknown'
    CHECK (rights_status IN ('unknown', 'pending', 'approved', 'rejected')),
  source_url TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS offer_media (
  offer_id INTEGER NOT NULL,
  media_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'gallery'
    CHECK (role IN ('cover', 'gallery')),
  display_order INTEGER NOT NULL DEFAULT 0 CHECK (display_order >= 0),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (offer_id, media_id, role),
  FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE RESTRICT,
  FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS offer_overrides (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  field_name TEXT NOT NULL CHECK (length(trim(field_name)) > 0),
  value_json TEXT NOT NULL,
  reason TEXT NOT NULL DEFAULT '',
  created_by INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT,
  UNIQUE (offer_id, field_name, created_at),
  FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS offer_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  sync_run_id INTEGER,
  change_type TEXT NOT NULL
    CHECK (change_type IN ('created', 'updated', 'published', 'unpublished', 'archived', 'synced')),
  before_json TEXT NOT NULL DEFAULT '{}',
  after_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE RESTRICT,
  FOREIGN KEY (sync_run_id) REFERENCES sync_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sync_run_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sync_run_id INTEGER NOT NULL,
  offer_id INTEGER,
  external_id TEXT NOT NULL,
  status TEXT NOT NULL
    CHECK (status IN ('received', 'validated', 'imported', 'rejected', 'removed')),
  error_code TEXT NOT NULL DEFAULT '',
  details_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE (sync_run_id, external_id),
  FOREIGN KEY (sync_run_id) REFERENCES sync_runs(id) ON DELETE CASCADE,
  FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL CHECK (length(trim(password_hash)) > 0),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'disabled', 'pending_reset')),
  last_login_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS roles (
  code TEXT PRIMARY KEY CHECK (length(trim(code)) > 0),
  display_name TEXT NOT NULL
);

INSERT OR IGNORE INTO roles(code, display_name)
VALUES ('admin', 'Administrador'), ('editor', 'Editor'), ('viewer', 'Leitor');

CREATE TABLE IF NOT EXISTS user_roles (
  user_id INTEGER NOT NULL,
  role_code TEXT NOT NULL,
  PRIMARY KEY (user_id, role_code),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_code) REFERENCES roles(code) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_user_id INTEGER,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL DEFAULT '',
  request_id TEXT NOT NULL DEFAULT '',
  ip_hash TEXT NOT NULL DEFAULT '',
  change_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  code TEXT PRIMARY KEY CHECK (length(trim(code)) > 0),
  status TEXT NOT NULL DEFAULT 'disabled'
    CHECK (status IN ('enabled', 'disabled', 'paused')),
  timeout_seconds INTEGER NOT NULL CHECK (timeout_seconds > 0),
  retry_limit INTEGER NOT NULL DEFAULT 0 CHECK (retry_limit >= 0),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_code TEXT NOT NULL,
  triggered_by INTEGER,
  lock_key TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL
    CHECK (status IN ('started', 'success', 'failed', 'cancelled')),
  error_code TEXT NOT NULL DEFAULT '',
  details_json TEXT NOT NULL DEFAULT '{}',
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT,
  FOREIGN KEY (job_code) REFERENCES jobs(code) ON DELETE RESTRICT,
  FOREIGN KEY (triggered_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_offers_active
  ON offers(kind, status, deleted_at, updated_at);
CREATE INDEX IF NOT EXISTS idx_media_active
  ON media(deleted_at, rights_status);
CREATE INDEX IF NOT EXISTS idx_offer_media_order
  ON offer_media(offer_id, role, display_order);
CREATE INDEX IF NOT EXISTS idx_offer_history_offer
  ON offer_history(offer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sync_run_items_run
  ON sync_run_items(sync_run_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource
  ON audit_events(resource_type, resource_id, created_at);
CREATE INDEX IF NOT EXISTS idx_job_runs_status
  ON job_runs(job_code, status, started_at);
