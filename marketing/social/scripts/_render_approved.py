#!/usr/bin/env python3
"""Render only campaigns with qa_marketing APROVAR."""

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
    discover_campaigns,
    find_photo,
    prepare_photo,
    qa_texts,
)

APPROVED = {
    "essenza-dune-jericoacoara-mai-2027",
    "foz-do-iguacu-2027",
    "jalapao-encantador-2027",
    "jericoacoara-mai-2027",
    "porto-de-galinhas-2027",
}


def main() -> int:
    logo = BRAND / "logo-vcb.png"
    ok_n = 0
    fail_n = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for camp in discover_campaigns():
            offer = json.loads((camp / "offer.json").read_text(encoding="utf-8"))
            slug = offer["slug"]
            if slug not in APPROVED:
                continue
            for fmt in offer.get("formats") or ["post", "story"]:
                if fmt not in FORMATS:
                    continue
                cw, ch = FORMATS[fmt]["w"], FORMATS[fmt]["h"]
                photo, msg = find_photo(camp, offer, cw, ch)
                if photo is None:
                    print(f"SKIP {slug}/{fmt}: {msg}")
                    fail_n += 1
                    continue
                framed, note = prepare_photo(camp, photo, fmt, cw, ch)
                html = build_html(offer, framed, logo, fmt, cw, ch)
                (camp / "source").mkdir(exist_ok=True)
                (camp / "export").mkdir(exist_ok=True)
                html_path = camp / "source" / f"{slug}-{fmt}-final.html"
                png_path = camp / "export" / f"{slug}-{FORMATS[fmt]['suffix']}.png"
                html_path.write_text(html, encoding="utf-8")
                page = browser.new_page(
                    viewport={"width": cw, "height": ch}, device_scale_factor=1
                )
                page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
                page.wait_for_timeout(400)
                ok_txt, tnote = qa_texts(page, offer)
                if not ok_txt:
                    print(f"FAIL TEXT {slug}/{fmt}: {tnote}")
                    page.close()
                    fail_n += 1
                    continue
                page.locator(".canvas").screenshot(path=str(png_path), type="png")
                page.close()
                print(
                    f"OK {png_path.relative_to(ROOT)} ({msg} | {note} | {tnote})"
                )
                ok_n += 1
        browser.close()
    print(f"\n=== {ok_n} OK / {fail_n} FAIL ===")
    return 0 if fail_n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
