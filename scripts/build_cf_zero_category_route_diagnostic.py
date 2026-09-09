from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "monitor" / "POST_CD_MONITOR_ZERO_CATEGORY_CF_DIAGNOSTIC_v0.1.md"
QUARANTINED_SOURCE_IDS = {"WSSRC-COM-001"}
QUARANTINED_OCCURRENCE_IDS = {"WSO-COM-A-0001", "WSO-COM-A-0002"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    audit = load(ROOT / "data" / "monitor" / "POST_CD_MONITOR_PRESSURE_CF_AUDIT_v0.1.json")
    canonical = load(ROOT / "data" / "canonical" / "registry.json")
    sources = load(ROOT / "data" / "sources" / "registry.json")
    expectations = load(ROOT / "data" / "monitor" / "expectations.json")

    zero_categories = set(audit["diagnostic_prompts"]["canonical_categories_without_configured_monitor_scope"])
    configured_source_ids = {row.get("source_id") for row in expectations.get("adapters", []) if row.get("source_id")}
    source_map = {row.get("source_id"): row for row in sources.get("sources", [])}

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in canonical.get("records", []):
        if row.get("category") not in zero_categories:
            continue
        if row.get("occurrence_id") in QUARANTINED_OCCURRENCE_IDS:
            continue
        grouped[row.get("source_id") or "NO_SOURCE_ID"].append(row)

    entries = []
    for source_id, uses in grouped.items():
        if source_id in QUARANTINED_SOURCE_IDS:
            continue
        source = source_map.get(source_id, {})
        auto = source.get("automated_monitoring_use") or "NOT_RECORDED"
        readiness = source.get("monitoring_readiness_status") or "NOT_RECORDED"
        verification = source.get("verification_mode") or "NOT_RECORDED"
        rights_block = any(token in auto for token in ("PROHIBITED", "HOLD")) or any(
            token in readiness for token in ("RIGHTS", "HOLD")
        )
        endpoint_review = "REVIEW" in auto or "ENDPOINT" in readiness
        entries.append(
            {
                "source_id": source_id,
                "institution": source.get("institution") or "not recorded",
                "jurisdiction": source.get("jurisdiction") or "not recorded",
                "domain": source.get("domain") or "not recorded",
                "readiness": readiness,
                "automated_use": auto,
                "verification_mode": verification,
                "already_configured": source_id in configured_source_ids,
                "rights_block": rights_block,
                "endpoint_review": endpoint_review,
                "categories": sorted({row.get("category") for row in uses if row.get("category")}),
                "regions": sorted({row.get("region") for row in uses if row.get("region")}),
                "series_ids": sorted({row.get("series_id") for row in uses if row.get("series_id")}),
                "occurrence_ids": sorted(row.get("occurrence_id") for row in uses if row.get("occurrence_id")),
                "count": len(uses),
            }
        )

    def rank(row: dict):
        if not row["rights_block"] and not row["endpoint_review"]:
            bucket = 0
        elif not row["rights_block"] and row["endpoint_review"]:
            bucket = 1
        else:
            bucket = 2
        return (bucket, len(row["categories"]), -row["count"], row["source_id"])

    entries.sort(key=rank)

    lines = [
        "# WORLD SIGNALS — CF zero-category Monitor route diagnostic v0.1",
        "",
        "Purpose: inspect the source-governance state behind Canonical occurrences in Monitor categories that currently have zero explicit configured coverage. This is a diagnostic, not a completeness target or permission to automate.",
        "",
        "OPEC remains excluded under `OPEC_QUARANTINE.md`.",
        "",
        "Zero-covered categories: " + ", ".join(sorted(zero_categories)),
        "",
        "| # | Source | Institution | Region(s) | Category | Occ. | Readiness | Automated use | Rights block | Endpoint review |",
        "|---:|---|---|---|---|---:|---|---|---|---|",
    ]
    for idx, row in enumerate(entries, 1):
        lines.append(
            f"| {idx} | `{row['source_id']}` | {row['institution']} | {', '.join(row['regions']) or 'none'} | {', '.join(row['categories'])} | {row['count']} | {row['readiness']} | {row['automated_use']} | {'YES' if row['rights_block'] else 'NO'} | {'YES' if row['endpoint_review'] else 'NO'} |"
        )

    lines.extend(["", "## Detail", ""])
    for idx, row in enumerate(entries, 1):
        lines.extend(
            [
                f"### {idx}. {row['source_id']} — {row['institution']}",
                "",
                f"- jurisdiction: {row['jurisdiction']}",
                f"- domain: {row['domain']}",
                f"- regions: {', '.join(row['regions']) or 'none'}",
                f"- categories: {', '.join(row['categories'])}",
                f"- canonical occurrences: {row['count']}",
                f"- series: {', '.join(row['series_ids']) or 'none'}",
                f"- occurrence ids: {', '.join(row['occurrence_ids'])}",
                f"- monitoring readiness: {row['readiness']}",
                f"- automated monitoring use: {row['automated_use']}",
                f"- verification mode: {row['verification_mode']}",
                f"- already configured Monitor source: {'YES' if row['already_configured'] else 'NO'}",
                f"- rights/automation block detected: {'YES' if row['rights_block'] else 'NO'}",
                f"- endpoint review still required: {'YES' if row['endpoint_review'] else 'NO'}",
                "",
            ]
        )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "source_count": len(entries), "output": str(OUT.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
