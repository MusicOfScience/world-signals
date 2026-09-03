from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from world_signals.coverage import build_coverage_audit
from world_signals.io import load_json

CANONICAL=ROOT/"data/canonical/registry.json"
SOURCES=ROOT/"data/sources/registry.json"
OUTDIR=ROOT/"artifacts/coverage"
JSON_OUT=OUTDIR/"coverage-audit.json"
MD_OUT=OUTDIR/"coverage-audit.md"


def table(rows: list[dict], key: str) -> list[str]:
    lines=[
        f"| {key.replace('_',' ').title()} | Occurrences | Series | Institutions | Sources | Occ/series |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row[key]} | {row['occurrence_count']} | {row['unique_series_count']} | "
            f"{row['unique_institution_count']} | {row['unique_source_count']} | {row['occurrences_per_series']} |"
        )
    return lines


def main() -> int:
    OUTDIR.mkdir(parents=True,exist_ok=True)
    registry=load_json(CANONICAL)
    sources=load_json(SOURCES)
    audit=build_coverage_audit(registry,sources)
    JSON_OUT.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    totals=audit["totals"]
    md=[
        "# WORLD SIGNALS — coverage and bias audit v0.1",
        "",
        f"Canonical registry: **v{audit['canonical_registry_version']}**  ",
        f"Occurrences: **{totals['occurrence_count']}**  ",
        f"Unique series: **{totals['unique_series_count']}**  ",
        f"Unique institutions: **{totals['unique_institution_count']}**  ",
        f"Unique canonical source IDs used: **{totals['unique_source_count']}**  ",
        "",
        "## Method",
        "",
        "Occurrence counts are deliberately **not** treated as coverage quality. A monthly release or central-bank series can generate many rows while representing one institutional signal family. The audit therefore compares occurrences with distinct series, institutions and sources. Threshold flags are review prompts only; they are not quotas.",
        "",
        f"Monetary policy + macroeconomic releases account for **{totals['monetary_plus_macro_occurrence_count']} occurrences ({totals['monetary_plus_macro_occurrence_share']:.1%})** of the current registry.",
        "",
        "## Region shape",
        "",
        *table(audit["by_region"],"region"),
        "",
        "## Category shape",
        "",
        *table(audit["by_category"],"category"),
        "",
        "## Highest-frequency series",
        "",
        "| Series | Occurrences | Region | Category | Institution |",
        "|---|---:|---|---|---|",
    ]
    for row in audit["high_frequency_series"][:25]:
        md.append(
            f"| `{row['series_id']}` | {row['occurrence_count']} | {row['region']} | {row['category']} | {row['institution']} |"
        )
    flags=audit["diagnostic_flags"]
    md += [
        "",
        "## Mechanical review prompts",
        "",
        f"- Regions with fewer than 10 distinct series: **{', '.join(flags['regions_with_fewer_than_10_unique_series']) or 'none'}**.",
        f"- Regions with fewer than 8 distinct institutions: **{', '.join(flags['regions_with_fewer_than_8_unique_institutions']) or 'none'}**.",
        f"- Categories with fewer than 5 distinct series: **{', '.join(flags['categories_with_fewer_than_5_unique_series']) or 'none'}**.",
        "- These are prompts for qualitative institutional/source review, not automatic findings of undercoverage.",
        "",
        "## Next analytical step",
        "",
        "Review the low-diversity regions/categories institution-by-institution against the Charter's systemic-importance standard. Add only missing high-value series with defensible primary sources; do not populate to equalise counts.",
        "",
    ]
    MD_OUT.write_text("\n".join(md),encoding="utf-8")

    print(json.dumps({
        "status":"PASS",
        "canonical_registry_version":audit["canonical_registry_version"],
        "occurrence_count":totals["occurrence_count"],
        "unique_series_count":totals["unique_series_count"],
        "unique_institution_count":totals["unique_institution_count"],
        "unique_source_count":totals["unique_source_count"],
        "monetary_plus_macro_occurrence_share":totals["monetary_plus_macro_occurrence_share"],
        "regions_with_fewer_than_10_unique_series":flags["regions_with_fewer_than_10_unique_series"],
        "regions_with_fewer_than_8_unique_institutions":flags["regions_with_fewer_than_8_unique_institutions"],
        "categories_with_fewer_than_5_unique_series":flags["categories_with_fewer_than_5_unique_series"],
        "top_regions":audit["by_region"],
        "top_categories":audit["by_category"],
        "top_high_frequency_series":audit["high_frequency_series"][:15],
        "artifact_json":str(JSON_OUT.relative_to(ROOT)),
        "artifact_markdown":str(MD_OUT.relative_to(ROOT)),
    },indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
