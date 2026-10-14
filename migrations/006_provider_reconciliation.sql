ALTER TABLE offers ADD COLUMN sync_state TEXT NOT NULL DEFAULT 'current'
  CHECK (sync_state IN ('current', 'stale'));

ALTER TABLE sync_runs ADD COLUMN snapshot_checksum TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_offers_provider_sync_state
  ON offers(provider, source, sync_state, external_id);
