# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-04  
**Purpose:** durable continuation point after conversation-length or branch interruptions.

This is an operational checkpoint, not a replacement for `WORLD_SIGNALS_PROJECT_CHARTER.md`, the canonical registries, monitor contracts, change ledger, coverage audits or source-rights evidence.

## Current source of truth

- **Canonical occurrence registry:** v0.20 — **669 occurrences**.
- **Tier-1 source registry:** v1.51 — **222 sources**.
- **Canonical schema:** v0.51.
- **Live monitor expectations:** v0.6.
- **Monitor operations policy:** v0.1.
- **Canonical commit readiness audit:** v0.8.
- **Automatic canonical commit:** **CLOSED / prohibited**.
- **Google Calendar writes:** **OFF / prohibited**.
- **Browser / GitHub Pages:** derived read-only projection, never canonical state.

Live Pages UX: `https://musicofscience.github.io/world-signals/`

Current visible layers include:

1. Calendar;
2. Event index;
3. configured Monitor routes;
4. reviewed Change history.

The next UX milestone is an **Operations** layer exposing browser-safe monitor governance, source readiness and timestamped recorded evidence while refusing to imply unobserved live runtime health.

## Architectural boundary

The executable architecture remains:

`AUTHORITATIVE SOURCE → FETCH → SNAPSHOT → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE → REVIEWED TRANSACTION → CANONICAL REGISTRY → DERIVED OUTPUTS`

Calendar/Pages, monitoring, Live Intelligence and Analysis remain separate layers. A source failure or missing item cannot itself cancel, complete or reschedule an event.

## Current scheduled read-only monitor cohort

`live-monitor.yml` runs with `contents: read` and produces timestamped reports/review candidates only.

Configured routes include:

- RBA Financial Stability Review RSS;
- Colombia SUIN Decree 111/1996 legal sentinel;
- EU CRA Article 71 / Cellar legal-topology sentinel;
- EU CBAM verifier-report milestone;
- EU CBAM certificate-sale milestone;
- EU CBAM annual declaration / certificate-surrender deadline.

Monitor hardening includes:

- read-only GitHub permissions;
- non-overlapping concurrency;
- execution-context and configuration fingerprinting;
- canonical/source/expectation/policy version + SHA capture;
- expected/observed adapter completeness checks;
- source-health state separated from event state;
- deterministic review-candidate manifest;
- regression tests inside the monitor workflow;
- evidence artefacts retained for 90 days.

## Coverage programme — completed corrections

### Regional Correction J — COMPLETE

Added 13 remaining-2026 monetary-policy occurrences across six previously missing series:

- Reserve Bank of India;
- State Bank of Pakistan;
- Central Bank of Sri Lanka;
- Bangko Sentral ng Pilipinas;
- Bank Negara Malaysia;
- Central Bank of Egypt.

Result: v0.17 / 649 → v0.18 / 662; source registry v1.48 → v1.49.

### Energy / Commodities Correction K — COMPLETE

Admitted only three high-value families after cross-audit:

- JODI Oil + Gas World Database first monthly updates — four remaining-2026 source-bundle occurrences;
- GECF 8th Heads-of-State Summit — 27 Oct 2026;
- International Copper Study Group meetings — 13 Oct 2026.

Result: v0.18 / 662 → v0.19 / 668; source registry v1.49 → v1.50. New sources remain manual provenance / production-automation holds.

### Physical Risk Correction L — COMPLETE

Schema v0.50/v0.51 introduced month-native seasonal timing so authorities need not be forced into invented civil days.

Correction L admitted exactly one occurrence:

- `WSO-RISK-A-0001` / `WSER-RISK-SWP-TC` — South-West Pacific tropical cyclone season 2026–27;
- source-native window: **November–April**;
- `MONTH_BOUNDED_SEASON_WINDOW`;
- no synthetic first/last day or timestamp;
- Fiji/RSMC Nadi source remains manual authoritative provenance with automated-monitoring rights hold.

Result: v0.19 / 668 → **v0.20 / 669**; source registry v1.50 / 221 → **v1.51 / 222**.

Reviewed migration commit: `d398ff464a77c0178743951f255482aa75068010`.
One-shot write workflow removed in `ba1e716a5dc5e9422f305411f514e5eb5fb58cd8`.
Normal CI and Pages deployment passed on the resulting state.

The proposed IMD/RSMC New Delhi North Indian Ocean season remains noncanonical because competent official material conflicts on the first phase: **April–June** versus **April–May**. WORLD SIGNALS did not choose a convenient winner.

Durable audit: `data/coverage/PHYSICAL_RISK_CORRECTION_L_AUDIT_v0.1.md`.

## Held / unresolved coverage nodes

### Health / biosecurity — taxonomy hold

Broad biosecurity must not be repaired by putting unlike institutions into one bucket. Current held nodes include BWC governance, IPPC/CPM, WOAH and Africa CDC. Human health, animal/zoonotic health, plant health/trade and biological-security governance require linked but distinct taxonomy.

### South Asia — precision / provenance backlog

Important held nodes include:

- Nepal federal budget native-calendar conversion provenance;
- Bangladesh FY2027-28 budget exact future presentation date;
- BIMSTEC high-level future scheduling;
- North Indian Ocean cyclone-season definition conflict.

### Source-rights holds

Fiji/RSMC Nadi, JODI, GECF, ICSG and several other sources may support manually curated factual provenance without thereby becoming production automated-monitor dependencies. Public accessibility and machine-readable transport never substitute for a rights/permission gate.

## Canonical auto-commit gate — CLOSED

Do not reopen merely because more parsers or coverage tranches pass tests. The harder real-world evidence remains:

1. **one prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence identity; and
2. **one explicit cancellation of an existing canonical occurrence** from positive authoritative evidence, not inferred from absence.

Until then:

`FETCH → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE`

is permitted on validated routes; automatic canonical mutation is not.

## Exact next work

1. **Web UX Operations layer** — publish browser-safe monitor/source governance and recorded evidence metadata, clearly separating configuration from runtime observation.
2. **Review-candidate UX contract** — design a static/read-only representation that can consume reviewed or retained candidate manifests without granting browser write authority.
3. **Cross-domain biosecurity taxonomy** — architecture before population.
4. **South Asia provenance backlog** — continue source/precision resolution.
5. Re-run coverage audit only after analytically justified additions.
6. Continue Live Intelligence v1 and Analysis v1 after the registry/monitor/UX boundaries remain stable.

## Recovery rule for future conversation branches

Recover from the repository in this order rather than trusting the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/canonical/schema.json`
5. `data/sources/registry.json`
6. `data/monitor/expectations.json`
7. `data/monitor/operations_policy.json`
8. `data/changes/ledger.json`
9. latest relevant `data/coverage/*AUDIT*` / transaction record
10. latest `main` commits and GitHub Actions runs.

If chat narrative and repository state disagree, stop and reconcile the discrepancy before new canonical or monitoring changes.
