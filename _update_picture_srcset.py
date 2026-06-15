"""Atualiza <picture> dos cards com srcset responsivo e dimensões."""
import re
from pathlib import Path

root = Path(__file__).parent
index_path = root / "index.html"
text = index_path.read_text(encoding="utf-8")

EAGER_IDS = ("pacote-aracaju", "pacote-fortaleza")

picture_re = re.compile(
    r'<picture><source srcset="pacotes/([^"]+\.webp)" type="image/webp" />'
    r'<img src="pacotes/([^"]+\.jpeg)"([^>]*)></picture>',
    re.DOTALL,
)

article_id_re = re.compile(r'id="(pacote-[^"]+)"')


def upgrade_picture(match: re.Match, article_id: str | None) -> str:
    webp = match.group(1)
    jpeg = match.group(2)
    attrs = match.group(3)

    stem = Path(webp).stem
    src400 = f"pacotes/{stem}-400.webp"
    src800 = f"pacotes/{stem}-800.webp"
    if not (root / src800).exists():
        src800 = f"pacotes/{webp}"

    srcset = f'{src400} 400w, {src800} 800w'
    source = (
        f'<picture><source srcset="{srcset}" '
        f'sizes="(max-width:640px) 100vw, 400px" type="image/webp" />'
    )

    attrs = re.sub(r'\s*loading="lazy"', "", attrs)
    if "width=" not in attrs:
        attrs += ' width="400" height="260"'
    if "decoding=" not in attrs:
        attrs += ' decoding="async"'

    if article_id not in EAGER_IDS and 'loading="lazy"' not in attrs:
        attrs += ' loading="lazy"'

    return f'{source}<img src="pacotes/{jpeg}"{attrs}></picture>'


def process_block(block: str) -> str:
    pos = 0
    out = []
    for m in picture_re.finditer(block):
        before = block[pos : m.start()]
        id_match = list(article_id_re.finditer(before))
        article_id = id_match[-1].group(1) if id_match else None
        out.append(before)
        out.append(upgrade_picture(m, article_id))
        pos = m.end()
    out.append(block[pos:])
    return "".join(out)


new_text = process_block(text)

# babi-sobre responsive
babi_old = (
    '<picture><source srcset="assets/babi-sobre.webp" type="image/webp" />'
    '<img src="assets/babi-sobre.jpeg?v=2"'
)
babi_new = (
    '<picture><source srcset="assets/babi-sobre.webp 480w, assets/babi-sobre.webp 960w" '
    'sizes="(max-width:640px) 100vw, 480px" type="image/webp" />'
    '<img src="assets/babi-sobre.jpeg?v=2"'
)
new_text = new_text.replace(babi_old, babi_new)

index_path.write_text(new_text, encoding="utf-8")
count = len(picture_re.findall(text))
print(f"Atualizados {count} pictures em index.html")
