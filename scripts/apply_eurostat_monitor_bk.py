from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
ADAPTER_INIT_PATH = ROOT / "src/world_signals/adapters/__init__.py"
APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BK"

EUROSTAT_ENDPOINT = "https://ec.europa.eu/eurostat/o/calendars/eventsIcal?theme=0&category=0"
EUROSTAT_SUBSCRIPTION_PAGE = "https://ec.europa.eu/eurostat/subscribe/ics.format"

EUROSTAT_TRACKED = [
    ("WSO-MAC-A-0030", "Inflation (HICP)"),
    ("WSO-MAC-A-0031", "Flash estimate inflation euro area"),
    ("WSO-MAC-A-0032", "Unemployment"),
    ("WSO-MAC-A-0033", "GDP main aggregates and employment"),
    ("WSO-MAC-A-0034", "GDP main aggregates and employment - update"),
    ("WSO-MAC-A-0035", "Preliminary flash estimate GDP - EU and euro area"),
    ("WSO-MAC-A-0036", "Flash estimate GDP and employment - EU and euro area"),
    ("WSO-MAC-B-0053", "Retail trade"),
    ("WSO-MAC-B-0054", "International trade in goods"),
    ("WSO-MAC-B-0055", "International trade in goods"),
    ("WSO-MAC-B-0056", "International trade in goods"),
    ("WSO-MAC-B-0057", "International trade in goods"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_by_id(data: dict, source_id: str) -> dict:
    matches = [row for row in data.get("sources", []) if row.get("source_id") == source_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(matches)}")
    return matches[0]


def preflight(canonical: dict, sources: dict, expectations: dict) -> None:
    if canonical.get("version") != "0.41" or len(canonical.get("records", [])) != 689:
        raise RuntimeError("BK requires exact post-BJ canonical v0.41 / 689")
    if sources.get("version") != "1.83" or len(sources.get("sources", [])) != 246:
        raise RuntimeError("BK requires exact post-BJ source registry v1.83 / 246")
    if expectations.get("version") != "0.10" or len(expectations.get("adapters", [])) != 8:
        raise RuntimeError("BK requires exact post-BJ monitor expectations v0.10 / 8")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic canonical commit gate is not closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate is not closed")
    if any(row.get("adapter_id") == "EUROSTAT_RELEASE_CALENDAR_ICS" for row in expectations["adapters"]):
        raise RuntimeError("Eurostat live adapter already exists")

    expected_ids = {occurrence_id for occurrence_id, _ in EUROSTAT_TRACKED}
    actual = [r for r in canonical["records"] if r.get("source_id") == "WSSRC-MAC-005"]
    actual_ids = {r.get("occurrence_id") for r in actual}
    if actual_ids != expected_ids or len(actual) != len(EUROSTAT_TRACKED):
        raise RuntimeError(f"Eurostat canonical dependency scope changed: {sorted(actual_ids)}")
    if any(r.get("source_timezone") != "Europe/Luxembourg" for r in actual):
        raise RuntimeError("Eurostat canonical source timezone drifted")

    eurostat = source_by_id(sources, "WSSRC-MAC-005")
    if eurostat.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("Eurostat automated monitoring permission is no longer CLEARED")
    if eurostat.get("verification_mode") != "AUTOMATED_PILOT":
        raise RuntimeError("Eurostat verification mode changed")
    if eurostat.get("monitoring_activation_status") != "ENDPOINT_IDENTITY_HOLD_NO_LIVE_ROUTE":
        raise RuntimeError("Eurostat is no longer at expected endpoint-identity hold")
    if eurostat.get("runtime_health_state") != "ENDPOINT_IDENTITY_HOLD":
        raise RuntimeError("Eurostat runtime hold state changed")


def transform_sources(sources: dict) -> dict:
    out = deepcopy(sources)
    eurostat = source_by_id(out, "WSSRC-MAC-005")
    endpoints = eurostat.setdefault("monitor_endpoints", [])
    if any(e.get("url") == EUROSTAT_ENDPOINT for e in endpoints):
        raise RuntimeError("Eurostat generated ICS endpoint already present before BK")
    endpoints.append({
        "endpoint_role": "release_calendar_all_category_ics_subscription",
        "url": EUROSTAT_ENDPOINT,
        "transport": "ICS",
        "observed_content_type": "text/plain",
        "semantic_format": "RFC5545_VCALENDAR",
        "completeness_scope": "FULL_RELEASE_CALENDAR_SUBSCRIPTION",
        "preferred_for_monitoring": True,
        "route_validation_state": "LIVE_HTTP_200_VCALENDAR_VALIDATED",
        "notes": (
            "Recovered from Eurostat's own live subscription-page generator. The all-category feed is used because "
            "the category=2 Euro-indicator filter omitted at least one tracked GDP update during BK validation. "
            "WORLD SIGNALS narrows scope through an explicit 12-occurrence allow-list."
        ),
    })
    eurostat.update({
        "machine_readable_available": "HTML + official generated ICS subscription",
        "parser_type": "ICS_RELEASE_DATE_SENTINEL_WITH_HTML_MANUAL_REVIEW",
        "parser_version": "eurostat-release-calendar-0.3",
        "runtime_health_state": "HEALTHY_AT_2026_09_08_ICS_PROBE",
        "live_adapter_id": "EUROSTAT_RELEASE_CALENDAR_ICS",
        "monitoring_activation_status": "LIVE_READ_ONLY_REVIEW_MONITOR_NO_AUTO_COMMIT",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "endpoint_route_validation_state": "OFFICIAL_GENERATOR_AND_ALL_CATEGORY_ICS_ROUTE_VALIDATED",
        "live_validation_evidence": {
            "generator_recovery_run_id": 34161096050,
            "full_feed_alignment_run_id": 34161197856,
            "filtered_negative_control_run_id": 34161294980,
            "observed_at": "2026-09-08",
            "subscription_page": EUROSTAT_SUBSCRIPTION_PAGE,
            "generated_feed_url": EUROSTAT_ENDPOINT,
            "transport_http_status": 200,
            "semantic_format": "RFC5545_VCALENDAR",
            "full_feed_vevent_count_at_probe": 2397,
            "canonical_dependency_count": 12,
            "feed_time_precision": "DAY",
            "uid_is_stable_identity": False,
            "category_2_filter_is_complete_for_tracked_scope": False,
            "automatic_commit_allowed": False,
        },
        "known_limitations": [
            "Official generated ICS feed exposes tracked release dates at civil-date precision; it must not downgrade richer canonical clock times.",
            "Generated-feed UID values are evidence only and are not stable WORLD SIGNALS occurrence identities.",
            "The category=2 Euro-indicator filter omitted a tracked GDP update in BK validation, so production uses the all-category feed plus an explicit allow-list.",
            "Absence, ambiguity, or date drift is review evidence only and is not cancellation, completion, or certainty evidence.",
        ],
    })
    if eurostat.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("BK changed Eurostat automation permission")
    out["version"] = "1.84"
    return out


def eurostat_expectation() -> dict:
    return {
        "adapter_id": "EUROSTAT_RELEASE_CALENDAR_ICS",
        "source_id": "WSSRC-MAC-005",
        "canonical_occurrence_ids": [occurrence_id for occurrence_id, _ in EUROSTAT_TRACKED],
        "monitor_role": "EXACT_RELEASE_TITLE_CIVIL_DATE_SENTINEL",
        "cadence": "DAILY",
        "feed": {
            "subscription_page": EUROSTAT_SUBSCRIPTION_PAGE,
            "url": EUROSTAT_ENDPOINT,
            "transport": "ICS",
            "semantic_format": "RFC5545_VCALENDAR",
            "source_time_precision": "DAY",
            "source_timezone": "Europe/Luxembourg",
            "scope": "ALL_CATEGORY_FEED_NARROWED_BY_TRACKED_ALLOW_LIST",
        },
        "tracked_items": [
            {"occurrence_id": occurrence_id, "feed_title": title}
            for occurrence_id, title in EUROSTAT_TRACKED
        ],
        "matching": {
            "identity": "EXACT_OFFICIAL_SUMMARY_PLUS_BOUNDED_NEAREST_DATE",
            "nearest_exact_title_max_days": 10,
            "uid_is_stable_identity": False,
        },
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "date_change_policy": "GENERATE_REVIEW_CANDIDATE_NO_DIRECT_CANONICAL_MUTATION",
        "absence_policy": "REVIEW_ONLY_NO_CANCELLATION_COMPLETION_OR_CERTAINTY_INFERENCE",
        "ambiguity_policy": "REVIEW_ONLY_NO_ARBITRARY_MATCH_SELECTION",
        "elapsed_policy": "DO_NOT_PRESENCE_CHECK_ELAPSED_OCCURRENCES_AGAINST_CURRENT_FEED",
        "precision_policy": "DATE_ONLY_FEED_CANNOT_DOWNGRADE_OR_OVERWRITE_CANONICAL_CLOCK_TIME",
        "certainty_policy": "ICS_HAS_NO_GOVERNED_CONFIRMED_PROVISIONAL_FIELD_DO_NOT_CHANGE_CERTAINTY",
        "automatic_commit_allowed": False,
    }


def transform_expectations(expectations: dict) -> dict:
    out = deepcopy(expectations)
    out["version"] = "0.11"
    out["adapters"].append(eurostat_expectation())
    if len(out["adapters"]) != 9:
        raise RuntimeError("BK post expectations do not contain exactly 9 adapters")
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("BK changed global write gates")
    return out


def patch_adapter_init(text: str) -> str:
    if "EUROSTAT_ICS_ALL_RELEASES" in text:
        raise RuntimeError("Eurostat adapter already exported")
    anchor = "from .japan_mof_jgb import (\n"
    if anchor not in text:
        raise RuntimeError("adapter __init__ anchor missing")
    block = '''from .eurostat_ics import (\n    EUROSTAT_ICS_ACCEPT,\n    EUROSTAT_ICS_ALL_RELEASES,\n    EUROSTAT_ICS_SUBSCRIPTION_PAGE,\n    EUROSTAT_TIMEZONE,\n    EurostatReleaseItem,\n    fetch_eurostat_release_calendar,\n    parse_eurostat_release_calendar_ics,\n)\n'''
    text = text.replace(anchor, block + anchor, 1)
    export_anchor = '    "FetchSnapshot",\n'
    if export_anchor not in text:
        raise RuntimeError("adapter __all__ anchor missing")
    export_block = '''    "EUROSTAT_ICS_ACCEPT",\n    "EUROSTAT_ICS_ALL_RELEASES",\n    "EUROSTAT_ICS_SUBSCRIPTION_PAGE",\n    "EUROSTAT_TIMEZONE",\n    "EurostatReleaseItem",\n'''
    text = text.replace(export_anchor, export_anchor + export_block, 1)
    fn_anchor = '    "fetch_eia_wpsr_schedule",\n'
    text = text.replace(fn_anchor, fn_anchor + '    "fetch_eurostat_release_calendar",\n', 1)
    parse_anchor = '    "parse_eia_wpsr_schedule_html",\n'
    text = text.replace(parse_anchor, parse_anchor + '    "parse_eurostat_release_calendar_ics",\n', 1)
    return text


def patch_live_runner(text: str) -> str:
    if "EUROSTAT_RELEASE_CALENDAR_ICS" in text:
        raise RuntimeError("live runner already contains Eurostat adapter")
    import_anchor = "    fetch_eia_wpsr_schedule,\n"
    if import_anchor not in text:
        raise RuntimeError("live runner adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_eurostat_release_calendar,\n", 1)
    module_anchor = "from world_signals.io import load_json\n"
    if module_anchor not in text:
        raise RuntimeError("live runner module import anchor missing")
    text = text.replace(
        module_anchor,
        module_anchor + "from world_signals.eurostat_monitor import eurostat_release_calendar_review_candidates\n",
        1,
    )
    insertion_anchor = '    try:\n        ons_items,ons_snaps=fetch_ons_upcoming_releases(\n'
    if insertion_anchor not in text:
        raise RuntimeError("live runner Eurostat insertion anchor missing")
    block = '''    if "EUROSTAT_RELEASE_CALENDAR_ICS" in configs:\n        eurostat_config=configs["EUROSTAT_RELEASE_CALENDAR_ICS"]\n        try:\n            eurostat_items,eurostat_snap=fetch_eurostat_release_calendar()\n            report["source_health"].append({\n                "adapter_id":"EUROSTAT_RELEASE_CALENDAR_ICS",\n                "source_id":eurostat_config["source_id"],\n                "state":"HEALTHY",\n                "snapshot":eurostat_snap.as_dict(),\n                "item_count":len(eurostat_items),\n                "feed_time_precision":"DAY",\n                "uid_is_stable_identity":False,\n            })\n            candidates,observations=eurostat_release_calendar_review_candidates(\n                registry.get("records",[]),eurostat_items,eurostat_config\n            )\n            report["review_candidates"].extend(candidates)\n            report["observations"].extend(observations)\n        except (AdapterError,ValueError) as exc:\n            report["source_health"].append({\n                "adapter_id":"EUROSTAT_RELEASE_CALENDAR_ICS",\n                "source_id":eurostat_config["source_id"],\n                "state":"DEGRADED",\n                "error":str(exc),\n                "canonical_action":"NONE",\n                "absence_is_not_event_state":True,\n            })\n\n'''
    return text.replace(insertion_anchor, block + insertion_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if '"EUROSTAT_RELEASE_CALENDAR_ICS"' in text:
        raise RuntimeError("smoke runner already contains Eurostat live route")
    import_anchor = "    fetch_eia_wpsr_schedule,\n" if "    fetch_eia_wpsr_schedule,\n" in text else "    fetch_ons_upcoming_releases,\n"
    if import_anchor not in text:
        raise RuntimeError("smoke runner adapter import anchor missing")
    text = text.replace(import_anchor, import_anchor + "    fetch_eurostat_release_calendar,\n", 1)
    text = text.replace('            "EUROSTAT_GENERATED_ICS_ENDPOINT_REDISCOVERY_REQUIRED"\n', '', 1)
    insertion_anchor = "    try:\n        ons_items,ons_snaps=fetch_ons_upcoming_releases()\n"
    if insertion_anchor not in text:
        raise RuntimeError("smoke runner Eurostat insertion anchor missing")
    block = '''    try:\n        eurostat_items,eurostat_snap=fetch_eurostat_release_calendar()\n        report["results"].append({\n            "adapter":"EUROSTAT_RELEASE_CALENDAR_ICS",\n            "status":"PASS",\n            "source_id":"WSSRC-MAC-005",\n            "snapshot":eurostat_snap.as_dict(),\n            "item_count":len(eurostat_items),\n            "feed_time_precision":"DAY",\n            "uid_is_stable_identity":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"EUROSTAT_RELEASE_CALENDAR_ICS",\n            "status":"FAIL",\n            "source_id":"WSSRC-MAC-005",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    return text.replace(insertion_anchor, block + insertion_anchor, 1)


def build_post_state() -> tuple[dict, dict, str, str, str]:
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    preflight(canonical, sources, expectations)
    return (
        transform_sources(sources),
        transform_expectations(expectations),
        patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8")),
        patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8")),
        patch_adapter_init(ADAPTER_INIT_PATH.read_text(encoding="utf-8")),
    )


def apply() -> None:
    if os.environ.get(APPLY_ENV) != "1":
        raise RuntimeError(f"write gate closed: set {APPLY_ENV}=1 explicitly")
    post_sources, post_expectations, live, smoke, adapter_init = build_post_state()
    dump_json(SOURCES_PATH, post_sources)
    dump_json(EXPECTATIONS_PATH, post_expectations)
    LIVE_RUNNER_PATH.write_text(live, encoding="utf-8")
    SMOKE_RUNNER_PATH.write_text(smoke, encoding="utf-8")
    ADAPTER_INIT_PATH.write_text(adapter_init, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply or simulate WORLD SIGNALS Eurostat monitor activation BK")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    post_sources, post_expectations, live, smoke, adapter_init = build_post_state()
    if args.apply:
        apply()
        print("BK transaction applied")
    else:
        print(json.dumps({
            "mode": "CHECK_ONLY",
            "post_source_version": post_sources["version"],
            "post_source_count": len(post_sources["sources"]),
            "post_expectations_version": post_expectations["version"],
            "post_adapter_count": len(post_expectations["adapters"]),
            "live_runner_has_eurostat": "EUROSTAT_RELEASE_CALENDAR_ICS" in live,
            "smoke_runner_has_eurostat": "EUROSTAT_RELEASE_CALENDAR_ICS" in smoke,
            "adapter_exports_eurostat": "EUROSTAT_ICS_ALL_RELEASES" in adapter_init,
            "automatic_canonical_commit": post_expectations["automatic_canonical_commit"],
            "google_calendar_write": post_expectations["google_calendar_write"],
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
