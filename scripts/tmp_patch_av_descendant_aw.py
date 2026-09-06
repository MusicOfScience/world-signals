from pathlib import Path

path = Path('tests/test_live_intelligence_foundation_av.py')
text = path.read_text(encoding='utf-8')
replacements = {
    'observations["observations"][0]["canonical_links"][0]["occurrence_id"] = "WSO-DOES-NOT-EXIST"': 'row["canonical_links"][0]["occurrence_id"] = "WSO-DOES-NOT-EXIST"',
    'observations["observations"][0]["event_time"]["event_timezone"] = "Asia/Tokyo"': 'row["event_time"]["event_timezone"] = "Asia/Tokyo"',
    'del observations["observations"][0]["revision_target_description"]': 'del revision["revision_target_description"]',
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f'expected exactly one occurrence of {old!r}; found {text.count(old)}')
    text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
print('AV descendant synthetic-row indexing repaired for AW')
