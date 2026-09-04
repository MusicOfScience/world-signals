#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.source_governance_audit import build_source_governance_audit

CANONICAL = ROOT / "data/canonical/registry.json"
SOURCES = ROOT / "data/sources/registry.json"
EXPECTATIONS = ROOT / "data/monitor/expectations.json"
AS_OF = date(2026, 9, 5)


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def parse_day(record: dict):
    for key in ("start_local", "date_earliest", "publication_datetime", "start_utc"):
        raw = record.get(key)
        if not raw:
            continue
        s = str(raw)[:10]
        try:
            return date.fromisoformat(s)
        except ValueError:
            pass
    return None


def is_active(record: dict) -> bool:
    lifecycle = str(record.get("lifecycle_status") or "").upper()
    certainty = str(record.get("certainty_status") or "").upper()
    if lifecycle in {"COMPLETED", "CANCELLED"}:
        return False
    if certainty == "CANCELLED":
        return False
    return True


def compact_event(r: dict):
    return {
        "occurrence_id": r.get("occurrence_id"),
        "canonical_name": r.get("canonical_name"),
        "category": r.get("category"),
        "jurisdiction": r.get("jurisdiction"),
        "institution": r.get("institution"),
        "day": parse_day(r).isoformat() if parse_day(r) else None,
        "certainty_status": r.get("certainty_status"),
        "lifecycle_status": r.get("lifecycle_status"),
        "timing_type": r.get("timing_type"),
    }


canonical = load(CANONICAL)
sources = load(SOURCES)
expectations = load(EXPECTATIONS)
audit = build_source_governance_audit(canonical, sources, expectations)
source_by_id = {s.get("source_id"): s for s in sources.get("sources", [])}
events_by_source = defaultdict(list)
for r in canonical.get("records", []):
    if r.get("source_id"):
        events_by_source[r["source_id"]].append(r)

p1 = [r for r in audit["backfill_research_queue"] if r["research_priority"] == "P1_CANONICAL_DEPENDENCY"]
if len(p1) != 87:
    raise SystemExit(f"Expected 87 P1 rows, got {len(p1)}")

field_shapes = Counter()
jurisdiction_sources = Counter()
domain_sources = Counter()
jurisdiction_deps = Counter()
domain_deps = Counter()
rows = []
for a in p1:
    sid = a["source_id"]
    s = source_by_id[sid]
    deps = events_by_source[sid]
    active = [r for r in deps if is_active(r)]
    future = [r for r in active if parse_day(r) is None or parse_day(r) >= AS_OF]
    dated_future = [r for r in future if parse_day(r)]
    next_day = min((parse_day(r) for r in dated_future), default=None)
    within90 = sum(1 for r in dated_future if AS_OF <= parse_day(r) <= AS_OF + timedelta(days=90))
    within180 = sum(1 for r in dated_future if AS_OF <= parse_day(r) <= AS_OF + timedelta(days=180))
    within365 = sum(1 for r in dated_future if AS_OF <= parse_day(r) <= AS_OF + timedelta(days=365))
    undated_active = sum(1 for r in future if parse_day(r) is None)
    shape = tuple(a["missing_governance_fields"])
    field_shapes[shape] += 1
    jur = str(s.get("jurisdiction") or a.get("jurisdiction") or "UNKNOWN")
    dom = str(s.get("domain") or a.get("domain") or "UNKNOWN")
    jurisdiction_sources[jur] += 1
    domain_sources[dom] += 1
    jurisdiction_deps[jur] += len(deps)
    domain_deps[dom] += len(deps)
    rows.append({
        "source_id": sid,
        "institution": s.get("institution"),
        "jurisdiction": jur,
        "domain": dom,
        "source_type": s.get("source_type"),
        "source_url": s.get("url") or s.get("source_url") or s.get("authoritative_url") or s.get("endpoint"),
        "machine_readable_available": s.get("machine_readable_available"),
        "missing": list(shape),
        "dependency_count": len(deps),
        "active_count": len(active),
        "future_or_undated_active_count": len(future),
        "within_90d": within90,
        "within_180d": within180,
        "within_365d": within365,
        "undated_active": undated_active,
        "next_day": next_day.isoformat() if next_day else None,
        "event_categories": dict(Counter(str(r.get("category") or "UNKNOWN") for r in deps)),
        "next_events": [compact_event(r) for r in sorted(dated_future, key=lambda x: parse_day(x))[:4]],
    })

# Mechanical ordering only; not a selection rule.
rows.sort(key=lambda r: (
    -int(r["within_90d"] > 0),
    -r["within_90d"],
    -r["within_180d"],
    -r["future_or_undated_active_count"],
    -r["dependency_count"],
    r["source_id"],
))

out = {
    "checkpoint": {
        "canonical_version": canonical.get("version"),
        "canonical_count": len(canonical.get("records", [])),
        "source_version": sources.get("version"),
        "source_count": len(sources.get("sources", [])),
        "p1_count": len(p1),
        "as_of": AS_OF.isoformat(),
    },
    "field_shape_counts": {" + ".join(k): v for k, v in sorted(field_shapes.items(), key=lambda kv: (-kv[1], kv[0]))},
    "unresolved_p1_source_concentration_by_jurisdiction": jurisdiction_sources.most_common(),
    "unresolved_p1_dependency_concentration_by_jurisdiction": jurisdiction_deps.most_common(),
    "unresolved_p1_source_concentration_by_domain": domain_sources.most_common(),
    "unresolved_p1_dependency_concentration_by_domain": domain_deps.most_common(),
    "mechanical_top_40": rows[:40],
    "all_p1_rows": rows,
}
print(json.dumps(out, indent=2, ensure_ascii=False))
