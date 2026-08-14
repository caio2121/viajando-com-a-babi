"""Regenera pacotes.html a partir dos cards em index.html + ofertas sincronizadas.

Unifica pacotes manuais e sincronizados no mesmo catálogo (sem seção 'Mais ofertas').
Executar após alterar pacotes na home ou após python _sync_operator.py.
"""
from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

import _catalog_ui as ui
import _dates as dates

root = Path(__file__).parent
TODAY = dates.TODAY
ARTICLE_RE = re.compile(r"<article\b[^>]*class=\"[^\"]*card[\s\S]*?</article>", re.I)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower().strip()


def slugify(text: str) -> str:
    base = normalize(text)
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def money_to_float(text: str) -> float:
    if not text:
        return 0.0
    m = re.search(r"([\d.]+,\d{2}|\d[\d.]*)", text.replace("R$", ""))
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


def infer_origin(card: str) -> tuple[str, str]:
    if re.search(r"\b(GIG|SDU)\b|Rio de Janeiro", card):
        iata = "GIG" if "GIG" in card else ("SDU" if "SDU" in card else "")
        return "rio", iata
    if re.search(r"\b(GRU|CGH|VCP)\b|S[aã]o Paulo|Campinas", card):
        iata = next((c for c in ("GRU", "CGH", "VCP") if c in card), "")
        return "sp", iata
    return "sem-aereo", ""


def infer_tipo(card: str, categoria: str) -> str:
    blob = normalize(card)
    if "cruzeiro" in blob or "navio" in blob or "msc" in blob or "costa serena" in blob:
        return "cruzeiro"
    if categoria == "sem-aereo":
        return "sem-aereo"
    return "com-aereo"


def card_id(card: str) -> str:
    m = re.search(r'\bid="([^"]+)"', card)
    return m.group(1) if m else ""


def card_destino(card: str) -> str:
    m = re.search(r'data-destino="([^"]+)"', card)
    return m.group(1) if m else ""


def dest_overlap(sync_dest: str, manual_ids: set[str], manual_destinos: set[str]) -> bool:
    key = slugify(sync_dest)
    if not key:
        return False
    for mid in manual_ids:
        midk = mid.replace("pacote-", "")
        if key == midk or key in midk or midk in key:
            return True
    for dest in manual_destinos:
        dk = slugify(dest)
        if key == dk or key in dk or dk in key:
            return True
    return False


def enrich_card(card: str, source: str = "manual") -> str:
    if "catalog-item" not in card:
        card = card.replace('class="card reveal"', 'class="card reveal catalog-item"', 1)
        card = card.replace("class='card reveal'", "class='card reveal catalog-item'", 1)
    destino = card_destino(card)
    categoria_m = re.search(r'data-categoria="([^"]+)"', card)
    categoria = categoria_m.group(1) if categoria_m else ""
    origem, iata = infer_origin(card)
    tipo = infer_tipo(card, categoria)
    badge = re.search(r'class="card__badge">([^<]+)', card)
    total = re.search(r"Total a partir de R\$\s*([\d.]+(?:,\d{2})?)", card)
    valor_attr = re.search(r'data-valor-total="([^"]+)"', card)
    iso_dates = dates.future_iso_dates(dates.extract_departure_dates(badge.group(1) if badge else ""))
    if "data-dates=" not in card:
        card = card.replace("<article", f'<article data-dates="{html.escape(dates.dates_attr(iso_dates), quote=True)}"', 1)
    if "data-sort-date=" not in card:
        sort_date = dates.next_sort_date(iso_dates)
        card = card.replace("<article", f'<article data-sort-date="{html.escape(sort_date, quote=True)}"', 1)
    if badge and dates.sanitize_date_text(badge.group(1)) != badge.group(1):
        card = card.replace(badge.group(0), f'class="card__badge">{html.escape(dates.sanitize_date_text(badge.group(1))[:70])}', 1)
    if "data-sort-price=" not in card:
        if valor_attr:
            price = money_to_float(valor_attr.group(1))
        elif total:
            price = money_to_float(total.group(1))
        else:
            price = money_to_float(re.search(r"R\$\s*([\d.]+(?:,\d{2})?)", card).group(0) if re.search(r"R\$\s*[\d.]+", card) else "")
        price_txt = f"{price:.2f}" if price > 0 else ""
        card = card.replace("<article", f'<article data-sort-price="{price_txt}"', 1)
    if "data-origem=" not in card:
        card = card.replace("<article", f'<article data-origem="{origem}" data-origem-iata="{iata}"', 1)
    if "data-destino-key=" not in card:
        card = card.replace("<article", f'<article data-destino-key="{slugify(destino)}"', 1)
    if "data-tipo=" not in card:
        card = card.replace("<article", f'<article data-tipo="{tipo}"', 1)
    if "data-source=" not in card:
        card = card.replace("<article", f'<article data-source="{source}"', 1)
    return card


index = (root / "index.html").read_text(encoding="utf-8")
start = index.find('<div class="pacotes__category" id="pacotes-completos">')
cta_start = index.find('<div class="pacotes__cta-extra">')
cta_end = index.find("</div>", cta_start) + len("</div>")
blocks = index[start:cta_start]
cta_block = index[cta_start:cta_end]

manual_cards = [enrich_card(c, "manual") for c in ARTICLE_RE.findall(blocks)]
manual_ids = {card_id(c) for c in manual_cards}
manual_destinos = {card_destino(c) for c in manual_cards}

sync_cards: list[str] = []
sync_file = root / "data" / "generated" / "pacotes-sync.html"
if sync_file.exists():
    for card in ARTICLE_RE.findall(sync_file.read_text(encoding="utf-8")):
        dest = card_destino(card)
        cid = card_id(card)
        stem = re.sub(r"-(gig|sdu|gru|cgh|vcp|rio|sp|sem-aereo|na)$", "", cid, flags=re.I)
        if cid in manual_ids or stem in manual_ids:
            continue
        if dest_overlap(dest, manual_ids, manual_destinos):
            continue
        sync_cards.append(enrich_card(card, "operator"))

all_cards = manual_cards + sync_cards

head_assets = (root / "_partials/head-assets.html").read_text(encoding="utf-8")
ga4 = (root / "_partials/ga4.html").read_text(encoding="utf-8")
hub_header = (root / "_partials/hub-header.html").read_text(encoding="utf-8")

head = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pacotes de viagem | Viajando com a Babi</title>
  <meta name="description" content="Catálogo de pacotes de viagem: Nordeste, Gramado, João Pessoa, Cone Sul, México, Caribe, Dubai, Disneyland e cruzeiros. Agência Cadastur. Fale com a Babi." />
  <link rel="canonical" href="https://viajandocomababi.com.br/pacotes.html" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://viajandocomababi.com.br/pacotes.html" />
  <meta property="og:title" content="Pacotes de viagem | Viajando com a Babi" />
  <meta property="og:description" content="Pacotes de viagem com aéreo e hospedagem para destinos nacionais e internacionais." />
  <meta property="og:image" content="https://viajandocomababi.com.br/assets/og-share.jpeg" />
  <meta property="og:locale" content="pt_BR" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="icon" type="image/png" href="assets/logo-vcb.png" />
{head_assets}  <link rel="stylesheet" href="style.css?v={ui.CSS_VERSION}" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{ "@type": "WebPage", "@id": "https://viajandocomababi.com.br/pacotes.html#webpage", "url": "https://viajandocomababi.com.br/pacotes.html", "name": "Pacotes de viagem | Viajando com a Babi", "isPartOf": {{ "@id": "https://viajandocomababi.com.br/#website" }} }},
      {{ "@type": "BreadcrumbList", "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Início", "item": "https://viajandocomababi.com.br/" }},
        {{ "@type": "ListItem", "position": 2, "name": "Pacotes de viagem", "item": "https://viajandocomababi.com.br/pacotes.html" }}
      ]}}
    ]
  }}
  </script>
{ga4}</head>
<body>
"""

main = f"""<main id="conteudo-principal">
  <section id="pacotes" class="pacotes pacotes-page">
    <div class="container pacotes-page__header">
      <nav class="breadcrumb breadcrumb--light" aria-label="Navegação"><a href="/">Início</a> / Pacotes de viagem</nav>
      <span class="label label--center">Catálogo completo</span>
      <h1 class="section-title">Pacotes de viagem</h1>
      <p class="section-sub">Pacotes com aéreo, hospedagem e serviços principais, além de cruzeiros e roteiros em grupo. Quer algo sob medida? <a href="roteiro-personalizado.html">Monte um roteiro personalizado</a>.</p>
    </div>
    <div class="container" data-catalog-root="pacotes">
{ui.toolbar("pacotes", 24)}
      <div class="pacotes__grid" data-catalog-list>
{"".join(all_cards)}
      </div>
{ui.empty_state("pacotes")}
{cta_block}

    </div>
  </section>
</main>
{ui.filter_modal()}
"""

hub_footer = (root / "_partials/hub-footer.html").read_text(encoding="utf-8")
lightbox = """
  <div class="lightbox-overlay" id="lightbox" role="dialog" aria-modal="true" aria-label="Visualizar imagem">
    <button class="lightbox__close" id="lightboxClose" aria-label="Fechar imagem">&#x2715;</button>
    <img class="lightbox__img" id="lightboxImg" src="" alt="" />
  </div>

"""
cookie_idx = hub_footer.find('<div id="cookieBanner"')
template_tail = hub_footer[:cookie_idx] + lightbox + hub_footer[cookie_idx:]

(root / "pacotes.html").write_text(head + hub_header + main + template_tail, encoding="utf-8")
print(f"pacotes.html atualizado ({len(manual_cards)} manuais + {len(sync_cards)} sincronizados)")
