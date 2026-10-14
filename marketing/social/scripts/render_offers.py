#!/usr/bin/env python3
"""Render Instagram POST/STORY creatives from offer.json + HTML templates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SOCIAL = ROOT / "marketing" / "social"
TEMPLATES = SOCIAL / "templates"
BRAND = SOCIAL / "brand"

POST_SIZE = (1080, 1350)
STORY_SIZE = (1080, 1920)


def load_offer(campaign_dir: Path) -> dict:
    path = campaign_dir / "offer.json"
    if not path.exists():
        raise FileNotFoundError(f"offer.json não encontrado em {campaign_dir}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def fill(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, value in mapping.items():
        out = out.replace("{{ " + key + " }}", value)
        out = out.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", out)
    if leftover:
        raise ValueError(f"Placeholders não preenchidos: {leftover}")
    return out


def destination_html(offer: dict) -> str:
    if offer.get("destination_html"):
        return offer["destination_html"]
    dest = offer["destination"]
    if "+" in dest:
        parts = [p.strip() for p in dest.split("+")]
        if len(parts) == 2:
            return (
                f'{escape(parts[0])}'
                f'<span class="plus">+ {escape(parts[1])}</span>'
            )
    return escape(dest)


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def photo_luminance(photo_path: Path) -> float:
    """Average perceived luminance 0-255 of the photo."""
    from PIL import Image

    with Image.open(photo_path) as im:
        rgb = im.convert("RGB").resize((64, 64))
        pixels = list(rgb.getdata())
    if not pixels:
        return 128.0
    return sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels) / len(pixels)


def resolve_logo(offer: dict, photo_path: Path) -> tuple[str, str, Path]:
    """
    Returns (mode, filename, path).

    Em barra/fundo branco: sempre o logo padrão (logo-vcb), sem placa/círculo extra.
    Em fundo escuro da foto (se logo solto): texto claro.
    """
    forced = offer.get("logo_mode") or offer.get("logo")
    if forced in {"dark-on-light", "on-light", "official", "standard", "white"}:
        mode = "standard"
    elif forced == "light-text":
        mode = "light-text"
    elif forced and str(forced).endswith((".png", ".PNG", ".webp")):
        return "custom", forced, (BRAND / forced).resolve()
    else:
        # Rodapé das artes é branco: preferir logo padrão.
        # light-text só se explicitamente pedido.
        mode = "standard"

    mapping = {
        "standard": "logo-vcb.png",
        "official": "logo-vcb.png",
        "white": "logo-white-bg.png",
        "light-text": "logo-light-text.png",
        "dark-text": "logo-dark-text.png",
    }
    name = mapping.get(mode, mapping["standard"])
    return mode, name, (BRAND / name).resolve()


def build_context(
    offer: dict,
    campaign_dir: Path,
    fmt: str,
    layout: str = "v2",
) -> dict[str, str]:
    photo = offer["photo"]
    photo_file = photo["file"]
    photo_path = (campaign_dir / "assets" / photo_file).resolve()
    if not photo_path.exists():
        raise FileNotFoundError(photo_path)

    logo_mode, logo_name, logo_path = resolve_logo(offer, photo_path)
    watermark_path = (BRAND / "logo-mark.png").resolve()

    includes = offer.get("includes") or []
    includes_html = "".join(
        (
            "<li>"
            '<span class="check" aria-hidden="true">✓</span>'
            f'<span class="label">{escape(item)}</span>'
            "</li>"
        )
        for item in includes[:4]
    )

    payment = offer.get("payment") or []
    if payment:
        payment_html = "<p class=\"payment\">" + "<br />".join(escape(p) for p in payment) + "</p>"
    else:
        payment_html = ""

    disclaimer = offer.get("disclaimer")
    disclaimer_html = f'<p class="disclaimer">{escape(disclaimer)}</p>' if disclaimer else ""

    hotel = offer.get("hotel")
    hotel_html = f'<p class="hotel">{escape(hotel)}</p>' if hotel else ""

    eyebrow = offer.get("eyebrow")
    eyebrow_html = f'<span class="eyebrow">{escape(eyebrow)}</span>' if eyebrow else "<span></span>"

    variant = offer.get("variant", "standard")
    premium_class = " canvas--premium" if variant == "premium" else ""

    pos_key = f"object_position_{fmt}"
    object_position = photo.get(pos_key) or photo.get("object_position") or "center center"

    if layout == "v1":
        css_href = file_url(TEMPLATES / "v1" / "creative.css")
    else:
        css_href = file_url(TEMPLATES / "creative.css")

    return {
        "title": escape(offer.get("destination", offer["slug"])),
        "css_href": css_href,
        "photo_src": file_url(photo_path),
        "photo_alt": escape(offer.get("photo_alt") or offer["destination"]),
        "object_position": escape(object_position),
        "logo_src": file_url(logo_path),
        "logo_mode": escape(logo_mode),
        "watermark_src": file_url(watermark_path),
        "eyebrow_html": eyebrow_html,
        "hotel_html": hotel_html,
        "destination_html": destination_html(offer),
        "tagline": escape(offer.get("tagline", "")),
        "date_display": escape(offer["date_display"]),
        "includes_html": includes_html,
        "price_value": escape(offer["price"]["value"]),
        "price_unit": escape(offer["price"]["unit"]),
        "payment_html": payment_html,
        "cta": escape(offer.get("cta", "Falar no WhatsApp")),
        "disclaimer_html": disclaimer_html,
        "premium_class": premium_class,
    }


def resolve_layout(suffix: str) -> str:
    """Map file suffix to template layout. v1 = cards/tarja; v2 = editorial."""
    if suffix in {"", "none", "v1"}:
        return "v1"
    return "v2"


def render_campaign(
    campaign_dir: Path,
    formats: list[str] | None = None,
    suffix: str = "v2",
) -> list[Path]:
    offer = load_offer(campaign_dir)
    slug = offer["slug"]
    wanted = formats or offer.get("formats") or ["post", "story"]
    export_dir = campaign_dir / "export"
    source_dir = campaign_dir / "source"
    export_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    layout = resolve_layout(suffix)
    tpl_dir = TEMPLATES / "v1" if layout == "v1" else TEMPLATES

    outputs: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for fmt in wanted:
            tpl_name = "post.html" if fmt == "post" else "story.html"
            template = (tpl_dir / tpl_name).read_text(encoding="utf-8")
            ctx = build_context(offer, campaign_dir, fmt, layout=layout)
            html = fill(template, {k: v for k, v in ctx.items() if not k.startswith("_")})
            tag = f"-{suffix}" if suffix else ""
            source_path = source_dir / f"{slug}-{fmt}{tag}.html"
            source_path.write_text(html, encoding="utf-8")

            width, height = (POST_SIZE if fmt == "post" else STORY_SIZE)
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto(source_path.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_timeout(450)
            out_name = f"{slug}-{fmt}-{width}x{height}{tag}.png"
            out_path = export_dir / out_name
            page.locator(".canvas").screenshot(path=str(out_path), type="png")
            page.close()
            outputs.append(out_path)
            print(f"OK [{layout}] {out_path.relative_to(ROOT)}")
        browser.close()
    return outputs


def discover_campaigns(base: Path) -> list[Path]:
    return sorted({p.parent for p in base.rglob("offer.json")})


def main() -> int:
    parser = argparse.ArgumentParser(description="Render social travel offer creatives")
    parser.add_argument("--campaign", type=Path, help="Pasta da campanha com offer.json")
    parser.add_argument("--all", action="store_true", help="Renderiza todas as campanhas")
    parser.add_argument("--format", choices=["post", "story"], action="append")
    parser.add_argument(
        "--suffix",
        default="v2",
        help="Sufixo e layout: v2=editorial; v1 ou none=tarja/cards (arquivo sem sufixo).",
    )
    args = parser.parse_args()

    if args.all:
        camps = discover_campaigns(SOCIAL / "campaigns")
    elif args.campaign:
        camps = [args.campaign.resolve()]
    else:
        parser.error("Use --campaign PATH ou --all")
        return 2

    suffix = "" if args.suffix in {"", "-", "none"} else args.suffix
    for camp in camps:
        render_campaign(camp, args.format, suffix=suffix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
