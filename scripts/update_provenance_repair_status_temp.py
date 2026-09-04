from pathlib import Path

root = Path(__file__).resolve().parents[1]

research = root / "data/coverage/PROVENANCE_SCOPE_REPAIR_A_RESEARCH_v0.1.md"
text = research.read_text(encoding="utf-8")
old = '''1. `data/canonical/registry.json` — one occurrence's provenance-semantic fields; count unchanged;
2. `data/sources/registry.json` — repaired TSE row, repaired SNB row, one new constitutional source, registry version/count metadata;
3. `data/changes/ledger.json` — one reviewed provenance-repair entry and ledger version/reference metadata.

It must leave monitor expectations and live-monitor code byte-identical, keep automatic canonical commit false, keep Google Calendar writes false, preserve all 669 occurrence IDs, and preserve every canonical date/time.
'''
new = '''1. `data/canonical/registry.json` — one occurrence's provenance-semantic fields; count unchanged;
2. `data/sources/registry.json` — repaired TSE row, repaired SNB row, one new constitutional source, registry version/count metadata;
3. `data/changes/ledger.json` — one reviewed provenance-repair entry and ledger version/reference metadata; `committed_at` is generated at apply time and is not pre-declared by research;
4. `data/coverage/biosecurity_overlay.json` — advance only its canonical checkpoint pointer from v0.20 / 669 to v0.21 / 669 because the overlay validator intentionally pins the exact canonical checkpoint it was audited against.

The overlay's systems, memberships, candidates and analytical content must remain byte-semantically unchanged. The transaction must also leave monitor expectations and live-monitor code byte-identical, keep automatic canonical commit false, keep Google Calendar writes false, preserve all 669 occurrence IDs, and preserve every canonical date/time.
'''
if old not in text:
    raise SystemExit("research transaction-boundary block not found")
research.write_text(text.replace(old, new, 1), encoding="utf-8")

status = root / "PROJECT_STATUS.md"
text = status.read_text(encoding="utf-8")
text = text.replace(
    "- **Tier-1 source registry:** v1.59 — **223 sources**.",
    "- **Tier-1 source registry:** v1.60 — **223 sources**.",
    1,
)
marker = "\n## Held / unresolved nodes\n"
section = '''
### P1-H geographically corrective / mixed-rights tranche — COMPLETE

P1-H backfilled OPEC, Japan ESRI GDP releases, Reserve Bank of India, South African Reserve Bank, Mexico constitutional budget deadlines and UN General Assembly 81st-session scheduling — **16 canonical dependencies** across Global, East Asia, South Asia, Africa and Latin America. The cohort deliberately traded raw dependency count for active-horizon, source-scope, regional and domain balance.

Guarded transaction run `33882096473` passed the fail-closed preflight, exact registry-only enforcement, registry validation, **229 tests**, Python compilation, browser checks and site build. Transaction commit `984b7df` changed only `data/sources/registry.json`; PR #20 merged as `7bf983d59859e60de24dad086f42bc5526726333`. Source registry advanced **v1.59 → v1.60 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Independent post-P1-H audit run `33882199612` measured:

- **55** fully explicit governance sources;
- **168** sources still missing at least one governance field;
- **97 P1** canonical-dependent sources;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **158**;
- missing `automated_monitoring_use`: **158**;
- missing `verification_mode`: **168**.

Brazil TSE and SNB remained intentionally excluded from P1-H because their defect was source scope/provenance rather than an ordinary missing-governance backfill.
'''
if "### P1-H geographically corrective / mixed-rights tranche — COMPLETE" not in text:
    if marker not in text:
        raise SystemExit("held/unresolved marker missing")
    text = text.replace(marker, "\n" + section + marker, 1)

old_backlog = '''**103 P1 canonical-dependent** and **71 P2 registry-only** source records still need bounded, evidence-specific governance research. Prioritise small tranches by live analytical relevance, dependency and active horizon; never infer rights from public accessibility, official status, machine readability or successful parsing.

P1-H selection/research is now frozen for OPEC (`WSSRC-COM-001`), Japan ESRI GDP (`WSSRC-MAC-016`), RBI (`WSSRC-CB-011`), SARB (`WSSRC-REG-006`), Mexico constitutional budget deadlines (`WSSRC-REG-010`) and UNGA 81st-session scheduling (`WSSRC-INT-001`) — **16 canonical dependencies** across Global, East Asia, South Asia, Africa and Latin America. This intentionally trades raw dependency count for active-horizon, source-scope, regional and domain balance. No registry mutation is authorised by the research freeze.
'''
new_backlog = '''**97 P1 canonical-dependent** and **71 P2 registry-only** source records still need bounded, evidence-specific governance research after P1-H. Prioritise small tranches by live analytical relevance, dependency and active horizon; never infer rights from public accessibility, official status, machine readability or successful parsing.

The two long-standing provenance-scope holds are now researched and frozen as **Provenance Scope Repair A** rather than being rolled into P1-I. Brazil TSE `WSSRC-EL-BR-001` remains the electoral-calendar authority for three genuine dependencies; new `WSSRC-EL-BR-002` is planned for Constitution art. 82 and the unchanged 5 January 2027 inauguration provenance. SNB `WSSRC-CB-009` retains its stable identity but is planned to move to the dedicated forward event schedule, which directly supports all 18 existing assessment/news-conference/summary occurrences. No repair data mutation is included in the research branch.

Frozen guarded post-state: canonical **v0.21 / 669**, source **v1.61 / 224**, change ledger **v0.10**, and the noncanonical biosecurity overlay checkpoint advanced only from canonical v0.20 / 669 to v0.21 / 669. Every canonical date/time and occurrence ID must remain unchanged; the Brazil change is provenance-semantic, not a reschedule.
'''
if old_backlog not in text:
    raise SystemExit("old P1 backlog block missing")
text = text.replace(old_backlog, new_backlog, 1)

old_next = '''1. **Source-governance P1-H transaction gate** — review/merge the frozen P1-H research/infrastructure, then reconcile merged source v1.59 and run the guarded read-only preflight before any registry-only v1.60 transaction. The transaction may change only the six frozen P1-H source records; Brazil TSE and SNB remain excluded.
2. **Held provenance-scope repairs** — treat Brazil TSE `WSSRC-EL-BR-001` and SNB `WSSRC-CB-009` separately; neither may receive governance backfill until the provenance relationship/source scope is repaired and reviewed.
3. **Biosecurity candidate-node research** — assess marginal analytical value + authoritative timing + rights one institution/system at a time; architecture does not authorise population.
4. **South Asia provenance resolution** — continue precise authoritative-date/native-calendar work.
5. Re-run coverage audit after analytically justified canonical additions only.
6. Continue **Live Intelligence v1** using aligned canonical + monitor + retained-review evidence: WHAT HAPPENED / EXPECTED / SURPRISED / MOVED / CONNECTIONS / NOISE / ALTERNATIVES / SECOND-ORDER; do not infer causality from temporal coincidence.
7. Keep the **canonical auto-commit gate CLOSED** until genuine prospective reschedule and explicit cancellation evidence satisfy the existing real-world gates; healthy monitoring is not mutation authority.
8. Continue **Analysis v1** once the live-intelligence evidence contract is stable.
'''
new_next = '''1. **Provenance Scope Repair A transaction gate** — review/merge the frozen Brazil TSE / Constitution and SNB research/infrastructure, reconcile merged canonical v0.20 / source v1.60, then run the guarded read-only preflight before the four-file reviewed transaction. It may change only `WSO-EL-A-0004` provenance-semantic fields, TSE/SNB source scope, append `WSSRC-EL-BR-002`, append one reviewed ledger entry, and advance only the biosecurity overlay's canonical checkpoint pointer.
2. **Independent post-repair audit** — prove canonical v0.21 / 669, source v1.61 / 224, ledger v0.10, exact 5 January 2027 preservation, unchanged SNB occurrences, updated governance queue metrics, overlay validity, automatic canonical commit false and Calendar write false before considering the repair complete.
3. **Next P1 selection diagnostic** — only after the provenance repair is merged/audited, reassess the remaining P1 queue by active horizon, dependency, source-scope integrity, regional breadth and domain diversity. Do not mechanically invent a P1-I six-source conveyor belt.
4. **Biosecurity candidate-node research** — assess marginal analytical value + authoritative timing + rights one institution/system at a time; architecture does not authorise population.
5. **South Asia provenance resolution** — continue precise authoritative-date/native-calendar work.
6. Re-run coverage audit after analytically justified canonical additions only.
7. Continue **Live Intelligence v1** using aligned canonical + monitor + retained-review evidence: WHAT HAPPENED / EXPECTED / SURPRISED / MOVED / CONNECTIONS / NOISE / ALTERNATIVES / SECOND-ORDER; do not infer causality from temporal coincidence.
8. Keep the **canonical auto-commit gate CLOSED** until genuine prospective reschedule and explicit cancellation evidence satisfy the existing real-world gates; healthy monitoring is not mutation authority.
9. Continue **Analysis v1** once the live-intelligence evidence contract is stable.
'''
if old_next not in text:
    raise SystemExit("old exact-next-work block missing")
text = text.replace(old_next, new_next, 1)
status.write_text(text, encoding="utf-8")
print("updated repair research boundary and project checkpoint")
