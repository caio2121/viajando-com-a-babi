"""Aplica head-assets e GA4 deferido nas páginas HTML estáticas."""
import re
from pathlib import Path

root = Path(__file__).parent
head_assets = (root / "_partials/head-assets.html").read_text(encoding="utf-8")
ga4 = (root / "_partials/ga4.html").read_text(encoding="utf-8")

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
    r'  <!-- Google Analytics 4.*?<!-- Google Analytics 4 \(carregamento adiado\) -->.*?</script>\s*|'
    r'  <!-- Google Analytics 4 -->.*?</script>\s*|'
    r'<script async src="https://www\.googletagmanager\.com/gtag/js[^"]*"></script>\s*'
    r'<script>\s*window\.dataLayer.*?gtag\(\'config\'.*?</script>\s*',
    re.DOTALL,
)

pages = [p for p in root.glob("*.html") if p.name not in ("404.html", "pacotes.html", "index.html")]

for path in pages:
    text = path.read_text(encoding="utf-8")
    orig = text

    if 'media="print" onload="this.media=\'all\'"' not in text:
        if FONT_BLOCK.search(text):
            text = FONT_BLOCK.sub(head_assets, text, count=1)
        elif FONT_BLOCK_ALT.search(text):
            text = FONT_BLOCK_ALT.sub(head_assets, text, count=1)

    text = GA4_BLOCK.sub("", text)
    if "loadGA4" not in text:
        text = text.replace("</head>", ga4 + "</head>")

    for old in ("15", "16", "17", "18", "19"):
        text = text.replace(f"style.css?v={old}", "style.css?v=20")
        text = text.replace(f"script.js?v={old}", "script.js?v=20")
        text = text.replace(f"analytics.js?v={old}", "analytics.js?v=6")

    if text != orig:
        path.write_text(text, encoding="utf-8")
        print(f"Atualizado: {path.name}")
