# WORLD SIGNALS — CF Monitor pressure closeout v0.1

**Closeout date:** 2026-09-10  
**Exact base `main`:** `9552c1db0d212af33524b80b28d91ef7a897e2d8`  
**Branch:** `feature/post-cd-monitor-pressure-cf`  
**Architecture layer:** Source / Change Monitor — pressure audit and pilot validation only

## 1. Scope and boundary

CF resumes the post-CD programme from clean `main` after the CE OPEC provenance transaction was quarantined. It does not merge, cherry-pick, rebase onto, or otherwise reactivate `feature/post-cd-pressure-audit-ce`.

The permanent quarantine protocol is `OPEC_QUARANTINE.md`; `tests/test_opec_quarantine_cf.py` fails if the known CE OPEC transaction machinery becomes live on an active branch. OPEC is therefore retained as non-blocking technical debt and historical evidence, not as a hidden dependency of CF.

CF is intentionally bounded to:

1. read-only Monitor pressure measurement;
2. source-aware candidate selection;
3. zero-covered-category diagnosis;
4. one independently justified NOAA/NHC physical-climate-risk pilot;
5. parser/sentinel regressions and live-source readiness validation.

CF does **not**:

- mutate Canonical Registry data;
- mutate the Source Registry;
- mutate the reviewed Change Ledger;
- alter Live Intelligence or Analysis;
- register the NHC pilot into scheduled Monitor expectations;
- grant automatic Canonical commit authority;
- grant Live/Analysis promotion authority;
- alter Google Calendar output;
- reopen any OPEC transaction.

## 2. Pressure audit result

Starting governed state used by the audit:

- Canonical Registry: `v0.41 / 689` occurrences;
- Source Registry: `v2.02 / 257` sources;
- Monitor expectations: `v0.27 / 25` configured adapters;
- explicit Monitor occurrence scope: `215` occurrences;
- monitored regions: all `9` current Canonical regions;
- monitored categories: `11`;
- zero explicit Monitor coverage: `CLIMATE_ENVIRONMENT`, `HEALTH_BIOSECURITY`, `PHYSICAL_CLIMATE_RISK`.

These are diagnostic pressures, not quotas. Region/category absence does not itself authorise a route.

## 3. Candidate-selection finding

The zero-category diagnostic found that the NOAA National Hurricane Center source `WSSRC-RISK-002` was the only current zero-covered-category candidate without an explicit rights/automation block. The WHO, UNFCCC, IPCC, Australian Bureau of Meteorology, RSMC Nadi and India Meteorological Department candidates remain rights-held or rights-audit-held and were not promoted merely to improve category balance.

Selected pilot target:

- source: `WSSRC-RISK-002` — NOAA National Hurricane Center;
- category: `PHYSICAL_CLIMATE_RISK`;
- series: `WSER-RISK-ATL-HURR`;
- occurrences: `WSO-COM-A-0049` (2026 Atlantic hurricane season) and `WSO-COM-A-0050` (2027 Atlantic hurricane season).

## 4. Source semantics and rights

NHC Tropical Cyclone Climatology is the semantic authority for the Atlantic season boundary. RSS is operational corroboration/source-health evidence only; storm/feed activity cannot reschedule, complete or cancel the season window.

The live endpoint probe found the climatology, RSS directory, Atlantic outlook feed, Atlantic basin feed, robots surface and NWS rights surface retrievable. The authoritative season semantics were `June 1` through `November 30`.

A 2026-09-10 authoritative recheck confirmed:

- NHC climatology still states that the Atlantic hurricane season runs from June 1 to November 30: `https://www.nhc.noaa.gov/climo/`;
- the NWS disclaimer states that NWS web information is public domain unless specifically noted otherwise and gives explicit appropriate-use guidance: `https://www.weather.gov/disclaimer/`.

The pilot stores semantic/provenance metadata and hashes only; fetched remote source bodies are not retained.

## 5. Pilot behaviour

`src/world_signals/adapters/nhc_atlantic_season.py`:

- extracts the explicit Atlantic season definition from NHC climatology;
- fails closed if the definition is absent or conflicting;
- validates RSS as machine-readable structure only;
- does not infer schedule semantics from RSS activity.

`src/world_signals/nhc_atlantic_season_monitor.py`:

- requires the exact two-occurrence allow-list;
- rejects source/scope drift;
- requires schedule, lifecycle, certainty, new-occurrence, Live/Analysis-promotion and automatic-commit authority all to remain `false`;
- emits observation-only baseline matches when Canonical dates agree;
- emits a review-only candidate if authoritative NHC season semantics drift;
- never performs a Canonical date mutation itself.

## 6. Validation evidence

The live readiness workflow reached a successful state on commit `6b68d2b3e7cc89c79a8df153827f872f8d07680f`:

- workflow run: `34356935004` — **SUCCESS**;
- quarantine regression: passed;
- NHC parser/sentinel regressions: passed;
- live NHC semantic readiness: passed;
- Canonical / Live / Analysis validators: passed;
- readiness verdict: `PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT`;
- review candidates: `0`;
- semantic baseline matches: `2`;
- RSS schedule authority: `false`;
- automatic Canonical commit: `false`;
- OPEC quarantine respected: `true`.

The immediately preceding run `34356818121` failed during harness hardening and was not treated as readiness evidence. The branch then corrected the NHC readiness Python source path and the season month-regex grouping before the successful run. The resulting readiness evidence was persisted in commit `9e8696e0b04f37b46dbda6468955ea709fd41537`.

## 7. Merge boundary

Before integration, all four temporary CF workflow files are removed from the branch. Permanent merged artefacts are limited to:

- the OPEC quarantine protocol and regression guard;
- pressure-audit / shortlist / diagnostic evidence;
- NHC endpoint/readiness evidence;
- reusable diagnostic/probe scripts;
- the NHC adapter and review-only monitor logic;
- regression tests;
- this closeout record.

The merge does not make NHC a scheduled production Monitor route. A future tranche must separately decide whether to register the validated pilot into `data/monitor` expectations, with current source/rights recheck and ordinary CI. That decision is not automatic merely because CF validated the parser and review-only semantics.

## 8. OPEC non-reactivation rule

Any future OPEC work must start from then-current `main`, inspect `OPEC_QUARANTINE.md`, closed PR `#113`, and preserved branch `feature/post-cd-pressure-audit-ce`, and explicitly account for the discovered descendant-safety, timestamp, test-integrity, rights/provenance and stable-event-identity failure modes. The quarantined CE branch must not be reopened or used as an integration base for unrelated work.
