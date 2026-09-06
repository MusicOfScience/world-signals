from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.monitor_coverage import build_monitor_coverage_audit


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    registry = load(ROOT / "data" / "canonical" / "registry.json")
    sources = load(ROOT / "data" / "sources" / "registry.json")
    expectations = load(ROOT / "data" / "monitor" / "expectations.json")
    audit = build_monitor_coverage_audit(registry, sources, expectations)

    out_dir = ROOT / "artifacts" / "monitor"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "monitor-coverage-audit.json"
    markdown_path = out_dir / "monitor-coverage-audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# WORLD SIGNALS — monitor coverage audit v{audit['version']}",
        "",
        f"Canonical registry: **v{audit['canonical_registry_version']}**",
        f"Source registry: **v{audit['source_registry_version']}**",
        f"Monitor expectations: **v{audit['monitor_expectations_version']}**",
        "",
        "## Methodological boundary",
        "",
        "This is a read-only audit of explicitly configured Source/Change Monitor scope. It is not a monitor-completeness score and does not authorise route creation, source promotion or canonical writes.",
        "",
        "- Occurrence density is not route diversity.",
        "- Missing regions or categories are qualitative review prompts, not quotas.",
        "- Only explicit `canonical_occurrence_ids` are counted; the audit does not infer scope from a series.",
        "- Source rights and monitoring readiness remain separate constraints on route viability.",
        "",
        "## Configured scope",
        "",
    ]
    for key, value in audit["totals"].items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "## Configured source readiness", ""])
    for key, counts in audit["configured_source_readiness"].items():
        lines.append(f"### {key}")
        lines.append("")
        for label, count in counts.items():
            lines.append(f"- {label}: {count}")
        lines.append("")

    lines.extend(["## Diagnostic prompts", ""])
    prompts = audit["diagnostic_prompts"]
    regions = prompts["canonical_regions_without_configured_monitor_scope"]
    categories = prompts["canonical_categories_without_configured_monitor_scope"]
    lines.append("Regions with canonical signals but no explicit configured monitor occurrence scope: " + (", ".join(regions) if regions else "none"))
    lines.append("")
    lines.append("Categories with canonical signals but no explicit configured monitor occurrence scope: " + (", ".join(categories) if categories else "none"))
    lines.append("")
    lines.append(prompts["note"])

    lines.extend(["", "## Region scope", "", "| Region | Canonical series | Monitored occurrences | Monitored series | Monitored institutions |", "|---|---:|---:|---:|---:|"])
    for row in audit["by_region"]:
        lines.append(
            f"| {row['region']} | {row['canonical_unique_series_count']} | {row['configured_monitor_occurrence_count']} | {row['configured_monitor_unique_series_count']} | {row['configured_monitor_unique_institution_count']} |"
        )

    lines.extend(["", "## Category scope", "", "| Category | Canonical series | Monitored occurrences | Monitored series | Monitored institutions |", "|---|---:|---:|---:|---:|"])
    for row in audit["by_category"]:
        lines.append(
            f"| {row['category']} | {row['canonical_unique_series_count']} | {row['configured_monitor_occurrence_count']} | {row['configured_monitor_unique_series_count']} | {row['configured_monitor_unique_institution_count']} |"
        )

    lines.extend(["", "## Adapter inventory", ""])
    for row in audit["adapter_inventory"]:
        scope = row["scope"]
        lines.extend(
            [
                f"### {row['adapter_id']}",
                "",
                f"- source: `{row['source_id']}` — {row.get('source_institution') or 'institution not recorded'}",
                f"- role: {row.get('monitor_role') or 'not recorded'}",
                f"- cadence: {row.get('cadence') or 'not recorded'}",
                f"- explicit occurrences: {scope['occurrence_count']}",
                f"- scoped series: {scope['unique_series_count']}",
                f"- regions: {', '.join(row['regions']) or 'none'}",
                f"- categories: {', '.join(row['categories']) or 'none'}",
                f"- readiness: {row.get('monitoring_readiness_status') or 'not recorded'}",
                f"- automated monitoring use: {row.get('automated_monitoring_use') or 'not recorded'}",
                "",
            ]
        )

    lines.extend(["## Candidate source holdings", ""])
    lines.append("These are source-governance states only. Inclusion here does not authorise a route.")
    lines.append("")
    lines.append(f"- candidate/pilot/endpoint-status sources with current canonical dependencies: **{len(audit['candidate_sources_with_canonical_dependencies'])}**")
    lines.append(f"- candidate/pilot/endpoint-status source holdings with no current canonical dependency: **{len(audit['candidate_sources_without_canonical_dependencies'])}**")
    lines.append("")

    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "PASS",
                "version": audit["version"],
                "canonical_registry_version": audit["canonical_registry_version"],
                "totals": audit["totals"],
                "diagnostic_prompts": audit["diagnostic_prompts"],
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
