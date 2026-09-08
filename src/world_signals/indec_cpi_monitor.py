from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .adapters.indec_calendar import INDECCPIRelease, INDEC_TIMEZONE

INDEC_SERIES_ID = "WSER-REG2-AR-CPI"
CANONICAL_SOURCE_ID = "WSSRC-REG2-006"
MONITOR_SOURCE_ID = "WSSRC-REG2-009"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _utc_for_local(start_local: str) -> str:
    local = datetime.fromisoformat(start_local).replace(tzinfo=ZoneInfo(INDEC_TIMEZONE))
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _identity_map(config: dict) -> dict[str, dict]:
    raw = config.get("identity_by_occurrence_id")
    if not isinstance(raw, dict) or len(raw) != 4:
        raise ValueError("INDEC CPI identity map must contain exactly four occurrences")
    out: dict[str, dict] = {}
    seen_reference_periods: set[str] = set()
    seen_month_slugs: set[str] = set()
    for occurrence_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"INDEC CPI identity config must be an object for {occurrence_id}")
        reference_period_es = value.get("reference_period_es")
        canonical_release_date = value.get("canonical_release_date")
        authoritative_calendar_time = value.get("authoritative_calendar_time")
        month_slug = value.get("month_slug")
        if not all(isinstance(v, str) and v for v in (
            reference_period_es, canonical_release_date, authoritative_calendar_time, month_slug
        )):
            raise ValueError(f"INDEC CPI incomplete identity config for {occurrence_id}")
        if reference_period_es in seen_reference_periods:
            raise ValueError(f"INDEC CPI duplicate configured reference period: {reference_period_es}")
        if month_slug in seen_month_slugs:
            raise ValueError(f"INDEC CPI duplicate configured month route: {month_slug}")
        seen_reference_periods.add(reference_period_es)
        seen_month_slugs.add(month_slug)
        out[occurrence_id] = {
            "reference_period_es": reference_period_es,
            "canonical_release_date": canonical_release_date,
            "authoritative_calendar_time": authoritative_calendar_time,
            "month_slug": month_slug,
        }
    return out


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 4 or len(set(configured)) != 4:
        raise ValueError("INDEC CPI configured scope must contain exactly four unique occurrence IDs")
    identity = _identity_map(config)
    if set(identity) != set(configured):
        raise ValueError("INDEC CPI identity map must exactly match configured occurrence IDs")

    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in set(configured)}
    if set(by_id) != set(configured):
        raise ValueError("INDEC CPI configured occurrence missing from Canonical")

    gate_checks = {
        "source_id": MONITOR_SOURCE_ID,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "request_budget_per_run": 5,
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_completed_release_fetch_allowed": False,
        "automatic_google_fetch_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gate_checks.items():
        if config.get(key) != expected:
            raise ValueError(f"INDEC CPI monitor gate drift for {key}: {config.get(key)!r}")

    for occurrence_id in configured:
        row = by_id[occurrence_id]
        expected = identity[occurrence_id]
        common = {
            "series_id": INDEC_SERIES_ID,
            "source_id": CANONICAL_SOURCE_ID,
            "region": "Latin America",
            "source_timezone": INDEC_TIMEZONE,
        }
        for key, value in common.items():
            if row.get(key) != value:
                raise ValueError(f"INDEC CPI Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}")

        precision = row.get("time_precision")
        if precision == "DAY":
            if row.get("timing_type") != "CIVIL_DATE" or row.get("start_local") != expected["canonical_release_date"]:
                raise ValueError(f"INDEC CPI date-only Canonical semantics drift for {occurrence_id}")
            if row.get("start_utc") is not None or row.get("all_day_semantics") is not True:
                raise ValueError(f"INDEC CPI date-only row gained inconsistent clock fields for {occurrence_id}")
        elif precision == "MINUTE":
            expected_local = expected["canonical_release_date"] + "T" + expected["authoritative_calendar_time"]
            if row.get("timing_type") != "TIMED_EVENT" or row.get("start_local") != expected_local:
                raise ValueError(f"INDEC CPI reviewed timed descendant does not match configured identity for {occurrence_id}")
            if row.get("start_utc") != _utc_for_local(expected_local) or row.get("all_day_semantics") is not False:
                raise ValueError(f"INDEC CPI reviewed timed descendant has inconsistent UTC/all-day semantics for {occurrence_id}")
        else:
            raise ValueError(f"INDEC CPI unsupported Canonical time precision for {occurrence_id}: {precision!r}")
    return by_id, identity


def _evidence(record: dict, item: INDECCPIRelease) -> dict:
    return {
        "report_title": item.title,
        "reference_period_es": item.reference_period,
        "observed_release_date": item.release_date,
        "observed_start_local": item.start_local,
        "observed_start_utc": _utc_for_local(item.start_local),
        "observed_end_local": item.end_local,
        "source_timezone": item.source_timezone,
        "visible_time_label": item.visible_time_label,
        "route_month_slug": item.route_month_slug,
        "embedded_google_calendar_metadata_observed": True,
        "google_followup_request_count": 0,
        "canonical_start_local": record.get("start_local"),
        "canonical_start_utc": record.get("start_utc"),
        "canonical_time_precision": record.get("time_precision"),
        "canonical_source_id": record.get("source_id"),
    }


def _candidate(record: dict, item: INDECCPIRelease | None, *, candidate_type: str) -> dict:
    evidence = None if item is None else _evidence(record, item)
    digest = _stable_hash({
        "candidate_type": candidate_type,
        "occurrence_id": record["occurrence_id"],
        "evidence": evidence,
    })
    return {
        "candidate_id": "WSRC-INDEC-CPI-" + digest[:16],
        "candidate_type": candidate_type,
        "source_id": MONITOR_SOURCE_ID,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "start_local": record.get("start_local"),
            "start_utc": record.get("start_utc"),
            "time_precision": record.get("time_precision"),
            "timing_type": record.get("timing_type"),
            "lifecycle_status": record.get("lifecycle_status"),
            "certainty_status": record.get("certainty_status"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": evidence,
        "review_state": "PENDING_AUTHORITATIVE_INDEC_CALENDAR_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "absence_is_not_cancellation_delay_completion_or_certainty_change": item is None,
        "automatic_commit_allowed": False,
        "canonical_clock_mutation_allowed": False,
        "lifecycle_mutation_allowed": False,
        "certainty_mutation_allowed": False,
    }


def indec_cpi_calendar_review_candidates(
    records: list[dict],
    releases: list[INDECCPIRelease],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id, identity = _configured_scope(records, config)
    by_reference: dict[str, INDECCPIRelease] = {}
    for item in releases:
        key = item.reference_period
        if key in by_reference:
            raise ValueError(f"multiple INDEC CPI calendar rows map to reference period {key!r}")
        by_reference[key] = item

    candidates: list[dict] = []
    observations: list[dict] = []
    configured_references = {v["reference_period_es"] for v in identity.values()}

    for key, item in by_reference.items():
        if key not in configured_references:
            observations.append({
                "type": "INDEC_CPI_CALENDAR_ROW_OUTSIDE_CONFIGURED_SCOPE",
                "reference_period_es": key,
                "release_date": item.release_date,
                "start_local": item.start_local,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })

    for occurrence_id in config["canonical_occurrence_ids"]:
        record = by_id[occurrence_id]
        expected = identity[occurrence_id]
        item = by_reference.get(expected["reference_period_es"])

        if item is None:
            observations.append({
                "type": "INDEC_CPI_EXPECTED_REPORT_ABSENT_FROM_CONFIGURED_MONTH_ROUTE",
                "occurrence_id": occurrence_id,
                "reference_period_es": expected["reference_period_es"],
                "month_slug": expected["month_slug"],
                "absence_is_not_cancellation_delay_completion_or_certainty_change": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            if record.get("lifecycle_status") != "COMPLETED":
                candidates.append(_candidate(
                    record,
                    None,
                    candidate_type="INDEC_CPI_EXPECTED_REPORT_ABSENT_SOURCE_MATCH_REVIEW",
                ))
            continue

        if item.route_month_slug != expected["month_slug"]:
            raise ValueError(f"INDEC CPI item route-month identity mismatch for {occurrence_id}")

        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "INDEC_CPI_COMPLETED_OCCURRENCE_CALENDAR_CORROBORATION_ONLY",
                "occurrence_id": occurrence_id,
                "observed_release_date": item.release_date,
                "observed_start_local": item.start_local,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        canonical_date = str(record.get("start_local") or "")[:10]
        canonical_time = str(record.get("start_local") or "")[11:19] if record.get("time_precision") == "MINUTE" else None
        observed_time = item.start_local[11:19]

        if item.release_date != canonical_date:
            candidate_type = "INDEC_CPI_SCHEDULE_DATE_CHANGE_REVIEW"
        elif record.get("time_precision") == "DAY":
            candidate_type = "INDEC_CPI_CLOCK_ENRICHMENT_REVIEW"
        elif canonical_time != observed_time or record.get("start_utc") != _utc_for_local(item.start_local):
            candidate_type = "INDEC_CPI_CLOCK_CHANGE_REVIEW"
        else:
            candidate_type = None

        if candidate_type is not None:
            candidates.append(_candidate(record, item, candidate_type=candidate_type))
            observations.append({
                "type": candidate_type + "_OBSERVED",
                "occurrence_id": occurrence_id,
                **_evidence(record, item),
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
        else:
            observations.append({
                "type": "INDEC_CPI_CALENDAR_EXACT_MATCH_NO_CHANGE",
                "occurrence_id": occurrence_id,
                **_evidence(record, item),
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })

    observations.append({
        "type": "INDEC_CALENDAR_MONITOR_HAS_NO_COMPLETION_CERTAINTY_OR_DIRECT_WRITE_AUTHORITY",
        "configured_occurrence_count": len(by_id),
        "observed_cpi_row_count": len(releases),
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
