# WORLD SIGNALS — Provenance Scope Repair A audit v0.1

**Status:** COMPLETE  
**Merged transaction:** PR #22 / `5adb07eb12ccd2fab1a51704d8dd5e9413e2d4be`  
**Reviewed transaction commit:** `21710437963a023be9e37fc89b0eb8ff6012cef7`  
**Transaction run:** `33886573084`  
**Independent audit run:** `33886673758`  
**Merged-main CI:** `33886955012` — SUCCESS  
**Merged-main Pages:** `33886992355` — SUCCESS
**Post-repair live monitor:** `33886954803` (run 57) — SUCCESS

## Purpose

Close the two long-standing provenance-scope holds for Brazil TSE and the Swiss National Bank without changing any canonical event timing or stable occurrence identity.

This was a provenance/source-scope repair, not a schedule correction.

## Reviewed post-state

- Canonical registry: **v0.21 / 669 occurrences**.
- Source registry: **v1.61 / 224 sources**.
- Change ledger: **v0.10**.
- Biosecurity overlay canonical checkpoint: **v0.21 / 669**.
- Monitor expectations: **v0.7**, unchanged.
- Automatic canonical commit: **false / CLOSED**.
- Google Calendar write: **false / OFF**.

## Brazil repair

`WSO-EL-A-0004` retains its stable occurrence identity and exact `start_local` **2027-01-05**.

The provenance defect was decomposed rather than hidden inside one source record:

- `WSSRC-EL-BR-001` remains the TSE electoral-calendar authority for its **three genuine electoral-calendar dependencies**.
- new `WSSRC-EL-BR-002` is the Brazilian constitutional source for the inauguration occurrence only.
- the inauguration uses `election_date_basis = CONSTITUTIONAL_RULE_DERIVED`.
- no Brazil canonical date/time changed.

## Swiss National Bank repair

`WSSRC-CB-009` retains its stable source identity but its authoritative timing surface is corrected to the SNB dedicated forward event schedule:

`https://www.snb.ch/en/services-events/digital-services/event-schedule`

All **18** existing SNB canonical occurrences remain unchanged.

## Exact transaction surface

The reviewed production transaction changed exactly four data files:

1. `data/canonical/registry.json`
2. `data/sources/registry.json`
3. `data/changes/ledger.json`
4. `data/coverage/biosecurity_overlay.json`

No monitor, parser, schema, Calendar, UI or workflow code was included in PR #22.

The ledger contains one reviewed `PROVENANCE_SCOPE_REPAIR` entry. Actual transaction `committed_at` is `2026-09-05T00:56:03+10:00`.

## Validation evidence

Guarded transaction run `33886573084` passed:

- read-only preflight;
- explicit apply gate;
- exact four-file surface enforcement;
- registry validation;
- **238 tests**;
- Python compilation;
- browser JavaScript checks;
- full site build;
- exact staged-file enforcement.

Independent post-transaction audit run `33886673758` separately confirmed:

- canonical **v0.21 / 669**;
- source **v1.61 / 224**;
- ledger **v0.10**;
- overlay checkpoint **v0.21 / 669**;
- Brazil inauguration **2027-01-05**;
- dependency split TSE **3** / Constitution **1** / SNB **18**;
- automatic canonical commit **false**;
- Google Calendar write **false**;
- **238 tests PASS**.

After PR #22 merged, merged-main CI run `33886955012` and Pages deployment run `33886992355` both completed successfully on exact main commit `5adb07eb12ccd2fab1a51704d8dd5e9413e2d4be`.

## Post-repair live-monitor alignment

The source-registry change in PR #22 matched the permanent live-monitor workflow's `push` path trigger, so the repair merge itself automatically produced a genuine post-repair observation rather than requiring a later scheduled or synthetic run.

Live-monitor run **57** / GitHub run id `33886954803` executed on exact repaired main commit `5adb07eb12ccd2fab1a51704d8dd5e9413e2d4be` and completed successfully. It recorded canonical **v0.21**, source **v1.61**, expectations **v0.7**, operations policy **v0.1**, **6 healthy / 0 degraded** adapters, all **6 expected adapters observed**, **0 review candidates**, `NO_CHANGE`, canonical hash unchanged, automatic canonical commit **false**, and Google Calendar write **false**.

Pages deployment `33886992355` completed successfully after run 57. The post-repair live-monitor configuration-alignment observation is therefore **CLOSED**. The earlier checkpoint statement that runtime evidence still predated v0.21/v1.61 was a documentation error, not a monitor or event-state failure.

## Measured source-governance queue after repair

Generic source-governance audit on v1.61 measured:

- fully explicit governance sources: **58**;
- sources missing one or more governance fields: **166**;
- P1 canonical-dependent: **95**;
- P2 registry-only: **71**;
- missing `canonical_provenance_use`: **156**;
- missing `automated_monitoring_use`: **156**;
- missing `verification_mode`: **166**.

These are measured post-repair values, not projected counts.

## Consequences / next gate

The Brazil TSE and SNB provenance-scope holds are CLOSED.

Do **not** mechanically create a P1-I six-source tranche. The next source-governance selection must be re-diagnosed against the remaining 95 P1 sources using active horizon, canonical dependency, source-scope integrity, regional breadth, domain diversity and analytical relevance as separate constraints.

Biosecurity candidate-node research and South Asia provenance resolution remain separate work lanes. The canonical automatic-commit gate remains CLOSED until genuine prospective reschedule and explicit cancellation evidence satisfy the existing real-world gates.
