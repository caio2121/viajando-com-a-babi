CREATE TABLE _integrity_migration_guard (
  valid INTEGER NOT NULL CHECK (valid = 1)
);

INSERT INTO _integrity_migration_guard(valid)
SELECT CASE WHEN EXISTS (
  SELECT 1 FROM offers o
  WHERE NOT EXISTS (SELECT 1 FROM providers p WHERE p.code = o.provider)
     OR (o.source = 'manual' AND o.provider <> 'manual')
     OR (o.source = 'operator' AND o.provider = 'manual')
     OR EXISTS (
       SELECT 1 FROM offer_overrides oo
       WHERE oo.offer_id = o.id
         AND oo.created_by IS NOT NULL
         AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = oo.created_by)
     )
)
OR EXISTS (
  SELECT 1 FROM sync_runs sr
  WHERE NOT EXISTS (SELECT 1 FROM providers p WHERE p.code = sr.provider)
)
THEN 0 ELSE 1 END;

DROP TABLE _integrity_migration_guard;

CREATE TRIGGER IF NOT EXISTS offers_provider_insert_guard
BEFORE INSERT ON offers
WHEN NOT EXISTS (SELECT 1 FROM providers WHERE code = NEW.provider)
  OR (NEW.source = 'manual' AND NEW.provider <> 'manual')
  OR (NEW.source = 'operator' AND NEW.provider = 'manual')
BEGIN
  SELECT RAISE(ABORT, 'provider ou ownership inválido');
END;

CREATE TRIGGER IF NOT EXISTS offers_provider_update_guard
BEFORE UPDATE OF source, provider ON offers
WHEN NOT EXISTS (SELECT 1 FROM providers WHERE code = NEW.provider)
  OR (NEW.source = 'manual' AND NEW.provider <> 'manual')
  OR (NEW.source = 'operator' AND NEW.provider = 'manual')
BEGIN
  SELECT RAISE(ABORT, 'provider ou ownership inválido');
END;

CREATE TRIGGER IF NOT EXISTS sync_runs_provider_insert_guard
BEFORE INSERT ON sync_runs
WHEN NOT EXISTS (SELECT 1 FROM providers WHERE code = NEW.provider)
BEGIN
  SELECT RAISE(ABORT, 'provider inexistente');
END;

CREATE TRIGGER IF NOT EXISTS sync_runs_provider_update_guard
BEFORE UPDATE OF provider ON sync_runs
WHEN NOT EXISTS (SELECT 1 FROM providers WHERE code = NEW.provider)
BEGIN
  SELECT RAISE(ABORT, 'provider inexistente');
END;

CREATE TRIGGER IF NOT EXISTS providers_delete_guard
BEFORE DELETE ON providers
WHEN EXISTS (SELECT 1 FROM offers WHERE provider = OLD.code)
  OR EXISTS (SELECT 1 FROM sync_runs WHERE provider = OLD.code)
BEGIN
  SELECT RAISE(ABORT, 'provider referenciado não pode ser removido');
END;

CREATE TRIGGER IF NOT EXISTS providers_code_update_guard
BEFORE UPDATE OF code ON providers
WHEN EXISTS (SELECT 1 FROM offers WHERE provider = OLD.code)
  OR EXISTS (SELECT 1 FROM sync_runs WHERE provider = OLD.code)
BEGIN
  SELECT RAISE(ABORT, 'provider referenciado não pode ser renomeado');
END;

CREATE TRIGGER IF NOT EXISTS offer_overrides_created_by_guard
BEFORE INSERT ON offer_overrides
WHEN NEW.created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.created_by)
BEGIN
  SELECT RAISE(ABORT, 'usuário criador inexistente');
END;

CREATE TRIGGER IF NOT EXISTS offer_overrides_created_by_update_guard
BEFORE UPDATE OF created_by ON offer_overrides
WHEN NEW.created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.created_by)
BEGIN
  SELECT RAISE(ABORT, 'usuário criador inexistente');
END;

CREATE TRIGGER IF NOT EXISTS users_delete_guard
BEFORE DELETE ON users
WHEN EXISTS (SELECT 1 FROM offer_overrides WHERE created_by = OLD.id)
BEGIN
  SELECT RAISE(ABORT, 'usuário referenciado não pode ser removido');
END;

CREATE TRIGGER IF NOT EXISTS offers_archive_soft_delete_insert
AFTER INSERT ON offers
WHEN NEW.status = 'archived' AND NEW.deleted_at IS NULL
BEGIN
  UPDATE offers SET deleted_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS offers_archive_soft_delete_update
AFTER UPDATE OF status ON offers
WHEN NEW.status = 'archived' AND NEW.deleted_at IS NULL
BEGIN
  UPDATE offers SET deleted_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS offers_restore_clears_soft_delete
AFTER UPDATE OF status ON offers
WHEN NEW.status <> 'archived' AND OLD.deleted_at IS NOT NULL
BEGIN
  UPDATE offers SET deleted_at = NULL WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS offers_physical_delete_guard
BEFORE DELETE ON offers
BEGIN
  SELECT RAISE(ABORT, 'oferta exige soft delete');
END;

CREATE TRIGGER IF NOT EXISTS media_physical_delete_guard
BEFORE DELETE ON media
BEGIN
  SELECT RAISE(ABORT, 'mídia exige soft delete');
END;

CREATE TRIGGER IF NOT EXISTS offer_overrides_physical_delete_guard
BEFORE DELETE ON offer_overrides
BEGIN
  SELECT RAISE(ABORT, 'override exige soft delete');
END;
