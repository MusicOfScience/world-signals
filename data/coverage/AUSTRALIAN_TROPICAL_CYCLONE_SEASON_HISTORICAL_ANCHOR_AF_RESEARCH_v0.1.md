# WORLD SIGNALS — Australian tropical cyclone season historical anchor AF research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `e576719bcbaf94730444cf64b1a1abeeacb25727`  
**Architecture position:** upstream Canonical Registry historical-anchor repair; no Analysis write

## Why AF exists

Post-AE reconnaissance confirms four categories remain present in the forward canonical registry but absent from the completed-anchor population:

- `CLIMATE_ENVIRONMENT`
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE`
- `ELECTIONS_GOVERNANCE`
- `PHYSICAL_CLIMATE_RISK`

The gap is genuine. The only past-starting non-terminal occurrence in these domains is `WSO-COM-A-0049` (Atlantic hurricane season 2026), correctly `ACTIVE` through 30 November 2026. Elapsed time therefore provides no stale-lifecycle repair.

AF does not treat the four categories as quotas. Candidate selection is based on marginal contract pressure, authoritative completion evidence, ontology/source reuse, representational balance and analytical novelty.

## Candidate comparison

### Australian tropical cyclone season 2025–26 — selected

Strengths:

- reuses existing series `WSER-RISK-AU-TC`;
- reuses existing primary Bureau of Meteorology source `WSSRC-RISK-001`;
- repairs both `PHYSICAL_CLIMATE_RISK` and `PHYSICAL_RISK_WINDOW` in the completed population;
- has an authoritative recurring season definition and competent first-party post-season evidence;
- exercises a risk-window temporal object rather than another publication, meeting, decision or data release;
- requires no new source identity and no taxonomy extension;
- preserves the project distinction between a risk window and realised shocks.

Geographic note: this is an Australian/Oceania specimen. Oceania is already represented among completed anchors, so AF is **not** a geographic-gap repair. Its value is domain and object-class diversity. The project should continue to prefer equally strong non-Western / Global South specimens where they add comparable architecture pressure.

### COP30, Belém — valuable but deferred

COP30 would be a strong `CLIMATE_ENVIRONMENT` / `ENVIRONMENTAL_GOVERNANCE_EVENT` specimen and would add Global South institutional context. However, first-party UNFCCC material contains non-trivial closing-date semantics that should not be silently normalised: the scheduled session window, actual closing plenaries and a later session-report date range do not present one frictionless endpoint. Under the charter's provenance rule, that disagreement deserves a dedicated resolution tranche rather than a convenient historical backfill.

### Elections/governance — valuable but higher ontology/source cost

The future elections/governance registry is already geographically broad. A 2026 South Korean local-election or comparable historical specimen would add useful political-process diversity, but current forward architecture does not provide an exact low-churn historical lineage/source reuse comparable with the BoM series. It remains a strong later candidate.

### Corporate / market structure — lower marginal novelty for this tranche

ASX/CME expiries and index-reconstitution mechanics are comparatively easy to backfill, but selecting one merely to remove a zero risks repairing a histogram with mechanical expiries rather than expanding the conceptual stress set. Market-structure remains unresolved, not rejected.

## First-party evidence

### Authoritative season definition

Bureau of Meteorology, Australian tropical cyclone season monitoring:

`https://www.bom.gov.au/climate/cyclones/australia/`

The Bureau defines the official tropical cyclone season in the Australian region as **1 November to 30 April**.

For AF the canonical window is therefore:

- start: `2025-11-01`
- end: `2026-04-30`
- timing type: `ALL_DAY_RANGE`
- precision: `DAY`
- all-day semantics: `true`.

The existing future Australian-season records deliberately keep `source_timezone = null` and UTC endpoints null because this is an Australian-region seasonal date window, not a single local clock event. AF preserves that contract. The source registry's `Australia/Brisbane` timezone describes the Bureau source route and is **not** promoted into the canonical seasonal window.

### Competent post-season evidence

Bureau of Meteorology, *2025–26 northern wet season*, issued **14 May 2026**:

`https://www.bom.gov.au/climate/current/season/tropics/summary.shtml`

The Bureau reports tropical-cyclone activity for the 2025–26 season, including 11 tropical cyclones in or moving into the Australian region during the northern wet season and seven reaching severe intensity. This is competent first-party post-season evidence that the historical seasonal risk window can be admitted as `COMPLETED`.

The activity statistics are contextual outcome evidence only. AF does not convert the season window into eleven cyclone occurrences and does not infer economic damage from cyclone count or severity.

A Bureau news item issued on the same date provides corroborating first-party summary material:

`https://www.bom.gov.au/news-and-media/northern-australias-2025-26-wet-season-summary-now-available`

## Canonical identity and lineage

Proposed historical occurrence:

- `occurrence_id`: `WSO-RISK-AU-TC-2025-26`
- `series_id`: `WSER-RISK-AU-TC`
- canonical name: `Australian tropical cyclone season 2025–26`
- source: `WSSRC-RISK-001`
- category: `PHYSICAL_CLIMATE_RISK`
- event type: `PHYSICAL_RISK_WINDOW`
- record class: `PHYSICAL_RISK_WINDOW`
- signal object class: `PHYSICAL_RISK_WINDOW`
- lifecycle: `COMPLETED`
- certainty: `CONFIRMED`
- jurisdiction: `Australian region`
- region: `Oceania / Pacific`.

Existing descendants that must remain byte-semantic unchanged:

- `WSO-COM-A-0051` — Australian tropical cyclone season 2026–27
- `WSO-COM-A-0052` — Australian tropical cyclone season 2027–28.

## Semantic guardrail

**Seasonal risk window ≠ individual tropical cyclone occurrence ≠ landfall ≠ damage ≠ climate-change attribution ≠ observed market response ≠ causal attribution.**

The canonical season window represents a period of elevated physical-climate exposure. Named cyclones or material physical shocks route to separate shock/occurrence handling under `physical_shock_routing = ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER` where warranted.

AF therefore preserves:

- `render_policy = THEMATIC_ONLY`;
- `visibility_tier = BACKGROUND`;
- `physical_shock_routing = ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER`;
- the existing commodity, supply-chain and transmission-channel scope as contextual exposure channels, not observed effects;
- `observed_market_response = null`.

No claim is made that the 2025–26 season, cyclone count, any individual cyclone or climate change caused a particular market move.

## Source-governance boundary

`WSSRC-RISK-001` currently has two live primary canonical dependencies, matching `canonical_dependency_count = 2`. AF adds one same-series historical primary dependency, so the only legitimate source-row mutation is:

`canonical_dependency_count: 2 → 3`.

No new source identity is required. Every other field of `WSSRC-RISK-001` and every other source row must remain unchanged.

The Bureau source remains `MANUAL_INFORMATIONAL_REFERENCE_ONLY` with production automation held pending permission/endpoint review. Public availability and page-element licensing are not converted into production crawling permission.

## Layer boundary

AF writes only upstream canonical/source/change/checkpoint state. It creates:

- no Analysis review;
- no Analysis evidence row;
- no Calendar write;
- no Live Intelligence claim;
- no market-response or causal attribution.

Under the live Analysis readiness function, lifecycle `COMPLETED` is sufficient to enter the completed canonical population. AF therefore should move the completed population from **17 to 18** while reviewed post-event samples remain **12**.

## Expected post-state

- canonical registry: `v0.35 / 685`
- source registry: `v1.76 / 240`
- change ledger: `v0.22 / 57`
- biosecurity overlay: `v0.10 @ canonical v0.35 / 685`, semantic payload unchanged
- Analysis schema: `v0.3` unchanged
- Analysis reviews: `v0.8 / 12` unchanged
- Analysis evidence: `v0.8 / 44` unchanged
- completed canonical Analysis population: `18`
- reviewed post-event population: `12`.

After AF, `PHYSICAL_CLIMATE_RISK` and `PHYSICAL_RISK_WINDOW` should no longer be absent from completed anchors/types. This is a coverage-pressure repair, not a claim of representative physical-risk modelling.

PR #40 remains untouched. Manual merge only.
