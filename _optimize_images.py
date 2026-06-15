"""Gera variantes WebP responsivas (400w) e otimiza assets. Requer: pip install Pillow"""
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Instale Pillow: pip install Pillow")

root = Path(__file__).parent
pacotes_dir = root / "pacotes"
assets_dir = root / "assets"
QUALITY = 78

CARD_WIDTHS = (400, 800)


def save_webp(img: Image.Image, path: Path, width: int) -> None:
    if img.width > width:
        ratio = width / img.width
        height = max(1, round(img.height * ratio))
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save(path, "WEBP", quality=QUALITY, method=6)
    print(f"  {path.relative_to(root)} ({img.width}x{img.height})")


def process_pacote_webp(webp_path: Path) -> None:
    stem = webp_path.stem
    if stem.endswith("-400") or stem.endswith("-800"):
        return

    with Image.open(webp_path) as img:
        img = img.convert("RGB")
        w400 = pacotes_dir / f"{stem}-400.webp"
        if not w400.exists() or w400.stat().st_mtime < webp_path.stat().st_mtime:
            save_webp(img.copy(), w400, 400)

        w800 = pacotes_dir / f"{stem}-800.webp"
        if not w800.exists() or w800.stat().st_mtime < webp_path.stat().st_mtime:
            save_webp(img.copy(), w800, 800)


def process_asset(name: str, max_width: int) -> None:
    webp = assets_dir / f"{name}.webp"
    if not webp.exists():
        return
    with Image.open(webp) as img:
        img = img.convert("RGB")
        if img.width > max_width:
            save_webp(img, webp, max_width)


print("Pacotes:")
for webp in sorted(pacotes_dir.glob("*.webp")):
    if "-400" not in webp.stem and "-800" not in webp.stem:
        process_pacote_webp(webp)

print("Assets:")
process_asset("babi-sobre", 480)
process_asset("cadastur", 860)

print("Concluído.")
