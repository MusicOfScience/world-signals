from __future__ import annotations

from hashlib import sha256
import json

from .adapters.fao_release_calendar import FAOReleaseSlot, FAO_TIMEZONE

FAO_SOURCE_ID = "WSSRC-COM-010"
FAO_REGION = "Cross-regional / Global"


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _identity_map(config: dict) -> dict[str, dict]:
    raw = config.get("identity_by_occurrence_id")
    if not isinstance(raw, dict) or len(raw) != 6:
        raise ValueError("FAO release identity map must contain exactly six occurrences")
    out: dict[str, dict] = {}
    seen: set[tuple[str, str]] = set()
    for occurrence_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"FAO release identity config must be an object for {occurrence_id}")
        product_key = value.get("product_key")
        slot_month = value.get("slot_month")
        series_id = value.get("series_id")
        if not all(isinstance(v, str) and v for v in (product_key, slot_month, series_id)):
            raise ValueError(f"FAO release identity config incomplete for {occurrence_id}")
        if product_key not in {"FFPI", "AMIS"}:
            raise ValueError(f"unsupported FAO product identity {product_key!r}")
        key = (slot_month, product_key)
        if key in seen:
            raise ValueError(f"duplicate FAO configured slot identity: {key!r}")
        seen.add(key)
        out[occurrence_id] = {
            "product_key": product_key,
            "slot_month": slot_month,
            "series_id": series_id,
        }
    return out


def _configured_scope(records: list[dict], config: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 6 or len(set(configured)) != 6:
        raise ValueError("FAO release configured scope must contain exactly six unique occurrence IDs")
    identity = _identity_map(config)
    if set(identity) != set(configured):
        raise ValueError("FAO release identity map must exactly match configured occurrence IDs")

    gate_checks = {
        "source_id": FAO_SOURCE_ID,
        "canonical_schedule_source_id": FAO_SOURCE_ID,
        "request_budget_per_run": 2,
        "robots_requests_per_run": 1,
        "calendar_requests_per_run": 1,
        "followup_requests_per_run": 0,
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_clock_mutation_allowed": False,
        "automatic_amis_followup_allowed": False,
        "automatic_faostat_followup_allowed": False,
        "automatic_pdf_fetch_allowed": False,
        "automatic_news_followup_allowed": False,
        "automatic_search_route_discovery_allowed": False,
        "automatic_commit_allowed": False,
    }
    for key, expected in gate_checks.items():
        if config.get(key) != expected:
            raise ValueError(f"FAO release monitor gate drift for {key}: {config.get(key)!r}")

    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in set(configured)}
    if set(by_id) != set(configured):
        raise ValueError("FAO configured occurrence missing from Canonical")

    for occurrence_id in configured:
        row = by_id[occurrence_id]
        expected = identity[occurrence_id]
        checks = {
            "series_id": expected["series_id"],
            "source_id": FAO_SOURCE_ID,
            "region": FAO_REGION,
            "source_timezone": FAO_TIMEZONE,
            "time_precision": "DAY",
            "timing_type": "CIVIL_DATE",
            "all_day_semantics": True,
        }
        for key, value in checks.items():
            if row.get(key) != value:
                raise ValueError(f"FAO Canonical scope drift for {occurrence_id} {key}: {row.get(key)!r}")
        if row.get("start_utc") is not None:
            raise ValueError(f"FAO date-only occurrence unexpectedly has UTC clock: {occurrence_id}")
        if not isinstance(row.get("start_local"), str) or len(row["start_local"]) != 10:
            raise ValueError(f"FAO configured occurrence must remain an exact civil date: {occurrence_id}")
    return by_id, identity


def _evidence(record: dict, item: FAOReleaseSlot) -> dict:
    return {
        "product_key": item.product_key,
        "product_label": item.product_label,
        "slot_month": item.slot_month,
        "observed_release_date": item.release_date,
        "source_timezone": item.source_timezone,
        "observed_time_precision": item.time_precision,
        "clock_exposed": False,
        "canonical_release_date": record.get("start_local"),
        "canonical_time_precision": record.get("time_precision"),
        "canonical_source_id": record.get("source_id"),
    }


def _candidate(record: dict, item: FAOReleaseSlot | None, *, candidate_type: str, identity: dict) -> dict:
    evidence = None if item is None else _evidence(record, item)
    digest = _stable_hash({
        "candidate_type": candidate_type,
        "occurrence_id": record["occurrence_id"],
        "identity": identity,
        "evidence": evidence,
    })
    return {
        "candidate_id": "WSRC-FAO-" + digest[:16],
        "candidate_type": candidate_type,
        "source_id": FAO_SOURCE_ID,
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
        "configured_identity": identity,
        "review_state": "PENDING_AUTHORITATIVE_FAO_CALENDAR_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "absence_is_not_cancellation_completion_or_certainty_change": item is None,
        "automatic_commit_allowed": False,
        "canonical_clock_mutation_allowed": False,
        "lifecycle_mutation_allowed": False,
        "certainty_mutation_allowed": False,
    }


def fao_release_calendar_review_candidates(
    records: list[dict],
    releases: list[FAOReleaseSlot],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id, identity = _configured_scope(records, config)
    observed: dict[tuple[str, str], FAOReleaseSlot] = {}
    for item in releases:
        key = (item.slot_month, item.product_key)
        if key in observed:
            raise ValueError(f"multiple FAO rows map to configured slot identity {key!r}")
        observed[key] = item

    candidates: list[dict] = []
    observations: list[dict] = []

    for occurrence_id in config["canonical_occurrence_ids"]:
        record = by_id[occurrence_id]
        expected = identity[occurrence_id]
        key = (expected["slot_month"], expected["product_key"])
        item = observed.get(key)

        if item is None:
            observations.append({
                "type": "FAO_RELEASE_CONFIGURED_SLOT_ABSENT",
                "occurrence_id": occurrence_id,
                "product_key": expected["product_key"],
                "slot_month": expected["slot_month"],
                "absence_is_not_cancellation_completion_or_certainty_change": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            if record.get("lifecycle_status") != "COMPLETED":
                candidates.append(
                    _candidate(
                        record,
                        None,
                        candidate_type="FAO_RELEASE_SLOT_MISSING_REVIEW",
                        identity=expected,
                    )
                )
            continue

        if record.get("lifecycle_status") == "COMPLETED":
            observations.append({
                "type": "FAO_RELEASE_COMPLETED_OCCURRENCE_CALENDAR_CORROBORATION_ONLY",
                "occurrence_id": occurrence_id,
                **_evidence(record, item),
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        canonical_date = record["start_local"]
        if item.release_date != canonical_date:
            candidates.append(
                _candidate(
                    record,
                    item,
                    candidate_type="FAO_RELEASE_DATE_CHANGE_REVIEW",
                    identity=expected,
                )
            )
            observation_type = "FAO_RELEASE_DATE_CHANGE_REVIEW_OBSERVED"
        else:
            observation_type = "FAO_RELEASE_DATE_MATCH_OBSERVATION"

        observations.append({
            "type": observation_type,
            "occurrence_id": occurrence_id,
            **_evidence(record, item),
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
        })

    configured_keys = {(v["slot_month"], v["product_key"]) for v in identity.values()}
    unexpected = sorted(set(observed) - configured_keys)
    if unexpected:
        raise ValueError(f"FAO parser returned rows outside configured monitor scope: {unexpected!r}")

    observations.append({
        "type": "FAO_RELEASE_CALENDAR_HAS_NO_COMPLETION_CERTAINTY_CLOCK_OR_DIRECT_WRITE_AUTHORITY",
        "configured_occurrence_count": len(by_id),
        "observed_release_row_count": len(releases),
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
