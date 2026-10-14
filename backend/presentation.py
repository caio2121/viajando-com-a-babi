from __future__ import annotations

import html
import urllib.parse
from datetime import date
from typing import Iterable


def whatsapp_url(message: str, number: str) -> str:
    return f"https://wa.me/{number}?text={urllib.parse.quote(message, safe='')}"


def _safe_dates(value: object) -> list[str]:
    result: list[str] = []
    for raw in str(value or "").replace(";", ",").split(","):
        candidate = raw.strip()
        if not candidate:
            continue
        try:
            date.fromisoformat(candidate)
        except ValueError:
            continue
        result.append(candidate)
    return result


def render_manual_package(data: dict, whatsapp_number: str) -> str:
    title = str(data.get("title") or "").strip()
    destination = str(data.get("destination") or title).strip()
    origin_bucket = str(data.get("origin_bucket") or "sem-aereo").strip()
    origin_airport = str(data.get("origin_airport") or "").strip()
    origin_city = str(data.get("origin_city") or "").strip()
    dates = _safe_dates(data.get("dates"))
    sort_date = dates[0] if dates else ""
    price = float(data.get("price") or 0)
    image_url = str(data.get("image_url") or "assets/og-share.jpeg").strip()
    if image_url.startswith("javascript:"):
        image_url = "assets/og-share.jpeg"
    features: Iterable[object] = data.get("features") or []
    features = [str(item).strip() for item in features if str(item).strip()][:8]
    category = "completo" if origin_bucket != "sem-aereo" else "sem-aereo"
    offer_type = "com-aereo" if origin_bucket != "sem-aereo" else "sem-aereo"
    source_id = str(data.get("external_id") or "manual")
    escaped_title = html.escape(title)
    escaped_destination = html.escape(destination)
    escaped_dates = html.escape(",".join(dates), quote=True)
    escaped_price = f"{price:.2f}" if price > 0 else ""
    date_label = " · ".join(dates) or "Consulte datas"
    price_label = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if price > 0 else "Consulte o valor"
    origin_feature = ""
    if origin_city or origin_airport:
        origin_feature = (
            f'<li><i class="fas fa-plane"></i> Saída {html.escape(origin_city)}'
            f'{f" ({html.escape(origin_airport)})" if origin_airport else ""}</li>'
        )
    elif origin_bucket == "sem-aereo":
        origin_feature = '<li><i class="fas fa-bed"></i> Pacote sem aéreo · consulte condições</li>'
    feature_html = "".join(f'<li><i class="fas fa-check"></i> {html.escape(item)}</li>' for item in features)
    message = f"Olá, Babi! Tenho interesse na oferta {title}."
    return f'''
        <article class="card reveal catalog-item" id="{html.escape(source_id, quote=True)}"
          data-destino="{escaped_title}" data-categoria="{category}" data-source="manual"
          data-source-id="{html.escape(source_id, quote=True)}" data-sort-date="{sort_date}"
          data-dates="{escaped_dates}" data-sort-price="{escaped_price}"
          data-origem="{html.escape(origin_bucket, quote=True)}"
          data-origem-iata="{html.escape(origin_airport, quote=True)}"
          data-destination="{escaped_destination}" data-destino-key="{html.escape(destination.lower(), quote=True)}"
          data-group-label="{escaped_destination}" data-offer-name="{escaped_title}"
          data-tipo="{offer_type}">
          <div class="card__img-wrap">
            <img src="{html.escape(image_url, quote=True)}" alt="{escaped_destination}: {escaped_title}"
              width="400" height="260" data-lightbox decoding="async" loading="lazy">
            <span class="card__badge">{html.escape(date_label)}</span>
          </div>
          <div class="card__body">
            <h4 class="card__title">{escaped_destination} <span>{escaped_title}</span></h4>
            <ul class="card__features">{origin_feature}{feature_html}</ul>
            <div class="card__footer">
              <div class="card__preco"><span class="card__total">A partir de <strong>{html.escape(price_label)}</strong></span></div>
              <a href="{whatsapp_url(message, whatsapp_number)}" target="_blank" rel="noopener noreferrer"
                class="btn btn--whatsapp btn--full"><i class="fab fa-whatsapp"></i> Quero esse pacote!</a>
            </div>
          </div>
        </article>'''
