# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-03  
**Purpose:** durable continuation point after conversation-length/branch interruptions.

This file is a compact operational checkpoint, not a replacement for `WORLD_SIGNALS_PROJECT_CHARTER.md`, the canonical registries, monitor expectations, change ledger, readiness audit, coverage evidence or machine-readable monitor operations policy.

## Current source of truth

- **Canonical occurrence registry:** v0.18 — **662 occurrences**.
- **Tier-1 source registry:** v1.49.
- **Live monitor expectations:** v0.6.
- **Canonical commit readiness audit:** v0.8.
- **Coverage audit:** v0.1, rerun after Regional Correction J against canonical v0.18.
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

The live monitor records the exact execution context and configuration used for every run:

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

Workflow controls include:

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

## Coverage audit + Regional Correction J — COMPLETE

The occurrence/series/institution coverage audit was made executable and durable. It explicitly rejects occurrence-count quotas and treats series identity and institution diversity as separate coverage dimensions.

### Baseline v0.17

- 649 occurrences;
- 185 unique series;
- 110 institutions;
- 141 canonical source IDs used;
- regions below 10 unique series: **Africa, South Asia, Southeast Asia**;
- South Asia also below 8 institutions;
- `PHYSICAL_CLIMATE_RISK` below 5 unique series.

### Regional Correction J

A bounded monetary-policy correction added **13 remaining-2026 occurrences across six previously missing series**:

- Reserve Bank of India;
- State Bank of Pakistan;
- Central Bank of Sri Lanka;
- Bangko Sentral ng Pilipinas;
- Bank Negara Malaysia;
- Central Bank of Egypt.

Important source-governance outcomes:

- existing dormant RBI source identity `WSSRC-CB-011` was reused rather than duplicated;
- five genuinely new source identities were added;
- canonical factual provenance and production-monitor permission remained separate;
- BNM remains manual-only rights hold;
- SBP/CBSL remain rights-audit or production-automation holds;
- BSP/CBE reuse clearance does not itself grant production crawling permission;
- none of the new series was silently added to the scheduled live-monitor cohort.

The migration was fail-closed and first ran entirely in memory. The reviewed one-shot transaction then passed registry validation, coverage tests, exact-state assertions and an unintended-file-change guard before committing only `data/canonical/registry.json` and `data/sources/registry.json`.

Canonical migration commit: `a30b66a93b2734afed0fbbc59183b17065e42844`.

Temporary Regional Correction J write and preflight workflows have been removed. The migration plan/script remain only as inert reproducibility evidence.

### Post-audit v0.18

- 662 occurrences;
- 191 unique series;
- 116 institutions;
- 147 canonical source IDs used;
- Africa: 9 → **10** unique series; exits the `<10 series` diagnostic;
- Southeast Asia: 8 → **10** unique series; exits the diagnostic;
- South Asia: 4 → **7** unique series and 2 → **5** institutions; improved but remains diagnostically thin;
- monetary + macro occurrence share: **65.33% → 66.01%**.

That last result is important: geographic balance improved while category concentration worsened slightly. The next correction must therefore not become another general central-bank sweep.

Durable post-audit decision record: `data/coverage/REGIONAL_CORRECTION_J_POST_AUDIT_v0.1.md`.

Current non-monetary concentration findings:

- **PHYSICAL_CLIMATE_RISK:** 4 occurrences / 2 series / 2 institutions;
- **HEALTH_BIOSECURITY:** 10 occurrences / 5 series / **1 institution**;
- **ENERGY_COMMODITIES:** 28 occurrences / 6 series / **3 institutions**;
- **CLIMATE_ENVIRONMENT:** 10 occurrences / 10 series / 7 institutions — not a simple breadth problem.

## CI checkpoint repair

After the v0.18 migration, canonical validation passed but the full CI suite exposed one intentionally hard-coded legacy checkpoint assertion (`649`). It was advanced to the reviewed v0.18 checkpoint (`662`) rather than weakened into a floating count assertion.

The existing three legacy timed-record warnings for missing `start_utc` remain explicit backfill candidates; Regional Correction J introduced none of them.

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

Proceed by qualitative gap research, not population quotas:

1. **Physical climate risk** — determine whether the current two-series footprint is an ontology/source-design artefact or a true omission of high-value scheduled risk windows/assessment catalysts.
2. **Health / biosecurity** — test whether the five-series footprint is effectively WHO-only and identify systemically important authoritative institutions/treaty/regulatory nodes without turning outbreaks into scheduled calendar events.
3. **Energy / commodities** — test institutional and geographic breadth, including producer-policy and Global South information catalysts, while keeping physical disruptions in Shock/Live Intelligence.
4. **South Asia cross-domain depth** — only after the category review, identify fiscal/trade/energy/institutional/climate/governance nodes that materially improve the region beyond the expanded monetary/macro core.
5. Re-audit before any further bounded canonical population tranche.
6. Continue calendar UX → Live Intelligence v1 → analytical layer v1 only after the coverage/source decisions above are stable.

## Recovery rule for future conversation branches

When conversational context is interrupted, recover from the repository in this order rather than trusting the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/sources/registry.json`
5. `data/monitor/expectations.json`
6. `data/fixtures/commit_readiness.json`
7. `data/monitor/operations_policy.json` when present
8. `data/coverage/REGIONAL_CORRECTION_J_POST_AUDIT_v0.1.md`
9. latest `main` commits and GitHub Actions runs

If chat narrative and repository state disagree, stop and reconcile the discrepancy explicitly before new canonical or monitoring changes.
