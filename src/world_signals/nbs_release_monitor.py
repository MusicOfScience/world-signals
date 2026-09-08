from __future__ import annotations

from hashlib import sha256
import json

from .adapters.nbs_native_rss import NBSNativeReleaseItem

NBS_TIMEZONE = "Asia/Shanghai"
CANONICAL_SOURCE_ID = "WSSRC-MAC-007"
MONITOR_SOURCE_ID = "WSSRC-MAC-026"
EXPECTED_CONFIGURED_COUNT = 36


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _identity_map(config: dict) -> dict[str, dict]:
    raw = config.get("identity_by_occurrence_id")
    if not isinstance(raw, dict) or len(raw) != EXPECTED_CONFIGURED_COUNT:
        raise ValueError(f"NBS RSS identity map must contain exactly {EXPECTED_CONFIGURED_COUNT} occurrences")
    out: dict[str, dict] = {}
    seen: set[tuple[str, int, int]] = set()
    for occurrence_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"NBS RSS identity config must be an object for {occurrence_id}")
        series_key = value.get("series_key")
        series_id = value.get("series_id")
        reference_year = value.get("reference_year")
        reference_month = value.get("reference_month")
        start_local = value.get("start_local")
        start_utc = value.get("start_utc")
        if series_key not in {"CPI", "PPI", "PMI", "NEP", "IP", "ENERGY", "FAI", "REALESTATE", "RETAIL"}:
            raise ValueError(f"NBS RSS invalid series key for {occurrence_id}: {series_key!r}")
        if not isinstance(series_id, str) or not series_id.startswith("WSER-"):
            raise ValueError(f"NBS RSS invalid series_id for {occurrence_id}")
        if not isinstance(reference_year, int) or reference_year < 2000:
            raise ValueError(f"NBS RSS invalid reference year for {occurrence_id}")
        if not isinstance(reference_month, int) or not 1 <= reference_month <= 12:
            raise ValueError(f"NBS RSS invalid reference month for {occurrence_id}")
        if not isinstance(start_local, str) or "T" not in start_local:
            raise ValueError(f"NBS RSS invalid start_local for {occurrence_id}")
        if not isinstance(start_utc, str) or not start_utc.endswith("Z"):
            raise ValueError(f"NBS RSS invalid start_utc for {occurrence_id}")
        identity = (series_key, reference_year, reference_month)
        if identity in seen:
            raise ValueError(f"NBS RSS duplicate configured identity: {identity!r}")
        seen.add(identity)
        out[occurrence_id] = {
            "series_key": series_key,
            "series_id": series_id,
            "reference_year": reference_year,
            "reference_month": reference_month,
            "start_local": start_local,
            "start_utc": start_utc,
        }
    return out


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != EXPECTED_CONFIGURED_COUNT or len(configured) != len(set(configured)):
        raise ValueError(f"NBS RSS configured scope must contain exactly {EXPECTED_CONFIGURED_COUNT} unique occurrence IDs")
    identity_by_id = _identity_map(config)
    if set(identity_by_id) != set(configured):
        raise ValueError("NBS RSS identity map does not exactly match configured occurrence IDs")

    configured_set = set(configured)
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in configured_set}
    if set(by_id) != configured_set:
        missing = sorted(configured_set - set(by_id))
        raise ValueError(f"NBS RSS configured occurrence missing from Canonical: {missing!r}")

    for occurrence_id in configured:
        row = by_id[occurrence_id]
        identity = identity_by_id[occurrence_id]
        checks = {
            "series_id": identity["series_id"],
            "source_id": CANONICAL_SOURCE_ID,
            "region": "East Asia",
            "source_timezone": NBS_TIMEZONE,
            "time_precision": "MINUTE",
            "timing_type": "LOCAL_DATETIME",
            "event_type": "DATA_RELEASE",
            "start_local": identity["start_local"],
            "start_utc": identity["start_utc"],
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(
                    f"NBS Canonical scope drift for {occurrence_id} {key}: "
                    f"expected {expected!r}, found {row.get(key)!r}"
                )

    gate_checks = {
        "source_id": MONITOR_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "request_budget_per_run": 1,
        "schedule_request_count_per_run": 0,
        "english_rss_request_count_per_run": 0,
        "article_followup_request_count_per_run": 0,
        "schedule_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "rss_publication_metadata_is_event_clock_authority": False,
        "rss_publication_metadata_is_schedule_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_item_link_fetch_allowed": False,
        "automatic_schedule_html_fetch_allowed": False,
        "automatic_english_rss_fetch_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gate_checks.items():
        if config.get(key) != expected:
            raise ValueError(f"NBS RSS monitor gate drift for {key}: {config.get(key)!r}")
    return by_id, identity_by_id


def _publication_candidate(record: dict, item: NBSNativeReleaseItem) -> dict:
    evidence = {
        "feed_title": item.title,
        "feed_link": item.link,
        "feed_channel": item.channel,
        "feed_source_text": item.source_text,
        "feed_publication_time": item.publication_time,
        "feed_publication_date": item.publication_date,
        "feed_doc_id": item.doc_id,
        "series_key": item.series_key,
        "reference_year": item.reference_year,
        "reference_month": item.reference_month,
        "canonical_start_local": record.get("start_local"),
        "canonical_start_utc": record.get("start_utc"),
        "canonical_source_id": record.get("source_id"),
        "feed_publication_metadata_is_event_clock_authority": False,
        "feed_publication_metadata_is_schedule_authority": False,
    }
    digest = _stable_hash({"occurrence_id": record["occurrence_id"], **evidence})
    return {
        "candidate_id": "WSRC-NBS-RSS-" + digest[:16],
        "candidate_type": "CHINA_NBS_CONFIGURED_RELEASE_PUBLICATION_EVIDENCE",
        "source_id": MONITOR_SOURCE_ID,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "lifecycle_status": record.get("lifecycle_status"),
            "certainty_status": record.get("certainty_status"),
            "start_local": record.get("start_local"),
            "start_utc": record.get("start_utc"),
            "time_precision": record.get("time_precision"),
            "source_timezone": record.get("source_timezone"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": evidence,
        "review_state": "PENDING_AUTHORITATIVE_NBS_PUBLICATION_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
        "completion_requires_review": True,
        "canonical_clock_mutation_allowed": False,
    }


def nbs_native_rss_review_candidates(
    records: list[dict],
    items: list[NBSNativeReleaseItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id, identity_by_id = _configured_scope(records, config)
    occurrence_by_identity = {
        (identity["series_key"], identity["reference_year"], identity["reference_month"]): by_id[occurrence_id]
        for occurrence_id, identity in identity_by_id.items()
    }

    candidates: list[dict] = []
    observations: list[dict] = []
    matched_ids: set[str] = set()

    for item in items:
        if item.series_key is None:
            continue
        identity = (item.series_key, int(item.reference_year), int(item.reference_month))
        record = occurrence_by_identity.get(identity)
        if record is None:
            observations.append({
                "type": "CHINA_NBS_RELEVANT_SERIES_PUBLICATION_OUTSIDE_CONFIGURED_SCOPE",
                "title": item.title,
                "link": item.link,
                "series_key": item.series_key,
                "reference_year": item.reference_year,
                "reference_month": item.reference_month,
                "feed_publication_time": item.publication_time,
                "feed_publication_metadata_is_event_clock_authority": False,
                "historical_or_untracked_publication_only": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        occurrence_id = record["occurrence_id"]
        if occurrence_id in matched_ids:
            raise ValueError(f"multiple NBS native RSS items mapped to one Canonical occurrence: {occurrence_id}")
        matched_ids.add(occurrence_id)

        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "CHINA_NBS_COMPLETED_OCCURRENCE_PUBLICATION_PRESENT_NO_LIFECYCLE_ACTION",
                "occurrence_id": occurrence_id,
                "canonical_source_id": CANONICAL_SOURCE_ID,
                "monitor_source_id": MONITOR_SOURCE_ID,
                "series_key": item.series_key,
                "reference_year": item.reference_year,
                "reference_month": item.reference_month,
                "feed_publication_time": item.publication_time,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
                "canonical_lifecycle_already_reviewed": True,
            })
            continue

        candidates.append(_publication_candidate(record, item))
        observations.append({
            "type": "CHINA_NBS_CONFIGURED_RELEASE_PUBLICATION_MATCHED_REVIEW_REQUIRED",
            "occurrence_id": occurrence_id,
            "canonical_source_id": CANONICAL_SOURCE_ID,
            "monitor_source_id": MONITOR_SOURCE_ID,
            "series_key": item.series_key,
            "reference_year": item.reference_year,
            "reference_month": item.reference_month,
            "feed_publication_time": item.publication_time,
            "feed_publication_metadata_is_event_clock_authority": False,
            "feed_publication_metadata_is_schedule_authority": False,
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    observations.append({
        "type": "CHINA_NBS_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_DELAY_CANCELLATION_OR_CERTAINTY_SEMANTICS",
        "configured_occurrence_count": len(by_id),
        "matched_occurrence_count": len(matched_ids),
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
