#!/usr/bin/env python3
"""
Sincroniza ofertas de viajandocomdesconto.com com o site Viajando com a Babi.

Uso:
  python _sync_operator.py              # coleta, filtra, gera fragments e operator-sync.json
  python _sync_operator.py --apply      # também atualiza cards existentes em index.html
  python _sync_operator.py --download-images  # baixa imagens ausentes

Depois:
  python _build_ofertas.py
  python _build_pacotes.py
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
GENERATED = DATA / "generated"
SYNC_FILE = DATA / "operator-sync.json"
SOURCE_URL = "https://viajandocomdesconto.com/"
WA_NUMBER = "5521920064617"
TODAY = date.today()

RIO_IATA = {"GIG", "SDU"}
SP_IATA = {"GRU", "CGH", "VCP"}
ORIGIN_PRIORITY = ("rio", "sp")

USER_AGENT = "ViajandoComABabi-Sync/1.0 (+https://viajandocomababi.com.br/)"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower().strip()


def slugify(text: str, prefix: str = "") -> str:
    base = normalize(text)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return f"{prefix}{base}"[:80].strip("-")


def fetch_html() -> str:
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", "replace")


def extract_json_array(html: str, name: str) -> list:
    match = re.search(rf"{name}\s*=\s*(\[.*?\]);", html, re.S)
    if not match:
        raise RuntimeError(f"Array {name} não encontrado na fonte")
    return json.loads(match.group(1))


def extract_dados(html: str) -> dict:
    match = re.search(r'id="dados"[^>]*>(\{.*?\})</script>', html, re.S)
    if not match:
        raise RuntimeError("Bloco dados não encontrado na fonte")
    return json.loads(match.group(1))


def parse_br_date(text: str) -> date | None:
    if not text:
        return None
    text = text.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", text)
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), m.group(3)
    if month < 1 or month > 12 or day < 1 or day > 31:
        return None
    if year is None:
        year = TODAY.year
        parsed = date(year, month, day)
        if parsed < TODAY:
            year += 1
    else:
        year = int(year)
        if year < 100:
            year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_date_range(text: str) -> tuple[date | None, date | None]:
    if not text:
        return None, None
    cleaned = re.sub(r"\s*(até|ate)\s*", " a ", text, flags=re.I)
    m = re.search(r"(\d{1,2})\s+a\s+(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", cleaned, re.I)
    if m and "/" not in m.group(1):
        year = m.group(4)
        start = parse_br_date(f"{m.group(1)}/{m.group(3)}" + (f"/{year}" if year else ""))
        end = parse_br_date(f"{m.group(2)}/{m.group(3)}" + (f"/{year}" if year else ""))
        return start, end
    parts = re.split(r"\s+a\s+|\s*-\s*", cleaned, maxsplit=1, flags=re.I)
    start = parse_br_date(parts[0]) if parts else None
    end = parse_br_date(parts[1]) if len(parts) > 1 else start
    return start, end


def is_range_valid(text: str) -> bool:
    start, end = parse_date_range(text)
    if end:
        return end >= TODAY
    if start:
        return start >= TODAY
    return True


def classify_origin(iata: str | None, cidade: str | None) -> str | None:
    code = (iata or "").upper()
    city = normalize(cidade or "")
    if code in RIO_IATA or "rio de janeiro" in city:
        return "rio"
    if code in SP_IATA or "sao paulo" in city:
        return "sp"
    return None


def has_flight(inclui: list[str] | None) -> bool:
    blob = normalize(" ".join(inclui or []))
    return "passagem aerea" in blob or "aereo ida" in blob or "bloqueio" in blob


def br_money_html(value: str) -> str:
    return re.sub(r"R\$\s*", "R$&nbsp;", value or "")


def wa_link(message: str) -> str:
    encoded = urllib.parse.quote(message, safe="")
    return f"https://wa.me/{WA_NUMBER}?text={encoded}"


def attr(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def nights_from_range(text: str) -> int | None:
    start, end = parse_date_range(text)
    if start and end and end >= start:
        delta = (end - start).days
        return delta if delta > 0 else None
    return None


def next_future_iso(*texts: str) -> str:
    candidates: list[date] = []
    for text in texts:
        if not text:
            continue
        start, end = parse_date_range(str(text))
        for parsed in (start, end):
            if parsed and parsed >= TODAY:
                candidates.append(parsed)
        for part in re.split(r"[,;]", str(text)):
            parsed = parse_br_date(part.strip())
            if parsed and parsed >= TODAY:
                candidates.append(parsed)
    if not candidates:
        return ""
    return min(candidates).isoformat()


def tipo_from_offer(offer: dict) -> str:
    blob = normalize(" ".join(offer.get("inclui") or []) + " " + (offer.get("title") or "") + " " + (offer.get("destination") or ""))
    if "cruzeiro" in blob or "navio" in blob or "msc" in blob:
        return "cruzeiro"
    if offer.get("flight_included"):
        return "com-aereo"
    return "sem-aereo"


def money_to_float(text: str) -> float:
    if not text:
        return 0.0
    m = re.search(r"([\d.,]+)", text.replace("R$", ""))
    if not m:
        return 0.0
    raw = m.group(1)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def pick_cheapest_hotel(hoteis: list[dict] | None) -> dict | None:
    if not hoteis:
        return None
    return min(hoteis, key=lambda h: money_to_float(h.get("preco", "")))


def fingerprint(*parts: str) -> str:
    raw = "|".join(normalize(p) for p in parts if p)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def local_image_stem(slug: str, destino: str) -> str:
    slug_map = {
        "portodegalinhascommarago": "pacote-porto-de-galinhas",
        "salvadorimperdivel": "pacote-salvador",
    }
    if slug in slug_map:
        return slug_map[slug]
    if slug and len(slug) > 4:
        candidate = slugify(slug, "pacote-")
    else:
        candidate = slugify(destino, "pacote-")
    for stem in (candidate, slugify(destino, "pacote-")):
        if (ROOT / "pacotes" / f"{stem}.jpeg").exists() or (ROOT / "pacotes" / f"{stem}.webp").exists():
            return stem
    return candidate if slug and len(slug) > 4 else slugify(destino, "pacote-")


def image_tags(stem: str, alt: str) -> str:
    jpeg = ROOT / "pacotes" / f"{stem}.jpeg"
    webp400 = ROOT / "pacotes" / f"{stem}-400.webp"
    webp800 = ROOT / "pacotes" / f"{stem}-800.webp"
    webp = ROOT / "pacotes" / f"{stem}.webp"
    if webp400.exists() and webp800.exists():
        srcset = f"pacotes/{stem}-400.webp 400w, pacotes/{stem}-800.webp 800w"
        fallback = f"pacotes/{stem}.jpeg" if jpeg.exists() else f"pacotes/{stem}-800.webp"
    elif webp.exists():
        srcset = f"pacotes/{stem}.webp 800w"
        fallback = f"pacotes/{stem}.jpeg" if jpeg.exists() else f"pacotes/{stem}.webp"
    elif jpeg.exists():
        return (
            f'<img src="pacotes/{stem}.jpeg" alt="{alt}" width="400" height="260" '
            f'data-lightbox decoding="async" loading="lazy">'
        )
    else:
        return (
            f'<img src="assets/og-share.jpeg" alt="{alt}" width="400" height="260" '
            f'decoding="async" loading="lazy">'
        )
    return (
        f'<picture><source srcset="{srcset}" sizes="(max-width:640px) 100vw, 400px" type="image/webp" />'
        f'<img src="{fallback}" alt="{alt}" width="400" height="260" data-lightbox '
        f'decoding="async" loading="lazy"></picture>'
    )


def download_image(rel_path: str, stem: str) -> bool:
    if not rel_path:
        return False
    url = rel_path if rel_path.startswith("http") else urllib.parse.urljoin(SOURCE_URL, rel_path)
    dest_jpeg = ROOT / "pacotes" / f"{stem}.jpeg"
    if dest_jpeg.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError):
        return False

    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data)).convert("RGB")
        dest_jpeg.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest_jpeg, "JPEG", quality=85, optimize=True)
        for width, suffix in ((800, "-800"), (400, "-400")):
            resized = img.copy()
            resized.thumbnail((width, 520))
            resized.save(ROOT / "pacotes" / f"{stem}{suffix}.webp", "WEBP", quality=82)
        img.save(ROOT / "pacotes" / f"{stem}.webp", "WEBP", quality=82)
        return True
    except Exception:
        return False


def filter_pacotes(raw: list[dict]) -> tuple[list[dict], dict]:
    selected: list[dict] = []
    stats = {"total": len(raw), "rio": 0, "sp": 0, "sem_aereo": 0, "ignored_origin": 0, "ignored_expired": 0}

    for pkg in raw:
        slug = pkg.get("slug") or slugify(pkg.get("nome", ""))
        origens = pkg.get("origens") or []
        flight = any(has_flight(o.get("inclui")) for o in origens) if origens else False

        candidates: list[tuple[str, dict]] = []
        if flight:
            for origin in origens:
                bucket = classify_origin(origin.get("iata"), origin.get("cidade"))
                if bucket:
                    candidates.append((bucket, origin))
            if not candidates:
                stats["ignored_origin"] += 1
                continue
            seen: set[str] = set()
            ordered = []
            for bucket in ORIGIN_PRIORITY:
                for b, o in candidates:
                    if b == bucket and bucket not in seen:
                        ordered.append((b, o))
                        seen.add(bucket)
        else:
            stats["sem_aereo"] += 1
            origin = origens[0] if origens else {}
            ordered = [("sem_aereo", origin)]

        for bucket, origin in ordered[:2 if flight else 1]:
            if not is_range_valid(origin.get("data", "")):
                stats["ignored_expired"] += 1
                continue
            hotel = pick_cheapest_hotel(origin.get("hoteis"))
            total = hotel.get("preco") if hotel else origin.get("por") or origin.get("de") or ""
            parcela = hotel.get("parcela") if hotel else origin.get("min_parcela") or ""
            offer_id = f"pacote:{slug}:{origin.get('iata') or bucket}"
            offer = {
                "id": offer_id,
                "fingerprint": fingerprint("pacote", slug, origin.get("iata", ""), origin.get("data", "")),
                "category": "pacote",
                "source_slug": slug,
                "title": pkg.get("nome") or pkg.get("destino") or "",
                "destination": pkg.get("destino") or "",
                "origin_city": origin.get("cidade") or "",
                "origin_airport": origin.get("iata") or "",
                "origin_bucket": bucket,
                "departure_date": origin.get("data") or "",
                "additional_dates": origin.get("outras") or "",
                "flight_included": flight,
                "categoria_site": "sem-aereo" if not flight else "completo",
                "capa": pkg.get("capa") or "",
                "inclui": origin.get("inclui") or [],
                "hoteis": origin.get("hoteis") or [],
                "taxas": origin.get("taxas") or "",
                "de": origin.get("de") or "",
                "por": origin.get("por") or "",
                "installments": parcela,
                "total_price": total,
                "evento": bool(pkg.get("evento")),
                "pacote_categoria": pkg.get("categoria") or "",
                "sort_date": next_future_iso(origin.get("data", ""), origin.get("outras") or ""),
                "sort_price": round(money_to_float(total), 2),
            }
            offer["tipo"] = tipo_from_offer(offer)
            selected.append(offer)
            if bucket == "rio":
                stats["rio"] += 1
            elif bucket == "sp":
                stats["sp"] += 1

    return selected, stats


def filter_promo_voos(raw: list[dict]) -> tuple[list[dict], dict]:
    selected: list[dict] = []
    stats = {"total": len(raw), "rio": 0, "sp": 0, "ignored_origin": 0, "ignored_expired": 0}

    for item in raw:
        bucket = classify_origin(item.get("origem_iata"), item.get("origem_cidade"))
        if not bucket:
            stats["ignored_origin"] += 1
            continue
        if not is_range_valid(item.get("data", "")):
            stats["ignored_expired"] += 1
            continue
        offer_id = f"voo:{item.get('origem_iata')}:{normalize(item.get('destino',''))}:{item.get('data','')}"
        preco = item.get("por") or item.get("de") or ""
        selected.append(
            {
                "id": offer_id,
                "fingerprint": fingerprint("voo", item.get("origem_iata", ""), item.get("destino", ""), item.get("data", "")),
                "category": "promo-voo",
                "title": item.get("nome") or item.get("destino") or "",
                "destination": item.get("destino") or "",
                "origin_city": item.get("origem_cidade") or "",
                "origin_airport": item.get("origem_iata") or "",
                "origin_bucket": bucket,
                "departure_date": item.get("data") or "",
                "additional_dates": ", ".join(item.get("outras") or []),
                "de": item.get("de") or "",
                "por": item.get("por") or "",
                "taxas": item.get("taxas") or "",
                "inclui": item.get("inclui") or [],
                "installments": item.get("min_label") or "",
                "obs": item.get("obs") or "",
                "nights": nights_from_range(item.get("data") or ""),
                "sort_date": next_future_iso(item.get("data", ""), ", ".join(item.get("outras") or [])),
                "sort_price": round(money_to_float(preco), 2),
            }
        )
        stats[bucket] += 1

    selected.sort(key=lambda o: (parse_date_range(o["departure_date"])[0] or TODAY, o["destination"]))
    return selected, stats


def filter_campanhas(raw: list[dict]) -> tuple[list[dict], dict]:
    selected: list[dict] = []
    stats = {"total": len(raw), "selected": 0, "ignored_expired": 0}

    for item in raw:
        venda = item.get("periodo_venda") or ""
        hosp = item.get("periodo_hospedagem") or ""
        if venda and not is_range_valid(venda):
            stats["ignored_expired"] += 1
            continue
        if not venda and hosp and not is_range_valid(hosp):
            stats["ignored_expired"] += 1
            continue
        destino = item.get("destino") or ""
        hotel = item.get("hospedagem") or ""
        offer_id = f"campanha:{slugify(destino)}:{slugify(hotel)}"
        selected.append(
            {
                "id": offer_id,
                "fingerprint": fingerprint("campanha", destino, hotel, item.get("desconto", ""), item.get("periodo_venda", "")),
                "category": "campanha",
                "title": f"{destino}: {hotel}".strip(": "),
                "destination": destino,
                "hotel": hotel,
                "desconto": item.get("desconto") or "",
                "periodo_venda": item.get("periodo_venda") or "",
                "periodo_hospedagem": item.get("periodo_hospedagem") or "",
                "chd": item.get("chd") or "",
                "nota": item.get("nota") or "",
                "fornecedor": item.get("fornecedor") or "",
                "exclusivo": item.get("exclusivo") or "",
                "sort_date": next_future_iso(item.get("periodo_venda") or "", item.get("periodo_hospedagem") or ""),
                "sort_price": 0,
            }
        )
        stats["selected"] += 1

    return selected, stats


def render_pacote_card(offer: dict) -> str:
    stem = local_image_stem(offer["source_slug"], offer["destination"])
    suffix = offer.get("origin_airport") or offer.get("origin_bucket") or "na"
    card_id = slugify(f"{stem}-{suffix}")
    destino_label = offer["title"][:80]
    badge = offer["departure_date"]
    if offer.get("additional_dates"):
        badge = f"{badge} · {offer['additional_dates']}" if badge else str(offer["additional_dates"])

    features = []
    if offer["flight_included"] and offer["origin_airport"]:
        aereo = offer.get("por") or offer.get("de") or ""
        de = f" de {offer['de']}" if offer.get("de") and offer.get("por") else ""
        features.append(
            f'<li><i class="fas fa-plane"></i> Saída {html.escape(offer["origin_city"])} ({html.escape(offer["origin_airport"])})'
            f"{': aéreo' + de + ' por ' + br_money_html(aereo) if aereo else ''}</li>"
        )
    elif not offer["flight_included"]:
        features.append('<li><i class="fas fa-bed"></i> Pacote sem aéreo · consulte condições</li>')

    hotel = pick_cheapest_hotel(offer.get("hoteis"))
    if hotel:
        regime = hotel.get("regime") or "consulte regime"
        features.append(
            f'<li><i class="fas fa-hotel"></i> {html.escape(hotel.get("nome", "Hospedagem"))} · {html.escape(regime)}</li>'
        )
    for line in (offer.get("inclui") or [])[:3]:
        clean = re.sub(r"[^\x00-\x7F\u00C0-\u024F\s.,·\-+%/()R$]", "", line).strip()
        if clean and "passagem" not in normalize(clean):
            features.append(f'<li><i class="fas fa-check"></i> {html.escape(clean)}</li>')
    if offer.get("taxas"):
        features.append(f'<li><i class="fas fa-exclamation-circle"></i> Taxas {br_money_html(offer["taxas"])} · sujeito a alteração</li>')

    parcela_html = ""
    total_html = ""
    if offer.get("installments"):
        m = re.search(r"(\d+)x\s*de?\s*R\$\s*([\d.,]+)", offer["installments"], re.I)
        if m:
            parcela_html = f'{html.escape(m.group(1))}x a partir de <strong>{br_money_html("R$ " + m.group(2))}</strong>'
        else:
            parcela_html = html.escape(offer["installments"])
    if offer.get("total_price"):
        total_html = f'Total a partir de {br_money_html(offer["total_price"])} + taxas · sujeito a alteração'

    subtitle = offer["title"].replace(offer["destination"], "").strip(" ·:-")[:60]
    msg = f"Olá, Babi! Tenho interesse na oferta {destino_label}."
    origem = offer.get("origin_bucket") or "sem-aereo"
    tipo = offer.get("tipo") or tipo_from_offer(offer)
    alt = f"{offer['destination']}: {offer['title']}"
    attrs = (
        f'id="{attr(card_id)}" data-destino="{attr(destino_label)}" '
        f'data-categoria="{attr(offer["categoria_site"])}" data-source="operator" '
        f'data-source-id="{attr(offer["id"])}" data-sort-date="{attr(offer.get("sort_date", ""))}" '
        f'data-sort-price="{offer.get("sort_price") or 0}" data-origem="{attr(origem)}" '
        f'data-origem-iata="{attr(offer.get("origin_airport", ""))}" '
        f'data-destino-key="{attr(slugify(offer["destination"]))}" data-tipo="{attr(tipo)}"'
    )
    return f"""
        <article class="card reveal catalog-item" {attrs}>
          <div class="card__img-wrap">
            {image_tags(stem, alt)}
            <span class="card__badge">{html.escape(str(badge)[:70])}</span>
          </div>
          <div class="card__body">
            <h4 class="card__title">{html.escape(offer['destination'])} <span>{html.escape(subtitle)}</span></h4>
            <ul class="card__features">
              {''.join(features)}
            </ul>
            <div class="card__footer">
              <div class="card__preco">
                {'<span class="card__parcela">' + parcela_html + '</span>' if parcela_html else ''}
                {'<span class="card__total">' + total_html + '</span>' if total_html else ''}
              </div>
              <a href="{wa_link(msg)}"
                 target="_blank" rel="noopener noreferrer"
                 class="btn btn--whatsapp btn--full">
                <i class="fab fa-whatsapp"></i> Quero esse pacote!
              </a>
            </div>
          </div>
        </article>"""


def render_voo_row(offer: dict) -> str:
    card_id = slugify(f"voo-{offer['origin_airport']}-{offer['destination']}", "promo-")
    destino_label = offer["title"]
    msg = f"Olá, Babi! Tenho interesse na promoção de voo {destino_label}."
    start, end = parse_date_range(offer.get("departure_date") or "")
    nights = offer.get("nights")
    nights_html = f" · {nights} noites" if nights else ""
    preco = offer.get("por") or offer.get("de") or ""
    taxas = offer.get("taxas") or ""
    ida = start.strftime("%d/%m") if start else (offer.get("departure_date") or "")
    volta = end.strftime("%d/%m") if end and end != start else ""
    extras = []
    if offer.get("additional_dates"):
        extras.append(f"Outras saídas: {html.escape(offer['additional_dates'])}")
    if offer.get("obs"):
        extras.append(html.escape(offer["obs"]))
    if offer.get("installments"):
        extras.append(html.escape(offer["installments"]))
    conditions = ""
    if extras:
        conditions = (
            '<details class="oferta-row__details">'
            "<summary>Ver condições</summary>"
            f'<p>{" · ".join(extras)}</p>'
            "</details>"
        )
    origem_txt = f"{offer['origin_city']} ({offer['origin_airport']})" if offer.get("origin_airport") else offer.get("origin_city") or ""
    attrs = (
        f'id="{attr(card_id)}" data-destino="{attr(destino_label)}" data-categoria="promo-voo" '
        f'data-source="operator" data-source-id="{attr(offer["id"])}" '
        f'data-sort-date="{attr(offer.get("sort_date", ""))}" data-sort-price="{offer.get("sort_price") or 0}" '
        f'data-origem="{attr(offer.get("origin_bucket", ""))}" data-origem-iata="{attr(offer.get("origin_airport", ""))}" '
        f'data-destino-key="{attr(slugify(offer["destination"]))}"'
    )
    volta_cell = (
        f'<div class="oferta-row__leg"><span class="oferta-row__kicker">Volta</span>'
        f'<strong>{html.escape(volta)}</strong>'
        f'<span>{html.escape(offer["destination"])} → {html.escape(offer["origin_airport"])}</span></div>'
        if volta else ""
    )
    return f"""
        <article class="oferta-row catalog-item" {attrs}>
          <div class="oferta-row__main">
            <h3 class="oferta-row__title">{html.escape(offer['destination'])}{html.escape(nights_html)}</h3>
            <p class="oferta-row__meta">Saindo de {html.escape(origem_txt)}</p>
            <div class="oferta-row__legs">
              <div class="oferta-row__leg">
                <span class="oferta-row__kicker">Ida</span>
                <strong>{html.escape(ida)}</strong>
                <span>{html.escape(offer["origin_airport"])} → {html.escape(offer["destination"])}</span>
              </div>
              {volta_cell}
            </div>
            {conditions}
          </div>
          <div class="oferta-row__price">
            {'<span class="oferta-row__value">' + br_money_html(preco) + '</span>' if preco else ''}
            {'<span class="oferta-row__tax">+ taxa ' + br_money_html(taxas) + '</span>' if taxas else ''}
            <a href="{wa_link(msg)}" target="_blank" rel="noopener noreferrer" class="btn btn--whatsapp btn--sm">
              <i class="fab fa-whatsapp"></i> Tenho interesse
            </a>
          </div>
        </article>"""


def render_campanha_row(offer: dict) -> str:
    card_id = slugify(f"camp-{offer['destination']}-{offer.get('hotel','')}", "campanha-")
    destino_label = offer["title"]
    msg = f"Olá, Babi! Tenho interesse na campanha {destino_label}."
    extras = []
    if offer.get("nota"):
        extras.append(offer["nota"])
    if offer.get("chd"):
        extras.append(offer["chd"])
    if offer.get("fornecedor"):
        extras.append(offer["fornecedor"])
    if offer.get("exclusivo"):
        extras.append(str(offer["exclusivo"]))
    summary = " · ".join(html.escape(x) for x in extras if x)
    long_note = (offer.get("nota") or "")
    details = ""
    if len(long_note) > 90:
        summary = html.escape((offer.get("chd") or "")[:80])
        details = (
            '<details class="oferta-row__details">'
            "<summary>Ver condições</summary>"
            f"<p>{html.escape(long_note)}</p>"
            "</details>"
        )
    attrs = (
        f'id="{attr(card_id)}" data-destino="{attr(destino_label)}" data-categoria="campanha" '
        f'data-source="operator" data-source-id="{attr(offer["id"])}" '
        f'data-sort-date="{attr(offer.get("sort_date", ""))}" data-sort-price="0" '
        f'data-destino-key="{attr(slugify(offer["destination"]))}"'
    )
    return f"""
        <article class="oferta-row catalog-item" {attrs}>
          <div class="oferta-row__main">
            <h3 class="oferta-row__title">{html.escape(offer['destination'])}</h3>
            <p class="oferta-row__meta">{html.escape(offer.get("hotel") or "Consulte hotel participante")}</p>
            <div class="oferta-row__legs">
              <div class="oferta-row__leg">
                <span class="oferta-row__kicker">Benefício</span>
                <strong>{html.escape(offer.get("desconto") or "Consulte")}</strong>
              </div>
              <div class="oferta-row__leg">
                <span class="oferta-row__kicker">Hospedagem</span>
                <strong>{html.escape(offer.get("periodo_hospedagem") or "Consulte")}</strong>
              </div>
              <div class="oferta-row__leg">
                <span class="oferta-row__kicker">Vendas até</span>
                <strong>{html.escape(offer.get("periodo_venda") or "Consulte")}</strong>
              </div>
            </div>
            {f'<p class="oferta-row__note">{summary}</p>' if summary else ''}
            {details}
          </div>
          <div class="oferta-row__price">
            <a href="{wa_link(msg)}" target="_blank" rel="noopener noreferrer" class="btn btn--whatsapp btn--sm">
              <i class="fab fa-whatsapp"></i> Quero saber mais
            </a>
          </div>
        </article>"""


def existing_card_ids(index_html: str) -> set[str]:
    return set(re.findall(r'<article class="card[^"]*" id="([^"]+)"', index_html))


def match_offer_to_card(offer: dict, card_ids: set[str]) -> str | None:
    stem = local_image_stem(offer["source_slug"], offer["destination"])
    if stem in card_ids:
        return stem
    dest = normalize(offer["destination"])
    for cid in card_ids:
        if dest and dest in normalize(cid.replace("pacote-", "").replace("-", " ")):
            return cid
    return None


def write_fragments(pacotes: list[dict], voos: list[dict], campanhas: list[dict]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "pacotes-sync.html").write_text(
        "\n".join(render_pacote_card(o) for o in pacotes), encoding="utf-8"
    )
    (GENERATED / "promo-voos-cards.html").write_text(
        "\n".join(render_voo_row(o) for o in voos), encoding="utf-8"
    )
    (GENERATED / "campanhas-cards.html").write_text(
        "\n".join(render_campanha_row(o) for o in campanhas), encoding="utf-8"
    )

def save_sync_state(
    pacotes: list[dict],
    voos: list[dict],
    campanhas: list[dict],
    stats: dict,
    cotado_em: str,
) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_sync": datetime.now().isoformat(timespec="seconds"),
        "source": SOURCE_URL,
        "cotado_em": cotado_em,
        "stats": stats,
        "offers": {"pacotes": pacotes, "promo_voos": voos, "campanhas": campanhas},
    }
    SYNC_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza ofertas da operadora")
    parser.add_argument("--apply", action="store_true", help="Reservado para futuras atualizações in-place em index.html")
    parser.add_argument("--download-images", action="store_true", help="Baixa imagens ausentes dos pacotes")
    args = parser.parse_args()

    print("Coletando fonte…")
    html = fetch_html()
    dados = extract_dados(html)
    pacotes_raw = extract_json_array(html, "PACOTES")
    voos_raw = extract_json_array(html, "PV_SNAPSHOT")
    promos_raw = dados.get("promos") or []
    cotado_em = dados.get("cotado_em") or ""

    pacotes, pacote_stats = filter_pacotes(pacotes_raw)
    voos, voo_stats = filter_promo_voos(voos_raw)
    campanhas, camp_stats = filter_campanhas(promos_raw)

    if args.download_images:
        seen: set[str] = set()
        for offer in pacotes:
            stem = local_image_stem(offer["source_slug"], offer["destination"])
            if stem in seen:
                continue
            seen.add(stem)
            download_image(offer.get("capa", ""), stem)

    write_fragments(pacotes, voos, campanhas)

    index_ids = existing_card_ids((ROOT / "index.html").read_text(encoding="utf-8"))
    matched = sum(1 for o in pacotes if match_offer_to_card(o, index_ids))

    stats = {
        "coleta": {
            "pacotes_fonte": len(pacotes_raw),
            "promo_voos_fonte": len(voos_raw),
            "campanhas_fonte": len(promos_raw),
        },
        "filtro_pacotes": pacote_stats,
        "filtro_voos": voo_stats,
        "filtro_campanhas": camp_stats,
        "publicados": {
            "pacotes": len(pacotes),
            "promo_voos": len(voos),
            "campanhas": len(campanhas),
        },
        "reconciliacao_index": {"cards_existentes": len(index_ids), "pacotes_correspondidos": matched},
    }
    save_sync_state(pacotes, voos, campanhas, stats, cotado_em)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\nArquivos gerados em {GENERATED} e {SYNC_FILE}")
    if args.apply:
        print("Nota: cards da home permanecem curados; catálogo expandido vai para pacotes.html via _build_pacotes.py")


if __name__ == "__main__":
    main()
