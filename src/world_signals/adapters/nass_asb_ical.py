from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from urllib.parse import urlparse

from .base import AdapterError, FetchSnapshot, fetch_bytes

NASS_ASB_ICAL_URL = "https://www.nass.usda.gov/Publications/Calendar/2026/NassReleases2026.ics"
NASS_PUBLICATIONS_URL = "https://www.nass.usda.gov/Publications/"
NASS_SECURITY_POLICY_URL = "https://www.nass.usda.gov/About_NASS/Security_Statement/index.php"
NASS_RIGHTS_URL = "https://www.nass.usda.gov/Data_and_Statistics/Citation_Request/"
NASS_TIMEZONE = "America/New_York"
NASS_ICAL_ACCEPT = "text/calendar,text/plain;q=0.9,*/*;q=0.1"
NASS_ICAL_HOST = "www.nass.usda.gov"
NASS_MIN_EVENTS = 1
NASS_MAX_EVENTS = 1000
NASS_TARGET_SUMMARIES = frozenset({"Crop Production", "Grain Stocks"})

_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
_FLOATING_DATETIME = re.compile(r"^\d{8}T\d{6}$")


@dataclass(frozen=True)
class NASSASBRelease:
    uid: str
    summary: str
    start_local: str
    dtstart_raw: str
    dtend_raw: str | None
    dtstamp_raw: str | None
    sequence_raw: str | None
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


def _unfold_ical(text: str) -> list[str]:
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[str] = []
    for line in raw:
        if line.startswith((" ", "\t")):
            if not lines:
                raise AdapterError("NASS iCalendar begins with an orphan folded line")
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _parse_property(line: str) -> tuple[str, dict[str, str], str]:
    if ":" not in line:
        raise AdapterError(f"NASS iCalendar malformed property line: {line!r}")
    lhs, value = line.split(":", 1)
    pieces = lhs.split(";")
    name = pieces[0].upper()
    if not name:
        raise AdapterError("NASS iCalendar empty property name")
    params: dict[str, str] = {}
    for part in pieces[1:]:
        if "=" not in part:
            raise AdapterError(f"NASS iCalendar malformed property parameter: {line!r}")
        key, val = part.split("=", 1)
        key = key.upper()
        if not key or key in params:
            raise AdapterError(f"NASS iCalendar duplicate/empty property parameter: {line!r}")
        params[key] = val
    return name, params, value


def _single(props: dict[str, list[tuple[dict[str, str], str]]], name: str, *, required: bool) -> tuple[dict[str, str], str] | None:
    values = props.get(name, [])
    if len(values) > 1:
        raise AdapterError(f"NASS iCalendar target event has duplicate {name}")
    if not values:
        if required:
            raise AdapterError(f"NASS iCalendar target event missing {name}")
        return None
    return values[0]


def _parse_floating_start(params: dict[str, str], raw: str) -> str:
    if params:
        raise AdapterError(f"NASS target DTSTART unexpectedly carries parameters: {params!r}")
    if raw.endswith("Z") or not _FLOATING_DATETIME.fullmatch(raw):
        raise AdapterError(f"NASS target DTSTART is not a floating second-precision datetime: {raw!r}")
    try:
        parsed = datetime.strptime(raw, "%Y%m%dT%H%M%S")
    except ValueError as exc:
        raise AdapterError(f"NASS target DTSTART is not a real civil datetime: {raw!r}") from exc
    return parsed.isoformat(timespec="seconds")


def parse_nass_asb_ical(body: bytes | str) -> list[NASSASBRelease]:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    head = raw[:3000].decode("utf-8", errors="replace").lower()
    if "<html" in head or "<!doctype" in head or "request rejected" in head or "access denied" in head:
        raise AdapterError("NASS iCalendar returned HTML/rejection content")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AdapterError("NASS iCalendar is not valid UTF-8") from exc
    lines = _unfold_ical(text)
    if lines.count("BEGIN:VCALENDAR") != 1 or lines.count("END:VCALENDAR") != 1:
        raise AdapterError("NASS iCalendar must contain exactly one VCALENDAR boundary")

    events: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            if current is not None:
                raise AdapterError("NASS iCalendar nested VEVENT")
            current = []
        elif line == "END:VEVENT":
            if current is None:
                raise AdapterError("NASS iCalendar orphan END:VEVENT")
            events.append(current)
            current = None
        elif current is not None:
            current.append(line)
    if current is not None:
        raise AdapterError("NASS iCalendar unclosed VEVENT")
    if not NASS_MIN_EVENTS <= len(events) <= NASS_MAX_EVENTS:
        raise AdapterError(
            f"NASS iCalendar event-count outside bounded contract: {len(events)} not in [{NASS_MIN_EVENTS}, {NASS_MAX_EVENTS}]"
        )

    seen_uids: set[str] = set()
    targets: list[NASSASBRelease] = []
    for event_lines in events:
        props: dict[str, list[tuple[dict[str, str], str]]] = {}
        for line in event_lines:
            name, params, value = _parse_property(line)
            props.setdefault(name, []).append((params, value))

        uid_entry = _single(props, "UID", required=False)
        if uid_entry is not None:
            uid = uid_entry[1].strip()
            if not uid:
                raise AdapterError("NASS iCalendar empty UID")
            if uid in seen_uids:
                raise AdapterError(f"NASS iCalendar duplicate UID: {uid}")
            seen_uids.add(uid)

        summary_entry = _single(props, "SUMMARY", required=False)
        if summary_entry is None:
            continue
        summary = summary_entry[1].strip()
        if summary not in NASS_TARGET_SUMMARIES:
            continue

        if uid_entry is None:
            raise AdapterError(f"NASS target event {summary!r} missing UID")
        uid = uid_entry[1].strip()
        if _UUID.fullmatch(uid) is None:
            raise AdapterError(f"NASS target UID is not UUID-shaped: {uid!r}")

        dtstart_entry = _single(props, "DTSTART", required=True)
        assert dtstart_entry is not None
        start_local = _parse_floating_start(dtstart_entry[0], dtstart_entry[1].strip())

        dtend_entry = _single(props, "DTEND", required=False)
        dtstamp_entry = _single(props, "DTSTAMP", required=False)
        sequence_entry = _single(props, "SEQUENCE", required=False)
        description_entry = _single(props, "DESCRIPTION", required=False)
        targets.append(
            NASSASBRelease(
                uid=uid,
                summary=summary,
                start_local=start_local,
                dtstart_raw=dtstart_entry[1].strip(),
                dtend_raw=None if dtend_entry is None else dtend_entry[1].strip(),
                dtstamp_raw=None if dtstamp_entry is None else dtstamp_entry[1].strip(),
                sequence_raw=None if sequence_entry is None else sequence_entry[1].strip(),
                description="" if description_entry is None else description_entry[1],
            )
        )
    if not targets:
        raise AdapterError("NASS iCalendar contains no Crop Production or Grain Stocks target events")
    return targets


def fetch_nass_asb_ical(*, timeout: int = 30) -> tuple[list[NASSASBRelease], FetchSnapshot]:
    body, snapshot = fetch_bytes(NASS_ASB_ICAL_URL, timeout=timeout, accept=NASS_ICAL_ACCEPT)
    if snapshot.status != 200:
        raise AdapterError(f"NASS iCalendar returned HTTP {snapshot.status}")
    parsed = urlparse(snapshot.resolved_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != NASS_ICAL_HOST
        or parsed.path != "/Publications/Calendar/2026/NassReleases2026.ics"
        or parsed.query
        or parsed.fragment
        or parsed.params
    ):
        raise AdapterError(f"NASS iCalendar resolved away from exact official endpoint: {snapshot.resolved_url!r}")
    if "text/calendar" not in snapshot.content_type.lower():
        raise AdapterError(f"NASS iCalendar content-type drift: {snapshot.content_type!r}")
    if snapshot.body_bytes < 1000 or snapshot.body_bytes > 2_000_000:
        raise AdapterError(f"NASS iCalendar body-size drift: {snapshot.body_bytes} bytes")
    return parse_nass_asb_ical(body), snapshot
