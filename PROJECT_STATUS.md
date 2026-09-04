# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-04  
**Purpose:** durable continuation point after conversation-length, branch or deployment interruptions.

This is an operational checkpoint. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains the authoritative architecture specification; canonical/source registries, monitor contracts, change ledger and audits remain primary evidence.

## Current source of truth

- **Canonical occurrence registry:** v0.20 — **669 occurrences**.
- **Tier-1 source registry:** v1.54 — **223 sources**.
- **Canonical schema:** v0.51.
- **Live monitor expectations:** v0.7.
- **Monitor operations policy:** v0.1.
- **Review-candidate state contract:** v0.1 — prospective activation after monitor run 47.
- **Manual review-decision store:** v0.1 — currently empty; reviewed repository changes only.
- **Durable review checkpoint architecture:** implemented/tested as a noncanonical layer; no routine monitor/Pages contents-write authority.
- **Canonical commit readiness audit:** v0.8.
- **Automatic canonical commit:** **CLOSED / prohibited**.
- **Google Calendar writes:** **OFF / prohibited**.
- **Browser / GitHub Pages:** derived read-only projection, never canonical state.

Live UX: `https://musicofscience.github.io/world-signals/`

## Publishing path — GitHub Actions only

GitHub Pages **Source is GitHub Actions**. `web/` + `scripts/build_site.py` are the application/build path.

Generated `docs/` output is ignored and not tracked. The stale v0.17/649 committed snapshot was removed in commit `954c3b0d6200cf322fa91220c56f3fdc4f80a7b0` so it cannot act as a competing publication surface.

The 2026-09-04 Pages-source incident is CLOSED. A fresh full Actions build/deploy (`33819680572`) succeeded after the source change and the user confirmed the public endpoint displayed the current tabbed application. Durable incident record: `data/monitor/PAGES_SOURCE_INCIDENT_2026-09-04.md`.

Current permanent workflows: exactly six — CI, Pages, coverage audit, monitor dry run, adapter smoke, live monitor. No temporary write-capable migration/diagnostic workflow should remain.

## Current visible Pages layers

1. Calendar;
2. Event index;
3. configured Monitor routes;
4. Operations / source governance;
5. latest retained dated monitor-run evidence;
6. retained review state inside the Actions evidence horizon;
7. **cross-domain Biosecurity system map** inside Operations;
8. reviewed Change history.

The UI distinguishes canonical events, configured monitoring, dated runtime evidence, transient run candidates, retained review state, analytical coverage overlays and reviewed history. It does not collapse these into one apparent “live” database.

## Architectural boundary

`AUTHORITATIVE SOURCE → FETCH → SNAPSHOT → PARSE → ASSERT → MATCH → DIFF → REVIEW CANDIDATE → REVIEW → REVIEWED TRANSACTION → CANONICAL REGISTRY → DERIVED OUTPUTS`

Calendar/Pages, monitoring, review state, Live Intelligence and Analysis remain separate layers. Source absence/failure cannot itself cancel, complete or reschedule an event.

## Scheduled read-only monitor cohort

`.github/workflows/live-monitor.yml` currently runs on cron **`23 5 * * *` (daily at 05:23 UTC)** and can also be dispatched manually. It has `contents: read` only.

Configured routes:

- RBA Financial Stability Review RSS;
- Colombia Decree 111/1996 legal sentinel — **machine inventory `WSSRC-REG4-002`; required manual SUIN clause verification `WSSRC-REG4-001`**;
- EU Cyber Resilience Act Article 71 / Cellar sentinel;
- EU CBAM verifier-report milestone;
- EU CBAM certificate-sale milestone;
- EU CBAM annual declaration / certificate-surrender milestone.

All configured **primary monitor sources now have explicit modern source-governance classifications**. Monitor hardening includes non-overlap concurrency, configuration fingerprints, expected/observed adapter completeness, source-health/event-state separation, deterministic candidate manifests and 90-day artefact retention.

### Latest retained pre-contract evidence

Run **47** / GitHub run id `33754900613`, recorded `2026-09-03T12:23:29.227611+00:00`:

- 6 healthy / 0 degraded;
- 0 review candidates;
- `NO_CHANGE`;
- canonical unchanged;
- run configuration canonical v0.17 / source v1.48, therefore public runtime projection correctly labels it stale relative to current v0.20 / v1.54.

Review-state contract activates prospectively **after run 47**. Do not manufacture a candidate or replay historical evidence merely to populate the UI. At this checkpoint the first genuine post-contract run 48+ remains an observation gate.

Pages follows the latest completed run, not merely the latest successful one. Newer failure cannot be hidden by an older green snapshot. Public runtime projection strips source snapshots, parser/error payloads, legal bodies/rules, old/new evidence values and observations.

## Review state / persistence

Stable identity model:

- `candidate_id` = immutable one-run evidence object;
- `review_item_id` = stable `WSRV-*` proposition;
- equivalent propositions aggregate across runs;
- materially different propositions remain siblings;
- later absence or fetch failure does not resolve an item;
- rejected/deferred items do not reopen merely through re-observation;
- canonical alignment without reviewed change-ledger linkage requires reconciliation rather than silent completion.

`data/monitor/review_decisions.json` is reviewed/manual and cannot be written by monitor or Pages.

Retained-horizon reducer is bounded by **90-day Actions artefact retention** and fails closed on missing successful-run evidence. Unsuccessful runs are evidence gaps, not “no candidate”.

A platform-neutral durable noncanonical review checkpoint/merge layer has also been implemented and tested so pending propositions can eventually survive source artefact expiry without turning Actions into a database. Checkpoint-private canonical proposed values may be retained only where needed for future reconciliation; opaque legal/topology raw payloads remain excluded. No routine checkpoint-writing workflow has been authorised.

Older audit language referring to a six-hour monitor cadence is historical/planning text; the **current executable workflow is daily at 05:23 UTC**. The 90-day retention limit, not the reducer's 400-run defensive ceiling, is the present evidence-horizon constraint.

## Coverage corrections completed

### Regional Correction J — COMPLETE

13 remaining-2026 monetary-policy occurrences across RBI, SBP, CBSL, BSP, BNM and CBE.

Result: v0.17 / 649 → v0.18 / 662; source v1.48 → v1.49.

### Energy / Commodities Correction K — COMPLETE

JODI Oil+Gas updates (four source-bundle occurrences), GECF Heads-of-State Summit and International Copper Study Group meeting.

Result: v0.18 / 662 → v0.19 / 668; source v1.49 → v1.50. The correction doubled ENERGY_COMMODITIES institutional breadth while reducing its oil-specific occurrence share; new sources remain manual provenance / automation holds.

### Physical Risk Correction L — COMPLETE

Schema v0.50/v0.51 added source-native month-bounded seasonal timing. One occurrence admitted:

- `WSO-RISK-A-0001` / `WSER-RISK-SWP-TC` — South-West Pacific tropical cyclone season 2026–27;
- native window November–April;
- no synthetic civil-day endpoints/timestamps;
- Fiji/RSMC Nadi source remains manual authoritative provenance / automation-rights hold.

Result: v0.19 / 668 → **v0.20 / 669**; source v1.50 / 221 → **v1.51 / 222**.

IMD/RSMC New Delhi North Indian Ocean season remains noncanonical because competent official material conflicts on first phase April–June vs April–May.

## Biosecurity cross-domain architecture — IMPLEMENTED / NO POPULATION

Mechanical diagnostic at v0.20 found `HEALTH_BIOSECURITY` genuinely WHO-only: **10 occurrences / 5 series / 1 institution**. No canonical WOAH, IPPC/CPM, BWC/UNODA, Africa CDC or One Health holdings were found.

`data/coverage/biosecurity_overlay.json` v0.1 defines a nonexclusive analytical/coverage overlay with four systems:

- human-health governance;
- animal/zoonotic health;
- plant/phytosanitary security;
- biological-security/arms-control governance.

`ONE_HEALTH` is a cross-cutting relationship, not a forced primary category.

Only the five existing WHO series are canonical memberships. Four noncanonical research nodes are represented without canonical IDs: WOAH; IPPC/CPM; BWC/UNODA; Africa CDC.

Executable validation fails if mapped series/category/institution diverge from canonical truth or if a candidate masquerades as canonical. The overlay grants **zero canonical mutation / zero event-population authority**.

Operations exposes a browser-safe **Biosecurity system map**, visibly separating the 5 WHO canonical series from the four noncanonical candidate nodes. CI passed on the overlay and public projection; Pages run `33821356707` deployed the visible map successfully.

Durable records:

- `data/coverage/BIOSECURITY_TAXONOMY_DIAGNOSTIC_v0.1.md`
- `data/coverage/BIOSECURITY_CROSS_DOMAIN_OVERLAY_AUDIT_v0.1.md`

## Source-governance backfill

### P0 configured-monitor tranche — COMPLETE

Initial completeness audit at source v1.51 / 222 found:

- **1** fully explicit modern-governance source;
- **221** sources missing at least one modern governance field;
- **5 P0** configured-monitor dependencies;
- **145 P1** canonical dependencies;
- **71 P2** registry-only sources.

P0 research separated factual provenance from automated use. The Colombia composite identity was decomposed rather than assigned one misleading blanket rights status:

- `WSSRC-REG4-001` remains the stable **SUIN manual legal-authority source** and remains the canonical source for `WSO-REG-D-0001`;
- new `WSSRC-REG4-002` is the **Colombia Open Data / Socrata machine sentinel**;
- monitor expectations explicitly require `WSSRC-REG4-001` clause-level verification after a machine-sentinel change.

Guarded transaction commit: **`20511a565d2ef690cbd3be0b10ab5dcaeeb98f82`**. Result: source **v1.51 / 222 → v1.52 / 223**; expectations **v0.6 → v0.7**; canonical remains **v0.20 / 669**.

Corrected live check-only preflight run `33833022931` passed with a clean working tree and canonical hash unchanged. Apply run `33833235253` changed exactly source registry, monitor expectations and live-monitor runner. Temporary write/preflight workflows were removed immediately.

Independent post-P0 audit run `33833361986` measured:

- **7** fully explicit governance sources;
- **216** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies remaining;
- **145 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **206**;
- missing `automated_monitoring_use`: **206**;
- missing `verification_mode`: **216**.

All configured primary monitor sources are therefore governance-explicit, while the large P1/P2 backlog remains deliberately unresolved. No bulk backfill is authorised. `NOT_RECORDED_IN_REGISTRY` remains unresolved governance, never implicit permission.

Durable record: `data/coverage/SOURCE_GOVERNANCE_P0_BACKFILL_AUDIT_v0.1.md`.

### P1-A high-dependency tranche — COMPLETE

P1-A backfilled explicit modern governance for exactly six canonical-dependent sources after direct source-specific research: China NBS (`WSSRC-MAC-007`), India MoSPI (`WSSRC-MAC-017`), U.S. EIA (`WSSRC-COM-003`), FAO (`WSSRC-COM-010`), WHO (`WSSRC-HEALTH-001`) and UNFCCC (`WSSRC-CLIM-001`). Factual-provenance fitness remained separate from automation permission throughout.

Brazil TSE `WSSRC-EL-BR-001` was deliberately excluded: Resolution 23.760 was amended by Resolution 23.771, while the 5 January 2027 presidential inauguration is constitutionally grounded rather than properly evidenced by the electoral-calendar source relationship. No Brazilian canonical date changed.

Read-only preflight run `33841251291` passed. An initial guarded apply run `33841284146` exposed a pre/post lifecycle-test defect and stopped before commit. After the lifecycle tests were repaired separately, guarded apply run `33842268368` passed all protections and committed only `data/sources/registry.json` (`bea051539ac92ada06043e6ddaa9322ae8ff53a7`). PR #3 merged as `6e25a024f964e070821910cac1148f10ca955e5c`.

Independent post-P1-A audit run `33843249249` measured source **v1.53 / 223**:

- **13** fully explicit governance sources;
- **210** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **139 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **200**;
- missing `automated_monitoring_use`: **200**;
- missing `verification_mode`: **210**.

The next P1 research queue is led by Fed/FOMC and BoJ (44 canonical dependencies each), RBA (33), ECB (22), ONS (19) and SNB (18), but the next bounded tranche must also guard against mechanical U.S./European weighting by considering active horizon and regional/institutional balance. No next-tranche classification is authorised yet.

Durable record: `data/coverage/SOURCE_GOVERNANCE_P1A_BACKFILL_AUDIT_v0.1.md`.

### P1-B high-dependency / balanced tranche — COMPLETE

P1-B backfilled six reviewed canonical-dependent sources: Fed/FOMC, Bank of Japan, Reserve Bank of Australia, European Central Bank schedule, UK Office for National Statistics and Reserve Bank of New Zealand. The cohort deliberately combined dependency with regional and governance-information balance rather than mechanical top-N selection.

Source registry advanced **v1.53 → v1.54 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**. ONS received bounded automated-monitoring clearance under its explicit bot/fair-use controls; RBNZ remains automation-rights-held. RBA meeting-window and separately timed decision-release semantics remain distinct.

An initial transaction exposed a historical migration-test lifecycle defect and committed nothing. A test-only repair made completed migration assertions forward-compatible while preserving exact frozen-field integrity. Guarded transaction run `33855888392` then passed all gates and PR #7 merged as `f9f9a5a3f77bd724e6e02cbc1e47e1ee8ac5a358`.

Independent post-P1-B audit run `33856544804` measured:

- **19** fully explicit governance sources;
- **204** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **133 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **194**;
- missing `automated_monitoring_use`: **194**;
- missing `verification_mode`: **204**.

P1-C research is now frozen for Eurostat, Bank of Canada, Japan MOF auctions, Electoral Commission NZ, PBoC financial-statistics publication rule and UN General Assembly mandated events. `WSSRC-CB-009` Swiss National Bank is held out despite 18 dependencies because the registered decisions/history URL does not directly support the forward schedule; repair source scope before governance backfill.

Durable P1-B audit: `data/coverage/SOURCE_GOVERNANCE_P1B_BACKFILL_AUDIT_v0.1.md`.
P1-C research/plan: `data/coverage/SOURCE_GOVERNANCE_P1C_RESEARCH_v0.1.md` and `data/coverage/SOURCE_GOVERNANCE_P1C_BACKFILL_PLAN_v0.1.json`.

## Held / unresolved nodes

### Biosecurity candidate admission

WOAH, IPPC/CPM, BWC/UNODA and Africa CDC require normal importance/source/timing/rights/admission review. Do not bulk-populate merely because the analytical overlay now exists. Africa CDC date conflict remains unresolved.

### South Asia provenance backlog

- Nepal federal-budget native-calendar conversion provenance;
- Bangladesh FY2027–28 exact budget-presentation date;
- BIMSTEC high-level future schedule;
- North Indian Ocean cyclone-season definition conflict.

### Source-governance P1/P2 backlog

**133 P1 canonical-dependent** and **71 P2 registry-only** source records still need bounded, evidence-specific governance research. Prioritise small tranches by live analytical relevance, dependency and active horizon; never infer rights from public accessibility, official status, machine readability or successful parsing.

## Canonical auto-commit gate — CLOSED

Do not reopen because parsers, coverage, UX, source-governance or review-state engineering pass tests. Remaining genuine real-world evidence:

1. one **prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence; and
2. one **explicit cancellation** of an already-canonical occurrence from positive authoritative evidence.

No source failure may satisfy either gate.

## Exact next work

1. **Observe first genuine post-contract live-monitor run 48+** against source v1.53 / expectations v0.7 and validate retained-review reduction against real evidence; do not manufacture a candidate.
2. **Validate the migrated Colombia adapter operationally** — machine health should report `WSSRC-REG4-002`; `WSSRC-REG4-001` remains manual verification authority only.
3. **Source-governance P1-C transaction gate** — after review/merge of the frozen P1-C infrastructure, reconcile merged source v1.54 and run the guarded read-only preflight before any registry-only v1.55 transaction; SNB remains excluded pending source-scope repair.
4. **Biosecurity candidate-node research** — assess marginal analytical value + authoritative timing + rights one institution/system at a time; architecture does not authorise population.
5. **South Asia provenance resolution** — continue precise authoritative-date/native-calendar work.
6. Re-run coverage audit after analytically justified canonical additions only.
7. Continue **Live Intelligence v1**: explicit WHAT HAPPENED / EXPECTED / SURPRISED / MOVED / CONNECTIONS / NOISE / ALTERNATIVES / SECOND-ORDER structure fed by canonical + monitor evidence, not post-hoc storytelling.
8. Then continue **Analysis v1** once the live-intelligence evidence contract is stable.

## Recovery rule

Recover from repository state, not the last chat sentence:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. `data/canonical/registry.json`
4. `data/canonical/schema.json`
5. `data/sources/registry.json`
6. monitor expectations/policy/review contracts/decisions/checkpoint
7. `data/changes/ledger.json`
8. latest relevant coverage/monitor audits
9. current `main` commits + Actions runs

If chat and repository state disagree, stop and reconcile before new canonical or monitoring changes.
