#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data/status/current_state.json"
DOCUMENT_PATHS = (
    ROOT / "README.md",
    ROOT / "PROJECT_STATUS.md",
    ROOT / "ROADMAP.md",
)
BEGIN_MARKER = "<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->"
END_MARKER = "<!-- WORLD_SIGNALS_CURRENT_STATE_END -->"
WRITE_ENV = "WORLD_SIGNALS_WRITE_DERIVED_STATE"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RuntimeError(f"{label} must be a list")
    return value


def build_snapshot() -> dict[str, Any]:
    canonical = load(ROOT / "data/canonical/registry.json")
    canonical_schema = load(ROOT / "data/canonical/schema.json")
    sources = load(ROOT / "data/sources/registry.json")
    changes = load(ROOT / "data/changes/ledger.json")
    overlay = load(ROOT / "data/coverage/biosecurity_overlay.json")
    monitor = load(ROOT / "data/monitor/expectations.json")
    monitor_policy = load(ROOT / "data/monitor/operations_policy.json")
    nhc = load(ROOT / "data/monitor/NHC_ATLANTIC_SEASON_CF_READINESS_v0.1.json")
    live_schema = load(ROOT / "data/live_intelligence/schema.json")
    live_observations = load(ROOT / "data/live_intelligence/observations.json")
    live_evidence = load(ROOT / "data/live_intelligence/evidence_registry.json")
    analysis_schema = load(ROOT / "data/analysis/schema.json")
    analysis_reviews = load(ROOT / "data/analysis/event_reviews.json")
    analysis_evidence = load(ROOT / "data/analysis/evidence_registry.json")
    signal_schema = load(ROOT / "data/signals/schema.json")
    signal_dataset = load(ROOT / "data/signals/signals.json")

    canonical_records = require_list(canonical.get("records"), "canonical.records")
    source_rows = require_list(sources.get("sources"), "sources.sources")
    change_rows = require_list(changes.get("changes"), "changes.changes")
    adapters = require_list(monitor.get("adapters"), "monitor.adapters")
    live_rows = require_list(live_observations.get("observations"), "live.observations")
    live_evidence_rows = require_list(live_evidence.get("evidence"), "live.evidence")
    review_rows = require_list(analysis_reviews.get("reviews"), "analysis.reviews")
    analysis_evidence_rows = require_list(analysis_evidence.get("evidence"), "analysis.evidence")
    signal_rows = require_list(signal_dataset.get("signals"), "signals.signals")

    monitor_sources = {
        row.get("source_id") for row in adapters if isinstance(row, dict) and row.get("source_id")
    }
    monitor_occurrences: set[str] = set()
    for row in adapters:
        if not isinstance(row, dict):
            continue
        for occurrence_id in row.get("canonical_occurrence_ids") or []:
            if isinstance(occurrence_id, str) and occurrence_id:
                monitor_occurrences.add(occurrence_id)

    linked_live_rows = []
    linked_occurrences: set[str] = set()
    for row in live_rows:
        if not isinstance(row, dict):
            continue
        links = row.get("canonical_links") or []
        valid_links = [link for link in links if isinstance(link, dict) and link.get("occurrence_id")]
        if valid_links:
            linked_live_rows.append(row)
            linked_occurrences.update(link["occurrence_id"] for link in valid_links)

    production_live_input_count = 0
    for review in review_rows:
        if isinstance(review, dict) and isinstance(review.get("live_inputs"), list):
            production_live_input_count += len(review["live_inputs"])

    production_revision_count = sum(
        1
        for review in review_rows
        if isinstance(review, dict) and review.get("revision_of_analysis_id")
    )
    reviewed_event_types = {
        review.get("canonical_event_type")
        for review in review_rows
        if isinstance(review, dict) and review.get("canonical_event_type")
    }

    nhc_target_ids = set(nhc.get("canonical_occurrence_ids") or [])
    nhc_registered = any(
        isinstance(row, dict)
        and row.get("source_id") == nhc.get("source_id")
        and nhc_target_ids
        and nhc_target_ids.issubset(set(row.get("canonical_occurrence_ids") or []))
        for row in adapters
    )

    dates = [
        value
        for value in (
            canonical.get("reference_date"),
            sources.get("reference_date"),
            changes.get("reference_date"),
            monitor.get("reference_date"),
            live_observations.get("reference_date"),
            analysis_reviews.get("reference_date"),
            signal_dataset.get("reference_date"),
        )
        if isinstance(value, str) and value
    ]

    live_population_policy = live_schema.get("population_policy") or {}
    live_projection_policy = live_schema.get("public_projection_policy") or {}
    live_input_policy = analysis_schema.get("live_input_policy") or {}
    revision_policy = analysis_schema.get("analysis_revision_policy") or {}
    monitor_boundary = monitor_policy.get("architecture_boundary") or {}

    live_row_auto_commit = all(row.get("automatic_canonical_commit") is False for row in live_rows)
    live_row_calendar_write = all(row.get("google_calendar_write") is False for row in live_rows)

    return {
        "project": "WORLD SIGNALS",
        "dataset": "DERIVED_PROJECT_STATE_SNAPSHOT",
        "version": "0.1",
        "reference_date": max(dates) if dates else None,
        "status": "DERIVED_NONCANONICAL_RECOVERY_SURFACE",
        "derivation_policy": {
            "governed_registries_and_contracts_remain_authoritative": True,
            "snapshot_is_not_canonical_state": True,
            "snapshot_is_not_calendar_state": True,
            "snapshot_is_not_monitor_runtime_evidence": True,
            "snapshot_may_not_mutate_upstream_layers": True,
        },
        "canonical": {
            "registry_version": canonical.get("version"),
            "occurrence_count": len(canonical_records),
            "schema_version": canonical_schema.get("version"),
        },
        "sources": {
            "registry_version": sources.get("version"),
            "source_count": len(source_rows),
        },
        "change_ledger": {
            "version": changes.get("version"),
            "entry_count": len(change_rows),
        },
        "coverage_overlays": {
            "biosecurity_overlay_version": overlay.get("version"),
            "biosecurity_canonical_checkpoint": overlay.get("canonical_checkpoint"),
        },
        "monitor": {
            "expectations_version": monitor.get("version"),
            "configured_adapter_count": len(adapters),
            "unique_monitor_source_count": len(monitor_sources),
            "explicit_scoped_occurrence_count": len(monitor_occurrences),
            "operations_policy_version": monitor_policy.get("version"),
            "automatic_canonical_commit": monitor.get("automatic_canonical_commit"),
            "google_calendar_write": monitor.get("google_calendar_write"),
            "nhc_atlantic_pilot": {
                "source_id": nhc.get("source_id"),
                "canonical_occurrence_ids": nhc.get("canonical_occurrence_ids"),
                "readiness_verdict": nhc.get("readiness_verdict"),
                "registered_in_expectations": nhc_registered,
            },
        },
        "live_intelligence": {
            "schema_version": live_schema.get("version"),
            "observations_version": live_observations.get("version"),
            "observation_count": len(live_rows),
            "evidence_version": live_evidence.get("version"),
            "evidence_count": len(live_evidence_rows),
            "canonical_linked_observation_count": len(linked_live_rows),
            "canonical_linked_occurrence_count": len(linked_occurrences),
            "automatic_ingestion_allowed": live_population_policy.get("automatic_ingestion_allowed"),
            "public_observation_projection_allowed": live_projection_policy.get("observation_projection_allowed"),
            "all_observation_auto_commit_gates_closed": live_row_auto_commit,
            "all_observation_calendar_write_gates_closed": live_row_calendar_write,
        },
        "analysis": {
            "schema_version": analysis_schema.get("version"),
            "reviews_version": analysis_reviews.get("version"),
            "review_count": len(review_rows),
            "evidence_version": analysis_evidence.get("version"),
            "evidence_count": len(analysis_evidence_rows),
            "reviewed_event_type_count": len(reviewed_event_types),
            "production_live_input_count": production_live_input_count,
            "production_revision_count": production_revision_count,
            "public_live_input_projection_allowed": live_input_policy.get("public_live_input_projection_allowed"),
            "public_revision_metadata_projection_allowed": revision_policy.get("public_revision_metadata_projection_allowed"),
            "automatic_latest_analysis_selection_allowed": revision_policy.get("automatic_latest_analysis_selection_allowed"),
        },
        "signals": {
            "schema_version": signal_schema.get("version"),
            "revision_count": len(signal_rows),
            "population_state": signal_dataset.get("population_state"),
            "production_population_allowed": (signal_schema.get("population_policy") or {}).get("production_population_allowed"),
            "admission_transaction_required": (signal_schema.get("population_policy") or {}).get("admission_transaction_required"),
            "maximum_production_signal_count": (signal_schema.get("population_policy") or {}).get("maximum_production_signal_count"),
            "public_signal_projection_allowed": (signal_schema.get("public_projection_policy") or {}).get("signal_projection_allowed"),
        },
        "write_gates": {
            "automatic_canonical_commit": monitor.get("automatic_canonical_commit"),
            "google_calendar_write": monitor.get("google_calendar_write"),
            "monitor_may_mutate_canonical": monitor_boundary.get("source_monitor_may_mutate_canonical"),
            "live_automatic_ingestion_allowed": live_population_policy.get("automatic_ingestion_allowed"),
            "live_public_projection_allowed": live_projection_policy.get("observation_projection_allowed"),
        },
        "quarantine": {
            "opec_quarantine_record_present": (ROOT / "OPEC_QUARANTINE.md").is_file(),
        },
    }


def render_current_state_block(snapshot: dict[str, Any]) -> str:
    canonical = snapshot["canonical"]
    sources = snapshot["sources"]
    changes = snapshot["change_ledger"]
    monitor = snapshot["monitor"]
    live = snapshot["live_intelligence"]
    analysis = snapshot["analysis"]
    signals = snapshot["signals"]
    nhc = monitor["nhc_atlantic_pilot"]
    return "\n".join(
        [
            BEGIN_MARKER,
            "## Mechanically derived current state",
            "",
            f"**Reference date:** {snapshot['reference_date']}",
            "**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.",
            "",
            f"- Canonical Registry: **v{canonical['registry_version']} / {canonical['occurrence_count']} occurrences**; schema **v{canonical['schema_version']}**.",
            f"- Source Registry: **v{sources['registry_version']} / {sources['source_count']} sources**.",
            f"- Change Ledger: **v{changes['version']} / {changes['entry_count']} entries**.",
            f"- Monitor expectations: **v{monitor['expectations_version']} / {monitor['configured_adapter_count']} configured adapters / {monitor['unique_monitor_source_count']} unique monitor sources / {monitor['explicit_scoped_occurrence_count']} explicitly scoped Canonical occurrences**.",
            f"- Live Intelligence: **v{live['schema_version']} / {live['observation_count']} observations / {live['evidence_count']} evidence rows / {live['canonical_linked_observation_count']} Canonical-linked observations**; automatic ingestion and public observation projection remain closed.",
            f"- Analysis: schema **v{analysis['schema_version']}**; reviews **v{analysis['reviews_version']} / {analysis['review_count']}**; evidence **v{analysis['evidence_version']} / {analysis['evidence_count']}**; production Live inputs **{analysis['production_live_input_count']}**; production revisions **{analysis['production_revision_count']}**.",
            f"- Signals: schema **v{signals['schema_version']} / {signals['revision_count']} admitted revision(s)**; population **{signals['population_state']}**; admission transaction required; maximum production population **{signals['maximum_production_signal_count']}**; public projection **closed**.",
            f"- NHC Atlantic pilot: **{nhc['readiness_verdict']}**; registered in scheduled Monitor expectations: **{str(nhc['registered_in_expectations']).lower()}**.",
            "- Automatic Canonical commit: **OFF**. Google Calendar writes: **OFF**. Public Live and Live-input projection: **OFF**. Public Analysis revision metadata/latest-head collapse: **OFF**.",
            "- OPEC CE remains quarantined; `OPEC_QUARANTINE.md` is present and PR #113 is not a selectable unfinished transaction.",
            END_MARKER,
        ]
    )


def replace_block(text: str, block: str) -> str:
    if BEGIN_MARKER not in text or END_MARKER not in text:
        raise RuntimeError("document is missing current-state markers")
    before, rest = text.split(BEGIN_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    return before.rstrip() + "\n\n" + block + after


def check_documents(snapshot: dict[str, Any]) -> list[str]:
    expected = render_current_state_block(snapshot)
    errors: list[str] = []
    for path in DOCUMENT_PATHS:
        text = path.read_text(encoding="utf-8")
        if BEGIN_MARKER not in text or END_MARKER not in text:
            errors.append(f"{path.name}: missing current-state markers")
            continue
        actual = BEGIN_MARKER + text.split(BEGIN_MARKER, 1)[1].split(END_MARKER, 1)[0] + END_MARKER
        if actual != expected:
            errors.append(f"{path.name}: current-state block drift")
    return errors


def check_snapshot() -> list[str]:
    current = build_snapshot()
    expected = load(SNAPSHOT_PATH)
    errors: list[str] = []
    if current != expected:
        errors.append("data/status/current_state.json drift")
    errors.extend(check_documents(current))
    return errors


def write_state() -> None:
    if os.environ.get(WRITE_ENV) != "YES":
        raise RuntimeError(f"--write requires {WRITE_ENV}=YES")
    snapshot = build_snapshot()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    block = render_current_state_block(snapshot)
    for path in DOCUMENT_PATHS:
        text = path.read_text(encoding="utf-8")
        path.write_text(replace_block(text, block), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive and validate the noncanonical WORLD SIGNALS recovery-state snapshot.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Fail if the checked-in snapshot or current-state document blocks drift from governed files.")
    group.add_argument("--write", action="store_true", help=f"Rewrite derived snapshot and document blocks; requires {WRITE_ENV}=YES.")
    args = parser.parse_args()

    if args.write:
        write_state()
        print("PROJECT_STATE_SNAPSHOT_WRITTEN")
        return 0
    if args.check:
        errors = check_snapshot()
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("PROJECT_STATE_SNAPSHOT_PASS")
        return 0

    print(json.dumps(build_snapshot(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
