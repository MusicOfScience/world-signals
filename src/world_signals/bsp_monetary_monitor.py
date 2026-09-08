from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .adapters.bsp_rss import BSPMediaReleaseItem

BSP_TIMEZONE = "Asia/Manila"
BSP_SERIES_ID = "WSER-REGJ-PH-BSP-MB"
CANONICAL_SOURCE_ID = "WSSRC-REGJ-003"
MONITOR_SOURCE_ID = "WSSRC-REGJ-006"
STANCE_BODY_PHRASE = "at its monetary policy meeting today, the monetary board decided"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"BSP RSS publication timestamp must be UTC Z time: {value!r}")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise ValueError(f"invalid BSP RSS UTC publication timestamp: {value!r}") from exc


def is_bsp_monetary_policy_stance_item(item: BSPMediaReleaseItem) -> bool:
    return (
        item.title.casefold().startswith("monetary board ")
        and STANCE_BODY_PHRASE in item.description_text.casefold()
    )


def _configured_scope(records: list[dict], config: dict) -> dict[str, dict]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 2 or len(configured) != len(set(configured)):
        raise ValueError("BSP RSS configured scope must contain exactly two unique occurrence IDs")
    configured_set = set(configured)
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in configured_set}
    if set(by_id) != configured_set:
        raise ValueError("BSP RSS configured occurrence missing from Canonical")
    for occurrence_id in configured:
        row = by_id[occurrence_id]
        checks = {
            "series_id": BSP_SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "region": "Southeast Asia",
            "source_timezone": BSP_TIMEZONE,
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(f"BSP Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None:
            raise ValueError(f"BSP Canonical date-only occurrence unexpectedly has start_utc: {occurrence_id}")
    if config.get("source_id") != MONITOR_SOURCE_ID:
        raise ValueError("BSP RSS monitor source identity drifted")
    if config.get("schedule_authority") is not False:
        raise ValueError("BSP RSS must not become schedule authority")
    if config.get("lifecycle_authority") is not False:
        raise ValueError("BSP RSS must not become lifecycle authority")
    if config.get("certainty_authority") is not False:
        raise ValueError("BSP RSS must not become certainty authority")
    return by_id


def _publication_candidate(record: dict, item: BSPMediaReleaseItem, publication_local_date: str) -> dict:
    evidence = {
        "feed_title": item.title,
        "feed_link": item.link,
        "feed_guid": item.guid,
        "published_utc": item.pub_date_utc,
        "publication_local_date": publication_local_date,
        "publication_timezone": BSP_TIMEZONE,
        "canonical_start_local": record.get("start_local"),
        "canonical_source_id": record.get("source_id"),
        "rss_publication_time_is_event_time": False,
    }
    digest = _stable_hash({"occurrence_id": record["occurrence_id"], **evidence})
    return {
        "candidate_id": "WSRC-BSP-RSS-" + digest[:16],
        "candidate_type": "BSP_MONETARY_POLICY_STANCE_PUBLICATION_EVIDENCE",
        "source_id": MONITOR_SOURCE_ID,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "lifecycle_status": record.get("lifecycle_status"),
            "start_local": record.get("start_local"),
            "time_precision": record.get("time_precision"),
            "source_timezone": record.get("source_timezone"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": evidence,
        "review_state": "PENDING_AUTHORITATIVE_BSP_STANCE_PUBLICATION_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
        "completion_requires_review": True,
        "canonical_clock_mutation_allowed": False,
    }


def bsp_monetary_rss_review_candidates(
    records: list[dict],
    items: list[BSPMediaReleaseItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id = _configured_scope(records, config)
    by_date: dict[str, list[dict]] = {}
    for record in by_id.values():
        by_date.setdefault(str(record.get("start_local")), []).append(record)

    candidates: list[dict] = []
    observations: list[dict] = []
    matched_ids: set[str] = set()

    for item in items:
        if not is_bsp_monetary_policy_stance_item(item):
            continue
        published_utc = _parse_utc(item.pub_date_utc)
        publication_local_date = published_utc.astimezone(ZoneInfo(BSP_TIMEZONE)).date().isoformat()
        matches = by_date.get(publication_local_date, [])
        if not matches:
            observations.append({
                "type": "BSP_MONETARY_POLICY_STANCE_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE",
                "title": item.title,
                "guid": item.guid,
                "published_utc": item.pub_date_utc,
                "publication_local_date": publication_local_date,
                "historical_or_untracked_publication_only": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue
        if len(matches) != 1:
            observations.append({
                "type": "BSP_MONETARY_POLICY_STANCE_IDENTITY_AMBIGUOUS_NO_GUESS",
                "title": item.title,
                "guid": item.guid,
                "published_utc": item.pub_date_utc,
                "publication_local_date": publication_local_date,
                "match_count": len(matches),
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue
        record = matches[0]
        occurrence_id = record["occurrence_id"]
        if occurrence_id in matched_ids:
            raise ValueError(f"multiple BSP stance publications mapped to one Canonical occurrence: {occurrence_id}")
        matched_ids.add(occurrence_id)

        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "BSP_COMPLETED_OCCURRENCE_STANCE_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION",
                "occurrence_id": occurrence_id,
                "canonical_source_id": CANONICAL_SOURCE_ID,
                "monitor_source_id": MONITOR_SOURCE_ID,
                "published_utc": item.pub_date_utc,
                "publication_local_date": publication_local_date,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
                "canonical_lifecycle_already_reviewed": True,
            })
            continue

        candidates.append(_publication_candidate(record, item, publication_local_date))
        observations.append({
            "type": "BSP_MONETARY_POLICY_STANCE_PUBLICATION_MATCHED_REVIEW_REQUIRED",
            "occurrence_id": occurrence_id,
            "canonical_source_id": CANONICAL_SOURCE_ID,
            "monitor_source_id": MONITOR_SOURCE_ID,
            "published_utc": item.pub_date_utc,
            "publication_local_date": publication_local_date,
            "rss_publication_time_is_event_time": False,
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    observations.append({
        "type": "BSP_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_OR_CERTAINTY_SEMANTICS",
        "configured_occurrence_count": len(by_id),
        "matched_occurrence_count": len(matched_ids),
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
