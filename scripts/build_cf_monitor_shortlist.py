from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "monitor" / "POST_CD_MONITOR_PRESSURE_CF_AUDIT_v0.1.json"
OUT = ROOT / "data" / "monitor" / "POST_CD_MONITOR_PRESSURE_CF_SHORTLIST_v0.1.md"

QUARANTINED_SOURCE_IDS = {"WSSRC-COM-001"}
QUARANTINED_OCCURRENCE_IDS = {"WSO-COM-A-0001", "WSO-COM-A-0002"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    audit = load(AUDIT)
    canonical = load(ROOT / "data" / "canonical" / "registry.json")

    zero_categories = set(audit["diagnostic_prompts"]["canonical_categories_without_configured_monitor_scope"])
    region_rows = {row["region"]: row for row in audit["by_region"]}
    occurrence_map = {row["occurrence_id"]: row for row in canonical["records"]}
    source_uses: dict[str, list[dict]] = {}
    for row in canonical["records"]:
        source_id = row.get("source_id")
        if source_id:
            source_uses.setdefault(source_id, []).append(row)

    rows = []
    for candidate in audit["candidate_sources_with_canonical_dependencies"]:
        source_id = candidate.get("source_id")
        if candidate.get("already_configured_monitor_source"):
            continue
        if source_id in QUARANTINED_SOURCE_IDS:
            continue

        uses = [
            row for row in source_uses.get(source_id, [])
            if row.get("occurrence_id") not in QUARANTINED_OCCURRENCE_IDS
        ]
        if not uses:
            continue

        categories = sorted({row.get("category") for row in uses if row.get("category")})
        regions = sorted({row.get("region") for row in uses if row.get("region")})
        zero_hits = sorted(set(categories) & zero_categories)
        region_floor = min(
            (region_rows[region]["configured_monitor_unique_series_count"] for region in regions if region in region_rows),
            default=999,
        )
        automated_use = candidate.get("automated_monitoring_use") or "NOT_RECORDED"
        readiness = candidate.get("monitoring_readiness_status") or "NOT_RECORDED"
        rights_hold = (
            "PROHIBITED" in automated_use
            or "HOLD" in automated_use
            or "RIGHTS_PENDING" in readiness
        )

        rank = (
            0 if zero_hits and not rights_hold else
            1 if zero_hits else
            2 if not rights_hold else
            3,
            region_floor,
            -len(uses),
            source_id or "",
        )
        rows.append(
            {
                "rank": rank,
                "source_id": source_id,
                "institution": candidate.get("institution"),
                "jurisdiction": candidate.get("jurisdiction"),
                "readiness": readiness,
                "automated_use": automated_use,
                "verification_mode": candidate.get("verification_mode"),
                "canonical_occurrences": len(uses),
                "series_ids": sorted({row.get("series_id") for row in uses if row.get("series_id")}),
                "regions": regions,
                "categories": categories,
                "zero_category_hits": zero_hits,
                "region_floor": region_floor,
                "rights_hold": rights_hold,
                "occurrence_ids": sorted(row["occurrence_id"] for row in uses),
            }
        )

    rows.sort(key=lambda row: row["rank"])

    lines = [
        "# WORLD SIGNALS — CF Monitor candidate shortlist v0.1",
        "",
        "This is a source-aware diagnostic shortlist derived from the post-CD Monitor coverage audit. It is **not** a completeness score and does not authorise a route.",
        "",
        "Selection rules:",
        "- OPEC source `WSSRC-COM-001` and occurrences `WSO-COM-A-0001` / `WSO-COM-A-0002` are excluded under `OPEC_QUARANTINE.md`.",
        "- Existing configured Monitor sources are excluded; this is a new-route pressure check.",
        "- A zero-covered category is a review prompt, not a quota.",
        "- Source readiness and rights outrank geographic/category balancing.",
        "- Rights-held candidates remain visible only after route-viable candidates.",
        "",
        "Current zero-covered Monitor categories: " + ", ".join(sorted(zero_categories)),
        "",
        "| # | Source | Institution | Region(s) | Category gap | Canonical occ. | Readiness | Automated use | Rights hold |",
        "|---:|---|---|---|---|---:|---|---|---|",
    ]

    for idx, row in enumerate(rows, start=1):
        lines.append(
            "| {idx} | `{source}` | {institution} | {regions} | {gaps} | {count} | {readiness} | {auto} | {hold} |".format(
                idx=idx,
                source=row["source_id"],
                institution=row["institution"] or "not recorded",
                regions=", ".join(row["regions"]) or "none",
                gaps=", ".join(row["zero_category_hits"]) or "—",
                count=row["canonical_occurrences"],
                readiness=row["readiness"],
                auto=row["automated_use"],
                hold="YES" if row["rights_hold"] else "NO",
            )
        )

    lines.extend(["", "## Candidate details", ""])
    for idx, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"### {idx}. {row['source_id']} — {row['institution'] or 'institution not recorded'}",
                "",
                f"- jurisdiction: {row['jurisdiction'] or 'not recorded'}",
                f"- regions: {', '.join(row['regions']) or 'none'}",
                f"- categories: {', '.join(row['categories']) or 'none'}",
                f"- zero-covered category hits: {', '.join(row['zero_category_hits']) or 'none'}",
                f"- canonical occurrences: {row['canonical_occurrences']}",
                f"- series: {', '.join(row['series_ids']) or 'none'}",
                f"- occurrence ids: {', '.join(row['occurrence_ids'])}",
                f"- readiness: {row['readiness']}",
                f"- automated monitoring use: {row['automated_use']}",
                f"- verification mode: {row['verification_mode'] or 'not recorded'}",
                f"- rights/automation hold: {'YES' if row['rights_hold'] else 'NO'}",
                "",
            ]
        )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "candidate_count": len(rows), "output": str(OUT.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
