#!/usr/bin/env python3
from pathlib import Path

path = Path('PROJECT_STATUS.md')
text = path.read_text(encoding='utf-8')

old_backlog = '''### Source-governance P1/P2 backlog

**103 P1 canonical-dependent** and **71 P2 registry-only** source records still need bounded, evidence-specific governance research. Prioritise small tranches by live analytical relevance, dependency and active horizon; never infer rights from public accessibility, official status, machine readability or successful parsing.
'''
new_backlog = '''### Source-governance P1/P2 backlog

**103 P1 canonical-dependent** and **71 P2 registry-only** source records still need bounded, evidence-specific governance research. Prioritise small tranches by live analytical relevance, dependency and active horizon; never infer rights from public accessibility, official status, machine readability or successful parsing.

P1-H selection/research is now frozen for OPEC (`WSSRC-COM-001`), Japan ESRI GDP (`WSSRC-MAC-016`), RBI (`WSSRC-CB-011`), SARB (`WSSRC-REG-006`), Mexico constitutional budget deadlines (`WSSRC-REG-010`) and UNGA 81st-session scheduling (`WSSRC-INT-001`) — **16 canonical dependencies** across Global, East Asia, South Asia, Africa and Latin America. This intentionally trades raw dependency count for active-horizon, source-scope, regional and domain balance. No registry mutation is authorised by the research freeze.
'''

old_next = '''1. **Source-governance P1-H selection diagnostic** — re-run/inspect the current 103-source P1 queue and choose any next bounded research cohort by active horizon, canonical dependency, source-scope integrity, regional breadth, domain diversity and governance-information value. Do not mechanically roll into another six-source tranche.
2. **Held provenance-scope repairs** — treat Brazil TSE `WSSRC-EL-BR-001` and SNB `WSSRC-CB-009` separately; neither may receive governance backfill until the provenance relationship/source scope is repaired and reviewed.
3. **Biosecurity candidate-node research** — assess marginal analytical value + authoritative timing + rights one institution/system at a time; architecture does not authorise population.
4. **South Asia provenance resolution** — continue precise authoritative-date/native-calendar work.
5. Re-run coverage audit after analytically justified canonical additions only.
6. Continue **Live Intelligence v1** using aligned canonical + monitor + retained-review evidence: WHAT HAPPENED / EXPECTED / SURPRISED / MOVED / CONNECTIONS / NOISE / ALTERNATIVES / SECOND-ORDER; do not infer causality from temporal coincidence.
7. Keep the **canonical auto-commit gate CLOSED** until genuine prospective reschedule and explicit cancellation evidence satisfy the existing real-world gates; healthy monitoring is not mutation authority.
8. Continue **Analysis v1** once the live-intelligence evidence contract is stable.
'''
new_next = '''1. **Source-governance P1-H transaction gate** — review/merge the frozen P1-H research/infrastructure, then reconcile merged source v1.59 and run the guarded read-only preflight before any registry-only v1.60 transaction. The transaction may change only the six frozen P1-H source records; Brazil TSE and SNB remain excluded.
2. **Held provenance-scope repairs** — treat Brazil TSE `WSSRC-EL-BR-001` and SNB `WSSRC-CB-009` separately; neither may receive governance backfill until the provenance relationship/source scope is repaired and reviewed.
3. **Biosecurity candidate-node research** — assess marginal analytical value + authoritative timing + rights one institution/system at a time; architecture does not authorise population.
4. **South Asia provenance resolution** — continue precise authoritative-date/native-calendar work.
5. Re-run coverage audit after analytically justified canonical additions only.
6. Continue **Live Intelligence v1** using aligned canonical + monitor + retained-review evidence: WHAT HAPPENED / EXPECTED / SURPRISED / MOVED / CONNECTIONS / NOISE / ALTERNATIVES / SECOND-ORDER; do not infer causality from temporal coincidence.
7. Keep the **canonical auto-commit gate CLOSED** until genuine prospective reschedule and explicit cancellation evidence satisfy the existing real-world gates; healthy monitoring is not mutation authority.
8. Continue **Analysis v1** once the live-intelligence evidence contract is stable.
'''

for old, new in ((old_backlog, new_backlog), (old_next, new_next)):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected one status replacement, found {count}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('P1-H PROJECT_STATUS update applied')
