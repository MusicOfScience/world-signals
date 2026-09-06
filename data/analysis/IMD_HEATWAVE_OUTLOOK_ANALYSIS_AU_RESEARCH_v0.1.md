# WORLD SIGNALS — IMD heatwave outlook Analysis AU research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `03a8f87f17570c2520edadf78237ed07d946107a`  
**Target:** `WSO-RISK-A-0002`  
**Architecture layer:** Analysis

## Research question

How should WORLD SIGNALS analyse IMD's 31 March 2026 updated April–June hot-weather and heatwave outlook without conflating the publication with the physical hazard, treating non-identical forecast windows as a forecast-error benchmark, or promoting later short-horizon warnings into proof of seasonal forecast skill?

## Canonical object inherited without mutation

AU is bound to the existing AT occurrence:

- occurrence: `WSO-RISK-A-0002`
- series: `WSER-RISK-IN-HEAT-OUTLOOK`
- institution: India Meteorological Department
- region: South Asia
- category: `PHYSICAL_CLIMATE_RISK`
- event type: `PHYSICAL_RISK_OUTLOOK_RELEASE`
- signal object class: `SCHEDULED_INFORMATION_CATALYST`
- lifecycle: `COMPLETED`
- timing: `CIVIL_DATE`
- `start_local`: `2026-03-31`
- source timezone: `Asia/Kolkata`
- precision: `DAY`
- all-day semantics: true
- UTC endpoints: null
- physical-shock routing: `NO_SHOCK_IN_THIS_RECORD`

The April–June 2026 period is the forecast/reference period, not Canonical occurrence timing.

## Evidence review

### 1. 31 March 2026 IMD updated seasonal outlook — target outcome

Source: `https://internal.imd.gov.in/press_release/20260331_pr_4854.pdf`

The first-party release is dated 31 March 2026 and is titled “Updated Seasonal outlook for hot weather season (April to June) 2026 and Monthly Outlook for April 2026 for the Rainfall and Temperature”.

Material analytical facts:

- IMD describes use of a Multi-Model Ensemble based on coupled global climate models, including the Monsoon Mission Climate Forecast System.
- For April–June, above-normal heatwave days were considered likely over parts of eastern, central and northwestern India and the southeast peninsula.
- The same product carries a separate April-only heatwave outlook with more specific regional indications.
- IMD says increased heatwave likelihood can pose significant risks to public health, water resources, power demand and essential services, with additional pressure on infrastructure/resource-management systems.
- It advises state/district preparedness and describes weekly, extended-range, early-warning and impact-based forecast products as part of the wider operational chain.
- It separately discusses potential agricultural effects and agrometeorological advice.

Analytical consequence: the event is a **risk-information catalyst** with explicit transmission channels. It is not an observed heatwave event and cannot itself supply realised-impact evidence.

### 2. 28 February 2026 IMD March–May outlook — prior official guidance

Source: `https://internal.imd.gov.in/press_release/20260228_pr_4773.pdf`

The February product forecast above-normal heatwave days during March–May over most parts of east and east-central India, many parts of the southeast peninsula and some parts of northwest and west-central India. It also identifies the same broad public-health, water, power and essential-service risk channels.

This is useful `OFFICIAL_PRIOR_GUIDANCE`, but it is **not a matched forecast-error benchmark** for 31 March because:

- the February seasonal window is March–May;
- the March release updates to April–June and also adds an April monthly outlook;
- geography and product details are not identical;
- no reviewed evidence supplies a probability distribution for what the 31 March update itself was expected to contain.

Therefore forecast evolution can be described, but directional surprise for the 31 March publication remains `NOT_ESTABLISHED`.

### 3. 1 May 2026 IMD monthly outlook — forecast evolution

Source: `https://internal.imd.gov.in/press_release/20260501_pr_4941.pdf`

IMD's May monthly outlook expects above-normal heatwave days over parts of Himalayan foothills, east-coast states, Gujarat and Maharashtra. This is a subsequent, shorter-horizon forecast using updated information.

It is evidence of the forecast-update chain. It is not a realised outcome for the March seasonal forecast and should not be scored as one.

### 4. Late-May operational heatwave releases — shorter-horizon context

Source archive: `https://internal.imd.gov.in/pages/press_release_mausam.php`

The archive records repeated late-May releases stating heatwave to severe-heatwave conditions were likely to continue over parts of central, northwestern and eastern India, followed by a 29 May release saying the prevailing heatwave had abated from most of northwest India and was likely to abate from most of central India.

This demonstrates two things relevant to AU:

1. the physical-risk environment evolved materially within the AMJ season;
2. shorter-horizon products supersede coarse seasonal guidance for operational decisions.

It does not prove that the March seasonal forecast was globally correct or incorrect.

### 5. 29 May / June outlook — continuing monthly forecast chain

Sources:

- IMD archive entry for 29 May, “LONG RANGE FORECAST FOR THE SOUTHWEST MONSOON SEASONAL RAINFALL DURING JUNE–SEPTEMBER, 2026 AND MONTHLY RAINFALL AND TEMPERATURE OUTLOOK FOR JUNE 2026”
- dynamic June heatwave outlook: `https://internal.imd.gov.in/section/nhac/dynamic/heatwave_monthly_outlook.pdf`

The June outlook says above-normal heatwave days were expected over many parts of Uttar Pradesh, Haryana, Punjab, Bihar, Odisha, Chhattisgarh, Gujarat and Andhra Pradesh, with isolated regions of Maharashtra, Telangana, Himachal Pradesh and Tamil Nadu; below-normal heatwave days were likely over Rajasthan and Jharkhand.

Again, this is subsequent forecast information, not a direct observational verification dataset for the March seasonal product.

### 6. 21 June 2026 IMD operational release — observation/warning context

Source: `https://mausam.imd.gov.in/Forecast/marquee_data/Press%20Release%2021-06-2026.pdf`

The operational release reports/forecasts heatwave conditions in isolated pockets across several states during the late-June period, including severe heatwave conditions in isolated pockets of Vidarbha for part of the forecast interval.

This confirms that heatwave conditions were part of the later operational weather context. It does not by itself establish a quantitative seasonal skill score because:

- it is a short-horizon operational product;
- it covers selected days and regions, not a full AMJ verifying dataset;
- seasonal and short-range forecast targets differ;
- a rigorous skill claim would require a defined verifying observation series and metric.

## Analytical interpretation

### WHAT HAPPENED

IMD published a probabilistic seasonal heat-risk outlook with explicit geographic, temporal and transmission-channel content. The publication itself is the event.

### WHAT WAS EXPECTED

Earlier IMD official guidance had already signalled elevated heatwave-day risk over broad parts of India. This lowers the justification for treating the existence of elevated heat risk in the later update as a surprise, while still not providing a matched benchmark for the exact 31 March update.

### WHAT SURPRISED

`NOT_ESTABLISHED`.

No reviewed pre-release benchmark predicts the 31 March update's content at matching spatial/temporal resolution. Changing forecast windows must not be subtracted as though they were the same metric.

### WHAT MOVED

No qualified event-specific market movement established. `what_moved = []`.

### WHAT APPEARS CONNECTED

Use `OBSERVATION_CONTEXT / NOT_A_CAUSAL_CLAIM / HIGH`.

The connection is documentary and operational: the seasonal outlook belongs to a forecast system that is subsequently updated through monthly, extended-range and shorter-horizon products. Later heatwave conditions and warnings provide context for the risk environment in which the seasonal outlook operated.

This is not a claim that the March publication caused later forecasts, caused heatwaves or caused economic/health outcomes.

### WHAT MAY BE NOISE

AU should explicitly reject:

- publication date as hazard start date;
- AMJ window as event timing;
- February MAM and March AMJ forecasts as directly commensurable forecast-error values;
- later monthly forecasts as verifying observations;
- selected spatial overlap as a national skill score;
- late-May abatement as proof that the seasonal forecast failed;
- late-June heatwave conditions as proof that the seasonal forecast succeeded;
- contemporaneous heat-sensitive market moves as publication responses without event-specific evidence;
- exact clock/UTC inference from a date-only Canonical occurrence;
- future publication recurrence inferred from historical cadence.

### ALTERNATIVE EXPLANATIONS

Later regional heatwave conditions are driven by meteorological and climate-system evolution, not by publication of the seasonal outlook. Monthly/shorter-range forecasts have access to newer initial conditions and information. Spatial heterogeneity means selected state-level matches or mismatches can be misleading if treated as validation of a national seasonal map.

### SECOND ORDER

Use `PLAUSIBLE_WATCH_ITEM`.

The March release itself names public-health, water, power-demand, essential-service, infrastructure/resource-management and agricultural channels and recommends preparedness. AU may therefore retain these as institutionally identified prospective transmission channels.

No reviewed evidence packet demonstrates realised responses or quantified outcomes attributable to the publication, so `OBSERVED` would overstate the evidence.

## Market and causality discipline

No market response is required for a valuable Analysis specimen. The publication is likely more important as a preparedness/risk-information signal than as a clean tradable event.

Any later movement in Indian power prices, agricultural commodities, equities, insurance or demand variables would require independent timing, rights and attribution evidence. Temporal overlap with heat conditions would still not establish that the 31 March release caused those moves.

## Schema conclusion

Analysis schema v0.4 is sufficient. No schema change is justified.

## Evidence packet proposed for AU

All rows are `PRIMARY_OFFICIAL`, Analysis-only, `canonical_provenance_effect = NONE`:

1. `WSEV-IMD-HEAT-OUTLOOK-20260331` — target official seasonal outcome
2. `WSEV-IMD-HEAT-PRIOR-20260228` — prior official guidance
3. `WSEV-IMD-HEAT-MAY-OUTLOOK-20260501` — subsequent monthly forecast
4. `WSEV-IMD-HEAT-LATEMAY-ARCHIVE-20260529` — operational heatwave evolution/abatement context
5. `WSEV-IMD-HEAT-JUNE-OUTLOOK-20260529` — subsequent June monthly forecast
6. `WSEV-IMD-HEAT-JUNE-OPS-20260621` — late-June operational heatwave context

No evidence row is allowed to backfill Canonical timing or change Source Registry governance.

## Japan data-vintage side finding

The Statistics Bureau's 4 September 2026 July Family Income and Expenditure Survey release remains a legitimate future Analysis specimen. The same release date also carried retrospective revisions to April–June 2026 real-change rates following CPI rebasing to the 2025 base.

For later Japan Analysis, expectations and historical comparisons should preserve vintage. A revised April–June history must not be silently treated as information that was available before the 4 September release.

This side finding is analytically important but does not require an upstream Canonical change to the July occurrence and does not outrank AU's new event-type contract.

## Decision

Proceed to an Analysis-only AU transaction if exact-base simulation, descendant tests, validators and the full suite remain green.
