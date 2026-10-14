from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "var" / "vcb.sqlite3"


class Database:
    """Acesso SQLite pequeno, transacional e compartilhado pelos handlers."""

    def __init__(self, path: str | Path | None = None, migrations_dir: str | Path | None = None):
        configured = path or os.environ.get("DATABASE_PATH") or DEFAULT_DB_PATH
        self.path = Path(configured)
        self.migrations_dir = Path(migrations_dir or ROOT / "migrations")
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn

    def migrate(self) -> None:
        with self._lock:
            conn = self.connect()
            try:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS schema_migrations ("
                    "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
                )
                applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
                for migration in sorted(self.migrations_dir.glob("*.sql")):
                    if migration.name in applied:
                        continue
                    script = migration.read_text(encoding="utf-8")
                    migration_name = migration.name.replace("'", "''")
                    conn.executescript(
                        "BEGIN IMMEDIATE;\n"
                        f"{script}\n"
                        "INSERT INTO schema_migrations(version, applied_at) "
                        f"VALUES ('{migration_name}', datetime('now'));\n"
                        "COMMIT;"
                    )
                conn.commit()
            finally:
                conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = self.connect()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            conn = self.connect()
            try:
                return conn.execute(sql, params).fetchone()
            finally:
                conn.close()

    def all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            conn = self.connect()
            try:
                return conn.execute(sql, params).fetchall()
            finally:
                conn.close()
