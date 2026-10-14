CREATE INDEX IF NOT EXISTS idx_offer_overrides_active_field
  ON offer_overrides(offer_id, field_name, deleted_at, id);
