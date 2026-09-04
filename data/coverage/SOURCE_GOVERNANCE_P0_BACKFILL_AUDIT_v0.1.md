# WORLD SIGNALS — P0 source-governance backfill audit v0.1

**Reference date:** 2026-09-04  
**Scope:** configured live-monitor source dependencies only.  
**Authority:** records what was researched, checked and migrated; it does **not** authorise bulk P1/P2 governance backfill or canonical event mutation.

## Purpose

The source-governance completeness audit found that most legacy source records predated the modern separation between canonical factual-provenance fitness, automated-monitoring permission, verification mode and monitoring readiness. The first corrective tranche therefore targeted only **P0 configured-monitor dependencies**. Research priority was determined by operational dependency, never by an inferred licence or by machine readability/public accessibility.

## Before

At source registry **v1.51 / 222 sources** and monitor expectations **v0.6**:

- fully explicit modern governance: **1 source**;
- sources missing one or more governance fields: **221**;
- P0 configured-monitor dependencies needing backfill: **5**;
- P1 canonical dependencies needing backfill: **145**;
- P2 registry-only records needing backfill: **71**;
- missing `canonical_provenance_use`: **211**;
- missing `automated_monitoring_use`: **211**;
- missing `verification_mode`: **221**.

The P0 source families were RBA Financial Stability Review, Colombia SUIN/Open Data, EU Cyber Resilience Act/EUR-Lex Cellar, CBAM verifier/certificate-sale, and CBAM annual declaration/surrender.

## Colombia decomposition

The existing `WSSRC-REG4-001` combined two genuinely different evidentiary and governance roles:

1. **SUIN-Juriscol operative legal text** — canonical legal authority for Decree 111/1996 Article 59 and required manual clause-level verification;
2. **Colombia Open Data / Socrata inventory** — machine-readable presence/version/status sentinel.

The open-data portal and the separate SUIN HTML legal-text surface have different reuse/access conditions. A single blanket source-level automation classification would therefore be misleading.

The reviewed repair preserves `WSSRC-REG4-001` as the stable canonical/manual legal-authority source and creates **`WSSRC-REG4-002`** for the machine sentinel. Canonical occurrence `WSO-REG-D-0001` remains sourced to `WSSRC-REG4-001`; no canonical source identity was reassigned. Monitor adapter `COLOMBIA_SUIN_DECREE_111_1996` now uses `WSSRC-REG4-002` as its primary machine source and explicitly requires `WSSRC-REG4-001` for clause-level manual verification before any legal-input candidate can affect canonical review.

Historical audit evidence referring to the former composite `WSSRC-REG4-001` is retained as historical provenance and is not rewritten.

## Guarded transaction

Frozen plan: `data/coverage/SOURCE_GOVERNANCE_P0_BACKFILL_PLAN_v0.1.json`  
Research record: `data/coverage/SOURCE_GOVERNANCE_P0_RESEARCH_v0.1.md`

The live check-only preflight initially failed closed twice:

- first, on a standalone CLI import-path defect;
- second, because the plan incorrectly required the legacy `WSSRC-REG4-001.canonical_dependency_count` helper to exist even though canonical truth already showed one dependency.

Neither failure mutated state. The second precondition was corrected to derive dependency count from the canonical registry and backfill the denormalised helper field rather than treating missing legacy metadata as authoritative.

Corrected read-only preflight run **33833022931** passed with:

- canonical **v0.20 / 669**, unchanged;
- proposed source **v1.52 / 223**;
- proposed expectations **v0.7 / 6 adapters**;
- primary monitor sources `WSSRC-FIN-001`, `WSSRC-REG4-002`, `WSSRC-TECH-001`, `WSSRC-TRD-005`, `WSSRC-TRD-006`;
- configured monitor sources missing modern governance: **0**;
- Colombia machine sentinel `WSSRC-REG4-002`;
- required manual legal-verification source `WSSRC-REG4-001`;
- canonical SHA identical before/after;
- automatic canonical commit `false`;
- Google Calendar write `false`;
- clean working tree after check-only execution.

The one-shot reviewed apply run **33833235253** passed the same preflight, exact post-state assertions, full tests, registry validation, JavaScript parse/site build, protected-file hashes and a strict three-file diff whitelist before committing.

Transaction commit: **`20511a565d2ef690cbd3be0b10ab5dcaeeb98f82`** — `Apply P0 source-governance backfill`.

Exactly three files changed:

- `data/sources/registry.json`;
- `data/monitor/expectations.json`;
- `scripts/run_live_monitor.py`.

The canonical registry, schema, change ledger, monitor policy, review contracts/state/checkpoint and canonical commit-readiness fixture were protected and unchanged. The temporary write-capable and preflight workflows were deleted immediately after use.

## Measured after-state

Independent read-only audit run **33833361986** measured source registry **v1.52 / 223 sources** and monitor expectations **v0.7**:

- fully explicit modern governance: **7 sources**;
- sources missing one or more governance fields: **216**;
- **P0 configured-monitor backlog: 0**;
- P1 canonical dependencies needing backfill: **145**;
- P2 registry-only records needing backfill: **71**;
- missing `canonical_provenance_use`: **206**;
- missing `automated_monitoring_use`: **206**;
- missing `verification_mode`: **216**;
- unique source IDs used by canonical registry: **151**;
- unique primary source IDs used by configured monitor: **5**.

Thus the P0 tranche increased fully explicit source-governance records **1 → 7** while adding one correctly decomposed source identity, and reduced the configured-monitor governance backlog **5 → 0**. It did not disguise the much larger P1/P2 research backlog.

## Current governance result

All configured primary monitor sources now have explicit modern governance classifications. This says nothing about canonical automatic-commit authority: all monitor routes remain review-only and the canonical auto-commit gate remains CLOSED.

The remaining **145 P1 + 71 P2** records must be researched in bounded source-specific tranches. Public access, official status, machine readability, parser success or an existing canonical dependency must never be treated as evidence of automated-use permission.

## Invariants

- Canonical registry remains **v0.20 / 669**.
- Canonical occurrence identities are unchanged.
- `WSO-REG-D-0001` remains canonically sourced to `WSSRC-REG4-001`.
- Automatic canonical commits remain **0 / CLOSED**.
- Google Calendar writes remain **0 / OFF**.
- No source failure or missing governance field may imply event-state change.
- This audit does **not** authorise bulk P1/P2 backfill.
