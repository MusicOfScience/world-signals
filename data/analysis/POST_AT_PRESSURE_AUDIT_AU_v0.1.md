# WORLD SIGNALS — post-AT pressure audit AU v0.1

**Reference date:** 2026-09-06  
**Exact post-#75 main:** `03a8f87f17570c2520edadf78237ed07d946107a`

## Frozen live checkpoint

- Canonical Registry: `v0.38 / 688`
- Canonical schema: `v0.52`
- Source Registry: `v1.80 / 243`
- Change Ledger: `v0.24 / 59`
- biosecurity overlay: `v0.13 @ v0.38 / 688`
- monitor expectations: `v0.10 / 8 adapters`
- Analysis schema: `v0.4`
- Analysis reviews: `v0.15 / 19`, checkpointed to Canonical `v0.37 / 687`
- Analysis evidence: `v0.15 / 85`
- reviewed event-type diversity: `17`
- production `EXACT_TIMESTAMP_SERIES`: `0`

AT added one new completed Canonical occurrence without an Analysis write. The completed Analysis-eligible frontier is therefore now 21 occurrences, of which 19 are reviewed.

## Decision

**Select `WSO-RISK-A-0002` — IMD updated hot-weather and heatwave outlook of 31 March 2026 — as AU, the first reviewed `PHYSICAL_RISK_OUTLOOK_RELEASE` specimen. Hold `WSO-MAC-B-0041` — Japan Family Income and Expenditure Survey, July 2026 — for later review.**

This is not a queue-completion exercise and not a decision to make the Analysis count cosmetically equal to twenty. The IMD specimen wins because it introduces a new analytical contract: a probabilistic seasonal physical-risk information catalyst followed by later monthly updates and shorter-horizon operational observations.

## Why IMD outranks Japan after AT

### A. IMD seasonal heatwave outlook — SELECT

The 31 March first-party IMD release:

- is a completed information publication, not the heatwave itself;
- provides an April–June 2026 seasonal outlook and an April monthly outlook;
- forecasts above-normal heatwave days across parts of eastern, central and northwestern India and the southeast peninsula;
- explicitly identifies potential transmission through public health, water, power demand, essential services, infrastructure/resource management and agriculture;
- sits inside an IMD forecast-update chain that includes monthly and shorter-horizon products.

For Analysis, the important problem is **not** “was the forecast right?”. It is whether WORLD SIGNALS can represent a seasonal risk outlook, later forecast updates and later observed/operational weather context without collapsing different horizons, geographies and evidence classes into a synthetic validation score or causal narrative.

This event type is currently unreviewed. AU therefore raises reviewed event-type diversity from 17 to 18 while adding a South Asian physical-risk analytical specimen.

### B. Japan household spending — HOLD, WITH DATA-VINTAGE WARNING

`WSO-MAC-B-0041` remains a valid completed Analysis candidate:

- July 2026 Family Income and Expenditure Survey;
- official release date 4 September 2026;
- `MACROECONOMIC_RELEASE / DATA_RELEASE`;
- East Asia / Statistics Bureau of Japan.

Fresh first-party review identifies an important wrinkle: on 4 September the Statistics Bureau retrospectively revised April–June 2026 real-change figures following the 2025-base CPI rebasing. That matters for any future Analysis packet because expectation, trend and historical-comparison values must be tagged to the vintage actually available at the relevant time.

It does **not** change the identity or timing of the July occurrence itself. No upstream Canonical correction is therefore required before AU. The current controlled sample already contains repeated macro/data-release semantics, so the data-vintage issue is important but does not outweigh the new physical-risk information contract.

## IMD analytical boundary

### What happened

On 31 March 2026 IMD published an updated April–June hot-weather outlook, including probabilistic temperature fields and heatwave-day anomalies. The Canonical occurrence is the publication event dated 31 March in `Asia/Kolkata`; April–June remains forecast/reference scope.

### What was expected

IMD's 28 February 2026 March–May outlook is defensible **official prior guidance** showing that elevated heatwave-day risk had already been signalled across broad parts of India.

But the windows are not identical:

- 28 February: March–May 2026;
- 31 March: April–June 2026 plus April monthly detail.

The earlier product is therefore context for prior official guidance, not a like-for-like forecast-error benchmark for the later release.

### What surprised

No competent pre-release benchmark was identified that forecast the content of the 31 March update at matching spatial and temporal resolution. AU must therefore use `NOT_ESTABLISHED`, with no invented scalar forecast-surprise score.

### What later evidence means

IMD's May and June monthly outlooks, and late-May / June shorter-horizon heatwave releases, show that the seasonal release sat within a continuing forecast and warning system. They can establish:

- forecast evolution;
- operational observation context;
- that heatwave conditions occurred or were forecast at shorter horizons in some regions.

They do **not** by themselves establish:

- seasonal forecast skill;
- a national hit/miss score;
- that spatial overlap is statistically meaningful skill;
- that later forecasts are consequences of the March publication;
- that the publication caused physical heatwaves, public-health outcomes, power demand or market moves.

## Schema decision

**No Analysis schema migration. Keep v0.4.**

The existing contract already supports:

- `OFFICIAL_PRIOR_GUIDANCE`;
- `NOT_ESTABLISHED` surprise;
- empty market movement;
- `OBSERVATION_CONTEXT`;
- `NOT_A_CAUSAL_CLAIM`;
- `PLAUSIBLE_WATCH_ITEM` or `NOT_ESTABLISHED` second-order effects;
- explicit alternatives and falsifiers.

The pressure is analytical discipline, not missing representation capacity.

## Second-order boundary

IMD itself identifies plausible preparedness and impact channels across public health, water, power, essential services, infrastructure/resource management and agriculture. AU may record these as **plausible watch items** because they are institutionally identified transmission channels.

AU must not upgrade them to observed second-order effects without separate evidence of realised responses or outcomes.

## Market boundary

No event-specific market response is established for the 31 March publication. `what_moved` remains empty. Heat-linked power demand, agricultural prices or equities must not be inferred from the existence of the outlook or from later heatwave conditions.

## Canonical / source boundary

AU is Analysis-only. It does not:

- alter the 31 March Canonical civil date or null UTC fields;
- convert April–June into occurrence timing;
- change Source Registry rights or monitoring status;
- add an IMD monitor adapter;
- add a future 2027 occurrence;
- mutate the biosecurity overlay;
- add physical-shock records;
- write Calendar or Google Calendar.

Analysis evidence remains analytically scoped and cannot become Canonical provenance merely by citation.

## Expected AU state if validated

- Canonical: `v0.38 / 688` unchanged
- Source Registry: `v1.80 / 243` unchanged
- Change Ledger: `v0.24 / 59` unchanged
- biosecurity overlay: `v0.13 @ v0.38 / 688` unchanged
- monitor expectations: `v0.10` unchanged
- Analysis schema: `v0.4` unchanged
- Analysis reviews: `v0.15 / 19` → `v0.16 / 20`
- Analysis review Canonical checkpoint: `v0.37 / 687` → `v0.38 / 688`
- Analysis evidence: `v0.15 / 85` → `v0.16 / 91`
- eligible completed occurrences: `21`
- reviewed occurrences: `20`
- reviewed event-type diversity: `18`
- reviewed `PHYSICAL_RISK_OUTLOOK_RELEASE`: `1`
- remaining completed/unreviewed: exactly `WSO-MAC-B-0041`
- production `EXACT_TIMESTAMP_SERIES`: `0`

## Descendant-test audit

AQ's historical plan and exact transform remain frozen at 19 reviews / 17 event types / Analysis v0.15 / 85 evidence. Its live-descendant regression currently hard-codes those values as permanent ceilings.

AU must narrowly repair only the live branch of `tests/test_eu_russia_sanctions_analysis_aq.py` so that it requires:

- reviewed count `>= 19`;
- event-type diversity `>= 17`;
- review/evidence versions `>= 0.15`;
- evidence rows `>= 85`;
- exactly one `SANCTIONS_PROCESS` contribution remains present.

The AQ plan, payload, frozen postconditions and exact historical transform must remain untouched.

## Research sources reviewed

Primary official sources:

- IMD, 31 Mar 2026 updated hot-weather / heatwave outlook: `https://internal.imd.gov.in/press_release/20260331_pr_4854.pdf`
- IMD, 28 Feb 2026 March–May hot-weather outlook: `https://internal.imd.gov.in/press_release/20260228_pr_4773.pdf`
- IMD, May 2026 monthly temperature/rainfall outlook: `https://internal.imd.gov.in/press_release/20260501_pr_4941.pdf`
- IMD press-release archive, including late-May heatwave updates and 29 May June outlook: `https://internal.imd.gov.in/pages/press_release_mausam.php`
- IMD June heatwave outlook: `https://internal.imd.gov.in/section/nhac/dynamic/heatwave_monthly_outlook.pdf`
- IMD 21 Jun 2026 operational release: `https://mausam.imd.gov.in/Forecast/marquee_data/Press%20Release%2021-06-2026.pdf`
- Statistics Bureau of Japan Family Income and Expenditure Survey and 4 Sep 2026 revision notices: `https://www.stat.go.jp/english/data/kakei/156.htm`, `https://www.stat.go.jp/data/kakei/sokuhou/tsuki/`, `https://www.stat.go.jp/data/kakei/`

## Next gate

Research → AU plan/payload → descendant-safe AQ repair → exact-base read-only simulation → validators → full suite → controlled Analysis-only transaction → exact mutation audit → temporary workflow removal → ordinary PR CI → manual merge.
