from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.monitor_coverage import build_monitor_coverage_audit

CANONICAL = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
EXPECTATIONS = ROOT / "data/monitor/expectations.json"
RUNNER = ROOT / "scripts/run_live_monitor.py"
ROADMAP = ROOT / "ROADMAP.md"
PLAN = ROOT / "data/monitor/NHC_ATLANTIC_SEASON_CI_PLAN_v0.1.json"

BASE_SHA = "c4f359c2c70f023c32990f20234aaf154dced152"
SOURCE_ID = "WSSRC-RISK-002"
SERIES_ID = "WSER-RISK-ATL-HURR"
ADAPTER_ID = "NHC_ATLANTIC_SEASON"
TARGET_IDS = ["WSO-COM-A-0049", "WSO-COM-A-0050"]
SEMANTIC_SHA = "1295e095eed4a6210eb837fe4fd606a81cf37f19e709075ab6061d9f95c98511"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_by_id(sources: dict) -> dict:
    rows = [row for row in sources.get("sources", []) if row.get("source_id") == SOURCE_ID]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one {SOURCE_ID}, found {len(rows)}")
    return rows[0]


def assert_prestate(canonical: dict, sources: dict, expectations: dict) -> None:
    plan = load(PLAN)
    if plan.get("exact_base_sha") != BASE_SHA:
        raise RuntimeError("CI plan exact base drift")
    if (canonical.get("version"), len(canonical.get("records", []))) != ("0.41", 689):
        raise RuntimeError("CI requires Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != ("2.02", 257):
        raise RuntimeError("CI requires Sources v2.02 / 257")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != ("0.27", 25):
        raise RuntimeError("CI requires Monitor v0.27 / 25")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("NHC route is already registered")

    source = source_by_id(sources)
    expected_source = {
        "authoritative_url": "https://www.nhc.noaa.gov/climo/",
        "canonical_dependency_count": 2,
        "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "verification_mode": "MANUAL_AUTHORITATIVE_RECHECK",
        "monitoring_readiness_status": "ENDPOINT_REVIEW_REQUIRED",
        "automated_retrieval_permission": "PENDING",
    }
    for key, value in expected_source.items():
        if source.get(key) != value:
            raise RuntimeError(f"NHC source prestate drift {key}: {source.get(key)!r}")

    by_id = {row.get("occurrence_id"): row for row in canonical.get("records", [])}
    for oid in TARGET_IDS:
        row = by_id.get(oid)
        if row is None:
            raise RuntimeError(f"missing NHC target {oid}")
        expected = {
            "series_id": SERIES_ID,
            "source_id": SOURCE_ID,
            "category": "PHYSICAL_CLIMATE_RISK",
            "event_type": "PHYSICAL_RISK_WINDOW",
            "jurisdiction": "Atlantic basin",
            "region": "Cross-regional / Global",
            "timing_type": "ALL_DAY_RANGE",
            "time_precision": "DAY",
            "time_status": "CONFIRMED",
            "certainty_status": "CONFIRMED",
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise RuntimeError(f"NHC target {oid} drift {key}: {row.get(key)!r}")
    if by_id[TARGET_IDS[0]].get("start_local") != "2026-06-01" or by_id[TARGET_IDS[0]].get("end_local") != "2026-11-30":
        raise RuntimeError("2026 NHC season boundary drifted")
    if by_id[TARGET_IDS[1]].get("start_local") != "2027-06-01" or by_id[TARGET_IDS[1]].get("end_local") != "2027-11-30":
        raise RuntimeError("2027 NHC season boundary drifted")


def _validated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def transform_sources(sources: dict) -> dict:
    out = deepcopy(sources)
    out["version"] = "2.03"
    out["reference_date"] = "2026-09-10"
    source = source_by_id(out)
    source.update({
        "automated_monitoring_use": "CLEARED",
        "automated_monitoring_scope": "NHC_ATLANTIC_SEASON_DEFINITION_AND_OUTLOOK_HEALTH_READ_ONLY_SENTINEL_ONLY",
        "automated_retrieval_permission": "CLEARED_BOUNDED_PUBLIC_DOMAIN_LOW_RATE_NHC_ENDPOINTS",
        "verification_mode": "AUTOMATED_PILOT",
        "monitoring_readiness_status": "PILOT_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_activation_status": "PILOT_READ_ONLY_SEASON_DEFINITION_SENTINEL_NO_AUTO_COMMIT",
        "live_adapter_id": ADAPTER_ID,
        "monitor_parser_type": "HTML_SEASON_DEFINITION_PLUS_RSS_HEALTH_SENTINEL",
        "monitor_parser_version": "nhc-atlantic-season-0.1",
        "monitor_route_validated_at": _validated_at(),
        "monitor_route_validation_run_id": int(os.getenv("GITHUB_RUN_ID", "0") or 0),
        "monitor_route_baseline_sha256": SEMANTIC_SHA,
        "rights_reviewed_at": "2026-09-10",
        "rights_review_scope": "CI_BOUNDED_NHC_PUBLIC_DOMAIN_AND_APPROPRIATE_USE_RECHECK",
        "rights_review_note": "Operational WORLD SIGNALS classification, not a legal opinion. Clearance is limited to two low-rate first-party NHC endpoint requests per daily monitor run.",
        "monitor_route_scope_note": "Read-only NHC Atlantic season-definition semantic sentinel plus Atlantic outlook RSS health corroboration. RSS activity, storm activity, source absence and elapsed season time have no schedule, lifecycle, certainty or completion authority.",
    })
    return out


def transform_expectations(expectations: dict) -> dict:
    out = deepcopy(expectations)
    out["version"] = "0.28"
    out["adapters"].append({
        "adapter_id": ADAPTER_ID,
        "source_id": SOURCE_ID,
        "canonical_occurrence_ids": TARGET_IDS,
        "monitor_role": "PHYSICAL_RISK_WINDOW_SEASON_DEFINITION_SENTINEL",
        "cadence": "DAILY",
        "endpoint": {
            "climatology_url": "https://www.nhc.noaa.gov/climo/",
            "atlantic_outlook_rss_url": "https://www.nhc.noaa.gov/xml/TWOAT.xml",
            "robots_url": "https://www.nhc.noaa.gov/robots.txt",
            "request_budget_per_run": 2
        },
        "baseline": {
            "authority_surface": "NHC_TROPICAL_CYCLONE_CLIMATOLOGY",
            "start_month_day": "06-01",
            "end_month_day": "11-30",
            "semantic_sha256": SEMANTIC_SHA
        },
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "semantic_change_policy": "GENERATE_REVIEW_CANDIDATE_REQUIRE_AUTHORITATIVE_NHC_REVERIFICATION",
        "rss_activity_policy": "SOURCE_HEALTH_CORROBORATION_ONLY_NO_SEASON_DATE_OR_EVENT_STATE_SEMANTICS",
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "canonical_date_mutation_allowed": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False
    })
    return out


def patch_runner(text: str) -> str:
    if 'if "NHC_ATLANTIC_SEASON" in configs:' in text:
        raise RuntimeError("NHC runtime handler already present")
    fetch_marker = "    fetch_nass_asb_ical,\n"
    if text.count(fetch_marker) != 1:
        raise RuntimeError("NHC runner fetch import insertion marker drift")
    text = text.replace(
        fetch_marker,
        fetch_marker + "    fetch_nhc_atlantic_climatology,\n    fetch_nhc_atlantic_outlook_health,\n",
        1,
    )
    monitor_marker = "from world_signals.nass_asb_monitor import nass_asb_ical_review_candidates\n"
    if text.count(monitor_marker) != 1:
        raise RuntimeError("NHC runner comparator import insertion marker drift")
    text = text.replace(
        monitor_marker,
        monitor_marker + "from world_signals.nhc_atlantic_season_monitor import nhc_atlantic_season_review_candidates\n",
        1,
    )
    handler_marker = '    if "HMT_T1_CONTENT_API" in configs:\n'
    if text.count(handler_marker) != 1:
        raise RuntimeError("NHC runner handler insertion marker drift")
    handler = '''    if "NHC_ATLANTIC_SEASON" in configs:\n        nhc_config=configs["NHC_ATLANTIC_SEASON"]\n        try:\n            nhc_definition,nhc_climo_snap=fetch_nhc_atlantic_climatology()\n            nhc_rss_snap=fetch_nhc_atlantic_outlook_health()\n            report["source_health"].append({\n                "adapter_id":"NHC_ATLANTIC_SEASON",\n                "source_id":nhc_config["source_id"],\n                "state":"HEALTHY",\n                "climatology_snapshot":nhc_climo_snap.as_dict(),\n                "atlantic_outlook_rss_snapshot":nhc_rss_snap.as_dict(),\n                "definition":nhc_definition.as_dict(),\n                "request_budget_per_run":2,\n                "climatology_request_count":1,\n                "rss_health_request_count":1,\n                "followup_request_count":0,\n                "rss_has_season_date_authority":False,\n                "storm_activity_has_event_state_authority":False,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "canonical_date_mutation_allowed":False,\n                "automatic_new_occurrence_creation_allowed":False,\n                "automatic_live_or_analysis_promotion_allowed":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=nhc_atlantic_season_review_candidates(\n                registry.get("records",[]),nhc_definition,nhc_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"NHC_ATLANTIC_SEASON",\n                "source_id":nhc_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "rss_absence_is_not_event_state":True,\n                "storm_activity_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "certainty_authority":False,\n                "automatic_commit_allowed":False,\n            })\n\n'''
    return text.replace(handler_marker, handler + handler_marker, 1)


def patch_roadmap(text: str) -> str:
    old = "## Stage 8 — recovery/status truth surfaces — CH IMPLEMENTING"
    new = "## Stage 8 — recovery/status truth surfaces — DONE / GUARDED"
    if old not in text:
        if new not in text:
            raise RuntimeError("Stage 8 roadmap marker drift")
    else:
        text = text.replace(old, new, 1)
    old9 = "## Stage 9 — next pressure selection — RECOMPUTE AFTER CH"
    new9 = "## Stage 9 — next pressure selection — CI NHC ACTIVATION SELECTED"
    if old9 not in text:
        if new9 not in text:
            raise RuntimeError("Stage 9 roadmap marker drift")
    else:
        text = text.replace(old9, new9, 1)
    return text


def build_poststate(canonical: dict, sources: dict, expectations: dict, runner_text: str, roadmap_text: str):
    new_sources = transform_sources(sources)
    new_expectations = transform_expectations(expectations)
    new_runner = patch_runner(runner_text)
    new_roadmap = patch_roadmap(roadmap_text)

    pre_audit = build_monitor_coverage_audit(canonical, sources, expectations)
    post_audit = build_monitor_coverage_audit(canonical, new_sources, new_expectations)
    pre = pre_audit["totals"]
    post = post_audit["totals"]
    if post["configured_adapter_count"] != pre["configured_adapter_count"] + 1:
        raise RuntimeError(f"CI adapter delta mismatch: {pre} -> {post}")
    if post["unique_monitor_source_count"] != pre["unique_monitor_source_count"] + 1:
        raise RuntimeError(f"CI unique-source delta mismatch: {pre} -> {post}")
    if post["scoped_occurrence_count"] != pre["scoped_occurrence_count"] + 2:
        raise RuntimeError(f"CI occurrence-scope delta mismatch: {pre} -> {post}")
    target = next(row for row in post_audit["adapter_inventory"] if row["adapter_id"] == ADAPTER_ID)
    if target["categories"] != ["PHYSICAL_CLIMATE_RISK"]:
        raise RuntimeError(f"CI NHC category projection mismatch: {target}")
    return new_sources, new_expectations, new_runner, new_roadmap, pre, post


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        raise RuntimeError("choose exactly one of --check or --apply")

    canonical = load(CANONICAL)
    sources = load(SOURCES)
    expectations = load(EXPECTATIONS)
    runner_text = RUNNER.read_text(encoding="utf-8")
    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    assert_prestate(canonical, sources, expectations)
    new_sources, new_expectations, new_runner, new_roadmap, pre, post = build_poststate(
        canonical, sources, expectations, runner_text, roadmap_text
    )

    result = {
        "status": "CI_SIMULATION_VALID" if args.check else "CI_READY_TO_APPLY",
        "exact_base_sha": BASE_SHA,
        "source_prestate": [sources.get("version"), len(sources.get("sources", []))],
        "source_poststate": [new_sources.get("version"), len(new_sources.get("sources", []))],
        "monitor_prestate": [expectations.get("version"), len(expectations.get("adapters", []))],
        "monitor_poststate": [new_expectations.get("version"), len(new_expectations.get("adapters", []))],
        "coverage_prestate": pre,
        "coverage_poststate": post,
        "canonical_mutation": "NONE",
        "live_mutation": "NONE",
        "analysis_mutation": "NONE",
        "automatic_commit_allowed": False,
        "google_calendar_write": False,
    }
    if args.check:
        print(json.dumps(result, indent=2))
        return 0

    if os.getenv("WORLD_SIGNALS_APPLY_MONITOR_CI") != "YES":
        raise RuntimeError("write gate closed: set WORLD_SIGNALS_APPLY_MONITOR_CI=YES")
    write_json(SOURCES, new_sources)
    write_json(EXPECTATIONS, new_expectations)
    RUNNER.write_text(new_runner, encoding="utf-8")
    ROADMAP.write_text(new_roadmap, encoding="utf-8")
    result["status"] = "CI_MATERIALIZED_BOUNDED_NHC_MONITOR"
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
