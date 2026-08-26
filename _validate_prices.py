"""Validação pós-build do catálogo de pacotes (plano4)."""
from __future__ import annotations

import re
import json
from pathlib import Path

from _money import parse_brl

ROOT = Path(__file__).parent
ARTICLE_RE = re.compile(r"<article\b[^>]*class=\"[^\"]*card[\s\S]*?</article>", re.I)


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("\xa0", " ").strip()


def main() -> None:
    data = json.loads((ROOT / "data/operator-sync.json").read_text(encoding="utf-8"))
    pkgs = data["offers"]["pacotes"]
    print("REGRESSAO SYNC")
    for o in pkgs:
        t = o.get("title") or ""
        if "GP F" in t or "Heineken" in t or "Sheeran" in t or "rmula" in t:
            print(t)
            print(
                "  total",
                o.get("package_total_price"),
                "inst",
                o.get("installment_count"),
                o.get("installment_value"),
                "air",
                o.get("airfare_sale_price"),
                "src",
                o.get("price_source"),
            )

    html = (ROOT / "pacotes.html").read_text(encoding="utf-8")
    arts = ARTICLE_RE.findall(html)
    print("cards in pacotes.html", len(arts))

    targets = [
        "GP Fórmula 1 2026",
        "GP Fórmula 1 2026 -  Setor Heineken Village Estrela",
        "GP Fórmula 1 2026 (Pacote completo)",
        "Show Ed Sheeran - Loop Tour",
    ]
    for dest in targets:
        block = next((a for a in arts if f'data-destino="{dest}"' in a), None)
        if not block:
            print("MISSING", dest)
            continue
        sp = re.search(r'data-sort-price="([^"]*)"', block)
        tot = re.search(r'class="card__total">(.*?)</span>', block, re.S)
        par = re.search(r'class="card__parcela">(.*?)</span>', block, re.S)
        print("HTML", dest[:50], "sort", sp.group(1) if sp else None)
        print("  total", strip_tags(tot.group(1)) if tot else None)
        print("  parc", strip_tags(par.group(1)) if par else None)

    # Home agora vem do sync (data-source=operator); checa presença e preço nos destaques
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    home_arts = ARTICLE_RE.findall(index_html)
    home_ops = [a for a in home_arts if 'data-source="operator"' in a]
    print("HOME", "cards", len(home_arts), "operator", len(home_ops))
    if len(home_ops) == 0:
        print("HOME FAIL: nenhum card data-source=operator")
    elif len(home_ops) > 30:
        print("HOME WARN: mais de 30 cards operator na home", len(home_ops))
    else:
        print("HOME OK: até 30 destaques do sync")
    missing_price = 0
    for a in home_ops:
        sp = re.search(r'data-sort-price="([^"]*)"', a)
        if not sp or not sp.group(1):
            missing_price += 1
    print("HOME sem data-sort-price", missing_price)

    # Ordenação programática sobre data-sort-price
    priced = []
    unpriced = []
    for a in arts:
        raw = re.search(r'data-sort-price="([^"]*)"', a)
        dest = re.search(r'data-destino="([^"]+)"', a)
        title = dest.group(1) if dest else "?"
        if not raw or raw.group(1) == "":
            unpriced.append(title)
            continue
        priced.append(float(raw.group(1)))
    asc = sorted(priced)
    desc = sorted(priced, reverse=True)
    print("priced", len(priced), "unpriced", len(unpriced), unpriced)
    print("menor primeiros 10", asc[:10])
    print("maior primeiros 10", desc[:10])
    print("asc self-check", "OK" if asc == sorted(asc) else "FAIL")
    print("desc self-check", "OK" if desc == sorted(desc, reverse=True) else "FAIL")

    # Inconsistências HTML: total vs parcela
    bad = 0
    for a in arts:
        title_m = re.search(r'data-destino="([^"]+)"', a)
        title = title_m.group(1) if title_m else "?"
        sp_m = re.search(r'data-sort-price="([^"]*)"', a)
        if not sp_m or not sp_m.group(1):
            continue
        total = float(sp_m.group(1))
        par = re.search(r'class="card__parcela">(.*?)</span>', a, re.S)
        if not par:
            continue
        text = strip_tags(par.group(1))
        m = re.search(r"(\d+)x\s*de\s*R\$\s*([\d.]+)", text, re.I)
        if not m:
            m = re.search(r"(\d+)x.*?R\$\s*([\d.]+)", text, re.I)
        if not m:
            continue
        calc = int(m.group(1)) * parse_brl(m.group(2))
        if calc and abs(total - calc) > max(5, 0.01 * calc):
            bad += 1
            if bad <= 8:
                print("HTML inconsistent", title, "total", total, "calc", calc)
    print("html inconsistencies", bad)


if __name__ == "__main__":
    main()
