# WORLD SIGNALS — post-AU pressure audit AV v0.1

**Exact post-#76 main:** `a487eaecd6c08e9692a42ce6ffed2dea1e455879`  
**Reference date:** 2026-09-06

## Frozen checkpoint

- Canonical Registry: `v0.38 / 688`
- Canonical schema: `v0.52`
- Source Registry: `v1.80 / 243`
- Change Ledger: `v0.24 / 59`
- biosecurity overlay: `v0.13 @ canonical v0.38 / 688`
- monitor expectations: `v0.10 / 8 configured adapters`
- monitor operations policy: `v0.1`
- Analysis schema: `v0.4`
- Analysis reviews: `v0.16 / 20`
- Analysis evidence: `v0.16 / 91`
- reviewed event-type diversity: `18`
- Analysis-eligible completed occurrences: `21`
- production `EXACT_TIMESTAMP_SERIES`: `0`
- sole completed/unreviewed canonical occurrence: `WSO-MAC-B-0041`

AV is a pressure audit. A one-item frontier is not an instruction to consume the item.

## Decision

**Pause further Analysis population and establish the executable Live Intelligence foundation with zero production population.**

Do not add a twenty-first Analysis review merely to make the completed sample read `21/21`. Do not add another monitor route because an uncovered geography exists. Do not manufacture a historical market-structure object. Do not create a cross-event causal graph before the upstream observation layer exists.

The highest-value unresolved pressure is architectural: the Charter requires a distinct Live Intelligence layer, `data/analysis/schema.json` already names `LIVE_INTELLIGENCE` as upstream, but the repository has no durable Live Intelligence dataset or validator.

## Candidate comparison

### A. Japan household-spending Analysis — HOLD

`WSO-MAC-B-0041` remains valid future Analysis material.

Fresh 6 September research confirms the 4 September 2026 Statistics Bureau release for July 2026:

- consumption expenditure: `¥301,245`;
- nominal y/y: `-1.5%`;
- real y/y: `-3.6%`;
- real seasonally adjusted m/m: `+0.5%`.

Official source:

- Statistics Bureau, Summary of the Latest Month on Family Income and Expenditure Survey: `https://www.stat.go.jp/english/data/kakei/156.htm`
- Statistics Bureau FIES notices/results: `https://www.stat.go.jp/data/kakei/`

Reuters reported contemporaneous expectations of about `-1.6%` y/y and `+2.6%` m/m, so the release was a clear negative consumption surprise:

- `https://www.reuters.com/world/asia-pacific/japan-year-on-year-household-spending-drops-8-straight-months-2026-09-03/`

The data-vintage issue remains important. The Statistics Bureau explicitly records retrospective revisions to April-June 2026 real-change figures following the CPI rebasing to the 2025 base. That is a revision to published statistical history, not a change to the identity or date of the July release.

Japan nevertheless has low marginal schema novelty now:

- `MACROECONOMIC_RELEASE` is already repeatedly represented;
- `DATA_RELEASE` surprise semantics are already exercised;
- Analysis already separates expectation, actual, surprise, movement and alternative drivers;
- finishing the queue is tidiness, not an architectural objective.

Contemporaneous yen/rates context also has powerful competing drivers. A 4 September global-markets report described strong US jobs, US yields/dollar moves, oil and geopolitical pressures, while separate Japan reporting described broader BOJ expectations and currency-policy pressure. No event-specific yen/rates attribution should be manufactured from proximity to the household-spending release.

Japan is **held, not rejected**. It may become a useful future Live Intelligence or Analysis stress case because one publication cycle combines current data, retrospective revisions, consensus surprise and strong competing market narratives.

### B. Cross-event / interaction architecture — DEFER

The existing Analysis schema already contains disciplined per-review interaction vocabulary, including observation context, common-driver context, temporal coincidence, transmission and legal/operational dependency.

What does not yet exist is a durable shared cross-event relationship object or causal graph.

That absence is real, but building a graph now would be premature:

- the project still lacks the upstream Live Intelligence observation layer from which developing multi-event context would arise;
- a graph designed from only 20 retrospective review packets risks encoding post-hoc narrative structure;
- repeated reports, temporal adjacency and common drivers must not be automatically collapsed into one story or one causal edge.

AV therefore does **not** create stable story IDs, automatic clustering or a causal graph. A later real specimen should prove whether a shared interaction object is required and what identity semantics it needs.

### C. Live Intelligence architecture — SELECT

This is the clearest architectural discontinuity.

The Charter requires:

`Canonical Registry → Calendar → Source/Change Monitor → Live Intelligence → Analysis`

The repository currently has governed Canonical, monitor and Analysis stores, but no `data/live_intelligence/` contract. Analysis already treats Live Intelligence as upstream, so this is not speculative roadmap expansion; it is a missing layer in the declared architecture.

The gap matters operationally because unscheduled shocks and developing information should not be forced into either:

- Canonical timing objects, where they can distort event identity/lifecycle; or
- final Analysis packets, where factual observations can become mixed prematurely with interpretation.

AV should therefore create the minimum executable layer **without population**.

### D. Source/Change Monitor depth — DEFER

AS only just added a materially different EIA Weekly Petroleum Status Report schedule-sentinel contract. Post-AS monitor scope is deliberately bounded: 8 configured adapters, 43 explicitly scoped occurrences, 11 series, 6 institutions, 4 regions and 6 categories.

That footprint is narrow relative to Canonical, but narrowness is not itself a defect. It is a pilot-readiness question.

No immediately adjacent candidate identified in this audit offers greater marginal operational novelty than establishing the missing Live Intelligence contract. A ninth adapter should require a defensible endpoint, rights posture, parser contract and failure semantics — not regional histogram pressure.

### E. Source-governance bottlenecks — IMPORTANT, NOT SELECTED

AR established a substantial gap between sources used as canonical provenance and sources that are actually endpoint-validated, rights-cleared and production-monitorable. AT then admitted the IMD outlook source conservatively without implying automated-monitor permission.

That distinction remains central:

**official source exists ≠ safe production monitor route**.

Source-governance work remains necessary, but it is route-specific and evidence-specific. Broad rights/backfill work now would not resolve the architectural discontinuity between monitor observations and pre-Analysis situational intelligence.

### F. Canonical coverage gaps — HOLD AS DIAGNOSTIC PRESSURES

AT improved but did not eliminate South Asian and physical-risk shallowness. Post-AT/AU descriptive coverage is approximately:

- South Asia: `29 occurrences / 9 series / 7 institutions / 7 sources / 4 categories`;
- `PHYSICAL_CLIMATE_RISK`: `7 occurrences / 4 series / 4 institutions / 4 sources`.

Those remain useful prompts, not quotas.

Corporate/financial market structure also still lacks a completed Analysis anchor. Fresh JPX research confirms that genuine forward-looking market-structure contracts exist — for example official Last Trading Day / Delivery Day tables for derivatives in 2026 and 2027:

- `https://www.jpx.co.jp/english/derivatives/rules/last-trading-day/`

JPX explicitly notes that last trading days can change with national holidays. That is exactly the sort of real contract the Canonical layer may eventually model if it is consequential and source-governed. It is **not** permission to backfill a historical occurrence merely to turn a category zero into a one.

## Why Live Intelligence outranks the alternatives

The marginal-value ordering from this audit is:

1. **Live Intelligence foundation** — closes a Charter-required architectural gap and creates a safe place for current observations before interpretation;
2. **future interaction architecture** — probably important, but should be informed by real Live Intelligence specimens rather than imposed retrospectively;
3. **source-governance / monitor depth** — operationally important, but current adapter diversity is already sufficient to avoid adding a route for tidiness;
4. **Canonical coverage expansion** — still has real gaps, but AT/AU just added a genuinely new South Asian physical-risk contract;
5. **Japan Analysis #21** — analytically valid but lowest marginal contract novelty among the immediate choices.

This is a pivot from one-at-a-time Analysis population. `READY_FOR_CONTROLLED_EXPANSION` remains a permission state, not an instruction to keep consuming every eligible occurrence.

## What Live Intelligence should mean before post-event Analysis

AV deliberately keeps the first contract narrow.

### Current state

A current state is a **derived as-of view over verified factual observations**. It is not a new authoritative truth object and is not a causal conclusion.

### Developing story

A developing story may eventually group multiple observations, but AV does not invent a `story_id`, automatically cluster reports or assume repeated coverage describes one object. The first populated specimen should test whether durable grouping is needed.

### Market reaction

A price, yield, spread, volume or probability movement can be stored as a factual `MARKET_OBSERVATION` when evidence and rights permit. The Live Intelligence layer must not say the move was **caused by** a nearby event. Attribution remains Analysis.

### Competing explanation

Live Intelligence may preserve contemporaneous factual context that later supports alternative explanations. It does not rank those contexts as causes or choose a preferred explanation.

### Confidence

Live Intelligence uses `verification_state` for **factual verification status**. It does not borrow Analysis causal-confidence grades.

This preserves the distinction between “we have good evidence this happened” and “we are confident this caused something else.”

## Monitor → Live Intelligence bridge

A monitor result does not automatically become situational intelligence.

AV requires:

- source failure/absence remains monitor/source-health state, never a Live Intelligence fact;
- a monitor review candidate remains a monitor review candidate;
- positive monitor evidence requires a separate Live Intelligence evidence record before it can support a Live observation;
- no monitor candidate receives automatic promotion;
- no Live observation mutates Canonical, monitor state or Analysis.

This keeps `Source/Change Monitor` and `Live Intelligence` operationally distinct rather than renaming the monitor queue.

## Revision semantics pressure-tested with Japan

The initial AV draft treated every `DATA_REVISION` as a revision of a prior Live Intelligence observation. That was too restrictive.

External statistical revisions and corrections to WORLD SIGNALS' own prior observations are different contracts:

1. **External data revision** — an authority revises previously published data. Live Intelligence may record that fact even if the earlier release was never stored as a Live observation. It must describe the revision target and carry revision/correction evidence. It must not manufacture a historical Live row merely to satisfy referential integrity.
2. **Correction/retraction of a prior Live observation** — WORLD SIGNALS corrects or retracts something it previously stored. That must explicitly reference and preserve the earlier observation.

This distinction directly protects the Japan April-June rebasing case from synthetic back-history.

## Time handling

Live Intelligence observation time, source-publication time and real-world event time are separate concepts.

- `observed_at_utc` is the WORLD SIGNALS observation timestamp;
- source publication timing belongs to evidence;
- real-world event time is optional and must preserve evidence precision;
- a civil date must not be promoted to a clock time;
- where an authoritative exact event timestamp has native local time, the local datetime and IANA timezone may be preserved alongside matching UTC;
- Australia/Melbourne is never canonicalised merely because it is the home display timezone;
- Live evidence cannot backfill missing Canonical time.

## Foundation-only population gate

AV v0.1 deliberately rejects non-empty production observation and evidence population.

The foundation consists of:

1. `data/live_intelligence/schema.json`;
2. an empty observation store;
3. an empty Live Intelligence evidence registry;
4. validator + metadata-only public projection;
5. CI integration;
6. static-build metadata integration;
7. regression tests proving layer, time, revision and provenance boundaries.

There is no fake current-news feed and no automatic ingestion.

## Existing Analysis evidence is not migrated

The existing 91 Analysis evidence rows remain in `data/analysis/`.

AV must not retrospectively relabel them as Live Intelligence just to make the new layer appear populated. Analysis evidence supports a reviewed interpretation; future Live evidence supports a factual pre-interpretation observation. Any prospective cross-reference between the two should be introduced explicitly and tested.

## Descendant-test audit before any future Analysis growth

`tests/test_imd_heatwave_outlook_analysis_au.py` contains two kinds of assertions that must remain distinguished:

- **frozen AU historical plan/payload/exact-transform assertions** — these should remain exact;
- **live-or-simulated descendant assertions** — these currently assert exact live values `20 reviews / 18 event types / reviews v0.16 / 91 evidence` and therefore become a stale ceiling if a later Analysis tranche legitimately grows the datasets.

AV does not mutate Analysis, so those assertions remain true and should **not** be changed merely for anticipation.

Before any future Analysis population tranche writes, repair only the genuinely live descendant path so legitimate growth is accepted while preserving AU's exact historical checkpoint and transform contract.

## Documentation drift

The pre-AV operational docs materially lag the executable repository:

- README still reports Canonical `v0.20 / 669`, Source `v1.51 / 222`, monitor `v0.6` and six routes;
- PROJECT_STATUS opens on Canonical `v0.22 / 669`, Source `v1.63 / 225`, monitor `v0.7` and six routes;
- ARCHITECTURE describes only RBA + Colombia as live pilots and combines “Live Intelligence / Analysis” into one runtime item;
- ROADMAP still describes scheduled monitoring and Analysis as future stages.

AV should realign compact operational documentation to the post-#76 checkpoint and make clear that historical detail remains in tranche audits and Git history. This is documentation/recovery repair, not a governed-data mutation.

## Protected state

AV must not modify:

- `data/canonical/registry.json`;
- `data/canonical/schema.json`;
- `data/sources/registry.json`;
- `data/changes/ledger.json`;
- `data/monitor/expectations.json`;
- `data/monitor/operations_policy.json`;
- `data/coverage/biosecurity_overlay.json`;
- `data/analysis/schema.json`;
- `data/analysis/event_reviews.json`;
- `data/analysis/evidence_registry.json`.

Automatic canonical commit remains OFF. Google Calendar writes remain OFF. No controlled Canonical transaction is required because AV is additive architecture/documentation work only.

## Explicit non-goals

AV does **not**:

- review `WSO-MAC-B-0041`;
- populate Live Intelligence observations or evidence;
- ingest current news automatically;
- add market-data providers or infer reuse rights;
- migrate Analysis evidence;
- create a causal graph or automatic story clustering;
- add a monitor adapter;
- populate Canonical coverage;
- change Canonical lifecycle or timing;
- enable automatic canonical commits;
- write Google Calendar;
- auto-merge.

## Post-AV gate

After AV is manually merged, run a fresh pressure audit before population.

The next decision should compare possible first Live Intelligence specimens that genuinely stress the contract:

- unscheduled physical shock;
- health emergency;
- policy/geopolitical development;
- external data revision;
- rights-cleared market observation linked to an existing Canonical occurrence.

The specimen should be selected for contract pressure, international relevance, source quality and rights/provenance discipline — not convenience or headline prominence.
