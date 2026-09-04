# WORLD SIGNALS — P1-B source-governance backfill audit v0.1

**Reference date:** 2026-09-04  
**Scope:** six reviewed P1 canonical-dependent source records.  
**Authority:** records researched classifications, guarded migration and measured after-state; it does **not** authorise further P1/P2 backfill, canonical mutation, monitor expansion or Calendar writes.

## Purpose

P1-B continued the bounded source-governance programme after P1-A. Selection combined canonical dependency, active analytical horizon, governance information value and regional/institutional balance rather than mechanically taking the largest unresolved rows.

The tranche preserved the separation between canonical factual-provenance fitness, automated-monitoring permission, verification mode and monitoring readiness.

## Before

Post-P1-A source registry **v1.53 / 223**, canonical **v0.20 / 669**, monitor expectations **v0.7** measured:

- fully explicit modern governance: **13 sources**;
- sources missing one or more governance fields: **210**;
- P0 configured-monitor backlog: **0**;
- P1 canonical-dependent backlog: **139**;
- P2 registry-only backlog: **71**;
- missing `canonical_provenance_use`: **200**;
- missing `automated_monitoring_use`: **200**;
- missing `verification_mode`: **210**.

`monitoring_readiness_status` was already populated across all 223 source records.

## Frozen P1-B set

| Source | Institution / surface | Canonical dependencies | Canonical provenance | Automated monitoring | Verification |
|---|---|---:|---|---|---|
| `WSSRC-CB-001` | Federal Reserve / FOMC | 44 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-006` | Bank of Japan | 44 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-CB-002` | Reserve Bank of Australia | 33 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-003` | European Central Bank | 22 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-MAC-006` | UK Office for National Statistics | 19 | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-007` | Reserve Bank of New Zealand | 11 | `CLEARED_CURATED_FACTUAL_METADATA` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |

The cohort covered three Indo-Pacific institutions, two European institutions and one US institution. ONS and RBNZ intentionally formed opposite automation-control cases: ONS publishes explicit bot/crawler rules and official release-query/feed routes, while RBNZ expressly prohibits automated website access absent an applicable exception or prior written permission.

RBA source semantics were also tightened: the advertised multi-day Monetary Policy Board meeting window and the separately timed decision-release occurrence remain distinct. For 2026 the RBA directly states a 2.30 pm policy-outcome release on the second meeting day and a 3.30 pm Governor media conference; no historical heuristic substitutes for current authoritative timing.

Frozen plan: `data/coverage/SOURCE_GOVERNANCE_P1B_BACKFILL_PLAN_v0.1.json`  
Research record: `data/coverage/SOURCE_GOVERNANCE_P1B_RESEARCH_v0.1.md`

## Guarded transaction and lifecycle repair

The first P1-B guarded transaction reached a valid prospective source **v1.54** state and passed preflight, exact six-source application, registry-only diff enforcement and registry validation. The full suite then stopped the commit because the older P1-A lifecycle tests incorrectly assumed that a completed P1-A repository must remain exactly source v1.53 forever.

No registry mutation was committed by that failed run.

A separate test-only repair made completed governance-migration tests forward-compatible: current source version may be later than a migration's post-version, but every exact field frozen by that migration must remain intact. The same contract was applied to P1-B before retrying the transaction.

Guarded transaction v2 run **33855888392** then passed:

- read-only P1-B preflight;
- exact six-source apply;
- source-registry-only working-diff enforcement;
- canonical/monitor protected-file checks;
- registry validation;
- full unit suite;
- Python compile checks;
- browser JavaScript syntax checks;
- derived-site build; and
- guarded source-registry commit.

Transaction commit: **`62900eb3218d312e5fbf49c0d8db36881b3010ab`** — `Apply P1-B source-governance backfill`.  
PR #7 merged to `main` as **`f9f9a5a3f77bd724e6e02cbc1e47e1ee8ac5a358`**.

The net transaction PR changed exactly one file: `data/sources/registry.json`. Temporary transaction workflows were removed before review.

Brazil TSE `WSSRC-EL-BR-001` remained excluded and unchanged; the Brazilian presidential inauguration guard remains **2027-01-05**.

## Measured after-state

Independent read-only post-P1-B audit run **33856544804** measured:

- canonical registry: **v0.20 / 669**;
- source registry: **v1.54 / 223**;
- monitor expectations: **v0.7**;
- fully explicit modern governance: **19 sources**;
- sources missing one or more governance fields: **204**;
- P0 configured-monitor backlog: **0**;
- P1 canonical-dependent backlog: **133**;
- P2 registry-only backlog: **71**;
- missing `canonical_provenance_use`: **194**;
- missing `automated_monitoring_use`: **194**;
- missing `verification_mode`: **204**;
- unique source IDs used by canonical registry: **151**;
- unique primary source IDs used by configured monitor: **5**.

Measured deltas from P1-A are therefore:

- fully explicit governance: **13 → 19** (`+6`);
- missing-any governance: **210 → 204** (`-6`);
- P1 backlog: **139 → 133** (`-6`);
- P2 backlog: **71 → 71** (unchanged);
- missing canonical provenance: **200 → 194** (`-6`);
- missing automated monitoring: **200 → 194** (`-6`);
- missing verification mode: **210 → 204** (`-6`).

This is the exact expected shape for a six-record P1 transaction whose monitoring-readiness fields were already explicit.

## Remaining P1 queue and new provenance hold

The leading unresolved row by raw dependency is `WSSRC-CB-009` Swiss National Bank (**18**), followed by Eurostat (**12**), several 11-dependency central-bank/source surfaces, Japan MOF auctions (**10**) and other macro/fiscal/electoral sources.

P1-C research found that the SNB source relationship must be repaired before governance backfill. The registry currently identifies the SNB monetary-policy **decisions/history** page as the authoritative forward schedule source, while the actual future 2026/2027 monetary-policy assessment schedule is published on a separate SNB event-schedule surface. The existing canonical dates need not be presumed wrong; the defect is source scope/provenance.

Therefore `WSSRC-CB-009` is held out of P1-C until that source relationship is reviewed and repaired. High dependency does not override provenance integrity.

## Current governance result

P1-B is **COMPLETE**.

Remaining measured governance backlog is **133 P1 + 71 P2**. P0 remains zero. No bulk backfill is authorised.

## Invariants

- Canonical registry remains **v0.20 / 669**.
- Source registry is **v1.54 / 223**.
- Monitor expectations remain **v0.7**.
- `WSSRC-EL-BR-001` remains held pending provenance-scope repair.
- `WSSRC-CB-009` is newly held pending SNB forward-schedule source-scope repair.
- Brazilian presidential inauguration remains **2027-01-05**.
- Automatic canonical commits remain **CLOSED**.
- Google Calendar writes remain **OFF**.
- Permanent workflow cohort remains exactly six.
- Public accessibility, official status, machine readability or a successful fetch never by themselves establish automation permission.
