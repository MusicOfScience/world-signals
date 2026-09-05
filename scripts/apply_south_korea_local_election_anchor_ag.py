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
PLAN_PATH = ROOT / "data/coverage/SOUTH_KOREA_LOCAL_ELECTION_HISTORICAL_ANCHOR_AG_PLAN_v0.1.json"
AUDIT_PATH = ROOT / "data/coverage/SOUTH_KOREA_LOCAL_ELECTION_HISTORICAL_ANCHOR_AG_TRANSACTION_AUDIT_v0.1.md"
APPLY_ENV = "WORLD_SIGNALS_APPLY_KR_LOCAL_ELECTION_ANCHOR_AG"


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
    return "WSA-AG-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


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
    source_ids = {row.get("source_id") for row in sources.get("sources", [])}
    series_ids = {row.get("series_id") for row in registry.get("records", [])}
    change_ids = {row.get("change_id") for row in ledger.get("changes", [])}

    for occurrence_id in p["required_absent_occurrence_ids"]:
        if occurrence_id in by_occ:
            errors.append(f"occurrence identity collision: {occurrence_id}")
    for series_id in p["required_absent_series_ids"]:
        if series_id in series_ids:
            errors.append(f"series identity collision: {series_id}")
    for source_id in p["required_absent_source_ids"]:
        if source_id in source_ids:
            errors.append(f"source identity collision: {source_id}")
    for change_id in p["required_absent_change_ids"]:
        if change_id in change_ids:
            errors.append(f"change identity collision: {change_id}")

    template_expected = p["required_template"]
    template = by_occ.get(template_expected["occurrence_id"])
    if template is None:
        errors.append("required South Africa local-election taxonomy template missing")
    else:
        for key, expected in template_expected.items():
            if key == "occurrence_id":
                continue
            if template.get(key) != expected:
                errors.append(f"election taxonomy template drift: {key} expected {expected!r} got {template.get(key)!r}")

    if item["primary_source_assertion_id"] != expected_assertion_id(item, "PRIMARY"):
        errors.append("primary assertion identity drift")
    if item["completion_source_assertion_id"] != expected_assertion_id(item, "COMPLETION"):
        errors.append("completion assertion identity drift")
    if item["change_id"] != expected_change_id(item):
        errors.append("change identity drift")

    timing = item["timing"]
    if timing.get("timing_type") != "CIVIL_DATE" or timing.get("start_local") != "2026-06-03":
        errors.append("South Korea election civil-date contract drift")
    if timing.get("source_timezone") != "Asia/Seoul":
        errors.append("South Korea source timezone drift")
    if timing.get("start_utc") is not None or timing.get("end_utc") is not None:
        errors.append("civil election date must not be converted into a synthetic UTC instant")
    if timing.get("time_precision") != "DAY" or timing.get("all_day_semantics") is not True:
        errors.append("South Korea election day-precision/all-day semantics drift")
    if item.get("category") != "ELECTIONS_GOVERNANCE" or item.get("subcategory") != "local_government_election" or item.get("event_type") != "ELECTION_MILESTONE":
        errors.append("existing election taxonomy reuse contract drift")

    source = plan["new_source"]
    if source.get("source_id") != item.get("source_id"):
        errors.append("new source identity must match anchor primary source")
    if source.get("source_timezone") != "Asia/Seoul":
        errors.append("new NEC source timezone drift")
    if source.get("canonical_provenance_use") != "CLEARED_CURATED_FACTUAL_METADATA":
        errors.append("NEC factual-provenance classification drift")
    if source.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED" or source.get("verification_mode") != "MANUAL_AUTHORITATIVE_RECHECK":
        errors.append("NEC automation/verification boundary drift")
    if source.get("canonical_dependency_count") != 1:
        errors.append("new NEC source dependency helper must begin at one")

    registry_report = validate_registry(registry, sources)
    if not registry_report.ok:
        errors.extend(f"canonical pre-state: {error}" for error in registry_report.errors)
    errors.extend(f"overlay pre-state: {error}" for error in validate_biosecurity_overlay(registry, overlay))
    analysis_report = validate_analysis(analysis_schema, evidence, reviews, registry)
    errors.extend(f"Analysis pre-state: {error}" for error in analysis_report.errors)

    readiness = analysis_population_readiness(analysis_schema, reviews, registry)
    if readiness["eligible_completed_occurrence_count"] != 18:
        errors.append(f"unexpected pre-AG completed population: {readiness['eligible_completed_occurrence_count']}")
    if readiness["reviewed_occurrence_count"] != 12:
        errors.append(f"unexpected pre-AG reviewed population: {readiness['reviewed_occurrence_count']}")

    if errors:
        raise SystemExit("PRECONDITION FAILED:\n- " + "\n- ".join(errors))


def build_anchor(template: dict, item: dict, reference_date: str) -> dict:
    out = copy.deepcopy(template)
    timing = item["timing"]
    out.update(
        occurrence_id=item["occurrence_id"],
        series_id=item["series_id"],
        external_source_id=None,
        canonical_name=item["canonical_name"],
        short_calendar_title=item["short_calendar_title"],
        category=item["category"],
        subcategory=item["subcategory"],
        jurisdiction=item["jurisdiction"],
        region=item["region"],
        institution=item["institution"],
        event_type=item["event_type"],
        record_class=item["record_class"],
        certainty_status=item["certainty_status"],
        lifecycle_status=item["lifecycle_status"],
        activation_mode="EXPLICITLY_SCHEDULED",
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
        source_id=item["source_id"],
        primary_source_assertion_id=item["primary_source_assertion_id"],
        last_successful_assertion_id=item["completion_source_assertion_id"],
        intrinsic_importance=item["intrinsic_importance"],
        expected_market_sensitivity=item["expected_market_sensitivity"],
        first_announced_at=None,
        first_discovered_at=reference_date,
        last_verified_at=reference_date,
        next_verification_due="SOURCE_SPECIFIC",
        observed_market_response=None,
        population_tranche="SOUTH_KOREA_LOCAL_ELECTION_HISTORICAL_ANCHOR_AG",
        location=None,
        related_documents=[
            {
                "source_id": item["source_id"],
                "role": "AUTHORITATIVE_SCHEDULE_VERIFICATION",
                "source_locator": item["schedule_url"],
            },
            {
                "source_id": item["source_id"],
                "role": item["related_document_role"],
                "source_locator": item["completion_url"],
            },
        ],
        derivation_sources=[item["source_id"]],
        status_history=[
            {
                "as_of": reference_date,
                "certainty_status": item["certainty_status"],
                "lifecycle_status": item["lifecycle_status"],
                "condition_state": out.get("condition_state", "NOT_REQUIRED"),
                "change_reason": "Historical electoral-process milestone admitted after competent first-party NEC post-event verification; completion is not inferred from elapsed time.",
                "source_assertion_id": item["completion_source_assertion_id"],
                "basis": item["completion_basis"],
            }
        ],
        notes=(
            item["completion_basis"]
            + " "
            + item["semantic_guardrail"]
            + ". NEC polling hours (06:00–18:00) and 29–30 May early voting remain supporting process detail, not canonical election-day clock time."
        ),
    )
    return out


def build_source(plan_source: dict) -> dict:
    return copy.deepcopy(plan_source)


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
            "source_id": item["source_id"],
            "certainty_status": item["certainty_status"],
            "lifecycle_status": item["lifecycle_status"],
            "category": item["category"],
            "subcategory": item["subcategory"],
            "event_type": item["event_type"],
            "timing_type": timing["timing_type"],
            "start_local": timing["start_local"],
            "source_timezone": timing["source_timezone"],
            "start_utc": timing["start_utc"],
            "time_precision": timing["time_precision"],
        },
        "source_assertion_id": item["completion_source_assertion_id"],
        "review_state": "APPROVED_FOR_CANONICAL_COMMIT",
        "reviewed_at": committed_at,
        "review_basis": [
            item["schedule_url"],
            item["schedule_card_url"],
            item["completion_url"],
            item["rights_url"],
            item["completion_basis"],
            "The event-specific NEC schedule confirms 3 June 2026; the generic English calendar's provisional label is not used as the sole final date authority.",
            "Election day remains a civil-date milestone. Polling hours and early voting are supporting process details, not canonical clock-time boundaries.",
            "The nationwide simultaneous local election is not collapsed into one synthetic national winner, vote share or mandate.",
            "NEC factual provenance is separated from KOGL content-reuse conditions and from production automation permission.",
        ],
        "commit_mode": "REVIEWED_SOUTH_KOREA_LOCAL_ELECTION_HISTORICAL_ANCHOR_AG",
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
    post_sources["sources"].append(build_source(plan["new_source"]))

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
    if post_sources["sources"][: len(old_sources)] != old_sources:
        errors.append("pre-existing source records changed")
    if post_ledger["changes"][: len(old_changes)] != old_changes:
        errors.append("pre-existing ledger records changed")
    if overlay_semantics(post_overlay) != old_overlay_semantics:
        errors.append("biosecurity overlay semantic content changed")

    if post_registry.get("record_count") != post["canonical_record_count"]:
        errors.append("canonical post-count mismatch")
    if len(post_sources.get("sources", [])) != post["source_record_count"]:
        errors.append("source post-count mismatch")
    if len(post_ledger.get("changes", [])) != post["change_ledger_count"]:
        errors.append("ledger post-count mismatch")

    new_row = post_registry["records"][-1]
    new_source = post_sources["sources"][-1]
    if new_row.get("occurrence_id") != item["occurrence_id"] or new_row.get("series_id") != item["series_id"]:
        errors.append("new election identity postcondition failed")
    if new_row.get("category") != "ELECTIONS_GOVERNANCE" or new_row.get("subcategory") != "local_government_election" or new_row.get("event_type") != "ELECTION_MILESTONE":
        errors.append("election taxonomy postcondition failed")
    if new_row.get("start_local") != "2026-06-03" or new_row.get("source_timezone") != "Asia/Seoul":
        errors.append("South Korea election date/timezone postcondition failed")
    if new_row.get("timing_type") != "CIVIL_DATE" or new_row.get("time_precision") != "DAY" or new_row.get("all_day_semantics") is not True:
        errors.append("South Korea election civil-date semantics postcondition failed")
    if new_row.get("start_utc") is not None or new_row.get("end_utc") is not None:
        errors.append("South Korea civil election date gained synthetic UTC")
    if new_row.get("lifecycle_status") != "COMPLETED" or new_row.get("certainty_status") != "CONFIRMED":
        errors.append("South Korea historical election lifecycle/certainty failed")
    if new_row.get("observed_market_response") is not None:
        errors.append("AG must not encode observed market response")
    if new_row.get("expected_market_sensitivity") != "MEDIUM":
        errors.append("AG expected market sensitivity drift")
    if new_source.get("source_id") != item["source_id"] or new_source.get("canonical_dependency_count") != 1:
        errors.append("new NEC source identity/dependency postcondition failed")
    if actual_primary_dependency_count(post_registry, item["source_id"]) != post["new_source_dependency_count"]:
        errors.append("new NEC source primary dependency truth mismatch")
    if new_source.get("automated_monitoring_use") != "ENDPOINT_REVIEW_REQUIRED" or new_source.get("verification_mode") != "MANUAL_AUTHORITATIVE_RECHECK":
        errors.append("new NEC source automation boundary failed")
    if sum(1 for row in post_registry["records"] if row.get("series_id") == item["series_id"]) != 1:
        errors.append("AG must create exactly one occurrence in the new South Korea local-election series")

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
        errors.append("elections/governance completion gap not repaired")
    if not any(
        row.get("lifecycle_status") == "COMPLETED" and row.get("event_type") == post["new_completed_event_type"]
        for row in post_registry["records"]
    ):
        errors.append("election-milestone completion gap not repaired")

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
        "# WORLD SIGNALS — AG transaction audit",
        "",
        "- tranche: `SOUTH_KOREA_LOCAL_ELECTION_HISTORICAL_ANCHOR_AG`",
        f"- committed_at: `{committed_at}`",
        f"- occurrence: `{item['occurrence_id']}`",
        f"- new series: `{item['series_id']}`",
        f"- new official source: `{item['source_id']}`",
        "- event taxonomy: reused `ELECTIONS_GOVERNANCE` / `local_government_election` / `ELECTION_MILESTONE`; no schema change",
        f"- canonical post-state: `v{registry['version']} / {registry['record_count']}`",
        f"- source post-state: `v{sources['version']} / {len(sources['sources'])}`",
        f"- ledger post-state: `v{ledger['version']} / {len(ledger['changes'])}`",
        f"- overlay post-state: `v{overlay['version']} @ canonical v{overlay['canonical_checkpoint']['registry_version']} / {overlay['canonical_checkpoint']['record_count']}`",
        f"- completed Analysis population: `{readiness['eligible_completed_occurrence_count']}`",
        f"- reviewed post-event population: `{readiness['reviewed_occurrence_count']}`",
        "- Analysis mutation: `none`",
        "- timing guardrail: election day is `2026-06-03` in `Asia/Seoul` with CIVIL_DATE/DAY semantics and no synthetic UTC instant",
        "- process guardrail: early voting and 06:00–18:00 polling hours remain supporting detail, not canonical clock boundaries",
        "- result guardrail: nationwide simultaneous local elections are not collapsed into one national winner, vote share or mandate",
        "- completion guardrail: current first-party NEC winner-pledge material; elapsed time alone is insufficient",
        "- automation guardrail: curated factual provenance permitted; production monitoring remains endpoint-review/manual-recheck only",
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
