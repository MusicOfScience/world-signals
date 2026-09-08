from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/monitor/FED_MONETARY_RSS_MONITOR_BP_PLAN_v0.1.json"
CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BP"
NEW_SOURCE_ID = "WSSRC-CB-015"
CANONICAL_SCHEDULE_SOURCE_ID = "WSSRC-CB-001"
ADAPTER_ID = "FED_MONETARY_POLICY_RSS"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    rows = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(rows)}")
    return rows[0]


def preflight(canonical: dict, sources: dict, expectations: dict, plan: dict) -> None:
    p = plan["preconditions"]
    if plan.get("exact_base_main_sha") != "edc800a694370b66d4c5c6d0a465fb3e5e554218":
        raise RuntimeError("BP plan is not frozen to the exact post-BO main SHA")
    if (canonical.get("version"), len(canonical.get("records", []))) != (
        p["canonical_registry_version"], p["canonical_record_count"]
    ):
        raise RuntimeError("BP requires exact Canonical v0.41 / 689")
    if (sources.get("version"), len(sources.get("sources", []))) != (
        p["source_registry_version"], p["source_count"]
    ):
        raise RuntimeError("BP requires exact Sources v1.88 / 247")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != (
        p["monitor_expectations_version"], p["configured_monitor_adapter_count"]
    ):
        raise RuntimeError("BP requires exact Monitor v0.13 / 11")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit gate must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate must remain closed")
    if any(row.get("source_id") == NEW_SOURCE_ID for row in sources.get("sources", [])):
        raise RuntimeError("BP machine RSS source already exists")
    if any(row.get("adapter_id") == ADAPTER_ID for row in expectations.get("adapters", [])):
        raise RuntimeError("BP Fed monetary RSS route already exists")

    schedule = source_by_id(sources, CANONICAL_SCHEDULE_SOURCE_ID)
    expected_schedule_fields = {
        "canonical_dependency_count": 44,
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        "verification_mode": "AUTOMATED_PILOT",
        "monitoring_activation_status": "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE",
        "source_timezone": "America/New_York",
    }
    for key, expected in expected_schedule_fields.items():
        if schedule.get(key) != expected:
            raise RuntimeError(f"BP FOMC schedule source pre-state drifted for {key}: {schedule.get(key)!r}")

    tracked = list(plan["tracked_publications"])
    ids = [row["occurrence_id"] for row in tracked]
    if len(ids) != 22 or len(ids) != len(set(ids)):
        raise RuntimeError("BP requires exact unique 22-occurrence publication allow-list")
    actual = [row for row in canonical.get("records", []) if row.get("occurrence_id") in set(ids)]
    by_id = {row["occurrence_id"]: row for row in actual}
    if set(by_id) != set(ids):
        raise RuntimeError("BP publication allow-list no longer matches Canonical")
    counts = {"WS.CB.FED.FOMC_POLICY_DECISION": 0, "WS.CB.FED.FOMC_MINUTES": 0}
    for expected in tracked:
        row = by_id[expected["occurrence_id"]]
        if row.get("series_id") != expected["series_id"]:
            raise RuntimeError(f"BP FOMC series drift for {expected['occurrence_id']}")
        if row.get("start_local") != expected["canonical_start_local"]:
            raise RuntimeError(f"BP FOMC timestamp drift for {expected['occurrence_id']}")
        if row.get("source_id") != CANONICAL_SCHEDULE_SOURCE_ID:
            raise RuntimeError(f"BP FOMC Canonical source drift for {expected['occurrence_id']}")
        if row.get("source_timezone") != "America/New_York" or row.get("time_precision") != "MINUTE":
            raise RuntimeError(f"BP FOMC temporal semantics drift for {expected['occurrence_id']}")
        counts[row["series_id"]] += 1
    if counts != {"WS.CB.FED.FOMC_POLICY_DECISION": 11, "WS.CB.FED.FOMC_MINUTES": 11}:
        raise RuntimeError(f"BP FOMC publication series counts drifted: {counts}")


def new_machine_source(plan: dict) -> dict:
    interface = plan["machine_interface"]
    evidence = plan["read_only_diagnostic"]
    return {
        "source_id": NEW_SOURCE_ID,
        "institution": "Board of Governors of the Federal Reserve System",
        "jurisdiction": "United States",
        "domain": "monetary_policy",
        "endpoint_role": "Monetary Policy RSS statement/minutes publication sentinel",
        "authoritative_url": interface["feed_url"],
        "source_type": "official_rss_feed",
        "information_supplied": (
            "Official Federal Reserve monetary-policy publication items and timezone-aware publication timestamps. "
            "This source is publication evidence only and is not FOMC schedule authority."
        ),
        "future_schedule_horizon": "not a schedule source; finite rolling publication feed",
        "typical_advance_notice": "not applicable; publication sentinel",
        "machine_readable_available": "RSS 2.0 XML",
        "source_timezone": "UTC",
        "recommended_verification_cadence": "daily; one dedicated feed request per run",
        "activation_status": "ACTIVE_GUARDED",
        "parser_type": "FED_MONETARY_POLICY_RSS_PUBLICATION_SENTINEL",
        "parser_version": "fed-monetary-rss-0.1",
        "known_limitations": [
            "The RSS feed is a publication interface, not FOMC forward schedule authority.",
            "The feed is finite and rolling; absence cannot imply cancellation, delay, completion or certainty change.",
            "Only the exact FOMC statement form and FOMC minutes title form are classified by BP; other FOMC-related items are observation-only.",
            "A matched publication creates a review candidate but does not automatically mark the Canonical occurrence COMPLETED.",
            "Meeting windows and press conferences are outside this route.",
            "WSSRC-CB-001 remains the Canonical schedule source and retains its separate HTML endpoint-permission hold.",
            "Third-party material, seals, logos and linked content are outside the BP public-domain clearance."
        ],
        "backup_source": None,
        "notes": "Separate machine-interface identity created to preserve schedule-source and publication-sentinel roles.",
        "timezone_scope": "FEED_NATIVE_UTC_PUBLICATION_TIMESTAMP_MATCHED_TO_AMERICA_NEW_YORK_CANONICAL_TIME",
        "licence_constraints": "BOARD_PRODUCED_PUBLIC_DOMAIN_CONTENT_EXCLUDES_THIRD_PARTY_MATERIAL_AND_MARKS",
        "ingestion_permission": "OFFICIAL_RSS_MACHINE_PUBLICATION_METADATA_ALLOWED",
        "licence_review_status": "CLEARED_PUBLIC_DOMAIN_BOARD_CONTENT_AND_OFFICIAL_RSS_MACHINE_INTERFACE",
        "automated_retrieval_permission": "OFFICIAL_RSS_SUBSCRIPTION_INTERFACE_EXPLICIT_SOFTWARE_USE",
        "redistribution_permission": "BOARD_PRODUCED_PUBLIC_DOMAIN_CONTENT_WITH_BOARD_CITATION_REQUESTED",
        "rights_evidence_url": interface["rights_evidence_url"],
        "rights_summary": (
            "Federal Reserve RSS documentation explicitly describes reader/aggregator software that automatically incorporates feed updates. "
            "The Board disclaimer states Board-produced website information is public domain unless otherwise indicated and may be copied/distributed without permission, with Board citation requested."
        ),
        "automation_summary": (
            "Automation is limited to one daily request to the dedicated Monetary Policy RSS. It does not clear broad Federal Reserve crawling and does not alter the separate FOMC HTML schedule endpoint hold."
        ),
        "rights_reviewed_at": "2026-09-08",
        "rights_review_scope": "BP_EXPLICIT_RSS_MACHINE_INTERFACE_AND_BOARD_PUBLIC_DOMAIN_CONTENT",
        "rights_review_note": "Operational governance classification for WORLD SIGNALS; not a legal opinion.",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_priority_score": 700,
        "canonical_dependency_count": 0,
        "monitoring_readiness_assessed_at": "2026-09-08",
        "monitoring_activation_status": "LIVE_READ_ONLY_PUBLICATION_SENTINEL_NO_AUTO_COMMIT",
        "last_successful_research_verification_at": "2026-09-08",
        "canonical_provenance_use": "MONITOR_ONLY_PUBLICATION_SENTINEL_NO_CANONICAL_SCHEDULE_AUTHORITY",
        "automated_monitoring_use": "CLEARED",
        "verification_mode": "AUTOMATED_PILOT",
        "runtime_health_state": "LIVE_GITHUB_ACTIONS_RSS_FETCH_PARSE_PASS_2026_09_08",
        "governance_backfill_reviewed_at": "2026-09-08",
        "governance_backfill_basis": (
            "Separate official RSS machine-interface identity created because WSSRC-CB-001 remains Canonical FOMC schedule authority with HTML endpoint permission still held."
        ),
        "live_adapter_id": ADAPTER_ID,
        "live_validation_evidence": {
            "read_only_diagnostic_run_id": evidence["run_id"],
            "read_only_diagnostic_job_id": evidence["job_id"],
            "observed_at": evidence["observed_at"],
            "rss_http_status": evidence["rss_http_status"],
            "feeds_documentation_http_status": evidence["feeds_documentation_http_status"],
            "disclaimer_http_status": evidence["disclaimer_http_status"],
            "rss_item_count": evidence["rss_item_count"],
            "fomc_related_item_count": evidence["fomc_related_item_count"],
            "rss_sha256": evidence["rss_sha256"],
            "historical_statement_timestamp_alignment": evidence["historical_statement_timestamp_alignment"],
            "historical_minutes_timestamp_alignment": evidence["historical_minutes_timestamp_alignment"],
            "automatic_commit_allowed": False
        },
        "related_source_ids": [CANONICAL_SCHEDULE_SOURCE_ID],
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "monitor_endpoints": [
            {
                "endpoint_role": "monetary_policy_rss",
                "url": interface["feed_url"],
                "transport": "RSS_2_0_XML",
                "preferred_for_monitoring": True,
                "completeness_scope": "FINITE_ROLLING_MONETARY_POLICY_PUBLICATIONS",
                "notes": "One dedicated feed request per daily run; no wider site crawl."
            },
            {
                "endpoint_role": "rss_machine_interface_documentation",
                "url": interface["feed_documentation_url"],
                "transport": "HTML_MANUAL_GOVERNANCE_REFERENCE",
                "preferred_for_monitoring": False,
                "completeness_scope": "RSS_SUBSCRIPTION_INTERFACE_DOCUMENTATION"
            }
        ]
    }


def monitor_expectation(plan: dict) -> dict:
    interface = plan["machine_interface"]
    route = plan["monitor_route"]
    return {
        "adapter_id": ADAPTER_ID,
        "source_id": NEW_SOURCE_ID,
        "canonical_occurrence_ids": [row["occurrence_id"] for row in plan["tracked_publications"]],
        "monitor_role": "OFFICIAL_FOMC_STATEMENT_AND_MINUTES_PUBLICATION_SENTINEL",
        "cadence": route["cadence"],
        "request_budget_per_run": route["request_budget_per_run"],
        "feed": {
            "url": interface["feed_url"],
            "transport": interface["transport"],
            "request_policy": interface["request_policy"]
        },
        "classification_contract": deepcopy(plan["classification_contract"]),
        "matching": deepcopy(route["matching"]),
        "source_role_contract": deepcopy(plan["source_role_contract"]),
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "absence_policy": route["absence_policy"],
        "positive_presence_policy": route["positive_presence_policy"],
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "meeting_window_monitoring": False,
        "press_conference_monitoring": False,
        "live_intelligence_policy": "NO_AUTOMATIC_PROMOTION_TO_LIVE_INTELLIGENCE_OR_ANALYSIS",
        "automatic_commit_allowed": False
    }


def transform_sources(sources: dict, plan: dict) -> dict:
    out = deepcopy(sources)
    if any(row.get("source_id") == NEW_SOURCE_ID for row in out.get("sources", [])):
        raise RuntimeError("BP machine source already exists")
    out["sources"].append(new_machine_source(plan))
    out["version"] = plan["postconditions"]["source_registry_version"]
    out["reference_date"] = plan["review_date"]
    return out


def transform_expectations(expectations: dict, plan: dict) -> dict:
    out = deepcopy(expectations)
    out["adapters"].append(monitor_expectation(plan))
    out["version"] = plan["postconditions"]["monitor_expectations_version"]
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BP changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "FED_MONETARY_POLICY_RSS" in text:
        raise RuntimeError("Fed monetary RSS adapter already exported")
    import_anchor = "from .fomc import (\n"
    block = '''from .fed_monetary_rss import (\n    FED_MONETARY_POLICY_RSS,\n    FED_MONETARY_POLICY_RSS_ACCEPT,\n    FedMonetaryRSSItem,\n    fetch_fed_monetary_policy_rss,\n    parse_fed_monetary_policy_rss,\n)\n'''
    if import_anchor not in text:
        raise RuntimeError("Fed RSS adapter import anchor missing")
    text = text.replace(import_anchor, block + import_anchor, 1)
    all_anchor = '    "FOMC_ACCEPT",\n'
    all_block = '''    "FED_MONETARY_POLICY_RSS",\n    "FED_MONETARY_POLICY_RSS_ACCEPT",\n    "FedMonetaryRSSItem",\n'''
    if all_anchor not in text:
        raise RuntimeError("Fed RSS __all__ anchor missing")
    text = text.replace(all_anchor, all_block + all_anchor, 1)
    fetch_anchor = '    "fetch_fomc_meeting_calendar",\n'
    fetch_block = '''    "fetch_fed_monetary_policy_rss",\n    "parse_fed_monetary_policy_rss",\n'''
    if fetch_anchor not in text:
        raise RuntimeError("Fed RSS __all__ fetch anchor missing")
    return text.replace(fetch_anchor, fetch_block + fetch_anchor, 1)


def patch_live_runner(text: str) -> str:
    if 'if "FED_MONETARY_POLICY_RSS" in configs:' in text:
        raise RuntimeError("Fed monetary RSS live runner already wired")
    import_anchor = "    fetch_eurostat_release_calendar,\n"
    if import_anchor not in text:
        raise RuntimeError("Fed RSS live runner adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_fed_monetary_policy_rss,\n", 1)
    monitor_anchor = "from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates\n"
    if monitor_anchor not in text:
        raise RuntimeError("Fed RSS monitor import anchor missing")
    text = text.replace(
        monitor_anchor,
        monitor_anchor + "from world_signals.fed_monetary_monitor import fed_monetary_rss_review_candidates\n",
        1,
    )
    insert_anchor = '    if "RBA_MPB_CALENDAR" in configs:\n'
    block = '''    if "FED_MONETARY_POLICY_RSS" in configs:\n        fed_config=configs["FED_MONETARY_POLICY_RSS"]\n        try:\n            fed_items,fed_snap=fetch_fed_monetary_policy_rss()\n            report["source_health"].append({\n                "adapter_id":"FED_MONETARY_POLICY_RSS",\n                "source_id":fed_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":fed_snap.as_dict(),\n                "item_count":len(fed_items),\n                "request_policy":"ONE_DEDICATED_FEED_REQUEST_PER_DAILY_MONITOR_RUN",\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n                "automatic_commit_allowed":False,\n            })\n            candidates,observations=fed_monetary_rss_review_candidates(\n                registry.get("records",[]),fed_items,fed_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"FED_MONETARY_POLICY_RSS",\n                "source_id":fed_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n                "schedule_authority":False,\n                "lifecycle_authority":False,\n            })\n\n'''
    if insert_anchor not in text:
        raise RuntimeError("Fed RSS live runner insertion anchor missing")
    return text.replace(insert_anchor, block + insert_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"adapter":"FED_MONETARY_POLICY_RSS"' in text:
        raise RuntimeError("Fed monetary RSS smoke runner already wired")
    import_anchor = "    fetch_eurostat_release_calendar,\n"
    if import_anchor not in text:
        raise RuntimeError("Fed RSS smoke adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_fed_monetary_policy_rss,\n", 1)
    insert_anchor = "    try:\n        robots_rules,robots_snap=fetch_rba_robots_policy()\n"
    block = '''    try:\n        fed_items,fed_snap=fetch_fed_monetary_policy_rss()\n        report["results"].append({\n            "adapter":"FED_MONETARY_POLICY_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-CB-015",\n            "snapshot":fed_snap.as_dict(),\n            "item_count":len(fed_items),\n            "request_policy":"ONE_DEDICATED_FEED_REQUEST_PER_DAILY_MONITOR_RUN",\n            "schedule_authority":False,\n            "lifecycle_authority":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"FED_MONETARY_POLICY_RSS",\n            "status":"FAIL",\n            "source_id":"WSSRC-CB-015",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    if insert_anchor not in text:
        raise RuntimeError("Fed RSS smoke insertion anchor missing")
    return text.replace(insert_anchor, block + insert_anchor, 1)


def build_post_state() -> tuple[dict, dict, str, str, str]:
    plan = load_json(PLAN_PATH)
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    preflight(canonical, sources, expectations, plan)

    schedule_before = deepcopy(source_by_id(sources, CANONICAL_SCHEDULE_SOURCE_ID))
    new_sources = transform_sources(sources, plan)
    new_expectations = transform_expectations(expectations, plan)
    new_live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    new_smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    new_init = patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8"))

    if len(new_sources["sources"]) != 248:
        raise RuntimeError("BP must produce exactly 248 sources")
    if source_by_id(new_sources, CANONICAL_SCHEDULE_SOURCE_ID) != schedule_before:
        raise RuntimeError("BP must leave WSSRC-CB-001 byte-semantically unchanged")
    if source_by_id(new_sources, NEW_SOURCE_ID).get("canonical_dependency_count") != 0:
        raise RuntimeError("BP machine source must have zero Canonical dependencies")
    if new_expectations["adapters"][:11] != expectations["adapters"]:
        raise RuntimeError("BP must preserve the eleven existing monitor routes semantically")
    if len(new_expectations["adapters"]) != 12:
        raise RuntimeError("BP must produce exactly twelve configured monitor routes")
    route = new_expectations["adapters"][11]
    if route.get("adapter_id") != ADAPTER_ID or route.get("automatic_commit_allowed") is not False:
        raise RuntimeError("BP appended monitor route contract invalid")
    if len(route.get("canonical_occurrence_ids") or []) != 22:
        raise RuntimeError("BP route must contain exactly 22 tracked publications")
    return new_sources, new_expectations, new_live, new_smoke, new_init


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply BP Federal Reserve Monetary Policy RSS publication sentinel")
    parser.add_argument("--apply", action="store_true", help="materialise the bounded BP post-state")
    args = parser.parse_args()
    new_sources, new_expectations, new_live, new_smoke, new_init = build_post_state()
    if not args.apply:
        print("BP Federal Reserve Monetary Policy RSS activation check-only PASS")
        return 0
    if os.environ.get(APPLY_ENV) != "1":
        raise RuntimeError(f"refusing write without {APPLY_ENV}=1")
    dump_json(SOURCES_PATH, new_sources)
    dump_json(EXPECTATIONS_PATH, new_expectations)
    LIVE_RUNNER_PATH.write_text(new_live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(new_smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(new_init, encoding="utf-8")
    print("BP Federal Reserve Monetary Policy RSS activation transaction applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
