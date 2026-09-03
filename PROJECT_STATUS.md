# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-03  
**Purpose:** durable continuation point after conversation-length/branch interruptions.

This file is a compact operational checkpoint, not a replacement for `WORLD_SIGNALS_PROJECT_CHARTER.md`, the canonical registries, monitor expectations, change ledger or readiness audit.

## Current source of truth

- **Canonical occurrence registry:** v0.17 — **649 occurrences**.
- **Tier-1 source registry:** v1.47.
- **Live monitor expectations:** v0.5.
- **Canonical commit readiness audit:** v0.7.
- **Automatic canonical commit:** **CLOSED / prohibited**.
- **Google Calendar writes:** **OFF / prohibited**.
- Browser/Pages remains a derived read-only projection, never canonical state.

## Current scheduled read-only monitor cohort

`live-monitor.yml` runs with `contents: read` permission and produces timestamped reports/review candidates only.

Validated routes represented in monitor expectations:

1. **RBA FSR RSS** — `WSSRC-FIN-001` / `WSO-FIN-B-0001`.
2. **Colombia SUIN Decree 111/1996 sentinel** — `WSSRC-REG4-001` / `WSO-REG-D-0001`.
3. **EU CRA Article 71 + Cellar RDF legal topology** — `WSSRC-TECH-001` / `WSO-TECH-A-0001`, `WSO-TECH-A-0007`.
4. **EU CBAM verifier-report milestone** — `WSSRC-TRD-005` / `WSO-TRD-A-0006`.
5. **EU CBAM certificate-sale milestone** — `WSSRC-TRD-005` / `WSO-TRD-A-0007`.

The existing monitor architecture separates source health, immutable semantic rule baselines and current-law topology. Source failure or absence cannot itself cancel, complete, reschedule or otherwise mutate an occurrence.

## CBAM annual deadline pilot — exact continuation point

A separate next pilot already exists:

- **Source:** `WSSRC-TRD-006` — European Commission / Taxation and Customs Union.
- **Canonical occurrence:** `WSO-TRD-A-0008` — first annual CBAM declaration and certificate-surrender deadline for 2026 imports.
- **Current legal interpretation encoded by the pilot:** Article 6(1) and Article 22(1) are parsed independently; both presently produce **30 September**, first due in **2027** for the **2026** reference/import year.
- **Live adapter smoke:** PASS.
- **Parent-act Cellar topology smoke:** PASS.
- **Parser negative controls:** PASS for date divergence and first-due-year divergence.
- **Review-comparator guard tests:** PASS for unchanged rule, shared-date change and paired-clause divergence.
- **Current source-registry readiness:** still an endpoint pilot; it has **not** been promoted merely because smoke/tests passed.
- **Current scheduled monitor status:** **not yet added to `data/monitor/expectations.json` or the scheduled live-monitor cohort**.

### Safe next sequence for this pilot

1. Freeze/review the annual-pilot expectation baseline in `data/monitor/expectations.json`.
2. Wire the annual rule into the read-only live monitor.
3. Add/confirm live-monitor source-health and review-candidate tests.
4. Run the GitHub live monitor and require:
   - source healthy;
   - paired clauses still internally consistent;
   - no unexpected semantic/topology change;
   - canonical SHA unchanged;
   - automatic commit false.
5. Only after that run passes, consider a guarded **source-readiness promotion** for `WSSRC-TRD-006`.
6. Do **not** create a new occurrence: `WSO-TRD-A-0008` already exists.

## Branch-recovery repairs completed 2026-09-03

Two interruption artefacts were found and repaired:

- Completed comparator-level guard tests for `cbam_annual_deadline_review_candidate`, including review-only handling of shared-date changes and Article 6/Article 22 divergence.
- Removed the completed one-shot write-capable workflow `.github/workflows/promote-cbam-source-v147.yml` after the v1.47 CBAM source promotion had already succeeded.

Post-repair CI and Pages deployment passed on `main`.

## Known held / non-production route

**Kenya Law PFM Act:** semantic section-25(2) baseline remains useful as offline regression/provenance evidence, but the current unversioned network route returned HTTP 403 from GitHub Actions. It is not a green live-monitor dependency and must not be represented as one.

## Canonical auto-commit gate — remaining real-world evidence

Do not reopen the gate merely because more parsers become green. The readiness audit still requires the harder evidence:

1. **one prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence identity; and
2. **one explicit cancellation of an existing canonical occurrence** reviewed from positive authoritative evidence, not inferred from absence.

Until those conditions and any subsequent audit requirements are satisfied:

`FETCH → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE`

is allowed on validated routes; automatic canonical mutation is not.

## Recovery rule for future conversation branches

When conversational context is interrupted, recover from the repository in this order rather than trusting the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/sources/registry.json`
5. `data/monitor/expectations.json`
6. `data/fixtures/commit_readiness.json`
7. latest `main` commits and GitHub Actions runs

If chat narrative and repository state disagree, stop and reconcile the discrepancy explicitly before new canonical or monitoring changes.
