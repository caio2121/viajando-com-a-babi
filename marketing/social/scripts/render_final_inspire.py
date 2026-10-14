#!/usr/bin/env python3
"""Render POST + STORY finais (centrado + baloes).

QA:
1) alta resolucao (cover scale <= 1.10)
2) enquadramento (smart-crop se ceu/noite vazios)
3) textos da arte vs offer.json (DOM + checklist)
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SOCIAL = ROOT / "marketing" / "social"
BRAND = SOCIAL / "brand"
CAMPAIGNS = SOCIAL / "campaigns"

FORMATS = {
    "post": {"w": 1080, "h": 1350, "suffix": "post-1080x1350-final"},
    "story": {"w": 1080, "h": 1920, "suffix": "story-1080x1920-final"},
}
MAX_COVER_SCALE = 1.10
MAX_COVER_SCALE_STORY = 1.15
# Recorte inteligente a partir de foto ja hi-res pode zoomar um pouco mais
# para eliminar topo vazio (ceu/noite), sem aceitar fonte WhatsApp baixa.
FRAMED_MAX_COVER_SCALE = 1.25

PLANE = (
    '<svg viewBox="0 0 24 24" width="48" height="48" aria-hidden="true">'
    '<path fill="currentColor" d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>'
    "</svg>"
)
CAL = (
    '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">'
    '<path fill="currentColor" d="M19 4h-1V2h-2v2H8V2H6v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z"/>'
    "</svg>"
)
ICON_BED = (
    '<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">'
    '<path fill="currentColor" d="M7 13c1.66 0 3-1.34 3-3S8.66 7 7 7s-3 1.34-3 3 1.34 3 3 3zm12-6h-8v7H3V5H1v15h2v-3h18v3h2v-9c0-2.21-1.79-4-4-4z"/>'
    "</svg>"
)
ICON_BUS = (
    '<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">'
    '<path fill="currentColor" d="M4 16c0 .88.39 1.67 1 2.22V20a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-1h8v1a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm9 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zM6 10V6h12v4H6z"/>'
    "</svg>"
)
ICON_SHIELD = (
    '<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">'
    '<path fill="currentColor" d="M12 1 3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>'
    "</svg>"
)
ICON_CARD = (
    '<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">'
    '<path fill="currentColor" d="M20 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>'
    "</svg>"
)
ICON_COFFEE = (
    '<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">'
    '<path fill="currentColor" d="M2 21h18v-2H2v2zm6-4h10a4 4 0 0 0 0-8h-1V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h2zm8-6h2a2 2 0 1 1 0 4h-2V11z"/>'
    "</svg>"
)
ICON_FALLS = (
    '<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">'
    '<path fill="currentColor" d="M12 2c-1.5 3-4 5.5-4 9a4 4 0 1 0 8 0c0-3.5-2.5-6-4-9zm-6 14c-1 1.5-2 3-2 5h4c0-2-1-3.5-2-5zm6 0c-1 1.5-2 3-2 5h4c0-2-1-3.5-2-5zm6 0c-1 1.5-2 3-2 5h4c0-2-1-3.5-2-5z"/>'
    "</svg>"
)

PREFERRED_PHOTO = {
    "jericoacoara-mai-2027": "hero-hires-v2.jpg",
    "fortaleza-jericoacoara-2027": "hero-hires.jpg",
    "fortaleza-jericoacoara-fev-2027": "hero-hires.jpg",
    "aracaju": "hero-hires.jpg",
    "essenza-dune-jericoacoara-mai-2027": "hero-hires.jpg",
    "jalapao-encantador-2027": "hero-hires.jpg",
    "foz-do-iguacu-2027": "hero-hires-v2.jpg",
    "porto-de-galinhas-2027": "hero-hires.jpg",
    "natal-luz-gramado-2026": "hero-hires.jpg",
}


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def cover_scale(w: int, h: int, cw: int, ch: int) -> float:
    return max(cw / w, ch / h)


def is_hires(path: Path, cw: int, ch: int) -> tuple[bool, str]:
    if not path.exists():
        return False, "arquivo inexistente"
    if path.name == "hero.png" and "jericoacoara" in str(path).replace("\\", "/"):
        source = path.with_name("hero-source-whatsapp.png")
        if source.exists():
            return False, "hero.png e upscale artificial do WhatsApp"
    try:
        with Image.open(path) as im:
            w, h = im.size
    except Exception as e:
        return False, f"nao foi possivel ler a imagem ({e})"
    scale = cover_scale(w, h, cw, ch)
    limit = MAX_COVER_SCALE_STORY if ch >= 1800 else MAX_COVER_SCALE
    if scale > limit:
        return False, f"resolucao insuficiente ({w}x{h}; cover scale {scale:.2f} > {limit})"
    return True, f"{w}x{h} scale={scale:.2f}"


def find_photo(camp_dir: Path, offer: dict, cw: int, ch: int) -> tuple[Path | None, str]:
    assets = camp_dir / "assets"
    slug = offer["slug"]
    candidates: list[Path] = []
    photo_meta = offer.get("photo") or {}
    # Story: prioridade absoluta do file_story se hi-res
    if ch >= 1800 and photo_meta.get("file_story"):
        story_path = assets / photo_meta["file_story"]
        ok, msg = is_hires(story_path, cw, ch)
        if ok:
            return story_path.resolve(), msg
    preferred = PREFERRED_PHOTO.get(slug)
    if preferred:
        candidates.append(assets / preferred)
    photo_file = photo_meta.get("file")
    if photo_file:
        candidates.append(assets / photo_file)
    for name in (
        "hero-hires.jpg",
        "hero-hires.jpeg",
        "hero-hires.png",
        "hero-hires-alt.jpg",
        "hero-hires-panorama.jpg",
        "hero-hires-panorama.jpeg",
        "hero-framed-story.jpg",
        "hero-framed-post.jpg",
        "hero.jpeg",
        "hero.jpg",
        "hero.png",
    ):
        candidates.append(assets / name)

    for extra in sorted(assets.glob("hero*.jpg")) + sorted(assets.glob("hero*.jpeg")) + sorted(
        assets.glob("hero*.png")
    ):
        # evitar story REPROVADA (bairro/obra) se existir alternativa
        if extra.name == "hero-hires-story.jpg":
            continue
        candidates.append(extra)

    scored: list[tuple[float, Path, str]] = []
    seen: set[Path] = set()
    reasons: list[str] = []
    preferred_ok: tuple[Path, str] | None = None
    for cand in candidates:
        cand = cand.resolve()
        if cand in seen or not cand.exists():
            continue
        seen.add(cand)
        ok, msg = is_hires(cand, cw, ch)
        if not ok:
            reasons.append(f"{cand.name}: {msg}")
            continue
        with Image.open(cand) as im:
            w, h = im.size
        if "framed" in cand.name.lower():
            scored.append((cover_scale(w, h, cw, ch) + 5.0, cand, msg))
        else:
            scored.append((cover_scale(w, h, cw, ch), cand, msg))
        if preferred and cand.name == preferred and preferred_ok is None:
            preferred_ok = (cand, msg)
    if preferred_ok:
        return preferred_ok
    if scored:
        scored.sort(key=lambda t: t[0])
        return scored[0][1], scored[0][2]
    return None, "; ".join(reasons) if reasons else "nenhuma foto candidata"


def crop_interest_score(crop: Image.Image) -> float:
    """Penaliza topo vazio (ceu uniforme OU noite preta sem detalhe).

    Nao premiar brilho medio no topo (isso favorece ceu azul).
    Premiar variancia/detalhe e luzes pontuais (Natal Luz).
    """
    arr = np.asarray(crop.convert("RGB"), dtype=np.float32)
    h = arr.shape[0]
    tip = arr[: int(h * 0.22)]
    top = arr[: int(h * 0.40)]
    mid = arr[int(h * 0.25) : int(h * 0.72)]
    lower = arr[int(h * 0.55) :]

    tip_lum = tip.mean(axis=2)
    top_lum = top.mean(axis=2)
    tip_var = float(tip.var())
    top_var = float(top.var())
    mid_var = float(mid.var())
    lower_var = float(lower.var())

    b, g, r = top[:, :, 2], top[:, :, 1], top[:, :, 0]
    skyish = float(np.mean((b > r + 10) & (b > g + 3) & (b > 130) & (top_lum > 120)))
    tip_sky = float(
        np.mean(
            (tip[:, :, 2] > tip[:, :, 0] + 10)
            & (tip[:, :, 2] > tip[:, :, 1] + 3)
            & (tip_lum > 120)
        )
    )
    dark_empty = float(np.mean((top_lum < 42) & (top.std(axis=2) < 20)))
    tip_dark = float(np.mean(tip_lum < 35))
    # luzes pontuais (Natal): pixels bem mais claros que a mediana
    tip_med = float(np.median(tip_lum))
    tip_mean = float(tip_lum.mean())
    tip_lights = float(np.mean(tip_lum > tip_med + 55))
    tip_p90 = float(np.percentile(tip_lum, 90))

    # ceu uniforme: alto brilho + baixa variancia
    flat_bright = 1.0 if (tip_mean > 140 and tip_var < 1800) else 0.0
    flat_dark = 1.0 if (tip_mean < 45 and tip_var < 2500) else 0.0
    flat_haze = 1.0 if tip_var < 120 else 0.0  # topo sem detalhe (neblina/ceu)
    # bokeh no topo escuro nao conta como "luzes boas"
    lights_bonus = tip_lights * 28000.0 if tip_mean >= 40 or tip_var > 6000 else 0.0

    return (
        mid_var * 1.15
        + lower_var * 0.85
        + top_var * 1.6
        + tip_var * 2.8
        + lights_bonus
        + tip_p90 * 18.0
        + tip_mean * 35.0
        - skyish * 55000.0
        - tip_sky * 40000.0
        - dark_empty * 50000.0
        - tip_dark * 35000.0
        - flat_bright * 80000.0
        - flat_dark * 90000.0
        - flat_haze * 70000.0
        - (55000.0 if tip_mean < 40 else 0.0)
    )


def brightness_anchor_y(img: Image.Image, win_h: int) -> int:
    """Y preferencial para colocar o miolo luminoso no alto do frame.

    Ignora ceu azul (brilhante mas vazio) para nao ancorar no topo de panoramas.
    """
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    lum = arr.mean(axis=2)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    sky = (b > r + 10) & (b > g + 3) & (b > 130) & (lum > 120)
    interesting = (lum > 110) & (~sky)
    row = interesting.mean(axis=1)
    if float(row.sum()) < 1e-6:
        # fallback: evita o terco superior se for ceu
        top = arr[: int(arr.shape[0] * 0.35)]
        top_sky = float(
            np.mean(
                (top[:, :, 2] > top[:, :, 0] + 10)
                & (top[:, :, 2] > 130)
                & (top.mean(axis=2) > 120)
            )
        )
        if top_sky > 0.4:
            return max(0, img.size[1] - win_h)
        return max(0, (img.size[1] - win_h) // 2)
    cum = np.cumsum(row)
    y_center = int(np.searchsorted(cum, cum[-1] * 0.42))
    y = y_center - int(win_h * 0.32)
    return int(min(max(0, y), img.size[1] - win_h))


def smart_crop(img: Image.Image, cw: int, ch: int) -> tuple[Image.Image, str]:
    """Escolhe melhor janela com a proporcao do canvas (com zoom opcional)."""
    iw, ih = img.size
    target = cw / ch
    candidates: list[tuple[float, Image.Image, str]] = []

    for zoom in (1.0, 0.88, 0.78, 0.68, 0.60, 0.55, 0.50, 0.45, 0.40, 0.34):
        if iw / ih >= target:
            win_h = int(ih * zoom)
            win_w = int(win_h * target)
        else:
            win_w = int(iw * zoom)
            win_h = int(win_w / target)
        if win_w < 220 or win_h < 220 or win_w > iw or win_h > ih:
            continue
        anchor_y = brightness_anchor_y(img, win_h)
        xs = [0, (iw - win_w) // 2, iw - win_w] if iw > win_w else [0]
        if iw - win_w > 80:
            xs.extend(
                [
                    int((iw - win_w) * 0.15),
                    int((iw - win_w) * 0.3),
                    int((iw - win_w) * 0.45),
                    int((iw - win_w) * 0.6),
                    int((iw - win_w) * 0.75),
                    int((iw - win_w) * 0.9),
                ]
            )
        ys = sorted(
            {
                0,
                anchor_y,
                max(0, anchor_y - win_h // 8),
                min(ih - win_h, anchor_y + win_h // 8),
                int((ih - win_h) * 0.1),
                int((ih - win_h) * 0.25),
                int((ih - win_h) * 0.4),
                int((ih - win_h) * 0.55),
                int((ih - win_h) * 0.7),
                int((ih - win_h) * 0.85),
                ih - win_h,
            }
        )
        for y in ys:
            for x in xs:
                x = min(max(0, int(x)), iw - win_w)
                y = min(max(0, int(y)), ih - win_h)
                crop = img.crop((x, y, x + win_w, y + win_h))
                if cover_scale(win_w, win_h, cw, ch) > FRAMED_MAX_COVER_SCALE:
                    continue
                scored = crop.resize((cw // 2, ch // 2), Image.Resampling.BILINEAR)
                score = crop_interest_score(scored)
                # bonus se o crop esta perto da ancora de brilho
                score += max(0.0, 12000.0 - abs(y - anchor_y) * 18.0)
                arr = np.asarray(scored.convert("RGB"), dtype=np.float32)
                tip = arr[: int(arr.shape[0] * 0.2)]
                tip_lum = tip.mean(axis=2)
                tip_var = float(tip.var())
                sky = float(
                    np.mean(
                        (tip[:, :, 2] > tip[:, :, 0] + 10)
                        & (tip[:, :, 2] > 130)
                        & (tip_lum > 120)
                    )
                )
                if tip_var < 700 and (sky > 0.45 or float(tip_lum.mean()) < 40):
                    score -= 100000.0
                candidates.append((score, crop, f"zoom={zoom:.2f} xy={x},{y}"))

    if not candidates:
        return img, "smart-crop: fallback imagem original"
    candidates.sort(key=lambda t: t[0], reverse=True)
    for score, crop, meta in candidates:
        bw, bh = crop.size
        if cover_scale(bw, bh, cw, ch) <= FRAMED_MAX_COVER_SCALE:
            return crop, f"smart-crop: {meta} score={score:.0f}"
    return img, "smart-crop: nenhum frame hi-res; usando original"


def center_cover_score(img: Image.Image, cw: int, ch: int) -> float:
    iw, ih = img.size
    scale = cover_scale(iw, ih, cw, ch)
    nw, nh = int(round(iw * scale)), int(round(ih * scale))
    scaled = img.resize((nw, nh), Image.Resampling.BILINEAR)
    left = max(0, (nw - cw) // 2)
    top = max(0, (nh - ch) // 2)
    crop = scaled.crop((left, top, left + cw, top + ch)).resize(
        (cw // 2, ch // 2), Image.Resampling.BILINEAR
    )
    return crop_interest_score(crop)


def needs_smart_crop(img: Image.Image, cw: int, ch: int) -> bool:
    iw, ih = img.size
    scale = cover_scale(iw, ih, cw, ch)
    nh = int(round(ih * scale))
    if nh <= ch + 2:
        return True
    nw = int(round(iw * scale))
    scaled = img.resize((nw, nh), Image.Resampling.BILINEAR)
    left = (nw - cw) // 2
    top = max(0, (nh - ch) // 2)
    crop = scaled.crop((left, top, left + cw, top + ch)).resize(
        (cw // 2, ch // 2), Image.Resampling.BILINEAR
    )
    arr = np.asarray(crop.convert("RGB"), dtype=np.float32)
    tip = arr[: int(arr.shape[0] * 0.22)]
    topb = arr[: int(arr.shape[0] * 0.40)]
    tip_lum = tip.mean(axis=2)
    tip_var = float(tip.var())
    skyish = float(
        np.mean(
            (topb[:, :, 2] > topb[:, :, 0] + 10)
            & (topb[:, :, 2] > topb[:, :, 1] + 3)
            & (topb[:, :, 2] > 130)
        )
    )
    dark_empty = float(
        np.mean((topb.mean(axis=2) < 42) & (topb.std(axis=2) < 20))
    )
    tip_dark = float(np.mean(tip_lum < 35))
    flat_bright = float(tip_lum.mean()) > 140 and tip_var < 1800
    return (
        skyish > 0.22
        or dark_empty > 0.22
        or tip_dark > 0.45
        or flat_bright
        or tip_var < 900
        or float(topb.var()) < 900
    )


def prepare_photo(
    camp: Path, photo: Path, fmt: str, cw: int, ch: int
) -> tuple[Path, str]:
    img = Image.open(photo).convert("RGB")
    base_score = center_cover_score(img, cw, ch)
    if not needs_smart_crop(img, cw, ch):
        return photo, f"enquadramento cover ok (score={base_score:.0f})"
    focused, note = smart_crop(img, cw, ch)
    new_score = crop_interest_score(
        focused.resize((cw // 2, ch // 2), Image.Resampling.BILINEAR)
    )
    # so aplica se melhorar de verdade o topo/interesse
    if new_score < base_score + 2500:
        return photo, (
            f"smart-crop descartado (base={base_score:.0f} novo={new_score:.0f}); "
            "mantendo original"
        )
    # crop ainda claramente ruim: nao piorar arte com zoom errado
    if new_score < -40000 and base_score > new_score - 80000:
        return photo, (
            f"smart-crop fraco descartado (base={base_score:.0f} novo={new_score:.0f})"
        )
    out = camp / "assets" / f"hero-framed-{fmt}.jpg"
    focused.convert("RGB").save(out, quality=92)
    ok, msg = is_hires(out, cw, ch)
    if not ok:
        # framed pode usar margem FRAMED_MAX; se passar de 1.10 mas <=1.25, aceita
        with Image.open(out) as im:
            w, h = im.size
        if cover_scale(w, h, cw, ch) <= FRAMED_MAX_COVER_SCALE:
            return out, f"{note} | framed scale ok<=1.25"
        return photo, f"smart-crop gerou asset invalido ({msg}); usando original"
    return out, note

def format_trip_dates(d1: str, mo1: str, d2: str, mo2: str, yr2: str = "") -> str:
    if yr2:
        left = f"{d1.zfill(2)}/{mo1.zfill(2)}/{yr2}"
        right = f"{d2.zfill(2)}/{mo2.zfill(2)}/{yr2}"
    else:
        left = f"{d1.zfill(2)}/{mo1.zfill(2)}"
        right = f"{d2.zfill(2)}/{mo2.zfill(2)}"
    return f"IDA: {left}  ·  RETORNO: {right}"


def parse_date_footer(offer: dict) -> str:
    raw = (offer.get("date_raw") or offer.get("date_display") or "").lower()
    m = re.search(
        r"(\d{1,2})/(\d{1,2})\s*a\s*(\d{1,2})/(\d{1,2})(?:[/\s]+(?:de\s+)?(\d{2,4}))?",
        raw,
    )
    if m:
        d1, mo1, d2, mo2, yr = m.groups()
        yr2 = (yr or "")[-2:] if yr else ""
        return format_trip_dates(d1, mo1, d2, mo2, yr2)

    m = re.search(r"(\d{1,2})\s*a\s*(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", raw)
    if m:
        d1, d2, mo, yr = m.group(1), m.group(2), m.group(3), m.group(4)
        mo = mo.zfill(2)
        yr2 = yr[-2:] if yr else ""
        return format_trip_dates(d1, mo, d2, mo, yr2)

    months = {
        "jan": "01",
        "fev": "02",
        "mar": "03",
        "abr": "04",
        "mai": "05",
        "jun": "06",
        "jul": "07",
        "ago": "08",
        "set": "09",
        "out": "10",
        "nov": "11",
        "dez": "12",
    }
    m = re.search(
        r"(\d{1,2})\s*a\s*(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})",
        raw,
    )
    if m:
        d1, d2, mon, yr = m.groups()
        mo = months.get(mon[:3], "01")
        return format_trip_dates(d1, mo, d2, mo, yr[-2:])

    m = re.search(
        r"(\d{1,2})\s*a\s*(\d{1,2})\s+([a-zç]+)(?:\s+(\d{4}))?",
        raw,
    )
    if m:
        d1, d2, mon, yr = m.groups()
        mo = months.get(mon[:3].lower(), mon[:3].upper())
        yr2 = yr[-2:] if yr else ""
        return format_trip_dates(d1, mo, d2, mo, yr2)
    return escape(offer.get("date_display") or "")


def fonts() -> str:
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com" />'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
        '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet" />'
    )


def dest_subtitle(offer: dict) -> str:
    eyebrow = (offer.get("eyebrow") or "").strip()
    hotel = (offer.get("hotel") or "").strip()
    raw = (offer.get("date_raw") or offer.get("date_display") or "").lower()
    months = {
        "01": "Jan",
        "02": "Fev",
        "03": "Mar",
        "04": "Abr",
        "05": "Mai",
        "06": "Jun",
        "07": "Jul",
        "08": "Ago",
        "09": "Set",
        "10": "Out",
        "11": "Nov",
        "12": "Dez",
        "jan": "Jan",
        "fev": "Fev",
        "mar": "Mar",
        "abr": "Abr",
        "mai": "Mai",
        "jun": "Jun",
        "jul": "Jul",
        "ago": "Ago",
        "set": "Set",
        "out": "Out",
        "nov": "Nov",
        "dez": "Dez",
    }
    mon = ""
    mon2 = ""
    yr = ""
    m = re.search(
        r"(\d{1,2})/(\d{1,2})\s*a\s*(\d{1,2})/(\d{1,2})(?:[/\s]+(?:de\s+)?(\d{2,4}))?",
        raw,
    )
    if m:
        mon = months.get(m.group(2).zfill(2), "")
        mon2 = months.get(m.group(4).zfill(2), "")
        yr = m.group(5) or ""
        if len(yr) == 2:
            yr = "20" + yr
    else:
        m = re.search(r"/(\d{1,2})/(\d{2,4})", raw)
        if m:
            mon = months.get(m.group(1).zfill(2), "")
            yr = m.group(2)
            if len(yr) == 2:
                yr = "20" + yr
        else:
            m = re.search(
                r"\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*\b(?:\s+de)?(?:\s+(\d{4}))?",
                raw,
            )
            if m:
                mon = months.get(m.group(1)[:3], "")
                yr = m.group(2) or ""
    if mon and mon2 and mon != mon2:
        mon_bit = f"{mon}/{mon2}"
    else:
        mon_bit = mon
    date_bit = " ".join(x for x in (mon_bit, yr) if x)
    left = hotel or eyebrow
    if left and date_bit:
        return f"{left} · {date_bit}"
    return left or date_bit or (offer.get("tagline") or "")


def promo_balloons(offer: dict) -> str:
    """Gera baloes laterais com icones para inclusoes do pacote."""
    items = offer.get("includes") or []
    blob = " ".join(items).lower()
    tagline = (offer.get("tagline") or "").lower()
    hotel = (offer.get("hotel") or "").strip()
    payments = offer.get("payment") or []
    pill = (offer.get("pill") or "").upper()
    has_air = any(k in blob for k in ("aéreo", "aereo", "bloqueio aéreo", "bloqueio aereo"))
    has_transfer = "transfer" in blob
    has_passeio = any(k in blob for k in ("passeio", "city tour", "bustour", "nativitaten"))
    has_protect = "protect" in blob
    has_hotel = hotel or any(k in blob for k in ("hotel", "hospedagem", "café", "cafe", "pensão", "pensao"))
    has_cafe = any(k in blob for k in ("café", "cafe", "pensão", "pensao", "café da manhã"))
    has_falls = any(k in tagline for k in ("cataratas", "iguacu", "iguaçu", "foz"))
    has_15x = any("15x" in p.lower() for p in payments)

    balloons: list[str] = []

    if has_air:
        balloons.append(f'<div class="badge-air">{PLANE}Pacote<br/>Aéreo</div>')
    elif "TERRESTRE" in pill:
        balloons.append(f'<div class="badge-air">{PLANE}Pacote<br/>Terrestre</div>')
    else:
        balloons.append(f'<div class="badge-air">{PLANE}Pacote<br/>Viagem</div>')

    if hotel:
        balloons.append(
            f'<div class="badge-pay">{ICON_BED}<span class="hi">{escape(hotel.upper())}</span>'
            f"<small>experiência premium</small></div>"
        )
    elif has_hotel:
        detail = "com café da manhã" if has_cafe else "incluso no pacote"
        balloons.append(
            f'<div class="badge-pay">{ICON_BED}<span class="hi">HOTEL</span>'
            f"<small>{escape(detail)}</small></div>"
        )

    if has_transfer and has_passeio:
        detail = "no pacote"
        if "leste" in blob and "oeste" in blob:
            detail = "Leste e Oeste"
        elif "nativitaten" in blob or "bustour" in blob:
            detail = "Bustour incluso"
        elif "city tour" in blob:
            detail = "city tour incluso"
        balloons.append(
            f'<div class="badge-pay">{ICON_BUS}<span class="hi">TRANSFER</span>'
            f"<small>+ passeios · {escape(detail)}</small></div>"
        )
    elif has_transfer:
        balloons.append(
            f'<div class="badge-pay">{ICON_BUS}<span class="hi">TRANSFER</span>'
            "<small>ida e volta</small></div>"
        )

    if has_protect:
        balloons.append(
            f'<div class="badge-pay">{ICON_SHIELD}<span class="hi">PROTECT</span>'
            "<small>cobertura inclusa</small></div>"
        )

    if has_15x:
        balloons.append(
            f'<div class="badge-pay">{ICON_CARD}<span class="hi">15x</span>'
            "<small>sem juros</small></div>"
        )
    elif payments and len(balloons) < 5:
        pay0 = payments[0]
        short = pay0 if len(pay0) < 22 else pay0[:20] + "…"
        balloons.append(
            f'<div class="badge-pay">{ICON_CARD}<span class="hi">PARCELE</span>'
            f"<small>{escape(short)}</small></div>"
        )

    if has_falls and len(balloons) < 5:
        balloons.append(
            f'<div class="badge-pay">{ICON_FALLS}<span class="hi">CATARATAS</span>'
            "<small>marco das 3 fronteiras</small></div>"
        )

    # no maximo 5 baloes para nao cobrir a arte
    return "\n".join(balloons[:5])


def dest_heading_html(destination: str) -> tuple[str, str]:
    """Titulo do destino em 1 linha, caixa ajustada ao texto."""
    dest_class = "dest--long" if len(destination) > 18 else ""
    return escape(destination.upper()), dest_class


def build_html(
    offer: dict, photo: Path, logo: Path, fmt: str, cw: int, ch: int
) -> str:
    dest = offer["destination"]
    dest_upper, dest_class = dest_heading_html(dest)
    unit = escape(offer["price"]["unit"])
    price = escape(offer["price"]["value"])
    price_label = escape(offer["price"].get("label") or "À vista")
    price_class = "price--compact" if len(offer["price"]["value"]) > 10 else ""
    disc = escape(offer.get("disclaimer") or "Consulte disponibilidade e condições.")
    items = [escape(i) for i in offer.get("includes", [])[:4]]
    payments = [escape(p) for p in offer.get("payment", [])[:2]]
    date_footer = parse_date_footer(offer)
    subtitle = escape(dest_subtitle(offer))
    balloons_html = promo_balloons(offer)
    chips = "".join(f"<span>{i}</span>" for i in items)
    pay_html = ""
    if payments:
        pay_html = (
            '<div class="pays">'
            + "".join(f"<div>{p}</div>" for p in payments)
            + "</div>"
        )

    story = fmt == "story"
    logo_h = 142 if story else 148
    balloon_top = 268 if story else 228
    stack_side = 56 if story else 52
    # Legibilidade Instagram: destino e preco precisam ler no celular
    h1 = 42 if story else 44
    h1_long = 34 if story else 36
    price_size = 60 if story else 64
    price_compact = 46 if story else 50
    chip_size = 19 if story else 18
    footer_h = 98 if story else 90
    disc_bottom = footer_h + 8
    badge_air_size = 158 if story else 163
    stack_bottom = 148 if story else 118
    balloon_max_h = 980 if story else 620

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<title>{escape(offer['slug'])} | {fmt}</title>
{fonts()}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{cw}px;height:{ch}px;overflow:hidden;background:#000;font-family:Nunito,sans-serif;-webkit-font-smoothing:antialiased}}
.canvas{{position:relative;width:{cw}px;height:{ch}px;overflow:hidden}}
.photo{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center center}}
.veil{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.12) 0%,transparent 32%,rgba(0,0,0,.42) 100%)}}
.logo-tab{{position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border-radius:0 0 28px 28px;padding:20px 36px 18px;box-shadow:0 10px 28px rgba(0,0,0,.28);z-index:5}}
.logo-tab img{{display:block;height:{logo_h}px;width:auto}}
.balloons{{position:absolute;left:28px;top:{balloon_top}px;display:flex;flex-direction:column;align-items:flex-start;gap:12px;z-index:5;max-height:{balloon_max_h}px;overflow:visible}}
.badge-air{{width:{badge_air_size}px;height:{badge_air_size}px;border-radius:50%;background:#3AAFA9;color:#17252A;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:20px;font-weight:900;line-height:1.05;text-align:center;box-shadow:0 14px 32px rgba(0,0,0,.38);flex-shrink:0}}
.badge-pay{{background:#fff;border-radius:16px;padding:14px 17px;box-shadow:0 12px 28px rgba(0,0,0,.32);color:#17252A;font-weight:900;font-size:19px;line-height:1.1;text-align:center;max-width:252px;display:flex;flex-direction:column;align-items:center;gap:2px;flex-shrink:0}}
.badge-pay svg{{color:#2B7A78;margin-bottom:2px}}
.badge-pay .hi{{color:#2B7A78;font-size:22px;display:block}}
.badge-pay small{{display:block;font-size:16px;font-weight:800;opacity:.85;margin-top:1px;line-height:1.15}}
.stack{{position:absolute;left:{stack_side}px;right:{stack_side}px;bottom:{stack_bottom}px;display:flex;flex-direction:column;align-items:center;z-index:4}}
.dest{{width:fit-content;max-width:92%;margin:0 auto;background:#fff;border-radius:12px;padding:12px 26px 10px;text-align:center;box-shadow:0 10px 24px rgba(0,0,0,.28);position:relative;z-index:2}}
.dest h1{{font-size:{h1}px;font-weight:900;color:#111;line-height:1.02;white-space:nowrap}}
.dest--long{{padding:12px 22px 10px}}
.dest--long h1{{font-size:{h1_long}px;white-space:normal}}
.dest--stacked{{padding:10px 20px 8px}}
.dest--stacked h1{{font-size:{h1}px;line-height:1.05;white-space:normal}}
.dest .tag{{margin-top:6px;font-size:22px;font-weight:800;color:#2B7A78;letter-spacing:.02em}}
.super{{margin-top:-11px;position:relative;z-index:3;background:#17252A;color:#fff;font-size:20px;font-weight:900;letter-spacing:.05em;padding:10px 22px;border-radius:9px;box-shadow:0 6px 14px rgba(0,0,0,.28)}}
.price-card{{margin-top:14px;width:100%;max-width:900px;background:#fff;border-radius:16px;padding:18px 20px 16px;text-align:center;box-shadow:0 12px 28px rgba(0,0,0,.3)}}
.price-card .avista-label{{font-size:22px;font-weight:800;color:#111}}
.price-card .price{{display:block;font-size:{price_size}px;font-weight:900;line-height:1;margin-top:2px;color:#111;letter-spacing:-.02em}}
.price-card .price--compact{{font-size:{price_compact}px;letter-spacing:-.01em}}
.price-card .unit{{margin-top:6px;font-size:20px;font-weight:800;color:#2B7A78;letter-spacing:.05em;text-transform:uppercase}}
.pays{{margin-top:8px;display:flex;flex-direction:column;gap:2px}}
.pays div{{font-size:18px;font-weight:800;color:#2B7A78}}
.incs{{margin-top:10px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px}}
.incs span{{background:#2B7A78;color:#fff;font-size:{chip_size}px;font-weight:800;padding:10px 14px;border-radius:999px;line-height:1.15}}
.footer{{position:absolute;left:0;right:0;bottom:0;height:{footer_h}px;background:#111;display:flex;align-items:center;justify-content:center;gap:12px;color:#fff;font-size:26px;font-weight:800;z-index:6}}
.disc{{position:absolute;bottom:{disc_bottom}px;left:56px;right:56px;text-align:center;font-size:15px;font-weight:700;color:#fff;background:rgba(0,0,0,.55);padding:8px 14px;border-radius:10px;text-shadow:0 1px 2px rgba(0,0,0,.4);z-index:5}}
</style>
</head>
<body>
<article class="canvas">
  <img class="photo" src="{file_url(photo)}" alt="" />
  <div class="veil"></div>
  <div class="logo-tab"><img src="{file_url(logo)}" alt="Viajando com a Babi" /></div>
  <div class="balloons">
    {balloons_html}
  </div>
  <div class="stack">
    <div class="dest {dest_class}">
      <h1>{dest_upper}</h1>
      {f'<div class="tag">{subtitle}</div>' if subtitle else ''}
    </div>
    <div class="super">SUPER OPORTUNIDADE</div>
    <div class="price-card">
      <div class="avista-label">{price_label}</div>
      <div class="price {price_class}">{price}</div>
      <div class="unit">{unit}</div>
      {pay_html}
      <div class="incs">{chips}</div>
    </div>
  </div>
  <p class="disc">{disc}</p>
  <div class="footer">{CAL}{date_footer}</div>
</article>
</body>
</html>"""


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def expected_texts(offer: dict) -> list[str]:
    out = [
        offer["destination"],
        offer["price"]["value"],
        offer["price"]["unit"],
        offer["price"].get("label") or "À vista",
        "SUPER OPORTUNIDADE",
    ]
    out.extend(offer.get("includes") or [])
    out.extend(offer.get("payment") or [])
    footer = parse_date_footer(offer)
    # pedacos das datas
    for part in re.findall(r"\d{2}/\d{2}(?:/\d{2})?", footer):
        out.append(part)
    return [t for t in out if t]


def qa_texts(page, offer: dict) -> tuple[bool, str]:
    body = page.locator("body").inner_text()
    nbody = norm(body)
    missing = []
    for t in expected_texts(offer):
        if norm(t) not in nbody:
            missing.append(t)
    if missing:
        return False, "textos ausentes: " + " | ".join(missing[:8])
    return True, "QA textos ok"


def discover_campaigns() -> list[Path]:
    return sorted(p.parent for p in CAMPAIGNS.rglob("offer.json"))


def main() -> int:
    logo = BRAND / "logo-vcb.png"
    results: list[str] = []
    failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for camp in discover_campaigns():
            offer_path = camp / "offer.json"
            offer = json.loads(offer_path.read_text(encoding="utf-8"))
            slug = offer["slug"]
            formats = offer.get("formats") or ["post", "story"]

            qa_mkt = (offer.get("photo") or {}).get("qa_marketing") or ""
            qa_up = qa_mkt.upper()
            if qa_up.startswith("REPROVAR"):
                failures.append(f"{slug}: foto reprovada no QA de marketing ({qa_mkt})")
                print(f"SKIP {slug}: foto reprovada no QA de marketing")
                continue
            # Foco: so renderiza APROVAR (ou sem nota). TROCAR exige nova foto.
            if qa_up.startswith("TROCAR"):
                failures.append(f"{slug}: foto marcada TROCAR no QA de marketing ({qa_mkt})")
                print(f"SKIP {slug}: foto TROCAR no QA de marketing")
                continue

            for fmt in formats:
                if fmt not in FORMATS:
                    continue
                cw, ch = FORMATS[fmt]["w"], FORMATS[fmt]["h"]
                photo, msg = find_photo(camp, offer, cw, ch)
                if photo is None:
                    failures.append(f"{slug}/{fmt}: {msg}")
                    print(f"SKIP {slug}/{fmt}: {msg}")
                    continue

                framed, frame_note = prepare_photo(camp, photo, fmt, cw, ch)
                html = build_html(offer, framed, logo, fmt, cw, ch)
                export = camp / "export"
                source = camp / "source"
                export.mkdir(parents=True, exist_ok=True)
                source.mkdir(parents=True, exist_ok=True)
                html_path = source / f"{slug}-{fmt}-final.html"
                png_path = export / f"{slug}-{FORMATS[fmt]['suffix']}.png"
                html_path.write_text(html, encoding="utf-8")

                page = browser.new_page(
                    viewport={"width": cw, "height": ch}, device_scale_factor=1
                )
                page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
                page.wait_for_timeout(450)
                ok_txt, txt_note = qa_texts(page, offer)
                if not ok_txt:
                    page.close()
                    failures.append(f"{slug}/{fmt}: {txt_note}")
                    print(f"FAIL QA TEXT {slug}/{fmt}: {txt_note}")
                    continue
                page.locator(".canvas").screenshot(path=str(png_path), type="png")
                page.close()

                offer.setdefault("photo", {})
                offer["photo"][f"qa_{fmt}"] = f"{msg} | {frame_note} | {txt_note}"
                offer_path.write_text(
                    json.dumps(offer, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                line = f"OK {png_path.relative_to(ROOT)} ({msg} | {frame_note} | {txt_note})"
                print(line)
                results.append(line)
        browser.close()

    print("\n=== RESUMO ===")
    for line in results:
        print(line)
    for line in failures:
        print(f"FALHOU  {line}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
