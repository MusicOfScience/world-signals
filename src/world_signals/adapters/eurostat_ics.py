from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re

from .base import AdapterError, FetchSnapshot, fetch_bytes

EUROSTAT_ICS_SUBSCRIPTION_PAGE = "https://ec.europa.eu/eurostat/subscribe/ics.format"
EUROSTAT_ICS_ALL_RELEASES = "https://ec.europa.eu/eurostat/o/calendars/eventsIcal?theme=0&category=0"
EUROSTAT_TIMEZONE = "Europe/Luxembourg"
EUROSTAT_ICS_ACCEPT = "text/calendar,text/plain;q=0.9,*/*;q=0.1"


@dataclass(frozen=True)
class EurostatReleaseItem:
    summary: str
    start_date: str
    uid: str | None
    categories: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def _unfold_ical(text: str) -> list[str]:
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[str] = []
    for line in raw:
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _unescape_text(value: str) -> str:
    # RFC 5545 TEXT escaping. Order matters: escaped backslash is last.
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def _date_from_dtstart(lhs: str, value: str) -> str:
    """Return source civil date without manufacturing a clock.

    Eurostat's subscription feed currently publishes tracked release DTSTART values
    as DATE values. Datetime DTSTARTs are deliberately rejected here because a
    future transport change must be reviewed rather than silently changing the
    monitor's precision semantics.
    """
    clean = value.strip()
    if not re.fullmatch(r"\d{8}", clean):
        raise AdapterError(f"Eurostat DTSTART is not a civil DATE value: {lhs}:{value}")
    try:
        parsed = date(int(clean[:4]), int(clean[4:6]), int(clean[6:8]))
    except ValueError as exc:
        raise AdapterError(f"invalid Eurostat DTSTART civil date: {value}") from exc
    return parsed.isoformat()


def parse_eurostat_release_calendar_ics(body: bytes | str) -> list[EurostatReleaseItem]:
    text = body.decode("utf-8-sig", errors="replace") if isinstance(body, bytes) else body
    lines = _unfold_ical(text)
    if "BEGIN:VCALENDAR" not in lines or "END:VCALENDAR" not in lines:
        raise AdapterError("Eurostat response is not a complete VCALENDAR")

    items: list[EurostatReleaseItem] = []
    current: dict[str, tuple[str, str]] | None = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            if current is not None:
                raise AdapterError("nested Eurostat VEVENT")
            current = {}
            continue
        if line == "END:VEVENT":
            if current is None:
                raise AdapterError("Eurostat VEVENT terminator without opener")
            summary_entry = current.get("SUMMARY")
            dtstart_entry = current.get("DTSTART")
            if summary_entry is None or dtstart_entry is None:
                raise AdapterError("Eurostat VEVENT missing SUMMARY or DTSTART")
            summary = _unescape_text(summary_entry[1]).strip()
            if not summary:
                raise AdapterError("Eurostat VEVENT has empty SUMMARY")
            start_date = _date_from_dtstart(dtstart_entry[0], dtstart_entry[1])
            uid = current.get("UID")
            categories = current.get("CATEGORIES")
            items.append(
                EurostatReleaseItem(
                    summary=summary,
                    start_date=start_date,
                    uid=_unescape_text(uid[1]).strip() if uid and uid[1].strip() else None,
                    categories=(
                        _unescape_text(categories[1]).strip()
                        if categories and categories[1].strip()
                        else None
                    ),
                )
            )
            current = None
            continue
        if current is None or ":" not in line:
            continue
        lhs, value = line.split(":", 1)
        key = lhs.split(";", 1)[0].upper()
        if key in {"SUMMARY", "DTSTART", "UID", "CATEGORIES"}:
            if key in current:
                raise AdapterError(f"duplicate {key} in Eurostat VEVENT")
            current[key] = (lhs, value)

    if current is not None:
        raise AdapterError("unterminated Eurostat VEVENT")
    if not items:
        raise AdapterError("Eurostat VCALENDAR contained no VEVENT items")
    return items


def fetch_eurostat_release_calendar(
    *, timeout: int = 30
) -> tuple[list[EurostatReleaseItem], FetchSnapshot]:
    body, snapshot = fetch_bytes(
        EUROSTAT_ICS_ALL_RELEASES,
        timeout=timeout,
        accept=EUROSTAT_ICS_ACCEPT,
    )
    return parse_eurostat_release_calendar_ics(body), snapshot
