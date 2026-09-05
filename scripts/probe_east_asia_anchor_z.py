#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
LEDGER = ROOT / "data/changes/ledger.json"
REFERENCE_DATE = "2026-09-06"
TARGET_IDS = ("WSO-FIS-A-0015", "WSO-MAC-B-0041")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_source_ids(value):
    out = set()
    if isinstance(value, dict):
        for child in value.values():
            out |= collect_source_ids(child)
    elif isinstance(value, list):
        for child in value:
            out |= collect_source_ids(child)
    elif isinstance(value, str) and value.startswith("WSSRC-"):
        out.add(value)
    return out


def date_prefix(row):
    for key in ("start_local", "end_local", "canonical_date", "date"):
        value = row.get(key)
        if isinstance(value, str) and len(value) >= 10 and value[:4].isdigit():
            return value[:10], key
    return None, None


def slim(row):
    date, date_field = date_prefix(row)
    return {
        "occurrence_id": row.get("occurrence_id"),
        "series_id": row.get("series_id"),
        "canonical_name": row.get("canonical_name"),
        "institution": row.get("institution"),
        "jurisdiction": row.get("jurisdiction"),
        "region": row.get("region"),
        "category": row.get("category"),
        "event_type": row.get("event_type"),
        "lifecycle_status": row.get("lifecycle_status"),
        "certainty_status": row.get("certainty_status"),
        "time_status": row.get("time_status"),
        "date_status": row.get("date_status"),
        "date": date,
        "date_field": date_field,
        "start_local": row.get("start_local"),
        "end_local": row.get("end_local"),
        "source_timezone": row.get("source_timezone"),
        "start_utc": row.get("start_utc"),
        "source_id": row.get("source_id"),
        "source_ids": sorted(collect_source_ids(row)),
    }


def main():
    canonical = load(CANONICAL)
    sources = load(SOURCES)
    ledger = load(LEDGER)
    records = canonical.get("records", [])
    by_id = {r.get("occurrence_id"): r for r in records}
    east = [r for r in records if r.get("region") == "East Asia"]

    past = []
    for row in east:
        date, _ = date_prefix(row)
        if date and date < REFERENCE_DATE:
            past.append(row)

    past_not_completed = [r for r in past if r.get("lifecycle_status") != "COMPLETED"]
    past_2026_not_completed = [r for r in past_not_completed if (date_prefix(r)[0] or "").startswith("2026-")]
    electionish = [
        r for r in east
        if r.get("category") == "ELECTIONS_GOVERNANCE"
        or "ELECTION" in str(r.get("event_type") or "")
        or "election" in str(r.get("canonical_name") or "").lower()
    ]

    refs = set()
    for row in past_2026_not_completed + electionish:
        refs |= collect_source_ids(row)
    source_map = {s.get("source_id"): s for s in sources.get("sources", [])}
    relevant_sources = []
    for sid in sorted(refs):
        s = source_map.get(sid)
        if not s:
            relevant_sources.append({"source_id": sid, "missing": True})
            continue
        relevant_sources.append({
            "source_id": sid,
            "institution": s.get("institution"),
            "jurisdiction": s.get("jurisdiction"),
            "domain": s.get("domain"),
            "endpoint_role": s.get("endpoint_role"),
            "authoritative_url": s.get("authoritative_url"),
            "source_type": s.get("source_type"),
            "canonical_provenance_use": s.get("canonical_provenance_use"),
            "automated_monitoring_use": s.get("automated_monitoring_use"),
            "verification_mode": s.get("verification_mode"),
            "activation_status": s.get("activation_status"),
        })

    payload = {
        "project": "WORLD SIGNALS",
        "probe": "EAST_ASIA_ANCHOR_Z_LIFECYCLE",
        "reference_date": REFERENCE_DATE,
        "canonical": {
            "version": canonical.get("version"),
            "count": len(records),
            "record_count_field": canonical.get("record_count"),
            "reference_date": canonical.get("reference_date"),
        },
        "sources": {"version": sources.get("version"), "count": len(sources.get("sources", []))},
        "ledger": {
            "version": ledger.get("version"),
            "count": len(ledger.get("changes", [])),
            "reference_date": ledger.get("reference_date"),
            "tail": ledger.get("changes", [])[-3:],
        },
        "east_asia": {
            "occurrence_count": len(east),
            "lifecycle_distribution": dict(sorted(Counter(str(r.get("lifecycle_status")) for r in east).items())),
            "category_distribution": dict(sorted(Counter(str(r.get("category")) for r in east).items())),
            "event_type_distribution": dict(sorted(Counter(str(r.get("event_type")) for r in east).items())),
            "past_dated_count": len(past),
            "past_dated_not_completed_count": len(past_not_completed),
            "past_2026_not_completed_count": len(past_2026_not_completed),
        },
        "past_2026_not_completed": [slim(r) for r in sorted(past_2026_not_completed, key=lambda r: (date_prefix(r)[0] or "", str(r.get("occurrence_id"))))],
        "target_full_records": {oid: by_id.get(oid) for oid in TARGET_IDS},
        "electionish": [slim(r) for r in sorted(electionish, key=lambda r: ((date_prefix(r)[0] or "9999"), str(r.get("occurrence_id"))))],
        "relevant_sources": relevant_sources,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
