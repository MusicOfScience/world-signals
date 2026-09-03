# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-03  
**Purpose:** durable continuation point after conversation-length/branch interruptions.

This file is a compact operational checkpoint, not a replacement for `WORLD_SIGNALS_PROJECT_CHARTER.md`, the canonical registries, monitor expectations, change ledger, readiness audit or machine-readable monitor operations policy.

## Current source of truth

- **Canonical occurrence registry:** v0.17 — **649 occurrences**.
- **Tier-1 source registry:** v1.48.
- **Live monitor expectations:** v0.6.
- **Canonical commit readiness audit:** v0.8.
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

## Annual CBAM integration — COMPLETE

`WSSRC-TRD-006 / WSO-TRD-A-0008` is no longer an endpoint-only pilot.

- Articles 6(1) and 22(1) are parsed independently.
- Both currently produce **30 September**, first due in **2027** for the **2026** reference/import year.
- Semantic-rule and paired-clause negative controls: PASS.
- Parent Regulation 2023/956 Cellar topology monitor: PASS.
- First scheduled-style live run with annual CBAM: **6 healthy / 0 degraded / 0 review candidates / NO_CHANGE**.
- Canonical SHA remained unchanged.
- Source promoted to **PILOT_VALIDATED_NO_AUTO_COMMIT** in source registry v1.48.
- Temporary write-capable promotion workflow removed immediately after successful promotion.

## Monitor operations hardening — PASS 1 COMPLETE

The live monitor now records the exact execution context and configuration used for every run:

- report schema version;
- GitHub run ID/number/SHA/event/ref/workflow/repository;
- canonical registry version + SHA;
- source-registry version + SHA;
- monitor-expectations version + SHA;
- combined configuration fingerprint;
- expected and observed adapter identities;
- missing/unexpected adapter detection;
- source-health summary;
- deterministic review-candidate manifest.

Workflow controls now include:

- `contents: read` only;
- one non-overlapping monitor concurrency group;
- 12-minute job timeout;
- adapter + live-monitor + legal-monitor regression tests within the monitor workflow;
- human-readable GitHub step summary;
- uniquely named evidence artifact per run;
- **90-day** evidence retention.

First hardened run: GitHub run `33754232015` — PASS.

- canonical registry v0.17;
- source registry v1.48;
- expectations v0.6;
- 6 expected adapters / 6 observed;
- no missing or unexpected adapters;
- 6 healthy / 0 degraded;
- 0 review candidates;
- canonical unchanged;
- final status `NO_CHANGE`.

## Branch-recovery repairs completed 2026-09-03

Earlier interruption artefacts were repaired:

- completed comparator-level guard tests for `cbam_annual_deadline_review_candidate`;
- removed completed CBAM v1.47 one-shot promotion workflow;
- added this durable `PROJECT_STATUS.md` checkpoint.

Annual-CBAM integration then completed after recovery, including v1.48 promotion and removal of that one-shot workflow.

## Known held / non-production route

**Kenya Law PFM Act:** semantic section-25(2) baseline remains useful as offline regression/provenance evidence, but the current unversioned network route returned HTTP 403 from GitHub Actions. It is not a green live-monitor dependency and must not be represented as one.

## Canonical auto-commit gate — remaining real-world evidence

Do not reopen the gate merely because more parsers become green. The readiness audit still requires the harder evidence:

1. **one prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence identity; and
2. **one explicit cancellation of an existing canonical occurrence** reviewed from positive authoritative evidence, not inferred from absence.

Until those conditions and any subsequent audit requirements are satisfied:

`FETCH → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE`

is allowed on validated routes; automatic canonical mutation is not.

## Exact next work

1. Finish monitor-operations hardening:
   - machine-readable operations policy;
   - source-health incident/recovery lifecycle;
   - deterministic review-candidate lifecycle/queue semantics;
   - evidence ageing/retention rules.
2. Run a full **coverage and bias audit at occurrence, series and institution levels**.
3. Use that audit to select a small corrective source/series tranche, deliberately guarding against machine-readability and US/EU convenience bias.
4. Re-audit before further population.
5. Then continue calendar UX → Live Intelligence v1 → analytical layer v1.

## Recovery rule for future conversation branches

When conversational context is interrupted, recover from the repository in this order rather than trusting the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/sources/registry.json`
5. `data/monitor/expectations.json`
6. `data/fixtures/commit_readiness.json`
7. `data/monitor/operations_policy.json` when present
8. latest `main` commits and GitHub Actions runs

If chat narrative and repository state disagree, stop and reconcile the discrepancy explicitly before new canonical or monitoring changes.
