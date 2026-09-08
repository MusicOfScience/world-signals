from __future__ import annotations

from hashlib import sha256
import json

from .adapters.cbsl_rss import CBSLMonetaryPolicyReviewItem

CBSL_TIMEZONE = "Asia/Colombo"
CBSL_SERIES_ID = "WSER-REGJ-LK-CBSL-MPB"
CANONICAL_SOURCE_ID = "WSSRC-REGJ-002"
MONITOR_SOURCE_ID = "WSSRC-REGJ-007"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _identity_map(config: dict) -> dict[str, dict]:
    raw = config.get("review_identity_by_occurrence_id")
    if not isinstance(raw, dict) or len(raw) != 2:
        raise ValueError("CBSL RSS review identity map must contain exactly two occurrences")
    out: dict[str, dict] = {}
    seen: set[tuple[int, int, str]] = set()
    for occurrence_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"CBSL RSS identity config must be an object for {occurrence_id}")
        review_number = value.get("review_number")
        review_year = value.get("year")
        announcement_date = value.get("announcement_date")
        if not isinstance(review_number, int) or review_number <= 0:
            raise ValueError(f"CBSL RSS invalid review number for {occurrence_id}")
        if not isinstance(review_year, int) or review_year < 2000:
            raise ValueError(f"CBSL RSS invalid review year for {occurrence_id}")
        if not isinstance(announcement_date, str) or len(announcement_date) != 10:
            raise ValueError(f"CBSL RSS invalid announcement date for {occurrence_id}")
        identity = (review_year, review_number, announcement_date)
        if identity in seen:
            raise ValueError(f"CBSL RSS duplicate configured review identity: {identity}")
        seen.add(identity)
        out[occurrence_id] = {
            "review_number": review_number,
            "year": review_year,
            "announcement_date": announcement_date,
        }
    return out


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 2 or len(configured) != len(set(configured)):
        raise ValueError("CBSL RSS configured scope must contain exactly two unique occurrence IDs")
    identity_by_id = _identity_map(config)
    if set(identity_by_id) != set(configured):
        raise ValueError("CBSL RSS identity map does not exactly match configured occurrence IDs")

    configured_set = set(configured)
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in configured_set}
    if set(by_id) != configured_set:
        raise ValueError("CBSL RSS configured occurrence missing from Canonical")

    for occurrence_id in configured:
        row = by_id[occurrence_id]
        identity = identity_by_id[occurrence_id]
        checks = {
            "series_id": CBSL_SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "region": "South Asia",
            "source_timezone": CBSL_TIMEZONE,
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "start_local": identity["announcement_date"],
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(f"CBSL Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None:
            raise ValueError(f"CBSL Canonical date-only occurrence unexpectedly has start_utc: {occurrence_id}")

    gate_checks = {
        "source_id": MONITOR_SOURCE_ID,
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_has_publication_clock": False,
        "official_link_filename_date_is_clock_time": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gate_checks.items():
        if config.get(key) != expected:
            raise ValueError(f"CBSL RSS monitor gate drift for {key}: {config.get(key)!r}")
    return by_id, identity_by_id


def _publication_candidate(record: dict, item: CBSLMonetaryPolicyReviewItem) -> dict:
    evidence = {
        "feed_title": item.title,
        "feed_link": item.link,
        "review_number": item.review_number,
        "review_year": item.review_year,
        "official_link_filename_date": item.link_date,
        "official_link_filename": item.link_filename,
        "canonical_start_local": record.get("start_local"),
        "canonical_source_id": record.get("source_id"),
        "rss_has_publication_clock": False,
        "official_link_filename_date_is_clock_time": False,
    }
    digest = _stable_hash({"occurrence_id": record["occurrence_id"], **evidence})
    return {
        "candidate_id": "WSRC-CBSL-RSS-" + digest[:16],
        "candidate_type": "CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_EVIDENCE",
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
        "review_state": "PENDING_AUTHORITATIVE_CBSL_MPR_PUBLICATION_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
        "completion_requires_review": True,
        "canonical_clock_mutation_allowed": False,
    }


def cbsl_mpr_rss_review_candidates(
    records: list[dict],
    items: list[CBSLMonetaryPolicyReviewItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id, identity_by_id = _configured_scope(records, config)
    occurrence_by_identity = {
        (identity["year"], identity["review_number"], identity["announcement_date"]): by_id[occurrence_id]
        for occurrence_id, identity in identity_by_id.items()
    }

    candidates: list[dict] = []
    observations: list[dict] = []
    matched_ids: set[str] = set()

    for item in items:
        identity = (item.review_year, item.review_number, item.link_date)
        record = occurrence_by_identity.get(identity)
        if record is None:
            observations.append({
                "type": "CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE",
                "title": item.title,
                "link": item.link,
                "review_number": item.review_number,
                "review_year": item.review_year,
                "official_link_filename_date": item.link_date,
                "historical_or_untracked_publication_only": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        occurrence_id = record["occurrence_id"]
        if occurrence_id in matched_ids:
            raise ValueError(f"multiple CBSL MPR feed items mapped to one Canonical occurrence: {occurrence_id}")
        matched_ids.add(occurrence_id)

        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "CBSL_COMPLETED_OCCURRENCE_MPR_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION",
                "occurrence_id": occurrence_id,
                "canonical_source_id": CANONICAL_SOURCE_ID,
                "monitor_source_id": MONITOR_SOURCE_ID,
                "review_number": item.review_number,
                "review_year": item.review_year,
                "official_link_filename_date": item.link_date,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
                "canonical_lifecycle_already_reviewed": True,
            })
            continue

        candidates.append(_publication_candidate(record, item))
        observations.append({
            "type": "CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_MATCHED_REVIEW_REQUIRED",
            "occurrence_id": occurrence_id,
            "canonical_source_id": CANONICAL_SOURCE_ID,
            "monitor_source_id": MONITOR_SOURCE_ID,
            "review_number": item.review_number,
            "review_year": item.review_year,
            "official_link_filename_date": item.link_date,
            "rss_has_publication_clock": False,
            "official_link_filename_date_is_clock_time": False,
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    observations.append({
        "type": "CBSL_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_OR_CERTAINTY_SEMANTICS",
        "configured_occurrence_count": len(by_id),
        "matched_occurrence_count": len(matched_ids),
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
