# WORLD SIGNALS — P1-A source-governance backfill audit v0.1

**Reference date:** 2026-09-04  
**Scope:** six reviewed high-dependency P1 canonical source records only.  
**Authority:** records researched classifications, guarded migration and measured after-state; it does **not** authorise further P1/P2 backfill, canonical mutation, monitor expansion or Calendar writes.

## Purpose

P1-A was the first bounded tranche after completion of the P0 configured-monitor governance repair. It targeted six canonical-dependent source records with substantial operational dependency while preserving the architectural separation between:

- canonical factual-provenance fitness;
- automated-monitoring permission;
- verification mode; and
- monitoring readiness.

Research priority remained operational dependency, not an inferred licence, source prestige, machine readability or public accessibility.

## Before

Independent post-P0 audit at source registry **v1.52 / 223 sources**, canonical **v0.20 / 669**, monitor expectations **v0.7** measured:

- fully explicit modern governance: **7 sources**;
- sources missing one or more governance fields: **216**;
- P0 configured-monitor backlog: **0**;
- P1 canonical-dependent backlog: **145**;
- P2 registry-only backlog: **71**;
- missing `canonical_provenance_use`: **206**;
- missing `automated_monitoring_use`: **206**;
- missing `verification_mode`: **216**.

`monitoring_readiness_status` was already present across all 223 records; P1-A therefore concerned only the three still-missing modern governance fields on its selected records.

## Frozen P1-A set

The reviewed plan admitted exactly six sources:

| Source | Institution / surface | Canonical dependencies | Canonical provenance | Automated monitoring | Verification |
|---|---|---:|---|---|---|
| `WSSRC-MAC-007` | China NBS | 36 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-MAC-017` | India MoSPI | 17 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-COM-003` | U.S. EIA WPSR | 16 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-COM-010` | FAO | 9 | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-HEALTH-001` | WHO | 6 | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |
| `WSSRC-CLIM-001` | UNFCCC / COP31 | 3 | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |

The transaction did **not** treat official status, successful fetching, open-data licensing elsewhere on the institution's estate, user-facing calendar export or machine-readable transport as evidence of permission to automate the specific monitored/scheduled surface.

Frozen plan: `data/coverage/SOURCE_GOVERNANCE_P1A_BACKFILL_PLAN_v0.1.json`  
Research record: `data/coverage/SOURCE_GOVERNANCE_P1A_RESEARCH_v0.1.md`

## Brazil / TSE hold

`WSSRC-EL-BR-001` was explicitly excluded from P1-A.

Current Brazilian electoral-calendar research established that TSE Resolution 23.760 was amended by Resolution 23.771 on 3 August 2026. Existing canonical milestones checked against the amended electoral schedule remain date-correct, including the conditional second round and diplomation deadline.

The presidential inauguration occurrence remains **2027-01-05**. Its date is constitutionally grounded rather than properly evidenced by the TSE electoral-calendar source relationship. That is a provenance-scope repair problem, not a date-correction problem.

Therefore:

- TSE governance fields were not backfilled in P1-A;
- the TSE source record remained unchanged;
- no Brazilian canonical date changed;
- the inauguration guard remained exactly `2027-01-05`.

## Guarded transaction

The infrastructure/planning PR added a default read-only migration script, frozen research/plan records and tests. The first merged-main read-only preflight run **33841251291** passed with a clean working tree.

The first guarded apply run **33841284146** reached a valid v1.53 in-run source state, changed exactly the six approved source records and passed the source-registry-only diff guard, but the post-state unit suite correctly failed because the initial P1-A tests only described the pre-transaction v1.52 lifecycle state. The workflow stopped before commit; no registry mutation was persisted.

A separate lifecycle-test repair taught the suite to distinguish:

- v1.52 pre-transaction: preflight/simulation must pass; and
- v1.53 completed state: exact frozen values must exist and replay must fail closed.

After that repair merged, guarded apply run **33842268368** passed:

- read-only preflight;
- exact six-source apply;
- source-registry-only working-diff enforcement;
- canonical/monitor protected-file checks;
- registry validation;
- full lifecycle-aware unit suite; and
- guarded source-registry commit.

Transaction commit: **`bea051539ac92ada06043e6ddaa9322ae8ff53a7`** — `Apply P1-A source governance backfill`.  
Merged to `main` in **`6e25a024f964e070821910cac1148f10ca955e5c`**.

The net transaction PR changed exactly one file:

- `data/sources/registry.json`.

Temporary preflight/apply workflows were removed after use. Canonical registry, monitor expectations, live-monitor code and permanent workflow cohort were unchanged.

## Measured after-state

Independent read-only post-transaction audit run **33843249249** measured:

- canonical registry: **v0.20 / 669**;
- source registry: **v1.53 / 223**;
- monitor expectations: **v0.7**;
- fully explicit modern governance: **13 sources**;
- sources missing one or more governance fields: **210**;
- **P0 configured-monitor backlog: 0**;
- P1 canonical-dependent backlog: **139**;
- P2 registry-only backlog: **71**;
- missing `canonical_provenance_use`: **200**;
- missing `automated_monitoring_use`: **200**;
- missing `verification_mode`: **210**;
- unique source IDs used by canonical registry: **151**;
- unique primary source IDs used by configured monitor: **5**.

Measured deltas from the post-P0 checkpoint are therefore:

- fully explicit governance: **7 → 13** (`+6`);
- missing-any governance: **216 → 210** (`-6`);
- P1 backlog: **145 → 139** (`-6`);
- P2 backlog: **71 → 71** (unchanged);
- missing canonical provenance: **206 → 200** (`-6`);
- missing automated monitoring: **206 → 200** (`-6`);
- missing verification mode: **216 → 210** (`-6`).

This is the exact expected shape for a six-record P1 transaction whose selected records already had explicit monitoring-readiness status.

## Remaining P1 queue — measured ordering

The audit ranks research attention by canonical occurrence dependency. The leading unresolved P1 records are currently:

1. `WSSRC-CB-001` — Federal Reserve Board / FOMC — **44**;
2. `WSSRC-CB-006` — Bank of Japan — **44**;
3. `WSSRC-CB-002` — Reserve Bank of Australia — **33**;
4. `WSSRC-CB-003` — European Central Bank — **22**;
5. `WSSRC-MAC-006` — UK Office for National Statistics — **19**;
6. `WSSRC-CB-009` — Swiss National Bank — **18**;
7. `WSSRC-MAC-005` — Eurostat — **12**;
8. `WSSRC-CB-004` — ECB publication surface — **11**;
9. `WSSRC-CB-005` — Bank of England — **11**;
10. `WSSRC-CB-007` — Reserve Bank of New Zealand — **11**;
11. `WSSRC-CB-008` — Bank of Canada — **11**;
12. `WSSRC-CB-013` — RBA release-schedule surface — **11**;
13. `WSSRC-FIS-007` — Japan Ministry of Finance auction calendar — **10**;
14. `WSSRC-MAC-003` — U.S. Bureau of Economic Analysis — **10**.

Lower-count but regionally important unresolved records include Australian ABS series surfaces and New Zealand electoral scheduling. The next tranche should therefore be selected from the measured queue using **dependency + active analytical horizon + regional/institutional balance**, rather than mechanically taking the six highest counts and reproducing a U.S./European bias.

No next-tranche classifications are authorised by this audit. Each selected source still requires direct source-specific rights/provenance research before any frozen migration plan is created.

## Current governance result

P1-A is **COMPLETE**.

It materially reduces unresolved governance while preserving the central rule: factual provenance permission is not automation permission. No selected source acquired broader automation authority merely because it is official, public, machine-readable or already used canonically.

The remaining backlog is **139 P1 + 71 P2**. P0 remains zero.

## Invariants

- Canonical registry remains **v0.20 / 669**.
- Source registry is **v1.53 / 223**.
- Monitor expectations remain **v0.7**.
- `WSSRC-EL-BR-001` remains excluded pending provenance-scope repair.
- Brazilian presidential inauguration remains **2027-01-05**.
- Automatic canonical commits remain **0 / CLOSED**.
- Google Calendar writes remain **0 / OFF**.
- Permanent workflow cohort remains exactly six.
- No source failure or missing governance field may imply event-state change.
- This audit does **not** authorise bulk P1/P2 backfill.
