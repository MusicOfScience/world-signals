from pathlib import Path

p = Path('PROJECT_STATUS.md')
s = p.read_text()

replacements = [
    ('- **Canonical occurrence registry:** v0.21 — **669 occurrences**.', '- **Canonical occurrence registry:** v0.22 — **669 occurrences**.'),
    ('- **Tier-1 source registry:** v1.62 — **224 sources**.', '- **Tier-1 source registry:** v1.63 — **225 sources**.'),
    ('- **Reviewed change ledger:** v0.10.', '- **Reviewed change ledger:** v0.11.'),
]
for old, new in replacements:
    if s.count(old) != 1:
        raise SystemExit(f'checkpoint scalar match count != 1: {old}')
    s = s.replace(old, new)

start = s.index('### Latest observed post-contract evidence\n')
end = s.index('\nThe review-state contract activated prospectively after run 47', start)
new_block = '''### Latest observed post-contract evidence

Run **59** / GitHub run id `33911315209`, recorded `2026-09-04T19:28:18.141283+00:00`, ran automatically after Vietnam Source-Scope Repair A merged on exact main commit `1c05406f810caebbb004ccad339d034a3aaa4cc0`:

- configuration canonical **v0.22 / 669** / source **v1.63 / 225** / expectations **v0.7** / operations policy **v0.1**;
- **6 healthy / 0 degraded** source adapters;
- all **6 expected adapters observed**, with no missing or unexpected adapters;
- **0 review candidates**;
- `NO_CHANGE`;
- canonical hash unchanged before/after;
- automatic canonical commit **false**;
- Google Calendar write **false**;
- configuration fingerprint `44f3e3cffd6b2596f2a396ca35790ef24e4df552abeb838f2322e4c0c3066ff4`.

This is the first live-monitor observation on the Vietnam-repaired canonical/source checkpoint. It closes configuration alignment on v0.22/v1.63. The initial push-triggered Pages run `33911315259` was cancelled by concurrency when the monitor-completion deployment superseded it; successor Pages run `33911351490` completed successfully on the same main commit. This is normal workflow supersession, not a deployment incident.

### Vietnam Source-Scope Repair A — COMPLETE

`WSO-REG-G-0001` remains the same **PROVISIONAL** occurrence on **20 October 2026**. Canonical provenance now points to first-order National Assembly source `WSSRC-REG5-002`; Government Electronic Newspaper source `WSSRC-REG5-001` remains historical/secondary official evidence. No canonical timing field changed. Governance state after the repair is **67 fully explicit / 158 incomplete / 87 P1 / 71 P2**. Durable closeout: `data/coverage/VIETNAM_SOURCE_SCOPE_REPAIR_A_AUDIT_v0.1.md`.
'''
s = s[:start] + new_block + s[end:]
p.write_text(s)
