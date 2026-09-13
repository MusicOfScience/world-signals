from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import html
import re
from urllib.parse import parse_qs, urlparse
from urllib.robotparser import RobotFileParser

from .base import AdapterError, FetchSnapshot, USER_AGENT, fetch_bytes

INDEC_CALENDAR_URL = "https://www.indec.gob.ar/indec/web/Calendario-Fecha-0"
INDEC_ROBOTS_URL = "https://www.indec.gob.ar/robots.txt"
INDEC_MONTH_ROUTE_TEMPLATE = "https://www.indec.gob.ar/Calendario/FiltrosCalendario/mes/{month_slug}/0"
INDEC_TIMEZONE = "America/Argentina/Buenos_Aires"
INDEC_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"
INDEC_OFFICIAL_HOSTS = {"indec.gob.ar", "www.indec.gob.ar"}
GOOGLE_CALENDAR_HOST = "calendar.google.com"
TITLE_RE = re.compile(
    r"^Índice de precios al consumidor \(IPC\)\. Cobertura nacional\. "
    r"(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre) de (\d{4})$"
)
MONTH_SLUG_RE = re.compile(
    r"^(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)-(\d{4})$"
)
SPANISH_MONTHS = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}
HREF_RE = re.compile(r'''href\s*=\s*["']([^"']+)["']''', re.IGNORECASE)


@dataclass(frozen=True)
class INDECCPIRelease:
    title: str
    reference_period_month_es: str
    reference_period_year: int
    reference_period: str
    release_date: str
    start_local: str
    end_local: str
    source_timezone: str
    visible_time_label: str
    route_month_slug: str
    embedded_calendar_url: str

    def as_dict(self) -> dict:
        return asdict(self)


def month_route_url(month_slug: str) -> str:
    match = MONTH_SLUG_RE.fullmatch(month_slug)
    if match is None:
        raise AdapterError(f"invalid INDEC calendar month slug: {month_slug!r}")
    return INDEC_MONTH_ROUTE_TEMPLATE.format(month_slug=month_slug)


def _parse_compact_local(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError as exc:
        raise AdapterError(f"INDEC embedded calendar datetime drift: {value!r}") from exc


def _calendar_release_from_href(href: str, *, month_slug: str, normalized_html: str) -> INDECCPIRelease | None:
    parsed = urlparse(html.unescape(href))
    if parsed.scheme != "https" or parsed.hostname != GOOGLE_CALENDAR_HOST or parsed.path != "/calendar/render":
        return None
    query = parse_qs(parsed.query, keep_blank_values=True)
    if query.get("action") != ["TEMPLATE"]:
        return None
    titles = query.get("text") or []
    if len(titles) != 1:
        raise AdapterError("INDEC embedded Google calendar metadata must contain exactly one text value")
    title = titles[0]
    title_match = TITLE_RE.fullmatch(title)
    if title_match is None:
        return None

    dates = query.get("dates") or []
    zones = query.get("ctz") or []
    if len(dates) != 1 or len(zones) != 1:
        raise AdapterError("INDEC CPI embedded calendar metadata missing dates or ctz")
    if zones[0] != INDEC_TIMEZONE:
        raise AdapterError(f"INDEC CPI embedded timezone drift: {zones[0]!r}")
    date_parts = dates[0].split("/")
    if len(date_parts) != 2:
        raise AdapterError(f"INDEC CPI embedded dates range drift: {dates[0]!r}")
    start = _parse_compact_local(date_parts[0])
    end = _parse_compact_local(date_parts[1])
    if end <= start or int((end - start).total_seconds()) != 1800:
        raise AdapterError("INDEC CPI embedded calendar duration must remain exactly 30 minutes")

    route_match = MONTH_SLUG_RE.fullmatch(month_slug)
    assert route_match is not None
    route_month_name, route_year_raw = route_match.groups()
    if (start.year, start.month) != (int(route_year_raw), SPANISH_MONTHS[route_month_name]):
        raise AdapterError(
            f"INDEC CPI embedded release date {start.date().isoformat()} is outside route month {month_slug}"
        )

    reference_month_es, reference_year_raw = title_match.groups()
    visible_time_label = start.strftime("%H:%M") + "hs"
    if title not in normalized_html:
        raise AdapterError("INDEC CPI embedded title is not also present in visible first-party calendar markup")
    if visible_time_label not in normalized_html:
        raise AdapterError("INDEC CPI embedded time is not also present in visible first-party calendar markup")

    return INDECCPIRelease(
        title=title,
        reference_period_month_es=reference_month_es,
        reference_period_year=int(reference_year_raw),
        reference_period=f"{reference_month_es} de {reference_year_raw}",
        release_date=start.date().isoformat(),
        start_local=start.isoformat(),
        end_local=end.isoformat(),
        source_timezone=zones[0],
        visible_time_label=visible_time_label,
        route_month_slug=month_slug,
        embedded_calendar_url=html.unescape(href),
    )


def _parse_indec_cpi_month(
    body: bytes | str,
    *,
    month_slug: str,
    allow_absent: bool,
) -> INDECCPIRelease | None:
    raw = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    normalized = html.unescape(raw)
    matches: list[INDECCPIRelease] = []
    for href in HREF_RE.findall(raw):
        item = _calendar_release_from_href(href, month_slug=month_slug, normalized_html=normalized)
        if item is not None:
            matches.append(item)
    if not matches and allow_absent:
        return None
    if len(matches) != 1:
        raise AdapterError(
            f"INDEC month route {month_slug} must contain exactly one national CPI calendar identity; found {len(matches)}"
        )
    return matches[0]


def parse_indec_cpi_month(body: bytes | str, *, month_slug: str) -> INDECCPIRelease:
    item = _parse_indec_cpi_month(body, month_slug=month_slug, allow_absent=False)
    assert item is not None
    return item


def indec_routes_allowed(robots_body: bytes | str, month_slugs: list[str]) -> bool:
    text = robots_body.decode("utf-8", errors="replace") if isinstance(robots_body, bytes) else robots_body
    parser = RobotFileParser()
    try:
        parser.parse(text.splitlines())
    except Exception as exc:
        raise AdapterError(f"unable to parse INDEC robots policy: {exc}") from exc
    urls = [month_route_url(slug) for slug in month_slugs]
    return all(parser.can_fetch(USER_AGENT, url) for url in urls)


def fetch_indec_robots_policy(month_slugs: list[str], *, timeout: int = 30) -> tuple[bool, FetchSnapshot]:
    body, snapshot = fetch_bytes(
        INDEC_ROBOTS_URL,
        timeout=timeout,
        accept="text/plain,*/*;q=0.1",
    )
    if snapshot.status != 200:
        raise AdapterError(f"INDEC robots policy returned HTTP {snapshot.status}")
    return indec_routes_allowed(body, month_slugs), snapshot


def fetch_indec_cpi_month(
    month_slug: str,
    *,
    allow_absent: bool = False,
    timeout: int = 30,
) -> tuple[INDECCPIRelease | None, FetchSnapshot]:
    url = month_route_url(month_slug)
    body, snapshot = fetch_bytes(
        url,
        timeout=timeout,
        accept=INDEC_ACCEPT,
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": INDEC_CALENDAR_URL,
        },
    )
    if snapshot.status != 200:
        raise AdapterError(f"INDEC calendar month route returned HTTP {snapshot.status}: {month_slug}")
    parsed = urlparse(snapshot.resolved_url)
    if parsed.scheme != "https" or parsed.hostname not in INDEC_OFFICIAL_HOSTS:
        raise AdapterError(f"INDEC month route resolved outside official HTTPS host: {snapshot.resolved_url!r}")
    return _parse_indec_cpi_month(
        body,
        month_slug=month_slug,
        allow_absent=allow_absent,
    ), snapshot


def fetch_indec_cpi_months(
    month_slugs: list[str],
    *,
    allow_absent_month_slugs: set[str] | None = None,
    timeout: int = 30,
) -> tuple[list[INDECCPIRelease], list[FetchSnapshot]]:
    if not month_slugs or len(month_slugs) != len(set(month_slugs)):
        raise AdapterError("INDEC month route list must be non-empty and unique")
    allowed_absences = set(allow_absent_month_slugs or set())
    if not allowed_absences.issubset(set(month_slugs)):
        raise AdapterError("INDEC allowed-absence month routes must be within the requested route set")
    releases: list[INDECCPIRelease] = []
    snapshots: list[FetchSnapshot] = []
    for month_slug in month_slugs:
        item, snapshot = fetch_indec_cpi_month(
            month_slug,
            allow_absent=month_slug in allowed_absences,
            timeout=timeout,
        )
        if item is not None:
            releases.append(item)
        snapshots.append(snapshot)
    return releases, snapshots
