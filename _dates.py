"""Normalização canônica de datas para sync e catálogo."""
from __future__ import annotations

import re
from datetime import date, datetime, time

TODAY = date.today()
MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

_RANGE_FULL = re.compile(
    r"(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+a\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
    re.I,
)
_RANGE_COMPACT = re.compile(
    r"(\d{1,2})\s+a\s+(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?",
    re.I,
)
_DATE_TOKEN = re.compile(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?")
_JS_DATE_RE = re.compile(
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"(\d{1,2})\s+(\d{4})(?:\s+\d{2}:\d{2}:\d{2}\s+GMT[+-]\d{4}(?:\s*\([^)]*\))?)?",
    re.I,
)
_JS_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_js_date(text: str | None) -> date | None:
    if not text:
        return None
    m = _JS_DATE_RE.search(str(text))
    if not m:
        return None
    month = _JS_MONTHS.get(m.group(1).lower())
    if not month:
        return None
    return _safe_date(int(m.group(3)), month, int(m.group(2)))


def sanitize_date_text(text: str | None) -> str:
    """Remove vazamentos de Date.toString() e troca por dd/mm/aaaa."""
    if not text:
        return ""
    raw = str(text)

    def repl(match: re.Match) -> str:
        parsed = parse_js_date(match.group(0))
        return parsed.strftime("%d/%m/%Y") if parsed else ""

    cleaned = _JS_DATE_RE.sub(repl, raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ·,;")
    return cleaned


def parse_yymmdd(text: str | None) -> date | None:
    raw = (text or "").strip()
    if not re.fullmatch(r"\d{6}", raw):
        return None
    year = 2000 + int(raw[0:2])
    month = int(raw[2:4])
    day = int(raw[4:6])
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_hhmm(text: str | None) -> str | None:
    raw = (text or "").strip()
    if len(raw) != 4 or not raw.isdigit():
        return None
    hour, minute = int(raw[:2]), int(raw[2:])
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_br_date(text: str | None, min_date: date | None = None) -> date | None:
    """Interpreta dd/mm ou dd/mm/aaaa. Sem ano, avança o calendário a partir de min_date."""
    if not text:
        return None
    text = str(text).strip()
    floor = min_date or TODAY
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", text)
    if not m:
        return None
    day, month, year_raw = int(m.group(1)), int(m.group(2)), m.group(3)
    if month < 1 or month > 12 or day < 1 or day > 31:
        return None
    if year_raw is None:
        parsed = _safe_date(floor.year, month, day)
        if parsed is None:
            return None
        if parsed < floor:
            parsed = _safe_date(floor.year + 1, month, day)
        return parsed
    year = int(year_raw)
    if year < 100:
        year += 2000
    return _safe_date(year, month, day)


def parse_date_range(text: str | None, min_date: date | None = None) -> tuple[date | None, date | None]:
    if not text:
        return None, None
    cleaned = re.sub(r"\s*(até|ate)\s*", " a ", str(text), flags=re.I)
    floor = min_date or TODAY
    full = _RANGE_FULL.search(cleaned)
    if full:
        start = parse_br_date(full.group(1), min_date=floor)
        end = parse_br_date(full.group(2), min_date=start or floor)
        return start, end
    m = _RANGE_COMPACT.search(cleaned)
    if m and "/" not in m.group(1):
        year = m.group(4)
        suffix = f"/{year}" if year else ""
        start = parse_br_date(f"{m.group(1)}/{m.group(3)}{suffix}", min_date=floor)
        end = parse_br_date(f"{m.group(2)}/{m.group(3)}{suffix}", min_date=start or floor)
        return start, end
    parts = re.split(r"\s+a\s+|\s*-\s*", cleaned, maxsplit=1, flags=re.I)
    start = parse_br_date(parts[0], min_date=floor) if parts else None
    end = parse_br_date(parts[1], min_date=start or floor) if len(parts) > 1 else start
    return start, end


def extract_departure_dates(*texts: str, today: date | None = None) -> list[date]:
    """Extrai saídas. Intervalo '16 a 21/09' conta só o dia 16, não o retorno."""
    today = today or TODAY
    blob = " · ".join(str(t) for t in texts if t)
    if not blob:
        return []

    used = [False] * len(blob)
    found: list[date] = []

    def available(start: int, end: int) -> bool:
        return all(not used[i] for i in range(start, end))

    def mark(start: int, end: int) -> None:
        for i in range(start, end):
            used[i] = True

    def add(parsed: date | None) -> None:
        if parsed:
            found.append(parsed)

    for m in _JS_DATE_RE.finditer(blob):
        if not available(m.start(), m.end()):
            continue
        add(parse_js_date(m.group(0)))
        mark(m.start(), m.end())

    for m in _RANGE_FULL.finditer(blob):
        if not available(m.start(), m.end()):
            continue
        start = parse_br_date(m.group(1), min_date=today)
        add(start)
        mark(m.start(), m.end())

    for m in _RANGE_COMPACT.finditer(blob):
        if not available(m.start(), m.end()):
            continue
        year = m.group(4)
        suffix = f"/{year}" if year else ""
        start = parse_br_date(f"{m.group(1)}/{m.group(3)}{suffix}", min_date=today)
        add(start)
        mark(m.start(), m.end())

    for m in _DATE_TOKEN.finditer(blob):
        if not available(m.start(), m.end()):
            continue
        parsed = parse_br_date(m.group(0), min_date=today)
        add(parsed)
        mark(m.start(), m.end())

    return found


def future_iso_dates(dates: list[date], today: date | None = None) -> list[str]:
    today = today or TODAY
    unique = sorted({d for d in dates if d >= today})
    return [d.isoformat() for d in unique]


def next_sort_date(iso_dates: list[str]) -> str:
    return iso_dates[0] if iso_dates else ""


def dates_attr(iso_dates: list[str]) -> str:
    return ",".join(iso_dates)


def format_short_pt(value: date | None) -> str:
    if not value:
        return ""
    return f"{value.day} {MESES_CURTOS[value.month - 1]}"


def nights_between(start: date | None, end: date | None) -> int | None:
    if start and end and end >= start:
        delta = (end - start).days
        return delta if delta > 0 else None
    return None


def combine_datetime(day: date | None, hhmm: str | None) -> datetime | None:
    if not day:
        return None
    if not hhmm:
        return datetime.combine(day, time.min)
    try:
        hour, minute = [int(p) for p in hhmm.split(":", 1)]
        return datetime.combine(day, time(hour, minute))
    except (TypeError, ValueError):
        return datetime.combine(day, time.min)


def itinerary_valid(
    departure: date | None,
    return_day: date | None,
    departure_time: str | None = None,
    return_time: str | None = None,
) -> bool:
    if departure and return_day:
        dep_dt = combine_datetime(departure, departure_time)
        ret_dt = combine_datetime(return_day, return_time)
        if dep_dt and ret_dt:
            return ret_dt >= dep_dt
    return True
