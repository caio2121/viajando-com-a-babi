"""Carrega somente configuração pública usada pelo bundle estático."""
from __future__ import annotations

import json
import os
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUBLIC_CONFIG_PATH = ROOT / "config" / "site-config.json"
REQUIRED_KEYS = {
    "brand_name", "public_base_url", "whatsapp_number", "whatsapp_display", "whatsapp_message",
    "instagram_url", "contact_email", "logo_path", "ga4_measurement_id", "ads_id", "ads_conversion",
    "provider_source_url",
}


def load_public_config(path: str | Path | None = None) -> dict[str, str]:
    configured = Path(path or os.environ.get("VCB_PUBLIC_CONFIG") or PUBLIC_CONFIG_PATH)
    config = json.loads(configured.read_text(encoding="utf-8"))
    optional_tracker_keys = {"ga4_measurement_id", "ads_id", "ads_conversion"}
    if set(config) != REQUIRED_KEYS or any(
        not isinstance(value, str) or (not value.strip() and key not in optional_tracker_keys)
        for key, value in config.items()
    ):
        raise ValueError("configuração pública incompleta ou inválida")
    if not config["whatsapp_number"].isdigit():
        raise ValueError("whatsapp_number inválido")
    if not config["public_base_url"].startswith("https://"):
        raise ValueError("public_base_url deve usar HTTPS")
    return config


def template_values(config: dict[str, str]) -> dict[str, str]:
    values = dict(config)
    values.update({
        "WHATSAPP_URL": "https://wa.me/" + config["whatsapp_number"] + "?text=" + urllib.parse.quote(config["whatsapp_message"]),
        "WHATSAPP_NUMBER": config["whatsapp_number"],
        "WHATSAPP_DISPLAY": config["whatsapp_display"],
        "INSTAGRAM_URL": config["instagram_url"],
        "CONTACT_EMAIL": config["contact_email"],
        "GA4_MEASUREMENT_ID": config["ga4_measurement_id"],
        "ADS_ID": config["ads_id"],
        "ADS_CONVERSION": config["ads_conversion"],
        "PROVIDER_SOURCE_URL": config["provider_source_url"],
    })
    return values


def render_public_template(text: str, config: dict[str, str] | None = None) -> str:
    for key, value in template_values(config or load_public_config()).items():
        text = text.replace("{{" + key + "}}", value)
    return text


def public_replacements(baseline: dict[str, str], config: dict[str, str]) -> dict[str, str]:
    """Mapeia valores legados do HTML estático para a configuração aprovada."""
    old_values = template_values(baseline)
    new_values = template_values(config)
    keys = (
        "brand_name", "public_base_url", "whatsapp_number", "whatsapp_display",
        "instagram_url", "contact_email", "logo_path", "WHATSAPP_URL",
        "GA4_MEASUREMENT_ID", "ADS_ID", "ADS_CONVERSION",
    )
    return {old_values[key]: new_values[key] for key in keys if old_values[key]}


def public_js(config: dict[str, str] | None = None) -> str:
    values = config or load_public_config()
    public = {key: values[key] for key in (
        "brand_name", "public_base_url", "whatsapp_number", "instagram_url", "contact_email", "logo_path",
        "ga4_measurement_id", "ads_id", "ads_conversion",
    )}
    return "window.VCB_CONFIG = " + json.dumps(public, ensure_ascii=False, separators=(",", ":")) + ";\n"
