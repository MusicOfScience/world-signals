from __future__ import annotations

from hashlib import sha256
import json

from .adapters.nhc_atlantic_season import NHCAtlanticSeasonDefinition


SOURCE_ID = "WSSRC-RISK-002"
SERIES_ID = "WSER-RISK-ATL-HURR"
CATEGORY = "PHYSICAL_CLIMATE_RISK"
EVENT_TYPE = "PHYSICAL_RISK_WINDOW"
TARGET_IDS = ("WSO-COM-A-0049", "WSO-COM-A-0050")


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _scope(records: list[dict], config: dict) -> list[dict]:
    ids = tuple(config.get("canonical_occurrence_ids") or [])
    if ids != TARGET_IDS:
        raise ValueError("NHC Atlantic season monitor requires the exact ordered two-occurrence allow-list")
    if config.get("source_id") != SOURCE_ID:
        raise ValueError("NHC Atlantic season monitor source identity drift")
    for gate in (
        "schedule_authority",
        "lifecycle_authority",
        "certainty_authority",
        "automatic_new_occurrence_creation_allowed",
        "automatic_live_or_analysis_promotion_allowed",
        "automatic_commit_allowed",
    ):
        if config.get(gate) is not False:
            raise ValueError(f"NHC Atlantic season write/authority gate drift: {gate}")
    by_id = {row.get("occurrence_id"): row for row in records if row.get("occurrence_id") in set(ids)}
    if set(by_id) != set(ids):
        raise ValueError("NHC Atlantic season configured occurrence missing from Canonical")
    rows = [by_id[oid] for oid in ids]
    for row in rows:
        checks = {
            "series_id": SERIES_ID,
            "source_id": SOURCE_ID,
            "category": CATEGORY,
            "event_type": EVENT_TYPE,
            "region": "Cross-regional / Global",
            "jurisdiction": "Atlantic basin",
            "timing_type": "ALL_DAY_RANGE",
            "time_precision": "DAY",
            "time_status": "CONFIRMED",
            "certainty_status": "CONFIRMED",
        }
        for key, expected in checks.items():
            if row.get(key) != expected:
                raise ValueError(f"NHC Atlantic Canonical scope drift for {row.get('occurrence_id')} {key}: {row.get(key)!r}")
        if not isinstance(row.get("start_local"), str) or not isinstance(row.get("end_local"), str):
            raise ValueError("NHC Atlantic season requires explicit civil-date range")
    return rows


def _mmdd(value: str) -> str:
    return value[5:10]


def nhc_atlantic_season_review_candidates(
    records: list[dict],
    definition: NHCAtlanticSeasonDefinition,
    config: dict,
) -> tuple[list[dict], list[dict]]:
    rows = _scope(records, config)
    mismatches = []
    observations = []
    for row in rows:
        canonical_start = _mmdd(row["start_local"])
        canonical_end = _mmdd(row["end_local"])
        match = (
            canonical_start == definition.start_month_day
            and canonical_end == definition.end_month_day
        )
        observations.append(
            {
                "type": "NHC_ATLANTIC_SEASON_SEMANTIC_BASELINE_CHECK",
                "occurrence_id": row["occurrence_id"],
                "canonical_start_month_day": canonical_start,
                "canonical_end_month_day": canonical_end,
                "observed_start_month_day": definition.start_month_day,
                "observed_end_month_day": definition.end_month_day,
                "semantic_match": match,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            }
        )
        if not match:
            mismatches.append(
                {
                    "occurrence_id": row["occurrence_id"],
                    "canonical_start_month_day": canonical_start,
                    "canonical_end_month_day": canonical_end,
                }
            )

    candidates = []
    if mismatches:
        evidence = {
            "source_id": SOURCE_ID,
            "authority_surface": definition.authority_surface,
            "semantic_sha256": definition.semantic_sha256,
            "observed_start_month_day": definition.start_month_day,
            "observed_end_month_day": definition.end_month_day,
            "canonical_mismatches": mismatches,
        }
        digest = _stable_hash(evidence)
        candidates.append(
            {
                "candidate_id": "WSRC-NHC-ATL-SEASON-" + digest[:16],
                "candidate_type": "NHC_ATLANTIC_SEASON_DEFINITION_DRIFT_REVIEW",
                "source_id": SOURCE_ID,
                "occurrence_ids": [row["occurrence_id"] for row in rows],
                "old_value": {
                    row["occurrence_id"]: {
                        "start_local": row["start_local"],
                        "end_local": row["end_local"],
                    }
                    for row in rows
                },
                "new_value": evidence,
                "review_state": "PENDING_AUTHORITATIVE_NHC_SEASON_DEFINITION_REVIEW",
                "candidate_origin": "LIVE_READ_ONLY_MONITOR",
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
                "canonical_date_mutation_allowed": False,
                "rss_activity_is_date_authority": False,
            }
        )

    observations.append(
        {
            "type": "NHC_RSS_AND_STORM_ACTIVITY_HAVE_NO_SEASON_DATE_SEMANTICS",
            "configured_occurrence_count": len(rows),
            "event_state_inference": "NONE",
            "automatic_commit_allowed": False,
            "rss_absence_is_not_cancellation_or_date_change": True,
        }
    )
    return candidates, observations
