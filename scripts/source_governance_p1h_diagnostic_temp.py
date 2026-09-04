#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from world_signals.source_governance_audit import build_source_governance_audit

registry = json.loads((ROOT / 'data/canonical/registry.json').read_text())
sources = json.loads((ROOT / 'data/sources/registry.json').read_text())
expectations = json.loads((ROOT / 'data/monitor/expectations.json').read_text())
audit = build_source_governance_audit(registry, sources, expectations)
reference = date.fromisoformat(registry.get('reference_date', '2026-09-04'))

records_by_source = defaultdict(list)
for record in registry.get('records', []):
    sid = record.get('source_id')
    if sid:
        records_by_source[sid].append(record)


def candidate_date(record):
    for key in ('start_utc', 'start_local', 'publication_datetime', 'date_earliest', 'date_latest'):
        value = record.get(key)
        if not value:
            continue
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00')).date()
        except ValueError:
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                pass
    return None


def jurisdiction_values(record):
    value = record.get('jurisdiction')
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []

rows = []
for row in audit['backfill_research_queue']:
    if row['research_priority'] != 'P1_CANONICAL_DEPENDENCY':
        continue
    recs = records_by_source.get(row['source_id'], [])
    lifecycle = Counter(str(r.get('lifecycle_status') or 'UNRECORDED') for r in recs)
    active = [r for r in recs if r.get('lifecycle_status') not in ('COMPLETED', 'CANCELLED')]
    active_dates = [d for r in active if (d := candidate_date(r)) and d >= reference]
    within_90 = [d for d in active_dates if (d - reference).days <= 90]
    regions = Counter(str(r.get('region') or 'UNRECORDED') for r in recs)
    categories = Counter(str(r.get('category') or 'UNRECORDED') for r in recs)
    jurisdictions = Counter(j for r in recs for j in jurisdiction_values(r))
    visibility = Counter(str(r.get('visibility_tier') or 'UNRECORDED') for r in recs)
    rows.append({
        **row,
        'active_noncompleted_dependency_count': len(active),
        'active_dated_within_90d_count': len(within_90),
        'earliest_active_date': min(active_dates).isoformat() if active_dates else None,
        'lifecycle_counts': dict(lifecycle),
        'canonical_regions': dict(regions),
        'canonical_categories': dict(categories),
        'canonical_jurisdictions': dict(jurisdictions),
        'visibility_tiers': dict(visibility),
    })

rows.sort(key=lambda r: (
    -r['active_dated_within_90d_count'],
    -r['active_noncompleted_dependency_count'],
    -r['canonical_occurrence_dependency_count'],
    str(r['source_id']),
))

region_totals = Counter()
category_totals = Counter()
for row in rows:
    region_totals.update(row['canonical_regions'])
    category_totals.update(row['canonical_categories'])

out = {
    'project': 'WORLD SIGNALS',
    'diagnostic': 'P1_H_SELECTION_DIAGNOSTIC',
    'base': {
        'canonical_version': registry.get('version'),
        'canonical_count': registry.get('record_count', len(registry.get('records', []))),
        'source_version': sources.get('version'),
        'source_count': sources.get('source_count', len(sources.get('sources', []))),
        'reference_date': reference.isoformat(),
        'p1_count': len(rows),
    },
    'selection_rule': 'Diagnostic ranking only: active 90-day horizon, then active noncompleted dependencies, then total dependency. Final cohort must also consider source-scope integrity, regional/domain balance and governance-information value; no permission inference.',
    'top_40': rows[:40],
    'p1_region_dependency_totals': dict(region_totals),
    'p1_category_dependency_totals': dict(category_totals),
}
print(json.dumps(out, indent=2, sort_keys=True))
