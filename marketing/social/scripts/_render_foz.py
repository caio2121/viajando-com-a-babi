#!/usr/bin/env python3
"""Render only Foz do Iguaçu post + story."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright  # noqa: E402
from render_final_inspire import (  # noqa: E402
    BRAND,
    FORMATS,
    build_html,
    find_photo,
    prepare_photo,
    qa_texts,
)

SLUG = "foz-do-iguacu-2027"
CAMP = ROOT / "marketing" / "social" / "campaigns" / "2027" / "foz-do-iguacu"


def main() -> int:
    offer = json.loads((CAMP / "offer.json").read_text(encoding="utf-8"))
    logo = BRAND / "logo-vcb.png"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for fmt in ["post", "story"]:
            cw, ch = FORMATS[fmt]["w"], FORMATS[fmt]["h"]
            photo, msg = find_photo(CAMP, offer, cw, ch)
            if photo is None:
                print(f"SKIP {fmt}: {msg}")
                continue
            framed, note = prepare_photo(CAMP, photo, fmt, cw, ch)
            html = build_html(offer, framed, logo, fmt, cw, ch)
            (CAMP / "source").mkdir(exist_ok=True)
            (CAMP / "export").mkdir(exist_ok=True)
            html_path = CAMP / "source" / f"{SLUG}-{fmt}-final.html"
            png_path = CAMP / "export" / f"{SLUG}-{FORMATS[fmt]['suffix']}.png"
            html_path.write_text(html, encoding="utf-8")
            page = browser.new_page(
                viewport={"width": cw, "height": ch}, device_scale_factor=1
            )
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_timeout(400)
            ok, tnote = qa_texts(page, offer)
            if not ok:
                print(f"FAIL TEXT {fmt}: {tnote}")
                page.close()
                continue
            page.locator(".canvas").screenshot(path=str(png_path), type="png")
            page.close()
            print(f"OK {png_path.relative_to(ROOT)} ({msg} | {note} | {tnote})")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
