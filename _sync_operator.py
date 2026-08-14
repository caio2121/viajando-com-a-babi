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

import _dates as dates
import _money as money

ROOT = Path(__file__).parent
DATA = ROOT / "data"
GENERATED = DATA / "generated"
SYNC_FILE = DATA / "operator-sync.json"
SOURCE_URL = "https://viajandocomdesconto.com/"
WA_NUMBER = "5521920064617"
TODAY = dates.TODAY

RIO_IATA = {"GIG", "SDU", "RIO"}
SP_IATA = {"GRU", "CGH", "VCP", "SAO"}
ORIGIN_PRIORITY = ("rio", "sp")
JS_LEAK_RE = re.compile(r"GMT[+-]|Horário Padrão|Invalid Date|\bNaN\b|\bundefined\b|\bnull\b", re.I)

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


def extract_js_object(html: str, needle: str) -> dict:
    idx = html.find(needle)
    if idx < 0:
        raise RuntimeError(f"{needle} não encontrado na fonte")
    start = html.find("{", idx)
    if start < 0:
        raise RuntimeError(f"Objeto após {needle} não encontrado")
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(html[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : i + 1])
    raise RuntimeError(f"Objeto {needle} desbalanceado")


def extract_dados(html: str) -> dict:
    match = re.search(r'id="dados"[^>]*>(\{.*?\})</script>', html, re.S)
    if not match:
        raise RuntimeError("Bloco dados não encontrado na fonte")
    return json.loads(match.group(1))


def extract_pvoo_payload(html: str) -> dict:
    return extract_js_object(html, "window.__PVOO_PAYLOAD = ")


def as_text(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    return str(value or "")


def parse_number(text: str | None) -> float | None:
    if text is None or text == "":
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def is_range_valid(text: str) -> bool:
    return is_sale_period_valid(text)


def classify_origin(iata: str | None, cidade: str | None) -> str | None:
    code = (iata or "").upper()
    city = normalize(cidade or "")
    if code in RIO_IATA or "rio de janeiro" in city:
        return "rio"
    if code in SP_IATA or "sao paulo" in city or city == "campinas":
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


def package_departure_dates(*texts: str) -> list[str]:
    return dates.future_iso_dates(dates.extract_departure_dates(*texts))


def next_future_iso(*texts: str) -> str:
    return dates.next_sort_date(package_departure_dates(*texts))


def is_sale_period_valid(text: str) -> bool:
    start, end = dates.parse_date_range(text)
    if end:
        return end >= TODAY
    if start:
        return start >= TODAY
    return True


def format_money(value: float | None, currency: str = "BRL") -> str:
    if value is None:
        return ""
    rounded = int(round(value))
    formatted = f"{rounded:,}".replace(",", ".")
    prefix = "US$" if currency == "USD" else "R$"
    return f"{prefix}&nbsp;{formatted}"


def mapa_names(mapa: dict, iata: str) -> tuple[str, str]:
    entry = mapa.get(iata) or []
    origin_name = entry[0] if len(entry) > 0 else iata
    dest_name = entry[1] if len(entry) > 1 else (entry[0] if entry else iata)
    return origin_name, dest_name


def tipo_from_offer(offer: dict) -> str:
    blob = normalize(" ".join(offer.get("inclui") or []) + " " + (offer.get("title") or "") + " " + (offer.get("destination") or ""))
    if "cruzeiro" in blob or "navio" in blob or "msc" in blob:
        return "cruzeiro"
    if offer.get("flight_included"):
        return "com-aereo"
    return "sem-aereo"


def money_to_float(text: str) -> float:
    return money.money_to_float(text)


def pick_cheapest_hotel(hoteis: list[dict] | None) -> dict | None:
    if not hoteis:
        return None
    return min(hoteis, key=lambda h: money.parse_brl(h.get("preco")) or float("inf"))


def package_has_components(inclui: list | None, hoteis: list | None) -> bool:
    if hoteis:
        return True
    blob = money.normalize_text(" ".join(str(x) for x in (inclui or [])))
    markers = (
        "hospedagem",
        "hotel",
        "transfer",
        "ingresso",
        "passeio",
        "servico",
        "serviço",
        "cafe da manha",
        "all inclusive",
    )
    return any(m in blob for m in markers)


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
            parsed_dates = dates.extract_departure_dates(
                as_text(origin.get("data")),
                as_text(origin.get("outras")),
            )
            departure_dates = dates.future_iso_dates(parsed_dates)
            if parsed_dates and not departure_dates:
                stats["ignored_expired"] += 1
                continue
            hotel = pick_cheapest_hotel(origin.get("hoteis"))
            inclui = origin.get("inclui") or []
            hoteis = origin.get("hoteis") or []
            installment_text = (hotel.get("parcela") if hotel else "") or origin.get("min_parcela") or ""
            airfare_original = money.parse_brl(origin.get("de"))
            airfare_sale = money.parse_brl(origin.get("por"))
            fees_text = (hotel.get("taxas") if hotel else "") or origin.get("taxas") or ""
            fees_value = money.parse_brl(fees_text)
            package_total, price_source = money.resolve_package_total(
                hotel_price_text=hotel.get("preco") if hotel else None,
                installment_text=installment_text,
                airfare_sale=airfare_sale,
                has_package_components=package_has_components(inclui, hoteis),
            )
            inst_count, inst_value = money.parse_installment(installment_text)
            total_display = money.format_brl(package_total) if package_total is not None else ""
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
                "departure_date": dates.sanitize_date_text(as_text(origin.get("data"))),
                "additional_dates": dates.sanitize_date_text(as_text(origin.get("outras"))),
                "departure_dates": departure_dates,
                "flight_included": flight,
                "categoria_site": "sem-aereo" if not flight else "completo",
                "capa": pkg.get("capa") or "",
                "inclui": inclui,
                "hoteis": hoteis,
                "taxas": fees_text,
                "fees": fees_value,
                "de": origin.get("de") or "",
                "por": origin.get("por") or "",
                "airfare_original_price": airfare_original,
                "airfare_sale_price": airfare_sale,
                "installments": installment_text,
                "installment_count": inst_count,
                "installment_value": inst_value,
                "total_price": total_display,
                "package_total_price": package_total,
                "price_source": price_source,
                "currency": "BRL",
                "evento": bool(pkg.get("evento")),
                "pacote_categoria": pkg.get("categoria") or "",
                "sort_date": dates.next_sort_date(departure_dates),
                "sort_price": package_total,
            }
            offer["tipo"] = tipo_from_offer(offer)
            selected.append(offer)
            if bucket == "rio":
                stats["rio"] += 1
            elif bucket == "sp":
                stats["sp"] += 1

    return selected, stats


def parse_pvoo_row(fields: list[str], mapa: dict, usd_rate: float | None) -> dict | None:
    if len(fields) < 7:
        return None
    origin_iata = (fields[0] or "").upper()
    dest_iata = (fields[1] or "").upper()
    departure = dates.parse_yymmdd(fields[2] if len(fields) > 2 else "")
    returning = dates.parse_yymmdd(fields[3] if len(fields) > 3 else "")
    nights_raw = parse_number(fields[4] if len(fields) > 4 else "")
    seats_raw = parse_number(fields[5] if len(fields) > 5 else "")
    price_raw = parse_number(fields[6] if len(fields) > 6 else "")
    currency_flag = parse_number(fields[7] if len(fields) > 7 else "") or 0
    deadline = dates.parse_yymmdd(fields[8] if len(fields) > 8 else "")
    dep_time = dates.parse_hhmm(fields[9] if len(fields) > 9 else "")
    ret_time = dates.parse_hhmm(fields[11] if len(fields) > 11 else "")
    tax_raw = parse_number(fields[13] if len(fields) > 13 else "")
    dest_flag = fields[14].strip() if len(fields) > 14 and fields[14] else ""
    airline = (fields[15] or "").strip() if len(fields) > 15 else ""

    origin_city, _ = mapa_names(mapa, origin_iata)
    _, destination = mapa_names(mapa, dest_iata)
    bucket = classify_origin(origin_iata, origin_city)
    currency = "USD" if currency_flag else "BRL"
    nights = int(nights_raw) if nights_raw else dates.nights_between(departure, returning)
    seats = int(seats_raw) if seats_raw is not None else None
    tax = tax_raw if tax_raw is not None else None
    sort_price = None
    if price_raw is not None:
        if currency == "USD" and usd_rate:
            sort_price = round(price_raw * usd_rate, 2)
        else:
            sort_price = round(price_raw, 2)

    destination_type = "nacional" if dest_flag == "1" else "internacional" if dest_flag == "0" else None
    return {
        "origin_iata": origin_iata,
        "dest_iata": dest_iata,
        "origin_city": origin_city,
        "destination": destination,
        "origin_bucket": bucket,
        "departure": departure,
        "returning": returning,
        "departure_time": dep_time,
        "return_time": ret_time,
        "nights": nights,
        "seats": seats,
        "price": price_raw,
        "tax": tax,
        "currency": currency,
        "deadline": deadline,
        "destination_type": destination_type,
        "airline": airline or None,
        "sort_price": sort_price,
        "raw": fields,
    }


def filter_promo_voos(payload: dict) -> tuple[list[dict], dict]:
    blob = payload.get("blob") or ""
    mapa = payload.get("mapa") or {}
    usd_rate = payload.get("usd")
    try:
        usd_rate = float(usd_rate) if usd_rate else None
    except (TypeError, ValueError):
        usd_rate = None

    lines = [ln.strip() for ln in blob.split("\n") if ln.strip()]
    selected: list[dict] = []
    seen: set[str] = set()
    stats = {
        "total": len(lines),
        "rio": 0,
        "sp": 0,
        "nacional": 0,
        "internacional": 0,
        "ignored_origin": 0,
        "ignored_expired": 0,
        "ignored_invalid_date": 0,
        "duplicates_removed": 0,
    }

    for line in lines:
        parsed = parse_pvoo_row(line.split("|"), mapa, usd_rate)
        if not parsed:
            stats["ignored_invalid_date"] += 1
            continue
        if not parsed["origin_bucket"]:
            stats["ignored_origin"] += 1
            continue
        dep = parsed["departure"]
        ret = parsed["returning"]
        if dep is None:
            stats["ignored_invalid_date"] += 1
            continue
        if parsed["deadline"] and parsed["deadline"] < TODAY:
            stats["ignored_expired"] += 1
            continue
        if dep < TODAY:
            stats["ignored_expired"] += 1
            continue
        if not dates.itinerary_valid(dep, ret, parsed["departure_time"], parsed["return_time"]):
            stats["ignored_invalid_date"] += 1
            continue

        fp = fingerprint(
            "voo",
            parsed["origin_iata"],
            parsed["dest_iata"],
            dep.isoformat(),
            ret.isoformat() if ret else "",
            parsed["departure_time"] or "",
            parsed["return_time"] or "",
            str(parsed["price"] if parsed["price"] is not None else ""),
            str(parsed["tax"] if parsed["tax"] is not None else ""),
        )
        if fp in seen:
            stats["duplicates_removed"] += 1
            continue
        seen.add(fp)

        source_id = (
            f"voo:{parsed['origin_iata']}:{parsed['dest_iata']}:"
            f"{dep.isoformat()}:{(ret.isoformat() if ret else '')}:"
            f"{parsed['price']}:{parsed['tax']}:{parsed['departure_time'] or ''}"
        )
        iso_dates = [dep.isoformat()]
        offer = {
            "id": source_id,
            "fingerprint": fp,
            "category": "promo-voo",
            "title": parsed["destination"],
            "destination": parsed["destination"],
            "destination_type": parsed["destination_type"],
            "destination_airport": parsed["dest_iata"] or None,
            "origin_city": parsed["origin_city"],
            "origin_airport": parsed["origin_iata"],
            "origin_bucket": parsed["origin_bucket"],
            "departure_date": dep.isoformat(),
            "departure_time": parsed["departure_time"],
            "return_date": ret.isoformat() if ret else None,
            "return_time": parsed["return_time"],
            "departure_dates": iso_dates,
            "nights": parsed["nights"],
            "price": parsed["price"],
            "tax": parsed["tax"],
            "currency": parsed["currency"],
            "seats": parsed["seats"],
            "last_seats": None,
            "airline": parsed["airline"],
            "sort_date": dep.isoformat(),
            "sort_price": parsed["sort_price"],
        }
        selected.append(offer)
        stats[parsed["origin_bucket"]] += 1
        if parsed["destination_type"] == "nacional":
            stats["nacional"] += 1
        elif parsed["destination_type"] == "internacional":
            stats["internacional"] += 1

    selected.sort(key=lambda o: (o.get("sort_date") or "9999-12-31", o.get("destination") or "", o.get("origin_airport") or ""))
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
    badge = dates.sanitize_date_text(as_text(offer.get("departure_date")))
    extra = dates.sanitize_date_text(as_text(offer.get("additional_dates")))
    if extra:
        badge = f"{badge} · {extra}" if badge else extra

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
    package_total = offer.get("package_total_price")
    if package_total is None and offer.get("sort_price") not in (None, ""):
        package_total = offer.get("sort_price")
    if isinstance(package_total, (int, float)) and package_total > 0:
        total_html = (
            f'A partir de <strong>{money.format_brl(float(package_total), html_nbsp=True)}</strong>'
        )
    else:
        total_html = "Consulte o valor"

    if offer.get("installments"):
        m = re.search(r"(\d+)x\s*de?\s*R\$\s*([\d.,]+)", offer["installments"], re.I)
        if m:
            parcela_html = f'{html.escape(m.group(1))}x de {br_money_html("R$ " + m.group(2))}'
        else:
            parcela_html = html.escape(offer["installments"])

    taxas_note = ""
    if offer.get("taxas") or offer.get("fees"):
        taxas_note = "+ taxas · sujeito a alteração"
    elif package_total:
        taxas_note = "sujeito a alteração"

    subtitle = offer["title"].replace(offer["destination"], "").strip(" ·:-")[:60]
    msg = f"Olá, Babi! Tenho interesse na oferta {destino_label}."
    origem = offer.get("origin_bucket") or "sem-aereo"
    tipo = offer.get("tipo") or tipo_from_offer(offer)
    alt = f"{offer['destination']}: {offer['title']}"
    sort_price = offer.get("sort_price")
    if sort_price in (None, ""):
        price_attr = ""
    else:
        price_attr = f"{float(sort_price):.2f}"
    dates_attr = dates.dates_attr(offer.get("departure_dates") or [])
    attrs = (
        f'id="{attr(card_id)}" data-destino="{attr(destino_label)}" '
        f'data-categoria="{attr(offer["categoria_site"])}" data-source="operator" '
        f'data-source-id="{attr(offer["id"])}" data-sort-date="{attr(offer.get("sort_date", ""))}" '
        f'data-dates="{attr(dates_attr)}" data-sort-price="{attr(price_attr)}" data-origem="{attr(origem)}" '
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
                <span class="card__total">{total_html}</span>
                {'<span class="card__parcela">' + parcela_html + '</span>' if parcela_html else ''}
                {'<span class="card__taxas">' + taxas_note + '</span>' if taxas_note else ''}
              </div>
              <a href="{wa_link(msg)}"
                 target="_blank" rel="noopener noreferrer"
                 class="btn btn--whatsapp btn--full">
                <i class="fab fa-whatsapp"></i> Quero esse pacote!
              </a>
            </div>
          </div>
        </article>"""


def _iso_to_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _leg_label(day: date | None, hhmm: str | None) -> str:
    label = dates.format_short_pt(day)
    if hhmm:
        label = f"{label} · {hhmm}" if label else hhmm
    return label


def _route_label(origin: str | None, dest: str | None) -> str:
    left = origin or ""
    right = dest or ""
    if left and right:
        return f"{left} → {right}"
    return left or right


def render_voo_row(offer: dict) -> str:
    dep_day = _iso_to_date(offer.get("departure_date"))
    ret_day = _iso_to_date(offer.get("return_date"))
    card_id = slugify(
        f"voo-{offer.get('origin_airport')}-{offer.get('destination')}-{offer.get('departure_date')}-{offer.get('return_date')}",
        "promo-",
    )
    destino_label = offer["title"]
    msg = f"Olá, Babi! Tenho interesse na promoção de voo {destino_label}."
    nights = offer.get("nights")
    nights_html = f" · {nights} noites" if nights else ""
    preco = format_money(offer.get("price"), offer.get("currency") or "BRL")
    tax_value = offer.get("tax")
    taxas = format_money(tax_value, "BRL") if tax_value else ""
    origin_iata = offer.get("origin_airport") or ""
    dest_iata = offer.get("destination_airport") or ""
    dest_name = offer.get("destination") or ""
    dest_leg = dest_iata or dest_name
    ida_label = _leg_label(dep_day, offer.get("departure_time"))
    volta_label = _leg_label(ret_day, offer.get("return_time"))
    origem_txt = (
        f"{offer['origin_city']} ({origin_iata})"
        if origin_iata
        else (offer.get("origin_city") or "")
    )
    dest_type = offer.get("destination_type") or ""
    price_attr = "" if offer.get("sort_price") in (None, "") else str(offer.get("sort_price"))
    dates_attr = dates.dates_attr(offer.get("departure_dates") or ([offer.get("departure_date")] if offer.get("departure_date") else []))
    attrs = (
        f'id="{attr(card_id)}" data-destino="{attr(destino_label)}" data-categoria="promo-voo" '
        f'data-source="operator" data-source-id="{attr(offer["id"])}" '
        f'data-sort-date="{attr(offer.get("sort_date", ""))}" data-dates="{attr(dates_attr)}" '
        f'data-sort-price="{attr(price_attr)}" data-origem="{attr(offer.get("origin_bucket", ""))}" '
        f'data-origem-iata="{attr(origin_iata)}" data-destino-key="{attr(slugify(offer["destination"]))}" '
        f'data-destino-tipo="{attr(dest_type)}"'
    )
    volta_cell = ""
    if ret_day or dest_leg:
        volta_cell = (
            f'<div class="oferta-row__leg"><span class="oferta-row__kicker">Volta</span>'
            f'<strong>{html.escape(volta_label)}</strong>'
            f'<span>{html.escape(_route_label(dest_leg, origin_iata))}</span></div>'
        )
    return f"""
        <article class="oferta-row catalog-item" {attrs}>
          <div class="oferta-row__main">
            <h3 class="oferta-row__title">{html.escape(offer['destination'])}{html.escape(nights_html)}</h3>
            <p class="oferta-row__meta">Saindo de {html.escape(origem_txt)}</p>
            <div class="oferta-row__legs">
              <div class="oferta-row__leg">
                <span class="oferta-row__kicker">Ida</span>
                <strong>{html.escape(ida_label)}</strong>
                <span>{html.escape(_route_label(origin_iata, dest_leg))}</span>
              </div>
              {volta_cell}
            </div>
          </div>
          <div class="oferta-row__price">
            {'<span class="oferta-row__value">' + preco + '</span>' if preco else ''}
            {'<span class="oferta-row__tax">+ taxa ' + taxas + '</span>' if taxas else ''}
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
    if SYNC_FILE.exists():
        try:
            old = json.loads(SYNC_FILE.read_text(encoding="utf-8"))
            if old.get("offers") == payload["offers"] and old.get("stats") == stats and old.get("cotado_em") == cotado_em:
                payload["last_sync"] = old.get("last_sync") or payload["last_sync"]
        except (OSError, json.JSONDecodeError):
            pass
    SYNC_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_voos(voos: list[dict]) -> dict:
    inverted = 0
    for offer in voos:
        dep = _iso_to_date(offer.get("departure_date"))
        ret = _iso_to_date(offer.get("return_date"))
        if dep and ret and not dates.itinerary_valid(dep, ret, offer.get("departure_time"), offer.get("return_time")):
            inverted += 1
    leaks = []
    html_path = GENERATED / "promo-voos-cards.html"
    if html_path.exists():
        text = html_path.read_text(encoding="utf-8")
        leaks = JS_LEAK_RE.findall(text)
    if inverted:
        raise RuntimeError(f"Voos com retorno anterior à ida: {inverted}")
    if leaks:
        raise RuntimeError(f"Datas JS brutas no HTML: {sorted(set(leaks))}")
    return {
        "inverted": inverted,
        "js_leaks": len(leaks),
        "sem_preco": sum(1 for o in voos if o.get("price") in (None, "")),
        "sem_taxa": sum(1 for o in voos if not o.get("tax")),
        "com_horario": sum(1 for o in voos if o.get("departure_time") or o.get("return_time")),
        "com_aeroporto_destino": sum(1 for o in voos if o.get("destination_airport")),
    }


def validate_pacotes(pacotes: list[dict]) -> dict:
    """Auditoria semântica de preços dos pacotes sincronizados."""
    with_total = 0
    without_total = 0
    with_installment = 0
    with_airfare = 0
    inconsistencies = []
    airfare_as_total = []
    consulte = []

    for offer in pacotes:
        title = offer.get("title") or offer.get("id") or ""
        total = offer.get("package_total_price")
        if total is None:
            total = offer.get("sort_price")
        air = offer.get("airfare_sale_price")
        if air is None:
            air = money.parse_brl(offer.get("por"))
        inst_count = offer.get("installment_count")
        inst_value = offer.get("installment_value")
        if inst_count is None or inst_value is None:
            inst_count, inst_value = money.parse_installment(offer.get("installments"))

        if air is not None and air > 0:
            with_airfare += 1
        if inst_count and inst_value:
            with_installment += 1

        if total is None or total <= 0:
            without_total += 1
            consulte.append(title)
            continue

        with_total += 1
        if total <= 0:
            inconsistencies.append({"title": title, "reason": "total_non_positive", "total": total})
        if inst_count is not None and inst_count <= 0:
            inconsistencies.append({"title": title, "reason": "installment_count_invalid", "count": inst_count})
        if inst_value is not None and inst_value <= 0:
            inconsistencies.append({"title": title, "reason": "installment_value_invalid", "value": inst_value})
        if inst_count and inst_value:
            calc = inst_count * inst_value
            if abs(total - calc) > money.price_tolerance(calc):
                inconsistencies.append(
                    {
                        "title": title,
                        "reason": "total_vs_installment",
                        "total": total,
                        "installment_total": calc,
                        "diff": round(abs(total - calc), 2),
                    }
                )

        has_components = package_has_components(offer.get("inclui"), offer.get("hoteis"))
        if air is not None and abs(total - air) < 0.01 and has_components:
            airfare_as_total.append(
                {
                    "title": title,
                    "total": total,
                    "airfare_sale_price": air,
                    "price_source": offer.get("price_source"),
                }
            )

    return {
        "analisados": len(pacotes),
        "com_preco_total": with_total,
        "sem_preco_total": without_total,
        "com_parcelamento": with_installment,
        "com_aereo": with_airfare,
        "inconsistencias": inconsistencies,
        "aereo_como_total": airfare_as_total,
        "consulte": consulte,
    }


def print_report(voos: list[dict], voo_stats: dict, pacotes: list[dict], campanhas: list[dict], checks: dict, price_audit: dict | None = None) -> None:
    multi = sum(1 for o in pacotes if len(o.get("departure_dates") or []) > 1)
    print("\nPROMO DE VOOS")
    print(f"Bloqueios encontrados na fonte: {voo_stats.get('total', 0)}")
    print(f"Bloqueios Rio: {voo_stats.get('rio', 0)}")
    print(f"Bloqueios São Paulo: {voo_stats.get('sp', 0)}")
    print(f"Nacionais: {voo_stats.get('nacional', 0)}")
    print(f"Internacionais: {voo_stats.get('internacional', 0)}")
    print(f"Descartados por data inválida: {voo_stats.get('ignored_invalid_date', 0)}")
    print(f"Duplicatas removidas: {voo_stats.get('duplicates_removed', 0)}")
    print(f"Itens publicados: {len(voos)}")
    print("\nVALIDAÇÃO")
    print(f"Voos com retorno < ida: {checks['inverted']}")
    print(f"Datas JS brutas no HTML: {checks['js_leaks']}")
    print(f"Itens sem preço: {checks['sem_preco']}")
    print(f"Itens sem taxa: {checks['sem_taxa']}")
    print(f"Itens com horários: {checks['com_horario']}")
    print(f"Itens com aeroporto de destino: {checks['com_aeroporto_destino']}")
    print("\nPACOTES")
    print(f"Total: {len(pacotes)}")
    print(f"Com múltiplas saídas: {multi}")
    if price_audit:
        print("\nAUDITORIA DE PREÇOS (sync)")
        print(f"Pacotes analisados: {price_audit['analisados']}")
        print(f"Com preço total confiável: {price_audit['com_preco_total']}")
        print(f"Sem preço total: {price_audit['sem_preco_total']}")
        print(f"Com parcelamento: {price_audit['com_parcelamento']}")
        print(f"Com preço de aéreo: {price_audit['com_aereo']}")
        print(f"Inconsistências preço/parcela: {len(price_audit['inconsistencias'])}")
        print(f"Suspeitos aéreo=total: {len(price_audit['aereo_como_total'])}")
        for row in price_audit["inconsistencias"][:10]:
            print(f"  ! {row}")
        for row in price_audit["aereo_como_total"][:10]:
            print(f"  ! aereo_como_total: {row}")
    print("\nCAMPANHAS")
    print(f"Publicadas: {len(campanhas)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza ofertas da operadora")
    parser.add_argument("--apply", action="store_true", help="Reservado para futuras atualizações in-place em index.html")
    parser.add_argument("--download-images", action="store_true", help="Baixa imagens ausentes dos pacotes")
    args = parser.parse_args()

    print("Coletando fonte…")
    html = fetch_html()
    dados = extract_dados(html)
    pacotes_raw = extract_json_array(html, "PACOTES")
    pvoo_payload = extract_pvoo_payload(html)
    promos_raw = dados.get("promos") or []
    cotado_em = dados.get("cotado_em") or pvoo_payload.get("ger") or ""

    pacotes, pacote_stats = filter_pacotes(pacotes_raw)
    voos, voo_stats = filter_promo_voos(pvoo_payload)
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
    checks = validate_voos(voos)
    price_audit = validate_pacotes(pacotes)

    index_ids = existing_card_ids((ROOT / "index.html").read_text(encoding="utf-8"))
    matched = sum(1 for o in pacotes if match_offer_to_card(o, index_ids))

    stats = {
        "coleta": {
            "pacotes_fonte": len(pacotes_raw),
            "promo_voos_fonte": voo_stats.get("total", 0),
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
        "validacao_voos": checks,
        "validacao_precos_pacotes": {
            "analisados": price_audit["analisados"],
            "com_preco_total": price_audit["com_preco_total"],
            "sem_preco_total": price_audit["sem_preco_total"],
            "inconsistencias": len(price_audit["inconsistencias"]),
            "aereo_como_total": len(price_audit["aereo_como_total"]),
        },
    }
    save_sync_state(pacotes, voos, campanhas, stats, cotado_em)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print_report(voos, voo_stats, pacotes, campanhas, checks, price_audit)
    print(f"\nArquivos gerados em {GENERATED} e {SYNC_FILE}")
    if args.apply:
        print("Nota: cards da home permanecem curados; catálogo expandido vai para pacotes.html via _build_pacotes.py")


if __name__ == "__main__":
    main()
