#!/usr/bin/env python3
"""Gera 10 modelos visuais distintos para uma oferta (POST 1080x1350)."""

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

WA_ICON = (
    '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">'
    '<path fill="currentColor" d="M20.5 3.5A11 11 0 0 0 3.1 17.3L2 22l4.8-1.1A11 11 0 1 0 20.5 3.5zm-8.5 17a9.1 9.1 0 0 1-4.6-1.3l-.3-.2-2.9.7.7-2.8-.2-.3a9.1 9.1 0 1 1 7.3 3.9zm5-6.8c-.3-.1-1.6-.8-1.9-.9s-.4-.1-.6.1-.7.9-.8 1-.3.2-.6.1a7.4 7.4 0 0 1-2.2-1.4 8.2 8.2 0 0 1-1.5-1.9c-.2-.3 0-.4.1-.6l.4-.5.3-.4a.5.5 0 0 0 0-.5c0-.1-.6-1.4-.8-1.9s-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 2.9 2.9 0 0 0-.9 2.2 5 5 0 0 0 1.1 2.7 11.5 11.5 0 0 0 4.4 3.9 15 15 0 0 0 1.5.5 3.6 3.6 0 0 0 1.6.1 2.7 2.7 0 0 0 1.8-1.2 2.2 2.2 0 0 0 .2-1.2c-.1-.1-.3-.2-.6-.3z"/>'
    "</svg>"
)


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def load_offer() -> dict:
    with (CAMPAIGN / "offer.json").open(encoding="utf-8") as f:
        return json.load(f)


def base_fonts() -> str:
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com" />'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
        '<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Nunito:wght@600;700;800&display=swap" rel="stylesheet" />'
    )


def shell(title: str, css: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<title>{escape(title)}</title>
{base_fonts()}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000;font-family:Nunito,sans-serif;color:#fff;-webkit-font-smoothing:antialiased}}
.canvas{{position:relative;width:{W}px;height:{H}px;overflow:hidden}}
.photo{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 55%}}
{css}
</style>
</head>
<body>
{body}
</body>
</html>"""


def includes_list(items: list[str], cls: str = "inc") -> str:
    lis = "".join(
        f'<li><span class="ck">✓</span><span>{escape(i)}</span></li>' for i in items[:4]
    )
    return f'<ul class="{cls}">{lis}</ul>'


def build_models(offer: dict, photo: str, logo: str) -> list[tuple[str, str, str]]:
    """Returns list of (id, label, html)."""
    dest = escape(offer["destination"])
    tag = escape(offer["tagline"])
    date = escape(offer["date_display"])
    price = escape(offer["price"]["value"])
    unit = escape(offer["price"]["unit"])
    cta = escape(offer["cta"])
    disc = escape(offer.get("disclaimer") or "")
    eyebrow = escape(offer.get("eyebrow") or "")
    items = offer["includes"]
    inc = includes_list(items)

    models: list[tuple[str, str, str]] = []

    # 01 Editorial leve (referência V2)
    models.append((
        "01-editorial-leve",
        "Editorial leve (foto + tipografia)",
        shell(
            "01",
            f"""
.veil{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,37,42,.25) 0%,rgba(23,37,42,.05) 30%,rgba(23,37,42,.75) 68%,rgba(23,37,42,.94) 100%)}}
.frame{{position:absolute;inset:0;padding:48px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:flex-start}}
.eyebrow{{font-size:20px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;opacity:.92}}
.logo{{width:118px;height:118px;object-fit:contain;filter:drop-shadow(0 6px 16px rgba(0,0,0,.35))}}
.spacer{{flex:1}}
.h1{{font-size:78px;font-weight:800;line-height:.98;text-shadow:0 4px 24px rgba(0,0,0,.35)}}
.tag{{font-family:'Dancing Script',cursive;font-size:36px;color:#DEF2F1;margin:10px 0 8px}}
.line{{width:72px;height:3px;background:linear-gradient(90deg,#3AAFA9,transparent);margin-bottom:18px}}
.price{{font-size:96px;font-weight:800;line-height:.95}}
.unit{{font-size:28px;font-weight:800;letter-spacing:.14em;color:#3AAFA9;margin-top:4px}}
.block{{margin-top:18px}}
.title{{font-size:18px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#3AAFA9;margin-bottom:12px}}
.inc{{display:grid;grid-template-columns:1fr 1fr;gap:12px 28px;list-style:none}}
.inc li{{display:flex;gap:10px;font-size:22px;font-weight:700;align-items:baseline}}
.ck{{color:#3AAFA9}}
.date{{margin-top:18px;font-size:26px;font-weight:800;letter-spacing:.12em;border-bottom:2px solid rgba(58,175,169,.65);padding-bottom:8px;width:fit-content}}
.cta{{margin-top:18px;display:inline-flex;align-items:center;gap:10px;border:1.5px solid rgba(255,255,255,.55);border-radius:999px;padding:14px 22px;font-size:20px;font-weight:800;max-width:920px;line-height:1.25}}
.cta svg{{color:#25D366;flex-shrink:0}}
.disc{{margin-top:12px;font-size:16px;opacity:.65;font-weight:600}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="frame">
    <div class="top"><span class="eyebrow">{eyebrow}</span><img class="logo" src="{logo}" alt="" /></div>
    <div class="spacer"></div>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <div class="line"></div>
    <p class="price">{price}</p>
    <p class="unit">{unit}</p>
    <div class="block"><p class="title">O pacote inclui</p>{inc}</div>
    <p class="date">{date}</p>
    <div class="cta">{WA_ICON}{cta}</div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    # 02 Tarja + cards
    models.append((
        "02-tarja-cards",
        "Tarja branca + cards (mais comercial)",
        shell(
            "02",
            f"""
.veil{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,37,42,.35) 0%,rgba(23,37,42,.1) 35%,rgba(23,37,42,.88) 72%,rgba(23,37,42,.96) 100%)}}
.wm{{position:absolute;top:110px;right:40px;width:260px;opacity:.18}}
.frame{{position:absolute;inset:0;padding:48px;display:flex;flex-direction:column}}
.eyebrow{{display:inline-flex;background:#DEF2F1;color:#17252A;font-weight:800;letter-spacing:.14em;text-transform:uppercase;padding:10px 16px;border-radius:999px;font-size:20px;width:fit-content}}
.spacer{{flex:1}}
.h1{{font-size:72px;font-weight:800}}
.tag{{font-family:'Dancing Script',cursive;font-size:34px;color:#DEF2F1;margin:8px 0 12px}}
.date{{display:inline-flex;background:rgba(58,175,169,.22);border:1px solid rgba(58,175,169,.55);padding:12px 18px;border-radius:14px;font-weight:800;letter-spacing:.08em;font-size:24px;width:fit-content}}
.box{{margin-top:14px;background:linear-gradient(145deg,rgba(43,122,120,.95),rgba(23,37,42,.96));border:2px solid rgba(158,227,223,.45);border-radius:24px;padding:18px}}
.title{{font-size:18px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#9fe3df;margin-bottom:12px}}
.inc{{display:grid;grid-template-columns:1fr 1fr;gap:10px;list-style:none}}
.inc li{{display:flex;gap:10px;align-items:center;min-height:62px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);border-radius:14px;padding:12px;font-size:19px;font-weight:800}}
.ck{{width:28px;height:28px;border-radius:50%;background:#fff;color:#2B7A78;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:16px}}
.price{{font-size:84px;font-weight:800;margin-top:12px}}
.unit{{font-size:26px;font-weight:800;color:#3AAFA9;letter-spacing:.12em}}
.foot{{margin-top:12px;display:flex;align-items:center;justify-content:space-between;gap:14px;background:rgba(255,255,255,.96);border-radius:24px;padding:12px 14px}}
.cta{{display:inline-flex;align-items:center;gap:10px;background:#157347;color:#fff;border-radius:999px;padding:14px 18px;font-size:17px;font-weight:800;line-height:1.25;max-width:700px}}
.logo{{width:130px;height:130px;object-fit:contain}}
.disc{{margin-top:10px;font-size:15px;opacity:.7}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <img class="wm" src="{logo}" alt="" />
  <div class="frame">
    <span class="eyebrow">{eyebrow}</span>
    <div class="spacer"></div>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <p class="date">{date}</p>
    <div class="box"><p class="title">O pacote inclui</p>{inc}</div>
    <p class="price">{price}</p>
    <p class="unit">{unit}</p>
    <div class="foot">
      <div class="cta">{WA_ICON}{cta}</div>
      <img class="logo" src="{logo}" alt="" />
    </div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    # 03 Poster central
    models.append((
        "03-poster-central",
        "Poster central (impacto no feed)",
        shell(
            "03",
            f"""
.veil{{position:absolute;inset:0;background:radial-gradient(ellipse at center, rgba(23,37,42,.15) 0%, rgba(23,37,42,.55) 55%, rgba(23,37,42,.92) 100%)}}
.frame{{position:absolute;inset:0;padding:56px 64px;display:flex;flex-direction:column;align-items:center;text-align:center}}
.logo{{width:110px;height:110px;object-fit:contain;margin-top:8px;filter:drop-shadow(0 8px 18px rgba(0,0,0,.4))}}
.spacer{{flex:1}}
.eyebrow{{font-size:18px;font-weight:800;letter-spacing:.28em;text-transform:uppercase;opacity:.85}}
.h1{{font-size:92px;font-weight:800;margin-top:18px;text-shadow:0 8px 40px rgba(0,0,0,.45)}}
.tag{{font-family:'Dancing Script',cursive;font-size:40px;color:#DEF2F1;margin:14px 0 22px;max-width:820px}}
.price{{font-size:88px;font-weight:800}}
.unit{{font-size:26px;font-weight:800;letter-spacing:.16em;color:#3AAFA9;margin-top:6px}}
.date{{margin-top:22px;font-size:24px;font-weight:800;letter-spacing:.14em}}
.inc{{margin-top:28px;list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:10px 18px;max-width:900px}}
.inc li{{font-size:20px;font-weight:700;opacity:.95;display:flex;gap:8px;align-items:center}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:28px;display:inline-flex;gap:10px;align-items:center;font-size:20px;font-weight:800;border-bottom:2px solid #25D366;padding-bottom:8px;max-width:860px;line-height:1.3}}
.cta svg{{color:#25D366}}
.disc{{margin-top:16px;font-size:15px;opacity:.6}}
.bottom{{margin-top:auto;padding-bottom:8px}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="frame">
    <img class="logo" src="{logo}" alt="" />
    <div class="spacer"></div>
    <p class="eyebrow">{eyebrow}</p>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <p class="price">{price}</p>
    <p class="unit">{unit}</p>
    <p class="date">{date}</p>
    {inc}
    <div class="bottom">
      <div class="cta">{WA_ICON}{cta}</div>
      <p class="disc">{disc}</p>
    </div>
  </div>
</article>
""",
        ),
    ))

    # 04 Faixa inferior sólida
    models.append((
        "04-faixa-solida",
        "Faixa sólida inferior (foto limpa em cima)",
        shell(
            "04",
            f"""
.photo{{height:58%;bottom:auto}}
.band{{position:absolute;left:0;right:0;bottom:0;height:46%;background:#17252A;padding:42px 48px 40px;display:flex;flex-direction:column}}
.fade{{position:absolute;left:0;right:0;top:48%;height:14%;background:linear-gradient(180deg,transparent,#17252A)}}
.topbar{{position:absolute;top:40px;left:48px;right:48px;display:flex;justify-content:space-between;align-items:flex-start}}
.eyebrow{{background:rgba(255,255,255,.92);color:#17252A;font-weight:800;letter-spacing:.14em;text-transform:uppercase;padding:10px 16px;border-radius:999px;font-size:18px}}
.logo{{width:108px;height:108px;object-fit:contain;filter:drop-shadow(0 6px 14px rgba(0,0,0,.35))}}
.row{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start}}
.left{{flex:1}}
.right{{text-align:right}}
.h1{{font-size:58px;font-weight:800;line-height:1}}
.tag{{font-family:'Dancing Script',cursive;font-size:30px;color:#9fe3df;margin-top:8px}}
.price{{font-size:72px;font-weight:800;line-height:1}}
.unit{{font-size:22px;font-weight:800;color:#3AAFA9;letter-spacing:.12em;margin-top:4px}}
.date{{margin-top:14px;font-size:22px;font-weight:800;letter-spacing:.1em;color:rgba(255,255,255,.9)}}
.title{{margin-top:18px;font-size:16px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#3AAFA9}}
.inc{{margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:8px 20px;list-style:none}}
.inc li{{display:flex;gap:8px;font-size:20px;font-weight:700;align-items:baseline}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:auto;display:inline-flex;align-items:center;gap:10px;background:#157347;border-radius:999px;padding:14px 20px;font-size:18px;font-weight:800;width:fit-content;max-width:980px;line-height:1.25}}
.disc{{margin-top:10px;font-size:14px;opacity:.55}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="fade"></div>
  <div class="topbar"><span class="eyebrow">{eyebrow}</span><img class="logo" src="{logo}" alt="" /></div>
  <div class="band">
    <div class="row">
      <div class="left">
        <h1 class="h1">{dest}</h1>
        <p class="tag">{tag}</p>
        <p class="date">{date}</p>
      </div>
      <div class="right">
        <p class="price">{price}</p>
        <p class="unit">{unit}</p>
      </div>
    </div>
    <p class="title">O pacote inclui</p>
    {inc}
    <div class="cta">{WA_ICON}{cta}</div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    # 05 Painel lateral
    models.append((
        "05-painel-lateral",
        "Painel lateral (composição assimétrica)",
        shell(
            "05",
            f"""
.photo{{left:38%;width:62%;object-position:center 45%}}
.panel{{position:absolute;left:0;top:0;bottom:0;width:42%;background:linear-gradient(165deg,#0f1a1d 0%,#17252A 55%,#1a3332 100%);padding:48px 36px;display:flex;flex-direction:column}}
.logo{{width:100px;height:100px;object-fit:contain}}
.eyebrow{{margin-top:28px;font-size:16px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:#9fe3df}}
.h1{{margin-top:18px;font-size:52px;font-weight:800;line-height:1.02}}
.tag{{margin-top:12px;font-family:'Dancing Script',cursive;font-size:28px;color:#DEF2F1;line-height:1.2}}
.price{{margin-top:28px;font-size:64px;font-weight:800;line-height:1}}
.unit{{font-size:20px;font-weight:800;color:#3AAFA9;letter-spacing:.12em;margin-top:6px}}
.date{{margin-top:18px;font-size:20px;font-weight:800;letter-spacing:.1em;opacity:.9}}
.title{{margin-top:24px;font-size:14px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#3AAFA9}}
.inc{{margin-top:12px;list-style:none;display:flex;flex-direction:column;gap:10px}}
.inc li{{display:flex;gap:10px;font-size:18px;font-weight:700;align-items:flex-start;line-height:1.3}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:auto;display:inline-flex;gap:10px;align-items:center;border:1.5px solid rgba(255,255,255,.4);border-radius:999px;padding:12px 16px;font-size:16px;font-weight:800;line-height:1.25}}
.cta svg{{color:#25D366;flex-shrink:0}}
.disc{{margin-top:12px;font-size:13px;opacity:.55;line-height:1.3}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="panel">
    <img class="logo" src="{logo}" alt="" />
    <p class="eyebrow">{eyebrow}</p>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <p class="price">{price}</p>
    <p class="unit">{unit}</p>
    <p class="date">{date}</p>
    <p class="title">O pacote inclui</p>
    {inc}
    <div class="cta">{WA_ICON}{cta}</div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    # 06 Preço herói
    models.append((
        "06-preco-heroi",
        "Preço herói (oferta em destaque)",
        shell(
            "06",
            f"""
.veil{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(23,37,42,.45) 0%,rgba(23,37,42,.2) 35%,rgba(23,37,42,.85) 70%,#0f1a1d 100%)}}
.frame{{position:absolute;inset:0;padding:48px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between}}
.logo{{width:112px;height:112px;object-fit:contain}}
.eyebrow{{font-size:18px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#9fe3df}}
.h1{{margin-top:24px;font-size:48px;font-weight:800;opacity:.95}}
.tag{{font-family:'Dancing Script',cursive;font-size:32px;color:#DEF2F1;margin-top:6px}}
.hero{{margin-top:auto;margin-bottom:8px}}
.price{{font-size:128px;font-weight:800;line-height:.9;letter-spacing:-.04em}}
.unit{{font-size:32px;font-weight:800;letter-spacing:.18em;color:#3AAFA9;margin-top:8px}}
.meta{{margin-top:22px;display:flex;justify-content:space-between;gap:24px;align-items:flex-end}}
.date{{font-size:24px;font-weight:800;letter-spacing:.12em}}
.inc{{list-style:none;display:flex;flex-direction:column;gap:8px;text-align:right}}
.inc li{{display:flex;gap:8px;justify-content:flex-end;font-size:18px;font-weight:700}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:22px;display:inline-flex;gap:10px;align-items:center;background:rgba(21,115,71,.35);border:1px solid rgba(37,211,102,.5);border-radius:999px;padding:14px 20px;font-size:18px;font-weight:800;max-width:980px;line-height:1.25}}
.cta svg{{color:#25D366}}
.disc{{margin-top:12px;font-size:15px;opacity:.6}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="frame">
    <div class="top"><span class="eyebrow">{eyebrow}</span><img class="logo" src="{logo}" alt="" /></div>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <div class="hero">
      <p class="price">{price}</p>
      <p class="unit">{unit}</p>
      <div class="meta">
        <p class="date">{date}</p>
        {inc}
      </div>
      <div class="cta">{WA_ICON}{cta}</div>
      <p class="disc">{disc}</p>
    </div>
  </div>
</article>
""",
        ),
    ))

    # 07 Postal / moldura
    models.append((
        "07-postal-moldura",
        "Postal com moldura (viagem / memória)",
        shell(
            "07",
            f"""
.canvas{{background:#DEF2F1}}
.mat{{position:absolute;inset:36px;background:#17252A;border-radius:8px;overflow:hidden}}
.photo{{inset:0;height:58%;border-radius:0}}
.body{{position:absolute;left:0;right:0;bottom:0;height:46%;padding:36px 40px 32px;display:flex;flex-direction:column;background:#F7FBFA;color:#17252A}}
.fade{{position:absolute;left:0;right:0;top:50%;height:10%;background:linear-gradient(180deg,transparent,#F7FBFA)}}
.logo{{position:absolute;top:28px;right:28px;width:96px;height:96px;object-fit:contain;z-index:2;filter:drop-shadow(0 4px 12px rgba(0,0,0,.35))}}
.eyebrow{{font-size:14px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:#2B7A78}}
.h1{{margin-top:8px;font-size:52px;font-weight:800;color:#17252A}}
.tag{{font-family:'Dancing Script',cursive;font-size:28px;color:#2B7A78;margin-top:4px}}
.row{{margin-top:16px;display:flex;justify-content:space-between;gap:20px}}
.price{{font-size:56px;font-weight:800;line-height:1;color:#17252A}}
.unit{{font-size:18px;font-weight:800;color:#3AAFA9;letter-spacing:.12em}}
.date{{font-size:20px;font-weight:800;letter-spacing:.1em;color:#2d4a52;align-self:flex-end}}
.title{{margin-top:14px;font-size:13px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#2B7A78}}
.inc{{margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;list-style:none}}
.inc li{{display:flex;gap:8px;font-size:17px;font-weight:700;color:#2d4a52;align-items:baseline}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:auto;display:inline-flex;gap:10px;align-items:center;background:#157347;color:#fff;border-radius:999px;padding:12px 18px;font-size:16px;font-weight:800;width:fit-content;max-width:900px;line-height:1.25}}
.disc{{margin-top:8px;font-size:13px;color:#3d5860}}
""",
            f"""
<article class="canvas">
  <div class="mat">
    <img class="photo" src="{photo}" alt="" />
    <div class="fade"></div>
    <img class="logo" src="{logo}" alt="" />
    <div class="body">
      <p class="eyebrow">{eyebrow}</p>
      <h1 class="h1">{dest}</h1>
      <p class="tag">{tag}</p>
      <div class="row">
        <div><p class="price">{price}</p><p class="unit">{unit}</p></div>
        <p class="date">{date}</p>
      </div>
      <p class="title">O pacote inclui</p>
      {inc}
      <div class="cta">{WA_ICON}{cta}</div>
      <p class="disc">{disc}</p>
    </div>
  </div>
</article>
""",
        ),
    ))

    # 08 Tipografia pura / cinema
    models.append((
        "08-cinema-tipografia",
        "Cinema tipográfico (muito foto)",
        shell(
            "08",
            f"""
.veil{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,.05) 40%,rgba(0,0,0,.75) 100%)}}
.frame{{position:absolute;inset:0;padding:52px;display:flex;flex-direction:column}}
.logo{{width:100px;height:100px;align-self:flex-end;object-fit:contain;opacity:.95}}
.spacer{{flex:1}}
.h1{{font-size:100px;font-weight:800;line-height:.92;text-shadow:0 10px 40px rgba(0,0,0,.5)}}
.tag{{margin-top:16px;font-size:28px;font-weight:700;max-width:860px;opacity:.95}}
.rule{{margin:22px 0;width:100%;height:1px;background:rgba(255,255,255,.35)}}
.row{{display:flex;justify-content:space-between;gap:24px;align-items:flex-end}}
.price{{font-size:64px;font-weight:800}}
.unit{{font-size:20px;font-weight:800;letter-spacing:.14em;color:#9fe3df}}
.date{{font-size:22px;font-weight:800;letter-spacing:.12em}}
.inc{{margin-top:18px;list-style:none;display:flex;flex-wrap:wrap;gap:8px 20px}}
.inc li{{font-size:18px;font-weight:700;opacity:.9;display:flex;gap:8px}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:22px;font-size:20px;font-weight:800;display:inline-flex;gap:10px;align-items:center}}
.cta svg{{color:#25D366}}
.disc{{margin-top:10px;font-size:14px;opacity:.55}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="frame">
    <img class="logo" src="{logo}" alt="" />
    <div class="spacer"></div>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <div class="rule"></div>
    <div class="row">
      <div><p class="price">{price}</p><p class="unit">{unit}</p></div>
      <p class="date">{date}</p>
    </div>
    {inc}
    <div class="cta">{WA_ICON}{cta}</div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    # 09 Lista vertical editorial
    models.append((
        "09-lista-vertical",
        "Lista vertical editorial",
        shell(
            "09",
            f"""
.veil{{position:absolute;inset:0;background:linear-gradient(105deg,rgba(15,26,29,.92) 0%,rgba(15,26,29,.78) 42%,rgba(15,26,29,.25) 70%,rgba(15,26,29,.4) 100%)}}
.frame{{position:absolute;inset:0;padding:52px 56px;display:flex;flex-direction:column;max-width:640px}}
.logo{{width:108px;height:108px;object-fit:contain}}
.eyebrow{{margin-top:28px;font-size:16px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:#9fe3df}}
.h1{{margin-top:14px;font-size:64px;font-weight:800;line-height:1}}
.tag{{margin-top:10px;font-family:'Dancing Script',cursive;font-size:30px;color:#DEF2F1}}
.price{{margin-top:28px;font-size:72px;font-weight:800}}
.unit{{font-size:22px;font-weight:800;color:#3AAFA9;letter-spacing:.14em}}
.date{{margin-top:14px;font-size:22px;font-weight:800;letter-spacing:.1em;opacity:.9}}
.title{{margin-top:28px;font-size:14px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#3AAFA9}}
.inc{{margin-top:12px;list-style:none}}
.inc li{{display:flex;gap:14px;align-items:center;padding:14px 0;border-bottom:1px solid rgba(255,255,255,.16);font-size:22px;font-weight:700}}
.inc li:last-child{{border-bottom:0}}
.ck{{color:#3AAFA9;font-size:20px}}
.cta{{margin-top:auto;display:inline-flex;gap:10px;align-items:center;background:#157347;border-radius:999px;padding:14px 20px;font-size:17px;font-weight:800;max-width:520px;line-height:1.25}}
.disc{{margin-top:12px;font-size:14px;opacity:.55}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="frame">
    <img class="logo" src="{logo}" alt="" />
    <p class="eyebrow">{eyebrow}</p>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <p class="price">{price}</p>
    <p class="unit">{unit}</p>
    <p class="date">{date}</p>
    <p class="title">O pacote inclui</p>
    {inc}
    <div class="cta">{WA_ICON}{cta}</div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    # 10 Night teal / premium soft
    models.append((
        "10-noite-teal",
        "Noite teal (tom mais sofisticado)",
        shell(
            "10",
            f"""
.photo{{filter:saturate(1.05) contrast(1.05)}}
.veil{{position:absolute;inset:0;background:
  linear-gradient(180deg,rgba(10,24,28,.55) 0%, rgba(10,24,28,.15) 28%, rgba(10,24,28,.35) 52%, rgba(8,18,22,.94) 78%, #071216 100%),
  radial-gradient(ellipse at 80% 20%, rgba(58,175,169,.18), transparent 45%)}}
.frame{{position:absolute;inset:0;padding:52px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.eyebrow{{font-size:15px;font-weight:800;letter-spacing:.28em;text-transform:uppercase;color:#9fe3df}}
.logo{{width:104px;height:104px;object-fit:contain}}
.spacer{{flex:1}}
.h1{{font-size:76px;font-weight:800;letter-spacing:-.02em}}
.tag{{margin-top:12px;font-family:'Dancing Script',cursive;font-size:36px;color:#b7ebe6}}
.card{{margin-top:28px;border-top:1px solid rgba(158,227,223,.35);border-bottom:1px solid rgba(158,227,223,.35);padding:22px 0}}
.price{{font-size:84px;font-weight:800;line-height:.95}}
.unit{{margin-top:6px;font-size:24px;font-weight:800;letter-spacing:.16em;color:#3AAFA9}}
.grid{{margin-top:18px;display:grid;grid-template-columns:1.1fr .9fr;gap:18px;align-items:start}}
.date{{font-size:22px;font-weight:800;letter-spacing:.12em}}
.inc{{list-style:none;display:flex;flex-direction:column;gap:8px}}
.inc li{{display:flex;gap:10px;font-size:18px;font-weight:700;align-items:baseline}}
.ck{{color:#3AAFA9}}
.cta{{margin-top:26px;display:inline-flex;gap:10px;align-items:center;padding:0;border:0;background:transparent;font-size:20px;font-weight:800;color:#fff;border-bottom:1px solid rgba(37,211,102,.8);padding-bottom:8px;max-width:920px;line-height:1.3}}
.cta svg{{color:#25D366}}
.disc{{margin-top:14px;font-size:14px;opacity:.5}}
""",
            f"""
<article class="canvas">
  <img class="photo" src="{photo}" alt="" />
  <div class="veil"></div>
  <div class="frame">
    <div class="top"><span class="eyebrow">{eyebrow}</span><img class="logo" src="{logo}" alt="" /></div>
    <div class="spacer"></div>
    <h1 class="h1">{dest}</h1>
    <p class="tag">{tag}</p>
    <div class="card">
      <p class="price">{price}</p>
      <p class="unit">{unit}</p>
      <div class="grid">
        <p class="date">{date}</p>
        {inc}
      </div>
    </div>
    <div class="cta">{WA_ICON}{cta}</div>
    <p class="disc">{disc}</p>
  </div>
</article>
""",
        ),
    ))

    return models


def main() -> int:
    offer = load_offer()
    photo = file_url(CAMPAIGN / "assets" / offer["photo"]["file"])
    logo = file_url(BRAND / "logo-vcb.png")
    models = build_models(offer, photo, logo)
    OUT.mkdir(parents=True, exist_ok=True)

    index_rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for mid, label, html in models:
            src = OUT / f"{mid}.html"
            png = OUT / f"{mid}.png"
            src.write_text(html, encoding="utf-8")
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto(src.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_timeout(400)
            page.locator(".canvas").screenshot(path=str(png), type="png")
            page.close()
            print(f"OK {png.relative_to(ROOT)}")
            index_rows.append((mid, label, png.name))
        browser.close()

    md = [
        "# 10 modelos | Jericoacoara (piloto)",
        "",
        "Oferta: **Jericoacoara** · 08 a 13 MAI 2027 · **R$ 2.790 POR PESSOA**",
        "",
        "Formato: POST 1080×1350. Mesmos dados comerciais; só muda a linguagem visual.",
        "",
        "| # | Modelo | Arquivo |",
        "|---|--------|---------|",
    ]
    for i, (mid, label, name) in enumerate(index_rows, 1):
        md.append(f"| {i} | {label} | `{name}` |")
    md.append("")
    md.append("Pasta: `marketing/social/campaigns/2027/jericoacoara/export/modelos/`")
    (OUT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Index: {OUT / 'README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
