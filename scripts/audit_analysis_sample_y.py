#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from sys import path as sys_path
sys_path.insert(0, str(ROOT / "src"))

from world_signals.analysis import analysis_population_readiness, validate_analysis

CANONICAL_PATH = ROOT / "data/canonical/registry.json"
SCHEMA_PATH = ROOT / "data/analysis/schema.json"
REVIEWS_PATH = ROOT / "data/analysis/event_reviews.json"
EVIDENCE_PATH = ROOT / "data/analysis/evidence_registry.json"
JSON_OUT = ROOT / "data/analysis/ANALYSIS_SAMPLE_AUDIT_Y_v0.1.json"
MD_OUT = ROOT / "data/analysis/ANALYSIS_SAMPLE_AUDIT_Y_v0.1.md"

REFERENCE_DATE = "2026-09-06"
BASE_MAIN_SHA = "f05b9623f973aed84a420354d273e039a4b61f8e"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def distribution(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items(), key=lambda item: (-item[1], item[0])))


def label(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    return str(value) if value not in {None, ""} else "UNSPECIFIED"


def collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_refs" and isinstance(child, list):
                refs.update(str(item) for item in child if item)
            else:
                refs.update(collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(collect_evidence_refs(child))
    return refs


def pct(part: int, whole: int) -> float:
    return round((100.0 * part / whole), 1) if whole else 0.0


def audit() -> dict[str, Any]:
    canonical = load(CANONICAL_PATH)
    schema = load(SCHEMA_PATH)
    reviews_dataset = load(REVIEWS_PATH)
    evidence_dataset = load(EVIDENCE_PATH)

    validation = validate_analysis(schema, evidence_dataset, reviews_dataset, canonical)
    if not validation.ok:
        raise RuntimeError("Analysis validation failed before audit: " + "; ".join(validation.errors))

    readiness = analysis_population_readiness(schema, reviews_dataset, canonical)
    canonical_by_id = {
        row["occurrence_id"]: row
        for row in canonical.get("records", [])
        if row.get("occurrence_id")
    }
    completed = [
        row for row in canonical.get("records", [])
        if row.get("lifecycle_status") == "COMPLETED"
    ]
    reviews = [
        row for row in reviews_dataset.get("reviews", [])
        if row.get("review_state") in {"REVIEWED_SAMPLE", "REVIEWED"}
        and row.get("review_phase") == "POST_EVENT"
    ]
    reviewed_occurrence_ids = {
        row.get("canonical_occurrence_id") for row in reviews if row.get("canonical_occurrence_id")
    }
    reviewed_canonical = [canonical_by_id[occ_id] for occ_id in sorted(reviewed_occurrence_ids)]
    unreviewed_completed = [row for row in completed if row.get("occurrence_id") not in reviewed_occurrence_ids]

    reviewed_regions = {label(row, "region") for row in reviewed_canonical}
    reviewed_categories = {label(row, "category") for row in reviewed_canonical}
    reviewed_event_types = {label(row, "event_type") for row in reviewed_canonical}
    reviewed_institutions = {label(row, "institution") for row in reviewed_canonical}

    frontier = []
    for row in sorted(unreviewed_completed, key=lambda item: item.get("occurrence_id", "")):
        region = label(row, "region")
        category = label(row, "category")
        event_type = label(row, "event_type")
        institution = label(row, "institution")
        novelty = {
            "new_region": region not in reviewed_regions,
            "new_category": category not in reviewed_categories,
            "new_event_type": event_type not in reviewed_event_types,
            "new_institution": institution not in reviewed_institutions,
        }
        frontier.append({
            "occurrence_id": row.get("occurrence_id"),
            "canonical_name": row.get("canonical_name"),
            "institution": institution,
            "region": region,
            "category": category,
            "event_type": event_type,
            "intrinsic_importance": row.get("intrinsic_importance"),
            "expected_market_sensitivity": row.get("expected_market_sensitivity"),
            "novelty_against_reviewed_sample": novelty,
            "novel_dimension_count": sum(1 for value in novelty.values() if value),
        })

    surprise_statuses = []
    interaction_types = []
    causal_statuses = []
    connection_confidences = []
    second_order_statuses = []
    benchmark_types = []
    movement_types = []
    measurement_precisions = []
    movement_reconstruction = []
    reviews_with_movement = 0
    reviews_without_movement = 0
    reviews_without_benchmarks = 0
    falsifier_counts = []

    for review in reviews:
        surprise_statuses.append(label(review.get("what_surprised") or {}, "status"))
        connection = review.get("what_appears_connected") or {}
        interaction_types.append(label(connection, "interaction_type"))
        causal_statuses.append(label(connection, "causal_status"))
        connection_confidences.append(label(connection, "confidence"))
        second_order_statuses.append(label(review.get("second_order_effects") or {}, "status"))

        benchmarks = (review.get("what_was_expected") or {}).get("benchmarks") or []
        if not benchmarks:
            reviews_without_benchmarks += 1
        for benchmark in benchmarks:
            benchmark_types.append(label(benchmark, "benchmark_type"))

        movements = review.get("what_moved") or []
        if movements:
            reviews_with_movement += 1
        else:
            reviews_without_movement += 1
        for movement in movements:
            movement_types.append(label(movement, "movement_type"))
            measurement_precisions.append(label(movement, "measurement_precision"))
            movement_reconstruction.append(str(movement.get("independently_reconstructed")))

        falsifier_counts.append(len(review.get("falsifiers") or []))

    referenced_evidence_ids: set[str] = set()
    for review in reviews:
        referenced_evidence_ids.update(collect_evidence_refs(review))
    evidence_by_id = {
        row.get("evidence_id"): row
        for row in evidence_dataset.get("evidence", [])
        if row.get("evidence_id")
    }
    referenced_evidence = [evidence_by_id[eid] for eid in sorted(referenced_evidence_ids) if eid in evidence_by_id]
    missing_evidence_refs = sorted(referenced_evidence_ids.difference(evidence_by_id))

    provider_counts = distribution([label(row, "provider") for row in referenced_evidence])
    evidence_class_counts = distribution([label(row, "evidence_class") for row in referenced_evidence])
    evidence_role_counts = distribution([
        str(role)
        for row in referenced_evidence
        for role in (row.get("roles") or [])
    ])
    top_provider = None
    if provider_counts:
        provider_name, provider_count = next(iter(provider_counts.items()))
        top_provider = {
            "provider": provider_name,
            "count": provider_count,
            "share_percent": pct(provider_count, len(referenced_evidence)),
        }

    all_registry_regions = {label(row, "region") for row in canonical.get("records", [])}
    all_registry_categories = {label(row, "category") for row in canonical.get("records", [])}
    all_registry_event_types = {label(row, "event_type") for row in canonical.get("records", [])}
    completed_regions = {label(row, "region") for row in completed}
    completed_categories = {label(row, "category") for row in completed}
    completed_event_types = {label(row, "event_type") for row in completed}

    exact_timestamp_count = measurement_precisions.count("EXACT_TIMESTAMP_SERIES")
    source_reported_market_rows = sum(
        1 for precision in measurement_precisions
        if precision in {"SOURCE_REPORTED_PRE_POST", "SOURCE_REPORTED_CHANGE_AND_ENDPOINT", "SESSION_LEVEL", "QUALITATIVE_ONLY"}
    )

    findings = []
    findings.append({
        "finding": "CONTROLLED_EXPANSION_GATE_IS_NOT_REPRESENTATIVE_COVERAGE",
        "severity": "METHOD",
        "detail": (
            "The schema readiness state is a minimum gate. The audit must not interpret "
            "READY_FOR_CONTROLLED_EXPANSION as evidence that the reviewed sample or completed-anchor population is globally representative."
        ),
    })
    if all_registry_regions - completed_regions:
        findings.append({
            "finding": "UPSTREAM_COMPLETED_ANCHOR_REGION_GAPS",
            "severity": "MATERIAL",
            "detail": "Some canonical regions represented in the registry have no completed anchor in the current Analysis-eligible population.",
            "values": sorted(all_registry_regions - completed_regions),
        })
    if exact_timestamp_count == 0 and movement_types:
        findings.append({
            "finding": "MARKET_MEASUREMENT_PRECISION_GAP",
            "severity": "MATERIAL",
            "detail": (
                "The reviewed sample contains market-response rows but none currently use EXACT_TIMESTAMP_SERIES precision. "
                "Future market-sensitive specimens should test higher-frequency measurement where defensibly obtainable, rather than merely adding more source-reported session moves."
            ),
        })
    if top_provider:
        findings.append({
            "finding": "EVIDENCE_PROVIDER_CONCENTRATION_DESCRIPTIVE",
            "severity": "WATCH",
            "detail": (
                f"The most-used referenced evidence provider is {top_provider['provider']} at {top_provider['share_percent']}% "
                "of referenced evidence rows. This is a concentration diagnostic, not a quality judgment or quota."
            ),
        })
    if frontier:
        findings.append({
            "finding": "QUEUE_COMPLETION_IS_NOT_THE_OBJECTIVE",
            "severity": "METHOD",
            "detail": (
                "The remaining completed-but-unreviewed frontier must be selected by marginal analytical value. "
                "Exhausting the current queue is not itself a research objective."
            ),
        })

    next_stage = {
        "recommendation": "SELECT_NEXT_PRESSURE_POINT_AFTER_AUDIT",
        "priority_order": [
            "Choose an upstream historical anchor that addresses a material completed-anchor geographic/domain gap where authoritative completion evidence is available.",
            "For the next market-sensitive Analysis specimen, prefer one that materially improves measurement precision or another under-tested contract dimension.",
            "Retain any remaining eligible review, including Bank of Canada if still present, as a legitimate option rather than a compulsory queue-completion task.",
        ],
        "anti_quota_note": (
            "Vocabulary states, regions, event types, providers and causal labels are not quotas. "
            "Do not manufacture DOWNSIDE surprises, stronger causal language, market moves or historical events merely to balance distributions."
        ),
    }

    return {
        "project": "WORLD SIGNALS",
        "audit": "ANALYSIS_SAMPLE_AUDIT_Y",
        "version": "0.1",
        "reference_date": REFERENCE_DATE,
        "base_main_sha": BASE_MAIN_SHA,
        "architecture_position": "ANALYSIS_AUDIT",
        "mutation_policy": {
            "canonical_registry": false,
            "source_registry": false,
            "change_ledger": false,
            "monitor_configuration": false,
            "analysis_schema": false,
            "analysis_reviews": false,
            "analysis_evidence": false,
            "calendar": false,
        },
        "checkpoint": {
            "canonical_registry_version": canonical.get("version"),
            "canonical_record_count": len(canonical.get("records", [])),
            "analysis_schema_version": schema.get("version"),
            "analysis_reviews_version": reviews_dataset.get("version"),
            "analysis_review_count": len(reviews_dataset.get("reviews", [])),
            "analysis_evidence_version": evidence_dataset.get("version"),
            "analysis_evidence_count": len(evidence_dataset.get("evidence", [])),
            "analysis_validation_ok": validation.ok,
        },
        "readiness": readiness,
        "reviewed_sample": {
            "regions": distribution([label(row, "region") for row in reviewed_canonical]),
            "categories": distribution([label(row, "category") for row in reviewed_canonical]),
            "event_types": distribution([label(row, "event_type") for row in reviewed_canonical]),
            "institutions": distribution([label(row, "institution") for row in reviewed_canonical]),
            "intrinsic_importance": distribution([label(row, "intrinsic_importance") for row in reviewed_canonical]),
            "expected_market_sensitivity": distribution([label(row, "expected_market_sensitivity") for row in reviewed_canonical]),
        },
        "analysis_semantics": {
            "surprise_status": distribution(surprise_statuses),
            "benchmark_type": distribution(benchmark_types),
            "reviews_without_benchmarks": reviews_without_benchmarks,
            "interaction_type": distribution(interaction_types),
            "causal_status": distribution(causal_statuses),
            "connection_confidence": distribution(connection_confidences),
            "second_order_status": distribution(second_order_statuses),
            "reviews_with_market_movement": reviews_with_movement,
            "reviews_without_market_movement": reviews_without_movement,
            "movement_type": distribution(movement_types),
            "measurement_precision": distribution(measurement_precisions),
            "movement_independently_reconstructed": distribution(movement_reconstruction),
            "total_market_movement_rows": len(movement_types),
            "exact_timestamp_series_rows": exact_timestamp_count,
            "source_reported_or_session_market_rows": source_reported_market_rows,
            "minimum_falsifier_count_per_review": min(falsifier_counts) if falsifier_counts else 0,
        },
        "evidence_profile": {
            "referenced_evidence_count": len(referenced_evidence),
            "missing_evidence_refs": missing_evidence_refs,
            "evidence_class": evidence_class_counts,
            "evidence_role": evidence_role_counts,
            "provider": provider_counts,
            "top_provider": top_provider,
            "primary_official_share_percent": pct(evidence_class_counts.get("PRIMARY_OFFICIAL", 0), len(referenced_evidence)),
        },
        "upstream_population_gaps": {
            "regions_present_in_registry_but_absent_from_completed_anchors": sorted(all_registry_regions - completed_regions),
            "categories_present_in_registry_but_absent_from_completed_anchors": sorted(all_registry_categories - completed_categories),
            "event_types_present_in_registry_but_absent_from_completed_anchors": sorted(all_registry_event_types - completed_event_types),
            "regions_with_completed_anchor_but_no_reviewed_sample": sorted(completed_regions - reviewed_regions),
            "categories_with_completed_anchor_but_no_reviewed_sample": sorted(completed_categories - reviewed_categories),
            "event_types_with_completed_anchor_but_no_reviewed_sample": sorted(completed_event_types - reviewed_event_types),
        },
        "eligible_unreviewed_frontier": frontier,
        "findings": findings,
        "next_stage": next_stage,
    }


def markdown(report: dict[str, Any]) -> str:
    checkpoint = report["checkpoint"]
    readiness = report["readiness"]
    semantics = report["analysis_semantics"]
    evidence = report["evidence_profile"]
    gaps = report["upstream_population_gaps"]
    frontier = report["eligible_unreviewed_frontier"]

    def fmt_dist(values: dict[str, int]) -> str:
        return ", ".join(f"{key}: {value}" for key, value in values.items()) or "none"

    lines = [
        "# WORLD SIGNALS — Analysis sample audit Y v0.1",
        "",
        f"**Reference date:** {report['reference_date']}  ",
        f"**Exact base main:** `{report['base_main_sha']}`  ",
        f"**Canonical checkpoint:** v{checkpoint['canonical_registry_version']} / {checkpoint['canonical_record_count']}  ",
        f"**Analysis checkpoint:** schema v{checkpoint['analysis_schema_version']}; reviews v{checkpoint['analysis_reviews_version']} / {checkpoint['analysis_review_count']}; evidence v{checkpoint['analysis_evidence_version']} / {checkpoint['analysis_evidence_count']}",
        "",
        "## Audit purpose",
        "",
        "This is the charter's **sample population → audit** checkpoint. It is descriptive and diagnostic, not a quota engine. It does not mutate the canonical registry, source registry, change ledger, monitor configuration, Analysis schema, Analysis reviews/evidence or Calendar.",
        "",
        "## Current readiness",
        "",
        f"- completed Analysis-eligible occurrences: **{readiness['eligible_completed_occurrence_count']}**",
        f"- reviewed completed occurrences: **{readiness['reviewed_occurrence_count']}**",
        f"- reviewed event-type diversity: **{readiness['reviewed_event_type_diversity']}**",
        f"- schema readiness state: **`{readiness['broad_population_state']}`**",
        "- interpretation: this is a minimum controlled-expansion gate, **not** evidence of representative global coverage.",
        "",
        "## Reviewed-sample shape",
        "",
        f"- regions — {fmt_dist(report['reviewed_sample']['regions'])}",
        f"- categories — {fmt_dist(report['reviewed_sample']['categories'])}",
        f"- event types — {fmt_dist(report['reviewed_sample']['event_types'])}",
        f"- intrinsic importance — {fmt_dist(report['reviewed_sample']['intrinsic_importance'])}",
        f"- expected market sensitivity — {fmt_dist(report['reviewed_sample']['expected_market_sensitivity'])}",
        "",
        "## Analytical semantics actually exercised",
        "",
        f"- surprise states — {fmt_dist(semantics['surprise_status'])}",
        f"- benchmark types — {fmt_dist(semantics['benchmark_type'])}; reviews with no benchmark: {semantics['reviews_without_benchmarks']}",
        f"- interaction types — {fmt_dist(semantics['interaction_type'])}",
        f"- causal statuses — {fmt_dist(semantics['causal_status'])}",
        f"- second-order states — {fmt_dist(semantics['second_order_status'])}",
        f"- reviews with market movement: {semantics['reviews_with_market_movement']}; without: {semantics['reviews_without_market_movement']}",
        f"- market movement rows: {semantics['total_market_movement_rows']}; precision — {fmt_dist(semantics['measurement_precision'])}",
        f"- exact-timestamp-series market rows: **{semantics['exact_timestamp_series_rows']}**",
        f"- minimum falsifier count in any review: {semantics['minimum_falsifier_count_per_review']}",
        "",
        "The absence of a vocabulary state is not a defect by itself. In particular, the audit must not manufacture a downside surprise, stronger causal status or market move merely to make the distribution look balanced.",
        "",
        "## Evidence profile",
        "",
        f"- referenced evidence rows: **{evidence['referenced_evidence_count']}**",
        f"- evidence classes — {fmt_dist(evidence['evidence_class'])}",
        f"- primary-official share: **{evidence['primary_official_share_percent']}%**",
        f"- evidence roles — {fmt_dist(evidence['evidence_role'])}",
    ]
    if evidence.get("top_provider"):
        tp = evidence["top_provider"]
        lines.append(f"- largest single provider: **{tp['provider']}** — {tp['count']} rows / {tp['share_percent']}% of referenced evidence")
    lines += [
        "",
        "Provider concentration is a provenance diagnostic, not a claim that the dominant provider is unreliable.",
        "",
        "## Upstream population gaps",
        "",
        "These are **completed-anchor gaps**, not permission to invent historical events and not quotas.",
        "",
        "- canonical regions present somewhere in the registry but absent from the current completed-anchor population: " + (", ".join(gaps["regions_present_in_registry_but_absent_from_completed_anchors"]) or "none"),
        "- categories present in the registry but absent from completed anchors: " + (", ".join(gaps["categories_present_in_registry_but_absent_from_completed_anchors"]) or "none"),
        "- event types present in the registry but absent from completed anchors: " + (", ".join(gaps["event_types_present_in_registry_but_absent_from_completed_anchors"]) or "none"),
        "- regions with a completed anchor but no reviewed sample: " + (", ".join(gaps["regions_with_completed_anchor_but_no_reviewed_sample"]) or "none"),
        "",
        "## Current eligible-unreviewed frontier",
        "",
    ]
    if frontier:
        for row in frontier:
            novelty = row["novelty_against_reviewed_sample"]
            lines.append(
                f"- `{row['occurrence_id']}` — {row.get('canonical_name') or row['institution']} — "
                f"{row['region']} / {row['category']} / {row['event_type']}; "
                f"novel region={novelty['new_region']}, category={novelty['new_category']}, "
                f"event type={novelty['new_event_type']}, institution={novelty['new_institution']}"
            )
    else:
        lines.append("- none")

    lines += [
        "",
        "Finishing this list is **not** the objective. Each item remains eligible, but selection must be based on marginal analytical pressure and source quality.",
        "",
        "## Material audit findings",
        "",
    ]
    for finding in report["findings"]:
        lines.append(f"- **{finding['finding']}** ({finding['severity']}): {finding['detail']}")
        if finding.get("values"):
            lines.append("  - " + ", ".join(finding["values"]))

    lines += [
        "",
        "## Recommended next stage",
        "",
        "1. Prefer an authoritative **upstream historical anchor** that reduces a material completed-anchor geographic/domain gap, rather than treating the final current queue item as compulsory.",
        "2. The next genuinely market-sensitive Analysis specimen should, where possible, improve **measurement precision** beyond source-reported session moves; the current sample has no `EXACT_TIMESTAMP_SERIES` market row.",
        "3. Keep Bank of Canada eligible. Review it when it adds a distinct contract test, closes a meaningful coverage gap, or supplies better market-measurement evidence — not merely because it is last in the queue.",
        "",
        "The audit therefore recommends **controlled expansion with upstream gap repair**, followed by a fresh audit before any broad/full population step.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    report = audit()
    JSON_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MD_OUT.write_text(markdown(report), encoding="utf-8")
    print("AUDIT_OK")
    print(json.dumps({
        "reviewed": report["readiness"]["reviewed_occurrence_count"],
        "eligible": report["readiness"]["eligible_completed_occurrence_count"],
        "event_type_diversity": report["readiness"]["reviewed_event_type_diversity"],
        "frontier": [row["occurrence_id"] for row in report["eligible_unreviewed_frontier"]],
        "completed_anchor_region_gaps": report["upstream_population_gaps"]["regions_present_in_registry_but_absent_from_completed_anchors"],
        "exact_timestamp_market_rows": report["analysis_semantics"]["exact_timestamp_series_rows"],
        "top_provider": report["evidence_profile"]["top_provider"],
    }, indent=2))


if __name__ == "__main__":
    main()
