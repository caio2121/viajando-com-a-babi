"""Aplica head-assets, GA4+consent e footer scripts nas páginas HTML estáticas.

Fora do pipeline de sync a cada 3 dias (_sync_operator → _build_ofertas → _build_pacotes).
Usa as versões canônicas de `_catalog_ui` para não regredir cache-bust de CSS/JS/analytics.
"""
import re
from pathlib import Path

from _catalog_ui import ANALYTICS_VERSION, CSS_VERSION, JS_VERSION
from _site_config import PUBLIC_CONFIG_PATH, load_public_config, public_replacements, render_public_template

root = Path(__file__).parent
public_config = load_public_config()
baseline_config = load_public_config(PUBLIC_CONFIG_PATH)
head_assets = render_public_template((root / "_partials/head-assets.html").read_text(encoding="utf-8"), public_config)
ga4 = render_public_template((root / "_partials/ga4.html").read_text(encoding="utf-8"), public_config)
hub_footer = render_public_template((root / "_partials/hub-footer.html").read_text(encoding="utf-8"), public_config)

FONT_BLOCK = re.compile(
    r'  <link rel="preconnect" href="https://fonts\.googleapis\.com" />.*?'
    r'(?:<!-- Font Awesome.*?-->\s*)?'
    r'  <link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/6\.5\.2/css/all\.min\.css"[^>]*/>\s*',
    re.DOTALL,
)
FONT_BLOCK_ALT = re.compile(
    r'  <link href="https://fonts\.googleapis\.com/css2[^"]+" rel="stylesheet" />\s*'
    r'  <link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/6\.5\.2/css/all\.min\.css"[^>]*/>\s*',
)
GA4_BLOCK = re.compile(
    r'  <!-- Google Analytics 4.*?</script>\s*',
    re.DOTALL,
)
FOOTER_BLOCK_OLD = re.compile(
    r'  <footer id="contato"[\s\S]*?</html>\s*$',
    re.DOTALL,
)
SKIP_FOOTER_TAIL = {"index.html", "404.html", "privacidade.html"}
SKIP_GA4 = {
    "cookies.html", "termos-de-uso.html", "condicoes-comerciais.html",
    "cancelamento-reembolso.html", "contato-lgpd.html", "google194769ee1567755b.html",
}

# Bumps legados → versões atuais em _catalog_ui (não hardcodar versões antigas).
_LEGACY_CSS = tuple(str(n) for n in range(15, int(CSS_VERSION)))
_LEGACY_ANALYTICS = tuple(str(n) for n in range(6, int(ANALYTICS_VERSION)))
_LEGACY_JS = tuple(str(n) for n in range(20, int(JS_VERSION)))

pages = list(root.glob("*.html"))

for path in pages:
    text = path.read_text(encoding="utf-8")
    orig = text

    if 'media="print" onload="this.media=\'all\'"' not in text:
        if FONT_BLOCK.search(text):
            text = FONT_BLOCK.sub(head_assets, text, count=1)
        elif FONT_BLOCK_ALT.search(text):
            text = FONT_BLOCK_ALT.sub(head_assets, text, count=1)

    config_tag = '  <script src="site-config.js?v=1"></script>\n'
    text = re.sub(r'\s*<script src="site-config\.js\?v=1"></script>\s*', '\n', text)
    text = text.replace("<head>", "<head>\n" + config_tag, 1)
    if path.name not in SKIP_GA4:
        text = GA4_BLOCK.sub(ga4, text, count=1)
        if "VCB_CONSENT_KEY" not in text:
            text = text.replace("</head>", ga4 + "</head>")
    for old, new in public_replacements(baseline_config, public_config).items():
        text = text.replace(old, new)

    for old_css in _LEGACY_CSS:
        text = text.replace(f"style.css?v={old_css}", f"style.css?v={CSS_VERSION}")
    for old_a in _LEGACY_ANALYTICS:
        text = text.replace(f"analytics.js?v={old_a}", f"analytics.js?v={ANALYTICS_VERSION}")
    for old_js in _LEGACY_JS:
        text = text.replace(f"script.js?v={old_js}", f"script.js?v={JS_VERSION}")

    if path.name not in SKIP_FOOTER_TAIL and '<footer id="contato"' in text:
        text = FOOTER_BLOCK_OLD.sub(hub_footer, text, count=1)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        print(f"Atualizado: {path.name}")
