#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from scripts.audit_analysis_sample_y import audit as base_audit

JSON_OUT = ROOT / "data/analysis/POST_AA_PRESSURE_AUDIT_AB_v0.1.json"
MD_OUT = ROOT / "data/analysis/POST_AA_PRESSURE_AUDIT_AB_v0.1.md"
REFERENCE_DATE = "2026-09-06"
BASE_MAIN_SHA = "c4b499436db54f6dc3ebbe045cfda2fba7f730dd"


def build_report() -> dict[str, Any]:
    report = base_audit()
    report["audit"] = "POST_AA_PRESSURE_AUDIT_AB"
    report["version"] = "0.1"
    report["reference_date"] = REFERENCE_DATE
    report["base_main_sha"] = BASE_MAIN_SHA

    gaps = report["upstream_population_gaps"]
    frontier = report["eligible_unreviewed_frontier"]
    semantics = report["analysis_semantics"]
    reviewed = report["reviewed_sample"]

    frontier_ranked = sorted(
        frontier,
        key=lambda row: (
            -row["novel_dimension_count"],
            row.get("region") or "",
            row.get("occurrence_id") or "",
        ),
    )

    comparison = {
        "east_asia_completed_anchor_gap_repaired": "East Asia" not in gaps["regions_present_in_registry_but_absent_from_completed_anchors"],
        "east_asia_reviewed_sample_present": reviewed["regions"].get("East Asia", 0) >= 1,
        "fiscal_financing_event_reviewed": reviewed["event_types"].get("FISCAL_FINANCING_EVENT", 0) >= 1,
        "exact_timestamp_series_gap_remains": semantics["exact_timestamp_series_rows"] == 0,
        "completed_anchor_region_gap_count": len(gaps["regions_present_in_registry_but_absent_from_completed_anchors"]),
        "completed_anchor_category_gap_count": len(gaps["categories_present_in_registry_but_absent_from_completed_anchors"]),
        "completed_anchor_event_type_gap_count": len(gaps["event_types_present_in_registry_but_absent_from_completed_anchors"]),
    }

    report["post_aa_comparison"] = comparison
    report["frontier_ranked_by_sample_novelty"] = frontier_ranked
    report["selection_discipline"] = {
        "frontier_is_not_backlog": True,
        "remaining_frontier_count": len(frontier),
        "upstream_gap_repair_has_priority_when_material": True,
        "market_precision_gap_is_not_permission_to_infer_timestamps": True,
        "recommendation": (
            "Do not consume the two remaining completed reviews mechanically. With East Asia and FISCAL_FINANCING_EVENT now repaired, "
            "the next tranche should compare: (a) a historical anchor in a still-missing completed category/event type, and (b) Bank of Canada "
            "only if authoritative high-frequency market evidence can materially improve measurement precision. Japan household spending is lower "
            "marginal value because it repeats East Asia, MACROECONOMIC_RELEASE and DATA_RELEASE."
        ),
    }
    return report


def markdown(report: dict[str, Any]) -> str:
    checkpoint = report["checkpoint"]
    readiness = report["readiness"]
    gaps = report["upstream_population_gaps"]
    comparison = report["post_aa_comparison"]
    semantics = report["analysis_semantics"]
    evidence = report["evidence_profile"]

    lines = [
        "# WORLD SIGNALS — Post-AA pressure audit AB v0.1",
        "",
        f"**Reference date:** {report['reference_date']}  ",
        f"**Exact base main:** `{report['base_main_sha']}`  ",
        f"**Canonical:** v{checkpoint['canonical_registry_version']} / {checkpoint['canonical_record_count']}  ",
        f"**Analysis:** schema v{checkpoint['analysis_schema_version']}; reviews v{checkpoint['analysis_reviews_version']} / {checkpoint['analysis_review_count']}; evidence v{checkpoint['analysis_evidence_version']} / {checkpoint['analysis_evidence_count']}",
        "",
        "## Purpose",
        "",
        "AB is a read-only post-AA pressure audit. It asks what AA actually repaired, what material gaps remain, and whether the two completed-but-unreviewed occurrences are genuinely the best next work. It is not a quota engine and does not mutate canonical, source, monitor, Analysis or Calendar data.",
        "",
        "## What AA repaired",
        "",
        f"- East Asia completed-anchor gap repaired: **{comparison['east_asia_completed_anchor_gap_repaired']}**",
        f"- East Asia now represented in reviewed Analysis sample: **{comparison['east_asia_reviewed_sample_present']}**",
        f"- `FISCAL_FINANCING_EVENT` now reviewed: **{comparison['fiscal_financing_event_reviewed']}**",
        f"- reviewed completed occurrences: **{readiness['reviewed_occurrence_count']} / {readiness['eligible_completed_occurrence_count']}**",
        f"- reviewed event-type diversity: **{readiness['reviewed_event_type_diversity']}**",
        "",
        "## What remains material",
        "",
        "- completed-anchor region gaps: " + (", ".join(gaps["regions_present_in_registry_but_absent_from_completed_anchors"]) or "none"),
        "- completed-anchor category gaps: " + (", ".join(gaps["categories_present_in_registry_but_absent_from_completed_anchors"]) or "none"),
        "- completed-anchor event-type gaps: " + (", ".join(gaps["event_types_present_in_registry_but_absent_from_completed_anchors"]) or "none"),
        f"- exact-timestamp market rows: **{semantics['exact_timestamp_series_rows']}**",
        f"- source-reported/session-level market rows: **{semantics['source_reported_or_session_market_rows']}**",
        "",
        "The absence of exact-timestamp market evidence remains a measurement gap, not permission to manufacture event times or reconstruct market data from incomplete reporting.",
        "",
        "## Remaining completed frontier",
        "",
    ]

    for row in report["frontier_ranked_by_sample_novelty"]:
        novelty = row["novelty_against_reviewed_sample"]
        lines.append(
            f"- `{row['occurrence_id']}` — {row.get('canonical_name') or row['institution']} — "
            f"{row['region']} / {row['category']} / {row['event_type']}; "
            f"new region={novelty['new_region']}, category={novelty['new_category']}, event type={novelty['new_event_type']}, institution={novelty['new_institution']}"
        )
    if not report["frontier_ranked_by_sample_novelty"]:
        lines.append("- none")

    lines += [
        "",
        "### Frontier interpretation",
        "",
        "Bank of Canada has greater marginal sample novelty than Japan household spending because North America still lacks a reviewed specimen. But neither frontier item repairs a missing completed category or event type. Household spending is particularly duplicative: East Asia is now reviewed, and `MACROECONOMIC_RELEASE` / `DATA_RELEASE` are already well exercised.",
        "",
        "## Evidence diagnostics",
        "",
        f"- referenced evidence rows: **{evidence['referenced_evidence_count']}**",
        f"- primary-official share: **{evidence['primary_official_share_percent']}%**",
    ]
    if evidence.get("top_provider"):
        tp = evidence["top_provider"]
        lines.append(f"- largest single provider: **{tp['provider']}** — {tp['count']} rows / {tp['share_percent']}%")

    lines += [
        "",
        "Provider concentration remains descriptive only; it is not a source-quality quota.",
        "",
        "## Selection recommendation",
        "",
        "1. **First compare upstream historical anchors in still-missing completed categories/event types.** Prefer an existing canonical series with strong first-party post-event evidence over inventing new history.",
        "2. **Keep Bank of Canada live as the strongest frontier candidate.** Promote it only if research can add distinct value — especially defensible high-frequency market measurement or a North America-specific analytical pressure test.",
        "3. **De-prioritise Japan household spending for now.** It is valid but low marginal diversity after AA.",
        "4. Re-audit again before any broad/full-population move. Queue exhaustion is not a research objective.",
        "",
        "AB therefore recommends **upstream category/event-type reconnaissance before the next Analysis write**.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        JSON_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        MD_OUT.write_text(markdown(report), encoding="utf-8")
    print("AUDIT_OK")
    print(json.dumps({
        "checkpoint": report["checkpoint"],
        "readiness": report["readiness"],
        "post_aa_comparison": report["post_aa_comparison"],
        "gaps": report["upstream_population_gaps"],
        "frontier": report["frontier_ranked_by_sample_novelty"],
        "measurement": {
            "exact_timestamp_series_rows": report["analysis_semantics"]["exact_timestamp_series_rows"],
            "source_reported_or_session_market_rows": report["analysis_semantics"]["source_reported_or_session_market_rows"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
