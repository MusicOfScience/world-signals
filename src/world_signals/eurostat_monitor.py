from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

EUROSTAT_ZONE = ZoneInfo("Europe/Luxembourg")


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _canonical_date(record: dict) -> date:
    value = record.get("start_local")
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError(f"Eurostat canonical occurrence {record.get('occurrence_id')} lacks start_local date")
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError(
            f"Eurostat canonical occurrence {record.get('occurrence_id')} has invalid start_local"
        ) from exc


def _review_candidate(
    *,
    source_id: str | None,
    occurrence_id: str,
    candidate_type: str,
    expected_title: str,
    canonical_date: str,
    evidence: dict,
) -> dict:
    payload = {
        "occurrence_id": occurrence_id,
        "candidate_type": candidate_type,
        "expected_title": expected_title,
        "canonical_date": canonical_date,
        "evidence": evidence,
    }
    return {
        "candidate_id": "WSRC-EUROSTAT-" + _stable_hash(payload)[:16],
        "candidate_type": candidate_type,
        "source_id": source_id,
        "occurrence_ids": [occurrence_id],
        "old_value": {
            "canonical_civil_date": canonical_date,
            "expected_feed_title": expected_title,
        },
        "new_value": evidence,
        "review_state": "PENDING_EUROSTAT_RELEASE_CALENDAR_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "automatic_commit_allowed": False,
        "event_state_inference": "NONE",
        "precision_effect": "DATE_ONLY_FEED_CANNOT_CREATE_REMOVE_OR_CHANGE_CANONICAL_CLOCK_TIME",
    }


def eurostat_release_calendar_review_candidates(
    records: list[dict],
    items: list[object],
    config: dict,
    *,
    now_utc: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    """Compare exact tracked Eurostat release names at civil-date precision only.

    Eurostat's official ICS subscription is an all-release feed. WORLD SIGNALS
    narrows that source through an explicit tracked occurrence allow-list. The
    source's UID is intentionally not an occurrence identity: current research
    showed it varies between generated feed views. Exact title plus a bounded
    nearest-date match is therefore the source-side matching contract.

    The feed exposes civil dates for the tracked releases. It never downgrades
    richer canonical timestamps. Absence, ambiguity, or drift creates review
    evidence only and never means cancellation, completion, or certainty change.
    """
    tracked = config.get("tracked_items") or []
    allowed = set(config.get("canonical_occurrence_ids") or [])
    tracked_ids = {row.get("occurrence_id") for row in tracked}
    if not tracked or None in tracked_ids:
        raise ValueError("Eurostat monitor requires tracked_items with occurrence_id")
    if tracked_ids != allowed:
        raise ValueError("Eurostat tracked_items must exactly match canonical_occurrence_ids")

    record_by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in allowed}
    if set(record_by_id) != allowed:
        missing = sorted(allowed - set(record_by_id))
        raise ValueError(f"Eurostat configured canonical occurrences missing: {missing}")

    by_title: dict[str, list[object]] = {}
    for item in items:
        title = getattr(item, "summary", None)
        observed_date = getattr(item, "start_date", None)
        if title and observed_date:
            by_title.setdefault(title, []).append(item)

    max_days = int((config.get("matching") or {}).get("nearest_exact_title_max_days", 10))
    if max_days < 0 or max_days > 14:
        raise ValueError("Eurostat nearest-date matching bound must be in 0..14 days")

    now = (now_utc or datetime.now(timezone.utc)).astimezone(EUROSTAT_ZONE).date()
    candidates: list[dict] = []
    observations: list[dict] = []

    for spec in tracked:
        occurrence_id = spec["occurrence_id"]
        expected_title = spec.get("feed_title")
        if not expected_title:
            raise ValueError(f"Eurostat tracked item {occurrence_id} missing feed_title")
        record = record_by_id[occurrence_id]
        if record.get("source_timezone") != "Europe/Luxembourg":
            raise ValueError(f"Eurostat occurrence {occurrence_id} lost Europe/Luxembourg timezone")

        canonical = _canonical_date(record)
        if canonical < now:
            observations.append({
                "type": "EUROSTAT_TRACKED_OCCURRENCE_ELAPSED_NOT_PRESENCE_CHECKED",
                "occurrence_id": occurrence_id,
                "canonical_civil_date": canonical.isoformat(),
                "event_state_inference": "NONE",
            })
            continue

        exact_title = by_title.get(expected_title, [])
        nearby: list[tuple[int, object, date]] = []
        for item in exact_title:
            try:
                item_date = date.fromisoformat(str(getattr(item, "start_date")))
            except ValueError:
                continue
            distance = abs((item_date - canonical).days)
            if distance <= max_days:
                nearby.append((distance, item, item_date))

        if not nearby:
            evidence = {
                "expected_feed_title": expected_title,
                "nearby_exact_title_matches": [],
                "nearest_exact_title_max_days": max_days,
                "absence_is_not_event_state": True,
            }
            candidates.append(_review_candidate(
                source_id=config.get("source_id"),
                occurrence_id=occurrence_id,
                candidate_type="EUROSTAT_TRACKED_ITEM_ABSENT_OR_OUTSIDE_MATCH_WINDOW",
                expected_title=expected_title,
                canonical_date=canonical.isoformat(),
                evidence=evidence,
            ))
            observations.append({
                "type": "EUROSTAT_TRACKED_ITEM_ABSENT_REVIEW_ONLY",
                "occurrence_id": occurrence_id,
                "expected_feed_title": expected_title,
            })
            continue

        nearest_distance = min(row[0] for row in nearby)
        nearest = [row for row in nearby if row[0] == nearest_distance]
        if len(nearest) != 1:
            evidence = {
                "expected_feed_title": expected_title,
                "nearest_distance_days": nearest_distance,
                "matches": [
                    {
                        "summary": getattr(item, "summary", None),
                        "observed_civil_date": item_date.isoformat(),
                        "uid_evidence_only": getattr(item, "uid", None),
                    }
                    for _, item, item_date in nearest
                ],
                "uid_is_stable_identity": False,
            }
            candidates.append(_review_candidate(
                source_id=config.get("source_id"),
                occurrence_id=occurrence_id,
                candidate_type="EUROSTAT_TRACKED_ITEM_IDENTITY_AMBIGUOUS",
                expected_title=expected_title,
                canonical_date=canonical.isoformat(),
                evidence=evidence,
            ))
            observations.append({
                "type": "EUROSTAT_TRACKED_ITEM_IDENTITY_AMBIGUOUS",
                "occurrence_id": occurrence_id,
                "match_count": len(nearest),
            })
            continue

        _, item, observed = nearest[0]
        common = {
            "occurrence_id": occurrence_id,
            "feed_title": expected_title,
            "canonical_civil_date": canonical.isoformat(),
            "observed_civil_date": observed.isoformat(),
            "uid_evidence_only": getattr(item, "uid", None),
            "uid_is_stable_identity": False,
            "feed_time_precision": "DAY",
            "canonical_time_precision": record.get("time_precision"),
        }
        if observed != canonical:
            evidence = {
                **common,
                "date_delta_days": (observed - canonical).days,
                "canonical_start_local_preserved_for_review": record.get("start_local"),
                "canonical_start_utc_preserved_for_review": record.get("start_utc"),
            }
            candidates.append(_review_candidate(
                source_id=config.get("source_id"),
                occurrence_id=occurrence_id,
                candidate_type="EUROSTAT_RELEASE_DATE_DRIFT",
                expected_title=expected_title,
                canonical_date=canonical.isoformat(),
                evidence=evidence,
            ))
            observations.append({"type": "EUROSTAT_RELEASE_DATE_DRIFT_REVIEW_REQUIRED", **common})
        else:
            observations.append({"type": "EUROSTAT_RELEASE_DATE_NO_CHANGE", **common})

    return candidates, observations
