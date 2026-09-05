# WORLD SIGNALS — RBA financial-stability historical anchor AC research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `09433d3a6ed0aca957271be49777eab33f08ee72`  
**Architecture position:** upstream canonical historical-anchor repair, before any new Analysis write

## Why AC exists

Post-AA pressure audit AB showed that the reviewed sample no longer has a completed-anchor regional gap. The remaining upstream weakness is domain/event-type breadth. Seven categories present in the canonical registry still have no completed Analysis-eligible anchor:

- `CLIMATE_ENVIRONMENT`
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE`
- `ELECTIONS_GOVERNANCE`
- `FINANCIAL_STABILITY_REGULATION`
- `HEALTH_BIOSECURITY`
- `PHYSICAL_CLIMATE_RISK`
- `TRADE_SANCTIONS_INDUSTRIAL_POLICY`

AC first tested whether these were another lifecycle-maintenance problem like Z. A read-only probe found **81 canonical occurrences across 45 series** in the seven categories, but only one past-starting non-terminal occurrence: the 2026 Atlantic hurricane season. It is correctly `ACTIVE` through 30 November 2026. Therefore the remaining gaps are genuine historical-anchor gaps, not stale `PLANNED` records that should simply be completed.

## Candidate comparison

AC considered existing-series historical backfills before inventing new series or bespoke history.

### RBA Financial Stability Review — selected

Existing canonical series: `WSER-FIN-AU-RBA-FSR`  
Existing source: `WSSRC-FIN-001`  
Current forward occurrence: `WSO-FIN-B-0001` — RBA Financial Stability Review — October 2026

A March 2026 backfill repairs both:

- category `FINANCIAL_STABILITY_REGULATION`; and
- event type `FINANCIAL_STABILITY_REPORT`.

It reuses an exact existing series and existing official publication/RSS source, so it creates no new series taxonomy and no new source identity.

### WHO World Health Assembly 79 — strong alternative, not selected

The existing `WSER-HEALTH-WHA` lineage could support a May 2026 WHA79 historical anchor with strong WHO first-party evidence. It would repair `HEALTH_BIOSECURITY` / `HEALTH_GOVERNANCE_EVENT`. It remains an attractive later specimen, but AC selects the RBA FSR because the RBA case additionally exercises authoritative minute-level publication timing and a central-bank financial-stability publication distinct from already-reviewed monetary-policy decisions.

### Elections/governance — deferred

Existing future election lineages include New Zealand, Brazil, Nigeria, Kenya, Victoria and South Africa. A South Korea June 2026 local-election anchor would require new series/source architecture rather than reusing an exact current lineage. AC does not create a fresh series merely to fill a category gap when a cleaner exact-lineage specimen exists.

### Climate/environment, trade/sanctions and market structure — deferred

These domains have plausible historical candidates, but several would require a new sub-series, a legal/implementation-boundary interpretation, or a lower-value mechanical market event. They remain candidates for subsequent controlled expansion rather than quota-filling.

## First-party RBA evidence

### FSR publication series / recurrence

RBA Financial Stability Review landing page:  
`https://www.rba.gov.au/publications/fsr/`

The RBA states that the FSR is published twice yearly, shortly after the March and September Monetary Policy Board meetings. The page identifies **19 March 2026** as the last publication and **1 October 2026** as the next publication.

### March 2026 Review

RBA March 2026 FSR:  
`https://www.rba.gov.au/publications/fsr/2026/mar/`

This is the source-native historical publication in the same official FSR family monitored by `WSSRC-FIN-001`.

### Post-event completion evidence

RBA media release 2026-09:  
`https://www.rba.gov.au/media-releases/2026/mr-26-09.html`

The RBA states on 19 March 2026 that it **today released its March 2026 Financial Stability Review**. The release describes the Review's assessment that global financial-system risks had increased while Australia's financial system remained well placed to handle the uncertain environment.

### Authoritative publication clock time

RBA News & Announcements archive:  
`https://www.rba.gov.au/news/`

The RBA records both the March 2026 Financial Stability Review and its media release at **19 March 2026, 11:30 am AEDT**.

Canonical timing therefore is:

- native/local: `2026-03-19T11:30:00`
- native IANA timezone: `Australia/Sydney`
- source timezone label: AEDT
- UTC: `2026-03-19T00:30:00Z`
- precision: minute
- basis: `EXPLICIT_AUTHORITATIVE_SCHEDULE`.

The UTC conversion follows the authoritative local timestamp; Melbourne time is not stored as canonical time.

## Source/provenance decision

`WSSRC-FIN-001` already describes the RBA's **Financial Stability Review publication schedule and RSS**, with authoritative URL `https://www.rba.gov.au/publications/fsr/`, source timezone `Australia/Sydney`, and live adapter `RBA_FSR_RSS`.

The repository's adapter fixture already includes `Financial Stability Review - March 2026` from the official FSR feed. The March occurrence is therefore within the existing endpoint/source contract. AC does **not** create a duplicate source merely because the historical publication has a child URL.

The direct March FSR URL is attached to the occurrence as `COMPLETION_OUTCOME_VERIFICATION`. The media release remains explicit research/ledger review evidence.

The current source-governance model does not require a legacy `canonical_dependency_count` helper on this source. Canonical truth is authoritative, so the source registry remains byte-identical.

## Historical-admission semantics

The new occurrence is admitted directly as `COMPLETED` because competent first-party post-event evidence establishes that the Review was released.

This is **not** completion inferred from elapsed time.

The historical occurrence reuses:

- series: `WSER-FIN-AU-RBA-FSR`
- source: `WSSRC-FIN-001`
- category: `FINANCIAL_STABILITY_REGULATION`
- event type: `FINANCIAL_STABILITY_REPORT`
- institution: Reserve Bank of Australia
- jurisdiction: Australia
- region: Oceania / Pacific
- intrinsic importance: `HIGH`
- expected market sensitivity: `MEDIUM`.

Stable new occurrence identity: `WSO-FIN-B-0004`.

## Expected post-state

- canonical registry: v0.31 / 681 → **v0.32 / 682**
- source registry: **v1.73 / 239 unchanged**
- change ledger: v0.18 / 53 → **v0.19 / 54**
- biosecurity overlay: v0.6 checkpoint v0.31/681 → **v0.7 checkpoint v0.32/682**, semantic content unchanged
- Analysis schema: **v0.3 unchanged**
- Analysis reviews: **v0.8 / 12 unchanged**
- Analysis evidence: **v0.8 / 44 unchanged**
- completed Analysis-eligible occurrences: 14 → **15**
- reviewed completed occurrences: **12 unchanged**.

After AC, `FINANCIAL_STABILITY_REGULATION` and `FINANCIAL_STABILITY_REPORT` should no longer appear among completed-anchor gaps. This does not make the population representative and does not create an obligation to fill every remaining gap immediately.
