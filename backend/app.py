from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import logging
import math
import mimetypes
import os
import secrets
import sqlite3
import time
import uuid
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .auth import hash_password, token_digest, verify_password
from .presentation import render_manual_package
from .providers import import_sync, offer_select_sql, offer_to_api
from .storage import Database, ROOT


LOG = logging.getLogger("vcb.backend")
HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", "8080"))
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5521920064617")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"
try:
    AUDIT_RETENTION_DAYS = int(os.environ.get("AUDIT_RETENTION_DAYS", "365"))
except ValueError as exc:
    raise RuntimeError("AUDIT_RETENTION_DAYS inválido") from exc
if not 30 <= AUDIT_RETENTION_DAYS <= 3650:
    raise RuntimeError("AUDIT_RETENTION_DAYS deve estar entre 30 e 3650")
DB = Database()


def _seed_if_empty() -> None:
    row = DB.one("SELECT COUNT(*) AS count FROM offers")
    if row and row["count"]:
        return
    try:
        result = import_sync(DB, ROOT)
        LOG.info("seed local concluído: %s", result)
    except Exception:
        LOG.exception("não foi possível importar o snapshot local; o fallback estático continua disponível")


_seed_if_empty()


def _json_error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


_AUDIT_SECRET_KEYS = {
    "password", "password_hash", "new_password", "token", "access_token", "refresh_token",
    "csrf_token", "secret", "authorization", "cookie", "api_key",
}


def _redact_audit(value):
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _AUDIT_SECRET_KEYS else _redact_audit(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_audit(item) for item in value]
    return value


def _audit(
    conn: sqlite3.Connection,
    handler: BaseHTTPRequestHandler | None,
    actor_user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: str = "",
    change: dict | None = None,
) -> None:
    _prune_audit(conn)
    address = ""
    if handler is not None:
        address = str(getattr(handler, "client_address", ("",))[0])
    audit_key = (SESSION_SECRET or "local-audit").encode("utf-8")
    ip_hash = hmac.new(audit_key, address.encode("utf-8"), hashlib.sha256).hexdigest()
    conn.execute(
        """INSERT INTO audit_events(
             actor_user_id, action, resource_type, resource_id, request_id, ip_hash, change_json
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            actor_user_id,
            action,
            resource_type,
            str(resource_id or ""),
            uuid.uuid4().hex,
            ip_hash,
            json.dumps(_redact_audit(change or {}), ensure_ascii=False, sort_keys=True),
        ),
    )


def _prune_audit(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT OR IGNORE INTO audit_retention_gate(id) VALUES (1)")
    conn.execute(
        "DELETE FROM audit_events WHERE created_at < datetime('now', ?)",
        (f"-{AUDIT_RETENTION_DAYS} days",),
    )
    conn.execute("DELETE FROM audit_retention_gate WHERE id = 1")


with DB.transaction() as _conn:
    _prune_audit(_conn)


def _ensure_bootstrap_admin() -> None:
    if not ADMIN_PASSWORD:
        return
    if DB.one("SELECT id FROM users LIMIT 1"):
        return
    with DB.transaction() as conn:
        user = conn.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD)),
        )
        conn.execute("INSERT INTO user_roles(user_id, role_code) VALUES (?, 'admin')", (user.lastrowid,))


_ensure_bootstrap_admin()


def _issue_password_reset(username: str, handler: BaseHTTPRequestHandler | None = None, ttl_seconds: int = 900) -> str | None:
    user = DB.one("SELECT id FROM users WHERE username=? AND status='active'", (username,))
    if not user:
        with DB.transaction() as conn:
            _audit(conn, handler, None, "auth.password_reset_requested", "auth", change={"username_present": bool(username)})
        return None
    token = secrets.token_urlsafe(32)
    with DB.transaction() as conn:
        conn.execute("DELETE FROM password_reset_tokens WHERE user_id=? AND used_at IS NULL", (user["id"],))
        conn.execute(
            "INSERT INTO password_reset_tokens(user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user["id"], token_digest(token), str(int(time.time()) + ttl_seconds)),
        )
        _audit(conn, handler, user["id"], "auth.password_reset_requested", "user", user["id"])
    return token


def _consume_password_reset(username: str, token: str, new_password: str, handler: BaseHTTPRequestHandler | None = None) -> bool:
    if not token or not isinstance(new_password, str):
        with DB.transaction() as conn:
            _audit(conn, handler, None, "auth.password_reset_failed", "auth", change={"reason": "invalid_input"})
        return False
    with DB.transaction() as conn:
        row = conn.execute(
            """SELECT t.id, t.expires_at, u.id AS user_id
               FROM password_reset_tokens t JOIN users u ON u.id=t.user_id
               WHERE u.username=? AND t.token_hash=? AND t.used_at IS NULL""",
            (username, token_digest(token)),
        ).fetchone()
        if not row or int(row["expires_at"]) < int(time.time()):
            _audit(conn, handler, None, "auth.password_reset_failed", "auth", change={"reason": "invalid_or_expired"})
            return False
        try:
            password_hash = hash_password(new_password)
        except ValueError:
            _audit(conn, handler, row["user_id"], "auth.password_reset_failed", "user", row["user_id"], {"reason": "validation"})
            return False
        conn.execute("UPDATE users SET password_hash=?, updated_at=datetime('now') WHERE id=?", (password_hash, row["user_id"]))
        conn.execute("UPDATE password_reset_tokens SET used_at=datetime('now') WHERE id=?", (row["id"],))
        _audit(conn, handler, row["user_id"], "auth.password_reset", "user", row["user_id"])
    return True


def _parse_json(handler: BaseHTTPRequestHandler) -> dict:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise ValueError("Content-Length inválido") from exc
    if length < 0:
        raise ValueError("Content-Length inválido")
    if length > 1_000_000:
        raise ValueError("payload excede o limite de 1 MB")
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON inválido") from exc
    if not isinstance(data, dict):
        raise ValueError("o corpo deve ser um objeto JSON")
    return data


def _cookie_header(name: str, value: str, max_age: int = 28_800) -> str:
    flags = [f"{name}={value}", f"Max-Age={max_age}", "Path=/", "HttpOnly", "SameSite=Lax"]
    if COOKIE_SECURE:
        flags.append("Secure")
    return "; ".join(flags)


def _sign_session(payload: dict) -> str:
    if not SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET não configurada")
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    digest = hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{digest}"


def _read_session(handler: BaseHTTPRequestHandler) -> dict | None:
    cookie = SimpleCookie()
    cookie.load(handler.headers.get("Cookie", ""))
    token = cookie.get("vcb_admin")
    if not token or not SESSION_SECRET:
        return None
    try:
        encoded, digest = token.value.split(".", 1)
        expected = hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, expected):
            return None
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        user = DB.one("SELECT id, username, status FROM users WHERE id=?", (int(payload.get("user_id", 0)),))
        if not user or user["status"] != "active":
            return None
        roles = [row[0] for row in DB.all("SELECT role_code FROM user_roles WHERE user_id=?", (user["id"],))]
        payload["user_id"] = user["id"]
        payload["username"] = user["username"]
        payload["roles"] = roles
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def _validate_csrf(handler: BaseHTTPRequestHandler, session: dict | None) -> bool:
    return bool(session and hmac.compare_digest(str(session.get("csrf", "")), handler.headers.get("X-CSRF-Token", "")))


def _has_role(session: dict, required_role: str) -> bool:
    roles = set(session.get("roles") or [])
    if "admin" in roles:
        return True
    return required_role in roles


def _slug(value: str) -> str:
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFD", value.lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")[:80]


def _validate_manual_payload(payload: dict, existing: dict | None = None) -> dict:
    merged = dict(existing or {})
    merged.update(payload)
    title = str(merged.get("title") or "").strip()
    destination = str(merged.get("destination") or title).strip()
    if not title or len(title) > 180:
        raise ValueError("title é obrigatório e deve ter até 180 caracteres")
    if len(destination) > 120:
        raise ValueError("destination deve ter até 120 caracteres")
    kind = str(merged.get("kind") or "pacote")
    if kind != "pacote":
        raise ValueError("o admin local gerencia pacotes; voos e campanhas continuam no provider")
    origin_bucket = str(merged.get("origin_bucket") or "sem-aereo").strip().replace("_", "-")
    if origin_bucket not in {"rio", "sp", "sem-aereo"}:
        raise ValueError("origin_bucket inválido")
    dates = merged.get("dates") or []
    if isinstance(dates, str):
        dates = [item.strip() for item in dates.replace(";", ",").split(",") if item.strip()]
    if not isinstance(dates, list) or len(dates) > 30 or any(not isinstance(item, str) for item in dates):
        raise ValueError("dates deve ser uma lista de datas ISO")
    import datetime

    for item in dates:
        try:
            if len(item) != 10:
                raise ValueError
            datetime.date.fromisoformat(item)
        except ValueError as exc:
            raise ValueError("dates deve usar o formato AAAA-MM-DD") from exc
    try:
        price = float(merged.get("price") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("price inválido") from exc
    if not math.isfinite(price) or price < 0 or price > 10_000_000:
        raise ValueError("price fora do limite permitido")
    features = merged.get("features") or []
    if isinstance(features, str):
        features = [line.strip() for line in features.splitlines() if line.strip()]
    if not isinstance(features, list) or len(features) > 8 or any(not isinstance(item, str) for item in features):
        raise ValueError("features deve ser uma lista de textos")
    features = [item.strip() for item in features if item.strip()]
    if any(len(item) > 240 for item in features):
        raise ValueError("cada feature deve ter até 240 caracteres")
    image_url = str(merged.get("image_url") or "assets/og-share.jpeg").strip()
    parsed_image = urlparse(image_url)
    image_path = parsed_image.path.lstrip("/")
    if (
        len(image_url) > 500
        or parsed_image.scheme
        or parsed_image.netloc
        or not image_path.startswith("assets/")
        or ".." in Path(image_path).parts
        or any(ord(char) < 32 for char in image_url)
        or any(char in image_url for char in '<>"\'`')
    ):
        raise ValueError("image_url inválida")
    status = str(merged.get("status") or "draft")
    if status not in {"draft", "published", "archived"}:
        raise ValueError("status inválido")
    external_id = str(merged.get("external_id") or f"manual:{uuid.uuid4().hex}")
    origin_city = str(merged.get("origin_city") or "").strip()
    origin_airport = str(merged.get("origin_airport") or "").strip()
    if len(origin_city) > 100 or len(origin_airport) > 30 or len(external_id) > 160:
        raise ValueError("campo de origem ou external_id excede o limite")
    return {
        "kind": kind,
        "title": title,
        "destination": destination,
        "origin_bucket": origin_bucket,
        "origin_city": origin_city,
        "origin_airport": origin_airport,
        "dates": dates,
        "price": price,
        "features": features,
        "image_url": image_url,
        "status": status,
        "external_id": external_id,
    }


def _manual_row(data: dict) -> dict:
    dates = data["dates"]
    return {
        "source": "manual",
        "provider": "manual",
        "external_id": data["external_id"],
        "kind": "pacote",
        "title": data["title"],
        "destination": data["destination"],
        "origin_city": data["origin_city"],
        "origin_airport": data["origin_airport"],
        "origin_bucket": data["origin_bucket"],
        "category_site": "completo" if data["origin_bucket"] != "sem-aereo" else "sem-aereo",
        "offer_type": "com-aereo" if data["origin_bucket"] != "sem-aereo" else "sem-aereo",
        "departure_date": dates[0] if dates else "",
        "sort_date": dates[0] if dates else "",
        "sort_price": data["price"] or None,
        "currency": "BRL",
        "status": data["status"],
        "is_highlight": 0,
        "display_order": 999999,
        "data_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
        "rendered_html": render_manual_package(data, WHATSAPP_NUMBER),
    }


_OVERRIDE_FIELDS = {"is_highlight", "display_order"}


def _validate_override_payload(payload: dict) -> tuple[str, object, str]:
    field = str(payload.get("field") or "").strip()
    if field not in _OVERRIDE_FIELDS:
        raise ValueError("campo não pode ser sobrescrito manualmente")
    value = payload.get("value")
    if field == "is_highlight" and not isinstance(value, bool):
        raise ValueError("is_highlight deve ser booleano")
    if field == "display_order" and (
        isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 1_000_000
    ):
        raise ValueError("display_order deve ser um inteiro entre 0 e 1000000")
    reason = str(payload.get("reason") or "").strip()
    if not reason or len(reason) > 500:
        raise ValueError("reason é obrigatório e deve ter até 500 caracteres")
    return field, value, reason


def _override_items(rows) -> list[dict]:
    items = []
    for row in rows:
        try:
            value = json.loads(row["value_json"])
        except (TypeError, json.JSONDecodeError):
            value = None
        items.append({
            "id": row["id"],
            "field": row["field_name"],
            "value": value,
            "reason": row["reason"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
        })
    return items


_HISTORY_FIELDS = (
    "title", "destination", "origin_city", "origin_airport", "origin_bucket",
    "sort_date", "sort_price", "currency", "status", "is_highlight",
    "display_order", "sync_state",
)
_HISTORY_DATA_FIELDS = ("dates", "features", "image_url")


def _history_diff(before_json: str, after_json: str) -> dict:
    try:
        before = json.loads(before_json or "{}")
    except json.JSONDecodeError:
        before = {}
    try:
        after = json.loads(after_json or "{}")
    except json.JSONDecodeError:
        after = {}
    changes = {
        field: {"before": before.get(field), "after": after.get(field)}
        for field in _HISTORY_FIELDS
        if before.get(field) != after.get(field)
    }
    for field in _HISTORY_DATA_FIELDS:
        before_data = _history_data(before.get("data_json"))
        after_data = _history_data(after.get("data_json"))
        if before_data.get(field) != after_data.get(field):
            changes[field] = {"before": before_data.get(field), "after": after_data.get(field)}
    return changes


def _history_data(value) -> dict:
    if not isinstance(value, str):
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


class Handler(BaseHTTPRequestHandler):
    server_version = "VCBLocal/1.0"

    def log_message(self, format: str, *args) -> None:
        LOG.info("request %s", format % args)

    def _send(self, status: int, payload: object, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.end_headers()

    def _require_admin(self, csrf: bool = False, required_role: str = "viewer") -> dict | None:
        session = _read_session(self)
        if not session:
            with DB.transaction() as conn:
                _audit(conn, self, None, "authz.denied", "route", urlparse(self.path).path, {"reason": "unauthenticated"})
            self._send(HTTPStatus.UNAUTHORIZED, _json_error("unauthorized", "autenticação administrativa necessária"))
            return None
        if csrf and not _validate_csrf(self, session):
            with DB.transaction() as conn:
                _audit(conn, self, session["user_id"], "authz.denied", "route", urlparse(self.path).path, {"reason": "csrf"})
            self._send(HTTPStatus.FORBIDDEN, _json_error("csrf_failed", "token CSRF inválido"))
            return None
        if not _has_role(session, required_role):
            with DB.transaction() as conn:
                _audit(conn, self, session["user_id"], "authz.denied", "route", urlparse(self.path).path, {"reason": "role"})
            self._send(HTTPStatus.FORBIDDEN, _json_error("forbidden", "permissão insuficiente"))
            return None
        return session

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "database": str(DB.path), "schema": "001_initial"})
            return
        if path == "/admin":
            self._redirect("/admin/")
            return
        if path == "/api/offers":
            self._public_offers(parse_qs(parsed.query))
            return
        if path == "/api/admin/session":
            session = self._require_admin()
            if session:
                self._send(HTTPStatus.OK, {"authenticated": True, "csrf": session["csrf"]})
            return
        if path == "/api/admin/audit":
            session = self._require_admin(required_role="admin")
            if session:
                self._admin_audit(parse_qs(parsed.query))
            return
        if path == "/api/admin/sync-runs":
            session = self._require_admin(required_role="editor")
            if session:
                self._admin_sync_runs(parse_qs(parsed.query))
            return
        if path == "/api/admin/offers":
            session = self._require_admin()
            if session:
                rows = DB.all(f"{offer_select_sql()} ORDER BY o.updated_at DESC, o.id DESC")
                self._send(HTTPStatus.OK, {"items": [offer_to_api(row, include_html=False) for row in rows]})
            return
        if path.startswith("/api/admin/offers/") and path.endswith("/overrides"):
            session = self._require_admin(required_role="editor")
            if session:
                try:
                    offer_id = int(path.split("/")[4])
                except (IndexError, ValueError):
                    self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_id", "id inválido"))
                    return
                self._admin_overrides(offer_id)
            return
        if path.startswith("/api/admin/offers/") and path.endswith("/history"):
            session = self._require_admin(required_role="editor")
            if session:
                try:
                    offer_id = int(path.split("/")[4])
                except (IndexError, ValueError):
                    self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_id", "id inválido"))
                    return
                self._admin_history(offer_id, parse_qs(parsed.query))
            return
        if path.startswith("/api/admin/offers/"):
            session = self._require_admin()
            if session:
                try:
                    offer_id = int(path.rsplit("/", 1)[1])
                except ValueError:
                    self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
                    return
                row = DB.one(f"{offer_select_sql()} WHERE o.id=?", (offer_id,))
                if not row:
                    self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
                else:
                    self._send(HTTPStatus.OK, offer_to_api(row, include_html=False))
            return
        self._serve_static(path)

    def _public_offers(self, query: dict[str, list[str]]) -> None:
        allowed = {"pacote", "promo-voo", "campanha"}
        kind = (query.get("kind") or [""])[0]
        if kind not in allowed:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_kind", "kind inválido"))
            return
        placement = (query.get("placement") or ["catalog"])[0]
        try:
            limit = min(max(int((query.get("limit") or ["1000"])[0] or 1000), 1), 1000)
        except (TypeError, ValueError):
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_query", "limit inválido"))
            return
        if placement == "home" and kind == "pacote":
            sql = f"""{offer_select_sql()} WHERE o.kind=? AND o.status='published'
                     AND COALESCE((SELECT json_extract(value_json, '$') FROM offer_overrides
                                   WHERE offer_id=o.id AND field_name='is_highlight' AND deleted_at IS NULL
                                   ORDER BY id DESC LIMIT 1), o.is_highlight)=1
                     ORDER BY COALESCE((SELECT json_extract(value_json, '$') FROM offer_overrides
                                        WHERE offer_id=o.id AND field_name='display_order' AND deleted_at IS NULL
                                        ORDER BY id DESC LIMIT 1), o.display_order), o.sort_date, o.title LIMIT ?"""
            params = (kind, limit)
        else:
            sql = f"""{offer_select_sql()} WHERE o.kind=? AND o.status='published'
                     ORDER BY COALESCE((SELECT json_extract(value_json, '$') FROM offer_overrides
                                        WHERE offer_id=o.id AND field_name='display_order' AND deleted_at IS NULL
                                        ORDER BY id DESC LIMIT 1), o.display_order), o.sort_date, o.title LIMIT ?"""
            params = (kind, limit)
        try:
            rows = DB.all(sql, params)
        except (ValueError, IndexError):
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_query", "parâmetros inválidos"))
            return
        self._send(HTTPStatus.OK, {"items": [offer_to_api(row, include_data=False) for row in rows], "count": len(rows), "source": "database"})

    def _admin_audit(self, query: dict[str, list[str]]) -> None:
        try:
            limit = min(max(int((query.get("limit") or ["100"])[0] or 100), 1), 200)
        except (TypeError, ValueError):
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_query", "limit inválido"))
            return
        with DB.transaction() as conn:
            _prune_audit(conn)
        rows = DB.all(
            """SELECT id, actor_user_id, action, resource_type, resource_id,
                      request_id, ip_hash, change_json, created_at
                 FROM audit_events ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        items = []
        for row in rows:
            try:
                change = json.loads(row["change_json"] or "{}")
            except json.JSONDecodeError:
                change = {}
            items.append({
                "id": row["id"],
                "actor_user_id": row["actor_user_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "request_id": row["request_id"],
                "ip_hash": row["ip_hash"],
                "change": change,
                "created_at": row["created_at"],
            })
        self._send(HTTPStatus.OK, {"items": items, "retention_days": AUDIT_RETENTION_DAYS})

    def _admin_sync_runs(self, query: dict[str, list[str]]) -> None:
        try:
            limit = min(max(int((query.get("limit") or ["50"])[0] or 50), 1), 100)
        except (TypeError, ValueError):
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_query", "limit inválido"))
            return
        rows = DB.all(
            """SELECT id, provider, source_reference, status, imported_count,
                      details_json, snapshot_checksum, started_at, finished_at
                 FROM sync_runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
        items = []
        for row in rows:
            try:
                details = json.loads(row["details_json"] or "{}")
            except json.JSONDecodeError:
                details = {}
            counts = DB.all(
                "SELECT status, COUNT(*) AS count FROM sync_run_items WHERE sync_run_id=? GROUP BY status",
                (row["id"],),
            )
            items.append({
                "id": row["id"],
                "provider": row["provider"],
                "source_reference": row["source_reference"],
                "status": row["status"],
                "imported_count": row["imported_count"],
                "snapshot_checksum": row["snapshot_checksum"],
                "details": details,
                "item_counts": {item["status"]: item["count"] for item in counts},
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
            })
        self._send(HTTPStatus.OK, {"items": items})

    def _admin_overrides(self, offer_id: int) -> None:
        row = DB.one("SELECT source FROM offers WHERE id=?", (offer_id,))
        if not row:
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
            return
        self._send(
            HTTPStatus.OK,
            {"items": _override_items(DB.all(
                """SELECT id, field_name, value_json, reason, created_by, created_at
                   FROM offer_overrides
                  WHERE offer_id=? AND deleted_at IS NULL
                  ORDER BY id DESC""",
                (offer_id,),
            )), "allowed_fields": sorted(_OVERRIDE_FIELDS)},
        )

    def _admin_history(self, offer_id: int, query: dict[str, list[str]]) -> None:
        try:
            limit = min(max(int((query.get("limit") or ["20"])[0] or 20), 1), 50)
        except (TypeError, ValueError):
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_query", "limit inválido"))
            return
        if not DB.one("SELECT id FROM offers WHERE id=?", (offer_id,)):
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
            return
        rows = DB.all(
            """SELECT id, sync_run_id, change_type, before_json, after_json, created_at
                 FROM offer_history WHERE offer_id=? ORDER BY id DESC LIMIT ?""",
            (offer_id, limit),
        )
        self._send(HTTPStatus.OK, {"items": [{
            "id": row["id"],
            "sync_run_id": row["sync_run_id"],
            "change_type": row["change_type"],
            "changes": _history_diff(row["before_json"], row["after_json"]),
            "created_at": row["created_at"],
        } for row in rows]})

    def _create_override(self, offer_id: int, payload: dict, session: dict) -> None:
        try:
            field, value, reason = _validate_override_payload(payload)
            row = DB.one("SELECT source FROM offers WHERE id=?", (offer_id,))
            if not row:
                self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
                return
            if row["source"] != "operator":
                self._send(HTTPStatus.CONFLICT, _json_error("not_provider_offer", "override só se aplica a oferta automática"))
                return
            with DB.transaction() as conn:
                override = conn.execute(
                    "INSERT INTO offer_overrides(offer_id, field_name, value_json, reason, created_by) VALUES (?, ?, ?, ?, ?)",
                    (offer_id, field, json.dumps(value, ensure_ascii=False), reason, session["user_id"]),
                )
                _audit(
                    conn,
                    self,
                    session["user_id"],
                    "offer.override_created",
                    "offer",
                    offer_id,
                    {"field": field, "reason": reason},
                )
            self._send(HTTPStatus.CREATED, {"id": override.lastrowid, "field": field, "value": value, "reason": reason})
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", str(exc)))

    def _delete_override(self, offer_id: int, field: str, session: dict) -> None:
        if field not in _OVERRIDE_FIELDS:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", "campo não pode ser sobrescrito manualmente"))
            return
        with DB.transaction() as conn:
            result = conn.execute(
                "UPDATE offer_overrides SET deleted_at=datetime('now') WHERE offer_id=? AND field_name=? AND deleted_at IS NULL",
                (offer_id, field),
            )
            if result.rowcount == 0:
                self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "override não encontrado"))
                return
            _audit(conn, self, session["user_id"], "offer.override_removed", "offer", offer_id, {"field": field})
        self._send(HTTPStatus.OK, {"ok": True, "field": field})

    def _serve_static(self, path: str) -> None:
        relative = path.lstrip("/") or "index.html"
        if relative == "admin/":
            relative = "admin/index.html"
        parts = Path(relative).parts
        normalized_parts = tuple(part.lower() for part in parts)
        blocked_roots = {".git", "backend", "data", "docs", "migrations", "tests", "var"}
        blocked_files = {"dockerfile", "compose.yaml", "requirements-dev.txt", ".env", ".env.example"}
        if (
            not parts
            or normalized_parts[0] in blocked_roots
            or any(part.startswith(".env") or part.startswith(".") for part in normalized_parts)
            or normalized_parts[-1] in blocked_files
            or normalized_parts[-1].endswith((".sqlite", ".sqlite3"))
        ):
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "recurso não encontrado"))
            return
        candidate = (ROOT / relative).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "recurso não encontrado"))
            return
        resolved_parts = tuple(part.lower() for part in candidate.relative_to(ROOT).parts)
        if (
            not resolved_parts
            or resolved_parts[0] in blocked_roots
            or any(part.startswith(".env") or part.startswith(".") for part in resolved_parts)
            or resolved_parts[-1] in blocked_files
            or resolved_parts[-1].endswith((".sqlite", ".sqlite3"))
        ):
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "recurso não encontrado"))
            return
        if not candidate.is_file():
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "recurso não encontrado"))
            return
        content = candidate.read_bytes()
        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = _parse_json(self)
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_json", str(exc)))
            return
        if path == "/api/admin/login":
            self._login(payload)
            return
        if path == "/api/admin/password-reset/request":
            username = str(payload.get("username") or "").strip()
            _issue_password_reset(username, self)
            self._send(HTTPStatus.ACCEPTED, {"ok": True, "message": "se houver uma conta, as instruções serão encaminhadas"})
            return
        if path == "/api/admin/password-reset/confirm":
            try:
                if not _consume_password_reset(
                    str(payload.get("username") or "").strip(),
                    str(payload.get("token") or ""),
                    str(payload.get("new_password") or ""),
                    self,
                ):
                    self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_reset", "token de recuperação inválido ou expirado"))
                    return
                self._send(HTTPStatus.OK, {"ok": True})
            except ValueError as exc:
                self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", str(exc)))
            return
        if path == "/api/admin/password-change":
            session = self._require_admin(csrf=True)
            if session:
                self._change_password(payload, session)
            return
        if path == "/api/admin/users":
            session = self._require_admin(csrf=True, required_role="admin")
            if session:
                self._create_user(payload, session)
            return
        if path == "/api/admin/logout":
            session = self._require_admin(csrf=True)
            if not session:
                return
            with DB.transaction() as conn:
                _audit(conn, self, session["user_id"], "auth.logout", "user", session["user_id"])
            self._send(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": _cookie_header("vcb_admin", "", 0)})
            return
        if path == "/api/admin/offers":
            session = self._require_admin(csrf=True, required_role="editor")
            if session:
                self._create_offer(payload, session)
            return
        if path.startswith("/api/admin/offers/") and path.endswith("/overrides"):
            session = self._require_admin(csrf=True, required_role="admin")
            if session:
                try:
                    offer_id = int(path.split("/")[4])
                except (IndexError, ValueError):
                    self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_id", "id inválido"))
                    return
                self._create_override(offer_id, payload, session)
            return
        self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "rota não encontrada"))

    def _login(self, payload: dict) -> None:
        if not SESSION_SECRET:
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, _json_error("admin_not_configured", "admin local sem credenciais de ambiente"))
            return
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        user = DB.one("SELECT id, username, password_hash, status FROM users WHERE username=?", (username,))
        if not user or user["status"] != "active" or not verify_password(password, user["password_hash"]):
            LOG.warning("falha de autenticação administrativa")
            with DB.transaction() as conn:
                _audit(conn, self, None, "auth.login_failed", "admin", change={"username_present": bool(username)})
            self._send(HTTPStatus.UNAUTHORIZED, _json_error("invalid_credentials", "credenciais inválidas"))
            return
        with DB.transaction() as conn:
            conn.execute("UPDATE users SET last_login_at=datetime('now') WHERE id=?", (user["id"],))
            _audit(conn, self, user["id"], "auth.login", "user", user["id"])
        roles = [row[0] for row in DB.all("SELECT role_code FROM user_roles WHERE user_id=?", (user["id"],))]
        session = {"user_id": user["id"], "exp": int(time.time()) + 28_800, "csrf": secrets.token_urlsafe(24), "roles": roles}
        self._send(HTTPStatus.OK, {"authenticated": True, "csrf": session["csrf"]}, {"Set-Cookie": _cookie_header("vcb_admin", _sign_session(session))})

    def _change_password(self, payload: dict, session: dict) -> None:
        try:
            current = str(payload.get("current_password") or "")
            new_password = str(payload.get("new_password") or "")
            user = DB.one("SELECT password_hash FROM users WHERE id=? AND status='active'", (session["user_id"],))
            if not user or not verify_password(current, user["password_hash"]):
                with DB.transaction() as conn:
                    _audit(conn, self, session["user_id"], "auth.password_change_failed", "user", session["user_id"], {"reason": "invalid_current"})
                self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_password", "senha atual inválida"))
                return
            password_hash = hash_password(new_password)
            with DB.transaction() as conn:
                conn.execute("UPDATE users SET password_hash=?, updated_at=datetime('now') WHERE id=?", (password_hash, session["user_id"]))
                _audit(conn, self, session["user_id"], "auth.password_change", "user", session["user_id"])
            self._send(HTTPStatus.OK, {"ok": True})
        except ValueError as exc:
            with DB.transaction() as conn:
                _audit(conn, self, session["user_id"], "auth.password_change_failed", "user", session["user_id"], {"reason": "validation"})
            self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", str(exc)))

    def _create_user(self, payload: dict, session: dict) -> None:
        username = str(payload.get("username") or "").strip()
        role = str(payload.get("role") or "viewer").strip()
        try:
            if not username or len(username) > 120 or any(char.isspace() for char in username):
                raise ValueError("username inválido")
            if role not in {"admin", "editor", "viewer"}:
                raise ValueError("role inválido")
            password_hash = hash_password(str(payload.get("password") or ""))
            with DB.transaction() as conn:
                user = conn.execute("INSERT INTO users(username, password_hash) VALUES (?, ?)", (username, password_hash))
                conn.execute("INSERT INTO user_roles(user_id, role_code) VALUES (?, ?)", (user.lastrowid, role))
                _audit(conn, self, session["user_id"], "user.created", "user", user.lastrowid, {"role": role})
            self._send(HTTPStatus.CREATED, {"id": user.lastrowid, "username": username, "role": role})
        except sqlite3.IntegrityError:
            self._send(HTTPStatus.CONFLICT, _json_error("duplicate", "usuário já existe"))
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", str(exc)))

    def _create_offer(self, payload: dict, session: dict) -> None:
        try:
            data = _validate_manual_payload(payload)
            if data["status"] in {"published", "archived"} and not _has_role(session, "admin"):
                with DB.transaction() as conn:
                    _audit(conn, self, session["user_id"], "authz.denied", "offer", "", {"reason": "publish_or_archive"})
                self._send(HTTPStatus.FORBIDDEN, _json_error("forbidden", "publicar ou arquivar exige papel admin"))
                return
            row = _manual_row(data)
            with DB.transaction() as conn:
                cursor = conn.execute(
                    """INSERT INTO offers(
                      source, provider, external_id, kind, title, destination, origin_city,
                      origin_airport, origin_bucket, category_site, offer_type, departure_date,
                      sort_date, sort_price, currency, status, is_highlight, display_order,
                      data_json, rendered_html
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    tuple(row[key] for key in (
                        "source", "provider", "external_id", "kind", "title", "destination", "origin_city",
                        "origin_airport", "origin_bucket", "category_site", "offer_type", "departure_date",
                        "sort_date", "sort_price", "currency", "status", "is_highlight", "display_order",
                        "data_json", "rendered_html",
                    )),
                )
                offer_id = cursor.lastrowid
                conn.execute(
                    "INSERT INTO offer_history(offer_id, change_type, before_json, after_json) VALUES (?, 'created', ?, ?)",
                    (
                        offer_id,
                        "{}",
                        json.dumps({**row, "id": offer_id, "sync_state": "current"}, ensure_ascii=False, sort_keys=True),
                    ),
                )
                _audit(
                    conn,
                    self,
                    session["user_id"],
                    "offer.published" if data["status"] == "published" else "offer.created",
                    "offer",
                    offer_id,
                    {"kind": data["kind"], "status": data["status"], "source": "manual"},
                )
            result = DB.one("SELECT * FROM offers WHERE id=?", (offer_id,))
            self._send(HTTPStatus.CREATED, offer_to_api(result, include_html=False))
        except Exception as exc:
            if isinstance(exc, sqlite3.IntegrityError):
                self._send(HTTPStatus.CONFLICT, _json_error("duplicate", "oferta manual duplicada"))
            elif isinstance(exc, ValueError):
                self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", str(exc)))
            else:
                LOG.exception("falha ao criar oferta administrativa")
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, _json_error("internal_error", "não foi possível salvar a oferta"))

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/admin/offers/") or "/overrides" in path:
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "rota não encontrada"))
            return
        session = self._require_admin(csrf=True, required_role="editor")
        if not session:
            return
        try:
            offer_id = int(path.rsplit("/", 1)[1])
            payload = _parse_json(self)
            row = DB.one("SELECT * FROM offers WHERE id=?", (offer_id,))
            if not row:
                raise LookupError
            if row["source"] != "manual":
                self._send(HTTPStatus.CONFLICT, _json_error("provider_owned", "ofertas automáticas só podem ser alteradas pelo provider"))
                return
            if "external_id" in payload and str(payload.get("external_id") or "").strip() != row["external_id"]:
                self._send(HTTPStatus.BAD_REQUEST, _json_error("identity_immutable", "external_id não pode ser alterado"))
                return
            current = json.loads(row["data_json"])
            data = _validate_manual_payload(payload, current)
            data["external_id"] = row["external_id"]
            if data["status"] in {"published", "archived"} and not _has_role(session, "admin"):
                with DB.transaction() as conn:
                    _audit(conn, self, session["user_id"], "authz.denied", "offer", offer_id, {"reason": "publish_or_archive"})
                self._send(HTTPStatus.FORBIDDEN, _json_error("forbidden", "publicar ou arquivar exige papel admin"))
                return
            if not _has_role(session, "admin") and (row["status"] != "draft" or data["status"] != "draft"):
                with DB.transaction() as conn:
                    _audit(conn, self, session["user_id"], "authz.denied", "offer", offer_id, {"reason": "non_draft_edit"})
                self._send(HTTPStatus.FORBIDDEN, _json_error("forbidden", "somente admin pode alterar oferta fora de rascunho"))
                return
            manual = _manual_row(data)
            with DB.transaction() as conn:
                conn.execute(
                    """UPDATE offers SET title=?, destination=?, origin_city=?, origin_airport=?, origin_bucket=?,
                      category_site=?, offer_type=?, departure_date=?, sort_date=?, sort_price=?, status=?,
                      data_json=?, rendered_html=?, updated_at=datetime('now') WHERE id=?""",
                    (manual["title"], manual["destination"], manual["origin_city"], manual["origin_airport"],
                     manual["origin_bucket"], manual["category_site"], manual["offer_type"], manual["departure_date"],
                     manual["sort_date"], manual["sort_price"], manual["status"], manual["data_json"],
                      manual["rendered_html"], offer_id),
                )
                conn.execute(
                    "INSERT INTO offer_history(offer_id, change_type, before_json, after_json) VALUES (?, 'updated', ?, ?)",
                    (
                        offer_id,
                        json.dumps(dict(row), ensure_ascii=False, default=str, sort_keys=True),
                        json.dumps({**manual, "id": offer_id, "sync_state": "current"}, ensure_ascii=False, sort_keys=True),
                    ),
                )
                action = {
                    "published": "offer.published",
                    "archived": "offer.archived",
                }.get(data["status"], "offer.updated")
                _audit(
                    conn,
                    self,
                    session["user_id"],
                    action,
                    "offer",
                    offer_id,
                    {"status_before": row["status"], "status_after": data["status"], "source": "manual"},
                )
            result = DB.one("SELECT * FROM offers WHERE id=?", (offer_id,))
            self._send(HTTPStatus.OK, offer_to_api(result, include_html=False))
        except LookupError:
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("validation_error", str(exc)))
        except Exception:
            LOG.exception("falha ao atualizar oferta administrativa")
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, _json_error("internal_error", "não foi possível atualizar a oferta"))

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/admin/offers/") and "/overrides/" in path:
            session = self._require_admin(csrf=True, required_role="admin")
            if not session:
                return
            parts = path.split("/")
            try:
                offer_id = int(parts[4])
                field = parts[6]
            except (IndexError, ValueError):
                self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_id", "id inválido"))
                return
            self._delete_override(offer_id, field, session)
            return
        if not path.startswith("/api/admin/offers/"):
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "rota não encontrada"))
            return
        session = self._require_admin(csrf=True, required_role="admin")
        if not session:
            return
        try:
            offer_id = int(path.rsplit("/", 1)[1])
        except ValueError:
            self._send(HTTPStatus.BAD_REQUEST, _json_error("invalid_id", "id inválido"))
            return
        row = DB.one("SELECT * FROM offers WHERE id=?", (offer_id,))
        if not row:
            self._send(HTTPStatus.NOT_FOUND, _json_error("not_found", "oferta não encontrada"))
            return
        if row["source"] != "manual":
            self._send(HTTPStatus.CONFLICT, _json_error("provider_owned", "ofertas automáticas não podem ser removidas pelo admin"))
            return
        with DB.transaction() as conn:
            conn.execute("UPDATE offers SET status='archived', updated_at=datetime('now') WHERE id=?", (offer_id,))
            conn.execute(
                "INSERT INTO offer_history(offer_id, change_type, before_json, after_json) VALUES (?, 'archived', ?, ?)",
                (
                    offer_id,
                    json.dumps(dict(row), ensure_ascii=False, default=str, sort_keys=True),
                    json.dumps({**dict(row), "status": "archived"}, ensure_ascii=False, default=str, sort_keys=True),
                ),
            )
            _audit(conn, self, session["user_id"], "offer.archived", "offer", offer_id, {"source": "manual"})
        self._send(HTTPStatus.OK, {"ok": True, "status": "archived"})


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    LOG.info("backend local ouvindo em http://%s:%s", HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("encerrando backend local")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
