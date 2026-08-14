"""Parser e helpers monetários BRL compartilhados pelo sync/build."""
from __future__ import annotations

import re
import unicodedata

_AMOUNT_RE = re.compile(r"([\d.]+,\d{2}|\d{1,3}(?:\.\d{3})+|\d+)")
_INSTALLMENT_RE = re.compile(
    r"(\d+)\s*x\s*(?:de\s*)?(?:R\$\s*)?([\d.]+,\d{2}|\d{1,3}(?:\.\d{3})+|\d+)",
    re.I,
)
_AMBIGUOUS_INSTALLMENT = re.compile(
    r"entrada|sinal|juros|financi|parcela\s*diferenc",
    re.I,
)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower().strip()


def parse_brl(text: str | None) -> float | None:
    """Interpreta valores no padrão brasileiro (milhar com ponto, decimal com vírgula)."""
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None
    cleaned = raw.replace("R$", "").replace("US$", "").strip()
    m = _AMOUNT_RE.search(cleaned)
    if not m:
        return None
    token = m.group(1)
    if "," in token:
        token = token.replace(".", "").replace(",", ".")
    else:
        token = token.replace(".", "")
    try:
        value = float(token)
    except ValueError:
        return None
    return value


def money_to_float(text: str | None) -> float:
    """Compatível com código antigo: None/inválido -> 0.0."""
    value = parse_brl(text)
    return value if value is not None else 0.0


def format_brl(value: float | None, *, html_nbsp: bool = False) -> str:
    if value is None:
        return ""
    rounded = int(round(value))
    formatted = f"{rounded:,}".replace(",", ".")
    sep = "&nbsp;" if html_nbsp else " "
    return f"R${sep}{formatted}"


def parse_installment(text: str | None) -> tuple[int | None, float | None]:
    if not text:
        return None, None
    m = _INSTALLMENT_RE.search(str(text))
    if not m:
        return None, None
    count = int(m.group(1))
    value = parse_brl(m.group(2))
    if count <= 0 or value is None or value <= 0:
        return None, None
    return count, value


def installment_is_ambiguous(text: str | None) -> bool:
    return bool(_AMBIGUOUS_INSTALLMENT.search(str(text or "")))


def price_tolerance(reference: float) -> float:
    """Tolerância: até R$ 5 ou 1% do valor de referência."""
    return max(5.0, abs(reference) * 0.01)


def prices_consistent(total: float, installment_count: int, installment_value: float) -> bool:
    calc = installment_count * installment_value
    return abs(total - calc) <= price_tolerance(calc)


def resolve_package_total(
    *,
    hotel_price_text: str | None,
    installment_text: str | None,
    airfare_sale: float | None,
    has_package_components: bool,
) -> tuple[float | None, str]:
    """
    Determina package_total_price e price_source.

    Nunca usa preço promocional de aéreo como total do pacote.
    """
    hotel_total = parse_brl(hotel_price_text)
    if hotel_total is not None and hotel_total > 0:
        source = "explicit_total"
        count, value = parse_installment(installment_text)
        if count and value and not prices_consistent(hotel_total, count, value):
            # Mantém total explícito do hotel; inconsistência é auditada depois.
            pass
        if airfare_sale is not None and abs(hotel_total - airfare_sale) < 0.01 and has_package_components:
            # Hotel espelhando aéreo: tenta parcela do pacote.
            if count and value and not installment_is_ambiguous(installment_text):
                return round(count * value, 2), "installment_calculated"
            return None, "unknown"
        return round(hotel_total, 2), source

    count, value = parse_installment(installment_text)
    if count and value and not installment_is_ambiguous(installment_text):
        calc = round(count * value, 2)
        if airfare_sale is not None and abs(calc - airfare_sale) < 0.01 and has_package_components:
            return None, "unknown"
        return calc, "installment_calculated"

    return None, "unknown"
