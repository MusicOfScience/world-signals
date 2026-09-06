# CURRENT RECOVERY OVERRIDE — POST-BD / BE OPEC FALLBACK LIFECYCLE COMPLETION

**Effective checkpoint:** 2026-09-07
**Exact post-BD main base:** `e54dddbaa0d60a39babc2fa47c1f054954b5c9ac`

This override supersedes stale "current" counts in the historical body below while preserving that body as an audit/recovery record. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains authoritative; governed registry/contract files remain operational truth.

## Current governed state

- Canonical Registry: **v0.40 / 689 occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v1.82 / 245 sources**
- reviewed Change Ledger: **v0.26 / 61 entries**
- biosecurity overlay: **v0.15 @ canonical v0.40 / 689**
- Source/Change Monitor expectations: **v0.10 / 8 configured adapters**
- Monitor operations policy: **v0.1**
- Live Intelligence: **v0.5 / 5 reviewed internal observations / 7 primary-official evidence rows / public observation projection CLOSED**
- Analysis schema: **v0.7**
- Analysis: **v0.17 / 21 reviews / 95 evidence / 18 reviewed event types**
- completed Analysis-eligible occurrences: **22**
- completed/unreviewed Analysis-eligible occurrences: **1** (`WSO-COM-A-0001`; not a population target)
- production `live_inputs`: **1 / public projection CLOSED**
- production Analysis revisions: **0 / gate CLOSED / public revision metadata projection CLOSED**
- production `EXACT_TIMESTAMP_SERIES`: **0**
- automatic canonical commit: **OFF / gate closed**
- Google Calendar writes: **OFF**

## Current architecture decision

BE repairs one upstream lifecycle state: the already-scheduled **6 September 2026 OPEC+ voluntary-adjustment review** (`WSO-COM-A-0001`) moves `PLANNED → COMPLETED` after reviewed post-event verification. The competent OPEC primary outcome statement was not retrievable on the accessible/indexed primary surface at review time, so BE uses one tightly bounded Reuters completion-only fallback source under the Charter's reputable-newswire tier. The fallback is explicitly secondary and primary OPEC outcome provenance remains a future reviewed upgrade requirement.

BE does **not** create the Reuters-reported 4 October meeting, add a sixth Live observation, populate a second Live→Analysis link, open Analysis revision production, infer any event clock time, or change monitor configuration. `WSSRC-COM-001` remains the OPEC schedule/decision authority; `WSSRC-COM-015` has zero Canonical dependencies and no forward-schedule or automation authority.

BD remains the fifth pressure-audited Live specimen. BC remains the historical-checkpoint / legitimate-descendant contract. BA's Analysis revision-lineage grammar remains production-closed. AZ's inaugural Live-to-Analysis relationship remains the only production `live_input`.

## Current configured monitor cohort

Eight configured adapters: RBA FSR; Colombia SUIN/Socrata; EU CRA/Cellar; three EU CBAM legal-rule routes; ONS release-calendar RSS; EIA WPSR schedule. Route presence does not imply blanket source automation permission, and all routes remain review-only with automatic canonical commit disabled.

## Recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. this current override
3. `data/canonical/registry.json`, `data/sources/registry.json`, `data/monitor/*`, `data/live_intelligence/*`, `data/analysis/*`
4. latest pressure/transaction audits
5. current `main` SHA and Actions runs
---

# WORLD SIGNALS — project status / branch-recovery checkpoint

**Updated:** 2026-09-05  
**Purpose:** durable continuation point after conversation-length, branch or deployment interruptions.

This is an operational checkpoint. `WORLD_SIGNALS_PROJECT_CHARTER.md` remains the authoritative architecture specification; canonical/source registries, monitor contracts, change ledger and audits remain primary evidence.

## Current source of truth

- **Canonical occurrence registry:** v0.22 — **669 occurrences**.
- **Tier-1 source registry:** v1.63 — **225 sources**.
- **Reviewed change ledger:** v0.11.
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

### Latest observed post-contract evidence

Run **59** / GitHub run id `33911315209`, recorded `2026-09-04T19:28:18.141283+00:00`, ran automatically after Vietnam Source-Scope Repair A merged on exact main commit `1c05406f810caebbb004ccad339d034a3aaa4cc0`:

- configuration canonical **v0.22 / 669** / source **v1.63 / 225** / expectations **v0.7** / operations policy **v0.1**;
- **6 healthy / 0 degraded** source adapters;
- all **6 expected adapters observed**, with no missing or unexpected adapters;
- **0 review candidates**;
- `NO_CHANGE`;
- canonical hash unchanged before/after;
- automatic canonical commit **false**;
- Google Calendar write **false**;
- configuration fingerprint `44f3e3cffd6b2596f2a396ca35790ef24e4df552abeb838f2322e4c0c3066ff4`.

This is the first live-monitor observation on the Vietnam-repaired canonical/source checkpoint. It closes configuration alignment on v0.22/v1.63. The initial push-triggered Pages run `33911315259` was cancelled by concurrency when the monitor-completion deployment superseded it; successor Pages run `33911351490` completed successfully on the same main commit. This is normal workflow supersession, not a deployment incident.

### Vietnam Source-Scope Repair A — COMPLETE

`WSO-REG-G-0001` remains the same **PROVISIONAL** occurrence on **20 October 2026**. Canonical provenance now points to first-order National Assembly source `WSSRC-REG5-002`; Government Electronic Newspaper source `WSSRC-REG5-001` remains historical/secondary official evidence. No canonical timing field changed. Governance state after the repair is **67 fully explicit / 158 incomplete / 87 P1 / 71 P2**. Durable closeout: `data/coverage/VIETNAM_SOURCE_SCOPE_REPAIR_A_AUDIT_v0.1.md`.

The review-state contract activated prospectively after run 47 and has now been exercised on genuine later evidence. Pages workflow-run deployment `33876115556` reduced **8 retained monitor runs** to **0 review items**, with **0 unsuccessful-run evidence gaps** and `horizon_complete=True`; runtime is `AVAILABLE_RETAINED_HORIZON(0)` at that retained checkpoint. The earlier observation gate is therefore CLOSED. Do not manufacture a candidate merely to test non-zero persistence; await natural future evidence.

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

### P1-C international / cross-domain tranche — COMPLETE

P1-C backfilled Eurostat, Bank of Canada, Japan MOF JGB auctions, Electoral Commission New Zealand, PBoC financial-statistics publication rule and UN General Assembly mandated events. Source registry advanced **v1.54 → v1.55 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Guarded transaction run `33858563869` passed all migration, one-file, validation and test gates. PR #9 merged as `7848b394d47b0a960200ca1077034ddc45847c2e`. Independent post-P1-C audit run `33859470953` measured:

- **25** fully explicit governance sources;
- **198** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **127 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **188**;
- missing `automated_monitoring_use`: **188**;
- missing `verification_mode`: **198**.

### P1-D international / cross-domain tranche — COMPLETE

P1-D backfilled RBA release scheduling, U.S. BEA, Statistics Bureau of Japan, Bank Indonesia, INDEC Argentina and Kenya Law / Constitution — **40 canonical dependencies** across Australia, the United States, Japan, Indonesia, Argentina and Kenya. Source registry advanced **v1.55 → v1.56 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Guarded transaction run `33865020762` passed preflight, exact one-file enforcement, registry validation and the full unit suite. PR #11 merged as `fbd95ede5a02daebfa6271e101a2e006ae9ca4ac`. Independent post-P1-D audit run `33866450058` measured:

- **31** fully explicit governance sources;
- **192** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **121 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **182**;
- missing `automated_monitoring_use`: **182**;
- missing `verification_mode`: **192**.

### P1-E mixed-rights / cross-domain tranche — COMPLETE

P1-E backfilled ECB monetary-policy publications, Bank of England MPC dates, Japan Customs/MOF trade statistics, ABS CPI, Convention on Biological Diversity COP and Central Bank of Egypt — **43 canonical dependencies**. Source registry advanced **v1.56 → v1.57 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Guarded transaction run `33868568393` passed preflight, exact one-file enforcement, registry validation, full unit suite, Python compilation, browser JavaScript checks and site build. PR #13 merged as `bd348a18d0b67d2b973ec7b61d0e8ede2e35cb9d`. Independent post-P1-E audit run `33869947061` measured:

- **37** fully explicit governance sources;
- **186** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **115 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **176**;
- missing `automated_monitoring_use`: **176**;
- missing `verification_mode`: **186**.

### P1-F mixed-rights / cross-domain tranche — COMPLETE

P1-F backfilled Statistics Bureau of Japan CPI, ABS Labour Force, CME E-mini S&P 500 expiry rules, IEA Oil Market Report schedule, ChinaMoney/NIFC LPR rules and Nigeria INEC — **29 canonical dependencies**. Source registry advanced **v1.57 → v1.58 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Guarded transaction run `33871313942` passed preflight, exact one-file enforcement, registry validation, full unit suite, Python compilation, browser JavaScript checks and site build. PR #15 merged as `21665ddce58cf9c7c7e868727ad4c2e19e6dce62`. Independent post-P1-F audit run `33872209871` measured:

- **43** fully explicit governance sources;
- **180** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **109 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **170**;
- missing `automated_monitoring_use`: **170**;
- missing `verification_mode`: **180**.

### P1-G mixed-rights / cross-domain tranche — COMPLETE

P1-G backfilled Statistics Bureau of Japan Labour Force Survey, ASX SPI 200 expiry rules, Bank of Canada / Department of Finance Canada bond auctions, JODI Oil + Gas World Database updates, WTO reform checkpoints and State Bank of Pakistan FY27 MPC dates — **28 canonical dependencies**. Source registry advanced **v1.58 → v1.59 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Guarded transaction run `33875500751` passed preflight, explicit apply gate, exact one-file enforcement, registry validation, **217 tests**, Python compilation, browser JavaScript checks and site build. Transaction commit `d43291bd352d28ae302fc3bdc1a5273d63705698` changed only `data/sources/registry.json`. PR #17 merged as `29363b2f7b2c387bf983350939d7e56d9d045cc7`.

Independent post-P1-G audit run `33875701696` measured:

- **49** fully explicit governance sources;
- **174** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **103 P1** canonical dependencies;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **164**;
- missing `automated_monitoring_use`: **164**;
- missing `verification_mode`: **174**.

Japan and Canada retain bounded automated-pilot verification; WTO remains manual-authoritative with endpoint review; ASX, JODI and SBP remain explicit rights-held/manual controls. Brazil TSE and Swiss National Bank remain excluded for provenance-scope repair. Brazil's `2027-01-05` inauguration remains constitutionally grounded rather than an electoral-calendar date.

Durable P1-F audit: `data/coverage/SOURCE_GOVERNANCE_P1F_BACKFILL_AUDIT_v0.1.md`.
P1-G research/plan: `data/coverage/SOURCE_GOVERNANCE_P1G_RESEARCH_v0.1.md` and `data/coverage/SOURCE_GOVERNANCE_P1G_BACKFILL_PLAN_v0.1.json`.
Durable P1-G audit: `data/coverage/SOURCE_GOVERNANCE_P1G_BACKFILL_AUDIT_v0.1.md`.


### P1-H geographically corrective / mixed-rights tranche — COMPLETE

P1-H backfilled OPEC, Japan ESRI GDP releases, Reserve Bank of India, South African Reserve Bank, Mexico constitutional budget deadlines and UN General Assembly 81st-session scheduling — **16 canonical dependencies** across Global, East Asia, South Asia, Africa and Latin America. The cohort deliberately traded raw dependency count for active-horizon, source-scope, regional and domain balance.

Guarded transaction run `33882096473` passed the fail-closed preflight, exact registry-only enforcement, registry validation, **229 tests**, Python compilation, browser checks and site build. Transaction commit `984b7df` changed only `data/sources/registry.json`; PR #20 merged as `7bf983d59859e60de24dad086f42bc5526726333`. Source registry advanced **v1.59 → v1.60 / 223**; canonical remains **v0.20 / 669** and monitor expectations **v0.7**.

Independent post-P1-H audit run `33882199612` measured:

- **55** fully explicit governance sources;
- **168** sources still missing at least one governance field;
- **97 P1** canonical-dependent sources;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **158**;
- missing `automated_monitoring_use`: **158**;
- missing `verification_mode`: **168**.

Brazil TSE and SNB remained intentionally excluded from P1-H because their defect was source scope/provenance rather than an ordinary missing-governance backfill. Those holds were subsequently closed by Provenance Scope Repair A.

### Provenance Scope Repair A — COMPLETE

PR #22 merged as `5adb07eb12ccd2fab1a51704d8dd5e9413e2d4be`. Canonical advanced **v0.20 → v0.21 / 669** solely for reviewed provenance semantics; source registry advanced **v1.60 / 223 → v1.61 / 224**; change ledger advanced **v0.9 → v0.10**. Brazil inauguration `WSO-EL-A-0004` remains exactly **2027-01-05** and now uses dedicated constitutional provenance `WSSRC-EL-BR-002`; TSE `WSSRC-EL-BR-001` retains its three genuine electoral-calendar dependencies. SNB `WSSRC-CB-009` now points to the dedicated forward event schedule while all **18** canonical SNB occurrences remain unchanged.

Independent post-transaction audit run `33886673758` measured **58 fully explicit**, **166 missing-any**, **95 P1** and **71 P2** sources. Automatic canonical commit remains false and Calendar write remains false. Merged-main CI `33886955012` and Pages `33886992355` both succeeded.

Durable audit: `data/coverage/PROVENANCE_SCOPE_REPAIR_A_AUDIT_v0.1.md`.

## Held / unresolved nodes

### Biosecurity candidate admission

WOAH, IPPC/CPM, BWC/UNODA and Africa CDC require normal importance/source/timing/rights/admission review. Do not bulk-populate merely because the analytical overlay now exists. Africa CDC date conflict remains unresolved.

### South Asia provenance backlog

- Nepal federal-budget native-calendar conversion provenance;
- Bangladesh FY2027–28 exact budget-presentation date;
- BIMSTEC high-level future schedule;
- North Indian Ocean cyclone-season definition conflict.

### Source-governance P1/P2 backlog

**95 P1 canonical-dependent** and **71 P2 registry-only** source records remain after the completed provenance repair. Prioritise bounded research by active horizon, canonical dependency, source-scope integrity, regional breadth, domain diversity and live analytical relevance as separate constraints; never infer rights from public accessibility, official status, machine readability or successful parsing.

Brazil TSE and SNB are no longer held nodes: Provenance Scope Repair A is merged and independently audited. Do not mechanically label the next work P1-I until a fresh selection diagnostic has tested the remaining queue.

## Canonical auto-commit gate — CLOSED

Do not reopen because parsers, coverage, UX, source-governance or review-state engineering pass tests. Remaining genuine real-world evidence:

1. one **prospective reschedule** detected after a prior canonical monitor snapshot and reviewed against the same stable occurrence; and
2. one **explicit cancellation** of an already-canonical occurrence from positive authoritative evidence.

No source failure may satisfy either gate.

## Verification Closeout A — COMPLETE

Fresh post-repair selection rejected mechanical dependency-only ranking and identified exactly eight future-active P1 sources for which `verification_mode` was the sole missing modern governance field. Vietnam `WSSRC-REG5-001` was held out for source-scope review because direct National Assembly provenance is better scoped than the registered government-news source.

Seven-source Verification Closeout A merged in PR #26 at signed main commit `849d4ef6a4b4814ec57235f08189e7a9eaf995c2`. Source registry advanced **v1.61 / 224 → v1.62 / 224**; canonical remains **v0.21 / 669**, ledger **v0.10**, expectations **v0.7**. APEC's one present stale dependency helper was corrected 0→1; there are now zero present `canonical_dependency_count` mismatches and eight legacy omissions remain deliberately unfilled.

Measured post-state governance audit: **65 fully explicit / 159 missing-any / 88 P1 / 71 P2**; missing provenance **156**, automation **156**, verification **159**.

Post-merge live-monitor run **58** / `33908223252` observed exact canonical **v0.21** / source **v1.62** configuration with **6 healthy / 0 degraded**, all 6 expected adapters observed, **0 candidates**, `NO_CHANGE`, canonical unchanged, auto canonical false and Calendar false. Follow-on Pages deployment `33908266777` succeeded.

Durable audit: `data/coverage/SOURCE_GOVERNANCE_VERIFICATION_CLOSEOUT_A_AUDIT_v0.1.md`.

**Next integrity-led source-governance work:** Vietnam `WSSRC-REG5-001` source-scope review before ordinary selection from the remaining 88-P1 queue.

## Exact next work

1. **Next P1 selection diagnostic** — reassess the remaining **95 P1** sources by active horizon, canonical dependency, source-scope integrity, regional breadth, domain diversity and analytical relevance. Do not mechanically invent a P1-I six-source conveyor belt.
2. **Biosecurity candidate-node research** — assess marginal analytical value + authoritative timing + rights one institution/system at a time; architecture does not authorise population.
3. **South Asia provenance resolution** — continue precise authoritative-date/native-calendar work.
4. Re-run coverage audit after analytically justified canonical additions only.
5. Continue **Live Intelligence v1** from aligned canonical + monitor + retained-review evidence: WHAT HAPPENED / EXPECTED / SURPRISED / MOVED / CONNECTIONS / NOISE / ALTERNATIVES / SECOND-ORDER; do not infer causality from temporal coincidence.
6. Keep the **canonical auto-commit gate CLOSED** until genuine prospective reschedule and explicit cancellation evidence satisfy the existing real-world gates; healthy monitoring is not mutation authority.
7. Continue **Analysis v1** once the live-intelligence evidence contract is stable.

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
