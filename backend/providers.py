from __future__ import annotations

import html
import hashlib
import json
import logging
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote

from .presentation import render_manual_package
from .storage import Database


LOG = logging.getLogger("vcb.providers")


class ProviderContractError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProviderAdapter(Protocol):
    name: str

    def normalize(self, kind: str, item: dict, rendered_html: str, display_order: int, is_highlight: bool) -> dict:
        ...


def _snapshot_checksum(payload: object) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _failed_sync(
    db: Database,
    sync_path: Path,
    code: str,
    message: str,
    checksum: str = "",
) -> None:
    with db.transaction() as conn:
        run = conn.execute(
            "INSERT INTO sync_runs(provider, source_reference, status, details_json, snapshot_checksum) "
            "VALUES (?, ?, 'failed', ?, ?)",
            (
                CativaAdapter.name,
                str(sync_path),
                json.dumps({"error_code": code, "message": message}, ensure_ascii=False),
                checksum,
            ),
        )
        conn.execute(
            "UPDATE sync_runs SET finished_at=datetime('now') WHERE id=?",
            (run.lastrowid,),
        )


def _staging_external_id(kind: str, item: object, index: int, seen: set[str]) -> str:
    candidate = _external_id(item)
    if not candidate:
        return f"__invalid__:{kind}:{index}"
    if candidate not in seen:
        return candidate
    return f"{candidate}#duplicate:{index}"


def _external_id(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("fingerprint") or item.get("id") or "").strip()


def _variant_external_id(candidate: str, item: object, index: int) -> str:
    canonical = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{candidate}#variant:{digest}:{index}"


class CativaAdapter:
    """Adapter para o formato atual, sem deixar esse formato vazar para a API."""

    name = "cativa"
    contract_version = "cativa-v1"
    allowed_fields = frozenset({
        "additional_dates", "airfare_original_price", "airfare_sale_price", "airline", "capa",
        "categoria_site", "category", "chd", "currency", "de", "departure_date", "departure_dates",
        "departure_time", "desconto", "destination", "destination_airport", "destination_type", "evento",
        "exclusivo", "fees", "fingerprint", "flight_included", "fornecedor", "hoteis", "hotel", "id",
        "inclui", "installment_count", "installment_value", "installments", "last_seats", "nights", "nota",
        "origin_airport", "origin_bucket", "origin_city", "package_total_price", "pacote_categoria",
        "periodo_hospedagem", "periodo_venda", "por", "price", "price_source", "return_date", "return_time",
        "seats", "sort_date", "sort_price", "source_slug", "tax", "taxas", "tipo", "title", "total_price",
    })
    manual_protected_fields = frozenset({
        "title", "destination", "origin_city", "origin_airport", "origin_bucket",
        "departure_date", "sort_date", "sort_price", "currency", "status", "data_json",
        "rendered_html",
    })

    def validate(self, kind: str, item: dict) -> None:
        if not isinstance(item, dict):
            raise ProviderContractError("invalid_record", "registro automático deve ser um objeto")
        unknown = sorted(set(item) - self.allowed_fields)
        if unknown:
            raise ProviderContractError(
                "schema_drift",
                f"schema do provider incompatível; campos desconhecidos: {', '.join(unknown[:8])}",
            )
        if kind not in {"pacote", "promo-voo", "campanha"}:
            raise ProviderContractError("invalid_kind", "tipo de oferta não suportado pelo provider")

    def normalize(self, kind: str, item: dict, rendered_html: str, display_order: int, is_highlight: bool) -> dict:
        self.validate(kind, item)
        external_id = _external_id(item)
        if not external_id:
            raise ProviderContractError("missing_external_id", "registro automático sem identificador externo")
        title = str(item.get("title") or item.get("destination") or "").strip()
        if not title:
            raise ProviderContractError("missing_title", "registro automático sem título ou destino")
        raw_price = item.get("sort_price")
        if raw_price not in (None, ""):
            try:
                price = float(raw_price)
            except (TypeError, ValueError) as exc:
                raise ProviderContractError("invalid_price", "preço normalizado inválido") from exc
            if not math.isfinite(price) or price < 0:
                raise ProviderContractError("invalid_price", "preço normalizado inválido")
        return {
            "source": "operator",
            "provider": self.name,
            "external_id": external_id,
            "kind": kind,
            "title": title,
            "destination": str(item.get("destination") or ""),
            "origin_city": str(item.get("origin_city") or ""),
            "origin_airport": str(item.get("origin_airport") or item.get("destination_airport") or ""),
            "origin_bucket": str(item.get("origin_bucket") or "").replace("_", "-"),
            "category_site": str(item.get("categoria_site") or item.get("category") or ""),
            "offer_type": str(item.get("tipo") or ""),
            "departure_date": str(item.get("departure_date") or ""),
            "sort_date": str(item.get("sort_date") or ""),
            "sort_price": raw_price,
            "currency": str(item.get("currency") or "BRL"),
            "status": "published",
            "is_highlight": int(is_highlight),
            "display_order": display_order,
            "data_json": json.dumps(item, ensure_ascii=False, sort_keys=True),
            "rendered_html": rendered_html,
        }


ARTICLE_RE = re.compile(r"<article\b[\s\S]*?</article>", re.I)
SOURCE_ID_RE = re.compile(r'\bdata-source-id="([^"]+)"', re.I)


def _html_map(paths: list[Path]) -> tuple[dict[str, str], dict[str, int]]:
    result: dict[str, str] = {}
    order: dict[str, int] = {}
    sequence = 0
    for path in paths:
        if not path.exists():
            continue
        for article in ARTICLE_RE.findall(path.read_text(encoding="utf-8")):
            match = SOURCE_ID_RE.search(article)
            if not match:
                continue
            source_id = unquote(html.unescape(match.group(1)))
            result[source_id] = article
            order.setdefault(source_id, sequence)
            sequence += 1
    return result, order


def _schema_fingerprint(keys: set[str]) -> str:
    canonical = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:16]


def _home_ids(path: Path) -> tuple[set[str], dict[str, int]]:
    if not path.exists():
        return set(), {}
    ids: set[str] = set()
    order: dict[str, int] = {}
    for index, article in enumerate(ARTICLE_RE.findall(path.read_text(encoding="utf-8"))):
        match = SOURCE_ID_RE.search(article)
        if match:
            source_id = unquote(html.unescape(match.group(1)))
            ids.add(source_id)
            order[source_id] = index
    return ids, order


def import_sync(db: Database, root: Path, sync_path: Path | None = None) -> dict:
    sync_path = sync_path or root / "data" / "operator-sync.json"
    try:
        raw_payload = sync_path.read_text(encoding="utf-8")
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        _failed_sync(db, sync_path, "malformed_snapshot", "snapshot JSON inválido")
        raise ValueError("snapshot do provider inválido") from exc
    except (OSError, UnicodeDecodeError) as exc:
        _failed_sync(db, sync_path, "snapshot_unavailable", "snapshot não pôde ser lido ou decodificado")
        raise ValueError("snapshot do provider indisponível") from exc
    checksum = _snapshot_checksum(payload)
    if not isinstance(payload, dict):
        _failed_sync(db, sync_path, "invalid_snapshot", "snapshot deve ser um objeto")
        raise ValueError("snapshot inválido")
    offers = payload.get("offers") or {}
    if not isinstance(offers, dict):
        _failed_sync(db, sync_path, "invalid_snapshot", "grupos do snapshot devem ser listas", checksum)
        raise ValueError("snapshot inválido")
    groups = {
        "pacote": offers.get("pacotes") or [],
        "promo-voo": offers.get("promo_voos") or [],
        "campanha": offers.get("campanhas") or [],
    }
    if any(not isinstance(items, list) for items in groups.values()):
        _failed_sync(db, sync_path, "invalid_snapshot", "grupos do snapshot devem ser listas", checksum)
        raise ValueError("snapshot inválido")
    html_map, generated_order = _html_map(
        [
            root / "data" / "generated" / "pacotes-sync.html",
            root / "data" / "generated" / "promo-voos-cards.html",
            root / "data" / "generated" / "campanhas-cards.html",
            root / "pacotes.html",
            root / "promo-voos.html",
            root / "campanhas.html",
        ]
    )
    home_ids, home_order = _home_ids(root / "index.html")
    adapter = CativaAdapter()
    started = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with db.transaction() as conn:
        run = conn.execute(
            "INSERT INTO sync_runs(provider, source_reference, status, details_json, snapshot_checksum, started_at) "
            "VALUES (?, ?, 'started', ?, ?, ?)",
            (
                adapter.name,
                str(payload.get("source") or ""),
                json.dumps({"sync": str(sync_path)}, ensure_ascii=False),
                checksum,
                started,
            ),
        )
        run_id = run.lastrowid
        contract_error: ProviderContractError | None = None
        if not any(groups.values()):
            conn.execute(
                "UPDATE sync_runs SET status='failed', details_json=?, finished_at=datetime('now') WHERE id=?",
                (json.dumps({
                    "error_code": "empty_snapshot",
                    "message": "snapshot vazio; dados persistidos anteriores foram preservados",
                    "contract_version": adapter.contract_version,
                }, ensure_ascii=False), run_id),
            )
            contract_error = ProviderContractError(
                "empty_snapshot",
                "sync vazio; os dados persistidos anteriores foram preservados",
            )
        normalized: list[dict] = []
        staged: list[dict] = []
        seen_external_ids: set[str] = set()
        schema_keys: set[str] = set()
        for kind, items in groups.items():
            for index, item in enumerate(items):
                candidate = _external_id(item)
                duplicate = bool(candidate and candidate in seen_external_ids)
                duplicate_variant = duplicate and isinstance(item, dict) and bool(item.get("fingerprint"))
                external_id = (
                    _variant_external_id(candidate, item, index)
                    if duplicate_variant
                    else _staging_external_id(kind, item, index, seen_external_ids)
                )
                seen_external_ids.add(candidate or external_id)
                staging = conn.execute(
                    "INSERT INTO sync_run_items(sync_run_id, external_id, status, details_json) VALUES (?, ?, 'received', ?)",
                    (run_id, external_id, json.dumps({"kind": kind, "index": index}, ensure_ascii=False)),
                )
                staged.append({
                    "id": staging.lastrowid,
                    "kind": kind,
                    "item": item,
                    "external_id": external_id,
                    "duplicate": duplicate,
                    "duplicate_variant": duplicate_variant,
                })
        current_record_id: int | None = None
        try:
            for record in staged:
                current_record_id = record["id"]
                kind = record["kind"]
                item = record["item"]
                source_id = _external_id(item)
                source_aliases = [source_id]
                if isinstance(item, dict):
                    source_aliases.extend(str(item.get(key) or "").strip() for key in ("id", "fingerprint"))
                source_aliases = list(dict.fromkeys(alias for alias in source_aliases if alias))
                rendered_html = next((html_map.get(alias, "") for alias in source_aliases if html_map.get(alias)), "")
                display_order = next(
                    (home_order[alias] for alias in source_aliases if alias in home_order),
                    next((generated_order[alias] for alias in source_aliases if alias in generated_order), 999999),
                )
                is_highlight = any(alias in home_ids for alias in source_aliases)
                if record["duplicate"] and not record["duplicate_variant"]:
                    raise ProviderContractError("duplicate_external_id", "identificador externo duplicado no snapshot")
                adapter.validate(kind, item)
                schema_keys.update(item)
                normalized_row = adapter.normalize(
                    kind,
                    item,
                    rendered_html,
                    display_order,
                    is_highlight,
                )
                if record["duplicate_variant"]:
                    normalized_row["external_id"] = record["external_id"]
                normalized.append(normalized_row)
                conn.execute(
                    "UPDATE sync_run_items SET status='validated', details_json=? WHERE id=?",
                    (json.dumps({"kind": kind, "external_id": source_id}, ensure_ascii=False), record["id"]),
                )
        except ProviderContractError as exc:
            details = {
                "error_code": exc.code,
                "message": str(exc),
                "contract_version": adapter.contract_version,
            }
            conn.execute(
                "UPDATE sync_runs SET status='failed', details_json=?, finished_at=datetime('now') WHERE id=?",
                (json.dumps(details, ensure_ascii=False), run_id),
            )
            conn.execute(
                "UPDATE sync_run_items SET status='rejected', error_code=CASE WHEN error_code='' THEN 'batch_rejected' ELSE error_code END "
                "WHERE sync_run_id=? AND status IN ('received', 'validated')",
                (run_id,),
            )
            if current_record_id is not None:
                conn.execute(
                    "UPDATE sync_run_items SET error_code=?, details_json=? WHERE id=?",
                    (exc.code, json.dumps({"error": str(exc)}, ensure_ascii=False), current_record_id),
                )
            LOG.error("provider contract rejected: provider=%s code=%s", adapter.name, exc.code)
            contract_error = exc
        if contract_error is None:
            counts = {"created": 0, "updated": 0, "total": len(normalized)}
            fingerprint = _schema_fingerprint(schema_keys)
            for row in normalized:
                manual_conflict = conn.execute(
                    "SELECT id FROM offers WHERE source='manual' AND external_id=?",
                    (row["external_id"],),
                ).fetchone()
                if manual_conflict:
                    conflict = ProviderContractError(
                        "ownership_conflict",
                        "identificador do provider pertence a uma oferta manual",
                    )
                    conn.execute(
                        "UPDATE sync_runs SET status='failed', details_json=?, finished_at=datetime('now') WHERE id=?",
                        (json.dumps({
                            "error_code": conflict.code,
                            "message": str(conflict),
                            "contract_version": adapter.contract_version,
                            "external_id": row["external_id"],
                        }, ensure_ascii=False), run_id),
                    )
                    conn.execute(
                        "UPDATE sync_run_items SET status='rejected', error_code=CASE WHEN error_code='' THEN 'batch_rejected' ELSE error_code END "
                        "WHERE sync_run_id=? AND status IN ('received', 'validated')",
                        (run_id,),
                    )
                    LOG.error("provider ownership conflict: provider=%s", adapter.name)
                    contract_error = conflict
                    break
            if contract_error is None:
                for record, row in zip(staged, normalized):
                    existing = conn.execute(
                        "SELECT * FROM offers WHERE provider=? AND external_id=?",
                        (row["provider"], row["external_id"]),
                    ).fetchone()
                    conn.execute(
                        """INSERT INTO offers(
                            source, provider, external_id, kind, title, destination, origin_city,
                            origin_airport, origin_bucket, category_site, offer_type, departure_date,
                            sort_date, sort_price, currency, status, is_highlight, display_order,
                            data_json, rendered_html, sync_state, updated_at
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                        ON CONFLICT(provider, external_id) DO UPDATE SET
                            source=excluded.source, kind=excluded.kind, title=excluded.title,
                            destination=excluded.destination, origin_city=excluded.origin_city,
                            origin_airport=excluded.origin_airport, origin_bucket=excluded.origin_bucket,
                            category_site=excluded.category_site, offer_type=excluded.offer_type,
                            departure_date=excluded.departure_date, sort_date=excluded.sort_date,
                            sort_price=excluded.sort_price, currency=excluded.currency,
                            status='published', is_highlight=excluded.is_highlight,
                            display_order=excluded.display_order, data_json=excluded.data_json,
                            rendered_html=excluded.rendered_html, sync_state='current', updated_at=datetime('now')""",
                        (
                            row["source"], row["provider"], row["external_id"], row["kind"], row["title"],
                            row["destination"], row["origin_city"], row["origin_airport"], row["origin_bucket"],
                            row["category_site"], row["offer_type"], row["departure_date"], row["sort_date"],
                            row["sort_price"], row["currency"], row["status"], row["is_highlight"],
                            row["display_order"], row["data_json"], row["rendered_html"], "current",
                        ),
                    )
                    if existing is None:
                        counts["created"] += 1
                        offer_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                        before = {}
                        change_type = "created"
                    else:
                        offer_id = existing["id"]
                        before = dict(existing)
                        if (
                            existing["data_json"] != row["data_json"]
                            or existing["rendered_html"] != row["rendered_html"]
                            or existing["sync_state"] != "current"
                        ):
                            counts["updated"] += 1
                        change_type = "synced"
                    after = {
                        **row,
                        "id": offer_id,
                        "sync_state": "current",
                    }
                    conn.execute(
                        "INSERT INTO offer_history(offer_id, sync_run_id, change_type, before_json, after_json) VALUES (?, ?, ?, ?, ?)",
                        (
                            offer_id,
                            run_id,
                            change_type,
                            json.dumps(before, ensure_ascii=False, default=str, sort_keys=True),
                            json.dumps(after, ensure_ascii=False, default=str, sort_keys=True),
                        ),
                    )
                    conn.execute(
                        "UPDATE sync_run_items SET status='imported', offer_id=? WHERE id=?",
                        (offer_id, record["id"]),
                    )
                imported_ids = {row["external_id"] for row in normalized}
                stale_rows = conn.execute(
                    "SELECT * FROM offers WHERE source='operator' AND provider=? AND sync_state='current'",
                    (adapter.name,),
                ).fetchall()
                stale_count = 0
                for stale in stale_rows:
                    if stale["external_id"] in imported_ids:
                        continue
                    conn.execute(
                        "UPDATE offers SET sync_state='stale', updated_at=datetime('now') WHERE id=?",
                        (stale["id"],),
                    )
                    conn.execute(
                        "INSERT INTO sync_run_items(sync_run_id, offer_id, external_id, status, details_json) VALUES (?, ?, ?, 'removed', ?)",
                        (
                            run_id,
                            stale["id"],
                            stale["external_id"],
                            json.dumps({"reason": "missing_from_snapshot", "action": "mark_stale"}, ensure_ascii=False),
                        ),
                    )
                    conn.execute(
                        "INSERT INTO offer_history(offer_id, sync_run_id, change_type, before_json, after_json) VALUES (?, ?, 'synced', ?, ?)",
                        (
                            stale["id"],
                            run_id,
                            json.dumps(dict(stale), ensure_ascii=False, default=str, sort_keys=True),
                            json.dumps({**dict(stale), "sync_state": "stale"}, ensure_ascii=False, default=str, sort_keys=True),
                        ),
                    )
                    stale_count += 1
                conn.execute(
                    "UPDATE sync_runs SET status='success', imported_count=?, details_json=?, finished_at=datetime('now') WHERE id=?",
                    (
                        len(normalized),
                        json.dumps({
                            **counts,
                            "stale": stale_count,
                            "contract_version": adapter.contract_version,
                            "schema_fingerprint": fingerprint,
                            "snapshot_checksum": checksum,
                        }, ensure_ascii=False),
                        run_id,
                    ),
                )
    if contract_error is not None:
        raise contract_error
    return counts


def offer_to_api(row, include_html: bool = True, include_data: bool = True) -> dict:
    data = dict(row)
    overrides = {}
    try:
        encoded_overrides = json.loads(data.get("overrides_json") or "{}")
        for field, encoded_value in encoded_overrides.items():
            try:
                overrides[field] = json.loads(encoded_value) if isinstance(encoded_value, str) else encoded_value
            except (TypeError, json.JSONDecodeError):
                continue
    except (TypeError, json.JSONDecodeError):
        overrides = {}
    for field in ("is_highlight", "display_order"):
        if field in overrides:
            data[field] = overrides[field]
    result = {
        "id": data["id"],
        "source": data["source"],
        "provider": data["provider"],
        "external_id": data["external_id"],
        "kind": data["kind"],
        "title": data["title"],
        "destination": data["destination"],
        "origin_city": data["origin_city"],
        "origin_airport": data["origin_airport"],
        "origin_bucket": data["origin_bucket"],
        "status": data["status"],
        "sync_state": data.get("sync_state", "current"),
        "override_fields": sorted(overrides),
        "is_highlight": bool(data["is_highlight"]),
        "display_order": data["display_order"],
        "sort_date": data["sort_date"],
        "sort_price": data["sort_price"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
    }
    if include_html:
        result["html"] = data["rendered_html"]
    if include_data:
        try:
            parsed_data = json.loads(data["data_json"])
            result["data"] = parsed_data if isinstance(parsed_data, dict) else {}
            result["data"].update({field: value for field, value in overrides.items() if field not in {"is_highlight", "display_order"}})
        except (TypeError, json.JSONDecodeError):
            result["data"] = {}
    return result


def offer_select_sql(alias: str = "o") -> str:
    if alias != "o":
        raise ValueError("alias de oferta inválido")
    return """SELECT o.*, COALESCE((
        SELECT json_group_object(field_name, value_json)
        FROM (
            SELECT field_name, value_json
            FROM offer_overrides
            WHERE offer_id=o.id AND deleted_at IS NULL
            ORDER BY id ASC
        )
    ), '{}') AS overrides_json FROM offers o"""


__all__ = ["CativaAdapter", "import_sync", "offer_to_api", "offer_select_sql", "render_manual_package"]
