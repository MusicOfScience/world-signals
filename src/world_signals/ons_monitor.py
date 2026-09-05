from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .monitor import compare_assertion

LONDON = ZoneInfo("Europe/London")


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def _source_match_candidate(
    *,
    source_id: str | None,
    occurrence_id: str,
    candidate_type: str,
    expected_title: str,
    matches: list[dict],
) -> dict:
    payload = {
        "occurrence_id": occurrence_id,
        "candidate_type": candidate_type,
        "expected_feed_title": expected_title,
        "matches": matches,
    }
    return {
        "candidate_id": "WSRC-ONS-" + _stable_hash(payload)[:16],
        "candidate_type": candidate_type,
        "source_id": source_id,
        "occurrence_ids": [occurrence_id],
        "old_value": {"expected_feed_title": expected_title},
        "new_value": {"matches": matches},
        "review_state": "PENDING_ONS_RELEASE_CALENDAR_HTML_VERIFICATION",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "automatic_commit_allowed": False,
        "event_state_inference": "NONE",
    }


def ons_release_calendar_review_candidates(
    records: list[dict],
    items: list[object],
    config: dict,
    *,
    now_utc: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    """Compare exact tracked ONS RSS identities and datetimes with canonical state.

    The ONS RSS transport provides title/link/guid/pubDate but not the calendar's
    Confirmed/Provisional status. Consequently this monitor compares only exact
    item identity and scheduled datetime. Any drift is review-only and requires
    the official HTML release calendar/item page before canonical action.

    Absence never means cancellation or completion. Elapsed occurrences are not
    presence-checked against the upcoming-only feed.
    """
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    tracked = config.get("tracked_items") or []
    allowed = set(config.get("canonical_occurrence_ids") or [])
    tracked_ids = {x.get("occurrence_id") for x in tracked}
    if not tracked or None in tracked_ids:
        raise ValueError("ONS monitor requires tracked_items with occurrence_id")
    if tracked_ids != allowed:
        raise ValueError("ONS tracked_items must exactly match canonical_occurrence_ids")

    record_by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in allowed}
    if set(record_by_id) != allowed:
        missing = sorted(allowed - set(record_by_id))
        raise ValueError(f"ONS configured canonical occurrences missing: {missing}")

    by_title: dict[str, list[object]] = {}
    for item in items:
        title = getattr(item, "title", None)
        if title:
            by_title.setdefault(title, []).append(item)

    candidates: list[dict] = []
    observations: list[dict] = []

    for spec in tracked:
        occurrence_id = spec["occurrence_id"]
        expected_title = spec.get("feed_title")
        if not expected_title:
            raise ValueError(f"ONS tracked item {occurrence_id} missing feed_title")
        record = record_by_id[occurrence_id]
        canonical_start_utc = _parse_utc(record.get("start_utc"))
        if canonical_start_utc is None:
            raise ValueError(f"ONS canonical occurrence {occurrence_id} lacks valid start_utc")

        if canonical_start_utc < now:
            observations.append({
                "type": "ONS_TRACKED_OCCURRENCE_ELAPSED_NOT_PRESENCE_CHECKED",
                "occurrence_id": occurrence_id,
                "canonical_start_utc": canonical_start_utc.isoformat().replace("+00:00", "Z"),
                "event_state_inference": "NONE",
            })
            continue

        matches = by_title.get(expected_title, [])
        if not matches:
            candidate = _source_match_candidate(
                source_id=config.get("source_id"),
                occurrence_id=occurrence_id,
                candidate_type="ONS_TRACKED_ITEM_ABSENT_OR_RENAMED",
                expected_title=expected_title,
                matches=[],
            )
            candidates.append(candidate)
            observations.append({
                "type": "ONS_TRACKED_ITEM_ABSENT_NO_EVENT_STATE_INFERENCE",
                "occurrence_id": occurrence_id,
                "expected_feed_title": expected_title,
            })
            continue

        if len(matches) != 1:
            match_payload = [
                {
                    "title": getattr(item, "title", None),
                    "link": getattr(item, "link", None),
                    "guid": getattr(item, "guid", None),
                    "pub_date_iso": getattr(item, "pub_date_iso", None),
                }
                for item in matches
            ]
            candidate = _source_match_candidate(
                source_id=config.get("source_id"),
                occurrence_id=occurrence_id,
                candidate_type="ONS_TRACKED_ITEM_IDENTITY_AMBIGUOUS",
                expected_title=expected_title,
                matches=match_payload,
            )
            candidates.append(candidate)
            observations.append({
                "type": "ONS_TRACKED_ITEM_IDENTITY_AMBIGUOUS",
                "occurrence_id": occurrence_id,
                "match_count": len(matches),
            })
            continue

        item = matches[0]
        pub_utc = _parse_utc(getattr(item, "pub_date_iso", None))
        if pub_utc is None:
            candidate = _source_match_candidate(
                source_id=config.get("source_id"),
                occurrence_id=occurrence_id,
                candidate_type="ONS_TRACKED_ITEM_DATETIME_UNPARSABLE",
                expected_title=expected_title,
                matches=[{
                    "title": getattr(item, "title", None),
                    "link": getattr(item, "link", None),
                    "pub_date_iso": getattr(item, "pub_date_iso", None),
                }],
            )
            candidates.append(candidate)
            continue

        local = pub_utc.astimezone(LONDON).replace(tzinfo=None).isoformat(timespec="seconds")
        assertion = {
            "source_id": config.get("source_id"),
            "start_local": local,
            "source_url": getattr(item, "link", None),
            "source_title": getattr(item, "title", None),
            "source_guid": getattr(item, "guid", None),
            "source_pub_date_utc": pub_utc.isoformat().replace("+00:00", "Z"),
            "evidence_class": "POSITIVE_OFFICIAL_ONS_RSS_SCHEDULE_ITEM",
            "rss_carries_certainty_status": False,
            "required_manual_verification": "ONS_HTML_RELEASE_CALENDAR_OR_ITEM_PAGE",
        }
        candidate = compare_assertion(record, assertion)
        if candidate:
            data = candidate.as_dict()
            data["candidate_origin"] = "LIVE_READ_ONLY_MONITOR"
            data["review_state"] = "PENDING_ONS_RELEASE_CALENDAR_HTML_VERIFICATION"
            data["automatic_commit_allowed"] = False
            data["event_state_inference"] = "NONE_UNTIL_MANUAL_VERIFICATION"
            candidates.append(data)
            observations.append({
                "type": "ONS_RELEASE_DATETIME_DRIFT_REVIEW_REQUIRED",
                "occurrence_id": occurrence_id,
                "canonical_start_local": record.get("start_local"),
                "observed_start_local": local,
            })
        else:
            observations.append({
                "type": "ONS_RELEASE_DATETIME_NO_CHANGE",
                "occurrence_id": occurrence_id,
                "feed_title": expected_title,
                "observed_start_utc": pub_utc.isoformat().replace("+00:00", "Z"),
            })

    return candidates, observations
