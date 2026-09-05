#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world_signals.analytical_overlays import validate_biosecurity_overlay
from src.world_signals.analysis import analysis_population_readiness, validate_analysis
from src.world_signals.validation import validate_registry

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
CANONICAL_SCHEMA_PATH = ROOT / "data/canonical/schema.json"
SOURCE_PATH = ROOT / "data/sources/registry.json"
LEDGER_PATH = ROOT / "data/changes/ledger.json"
OVERLAY_PATH = ROOT / "data/coverage/biosecurity_overlay.json"
EXPECTATIONS_PATH = ROOT / "data/monitor/expectations.json"
OPERATIONS_PATH = ROOT / "data/monitor/operations_policy.json"
ANALYSIS_SCHEMA_PATH = ROOT / "data/analysis/schema.json"
ANALYSIS_REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
ANALYSIS_EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
PLAN_PATH = ROOT / "data/coverage/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_HISTORICAL_ANCHOR_AF_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/AUSTRALIAN_TROPICAL_CYCLONE_SEASON_HISTORICAL_ANCHOR_AF_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_AU_TC_SEASON_ANCHOR_AF"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def overlay_semantics(overlay: dict) -> dict:
    return {
        key: copy.deepcopy(value)
        for key, value in overlay.items()
        if key not in {"version", "canonical_checkpoint"}
    }


def transaction_time() -> str:
    return datetime.now(ZoneInfo("Australia/Melbourne")).isoformat(timespec="seconds")


def expected_assertion_id(item: dict, role: str) -> str:
    material = "|".join(
        [item["occurrence_id"], item["series_id"], item["source_id"], role, item["timing"]["start_local"]]
    )
    return "WSA-AF-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def expected_change_id(item: dict) -> str:
    material = "|".join(
        [
            item["occurrence_id"],
            item["series_id"],
            item["source_id"],
            item["timing"]["start_local"],
            "HISTORICAL_OCCURRENCE_ADMISSION",
        ]
    )
    return "WSCHANGE-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:18]


def actual_primary_dependency_count(registry: dict, source_id: str) -> int:
    return sum(1 for row in registry.get("records", []) if row.get("source_id") == source_id)


def preflight(
    registry: dict,
    schema: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    analysis_schema: dict,
    reviews: dict,
    evidence: dict,
    plan: dict,
) -> None:
    p = plan["preconditions"]
    item = plan["anchor"]
    errors: list[str] = []

    checks = [
        (str(schema.get("version")) == p["canonical_schema_version"], "canonical schema version drift"),
        (str(registry.get("version")) == p["canonical_registry_version"], "canonical registry version drift"),
        (registry.get("record_count") == p["canonical_record_count"] == len(registry.get("records", [])), "canonical record-count drift"),
        (str(sources.get("version")) == p["source_registry_version"], "source registry version drift"),
        (len(sources.get("sources", [])) == p["source_record_count"], "source record-count drift"),
        (str(ledger.get("version")) == p["change_ledger_version"], "change ledger version drift"),
        (len(ledger.get("changes", [])) == p["change_ledger_count"], "change ledger count drift"),
        (str(overlay.get("version")) == p["biosecurity_overlay_version"], "biosecurity overlay version drift"),
        (overlay.get("canonical_checkpoint") == p["biosecurity_overlay_checkpoint"], "biosecurity overlay checkpoint drift"),
        (str(analysis_schema.get("version")) == p["analysis_schema_version"], "Analysis schema version drift"),
        (str(reviews.get("version")) == p["analysis_reviews_version"] and len(reviews.get("reviews", [])) == p["analysis_review_count"], "Analysis reviews drift"),
        (str(evidence.get("version")) == p["analysis_evidence_version"] and len(evidence.get("evidence", [])) == p["analysis_evidence_count"], "Analysis evidence drift"),
    ]
    errors.extend(message for ok, message in checks if not ok)

    by_occ = {row.get("occurrence_id"): row for row in registry.get("records", [])}
    by_source = {row.get("source_id"): row for row in sources.get("sources", [])}
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}

    for occurrence_id in p["required_absent_occurrence_ids"]:
        if occurrence_id in by_occ:
            errors.append(f"occurrence identity collision: {occurrence_id}")
    for change_id in p["required_absent_change_ids"]:
        if change_id in change_ids:
            errors.append(f"change identity collision: {change_id}")

    for label, expected_record in (
        ("template", p["required_template"]),
        ("second descendant", p["required_second_descendant"]),
        ("active Atlantic season", p["required_active_atlantic"]),
    ):
        row = by_occ.get(expected_record["occurrence_id"])
        if row is None:
            errors.append(f"required {label} record missing")
        else:
            for key, expected in expected_record.items():
                if key == "occurrence_id":
                    continue
                if row.get(key) != expected:
                    errors.append(f"{label} field drift: {key} expected {expected!r} got {row.get(key)!r}")

    expected_source = p["required_primary_source"]
    source = by_source.get(expected_source["source_id"])
    if source is None:
        errors.append("required Bureau source missing")
    else:
        for key in (
            "institution",
            "authoritative_url",
            "source_type",
            "source_timezone",
            "canonical_dependency_count",
            "canonical_provenance_use",
            "automated_monitoring_use",
            "verification_mode",
        ):
            if source.get(key) != expected_source[key]:
                errors.append(f"Bureau source field drift: {key}")
        actual = actual_primary_dependency_count(registry, expected_source["source_id"])
        if actual != expected_source["actual_primary_dependency_count"]:
            errors.append(f"Bureau actual primary dependency count drift: {actual}")
        if actual != source.get("canonical_dependency_count"):
            errors.append("Bureau dependency helper does not match canonical truth")

    if item["primary_source_assertion_id"] != expected_assertion_id(item, "PRIMARY"):
        errors.append("primary assertion identity drift")
    if item["completion_source_assertion_id"] != expected_assertion_id(item, "COMPLETION"):
        errors.append("completion assertion identity drift")
    if item["change_id"] != expected_change_id(item):
        errors.append("change identity drift")

    timing = item["timing"]
    if timing["start_local"] != "2025-11-01" or timing["end_local"] != "2026-04-30":
        errors.append("Australian season date-window drift")
    if timing.get("source_timezone") is not None or timing.get("start_utc") is not None or timing.get("end_utc") is not None:
        errors.append("regional season must not synthesize a single timezone or UTC endpoints")
    if timing.get("timing_type") != "ALL_DAY_RANGE" or timing.get("time_precision") != "DAY" or timing.get("all_day_semantics") is not True:
        errors.append("regional season timing semantics drift")
    if item.get("record_class") != "PHYSICAL_RISK_WINDOW" or item.get("signal_object_class") != "PHYSICAL_RISK_WINDOW":
        errors.append("physical-risk object-class drift")

    registry_report = validate_registry(registry, sources)
    if not registry_report.ok:
        errors.extend(f"canonical pre-state: {error}" for error in registry_report.errors)
    errors.extend(f"overlay pre-state: {error}" for error in validate_biosecurity_overlay(registry, overlay))
    analysis_report = validate_analysis(analysis_schema, evidence, reviews, registry)
    errors.extend(f"Analysis pre-state: {error}" for error in analysis_report.errors)

    readiness = analysis_population_readiness(analysis_schema, reviews, registry)
    if readiness["eligible_completed_occurrence_count"] != 17:
        errors.append(f"unexpected pre-AF completed population: {readiness['eligible_completed_occurrence_count']}")
    if readiness["reviewed_occurrence_count"] != 12:
        errors.append(f"unexpected pre-AF reviewed population: {readiness['reviewed_occurrence_count']}")

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_anchor(template: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(template)
    timing = item["timing"]
    out.update(
        occurrence_id=item["occurrence_id"],
        canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"],
        certainty_status=item["certainty_status"],
        lifecycle_status=item["lifecycle_status"],
        timing_type=timing["timing_type"],
        start_local=timing["start_local"],
        end_local=timing["end_local"],
        source_timezone=timing["source_timezone"],
        start_utc=timing["start_utc"],
        end_utc=timing["end_utc"],
        date_earliest=None,
        date_latest=None,
        time_precision=timing["time_precision"],
        all_day_semantics=timing["all_day_semantics"],
        time_status=timing["time_status"],
        time_basis=timing["time_basis"],
        publication_datetime=None,
        primary_source_assertion_id=item["primary_source_assertion_id"],
        last_successful_assertion_id=item["completion_source_assertion_id"],
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        observed_market_response=None,
        population_tranche="AUSTRALIAN_TROPICAL_CYCLONE_SEASON_HISTORICAL_ANCHOR_AF",
        related_documents=[
            {
                "source_id": item["source_id"],
                "role": item["related_document_role"],
                "source_locator": item["completion_url"],
            }
        ],
        derivation_sources=[item["source_id"]],
        status_history=[
            {
                "as_of": reference_date,
                "certainty_status": item["certainty_status"],
                "lifecycle_status": item["lifecycle_status"],
                "condition_state": out.get("condition_state", "NOT_REQUIRED"),
                "change_reason": "Historical physical-risk window admitted after competent first-party post-season verification; completion is not inferred from elapsed time.",
                "source_assertion_id": item["completion_source_assertion_id"],
                "basis": item["completion_basis"],
            }
        ],
        notes=(
            item["completion_basis"]
            + " "
            + item["semantic_guardrail"]
            + ". Actual named cyclones or material shocks remain separate objects routed through the Shock Register where warranted."
        ),
    )
    return out


def build_ledger_change(item: dict, committed_at: str, before_version: str, after_version: str) -> dict:
    timing = item["timing"]
    return {
        "change_id": item["change_id"],
        "occurrence_id": item["occurrence_id"],
        "change_type": "HISTORICAL_OCCURRENCE_ADMISSION",
        "old_values": {"canonical_presence": False},
        "new_values": {
            "canonical_presence": True,
            "series_id": item["series_id"],
            "certainty_status": item["certainty_status"],
            "lifecycle_status": item["lifecycle_status"],
            "timing_type": timing["timing_type"],
            "start_local": timing["start_local"],
            "end_local": timing["end_local"],
            "source_timezone": timing["source_timezone"],
            "start_utc": timing["start_utc"],
            "end_utc": timing["end_utc"],
            "time_precision": timing["time_precision"],
            "record_class": item["record_class"],
            "signal_object_class": item["signal_object_class"],
        },
        "source_assertion_id": item["completion_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["season_definition_url"],
            item["completion_url"],
            item["corroborating_url"],
            item["completion_basis"],
            "The Bureau's official 1 November–30 April season definition supplies the window boundaries; the 14 May 2026 Bureau summary supplies competent post-season completion evidence.",
            "The Australian-region seasonal window retains null canonical timezone/UTC endpoints; Bureau source-route timezone metadata is not promoted into the event object.",
            "Seasonal risk window, individual cyclones, landfall/damage, climate attribution, market response and causal attribution remain distinct.",
        ],
        "commit_mode": "REVIEWED_AUSTRALIAN_TROPICAL_CYCLONE_SEASON_HISTORICAL_ANCHOR_AF",
        "committed_at": committed_at,
        "registry_version_before": before_version,
        "registry_version_after": after_version,
        "canonical_mutation_committed": True,
    }


def build_post_state(
    registry: dict,
    schema: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    analysis_schema: dict,
    reviews: dict,
    evidence: dict,
    plan: dict,
    committed_at: str,
) -> tuple[dict, dict, dict, dict, dict]:
    preflight(registry, schema, sources, ledger, overlay, analysis_schema, reviews, evidence, plan)
    p = plan["preconditions"]
    post = plan["postconditions"]
    item = plan["anchor"]
    reference_date = plan["reference_date"]

    old_records = copy.deepcopy(registry["records"])
    old_sources = copy.deepcopy(sources["sources"])
    old_changes = copy.deepcopy(ledger["changes"])
    old_overlay_semantics = overlay_semantics(overlay)
    by_occ = {row["occurrence_id"]: row for row in registry["records"]}

    post_registry = copy.deepcopy(registry)
    post_registry["version"] = post["canonical_registry_version"]
    post_registry["reference_date"] = reference_date
    post_registry["records"].append(build_anchor(by_occ[item["template_occurrence_id"]], item, reference_date))
    post_registry["record_count"] = len(post_registry["records"])

    post_sources = copy.deepcopy(sources)
    post_sources["version"] = post["source_registry_version"]
    post_sources["reference_date"] = reference_date
    target_source = next(row for row in post_sources["sources"] if row.get("source_id") == item["source_id"])
    target_source["canonical_dependency_count"] = post["primary_source_dependency_count"]

    post_ledger = copy.deepcopy(ledger)
    post_ledger["version"] = post["change_ledger_version"]
    post_ledger["reference_date"] = reference_date
    post_ledger["changes"].append(
        build_ledger_change(item, committed_at, p["canonical_registry_version"], post["canonical_registry_version"])
    )

    post_overlay = copy.deepcopy(overlay)
    post_overlay["version"] = post["biosecurity_overlay_version"]
    post_overlay["canonical_checkpoint"] = copy.deepcopy(post["biosecurity_overlay_checkpoint"])

    errors: list[str] = []
    if post_registry["records"][: len(old_records)] != old_records:
        errors.append("pre-existing canonical records changed")
    if post_ledger["changes"][: len(old_changes)] != old_changes:
        errors.append("pre-existing ledger records changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        errors.append("biosecurity overlay semantic content changed")

    old_by_source = {row["source_id"]: row for row in old_sources}
    new_by_source = {row["source_id"]: row for row in post_sources["sources"]}
    if set(old_by_source) != set(new_by_source):
        errors.append("source identity set changed")
    changed_source_ids = [source_id for source_id in old_by_source if old_by_source[source_id] != new_by_source[source_id]]
    if changed_source_ids != [item["source_id"]]:
        errors.append(f"existing source mutation scope drift: {changed_source_ids}")
    else:
        before = copy.deepcopy(old_by_source[item["source_id"]])
        after = copy.deepcopy(new_by_source[item["source_id"]])
        before_count = before.pop("canonical_dependency_count", None)
        after_count = after.pop("canonical_dependency_count", None)
        if before != after or (before_count, after_count) != (2, 3):
            errors.append("Bureau source mutation exceeds dependency helper 2->3")

    if post_registry.get("record_count") != post["canonical_record_count"]:
        errors.append("canonical post-count mismatch")
    if len(post_sources.get("sources", [])) != post["source_record_count"]:
        errors.append("source post-count mismatch")
    if len(post_ledger.get("changes", [])) != post["change_ledger_count"]:
        errors.append("ledger post-count mismatch")
    if actual_primary_dependency_count(post_registry, item["source_id"]) != post["primary_source_dependency_count"]:
        errors.append("post-state Bureau primary dependency truth mismatch")
    if target_source.get("canonical_dependency_count") != actual_primary_dependency_count(post_registry, item["source_id"]):
        errors.append("post-state Bureau dependency helper mismatch")

    new_row = post_registry["records"][-1]
    if new_row.get("category") != "PHYSICAL_CLIMATE_RISK" or new_row.get("event_type") != "PHYSICAL_RISK_WINDOW":
        errors.append("physical-risk taxonomy postcondition failed")
    if new_row.get("record_class") != "PHYSICAL_RISK_WINDOW" or new_row.get("signal_object_class") != "PHYSICAL_RISK_WINDOW":
        errors.append("physical-risk object-class postcondition failed")
    if new_row.get("start_local") != "2025-11-01" or new_row.get("end_local") != "2026-04-30":
        errors.append("season-window postcondition failed")
    if new_row.get("source_timezone") is not None or new_row.get("start_utc") is not None or new_row.get("end_utc") is not None:
        errors.append("regional season timezone/UTC guardrail failed")
    if new_row.get("lifecycle_status") != "COMPLETED" or new_row.get("certainty_status") != "CONFIRMED":
        errors.append("historical physical-risk window lifecycle/certainty failed")
    if new_row.get("physical_shock_routing") != "ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER":
        errors.append("Shock Register routing guardrail drift")
    if new_row.get("observed_market_response") is not None:
        errors.append("AF must not encode observed market response")

    registry_report = validate_registry(post_registry, post_sources)
    if not registry_report.ok:
        errors.extend(f"registry post-state: {error}" for error in registry_report.errors)
    errors.extend(f"overlay post-state: {error}" for error in validate_biosecurity_overlay(post_registry, post_overlay))
    analysis_report = validate_analysis(analysis_schema, evidence, reviews, post_registry)
    errors.extend(f"Analysis post-state: {error}" for error in analysis_report.errors)

    readiness = analysis_population_readiness(analysis_schema, reviews, post_registry)
    if readiness["eligible_completed_occurrence_count"] != post["completed_analysis_population_count"]:
        errors.append(f"completed Analysis population mismatch: {readiness['eligible_completed_occurrence_count']}")
    if readiness["reviewed_occurrence_count"] != post["reviewed_completed_count"]:
        errors.append(f"reviewed Analysis population mismatch: {readiness['reviewed_occurrence_count']}")
    if not any(
        row.get("lifecycle_status") == "COMPLETED" and row.get("category") == post["new_completed_category"]
        for row in post_registry["records"]
    ):
        errors.append("physical-climate-risk completion gap not repaired")
    if not any(
        row.get("lifecycle_status") == "COMPLETED" and row.get("event_type") == post["new_completed_event_type"]
        for row in post_registry["records"]
    ):
        errors.append("physical-risk-window completion gap not repaired")

    if errors:
        raise SystemExit("POSTCONDITION FAILED:\n- " + "\n- ".join(errors))

    return post_registry, post_sources, post_ledger, post_overlay, readiness


def audit_text(
    plan: dict,
    committed_at: str,
    registry: dict,
    sources: dict,
    ledger: dict,
    overlay: dict,
    readiness: dict,
) -> str:
    item = plan["anchor"]
    protected = {
        "canonical_schema": file_hash(CANONICAL_SCHEMA_PATH),
        "monitor_expectations": file_hash(EXPECTATIONS_PATH),
        "monitor_operations_policy": file_hash(OPERATIONS_PATH),
        "analysis_schema": file_hash(ANALYSIS_SCHEMA_PATH),
        "analysis_reviews": file_hash(ANALYSIS_REVIEWS_PATH),
        "analysis_evidence": file_hash(ANALYSIS_EVIDENCE_PATH),
    }
    lines = [
        "# WORLD SIGNALS — AF transaction audit",
        "",
        f"- tranche: `AUSTRALIAN_TROPICAL_CYCLONE_SEASON_HISTORICAL_ANCHOR_AF`",
        f"- committed_at: `{committed_at}`",
        f"- occurrence: `{item['occurrence_id']}`",
        f"- series reused: `{item['series_id']}`",
        f"- primary source reused: `{item['source_id']}`",
        "- source dependency helper: `2 -> 3`",
        f"- canonical post-state: `v{registry['version']} / {registry['record_count']}`",
        f"- source post-state: `v{sources['version']} / {len(sources['sources'])}`",
        f"- ledger post-state: `v{ledger['version']} / {len(ledger['changes'])}`",
        f"- overlay post-state: `v{overlay['version']} @ canonical v{overlay['canonical_checkpoint']['registry_version']} / {overlay['canonical_checkpoint']['record_count']}`",
        f"- completed Analysis population: `{readiness['eligible_completed_occurrence_count']}`",
        f"- reviewed post-event population: `{readiness['reviewed_occurrence_count']}`",
        "- Analysis mutation: `none`",
        "- timing guardrail: `2025-11-01` to `2026-04-30`, regional all-day range; canonical timezone and UTC endpoints remain null",
        "- completion guardrail: Bureau 14 May 2026 post-season evidence; elapsed time alone is insufficient",
        "- semantic guardrail: season window != individual cyclone != landfall/damage != climate attribution != market move != causal attribution",
        "- actual cyclone events remain routed to the Shock Register where warranted",
        "- existing 2026-27 and 2027-28 Australian season records unchanged",
        "- Atlantic hurricane season 2026 remains ACTIVE",
        "- new source identities: `0`",
        "- PR #40: untouched",
        "",
        "## Protected SHA-256",
        "",
    ]
    for name, digest in protected.items():
        lines.append(f"- {name}: `{digest}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plan = load(PLAN_PATH)
    registry = load(CANONICAL_PATH)
    schema = load(CANONICAL_SCHEMA_PATH)
    sources = load(SOURCE_PATH)
    ledger = load(LEDGER_PATH)
    overlay = load(OVERLAY_PATH)
    analysis_schema = load(ANALYSIS_SCHEMA_PATH)
    reviews = load(ANALYSIS_REVIEWS_PATH)
    evidence = load(ANALYSIS_EVIDENCE_PATH)
    committed_at = transaction_time()

    before_analysis = (
        semantic_hash(analysis_schema),
        semantic_hash(reviews),
        semantic_hash(evidence),
    )

    post_registry, post_sources, post_ledger, post_overlay, readiness = build_post_state(
        registry,
        schema,
        sources,
        ledger,
        overlay,
        analysis_schema,
        reviews,
        evidence,
        plan,
        committed_at,
    )

    result = {
        "occurrence_id": plan["anchor"]["occurrence_id"],
        "canonical_post": [post_registry["version"], post_registry["record_count"]],
        "source_post": [post_sources["version"], len(post_sources["sources"])],
        "ledger_post": [post_ledger["version"], len(post_ledger["changes"])],
        "overlay_post": [post_overlay["version"], post_overlay["canonical_checkpoint"]],
        "completed_analysis_population": readiness["eligible_completed_occurrence_count"],
        "reviewed_post_event_population": readiness["reviewed_occurrence_count"],
    }

    if not args.apply:
        print("CHECK_ONLY_OK")
        print(json.dumps(result, indent=2))
        return

    if os.environ.get(APPLY_ENV) != "REVIEWED_APPLY":
        raise SystemExit(f"APPLY BLOCKED: set {APPLY_ENV}=REVIEWED_APPLY in the reviewed transaction workflow")

    dump(CANONICAL_PATH, post_registry)
    dump(SOURCE_PATH, post_sources)
    dump(LEDGER_PATH, post_ledger)
    dump(OVERLAY_PATH, post_overlay)
    AUDIT_PATH.write_text(
        audit_text(plan, committed_at, post_registry, post_sources, post_ledger, post_overlay, readiness),
        encoding="utf-8",
    )

    after_analysis = (
        semantic_hash(load(ANALYSIS_SCHEMA_PATH)),
        semantic_hash(load(ANALYSIS_REVIEWS_PATH)),
        semantic_hash(load(ANALYSIS_EVIDENCE_PATH)),
    )
    if after_analysis != before_analysis:
        raise SystemExit("POST-WRITE FAILED: Analysis drift detected")

    print("APPLY_OK")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
