"""Gera promo-voos.html e campanhas.html a partir dos fragments sincronizados."""
import urllib.parse
from pathlib import Path

import _catalog_ui as ui

ROOT = Path(__file__).parent
GENERATED = ROOT / "data" / "generated"

PAGES = {
    "promo-voos.html": {
        "fragment": "promo-voos-cards.html",
        "kind": "voos",
        "page_size": 20,
        "title": "Promoções de voos | Viajando com a Babi",
        "description": "Promoções de passagens aéreas com saída do Rio de Janeiro e São Paulo. Consulte datas, taxas e disponibilidade com a Babi.",
        "canonical": "https://viajandocomababi.com.br/promo-voos.html",
        "h1": "Promoções de voos",
        "sub": "Passagens promocionais com saída do Rio de Janeiro e São Paulo. Valores e datas conforme operadora, sujeitos a alteração e disponibilidade.",
        "breadcrumb": "Promoções de voos",
        "cta_text": "saber mais sobre promoções de voo",
        "schema_name": "Promoções de voos",
        "section_class": "ofertas-page ofertas-page--voos",
        "list_class": "oferta-list",
    },
    "campanhas.html": {
        "fragment": "campanhas-cards.html",
        "kind": "campanhas",
        "page_size": 30,
        "title": "Campanhas e ofertas de viagem | Viajando com a Babi",
        "description": "Campanhas de hotéis, resorts e condições especiais de viagem. Descontos sazonais e promoções com a Babi.",
        "canonical": "https://viajandocomababi.com.br/campanhas.html",
        "h1": "Campanhas e ofertas",
        "sub": "Descontos em hospedagem, resorts e condições especiais. Consulte prazos de venda e hospedagem antes de reservar.",
        "breadcrumb": "Campanhas",
        "cta_text": "saber mais sobre campanhas",
        "schema_name": "Campanhas e ofertas de viagem",
        "section_class": "ofertas-page ofertas-page--campanhas",
        "list_class": "oferta-list",
    },
}


def build_page(filename: str, cfg: dict) -> None:
    cards = (GENERATED / cfg["fragment"]).read_text(encoding="utf-8")
    head_assets = (ROOT / "_partials/head-assets.html").read_text(encoding="utf-8")
    ga4 = (ROOT / "_partials/ga4.html").read_text(encoding="utf-8")
    hub_header = (ROOT / "_partials/hub-header.html").read_text(encoding="utf-8")
    hub_footer = (ROOT / "_partials/hub-footer.html").read_text(encoding="utf-8")
    wa_cta = (
        "https://wa.me/5521920064617?text="
        + urllib.parse.quote(f"Olá Babi! Vim pelo site e quero {cfg['cta_text']}.")
    )

    head = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{cfg['title']}</title>
  <meta name="description" content="{cfg['description']}" />
  <link rel="canonical" href="{cfg['canonical']}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{cfg['canonical']}" />
  <meta property="og:title" content="{cfg['title']}" />
  <meta property="og:description" content="{cfg['description']}" />
  <meta property="og:image" content="https://viajandocomababi.com.br/assets/og-share.jpeg" />
  <meta property="og:locale" content="pt_BR" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="icon" type="image/png" href="assets/logo-vcb.png" />
{head_assets}  <link rel="stylesheet" href="style.css?v={ui.CSS_VERSION}" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{ "@type": "WebPage", "@id": "{cfg['canonical']}#webpage", "url": "{cfg['canonical']}", "name": "{cfg['schema_name']} | Viajando com a Babi", "isPartOf": {{ "@id": "https://viajandocomababi.com.br/#website" }} }},
      {{ "@type": "BreadcrumbList", "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Início", "item": "https://viajandocomababi.com.br/" }},
        {{ "@type": "ListItem", "position": 2, "name": "{cfg['breadcrumb']}", "item": "{cfg['canonical']}" }}
      ]}}
    ]
  }}
  </script>
{ga4}</head>
<body>
"""

    main = f"""<main id="conteudo-principal">
  <section id="ofertas" class="pacotes {cfg['section_class']}">
    <div class="container pacotes-page__header">
      <nav class="breadcrumb breadcrumb--light" aria-label="Navegação"><a href="/">Início</a> / {cfg['breadcrumb']}</nav>
      <span class="label label--center">Ofertas atualizadas</span>
      <h1 class="section-title">{cfg['h1']}</h1>
      <p class="section-sub">{cfg['sub']}</p>
    </div>
    <div class="container" data-catalog-root="{cfg['kind']}">
{ui.toolbar(cfg['kind'], cfg['page_size'])}
      <div class="{cfg['list_class']}" data-catalog-list>
{cards}
      </div>
{ui.empty_state(cfg['kind'])}
      <div class="pacotes__cta-extra">
        <p>Não encontrou o que procura?</p>
        <a href="{wa_cta}"
           target="_blank" rel="noopener noreferrer"
           class="btn btn--outline btn--md">
          <i class="fab fa-whatsapp"></i> Falar com a Babi
        </a>
      </div>
    </div>
  </section>
</main>
"""

    cookie_idx = hub_footer.find('<div id="cookieBanner"')
    tail = hub_footer[:cookie_idx] + hub_footer[cookie_idx:]
    (ROOT / filename).write_text(head + hub_header + main + tail, encoding="utf-8")
    print(f"{filename} atualizado")


if __name__ == "__main__":
    if not GENERATED.exists():
        raise SystemExit("Execute python _sync_operator.py antes.")
    for fname, cfg in PAGES.items():
        build_page(fname, cfg)
