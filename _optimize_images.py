"""Gera variantes WebP responsivas (400w/800w) e otimiza assets. Requer: pip install Pillow"""
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Instale Pillow: pip install Pillow")

root = Path(__file__).parent
pacotes_dir = root / "pacotes"
assets_dir = root / "assets"
QUALITY = 78


def save_webp(img: Image.Image, path: Path, width: int, quality: int = QUALITY) -> None:
    if img.width > width:
        ratio = width / img.width
        height = max(1, round(img.height * ratio))
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save(path, "WEBP", quality=quality, method=6)
    print(f"  {path.relative_to(root)} ({img.width}x{img.height}, q={quality})")


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


def process_asset(name: str, max_width: int, quality: int = 85) -> None:
    jpg = assets_dir / f"{name}.jpg"
    png = assets_dir / f"{name}.png"
    webp = assets_dir / f"{name}.webp"
    src = jpg if jpg.exists() else png if png.exists() else webp
    if not src.exists():
        return
    with Image.open(src) as img:
        img = img.convert("RGB")
        if img.width > max_width:
            save_webp(img, webp, max_width, quality)
        elif src != webp:
            save_webp(img, webp, img.width, quality)
        elif img.width < max_width and src == jpg:
            # WebP antigo menor que o JPG fonte: regenerar em alta resolução
            save_webp(img, webp, min(img.width, max_width), quality)


print("Pacotes:")
for webp in sorted(pacotes_dir.glob("*.webp")):
    if "-400" not in webp.stem and "-800" not in webp.stem:
        process_pacote_webp(webp)

print("Assets:")
process_asset("babi-sobre", 960)
process_asset("cadastur", 960, quality=88)

print("Concluído.")
