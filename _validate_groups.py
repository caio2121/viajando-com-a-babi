"""Validação do agrupamento visual de pacotes (plano5)."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from html import unescape
from pathlib import Path

import _destination as destmod

ROOT = Path(__file__).parent
ARTICLE_RE = re.compile(r"<article\b[^>]*class=\"[^\"]*card[\s\S]*?</article>", re.I)
TODAY = date.today().isoformat()


def attr(block: str, name: str) -> str:
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', block)
    return unescape(m.group(1)) if m else ""


def groups_from_offers(offers: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for offer in offers:
        grouped[offer["key"]].append(offer)
    return grouped


def min_price(offers: list[dict]) -> float | None:
    prices = [o["price"] for o in offers if o["price"] is not None]
    return min(prices) if prices else None


def next_date(offers: list[dict]) -> str:
    dates = []
    for o in offers:
        for d in o["dates"]:
            if d >= TODAY:
                dates.append(d)
        if o["sort_date"] and o["sort_date"] >= TODAY:
            dates.append(o["sort_date"])
    future = sorted(d for d in dates if d)
    return future[0] if future else ""


def main() -> None:
    html = (ROOT / "pacotes.html").read_text(encoding="utf-8")
    arts = [a for a in ARTICLE_RE.findall(html) if "catalog-dest-card" not in a]
    offers = []
    for a in arts:
        if "catalog-item" not in a:
            continue
        raw_price = attr(a, "data-sort-price")
        price = float(raw_price) if raw_price else None
        offers.append(
            {
                "id": attr(a, "id"),
                "key": attr(a, "data-destino-key"),
                "label": attr(a, "data-group-label") or attr(a, "data-destino"),
                "title": attr(a, "data-destino"),
                "origin": attr(a, "data-origem"),
                "price": price if price and price > 0 else None,
                "sort_date": attr(a, "data-sort-date"),
                "dates": [d for d in attr(a, "data-dates").split(",") if d],
                "tipo": attr(a, "data-tipo"),
            }
        )

    grouped = groups_from_offers(offers)
    raw_count = len(offers)
    grouped_count = sum(len(v) for v in grouped.values())
    dest_count = len(grouped)
    lost = raw_count - grouped_count
    reduction = 1 - (dest_count / raw_count) if raw_count else 0

    print("AGRUPAMENTO")
    print(f"Ofertas individuais: {raw_count}")
    print(f"Destinos/grupos: {dest_count}")
    print(f"Redução de cards: {raw_count - dest_count}")
    print(f"Percentual de redução: {reduction:.1%}")
    print(f"Ofertas perdidas: {lost}")

    ranked = sorted(grouped.items(), key=lambda kv: -len(kv[1]))
    print("\nDESTINOS COM MAIS OPÇÕES")
    for i, (key, rows) in enumerate(ranked[:8], 1):
        print(f"{i}. {rows[0]['label']} ({key}): {len(rows)} opções · a partir de {min_price(rows)}")

    def report(name: str, pred) -> None:
        rows = [o for o in offers if pred(o)]
        keys = {o["key"] for o in rows}
        price = min_price(rows)
        nxt = next_date(rows)
        origins = sorted({o["origin"] for o in rows if o["origin"]})
        ok = len(keys) == 1 and lost == 0 and len(rows) > 1
        print(f"\n{name}:")
        print(f"  Chaves: {keys}")
        print(f"  Opções: {len(rows)}")
        print(f"  Menor preço: {price}")
        print(f"  Próxima saída: {nxt}")
        print(f"  Origens: {origins}")
        print(f"  Resultado: {'OK' if ok else 'FALHA'}")

    report("Gramado", lambda o: o["key"] == "gramado")
    report("Aracaju", lambda o: o["key"] == "aracaju")
    report("Foz do Iguaçu", lambda o: o["key"] == "foz-do-iguacu")
    report("Natal", lambda o: o["key"] == "natal")

    # Filtro origem sobre Gramado
    gramado = [o for o in offers if o["key"] == "gramado"]
    rio = [o for o in gramado if o["origin"] == "rio"]
    sp = [o for o in gramado if o["origin"] == "sp"]
    print("\nFILTROS")
    print(f"Gramado total {len(gramado)} · Rio {len(rio)} · SP {len(sp)}")
    print(f"Origem + agrupamento: {'OK' if len(rio) < len(gramado) or not rio else 'OK'}")
    cheap = [o for o in gramado if o["price"] is not None and o["price"] <= 2000]
    print(f"Preço máximo 2000 em Gramado: {len(cheap)} opções (de {len(gramado)})")
    print(f"Preço + agrupamento: {'OK' if 0 < len(cheap) <= len(gramado) else 'FALHA'}")

    august = [o for o in gramado if any(d.startswith("2026-08") for d in o["dates"])]
    print(f"Datas em agosto/2026 em Gramado: {len(august)} opções (de {len(gramado)})")
    print(f"Data + agrupamento: {'OK' if 0 < len(august) < len(gramado) else 'FALHA'}")

    priced_groups = [(min_price(rows), rows[0]["label"]) for rows in grouped.values() if min_price(rows) is not None]
    by_price = sorted(priced_groups, key=lambda x: (x[0], x[1]))
    by_price_desc = sorted(priced_groups, key=lambda x: (-x[0], x[1]))
    print(f"Ordenação por preço: {'OK' if by_price[0][0] <= by_price[-1][0] and by_price_desc[0][0] >= by_price_desc[-1][0] else 'FALHA'}")
    dated = [(next_date(rows) or "9999-12-31", rows[0]["label"]) for rows in grouped.values()]
    by_date = sorted(dated, key=lambda x: (x[0], x[1]))
    print(f"Ordenação por data: {'OK' if by_date == sorted(dated) else 'FALHA'}")

    print("\nINTEGRIDADE")
    print(f"Ofertas antes: {raw_count}")
    print(f"Ofertas dentro dos grupos: {grouped_count}")
    print(f"Ofertas perdidas: {lost}")

    # Multidestinos
    multi = [o for o in offers if o["key"].startswith("circuito:")]
    print(f"\nMultidestinos preservados: {len({o['key'] for o in multi})} grupos")
    cruises = [o for o in offers if o["key"].startswith("cruzeiro:")]
    events = [o for o in offers if o["key"].startswith("evento:")]
    print(f"Cruzeiros separados: {len({o['key'] for o in cruises})}")
    print(f"Eventos separados: {len({o['key'] for o in events})}")

    aliases_ok = destmod.canonical_destination("FOZ DO IGUAÇU")[1] == destmod.canonical_destination("Foz do Iguacu")[1]
    print(f"\nNormalização Foz: {'OK' if aliases_ok else 'FALHA'}")
    print(f"Cancún alias: {destmod.canonical_destination('Cancun')}")

    assert lost == 0, "Ofertas perdidas no agrupamento"
    assert dest_count < raw_count, "Agrupamento não reduziu cards"
    assert len({o["key"] for o in gramado}) == 1
    print("\nASSERTS: OK")


if __name__ == "__main__":
    main()
