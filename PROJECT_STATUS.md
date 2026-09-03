# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-03  
**Purpose:** durable continuation point after conversation-length/branch interruptions.

This file is a compact operational checkpoint, not a replacement for `WORLD_SIGNALS_PROJECT_CHARTER.md`, the canonical registries, monitor expectations, change ledger, readiness audit, coverage evidence or machine-readable monitor operations policy.

## Current source of truth

- **Canonical occurrence registry:** v0.19 — **668 occurrences**.
- **Tier-1 source registry:** v1.50.
- **Live monitor expectations:** v0.6.
- **Canonical commit readiness audit:** v0.8.
- **Latest coverage audit:** executable audit v0.2, run against canonical v0.19 / 668.
- **Automatic canonical commit:** **CLOSED / prohibited**.
- **Google Calendar writes:** **OFF / prohibited**.
- Browser/Pages remains a derived read-only projection, never canonical state.

## Current scheduled read-only monitor cohort

`live-monitor.yml` runs with `contents: read` permission and produces timestamped reports/review candidates only.

Current adapter entries represented in monitor expectations:

1. **RBA FSR RSS** — `WSSRC-FIN-001` / `WSO-FIN-B-0001`.
2. **Colombia SUIN Decree 111/1996 sentinel** — `WSSRC-REG4-001` / `WSO-REG-D-0001`.
3. **EU CRA Article 71 + Cellar RDF legal topology** — `WSSRC-TECH-001` / `WSO-TECH-A-0001`, `WSO-TECH-A-0007`.
4. **EU CBAM verifier-report milestone** — `WSSRC-TRD-005` / `WSO-TRD-A-0006`.
5. **EU CBAM certificate-sale milestone** — `WSSRC-TRD-005` / `WSO-TRD-A-0007`.
6. **EU CBAM annual declaration + certificate-surrender deadline** — `WSSRC-TRD-006` / `WSO-TRD-A-0008`.

The monitor architecture separates source health, immutable semantic-rule baselines and current-law topology. Source failure or absence cannot itself cancel, complete, reschedule or otherwise mutate an occurrence.

Monitor hardening currently includes:

- `contents: read` only;
- non-overlapping monitor concurrency;
- execution-context + configuration fingerprinting;
- canonical/source/expectations version + SHA capture;
- expected/observed adapter completeness checks;
- source-health summary separated from event state;
- deterministic review-candidate manifest;
- adapter/live/legal-monitor regression tests inside the workflow;
- uniquely named evidence artifacts;
- 90-day retention.

## Coverage programme — current state

### Baseline v0.17

- 649 occurrences;
- 185 unique series;
- 110 institutions;
- 141 canonical source IDs used.

### Regional Correction J — COMPLETE

Added 13 remaining-2026 monetary-policy occurrences across six previously missing series:

- Reserve Bank of India;
- State Bank of Pakistan;
- Central Bank of Sri Lanka;
- Bangko Sentral ng Pilipinas;
- Bank Negara Malaysia;
- Central Bank of Egypt.

Result:

- canonical v0.17 → **v0.18**;
- 649 → **662 occurrences**;
- source registry v1.48 → **v1.49**;
- Africa and Southeast Asia exited the original `<10 unique series` diagnostic;
- South Asia improved from 4 → 7 series and 2 → 5 institutions;
- monetary + macro occurrence share nevertheless rose 65.33% → 66.01%, proving that further coverage repair should not simply become another central-bank sweep.

Migration commit: `a30b66a93b2734afed0fbbc59183b17065e42844`.

Temporary write/preflight workflows were removed. Durable evidence:

- `data/coverage/REGIONAL_CORRECTION_J_POST_AUDIT_v0.1.md`
- `data/coverage/QUALITATIVE_COVERAGE_PRIORITY_v0.1.json`

### Physical climate risk audit — ONTOLOGY HOLD

Current footprint remains 4 occurrences / 2 series / 2 institutions.

High-value missing candidates expose a timing-model limitation:

- RSMC Nadi Southwest Pacific season: source-native **November–April**;
- IMD/RSMC New Delhi North Indian Ocean: **April–June and October–December**.

Do not convert those month statements into invented first/last civil dates. Required next ontology work:

- `MONTH_BOUNDED_SEASON_WINDOW`;
- `MULTI_PHASE_SEASON_WINDOW` / explicit season phases.

Durable audit: `data/coverage/PHYSICAL_CLIMATE_RISK_ONTOLOGY_AUDIT_v0.1.md`.

### Health / biosecurity audit — TAXONOMY HOLD

`HEALTH_BIOSECURITY` remains 10 occurrences / 5 series / one WHO institutional family, but broad biosecurity cannot be repaired by misclassifying distinct systems.

Important held nodes include:

- BWC Working Group — 7–11 Dec 2026;
- IPPC/CPM-21 — 5–9 Apr 2027;
- WOAH General Session — 24–28 May 2027;
- Africa CDC remains important but conflicting official CPHIA date surfaces require reconciliation.

Plant health, animal/zoonotic health, human public-health governance and biological-weapons security require a cross-domain coverage model rather than cosmetic category stuffing.

Durable audit: `data/coverage/HEALTH_BIOSECURITY_INSTITUTIONAL_AUDIT_v0.1.md`.

### South Asia cross-domain audit — PRECISION / PROVENANCE HOLDS

Current v0.19 shape remains 25 occurrences / 7 series / 5 institutions. The v0.19 mechanical audit still flags South Asia below 10 series and below 8 institutions.

Key held candidates:

- Nepal federal budget: authoritative native-calendar rule **15 Jestha**, but no authoritative government conversion chain yet established for 15 Jestha 2084 → Gregorian 2027;
- Bangladesh FY2027-28 budget process: authoritative process visible, exact future presentation date not yet published;
- BIMSTEC: institutional monitor, exact future high-level timing not yet established;
- North Indian Ocean cyclone seasons remain under the physical-risk ontology hold.

Durable audit: `data/coverage/SOUTH_ASIA_CROSS_DOMAIN_DEPTH_AUDIT_v0.1.md`.

### Energy / Commodities Correction K — COMPLETE / SUCCESSFUL

The pre-correction energy footprint was 28 occurrences / 6 series / 3 institutions, with **23/28 (82.1%) explicitly oil-specific**.

Cross-audit ranking selected only three add-now families:

1. **JODI Oil + Gas World Database first monthly updates** — four remaining 2026 `SOURCE_BUNDLE` occurrences;
2. **GECF 8th Heads-of-State Summit** — 27 Oct 2026;
3. **International Copper Study Group meetings** — 13 Oct 2026.

The first read-only preflight correctly failed closed because initially proposed commodity IDs were already occupied. Diagnostic run `33765743527` reconciled identities without mutation. Existing identities were preserved; Correction K moved to occurrence IDs `WSO-COM-A-0053`–`0058` and source IDs `WSSRC-COM-012`–`014`. The transaction script was then made plan-driven.

Successful migration:

- canonical v0.18 → **v0.19**;
- 662 → **668 occurrences**;
- source registry v1.49 → **v1.50**;
- +6 occurrences;
- +3 series;
- +3 institutions/sources;
- monitor expectations/policy SHA unchanged;
- all three new sources remain `PRODUCTION_AUTOMATION_HOLD`;
- migration commit: `b142b377b9bd5280a275a7e5b9c67fe6b86777a6`.

Measured v0.19 re-audit:

- ENERGY_COMMODITIES 28 → **34 occurrences**;
- 6 → **9 series**;
- 3 → **6 institutions**;
- 4 → **7 used source IDs**;
- occurrences/series 4.67 → **3.78**;
- legacy explicitly oil-specific footprint falls mechanically from 82.1% to **67.6%** of the enlarged category; JODI remains explicitly mixed Oil+Gas;
- monetary + macro occurrence share falls 66.01% → **65.42%**.

Temporary diagnostic, preflight and write-capable Correction K workflows have all been removed. The frozen plan and migration script remain only as reproducibility evidence.

Durable evidence:

- `data/coverage/ENERGY_COMMODITIES_BREADTH_AUDIT_v0.1.md`
- `data/coverage/CROSS_AUDIT_CORRECTION_CANDIDATES_v0.1.json`
- `data/coverage/ENERGY_COMMODITIES_CORRECTION_K_PLAN_v0.1.json`
- `data/coverage/ENERGY_COMMODITIES_CORRECTION_K_TRANSACTION_AUDIT_v0.1.md`

No further energy population follows automatically from this successful correction.

## Known held / non-production routes

- **Kenya Law PFM Act:** semantic section-25(2) baseline remains useful offline, but the current unversioned network route returned HTTP 403 from GitHub Actions. Not a green live-monitor dependency.
- **JODI / GECF / ICSG:** admitted for manually curated canonical provenance only in Correction K; production automated retrieval remains explicitly held.

## Canonical auto-commit gate — still CLOSED

Do not reopen the gate merely because more parsers or coverage tranches become green. The readiness audit still requires the harder real-world evidence:

1. **one prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence identity; and
2. **one explicit cancellation of an existing canonical occurrence** reviewed from positive authoritative evidence, not inferred from absence.

Until those conditions and any subsequent audit requirements are satisfied:

`FETCH → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE`

is allowed on validated routes; automatic canonical mutation is not.

## Exact next work

Population should pause again. The highest-value next work is architectural:

1. **Physical-risk timing ontology** — add source-native month-bounded and multi-phase seasonal-window semantics without inventing civil-day precision; test renderer/validator behavior before any Fiji/IMD population.
2. **Cross-domain biosecurity coverage taxonomy** — distinguish human health, animal/zoonotic health, plant health/trade and biological-security governance while preserving analytical links.
3. **South Asia source/precision backlog** — continue Nepal conversion-provenance, Bangladesh budget-date and regional-institution monitoring.
4. Re-run coverage audit after any ontology-enabled or taxonomy-reviewed additions.
5. Then resume calendar UX refinement → Live Intelligence v1 → analytical layer v1.

## Recovery rule for future conversation branches

When conversational context is interrupted, recover from the repository in this order rather than trusting the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/sources/registry.json`
5. `data/monitor/expectations.json`
6. `data/fixtures/commit_readiness.json`
7. `data/monitor/operations_policy.json`
8. latest relevant `data/coverage/*_AUDIT*` / correction transaction records
9. latest `main` commits and GitHub Actions runs

If chat narrative and repository state disagree, stop and reconcile the discrepancy explicitly before new canonical or monitoring changes.
