"""Destino canônico e chave de agrupamento visual do catálogo.

Agrupa a apresentação, não os dados: cada oferta permanece individual.
"""
from __future__ import annotations

import re
import unicodedata

AIRPORT_SUFFIX = re.compile(r"\s*\(([A-Za-z]{3})\)\s*$")
PLACE_CONJ = re.compile(r"\s+(?:e|&|\+)\s+", re.I)
HOTELISH = (
    "hotel",
    "convention",
    "resort",
    "taua",
    "transfer",
    "show de",
    "ingresso",
)

JUNK_KEYS = {
    "",
    "excursao",
    "cidade-de-origem",
    "recepcao",
}

# Grafia canônica. Não é uma lista fechada de destinos.
ALIASES = {
    "cancun": "Cancún",
    "foz-do-iguacu": "Foz do Iguaçu",
    "foz-iguacu": "Foz do Iguaçu",
    "ilheus": "Ilhéus",
    "maceio": "Maceió",
    "joao-pessoa": "João Pessoa",
    "sao-paulo": "São Paulo",
    "rio-de-janeiro": "Rio de Janeiro",
    "curacao": "Curaçao",
    "montevideu": "Montevidéu",
    "montevideo": "Montevidéu",
    "cidade-do-mexico": "Cidade do México",
    "caldas-novas": "Caldas Novas",
    "porto-seguro": "Porto Seguro",
    "fernando-de-noronha": "Fernando de Noronha",
    "florianopolis": "Florianópolis",
    "belem": "Belém",
    "brasilia": "Brasília",
    "sao-luis": "São Luís",
}

SMALL_WORDS = {"de", "do", "da", "dos", "das", "e", "del", "la", "los", "las", "el"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower().strip()


def slugify(text: str) -> str:
    base = normalize(text)
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def strip_airport_code(text: str | None) -> str:
    return AIRPORT_SUFFIX.sub("", text or "").strip()


def is_junk_destination(text: str | None) -> bool:
    key = slugify(strip_airport_code(text or ""))
    return key in JUNK_KEYS


def title_dest(text: str | None) -> str:
    raw = strip_airport_code((text or "").strip())
    if not raw:
        return ""
    key = slugify(raw)
    if key in ALIASES:
        return ALIASES[key]
    letters = [c for c in raw if c.isalpha()]
    if letters and all(c.upper() == c for c in letters):
        words = raw.lower().split()
        out = []
        for i, w in enumerate(words):
            if i > 0 and w in SMALL_WORDS:
                out.append(w)
            else:
                out.append(w[:1].upper() + w[1:])
        return " ".join(out)
    return raw


def looks_multidest(text: str | None) -> bool:
    raw = (text or "").strip()
    if not PLACE_CONJ.search(raw):
        return False
    blob = normalize(raw)
    if any(marker in blob for marker in HOTELISH):
        return False
    parts = PLACE_CONJ.split(raw)
    if len(parts) != 2:
        return False
    return all(3 <= len(p.strip()) <= 40 for p in parts)


def fallback_from_title(title: str | None) -> str:
    t = (title or "").strip()
    if not t:
        return ""
    if ":" in t:
        head = t.split(":", 1)[0].strip()
        if 3 <= len(head) <= 48:
            return head
    return t[:80]


def canonical_destination(destination: str | None, title: str | None = "") -> tuple[str, str]:
    """Retorna (rótulo, chave) do destino turístico."""
    raw = strip_airport_code((destination or "").strip())
    if is_junk_destination(raw):
        raw = ""
    if not raw:
        raw = fallback_from_title(title or "")
    label = title_dest(raw) or (title or "Destino").strip()[:80]
    if not label:
        label = "Destino"
    return label, slugify(label)


def match_known_destination(text: str, known_labels: list[str]) -> str | None:
    blob = normalize(text)
    best = None
    best_len = 0
    for label in known_labels:
        n = normalize(label)
        if n and n in blob and len(n) > best_len:
            best = label
            best_len = len(n)
    return best


def event_group(title: str, destination: str = "") -> tuple[str, str] | None:
    blob = normalize(f"{title} {destination}")
    if "formula 1" in blob or "f1" in blob or "heineken village" in blob:
        return "evento:gp-formula-1", "GP Fórmula 1"
    if "sheeran" in blob:
        return "evento:ed-sheeran", "Show Ed Sheeran"
    return None


def park_group(title: str, dest_key: str) -> tuple[str, str] | None:
    blob = normalize(title)
    if "disney" not in blob and "disneyland" not in blob:
        return None
    if dest_key == "paris":
        return "parque:disneyland-paris", "Disneyland Paris"
    if dest_key in ("los-angeles", "california"):
        return "parque:disneyland-california", "Disneyland Califórnia"
    return None


def group_identity(
    *,
    destination: str = "",
    title: str = "",
    tipo: str = "",
    evento: bool = False,
    categoria: str = "",
    known_labels: list[str] | None = None,
    is_manual: bool = False,
) -> tuple[str, str]:
    """Retorna (group_key, group_label)."""
    if evento or (categoria or "").lower() == "evento":
        ev = event_group(title, destination)
        if ev:
            return ev
    ev = event_group(title, destination)
    if ev:
        return ev

    dest_for_canon = destination
    if is_manual:
        text = destination or title
        if looks_multidest(text):
            label = title_dest(text) or text
            return f"circuito:{slugify(label)}", label
        if known_labels:
            matched = match_known_destination(text, known_labels)
            if matched:
                dest_for_canon = matched

    label, dest_key = canonical_destination(dest_for_canon, title)

    if tipo == "cruzeiro":
        return f"cruzeiro:{dest_key}", f"Cruzeiro · {label}"

    park = park_group(title, dest_key)
    if park:
        return park

    return dest_key, label


def offer_name(title: str, destination: str = "", group_label: str = "") -> str:
    """Título da opção sem repetir o destino no começo."""
    t = (title or "").strip()
    if not t:
        return ""
    for prefix in (destination, group_label):
        prefix = (prefix or "").strip()
        if prefix and t.lower().startswith(prefix.lower()):
            rest = t[len(prefix):].strip(" ·:-")
            rest = re.sub(r"^(em|de|do|da|com)\s+", "", rest, flags=re.I).strip(" ·:-")
            if rest and len(rest) >= 8:
                return rest[:80]
            return t[:80]
    return t[:80]


def known_labels_from_offers(offers: list[dict] | None) -> list[str]:
    labels = list(ALIASES.values())
    for offer in offers or []:
        label, _key = canonical_destination(offer.get("destination") or "", offer.get("title") or "")
        if label:
            labels.append(label)
    uniq: list[str] = []
    seen: set[str] = set()
    for lab in sorted(set(labels), key=lambda s: (-len(s), s.lower())):
        key = slugify(lab)
        if key and key not in seen:
            seen.add(key)
            uniq.append(lab)
    return uniq
