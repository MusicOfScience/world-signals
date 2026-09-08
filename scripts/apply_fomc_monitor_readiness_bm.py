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

SOURCE_ID = "WSSRC-CB-001"
TARGET_SOURCE_VERSION = "1.86"
APPLY_ENV = "WORLD_SIGNALS_APPLY_MONITOR_BM"

EXPECTED_SERIES = {
    "WS.CB.FED.FOMC_MEETING_WINDOW",
    "WS.CB.FED.FOMC_POLICY_DECISION",
    "WS.CB.FED.FOMC_PRESS_CONFERENCE",
    "WS.CB.FED.FOMC_MINUTES",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _source_by_id(sources: dict, source_id: str) -> dict:
    matches = [row for row in sources["sources"] if row.get("source_id") == source_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one source {source_id}, found {len(matches)}")
    return matches[0]


def assert_preconditions(canonical: dict, sources: dict, expectations: dict) -> None:
    if (canonical.get("version"), len(canonical.get("records", []))) != ("0.41", 689):
        raise RuntimeError("BM requires exact Canonical v0.41 / 689 pre-state")
    if (sources.get("version"), len(sources.get("sources", []))) != ("1.85", 247):
        raise RuntimeError("BM requires exact Sources v1.85 / 247 pre-state")
    if (expectations.get("version"), len(expectations.get("adapters", []))) != ("0.12", 10):
        raise RuntimeError("BM requires exact Monitor v0.12 / 10 pre-state")
    if expectations.get("automatic_canonical_commit") is not False:
        raise RuntimeError("automatic Canonical commit must remain closed")
    if expectations.get("google_calendar_write") is not False:
        raise RuntimeError("Google Calendar writes must remain closed")
    if any(row.get("source_id") == SOURCE_ID for row in expectations["adapters"]):
        raise RuntimeError("BM is readiness-only: FOMC production route already exists")

    source = _source_by_id(sources, SOURCE_ID)
    required = {
        "automated_monitoring_use": "ENDPOINT_REVIEW_REQUIRED",
        "automated_retrieval_permission": "PENDING_ENDPOINT_OPERATIONAL_REVIEW",
        "verification_mode": "AUTOMATED_PILOT",
        "parser_version": "fomc-calendar-rule-0.1",
        "monitoring_readiness_status": "PILOT_VALIDATED_NO_AUTO_COMMIT",
        "monitoring_activation_status": "PILOT_WITH_REVIEWED_COMMIT_ONLY",
        "source_timezone": "America/New_York",
        "canonical_dependency_count": 44,
    }
    for key, expected in required.items():
        if source.get(key) != expected:
            raise RuntimeError(
                f"unexpected {SOURCE_ID} pre-state {key}: {source.get(key)!r} != {expected!r}"
            )

    rows = [row for row in canonical["records"] if row.get("source_id") == SOURCE_ID]
    if len(rows) != 44:
        raise RuntimeError(f"expected 44 FOMC Canonical dependencies, found {len(rows)}")
    if {row.get("series_id") for row in rows} != EXPECTED_SERIES:
        raise RuntimeError("FOMC Canonical series decomposition drifted")
    if {row.get("source_timezone") for row in rows} != {"America/New_York"}:
        raise RuntimeError("FOMC Canonical source-native timezone drifted")
    if sum(row.get("time_precision") == "DATE_RANGE" for row in rows) != 11:
        raise RuntimeError("FOMC meeting-window precision decomposition drifted")
    if sum(row.get("time_precision") == "MINUTE" for row in rows) != 33:
        raise RuntimeError("FOMC timed-event precision decomposition drifted")


def build_post_state() -> dict:
    canonical = _load(CANONICAL)
    sources = _load(SOURCES)
    expectations = _load(EXPECTATIONS)
    assert_preconditions(canonical, sources, expectations)

    post = deepcopy(sources)
    post["version"] = TARGET_SOURCE_VERSION
    post["reference_date"] = "2026-09-08"
    target = _source_by_id(post, SOURCE_ID)

    target["parser_type"] = "HTML_FOMC_SCHEDULE_READINESS_ADAPTER"
    target["parser_version"] = "fomc-schedule-readiness-0.2"
    target["runtime_health_state"] = "LIVE_GITHUB_ACTIONS_FETCH_PARSE_PASS_2026_09_08"
    target["monitoring_readiness_status"] = "PILOT_ADAPTER_LIVE_VALIDATED_PERMISSION_HOLD"
    target["monitoring_activation_status"] = "ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE"
    target["monitoring_readiness_assessed_at"] = "2026-09-08"
    target["automation_summary"] = (
        "A real first-party FOMC schedule adapter is live-validated against the meeting calendar "
        "and September/October/December 2026 operational calendars. Reachability and successful "
        "parsing are not treated as automated-retrieval permission; automated_monitoring_use "
        "remains ENDPOINT_REVIEW_REQUIRED and no production monitor route is configured."
    )
    target["live_validation_evidence"] = {
        "post_bl_pressure_audit_run_id": 34182397891,
        "source_scope_probe_run_id": 34182471933,
        "endpoint_operational_probe_run_id": 34182651174,
        "adapter_preflight_success_run_id": 34183359710,
        "adapter_preflight_success_job_id": 101926752639,
        "first_fail_closed_preflight_run_id": 34183129817,
        "first_fail_closed_preflight_job_id": 101926078988,
        "observed_at": "2026-09-08",
        "meeting_calendar_http_status": 200,
        "operational_calendar_http_statuses": [200, 200, 200],
        "meeting_schedule_semantic_sha256": "e9db0ba88ed1798569706a99201a457e87b0abe80e4ccb06266d297ff8a533a5",
        "september_operational_semantic_sha256": "8a601428ad51e2f1e8444356f196e5a054749a60ba913930a3b9447917d873c8",
        "october_operational_semantic_sha256": "8c6252d6cf334c92e687217280e86f8c1722df2cbef2a41c262eee334e48181f",
        "december_operational_semantic_sha256": "6a10ba410fbd110391317a4892ab548cb3bff6c1e9c86448dfec734838533610",
    }

    limitations = list(target.get("known_limitations") or [])
    additions = [
        "The conventional /robots.txt path returned HTTP 404 during the bounded BM probe; absence of a robots file is neither permission nor prohibition and does not clear automated retrieval.",
        "The Federal Reserve monetary-policy RSS feed is a separate machine-readable publication interface and is not forward schedule authority; BM does not activate or fold it into this source route.",
        "The FOMC calendar's generic tentative-date note is preserved as source semantics but is not converted into automatic Canonical certainty changes.",
        "The general three-week minutes-release convention is not used to manufacture future minutes occurrences; explicit monthly operational calendars remain required for clocks and publication dates.",
        "The historical source record overstated durable parser readiness: BM replaces the bootstrap-era parser label with a real live-validated adapter while keeping the automation permission hold closed.",
    ]
    for item in additions:
        if item not in limitations:
            limitations.append(item)
    target["known_limitations"] = limitations

    pre_by_id = {row["source_id"]: row for row in sources["sources"]}
    post_by_id = {row["source_id"]: row for row in post["sources"]}
    if set(pre_by_id) != set(post_by_id):
        raise RuntimeError("BM must not add or remove source identities")
    changed = [source_id for source_id in pre_by_id if pre_by_id[source_id] != post_by_id[source_id]]
    if changed != [SOURCE_ID]:
        raise RuntimeError(f"BM must change exactly {SOURCE_ID}; changed={changed}")
    if len(post["sources"]) != 247:
        raise RuntimeError("BM must not change source population")
    if target.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED":
        raise RuntimeError("BM must not clear FOMC production monitoring permission")
    if target.get("automated_retrieval_permission") != "PENDING_ENDPOINT_OPERATIONAL_REVIEW":
        raise RuntimeError("BM must conservatively retain the existing automated-retrieval hold")
    if target.get("verification_mode") != "AUTOMATED_PILOT":
        raise RuntimeError("BM must preserve FOMC verification mode")
    return post


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the bounded BM FOMC readiness truth repair")
    parser.add_argument("--apply", action="store_true", help="write the Source Registry post-state")
    args = parser.parse_args()

    post = build_post_state()
    if not args.apply:
        print("BM FOMC readiness check-only PASS")
        return 0
    if os.environ.get(APPLY_ENV) != "1":
        raise RuntimeError(f"refusing write without {APPLY_ENV}=1")
    SOURCES.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n")
    print("BM FOMC readiness source transaction applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
