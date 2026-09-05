from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SCHEMA_PATH = ROOT / "data/canonical/schema.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
BIOSECURITY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
OPERATIONS_POLICY_PATH = ROOT / "data/monitor/operations_policy.json"
SOURCES_PATH = ROOT / "data/sources/registry.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
LIVE_RUNNER_PATH = ROOT / "scripts/run_live_monitor.py"
SMOKE_RUNNER_PATH = ROOT / "scripts/run_adapter_smoke.py"
AUDIT_PATH = ROOT / "data/monitor/CORE_MONITOR_EXPANSION_O_TRANSACTION_AUDIT_v0.1.md"

APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_O"

ONS_TRACKED = [
    ("WSO-MAC-A-0037", "Consumer price inflation, UK: August 2026"),
    ("WSO-MAC-A-0038", "Consumer price inflation, UK: September 2026"),
    ("WSO-MAC-A-0039", "Consumer price inflation, UK: October 2026"),
    ("WSO-MAC-A-0040", "Consumer price inflation, UK: November 2026"),
    ("WSO-MAC-A-0041", "Consumer price inflation, UK: December 2026"),
    ("WSO-MAC-A-0042", "UK Labour Market: September 2026"),
    ("WSO-MAC-A-0043", "UK Labour Market: October 2026"),
    ("WSO-MAC-A-0044", "UK Labour Market: November 2026"),
    ("WSO-MAC-A-0045", "UK Labour Market: December 2026"),
    ("WSO-MAC-A-0046", "UK Labour Market: January 2027"),
    ("WSO-MAC-A-0047", "GDP quarterly national accounts, UK: April to June 2026"),
    ("WSO-MAC-A-0048", "GDP first quarterly estimate, UK: July to September 2026"),
    ("WSO-MAC-A-0049", "GDP quarterly national accounts, UK: July to September 2026"),
    ("WSO-MAC-B-0035", "GDP monthly estimate, UK: July 2026"),
    ("WSO-MAC-B-0036", "Index of Production, UK: July 2026"),
    ("WSO-MAC-B-0037", "UK Trade: July 2026"),
    ("WSO-MAC-B-0038", "GDP monthly estimate, UK: August 2026"),
    ("WSO-MAC-B-0039", "Index of Production, UK: August 2026"),
    ("WSO-MAC-B-0040", "UK Trade: August 2026"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def source_by_id(data: dict, source_id: str) -> dict:
    matches = [r for r in data.get("sources", []) if r.get("source_id") == source_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one source {source_id}, found {len(matches)}")
    return matches[0]


def preflight(canonical: dict, sources: dict, expectations: dict) -> None:
    if canonical.get("version") != "0.28" or len(canonical.get("records", [])) != 674:
        raise RuntimeError("core monitor O requires exact canonical v0.28 / 674 pre-state")
    if sources.get("version") != "1.69" or len(sources.get("sources", [])) != 233:
        raise RuntimeError("core monitor O requires exact source v1.69 / 233 pre-state")
    if expectations.get("version") != "0.7" or len(expectations.get("adapters", [])) != 6:
        raise RuntimeError("core monitor O requires expectations v0.7 / 6-adapter pre-state")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic canonical commit gate is not closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar write gate is not closed")
    if any(a.get("adapter_id") == "ONS_RELEASE_CALENDAR_RSS" for a in expectations.get("adapters", [])):
        raise RuntimeError("ONS live adapter already present in pre-state")

    canonical_ons = [r for r in canonical["records"] if r.get("source_id") == "WSSRC-MAC-006"]
    expected_ids = {occurrence_id for occurrence_id, _ in ONS_TRACKED}
    actual_ids = {r.get("occurrence_id") for r in canonical_ons}
    if actual_ids != expected_ids:
        raise RuntimeError(f"ONS canonical dependency scope changed: {sorted(actual_ids)}")

    ons = source_by_id(sources, "WSSRC-MAC-006")
    eurostat = source_by_id(sources, "WSSRC-MAC-005")
    for label, source in (("ONS", ons), ("Eurostat", eurostat)):
        if source.get("automated_monitoring_use") != "CLEARED":
            raise RuntimeError(f"{label} automated monitoring permission is no longer CLEARED")
    endpoints = eurostat.get("monitor_endpoints") or []
    bad = [e for e in endpoints if e.get("url") == "https://ec.europa.eu/eurostat/en/news/release-calendar"]
    if len(bad) != 1:
        raise RuntimeError("expected exactly one Eurostat misclassified release-calendar endpoint")
    if bad[0].get("transport") != "ICS":
        raise RuntimeError("Eurostat endpoint no longer has expected pre-repair ICS misclassification")


def transform_sources(sources: dict) -> dict:
    out = deepcopy(sources)
    ons = source_by_id(out, "WSSRC-MAC-006")
    eurostat = source_by_id(out, "WSSRC-MAC-005")

    ons.update({
        "parser_version": "ons-release-calendar-0.3",
        "live_adapter_id": "ONS_RELEASE_CALENDAR_RSS",
        "monitoring_activation_status": "LIVE_READ_ONLY_REVIEW_MONITOR_NO_AUTO_COMMIT",
        "monitoring_readiness_status": "LIVE_VALIDATED_NO_AUTO_COMMIT",
        "endpoint_route_validation_state": "RSS_PAGINATION_AND_19_CANONICAL_IDENTITIES_VALIDATED",
        "runtime_health_state": "HEALTHY_AT_2026_09_05_IDENTITY_PROBE",
        "live_validation_evidence": {
            "research_run_id": 33969711355,
            "observed_at": "2026-09-05",
            "transport": "application/rss+xml",
            "page_count": 4,
            "upcoming_item_count": 343,
            "canonical_identity_matches": 19,
            "canonical_identity_failures": 0,
            "datetime_mismatches": 0,
            "certainty_status_present_in_rss": False,
            "automatic_commit_allowed": False
        },
    })

    endpoints = eurostat.get("monitor_endpoints") or []
    for endpoint in endpoints:
        if endpoint.get("url") == "https://ec.europa.eu/eurostat/en/news/release-calendar":
            endpoint.update({
                "endpoint_role": "release_calendar_subscription_landing_page",
                "transport": "HTML",
                "preferred_for_monitoring": False,
                "route_validation_state": "HTML_LANDING_PAGE_NOT_GENERATED_ICS_FEED",
                "notes": (
                    "Current verification shows this URL is HTML. Eurostat still explicitly offers generated .ics "
                    "subscription URLs, but a stable authoritative generated feed URL was not recovered in this pass. "
                    "Do not substitute HTML scraping for the intended ICS/feed route."
                ),
            })
    eurostat.update({
        "monitoring_activation_status": "ENDPOINT_IDENTITY_HOLD_NO_LIVE_ROUTE",
        "monitoring_readiness_status": "HOLD_GENERATED_ICS_ENDPOINT_REDISCOVERY_REQUIRED",
        "endpoint_route_validation_state": "MISCLASSIFIED_ICS_ENDPOINT_REPAIRED_GENERATED_FEED_UNRESOLVED",
        "runtime_health_state": "ENDPOINT_IDENTITY_HOLD",
    })
    if eurostat.get("automated_monitoring_use") != "CLEARED":
        raise RuntimeError("Eurostat permission state changed during endpoint repair")

    out["version"] = "1.70"
    return out


def ons_expectation() -> dict:
    return {
        "adapter_id": "ONS_RELEASE_CALENDAR_RSS",
        "source_id": "WSSRC-MAC-006",
        "canonical_occurrence_ids": [occurrence_id for occurrence_id, _ in ONS_TRACKED],
        "monitor_role": "UPCOMING_RELEASE_DATETIME_SENTINEL",
        "cadence": "DAILY",
        "feed": {
            "base_url": "https://www.ons.gov.uk/releasecalendar",
            "transport": "RSS",
            "content_type": "application/rss+xml",
            "page_limit": 100,
            "max_pages": 10,
            "release_type": "type-upcoming"
        },
        "tracked_items": [
            {"occurrence_id": occurrence_id, "feed_title": title}
            for occurrence_id, title in ONS_TRACKED
        ],
        "source_failure_policy": "SOURCE_HEALTH_ONLY_NO_EVENT_MUTATION",
        "identity_policy": "EXACT_TITLE_ONE_MATCH_REQUIRED",
        "absence_policy": "SOURCE_MATCH_REVIEW_ONLY_NO_CANCELLATION_OR_COMPLETION_INFERENCE",
        "elapsed_policy": "DO_NOT_PRESENCE_CHECK_ELAPSED_OCCURRENCES_AGAINST_UPCOMING_FEED",
        "datetime_change_policy": "GENERATE_REVIEW_CANDIDATE_REQUIRE_OFFICIAL_HTML_VERIFICATION",
        "certainty_policy": "RSS_HAS_NO_CONFIRMED_PROVISIONAL_FIELD_DO_NOT_CHANGE_CERTAINTY_FROM_RSS",
        "automatic_commit_allowed": False
    }


def transform_expectations(expectations: dict) -> dict:
    out = deepcopy(expectations)
    out["version"] = "0.8"
    out["adapters"].append(ons_expectation())
    if len(out["adapters"]) != 7:
        raise RuntimeError("post expectations do not contain exactly 7 adapters")
    if out.get("automatic_canonical_commit") is not False or out.get("google_calendar_write") is not False:
        raise RuntimeError("global write gates changed")
    return out


def patch_live_runner(text: str) -> str:
    if "ONS_RELEASE_CALENDAR_RSS" in text:
        raise RuntimeError("live runner already contains ONS adapter")
    import_anchor = "    fetch_cellar_rdf_notice,\n    fetch_rba_fsr,\n"
    if import_anchor not in text:
        raise RuntimeError("live runner adapter import anchor not found")
    text = text.replace(
        import_anchor,
        "    fetch_cellar_rdf_notice,\n    fetch_ons_upcoming_releases,\n    fetch_rba_fsr,\n",
        1,
    )
    live_import_anchor = "from world_signals.io import load_json\n"
    if live_import_anchor not in text:
        raise RuntimeError("live runner module import anchor not found")
    text = text.replace(
        live_import_anchor,
        live_import_anchor + "from world_signals.ons_monitor import ons_release_calendar_review_candidates\n",
        1,
    )
    insertion_anchor = "    try:\n        rows,snap=fetch_suin_rows(\n"
    if insertion_anchor not in text:
        raise RuntimeError("live runner ONS insertion anchor not found")
    block = '''    try:\n        ons_items,ons_snaps=fetch_ons_upcoming_releases(\n            limit=int((configs["ONS_RELEASE_CALENDAR_RSS"].get("feed") or {}).get("page_limit",100)),\n            max_pages=int((configs["ONS_RELEASE_CALENDAR_RSS"].get("feed") or {}).get("max_pages",10)),\n        )\n        report["source_health"].append({\n            "adapter_id":"ONS_RELEASE_CALENDAR_RSS",\n            "source_id":configs["ONS_RELEASE_CALENDAR_RSS"]["source_id"],\n            "state":"HEALTHY",\n            "snapshots":[snap.as_dict() for snap in ons_snaps],\n            "page_count":len(ons_snaps),\n            "item_count":len(ons_items),\n            "rss_carries_certainty_status":False,\n        })\n        candidates,observations=ons_release_calendar_review_candidates(\n            registry.get("records",[]),ons_items,configs["ONS_RELEASE_CALENDAR_RSS"]\n        )\n        report["review_candidates"].extend(candidates)\n        report["observations"].extend(observations)\n    except (AdapterError,ValueError) as exc:\n        report["source_health"].append({\n            "adapter_id":"ONS_RELEASE_CALENDAR_RSS",\n            "source_id":configs["ONS_RELEASE_CALENDAR_RSS"]["source_id"],\n            "state":"DEGRADED",\n            "error":str(exc),\n            "canonical_action":"NONE",\n            "absence_is_not_event_state":True,\n        })\n\n'''
    return text.replace(insertion_anchor, block + insertion_anchor, 1)


def patch_smoke_runner(text: str) -> str:
    if "ONS_RELEASE_CALENDAR_RSS" in text:
        raise RuntimeError("smoke runner already contains ONS adapter")
    import_anchor = "    fetch_cellar_rdf_notice,\n    fetch_rba_fsr,\n"
    if import_anchor not in text:
        raise RuntimeError("smoke runner adapter import anchor not found")
    text = text.replace(
        import_anchor,
        "    fetch_cellar_rdf_notice,\n    fetch_ons_upcoming_releases,\n    fetch_rba_fsr,\n",
        1,
    )
    held_anchor = '            "EU_CRA_CURRENT_ELI_HTML_HTTP_202_ROUTE"\n'
    if held_anchor not in text:
        raise RuntimeError("smoke held-route anchor not found")
    text = text.replace(
        held_anchor,
        '            "EU_CRA_CURRENT_ELI_HTML_HTTP_202_ROUTE",\n            "EUROSTAT_GENERATED_ICS_ENDPOINT_REDISCOVERY_REQUIRED"\n',
        1,
    )
    insertion_anchor = "    try:\n        meta,snap=fetch_suin_metadata()\n"
    if insertion_anchor not in text:
        raise RuntimeError("smoke ONS insertion anchor not found")
    block = '''    try:\n        ons_items,ons_snaps=fetch_ons_upcoming_releases()\n        report["results"].append({\n            "adapter":"ONS_RELEASE_CALENDAR_RSS",\n            "status":"PASS",\n            "source_id":"WSSRC-MAC-006",\n            "snapshots":[snap.as_dict() for snap in ons_snaps],\n            "page_count":len(ons_snaps),\n            "item_count":len(ons_items),\n            "rss_carries_certainty_status":False,\n            "automatic_commit_allowed":False,\n        })\n    except AdapterError as exc:\n        failures.append(str(exc))\n        report["results"].append({\n            "adapter":"ONS_RELEASE_CALENDAR_RSS",\n            "status":"FAIL",\n            "source_id":"WSSRC-MAC-006",\n            "error":str(exc),\n            "canonical_action":"NONE",\n        })\n\n'''
    return text.replace(insertion_anchor, block + insertion_anchor, 1)


def build_post_state() -> tuple[dict, dict, str, str]:
    canonical = load_json(CANONICAL_PATH)
    sources = load_json(SOURCES_PATH)
    expectations = load_json(EXPECTATIONS_PATH)
    preflight(canonical, sources, expectations)
    post_sources = transform_sources(sources)
    post_expectations = transform_expectations(expectations)
    post_live = patch_live_runner(LIVE_RUNNER_PATH.read_text(encoding="utf-8"))
    post_smoke = patch_smoke_runner(SMOKE_RUNNER_PATH.read_text(encoding="utf-8"))
    return post_sources, post_expectations, post_live, post_smoke


def render_audit(protected_before: dict[str, str]) -> str:
    return f"""# WORLD SIGNALS — Core monitor expansion O transaction audit v0.1\n\n**Applied at:** {datetime.now(timezone.utc).isoformat()}  \n**Research identity probe:** GitHub Actions run `33969711355` — 19/19 exact ONS identities, 0 datetime mismatches.\n\n## Pre → post\n\n- canonical registry: v0.28 / 674 → **unchanged**\n- source registry: v1.69 / 233 → **v1.70 / 233**\n- monitor expectations: v0.7 / 6 adapters → **v0.8 / 7 adapters**\n- automatic canonical commit: **OFF**\n- Google Calendar writes: **OFF**\n\n## ONS\n\nActivated `ONS_RELEASE_CALENDAR_RSS` as a read-only review route for the 19 existing ONS canonical dependencies. The route paginates the official upcoming RSS to exhaustion inside a hard bound, matches explicit feed identities, compares scheduled datetime only, and never derives Confirmed/Provisional status from RSS.\n\nAbsence/renaming is source-match review evidence only. Elapsed occurrences are not presence-checked against the upcoming feed. No automatic event mutation is authorised.\n\n## Eurostat\n\nRepaired the stored `https://ec.europa.eu/eurostat/en/news/release-calendar` endpoint from misclassified `ICS` to its observed HTML landing-page role. Eurostat automated-monitoring permission remains `CLEARED`, but live activation is held pending recovery and validation of the actual generated `.ics` subscription URL. No HTML scraping route was substituted.\n\n## Protected-file hashes before apply\n\n```json\n{json.dumps(protected_before, indent=2, sort_keys=True)}\n```\n\nThe transaction does not write any protected file.\n"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply core monitor expansion O")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    protected_paths = [CANONICAL_PATH, SCHEMA_PATH, LEDGER_PATH, BIOSECURITY_PATH, OPERATIONS_POLICY_PATH]
    protected_before = {str(p.relative_to(ROOT)): file_hash(p) for p in protected_paths}
    post_sources, post_expectations, post_live, post_smoke = build_post_state()

    summary = {
        "mode": "APPLY" if args.apply else "CHECK_ONLY",
        "canonical": {"version": "0.28", "count": 674, "unchanged": True},
        "source_registry": {"version": post_sources["version"], "count": len(post_sources["sources"])},
        "monitor_expectations": {"version": post_expectations["version"], "adapter_count": len(post_expectations["adapters"])},
        "ons_adapter_id": "ONS_RELEASE_CALENDAR_RSS",
        "ons_tracked_count": len(ONS_TRACKED),
        "eurostat_hold": "HOLD_GENERATED_ICS_ENDPOINT_REDISCOVERY_REQUIRED",
        "automatic_canonical_commit": post_expectations["automatic_canonical_commit"],
        "google_calendar_write": post_expectations["google_calendar_write"],
    }

    if args.apply:
        if os.getenv(APPLY_ENV) != "YES":
            raise RuntimeError(f"--apply requires {APPLY_ENV}=YES")
        dump_json(SOURCES_PATH, post_sources)
        dump_json(EXPECTATIONS_PATH, post_expectations)
        LIVE_RUNNER_PATH.write_text(post_live, encoding="utf-8")
        SMOKE_RUNNER_PATH.write_text(post_smoke, encoding="utf-8")
        AUDIT_PATH.write_text(render_audit(protected_before), encoding="utf-8")
        protected_after = {str(p.relative_to(ROOT)): file_hash(p) for p in protected_paths}
        if protected_after != protected_before:
            raise RuntimeError("protected file changed during monitor O apply")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print("APPLIED: core monitor expansion O")
        return 0

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
