from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
EXPECTATIONS = ROOT / "data/monitor/expectations.json"

SOURCE_ID = "WSSRC-REG6-001"
OCCURRENCE_ID = "WSO-REG-I-0001"
SERIES_ID = "WSER-REG6-KE-BPS"
TARGET_SOURCE_VERSION = "1.87"
APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BN"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _source_by_id(sources: dict, source_id: str) -> dict:
    matches = [row for row in sources["sources"] if row.get("source_id") == source_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one source {source_id}, found {len(matches)}")
    return matches[0]


def _canonical_dependencies(canonical: dict) -> list[dict]:
    return [
        row for row in canonical["records"]
        if row.get("source_id") == SOURCE_ID or SOURCE_ID in (row.get("source_ids") or [])
    ]


def assert_preconditions(canonical: dict, sources: dict, expectations: dict) -> None:
    if (canonical.get("version"), len(canonical.get("records", []))) != ("0.41", 689):
        raise RuntimeError("BN requires exact Canonical v0.41 / 689 pre-state")
    if (sources.get("version"), len(sources.get("sources", []))) != ("1.86", 247):
        raise RuntimeError("BN requires exact Sources v1.86 / 247 pre-state")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != ("0.12", 10):
        raise RuntimeError("BN requires exact Monitor v0.12 / 10 pre-state")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar writes must remain closed")
    if any(row.get("source_id") == SOURCE_ID for row in expectations["adapters"]):
        raise RuntimeError("BN is readiness-only: Kenya production route already exists")

    source = _source_by_id(sources, SOURCE_ID)
    required = {
        "source_timezone": "Africa/Nairobi",
        "parser_version": "kenya-bps-rule-0.1",
        "runtime_health_state": "RESEARCH_VERIFIED_NOT_LIVE_POLLED",
        "monitoring_readiness_status": "ENDPOINT_TEST_PRIORITY",
        "monitoring_activation_status": "MANUAL_LEGAL_RULE_RECHECK_NO_AUTO_COMMIT",
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "automated_retrieval_permission": "ENDPOINT_OPERATIONAL_REVIEW_REQUIRED",
        "verification_mode": "MANUAL_AUTHORITATIVE_RECHECK",
        "canonical_provenance_use": "CLEARED_CURATED_FACTUAL_METADATA",
    }
    for key, expected in required.items():
        if source.get(key) != expected:
            raise RuntimeError(
                f"unexpected {SOURCE_ID} pre-state {key}: {source.get(key)!r} != {expected!r}"
            )

    deps = _canonical_dependencies(canonical)
    if len(deps) != 1:
        raise RuntimeError(f"expected one Kenya BPS Canonical dependency, found {len(deps)}")
    row = deps[0]
    if row.get("occurrence_id") != OCCURRENCE_ID or row.get("series_id") != SERIES_ID:
        raise RuntimeError("Kenya BPS stable Canonical identity drifted")
    if row.get("category") != "FISCAL_SOVEREIGN_FINANCE" or row.get("region") != "Africa":
        raise RuntimeError("Kenya BPS Canonical taxonomy drifted")
    if row.get("time_precision") != "DAY" or row.get("lifecycle_status") != "PLANNED":
        raise RuntimeError("Kenya BPS temporal/lifecycle semantics drifted")


def build_post_state() -> dict:
    canonical = _load(CANONICAL)
    sources = _load(SOURCES)
    expectations = _load(EXPECTATIONS)
    assert_preconditions(canonical, sources, expectations)

    post = deepcopy(sources)
    post["version"] = TARGET_SOURCE_VERSION
    post["reference_date"] = "2026-09-08"
    target = _source_by_id(post, SOURCE_ID)

    target["runtime_health_state"] = "LIVE_GITHUB_ACTIONS_FETCH_PARSE_PASS_2026_09_08"
    target["monitoring_readiness_status"] = "PILOT_ADAPTER_LIVE_VALIDATED_PERMISSION_HOLD"
    target["monitoring_activation_status"] = "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE"
    target["monitoring_readiness_assessed_at"] = "2026-09-08"
    target["verification_mode"] = "AUTOMATED_PILOT"
    target["automation_summary"] = (
        "The existing Kenya PFM section 25(2) adapter was live-validated in a bounded GitHub Actions "
        "probe against both the frozen 2025-11-04 and current unversioned Kenya Law surfaces. Both "
        "returned HTTP 200 and the same semantic statutory deadline rule. Successful reachability and "
        "parsing do not clear unattended polling: automated_monitoring_use remains ENDPOINT_REVIEW_REQUIRED, "
        "automated_retrieval_permission remains ENDPOINT_OPERATIONAL_REVIEW_REQUIRED, and no production "
        "monitor route is configured."
    )
    target["live_validation_evidence"] = {
        "read_only_probe_run_id": 34189112995,
        "read_only_probe_job_id": 101943332200,
        "observed_at": "2026-09-08",
        "historical_github_actions_current_route_status_2026_09_03": 403,
        "baseline_2025_11_04_http_status": 200,
        "current_unversioned_http_status": 200,
        "baseline_rule_sha256": "3121afc21199d121650558d896055e91ab24a6ff01c62a27dfc797baeaaab50c",
        "current_rule_sha256": "3121afc21199d121650558d896055e91ab24a6ff01c62a27dfc797baeaaab50c",
        "statutory_section": "25(2)",
        "deadline_month": 2,
        "deadline_day": 15,
    }

    limitations = list(target.get("known_limitations") or [])
    additions = [
        "GitHub Actions returned HTTP 403 on the current Kenya Law route on 3 September 2026, but a bounded BN probe on 8 September returned HTTP 200 for both the current and frozen versioned routes; runtime reachability can change and is not permission.",
        "The current and frozen routes exposed the same section 25(2) semantic rule in BN; a later rule divergence would require human review and cannot itself infer an event-state change.",
    ]
    for item in additions:
        if item not in limitations:
            limitations.append(item)
    target["known_limitations"] = limitations

    pre_by_id = {row["source_id"]: row for row in sources["sources"]}
    post_by_id = {row["source_id"]: row for row in post["sources"]}
    if set(pre_by_id) != set(post_by_id):
        raise RuntimeError("BN must not add or remove source identities")
    changed = [source_id for source_id in pre_by_id if pre_by_id[source_id] != post_by_id[source_id]]
    if changed != [SOURCE_ID]:
        raise RuntimeError(f"BN must change exactly {SOURCE_ID}; changed={changed}")
    if len(post["sources"]) != 247:
        raise RuntimeError("BN must not change source population")
    if target.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED":
        raise RuntimeError("BN must not clear Kenya production monitoring permission")
    if target.get("automated_retrieval_permission") != "ENDPOINT_OPERATIONAL_REVIEW_REQUIRED":
        raise RuntimeError("BN must retain the Kenya endpoint permission hold")
    return post


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the bounded BN Kenya PFM readiness truth repair")
    parser.add_argument("--apply", action="store_true", help="write the Source Registry post-state")
    args = parser.parse_args()

    post = build_post_state()
    if not args.apply:
        print("BN Kenya PFM readiness check-only PASS")
        return 0
    if os.environ.get(APPLY_ENV) != "1":
        raise RuntimeError(f"refusing write without {APPLY_ENV}=1")
    SOURCES.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n")
    print("BN Kenya PFM readiness source transaction applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
