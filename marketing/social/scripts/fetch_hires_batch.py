#!/usr/bin/env python3
from pathlib import Path
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def cover_scale(w: int, h: int) -> float:
    return max(1080 / w, 1350 / h)


def fetch(url: str, dest: Path) -> None:
    ua = {"User-Agent": "ViajandoComABabiBot/1.0 (marketing creatives)"}
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=ua)
    data = urllib.request.urlopen(req, timeout=90).read()
    dest.write_bytes(data)
    im = Image.open(dest)
    w, h = im.size
    s = cover_scale(w, h)
    flag = "OK" if s <= 1.10 else "LOW"
    print(f"{flag} {w}x{h} scale={s:.2f} -> {dest.relative_to(ROOT)}")


def main() -> None:
    items = [
        (
            ROOT / "marketing/social/campaigns/2027/fortaleza-jericoacoara-fev/assets/hero-hires.jpg",
            "https://commons.wikimedia.org/wiki/Special:FilePath/Morro_Branco_CE_29.JPG",
        ),
        (
            ROOT / "marketing/social/campaigns/2027/foz-do-iguacu/assets/hero-hires.jpg",
            "https://commons.wikimedia.org/wiki/Special:FilePath/Iguaz%C3%BA_Falls_01.jpg",
        ),
        (
            ROOT / "marketing/social/campaigns/2027/jalapao/assets/hero-hires.jpg",
            "https://commons.wikimedia.org/wiki/Special:FilePath/Fervedouro.jpg",
        ),
        (
            ROOT / "marketing/social/campaigns/2027/porto-de-galinhas/assets/hero-hires.jpg",
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&w=2400&q=90",
        ),
        (
            ROOT / "marketing/social/campaigns/2026/natal-luz-gramado/assets/hero-hires.jpg",
            "https://images.unsplash.com/photo-1512389142860-9c449e58a543?ixlib=rb-4.0.3&w=2400&q=90",
        ),
    ]
    for dest, url in items:
        try:
            fetch(url, dest)
        except Exception as e:
            print(f"FAIL {dest}: {e}")

    # fallbacks
    fallbacks = [
        (
            ROOT / "marketing/social/campaigns/2027/jalapao/assets/hero-hires.jpg",
            [
                "https://commons.wikimedia.org/wiki/Special:FilePath/Fervedouro_do_Ceir%C3%A1.jpg",
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&w=2400&q=90",
            ],
        ),
        (
            ROOT / "marketing/social/campaigns/2027/porto-de-galinhas/assets/hero-hires.jpg",
            [
                "https://images.unsplash.com/photo-1559827260-dc66d52bef19?ixlib=rb-4.0.3&w=2400&q=90",
                str(ROOT / "materiais-evento/imagens/ofertas/porto-galinhas.jpeg"),
            ],
        ),
        (
            ROOT / "marketing/social/campaigns/2026/natal-luz-gramado/assets/hero-hires.jpg",
            [
                "https://images.unsplash.com/photo-1482517969863-f23c920ce9ff?ixlib=rb-4.0.3&w=2400&q=90",
                "https://images.unsplash.com/photo-1543584520-1a83a2d8c2e6?ixlib=rb-4.0.3&w=2400&q=90",
            ],
        ),
    ]
    for dest, urls in fallbacks:
        ok = False
        if dest.exists():
            im = Image.open(dest)
            if cover_scale(*im.size) <= 1.10:
                ok = True
        if ok:
            continue
        for url in urls:
            try:
                if url.startswith("http"):
                    fetch(url, dest)
                else:
                    src = Path(url)
                    if src.exists():
                        dest.write_bytes(src.read_bytes())
                        im = Image.open(dest)
                        print(f"COPY {im.size} -> {dest.relative_to(ROOT)}")
                im = Image.open(dest)
                if cover_scale(*im.size) <= 1.10:
                    break
            except Exception as e:
                print(f"FAIL fallback {url}: {e}")


if __name__ == "__main__":
    main()
