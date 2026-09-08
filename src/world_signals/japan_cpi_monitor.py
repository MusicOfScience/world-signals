from __future__ import annotations

from hashlib import sha256
import json

from .adapters.japan_cpi_schedule import JAPAN_CPI_TIMEZONE, JapanCPIReleaseRow

JAPAN_CPI_SOURCE_ID = "WSSRC-MAC-014"
JAPAN_CPI_SERIES_ID = "WSER-MAC-JP-CPI"
JAPAN_CPI_REGION = "East Asia"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _identity_map(config: dict) -> dict[str, dict]:
    raw = config.get("identity_by_occurrence_id")
    if not isinstance(raw, dict) or len(raw) != 7:
        raise ValueError("Japan CPI identity map must contain exactly seven occurrences")
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 7 or len(set(configured)) != 7 or set(configured) != set(raw):
        raise ValueError("Japan CPI configured occurrence IDs and identity map must match exactly")

    out: dict[str, dict] = {}
    seen_periods: set[str] = set()
    for occurrence_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"Japan CPI identity config must be an object for {occurrence_id}")
        reference_period = value.get("reference_period")
        series_id = value.get("series_id")
        if not isinstance(reference_period, str) or not reference_period:
            raise ValueError(f"Japan CPI reference period missing for {occurrence_id}")
        if series_id != JAPAN_CPI_SERIES_ID:
            raise ValueError(f"Japan CPI series identity drift for {occurrence_id}: {series_id!r}")
        if reference_period in seen_periods:
            raise ValueError(f"duplicate configured Japan CPI reference period: {reference_period}")
        seen_periods.add(reference_period)
        out[occurrence_id] = {
            "reference_period": reference_period,
            "series_id": series_id,
        }
    return out


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    identity = _identity_map(config)
    gate_checks = {
        "source_id": JAPAN_CPI_SOURCE_ID,
        "canonical_schedule_source_id": JAPAN_CPI_SOURCE_ID,
        "request_budget_per_run": 2,
        "robots_requests_per_run": 1,
        "schedule_requests_per_run": 1,
        "followup_requests_per_run": 0,
        "schedule_mutation_authority": False,
        "clock_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_tokyo_cpi_followup_allowed": False,
        "automatic_estat_api_followup_allowed": False,
        "automatic_data_release_followup_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_news_followup_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gate_checks.items():
        if config.get(key) != expected:
            raise ValueError(f"Japan CPI monitor gate drift for {key}: {config.get(key)!r}")

    configured = set(identity)
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in configured}
    if set(by_id) != configured:
        raise ValueError("Japan CPI configured occurrence missing from Canonical")

    for occurrence_id, expected in identity.items():
        row = by_id[occurrence_id]
        checks = {
            "series_id": expected["series_id"],
            "source_id": JAPAN_CPI_SOURCE_ID,
            "region": JAPAN_CPI_REGION,
            "source_timezone": JAPAN_CPI_TIMEZONE,
            "time_precision": "MINUTE",
            "time_basis": "EXPLICIT_OCCURRENCE_TIME",
            "timing_type": "LOCAL_DATETIME",
            "reference_period": expected["reference_period"],
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise ValueError(
                    f"Japan CPI Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}"
                )
        start_local = row.get("start_local")
        start_utc = row.get("start_utc")
        if not isinstance(start_local, str) or len(start_local) < 19 or "T" not in start_local:
            raise ValueError(f"Japan CPI Canonical start_local must remain a local datetime: {occurrence_id}")
        if not isinstance(start_utc, str) or not start_utc.endswith("Z"):
            raise ValueError(f"Japan CPI Canonical start_utc must remain explicit: {occurrence_id}")
        if row.get("all_day_semantics") is True:
            raise ValueError(f"Japan CPI occurrence unexpectedly became all-day: {occurrence_id}")
    return by_id, identity


def _evidence(record: dict, item: JapanCPIReleaseRow) -> dict:
    return {
        "reference_period": item.reference_period,
        "survey_month_label": item.survey_month_label,
        "observed_release_date": item.release_date,
        "source_timezone": item.source_timezone,
        "observed_time_precision": item.time_precision,
        "clock_exposed_by_schedule": item.clock_exposed_by_schedule,
        "canonical_release_date": record["start_local"][:10],
        "canonical_start_local_preserved": record.get("start_local"),
        "canonical_start_utc_preserved": record.get("start_utc"),
        "canonical_time_precision_preserved": record.get("time_precision"),
        "canonical_time_basis_preserved": record.get("time_basis"),
        "canonical_timing_type_preserved": record.get("timing_type"),
        "canonical_source_id": record.get("source_id"),
    }


def _candidate(
    record: dict,
    item: JapanCPIReleaseRow | None,
    *,
    candidate_type: str,
    identity: dict,
) -> dict:
    evidence = None if item is None else _evidence(record, item)
    digest = _stable_hash({
        "candidate_type": candidate_type,
        "occurrence_id": record["occurrence_id"],
        "identity": identity,
        "evidence": evidence,
    })
    return {
        "candidate_id": "WSRC-JPCPI-" + digest[:16],
        "candidate_type": candidate_type,
        "source_id": JAPAN_CPI_SOURCE_ID,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "start_local": record.get("start_local"),
            "start_utc": record.get("start_utc"),
            "time_precision": record.get("time_precision"),
            "time_basis": record.get("time_basis"),
            "timing_type": record.get("timing_type"),
            "lifecycle_status": record.get("lifecycle_status"),
            "certainty_status": record.get("certainty_status"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": evidence,
        "configured_identity": identity,
        "review_state": "PENDING_AUTHORITATIVE_JAPAN_CPI_SCHEDULE_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "absence_is_not_cancellation_completion_delay_or_certainty_change": item is None,
        "schedule_mutation_authority": False,
        "automatic_commit_allowed": False,
        "canonical_clock_mutation_allowed": False,
        "lifecycle_mutation_allowed": False,
        "certainty_mutation_allowed": False,
    }


def japan_cpi_schedule_review_candidates(
    records: list[dict],
    releases: list[JapanCPIReleaseRow],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id, identity = _configured_scope(records, config)

    observed: dict[str, JapanCPIReleaseRow] = {}
    for item in releases:
        if item.reference_period in observed:
            raise ValueError(f"duplicate Japan CPI observed reference period: {item.reference_period}")
        observed[item.reference_period] = item

    configured_periods = {value["reference_period"] for value in identity.values()}
    candidates: list[dict] = []
    observations: list[dict] = []

    for occurrence_id in config["canonical_occurrence_ids"]:
        record = by_id[occurrence_id]
        expected = identity[occurrence_id]
        item = observed.get(expected["reference_period"])

        if item is None:
            observations.append({
                "type": "JAPAN_CPI_RELEASE_CONFIGURED_ROW_ABSENT",
                "occurrence_id": occurrence_id,
                "reference_period": expected["reference_period"],
                "absence_is_not_cancellation_completion_delay_or_certainty_change": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            if record.get("lifecycle_status") != "COMPLETED":
                candidates.append(
                    _candidate(
                        record,
                        None,
                        candidate_type="JAPAN_CPI_RELEASE_ROW_MISSING_REVIEW",
                        identity=expected,
                    )
                )
            continue

        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "JAPAN_CPI_COMPLETED_OCCURRENCE_SCHEDULE_CORROBORATION_ONLY",
                "occurrence_id": occurrence_id,
                **_evidence(record, item),
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        canonical_date = record["start_local"][:10]
        if item.release_date != canonical_date:
            candidates.append(
                _candidate(
                    record,
                    item,
                    candidate_type="JAPAN_CPI_RELEASE_DATE_CHANGE_REVIEW",
                    identity=expected,
                )
            )
            observation_type = "JAPAN_CPI_RELEASE_DATE_CHANGE_REVIEW_OBSERVED"
        else:
            observation_type = "JAPAN_CPI_RELEASE_DATE_MATCH_OBSERVATION"

        observations.append({
            "type": observation_type,
            "occurrence_id": occurrence_id,
            **_evidence(record, item),
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    outside_scope = sorted(set(observed) - configured_periods)
    observations.append({
        "type": "JAPAN_CPI_OUTSIDE_CONFIGURED_REFERENCE_PERIOD_OBSERVATION",
        "outside_configured_reference_period_count": len(outside_scope),
        "outside_configured_reference_periods": outside_scope,
        "automatic_canonical_addition_allowed": False,
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    observations.append({
        "type": "JAPAN_CPI_SCHEDULE_HAS_NO_CLOCK_LIFECYCLE_CERTAINTY_OR_DIRECT_WRITE_AUTHORITY",
        "configured_occurrence_count": len(by_id),
        "observed_national_schedule_row_count": len(releases),
        "clock_rule_is_separate_from_schedule": True,
        "schedule_mutation_authority": False,
        "canonical_clock_mutation_allowed": False,
        "lifecycle_mutation_allowed": False,
        "certainty_mutation_allowed": False,
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
