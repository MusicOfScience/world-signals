# WORLD SIGNALS — Australian tropical cyclone season Analysis AJ research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `c85db2ec3a675a749acb8201705fb6f1f85de27d`  
**Architecture position:** Analysis; no Canonical Registry, Source/Change Monitor or Calendar write

## Why AJ exists

PR #64 moved the Analysis layer to v0.9 / 13 reviews / 50 evidence while leaving the canonical registry at v0.37 / 687. The completed Analysis-eligible population is 20 occurrences; seven remain unreviewed.

The remaining upstream completed-anchor category gap is `CORPORATE_FINANCIAL_MARKET_STRUCTURE`, but the charter does not permit queue or histogram completion to substitute for marginal analytical value. A mechanical ASX/CME expiry remains useful later, but it would add less Analysis-contract pressure than the first reviewed seasonal physical-risk window.

AJ therefore selects `WSO-RISK-AU-TC-2025-26` — Australian tropical cyclone season 2025–26.

This specimen adds:

- first reviewed `PHYSICAL_CLIMATE_RISK` category;
- first reviewed `PHYSICAL_RISK_WINDOW` event type;
- first Analysis object whose canonical time is a regional all-day seasonal range rather than a release timestamp, civil-date milestone or meeting window;
- a direct test of whether climatology is incorrectly promoted into a season-specific forecast;
- a direct test of whether realised hazard counts are incorrectly promoted into damage, market response or climate attribution.

The selection does not claim Australia is under-represented in the sample. It is chosen for object-class and causal-discipline novelty, not geographic quota repair.

## Canonical target

Existing completed occurrence:

- occurrence: `WSO-RISK-AU-TC-2025-26`
- series: `WSER-RISK-AU-TC`
- institution: Australian Bureau of Meteorology
- jurisdiction: Australian region
- region: Oceania / Pacific
- category: `PHYSICAL_CLIMATE_RISK`
- event type: `PHYSICAL_RISK_WINDOW`
- lifecycle: `COMPLETED`
- canonical window: 1 November 2025 through 30 April 2026
- timing: `ALL_DAY_RANGE`
- precision: `DAY`
- source timezone: null
- UTC endpoints: null.

AJ preserves the AF boundary: a regional seasonal risk window does not acquire a synthetic single timezone or UTC release clock.

## First-party evidence

### 1. Bureau Australian tropical cyclone season planning surface

`https://www.bom.gov.au/climate/cyclones/australia/`

The Bureau states that the official Australian-region tropical cyclone season runs from **1 November to 30 April**. The page, last updated October 2025, gives planning climatology of approximately **10 tropical cyclones per season, with 3–4 making landfall** based on seasons since 1980–81. It also notes that year-to-year activity varies substantially and that only one tropical cyclone is required to create significant community impacts.

This material is an official climatological/planning baseline. AJ must **not** relabel the long-run average as a probabilistic forecast for 2025–26.

### 2. Bureau Tropical Climate Update — 14 October 2025

`https://www.bom.gov.au/climate/tropical-note/archive/20251014.archive.shtml`

The contemporaneous archived update says tropical-cyclone risk increases from November to April, describes that period as the official Australian-region season, and directs readers to the updated season outlook/planning material. It stresses that a single cyclone can significantly affect communities and that tropical lows and offshore cyclones can also have major impacts.

The archived update establishes pre-season risk framing, but does not provide a reviewed numerical 2025–26 Australian-region count forecast that would justify a directional surprise classification.

### 3. Bureau 2025–26 northern wet-season summary — issued 14 May 2026

`https://www.bom.gov.au/climate/current/season/tropics/summary.shtml`

The Bureau reports:

- **11** tropical cyclones formed in or moved into the Australian region;
- the all-season average since 1980–81 is **10**, making the season slightly above average by raw count;
- **7** cyclones reached severe intensity, Category 3 or greater;
- Severe TC Narelle and Severe TC Maila reached Category 5;
- **4** cyclones — Fina, Luana, Hayley and Narelle — made mainland landfall at tropical-cyclone strength;
- **2** additional systems — Mitchell and Koji — crossed at tropical-low strength.

The same summary records very warm regional sea-surface temperatures and a wet northern season. Those are contextual climate observations, not proof that a single driver caused the cyclone count or severity distribution.

### 4. Bureau post-season news summary — issued 14 May 2026

`https://www.bom.gov.au/news-and-media/northern-australias-2025-26-wet-season-summary-now-available`

The Bureau characterises the 11 cyclones as close to the average of 10, reports six cyclone/low land crossings and seven severe cyclones, and notes that sea-surface temperatures around northern Australia were the fourth warmest on record while the Coral Sea was the warmest on record for the second consecutive wet season.

This corroborates the outcome and reinforces why raw cyclone count alone is an incomplete severity or impact measure.

## Expectation discipline

AJ uses the Bureau climatology only as `OTHER_DEFENSIBLE_EXPECTATION` context:

- average Australian-region tropical cyclones per season: 10;
- typical mainland landfalls: 3–4.

Those values describe a historical distribution, not a season-specific point prediction. Therefore:

- actual 11 versus climatological 10 does **not** automatically equal an upside surprise;
- actual 4 cyclone-strength mainland landfalls versus typical 3–4 does **not** establish a surprise;
- seven severe cyclones cannot be compared with a season-specific severe-count forecast because AJ has not established such a forecast from the reviewed pre-season first-party material.

`what_surprised.status` is consequently `NOT_ESTABLISHED`.

A later discovery of an authoritative archived 2025–26 probability/count forecast would require re-opening this classification.

## Hazard outcome is not market outcome

AJ writes no `what_moved` row.

The canonical object's expected market sensitivity is not permission to invent a market proxy. The season contains multiple distinct cyclones, landfalls, locations and impact pathways across six months. Any defensible economic or market analysis must bind to separately specified shock occurrences, exposures and measurement windows.

Therefore:

**season window ≠ named cyclone ≠ landfall ≠ insured loss ≠ supply disruption ≠ commodity move ≠ GDP effect ≠ market response.**

The AF routing rule remains controlling: realised physical shocks route to separate shock objects where warranted.

## Climate/context discipline

The Bureau records very warm regional and Coral Sea SSTs and substantial year-to-year variability. Bureau planning material also explains that warmer oceans can contribute to more intense cyclones and rainfall. AJ may record those facts as `COMMON_DRIVER_CONTEXT` while retaining `NOT_A_CAUSAL_CLAIM`.

AJ does **not** claim:

- the 2025–26 cyclone count was caused by climate change;
- seven severe cyclones were caused by one climate driver;
- the season's rainfall anomaly was caused by tropical cyclones alone;
- cyclone count is a damage metric;
- landfall count is an economic-loss metric.

## Selection versus remaining frontier

After AJ, the following completed anchors remain legitimate future Analysis specimens:

- RBA Financial Stability Review — March 2026;
- 79th World Health Assembly;
- South Korea local elections;
- UNFCCC SB64;
- EU Russia sanctions renewal;
- Japan household spending.

The RBA FSR remains particularly useful for financial-stability semantics, but the BoC tranche already exercised exact canonical timing versus non-exact market precision. The physical-risk window therefore has greater immediate marginal object-class novelty.

`CORPORATE_FINANCIAL_MARKET_STRUCTURE` remains an upstream canonical completed-anchor gap and is not repaired in AJ merely to eliminate the final zero.

## Expected Analysis post-state

- canonical registry: v0.37 / 687 unchanged
- source registry: v1.78 / 242 unchanged
- change ledger: v0.24 / 59 unchanged
- biosecurity overlay: v0.12 at canonical v0.37 / 687 unchanged
- Analysis schema: v0.3 unchanged
- Analysis reviews: v0.10 / 14
- Analysis evidence: v0.10 / 54
- completed eligible: 20
- reviewed completed: 14
- reviewed event-type diversity: 12
- reviewed `PHYSICAL_RISK_WINDOW`: 1
- `EXACT_TIMESTAMP_SERIES`: 0.

PR #40 remains untouched. Manual merge only.
