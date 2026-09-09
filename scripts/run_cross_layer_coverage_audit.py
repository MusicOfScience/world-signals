from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.cross_layer_coverage import build_cross_layer_coverage_audit


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    audit = build_cross_layer_coverage_audit(
        load(ROOT / "data" / "canonical" / "registry.json"),
        load(ROOT / "data" / "monitor" / "expectations.json"),
        load(ROOT / "data" / "live_intelligence" / "observations.json"),
        load(ROOT / "data" / "analysis" / "event_reviews.json"),
    )

    out_dir = ROOT / "artifacts" / "coverage"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cross-layer-coverage-audit.json"
    markdown_path = out_dir / "cross-layer-coverage-audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals = audit["totals"]
    bridge = audit["bridge_frontier"]
    prompts = audit["diagnostic_prompts"]
    region_comparison = audit["region_comparison"]

    lines = [
        f"# WORLD SIGNALS — cross-layer coverage / pressure audit v{audit['version']}",
        "",
        "## Boundary",
        "",
        "This is a read-only diagnostic across Canonical → Monitor → Live Intelligence → Analysis. It does not create a blended coverage score, population quota, route recommendation or write authority.",
        "",
        "Canonical categories and Live domain tags remain distinct taxonomies. Downstream absence is a review prompt only.",
        "",
        "## Region-comparison boundary",
        "",
        "Live may use a finer regional label than Canonical. Comparison prompts therefore use only the explicit audit-only equivalences below; raw governed labels remain unchanged and are retained in the JSON artifact.",
        "",
    ]
    for live_region, comparison_region in region_comparison["live_to_canonical_equivalence"].items():
        lines.append(f"- `{live_region}` → `{comparison_region}` for audit comparison only.")
    lines.extend(
        [
            "",
            region_comparison["note"],
            "",
            "## Current layer shape",
            "",
            f"- Canonical: **{totals['canonical_occurrence_count']} occurrences / {totals['canonical_unique_series_count']} series**.",
            f"- Monitor: **{totals['configured_monitor_adapter_count']} adapters / {totals['configured_monitor_scoped_occurrence_count']} explicitly scoped occurrences / {totals['configured_monitor_scoped_series_count']} series**.",
            f"- Live Intelligence: **{totals['live_observation_count']} observations / {totals['canonical_linked_live_observation_count']} Canonical-linked**.",
            f"- Analysis: **{totals['analysis_review_count']} reviews / {totals['production_live_input_count']} production Live inputs / {totals['production_revision_count']} production revisions**.",
            "",
            "## Live → Analysis frontier",
            "",
            f"- Used Live observation IDs: **{len(bridge['used_live_observation_ids'])}**.",
            f"- Completed linked observations with an existing Analysis target and not yet used: **{len(bridge['completed_linked_with_existing_analysis_unconsumed'])}**.",
            f"- Completed linked observations without an Analysis review: **{len(bridge['completed_linked_without_analysis_review'])}**.",
            f"- Linked observations whose target is not completed: **{len(bridge['noncompleted_linked_unconsumed'])}**.",
            f"- Unlinked Live observations: **{len(bridge['unlinked_live_observation_ids'])}**.",
            "",
            bridge["note"],
            "",
            "## Regional cross-layer shape",
            "",
            "| Comparison region | Canonical occurrences | Canonical series | Monitor occurrences | Monitor series | Live obs | Raw Live labels | Linked Live | Analysis reviews | Analysis + Live input |",
            "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|",
        ]
    )

    for row in audit["by_region"]:
        raw_labels = ", ".join(row["raw_live_region_labels"]) or "—"
        lines.append(
            f"| {row['region']} | {row['canonical_occurrence_count']} | {row['canonical_unique_series_count']} | "
            f"{row['configured_monitor_occurrence_count']} | {row['configured_monitor_unique_series_count']} | "
            f"{row['live_observation_count']} | {raw_labels} | {row['canonical_linked_live_observation_count']} | "
            f"{row['analysis_review_count']} | {row['analysis_with_live_input_count']} |"
        )

    lines.extend(
        [
            "",
            "## Canonical-category downstream shape",
            "",
            "| Canonical category | Canonical occurrences | Canonical series | Monitor occurrences | Monitor series | Analysis reviews | Analysis + Live input |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in audit["by_canonical_category"]:
        lines.append(
            f"| {row['category']} | {row['canonical_occurrence_count']} | {row['canonical_unique_series_count']} | "
            f"{row['configured_monitor_occurrence_count']} | {row['configured_monitor_unique_series_count']} | "
            f"{row['analysis_review_count']} | {row['analysis_with_live_input_count']} |"
        )

    lines.extend(["", "## Live domain tags", ""])
    for row in audit["live_by_domain_tag"]:
        lines.append(f"- {row['domain_tag']}: {row['live_observation_count']}")

    lines.extend(
        [
            "",
            "## Mechanical review prompts",
            "",
            "These are not findings of undercoverage and do not authorise population.",
            "",
            "- Canonical regions with no configured Monitor scope: "
            + (", ".join(prompts["regions_with_canonical_series_but_no_configured_monitor_scope"]) or "none"),
            "- Canonical regions with no Live observation: "
            + (", ".join(prompts["regions_with_canonical_series_but_no_live_observation"]) or "none"),
            "- Regions with Live observation but no Analysis review: "
            + (", ".join(prompts["regions_with_live_observation_but_no_analysis_review"]) or "none"),
            "- Canonical categories with no configured Monitor scope: "
            + (", ".join(prompts["canonical_categories_without_configured_monitor_scope"]) or "none"),
            "- Canonical categories with no Analysis review: "
            + (", ".join(prompts["canonical_categories_without_analysis_review"]) or "none"),
            "",
            prompts["note"],
            "",
            "## Next-use rule",
            "",
            "Use this artifact with the Charter and current source/rights evidence to choose the next bounded tranche. Do not select from any list here mechanically. OPEC CE quarantine remains outside ordinary pressure selection.",
            "",
        ]
    )

    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "PASS",
                "dataset": audit["dataset"],
                "version": audit["version"],
                "checkpoints": audit["checkpoints"],
                "totals": totals,
                "region_comparison": region_comparison,
                "bridge_frontier": bridge,
                "diagnostic_prompts": prompts,
                "artifact_json": str(json_path.relative_to(ROOT)),
                "artifact_markdown": str(markdown_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
