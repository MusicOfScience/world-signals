# WORLD SIGNALS — energy / commodities breadth audit v0.1

**Audit date:** 2026-09-03  
**Canonical baseline:** v0.18 / 662 occurrences  
**Current category:** `ENERGY_COMMODITIES` — 28 occurrences / 6 series / 3 institutions / 4 used source IDs  
**Canonical mutation authorised by this audit:** **NO**

## Question

Does the current 28-occurrence footprint represent meaningful global energy/commodity breadth, or is occurrence density masking an oil/OECD-US concentration?

## Current canonical shape

The six current series are:

1. `WSER-COM-OPEC-VOL` — OPEC+ voluntary-adjustment review — OPEC — 1 occurrence.
2. `WSER-COM-OPEC-JMMC` — OPEC+ Joint Ministerial Monitoring Committee — OPEC — 1 occurrence.
3. `WSER-COM-OPEC-ONOMM` — OPEC and non-OPEC Ministerial Meeting — OPEC — 1 occurrence.
4. `WSER-COM-IEA-OMR` — IEA Oil Market Report — 4 occurrences.
5. `WSER-COM-EIA-STEO` — EIA Short-Term Energy Outlook — 5 occurrences.
6. `WSER-COM-EIA-WPSR` — EIA Weekly Petroleum Status Report — 16 occurrences.

Institutional distribution:

- U.S. Energy Information Administration: **21 occurrences**;
- International Energy Agency: **4**;
- OPEC: **3**.

Signal-family distribution:

- explicitly oil/petroleum-specific: **23 of 28 occurrences (82.1%)**;
- broad multi-energy outlook: **5 of 28**;
- dedicated global natural-gas data series: **0**;
- dedicated LNG data series: **0**;
- dedicated coal/electricity signal family: **0**;
- dedicated metals/critical-minerals signal family: **0**.

The 28-row count therefore materially overstates breadth.

## Authoritative candidate review

### 1. JODI Oil + Gas World Database updates — strongest information-catalyst candidate

**Authority:** Joint Organisations Data Initiative (JODI), coordinated through the International Energy Forum with partner organisations including APEC, Eurostat, GECF, IEA, IEF, OLADE, OPEC and UNSD.  
**Products:** JODI-Oil World Database + JODI-Gas World Database.  
**Official 2026 update schedule:** the first Oil and Gas World Database updates occur at **12:00 London time** on the same published dates. Remaining dates after the WORLD SIGNALS 3 September reference point are:

- **22 September 2026**;
- **21 October 2026**;
- **19 November 2026**;
- **21 December 2026**.

**Sources:** https://www.jodidata.org/oil/support/update-calendar.aspx ; https://www.jodidata.org/gas/support/update-calendar.aspx ; official combined schedule PDF.  
**Assessment:** `HIGH_VALUE_CANONICAL_CANDIDATE / SOURCE_BUNDLE / GAS_AND_OIL_DATA_TRANSPARENCY`

The combined official schedule explicitly states that the first JODI-Oil and JODI-Gas updates occur together. WORLD SIGNALS should therefore avoid two duplicate calendar rows. The natural model is **one publication occurrence with multiple `data_products[]`**, for example:

- JODI-Oil World Database update;
- JODI-Gas World Database update.

This is exactly the canonical `SOURCE_BUNDLE` pattern: one information-system event containing multiple independent data products at the same timestamp.

JODI-Gas materially improves the current category because it covers natural-gas production, consumption, pipeline trade, LNG imports/exports, storage and other flows across participating economies. JODI-Oil also supplies broad country-level oil production, demand, trade and stock data rather than a single-country petroleum report.

The calendar states that supplementary updates may occur after the first monthly update. Those later updates are observations/data revisions, not extra scheduled canonical occurrences unless separately material.

**Rights/automation:** JODI describes the databases as freely available and provides downloadable data, but its website terms reserve intellectual-property rights and do not establish unrestricted automated retrieval or redistribution. Canonical factual metadata and production crawler permission remain separate; source/endpoint review is required before live automation.

### 2. Gas Exporting Countries Forum 8th Summit — strong gas-producer policy candidate

**Authority:** Gas Exporting Countries Forum (GECF).  
**Official forward date:** the GECF states that the **8th GECF Summit will be hosted in Moscow on 27 October 2026**.  
**Source:** https://www.gecf.org/Events-Conferences/Events-HH/ArticleID/1689/GECF-Secretary-General-holds-high-level-meetings-on-the-sidelines-of-the-St-Petersburg-International-Economic-Forum-SPIEF-2026  
**Assessment:** `HIGH_VALUE_CANONICAL_CANDIDATE / GAS_PRODUCER_POLICY / HEADS_OF_STATE_SUMMIT`

This materially broadens producer-policy coverage beyond oil/OPEC. GECF member and observer countries span major gas/LNG producers across the Middle East, Africa, Eurasia, Latin America and Asia.

The GECF also confirms that its **28th Ministerial Meeting** is scheduled in Moscow in **October 2026**, but the official material reviewed in this pass does not establish an exact day. Do not derive a Ministerial Meeting date from proximity to the Summit.

The GECF Monthly Gas Market Report is substantively useful and currently has monthly editions through August 2026, but no authoritative forward publication-date calendar was established. Keep future MGMR releases in Source/Change Monitor until dated rather than extrapolating historical cadence.

**Rights/automation:** GECF publication material asserts copyright and restricts reproduction without express permission. No production automated-access permission was established. Manual factual provenance may be assessed separately; automated monitoring remains on hold pending rights/endpoint review.

### 3. International Copper Study Group autumn meeting — strong non-fossil commodity candidate

**Authority:** International Copper Study Group (ICSG), an intergovernmental organisation.  
**Official forward date:** the ICSG states that its next Study Group meetings will be held in Lisbon on **13 October 2026**.  
**Source:** https://icsg.org/meetings-and-events/  
**Assessment:** `HIGH_VALUE_CANONICAL_CANDIDATE / INDUSTRIAL_METALS / TRANSITION_SUPPLY_CHAIN`

ICSG meetings bring together government members, industry advisers and observers and are held twice yearly. At the April 2026 meeting the statistical process produced an updated global copper market forecast for 2026–27. Copper has material transmission channels through electrification, grids, construction, manufacturing, China demand, mine/smelter disruptions and investment.

The canonical object should be the **ICSG Study Group meeting**, not an invented forecast-release timestamp. If an authoritative source separately schedules the resulting forecast publication, that is a related information-release occurrence; if the release appears without advance timing, it belongs in Live Intelligence/observation until then.

**Rights/automation:** ICSG states that site material may not be reproduced without permission, while allowing reasonable extracts for comment/review with acknowledgement. Its statistical publications also include paid products. Production retrieval/redistribution is therefore a rights hold unless a separate authorised route is established. The meeting date remains usable as manually curated factual provenance subject to project source-governance rules.

### 4. Australian Resources and Energy Quarterly — high-value source family, no current authoritative forward date

**Authority:** Australian Government Department of Industry, Science and Resources, Office of the Chief Economist.  
**Publication:** Resources and Energy Quarterly (REQ).  
**Coverage:** global prices, production, consumption and outlook plus Australian export values/volumes/prices for major commodities including iron ore, coal, LNG, oil, gold and critical minerals.  
**Current official page:** lists June 2026 as the latest 2026 edition at the time of this audit. Historical editions show quarterly publication, but the page reviewed does **not** establish the exact date of a September or December 2026 edition.  
**Source:** https://www.industry.gov.au/publications/resources-and-energy-quarterly  
**Assessment:** `HIGH_VALUE_MONITOR_SOURCE / DO_NOT_EXTRAPOLATE_RELEASE_DATE`

REQ is analytically valuable because it would add Australian and Asia-facing resources intelligence and broaden the commodity mix far beyond oil. But WORLD SIGNALS must not infer an October 2026 release merely because the September 2025 edition appeared on 7 October, or infer a December date from earlier years.

Register/monitor the publication family and admit a canonical release occurrence only when the department publishes authoritative future timing or the actual release becomes an observation.

### 5. GECF Monthly Gas Market Report — useful but forward-date unavailable

**Authority:** GECF.  
**Current source:** https://www.gecf.org/Publications-Data/Monthly-Gas-Market-Report  
**Assessment:** `MONITOR_SOURCE / NO_FORWARD_OCCURRENCE_YET`

The report covers natural-gas consumption/production, pipeline and LNG trade, storage and prices. It would improve gas-market information breadth, but an exact future release calendar was not identified. Historical monthly cadence is not canonical schedule authority.

### 6. Additional EIA or IEA series — lower correction priority

There are many valid EIA and IEA energy publications, including gas, coal, electricity, renewables and critical-mineral reports. Some may ultimately belong in WORLD SIGNALS. However, the immediate coverage problem is **not lack of EIA/IEA rows**; those institutions already dominate or materially contribute to the current category.

New series from them should be added because they supply a unique material signal, not because they are easy to schedule or parse.

## Geographic / institutional interpretation

The current category is globally labelled because the products and producer groups affect global markets, but the institution set is narrow:

- one US government statistical agency;
- one OECD-centred intergovernmental energy agency;
- one oil-producer organisation.

The strongest correction candidates improve different axes:

- **JODI/IEF:** producer-consumer data transparency; broad country participation; oil + gas/LNG;
- **GECF:** gas-producer strategy and Heads-of-State politics; strong Global South/emerging-power membership;
- **ICSG:** intergovernmental industrial-metal market governance/forecasting;
- **Australian REQ:** resource-export and Asia-facing commodity outlook, including critical minerals, once authoritative timing exists.

This is a better correction than simply adding more weekly EIA reports.

## Decision

**No canonical population in this audit.**

Recommended bounded correction candidates for the later cross-audit population stage:

1. **JODI Oil+Gas World Database combined monthly update** — four remaining-2026 occurrences, modelled as one source-bundle series with two data products.
2. **8th GECF Summit — 27 October 2026** — one gas-producer-policy occurrence.
3. **ICSG autumn Study Group meeting — 13 October 2026** — one industrial-metals/critical-supply-chain occurrence.

Hold/monitor:

- GECF 28th Ministerial Meeting — October 2026 only; do not invent exact day;
- GECF Monthly Gas Market Report — no authoritative forward release dates found;
- Australian Resources and Energy Quarterly — high-value source family, but no authoritative exact future release date found in this pass;
- further IEA/EIA series — evaluate only for unique signal value after institutional/geographic correction.

Before population, complete source-identity registration/rights classification and audit the three proposed series together with the physical-risk and biosecurity findings. The final corrective tranche should remain small and should be selected for **marginal informational value**, not for equal category counts.

## Architecture invariant

Occurrence count is not coverage quality. A category with 28 rows can still be structurally narrow if 16 are one weekly US report and 23 of 28 are oil-specific.
