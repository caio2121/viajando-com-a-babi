#!/usr/bin/env python3
"""5 variações POST inspiradas no estilo comercial (cards flutuantes + tarjas)."""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SOCIAL = ROOT / "marketing" / "social"
BRAND = SOCIAL / "brand"
CAMPAIGN = SOCIAL / "campaigns" / "2027" / "jericoacoara"
OUT = CAMPAIGN / "export" / "modelos"
W, H = 1080, 1350

PLANE = (
    '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true">'
    '<path fill="currentColor" d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>'
    "</svg>"
)
CAL = (
    '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">'
    '<path fill="currentColor" d="M19 4h-1V2h-2v2H8V2H6v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z"/>'
    "</svg>"
)


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def load_offer() -> dict:
    with (CAMPAIGN / "offer.json").open(encoding="utf-8") as f:
        return json.load(f)


def fonts() -> str:
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com" />'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
        '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet" />'
    )


def shell(title: str, css: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<title>{escape(title)}</title>
{fonts()}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000;font-family:Nunito,sans-serif;-webkit-font-smoothing:antialiased}}
.canvas{{position:relative;width:{W}px;height:{H}px;overflow:hidden}}
.photo{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 45%}}
{css}
</style>
</head>
<body>
{body}
</body>
</html>"""


def build(offer: dict, photo: str, logo: str) -> list[tuple[str, str, str]]:
    dest = escape(offer["destination"].upper())
    unit = escape(offer["price"]["unit"])
    # Quebra preço estilo referência: valor grande
    raw_price = offer["price"]["value"]  # R$ 2.790
    price_main = escape(raw_price)
    date_footer = "08/05/27  ·  RETORNO: 13/05/27"
    disc = escape(offer.get("disclaimer") or "")
    items = [escape(i) for i in offer["includes"][:4]]

    models: list[tuple[str, str, str]] = []

    # 11 — Clone estrutural com accent teal da marca
    models.append((
        "11-inspire-teal",
        "Inspiração | clone comercial (accent teal)",
        shell(
            "11",
            """
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.08) 0%,rgba(0,0,0,.05) 45%,rgba(0,0,0,.28) 100%)}
.logo-tab{position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border-radius:0 0 22px 22px;padding:18px 28px 16px;box-shadow:0 10px 28px rgba(0,0,0,.28);z-index:5}
.logo-tab img{display:block;height:92px;width:auto}
.stack{position:absolute;left:48px;right:48px;bottom:118px;display:flex;flex-direction:column;align-items:center;gap:0;z-index:4}
.row-badges{align-self:flex-start;display:flex;flex-direction:column;align-items:flex-start;gap:14px;margin:0 0 18px 8px}
.badge-air{width:118px;height:118px;border-radius:50%;background:#3AAFA9;color:#17252A;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:15px;font-weight:900;line-height:1.05;text-align:center;box-shadow:0 10px 24px rgba(0,0,0,.3)}
.badge-air svg{color:#17252A}
.badge-pay{background:#fff;border-radius:14px;padding:12px 16px;box-shadow:0 8px 20px rgba(0,0,0,.25);color:#17252A;font-weight:900;font-size:18px;line-height:1.15;text-align:center}
.badge-pay .hi{color:#2B7A78;font-size:22px}
.badge-pay small{display:block;font-size:13px;font-weight:800;opacity:.75;margin-top:2px}
.dest{width:100%;background:#fff;border-radius:14px;padding:22px 28px;text-align:center;box-shadow:0 12px 30px rgba(0,0,0,.32);position:relative;z-index:2}
.dest h1{font-size:42px;font-weight:900;color:#111;letter-spacing:.02em;line-height:1.05}
.super{position:relative;z-index:3;margin-top:-16px;background:#3AAFA9;color:#17252A;font-size:22px;font-weight:900;letter-spacing:.04em;padding:12px 28px;border-radius:10px;box-shadow:0 8px 18px rgba(0,0,0,.25)}
.price-card{margin-top:18px;width:92%;background:#fff;clip-path:polygon(0 0,100% 0,94% 100%,0 100%);border-radius:18px 28px 18px 18px;padding:26px 36px 22px;box-shadow:0 14px 34px rgba(0,0,0,.35);text-align:left}
.price-card .from{font-size:24px;font-weight:800;color:#222}
.price-card .from .hi{color:#2B7A78;font-size:30px;font-weight:900}
.price-card .avista{margin-top:6px;font-size:34px;font-weight:900;color:#111}
.price-card .avista .big{font-size:64px;letter-spacing:-.02em}
.price-card .unit{margin-top:4px;font-size:20px;font-weight:800;color:#555}
.footer{position:absolute;left:0;right:0;bottom:0;height:86px;background:#111;display:flex;align-items:center;justify-content:center;gap:14px;color:#fff;font-size:26px;font-weight:800;letter-spacing:.02em;z-index:6}
.footer svg{opacity:.95}
.disc{position:absolute;bottom:92px;left:48px;right:48px;text-align:center;font-size:14px;color:rgba(255,255,255,.88);text-shadow:0 1px 4px rgba(0,0,0,.5);z-index:5}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="logo-tab"><img src="{logo}" alt="Viajando com a Babi" /></div>
  <div class="stack">
    <div class="row-badges">
      <div class="badge-air">{PLANE}Pacote<br/>Aéreo</div>
      <div class="badge-pay">COM TRANSFER<br/><span class="hi">+ PASSEIOS</span><small>Leste e Oeste</small></div>
    </div>
    <div class="dest"><h1>{dest}</h1></div>
    <div class="super">SUPER OPORTUNIDADE</div>
    <div class="price-card">
      <div class="from">Pacote completo com <span class="hi">aéreo</span></div>
      <div class="avista">À vista <span class="big">{price_main}</span></div>
      <div class="unit">{unit.lower()} em apto duplo</div>
    </div>
  </div>
  <p class="disc">{disc}</p>
  <div class="footer">{CAL}{escape(date_footer)}</div>
</article>
""",
        ),
    ))

    # 12 — Accent ouro (mais perto da referência visual)
    models.append((
        "12-inspire-ouro",
        "Inspiração | accent ouro (mais perto da referência)",
        shell(
            "12",
            """
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.06) 0%,rgba(0,0,0,.04) 40%,rgba(0,0,0,.3) 100%)}
.logo-tab{position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border-radius:0 0 22px 22px;padding:16px 26px 14px;box-shadow:0 10px 28px rgba(0,0,0,.28);z-index:5}
.logo-tab img{display:block;height:88px;width:auto}
.stack{position:absolute;left:42px;right:42px;bottom:112px;z-index:4}
.side{position:absolute;left:42px;bottom:520px;display:flex;flex-direction:column;gap:14px;z-index:5}
.badge-air{width:124px;height:124px;border-radius:50%;background:#F5C518;color:#111;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:16px;font-weight:900;line-height:1.05;text-align:center;box-shadow:0 10px 24px rgba(0,0,0,.32)}
.badge-pay{background:#fff;border-radius:12px;padding:10px 14px;box-shadow:0 8px 20px rgba(0,0,0,.28);color:#111;font-weight:900;font-size:17px;line-height:1.15;text-align:center;max-width:150px}
.badge-pay .hi{color:#E6A800;font-size:22px}
.badge-pay small{display:block;font-size:12px;font-weight:800;opacity:.7;margin-top:2px}
.dest{background:#fff;border-radius:8px;padding:20px 24px;text-align:center;box-shadow:0 12px 28px rgba(0,0,0,.34);transform:perspective(800px) rotateX(2deg);position:relative;z-index:2}
.dest h1{font-size:40px;font-weight:900;color:#111;letter-spacing:.03em}
.super{width:max-content;margin:-14px auto 0;position:relative;z-index:3;background:#F5C518;color:#111;font-size:20px;font-weight:900;letter-spacing:.05em;padding:11px 26px;border-radius:8px;box-shadow:0 8px 18px rgba(0,0,0,.28)}
.price-card{margin:20px auto 0;width:90%;background:#fff;transform:skewX(-4deg);border-radius:16px;padding:24px 40px 20px;box-shadow:0 14px 34px rgba(0,0,0,.36)}
.price-card .inner{transform:skewX(4deg)}
.price-card .from{font-size:23px;font-weight:800;color:#222}
.price-card .from .hi{color:#E6A800;font-weight:900;font-size:28px}
.price-card .avista{margin-top:4px;font-size:32px;font-weight:900;color:#111}
.price-card .avista .big{font-size:62px}
.price-card .unit{margin-top:2px;font-size:18px;font-weight:800;color:#666}
.footer{position:absolute;left:0;right:0;bottom:0;height:84px;background:#000;display:flex;align-items:center;justify-content:center;gap:12px;color:#fff;font-size:25px;font-weight:800;z-index:6}
.disc{position:absolute;bottom:90px;left:40px;right:40px;text-align:center;font-size:13px;color:rgba(255,255,255,.9);text-shadow:0 1px 4px rgba(0,0,0,.55);z-index:5}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="logo-tab"><img src="{logo}" alt="Viajando com a Babi" /></div>
  <div class="side">
    <div class="badge-air">{PLANE}Pacote<br/>Aéreo</div>
    <div class="badge-pay">INCLUI<br/><span class="hi">4 ITENS</span><small>aéreo · transfer · hotel · passeios</small></div>
  </div>
  <div class="stack">
    <div class="dest"><h1>{dest}</h1></div>
    <div class="super">SUPER OPORTUNIDADE</div>
    <div class="price-card"><div class="inner">
      <div class="from">Valor promocional <span class="hi">único</span></div>
      <div class="avista">À vista <span class="big">{price_main}</span></div>
      <div class="unit">{unit.lower()} em apto duplo</div>
    </div></div>
  </div>
  <p class="disc">{disc}</p>
  <div class="footer">{CAL}{escape(date_footer)}</div>
</article>
""",
        ),
    ))

    # 13 — Stack centrado limpo (sem badges laterais)
    models.append((
        "13-inspire-centrado",
        "Inspiração | stack centrado limpo",
        shell(
            "13",
            """
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.1) 0%,transparent 35%,rgba(0,0,0,.35) 100%)}
.logo-tab{position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border-radius:0 0 24px 24px;padding:18px 30px 16px;box-shadow:0 10px 28px rgba(0,0,0,.28);z-index:5}
.logo-tab img{display:block;height:96px;width:auto}
.stack{position:absolute;left:56px;right:56px;bottom:120px;display:flex;flex-direction:column;align-items:center;z-index:4}
.pill{background:#3AAFA9;color:#17252A;font-size:18px;font-weight:900;letter-spacing:.08em;padding:10px 22px;border-radius:999px;margin-bottom:16px;box-shadow:0 8px 18px rgba(0,0,0,.25)}
.dest{width:100%;background:#fff;border-radius:16px;padding:26px 24px 22px;text-align:center;box-shadow:0 12px 30px rgba(0,0,0,.32)}
.dest h1{font-size:48px;font-weight:900;color:#111}
.dest .tag{margin-top:6px;font-size:20px;font-weight:800;color:#2B7A78}
.super{margin-top:-14px;background:#17252A;color:#fff;font-size:20px;font-weight:900;letter-spacing:.06em;padding:12px 26px;border-radius:10px;box-shadow:0 8px 18px rgba(0,0,0,.3)}
.price-card{margin-top:18px;width:100%;background:#fff;border-radius:20px;padding:28px 32px 24px;text-align:center;box-shadow:0 14px 34px rgba(0,0,0,.34)}
.price-card .avista{font-size:30px;font-weight:900;color:#111}
.price-card .avista .big{display:block;font-size:72px;line-height:1;margin-top:4px;color:#111}
.price-card .unit{margin-top:8px;font-size:22px;font-weight:800;color:#2B7A78;letter-spacing:.06em}
.incs{margin-top:14px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px}
.incs span{background:#DEF2F1;color:#17252A;font-size:15px;font-weight:800;padding:8px 12px;border-radius:999px}
.footer{position:absolute;left:0;right:0;bottom:0;height:86px;background:#111;display:flex;align-items:center;justify-content:center;gap:14px;color:#fff;font-size:26px;font-weight:800;z-index:6}
.disc{position:absolute;bottom:92px;left:48px;right:48px;text-align:center;font-size:14px;color:rgba(255,255,255,.9);text-shadow:0 1px 4px rgba(0,0,0,.5);z-index:5}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="logo-tab"><img src="{logo}" alt="Viajando com a Babi" /></div>
  <div class="stack">
    <div class="pill">PACOTE AÉREO</div>
    <div class="dest">
      <h1>{dest}</h1>
      <div class="tag">Nordeste · Mai 2027</div>
    </div>
    <div class="super">SUPER OPORTUNIDADE</div>
    <div class="price-card">
      <div class="avista">À vista<span class="big">{price_main}</span></div>
      <div class="unit">{unit}</div>
      <div class="incs">{"".join(f"<span>{i}</span>" for i in items)}</div>
    </div>
  </div>
  <p class="disc">{disc}</p>
  <div class="footer">{CAL}{escape(date_footer)}</div>
</article>
""",
        ),
    ))

    # 14 — Destino em faixa larga + preço trapezoidal + chips de inclusão
    models.append((
        "14-inspire-faixas",
        "Inspiração | faixas + preço trapezoidal + chips",
        shell(
            "14",
            """
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.12) 0%,transparent 30%,rgba(0,0,0,.25) 100%)}
.logo-tab{position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border-radius:0 0 20px 20px;padding:14px 24px 12px;box-shadow:0 10px 26px rgba(0,0,0,.28);z-index:5}
.logo-tab img{display:block;height:84px;width:auto}
.air-float{position:absolute;left:48px;top:210px;width:110px;height:110px;border-radius:50%;background:#3AAFA9;color:#17252A;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:14px;font-weight:900;text-align:center;line-height:1.05;box-shadow:0 10px 24px rgba(0,0,0,.3);z-index:5}
.stack{position:absolute;left:40px;right:40px;bottom:110px;z-index:4}
.dest{background:#fff;border-radius:6px;padding:18px 20px;text-align:center;box-shadow:0 12px 28px rgba(0,0,0,.34)}
.dest h1{font-size:38px;font-weight:900;color:#111;letter-spacing:.04em}
.super{width:max-content;margin:-12px auto 0;background:#F5C518;color:#111;font-size:18px;font-weight:900;letter-spacing:.05em;padding:10px 22px;border-radius:6px;box-shadow:0 8px 16px rgba(0,0,0,.28);position:relative;z-index:3}
.chips{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin:16px 0 4px}
.chips span{background:rgba(255,255,255,.95);color:#17252A;font-size:15px;font-weight:800;padding:9px 12px;border-radius:10px;box-shadow:0 6px 14px rgba(0,0,0,.22)}
.price-card{margin:14px auto 0;width:88%;background:#fff;clip-path:polygon(0 0,100% 0,90% 100%,0 100%);border-radius:14px;padding:22px 34px 18px;box-shadow:0 14px 32px rgba(0,0,0,.36)}
.price-card .from{font-size:22px;font-weight:800;color:#333}
.price-card .from .hi{color:#2B7A78;font-size:26px}
.price-card .avista{margin-top:2px;font-size:30px;font-weight:900;color:#111}
.price-card .avista .big{font-size:58px}
.price-card .unit{font-size:18px;font-weight:800;color:#666;margin-top:2px}
.footer{position:absolute;left:0;right:0;bottom:0;height:82px;background:#000;display:flex;align-items:center;justify-content:center;gap:12px;color:#fff;font-size:24px;font-weight:800;z-index:6}
.disc{position:absolute;bottom:88px;left:40px;right:40px;text-align:center;font-size:13px;color:rgba(255,255,255,.9);text-shadow:0 1px 4px rgba(0,0,0,.55);z-index:5}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="logo-tab"><img src="{logo}" alt="Viajando com a Babi" /></div>
  <div class="air-float">{PLANE}Pacote<br/>Aéreo</div>
  <div class="stack">
    <div class="dest"><h1>{dest}</h1></div>
    <div class="super">SUPER OPORTUNIDADE</div>
    <div class="chips">{"".join(f"<span>✓ {i}</span>" for i in items)}</div>
    <div class="price-card">
      <div class="from">Pacote com <span class="hi">aéreo incluso</span></div>
      <div class="avista">À vista <span class="big">{price_main}</span></div>
      <div class="unit">{unit.lower()} em apto duplo</div>
    </div>
  </div>
  <p class="disc">{disc}</p>
  <div class="footer">{CAL}{escape(date_footer)}</div>
</article>
""",
        ),
    ))

    # 15 — Compacto inferior: mais foto, bloco comercial baixo
    models.append((
        "15-inspire-compacto",
        "Inspiração | bloco compacto (mais foto)",
        shell(
            "15",
            """
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05) 0%,transparent 40%,rgba(0,0,0,.45) 100%)}
.logo-tab{position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border-radius:0 0 22px 22px;padding:16px 28px 14px;box-shadow:0 10px 28px rgba(0,0,0,.28);z-index:5}
.logo-tab img{display:block;height:90px;width:auto}
.float-l{position:absolute;left:40px;top:48%;transform:translateY(-50%);z-index:5;display:flex;flex-direction:column;gap:12px}
.badge-air{width:112px;height:112px;border-radius:50%;background:#3AAFA9;color:#17252A;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:14px;font-weight:900;text-align:center;line-height:1.05;box-shadow:0 10px 24px rgba(0,0,0,.3)}
.badge-pay{background:#fff;border-radius:12px;padding:10px 12px;box-shadow:0 8px 18px rgba(0,0,0,.28);color:#111;font-weight:900;font-size:15px;text-align:center;line-height:1.15;max-width:140px}
.badge-pay .hi{color:#2B7A78;font-size:18px}
.stack{position:absolute;left:36px;right:36px;bottom:96px;z-index:4}
.dest{background:#fff;border-radius:10px;padding:16px 18px;text-align:center;box-shadow:0 10px 24px rgba(0,0,0,.32)}
.dest h1{font-size:36px;font-weight:900;color:#111;letter-spacing:.03em}
.row{display:flex;align-items:stretch;gap:12px;margin-top:12px}
.super{flex:0 0 auto;align-self:center;background:#F5C518;color:#111;font-size:16px;font-weight:900;letter-spacing:.04em;padding:14px 16px;border-radius:10px;writing-mode:vertical-rl;transform:rotate(180deg);box-shadow:0 8px 16px rgba(0,0,0,.25);text-align:center}
.price-card{flex:1;background:#fff;border-radius:14px;padding:16px 20px 14px;box-shadow:0 12px 28px rgba(0,0,0,.34)}
.price-card .avista{font-size:24px;font-weight:900;color:#111}
.price-card .avista .big{font-size:48px}
.price-card .unit{font-size:16px;font-weight:800;color:#555;margin-top:2px}
.price-card .mini{margin-top:8px;font-size:14px;font-weight:800;color:#2B7A78}
.footer{position:absolute;left:0;right:0;bottom:0;height:78px;background:#000;display:flex;align-items:center;justify-content:center;gap:12px;color:#fff;font-size:23px;font-weight:800;z-index:6}
.disc{position:absolute;bottom:82px;left:36px;right:36px;text-align:center;font-size:12px;color:rgba(255,255,255,.88);text-shadow:0 1px 4px rgba(0,0,0,.55);z-index:5}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="logo-tab"><img src="{logo}" alt="Viajando com a Babi" /></div>
  <div class="float-l">
    <div class="badge-air">{PLANE}Pacote<br/>Aéreo</div>
    <div class="badge-pay">COM<br/><span class="hi">TRANSFER</span><br/>+ hotel + passeios</div>
  </div>
  <div class="stack">
    <div class="dest"><h1>{dest}</h1></div>
    <div class="row">
      <div class="super">SUPER OPORTUNIDADE</div>
      <div class="price-card">
        <div class="avista">À vista <span class="big">{price_main}</span></div>
        <div class="unit">{unit.lower()} em apto duplo</div>
        <div class="mini">Aéreo · Transfer · Hotel · Passeios</div>
      </div>
    </div>
  </div>
  <p class="disc">{disc}</p>
  <div class="footer">{CAL}{escape(date_footer)}</div>
</article>
""",
        ),
    ))

    return models


def main() -> int:
    offer = load_offer()
    photo = file_url(CAMPAIGN / "assets" / offer["photo"]["file"])
    logo = file_url(BRAND / "logo-vcb.png")
    models = build(offer, photo, logo)
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for mid, label, html in models:
            src = OUT / f"{mid}.html"
            png = OUT / f"{mid}.png"
            src.write_text(html, encoding="utf-8")
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto(src.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_timeout(450)
            page.locator(".canvas").screenshot(path=str(png), type="png")
            page.close()
            print(f"OK {png.relative_to(ROOT)}")
            rows.append((mid, label, png.name))
        browser.close()

    readme = OUT / "README.md"
    extra = [
        "",
        "## Inspiração comercial (estilo referência)",
        "",
        "Mesma oferta Jericoacoara. Linguagem: logo no topo, badges flutuantes, tarja de destino, selo SUPER OPORTUNIDADE, card de preço, barra preta de datas.",
        "",
        "| # | Modelo | Arquivo |",
        "|---|--------|---------|",
    ]
    for i, (mid, label, name) in enumerate(rows, 11):
        extra.append(f"| {i} | {label} | `{name}` |")
    extra.append("")
    if readme.exists():
        text = readme.read_text(encoding="utf-8").rstrip()
        # remove previous inspire section if re-run
        marker = "## Inspiração comercial"
        if marker in text:
            text = text.split(marker)[0].rstrip()
        readme.write_text(text + "\n" + "\n".join(extra) + "\n", encoding="utf-8")
    else:
        readme.write_text("\n".join(extra) + "\n", encoding="utf-8")
    print(f"Index updated: {readme}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
