CREATE TABLE IF NOT EXISTS audit_retention_gate (
  id INTEGER PRIMARY KEY CHECK (id = 1)
);

CREATE TRIGGER IF NOT EXISTS audit_events_no_update
BEFORE UPDATE ON audit_events
BEGIN
  SELECT RAISE(ABORT, 'audit_events é append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
BEFORE DELETE ON audit_events
WHEN NOT EXISTS (SELECT 1 FROM audit_retention_gate WHERE id = 1)
BEGIN
  SELECT RAISE(ABORT, 'audit_events é append-only');
END;

CREATE TRIGGER IF NOT EXISTS users_audit_delete_guard
BEFORE DELETE ON users
WHEN EXISTS (SELECT 1 FROM audit_events WHERE actor_user_id = OLD.id)
BEGIN
  SELECT RAISE(ABORT, 'usuário possui eventos de auditoria');
END;

CREATE INDEX IF NOT EXISTS idx_audit_events_actor_action
  ON audit_events(actor_user_id, action, created_at);
