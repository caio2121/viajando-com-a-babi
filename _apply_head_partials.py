"""Aplica head-assets, GA4+consent e footer scripts nas páginas HTML estáticas."""
import re
from pathlib import Path

root = Path(__file__).parent
head_assets = (root / "_partials/head-assets.html").read_text(encoding="utf-8")
ga4 = (root / "_partials/ga4.html").read_text(encoding="utf-8")
hub_footer = (root / "_partials/hub-footer.html").read_text(encoding="utf-8")

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

pages = list(root.glob("*.html"))

for path in pages:
    text = path.read_text(encoding="utf-8")
    orig = text

    if 'media="print" onload="this.media=\'all\'"' not in text:
        if FONT_BLOCK.search(text):
            text = FONT_BLOCK.sub(head_assets, text, count=1)
        elif FONT_BLOCK_ALT.search(text):
            text = FONT_BLOCK_ALT.sub(head_assets, text, count=1)

    text = GA4_BLOCK.sub(ga4, text, count=1)
    if "VCB_CONSENT_KEY" not in text:
        text = text.replace("</head>", ga4 + "</head>")

    for old_css in ("15", "16", "17", "18", "19", "20", "21"):
        text = text.replace(f"style.css?v={old_css}", "style.css?v=22")
    for old_js in ("6", "7"):
        text = text.replace(f"analytics.js?v={old_js}", "analytics.js?v=8")

    if path.name not in SKIP_FOOTER_TAIL and '<footer id="contato"' in text:
        text = FOOTER_BLOCK_OLD.sub(hub_footer, text, count=1)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        print(f"Atualizado: {path.name}")
