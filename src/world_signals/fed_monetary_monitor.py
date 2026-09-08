from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

from .adapters.fed_monetary_rss import FedMonetaryRSSItem

FOMC_TIMEZONE = "America/New_York"
DECISION_SERIES = "WS.CB.FED.FOMC_POLICY_DECISION"
MINUTES_SERIES = "WS.CB.FED.FOMC_MINUTES"
DECISION_TITLE = "Federal Reserve issues FOMC statement"
MINUTES_TITLE_RE = re.compile(r"^Minutes of the Federal Open Market Committee,\s+.+$", re.I)


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"Fed RSS publication timestamp must be UTC Z time: {value!r}")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"invalid Fed RSS UTC publication timestamp: {value!r}") from exc
    return dt.astimezone(timezone.utc)


def _canonical_datetime(record: dict) -> datetime:
    value = record.get("start_local")
    if not isinstance(value, str):
        raise ValueError(f"FOMC Canonical occurrence lacks start_local: {record.get('occurrence_id')}")
    try:
        local = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid FOMC Canonical start_local: {value!r}") from exc
    if local.tzinfo is not None:
        raise ValueError(f"FOMC Canonical start_local unexpectedly carries offset: {value!r}")
    return local.replace(tzinfo=ZoneInfo(FOMC_TIMEZONE))


def classify_fed_monetary_item(item: FedMonetaryRSSItem) -> str | None:
    if item.title == DECISION_TITLE and item.description == DECISION_TITLE:
        return DECISION_SERIES
    if MINUTES_TITLE_RE.fullmatch(item.title) and item.description == item.title:
        return MINUTES_SERIES
    return None


def is_fomc_related(item: FedMonetaryRSSItem) -> bool:
    text = (item.title + " " + item.description).casefold()
    return "fomc" in text or "federal open market committee" in text


def _configured_scope(records: list[dict], config: dict) -> dict[str, dict]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 22 or len(configured) != len(set(configured)):
        raise ValueError("Fed monetary RSS configured scope must contain exactly 22 unique occurrence IDs")
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in set(configured)}
    if set(by_id) != set(configured):
        raise ValueError("Fed monetary RSS configured occurrence missing from Canonical")
    for occurrence_id in configured:
        row = by_id[occurrence_id]
        if row.get("source_id") != "WSSRC-CB-001":
            raise ValueError(f"FOMC Canonical source-role drift for {occurrence_id}")
        if row.get("series_id") not in {DECISION_SERIES, MINUTES_SERIES}:
            raise ValueError(f"FOMC RSS scope contains unsupported series for {occurrence_id}")
        if row.get("source_timezone") != FOMC_TIMEZONE:
            raise ValueError(f"FOMC Canonical timezone drift for {occurrence_id}")
        if row.get("time_precision") != "MINUTE":
            raise ValueError(f"FOMC Canonical precision drift for {occurrence_id}")
    return by_id


def _nearest_occurrence(
    scoped: list[dict],
    *,
    series_id: str,
    published_utc: datetime,
    tolerance_minutes: int,
) -> tuple[dict | None, bool, int | None]:
    matches: list[tuple[int, dict]] = []
    for record in scoped:
        if record.get("series_id") != series_id:
            continue
        canonical_utc = _canonical_datetime(record).astimezone(timezone.utc)
        delta_seconds = abs(int((canonical_utc - published_utc).total_seconds()))
        if delta_seconds <= tolerance_minutes * 60:
            matches.append((delta_seconds, record))
    matches.sort(key=lambda pair: (pair[0], pair[1]["occurrence_id"]))
    if not matches:
        return None, False, None
    if len(matches) > 1 and matches[0][0] == matches[1][0]:
        return None, True, matches[0][0]
    return matches[0][1], False, matches[0][0]


def _publication_candidate(record: dict, item: FedMonetaryRSSItem, *, monitor_source_id: str) -> dict:
    evidence = {
        "feed_title": item.title,
        "feed_link": item.link,
        "feed_guid": item.guid,
        "published_utc": item.pub_date_utc,
        "canonical_start_local": record.get("start_local"),
        "canonical_timezone": record.get("source_timezone"),
        "canonical_source_id": record.get("source_id"),
    }
    digest = _stable_hash({"occurrence_id": record["occurrence_id"], **evidence})
    return {
        "candidate_id": "WSRC-FED-RSS-" + digest[:16],
        "candidate_type": "FED_FOMC_PUBLICATION_EVIDENCE_AVAILABLE",
        "source_id": monitor_source_id,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "lifecycle_status": record.get("lifecycle_status"),
            "start_local": record.get("start_local"),
            "source_timezone": record.get("source_timezone"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": evidence,
        "review_state": "PENDING_AUTHORITATIVE_FOMC_PUBLICATION_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
        "completion_requires_review": True,
    }


def fed_monetary_rss_review_candidates(
    records: list[dict],
    items: list[FedMonetaryRSSItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id = _configured_scope(records, config)
    scoped = list(by_id.values())
    tolerance = int((config.get("matching") or {}).get("timestamp_tolerance_minutes", 180))
    if tolerance < 0 or tolerance > 180:
        raise ValueError("Fed monetary RSS timestamp tolerance must be between 0 and 180 minutes")
    monitor_source_id = str(config.get("source_id") or "")
    if monitor_source_id != "WSSRC-CB-015":
        raise ValueError("Fed monetary RSS monitor source identity drifted")

    candidates: list[dict] = []
    observations: list[dict] = []
    matched_occurrence_ids: set[str] = set()

    for item in items:
        series_id = classify_fed_monetary_item(item)
        if series_id is None:
            if is_fomc_related(item):
                observations.append({
                    "type": "FED_FOMC_RSS_ITEM_UNCLASSIFIED_NO_EVENT_INFERENCE",
                    "title": item.title,
                    "guid": item.guid,
                    "published_utc": item.pub_date_utc,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                })
            continue

        published_utc = _parse_utc(item.pub_date_utc)
        record, ambiguous, delta_seconds = _nearest_occurrence(
            scoped,
            series_id=series_id,
            published_utc=published_utc,
            tolerance_minutes=tolerance,
        )
        if ambiguous:
            observations.append({
                "type": "FED_FOMC_RSS_IDENTITY_AMBIGUOUS_NO_GUESS",
                "series_id": series_id,
                "guid": item.guid,
                "published_utc": item.pub_date_utc,
                "event_state_inference": "NONE",
            })
            continue
        if record is None:
            observations.append({
                "type": "FED_FOMC_RSS_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE",
                "series_id": series_id,
                "title": item.title,
                "guid": item.guid,
                "published_utc": item.pub_date_utc,
                "historical_or_untracked_publication_only": True,
                "event_state_inference": "NONE",
            })
            continue
        occurrence_id = record["occurrence_id"]
        if occurrence_id in matched_occurrence_ids:
            raise ValueError(f"multiple Fed RSS publications mapped to one Canonical occurrence: {occurrence_id}")
        matched_occurrence_ids.add(occurrence_id)

        # Once Canonical completion has been manually reviewed and committed,
        # the same rolling-feed publication becomes corroboration only. This
        # avoids generating a fresh completion proposition on every daily run.
        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "FED_FOMC_RSS_COMPLETED_OCCURRENCE_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION",
                "occurrence_id": occurrence_id,
                "series_id": series_id,
                "canonical_source_id": record.get("source_id"),
                "monitor_source_id": monitor_source_id,
                "published_utc": item.pub_date_utc,
                "canonical_start_local": record.get("start_local"),
                "timestamp_delta_seconds": delta_seconds,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
                "canonical_lifecycle_already_reviewed": True,
            })
            continue

        candidates.append(_publication_candidate(record, item, monitor_source_id=monitor_source_id))
        observations.append({
            "type": "FED_FOMC_RSS_PUBLICATION_MATCHED_REVIEW_REQUIRED",
            "occurrence_id": occurrence_id,
            "series_id": series_id,
            "canonical_source_id": record.get("source_id"),
            "monitor_source_id": monitor_source_id,
            "published_utc": item.pub_date_utc,
            "canonical_start_local": record.get("start_local"),
            "timestamp_delta_seconds": delta_seconds,
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    # Feed absence is deliberately nonsemantic. The RSS is a finite rolling
    # publication feed; it is not the FOMC schedule authority and is not
    # expected to contain future scheduled occurrences.
    observations.append({
        "type": "FED_FOMC_RSS_ABSENCE_HAS_NO_SCHEDULE_OR_LIFECYCLE_SEMANTICS",
        "configured_occurrence_count": len(scoped),
        "matched_occurrence_count": len(matched_occurrence_ids),
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
