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
- **Review-candidate state contract:** v0.1 — prospective activation after monitor run 47.
- **Manual review-decision store:** v0.1 — currently empty, reviewed repository commits only.
- **Canonical commit readiness audit:** v0.8.
- **Automatic canonical commit:** **CLOSED / prohibited**.
- **Google Calendar writes:** **OFF / prohibited**.
- **Browser / GitHub Pages:** derived read-only projection, never canonical state.

Live Pages UX: `https://musicofscience.github.io/world-signals/`

Current visible layers include:

1. Calendar;
2. Event index;
3. configured Monitor routes;
4. Operations / source governance;
5. latest retained dated monitor-run evidence;
6. retained review state inside the Actions evidence horizon;
7. reviewed Change history.

The Operations layer deliberately distinguishes a single-run candidate snapshot from retained review state and from reviewed canonical history. It does not claim current source health from a static build and it does not claim that the retained-horizon reducer is a permanent queue.

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

### Latest retained single-run evidence

Latest retained pre-contract run used by the public runtime projection:

- live-monitor run **47** / GitHub run id `33754900613`;
- recorded at `2026-09-03T12:23:29.227611+00:00`;
- **6 healthy / 0 degraded / 0 candidates**;
- `NO_CHANGE`;
- canonical unchanged;
- run configuration: canonical v0.17 / source registry v1.48;
- therefore correctly labelled `STALE_RELATIVE_TO_CURRENT_SITE` against current v0.20 / v1.51.

Pages follows the latest **completed** monitor run, not merely the latest successful run. A newer failed run cannot be hidden behind an older green snapshot. Runtime artefacts are sanitized before public projection; raw snapshots, parser errors, legal payloads, old/new candidate evidence and observations do not enter Pages.

## Retained review state — IMPLEMENTED WITH RETENTION BOUNDARY

`data/monitor/review_candidate_state_contract.json` v0.1 activates prospectively **after monitor run 47**. Historical monitor experiments are not retroactively promoted.

Identity model:

- `candidate_id` = immutable monitor evidence object;
- `review_item_id` = stable proposition identity, prefix `WSRV-`;
- identical propositions aggregate even if candidate IDs differ;
- materially different propositions remain siblings;
- later candidate absence does not resolve an item;
- fetch/source failure does not resolve an item;
- rejected/deferred items do not reopen merely because they are reobserved.

`src/world_signals/review_state.py` implements the reducer. Canonical field propositions hash occurrence scope + the fields and values actually proposed. Legal/rule/topology propositions are opaque identities: raw rule state may be used transiently to derive a digest but is not exposed publicly.

`data/monitor/review_decisions.json` v0.1 is the reviewed manual-decision store. The monitor and Pages/browser cannot write it.

`scripts/fetch_retained_review_state.py` scans retained successful post-contract monitor artefacts, fails rather than silently omitting a successful run whose artefact is missing, and records unsuccessful runs without interpreting them as candidate absence. The v0.1 reducer has a hard ceiling of 400 retained successful runs.

First real Pages reduction after activation:

- successful post-contract runs considered: **0**;
- retained review items: **0**;
- unsuccessful post-contract runs: **0**;
- evidence horizon: complete for evidence that presently exists.

This is a meaningful prospective empty state, not a statement about pre-contract history.

Current limitation: the state is complete only inside the 90-day retained Actions artefact horizon. **Do not call it a permanent queue.** Before indefinite pending-review persistence can be claimed, design an independently constrained durable checkpoint mechanism without granting the monitor or Pages workflow repository contents-write authority merely to persist state.

Durable audit: `data/monitor/RETAINED_REVIEW_STATE_AUDIT_v0.1.md`.

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

Do not reopen merely because more parsers, UX features or coverage tranches pass tests. The harder real-world evidence remains:

1. **one prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence identity; and
2. **one explicit cancellation of an existing canonical occurrence** from positive authoritative evidence, not inferred from absence.

Until then:

`FETCH → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE`

is permitted on validated routes; automatic canonical mutation is not.

## Exact next work

1. **Durable review persistence architecture** — design a constrained checkpoint beyond the 90-day Actions horizon without turning Actions into a database or granting routine monitor/Pages contents-write authority.
2. **Observe first post-contract monitor run** — validate retained-state reduction on genuine run 48+ evidence; do not manufacture a candidate merely to demonstrate the UI.
3. **Cross-domain biosecurity taxonomy** — architecture before population.
4. **South Asia provenance backlog** — continue source/precision resolution.
5. **Source-governance backfill** — progressively classify older source records whose explicit provenance/automation fields are still `NOT_RECORDED_IN_REGISTRY`; do not treat missing classification as permission.
6. Re-run coverage audit only after analytically justified additions.
7. Continue **Live Intelligence v1** and then **Analysis v1** after the registry/monitor/review boundaries remain stable.

## Recovery rule for future conversation branches

Recover from the repository in this order rather than trusting the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/canonical/schema.json`
5. `data/sources/registry.json`
6. `data/monitor/expectations.json`
7. `data/monitor/operations_policy.json`
8. `data/monitor/review_candidate_state_contract.json`
9. `data/monitor/review_decisions.json`
10. `data/changes/ledger.json`
11. latest relevant `data/coverage/*AUDIT*` and `data/monitor/*AUDIT*`
12. latest `main` commits and GitHub Actions runs.

If chat narrative and repository state disagree, stop and reconcile the discrepancy before new canonical or monitoring changes.
