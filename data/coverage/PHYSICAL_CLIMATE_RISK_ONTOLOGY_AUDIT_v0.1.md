# WORLD SIGNALS — physical climate risk ontology/source audit v0.1

**Audit date:** 2026-09-03  
**Canonical baseline:** v0.18 / 662 occurrences  
**Current category:** `PHYSICAL_CLIMATE_RISK` — 4 occurrences / 2 series / 2 institutions / 2 sources  
**Canonical mutation authorised by this audit:** **NO**

## Question

Does the `<5 unique series` diagnostic indicate a simple population gap, or is the current `PHYSICAL_CLIMATE_RISK` footprint partly constrained by ontology and source-precision differences?

## Current canonical shape

The category currently contains only formal tropical-cyclone seasonal risk windows:

1. `WSER-RISK-ATL-HURR` — Atlantic hurricane season — NOAA National Hurricane Center — exact annual window **1 June–30 November**.
2. `WSER-RISK-AU-TC` — Australian tropical cyclone season — Australian Bureau of Meteorology — exact annual window **1 November–30 April**.

The category is therefore not a general inventory of climate, weather, forecast or disaster events. It is presently a narrow class of **scheduled physical-hazard exposure windows**. Actual storms/disruptions remain Shock/Live Intelligence objects.

## Authoritative candidate review

### 1. Eastern Pacific hurricane season — authoritative but deprioritised

**Authority:** NOAA National Hurricane Center  
**Official season:** **15 May–30 November**.  
**Source:** https://www.nhc.noaa.gov/climo/  
**Assessment:** `CANONICAL_SEMANTICS_STRONG / POPULATION_DEPRIORITISED`

NHC explicitly defines an official Eastern Pacific hurricane season. It could be represented with the same exact-day-range semantics as the existing Atlantic series.

However, adding it now would increase series count without increasing institutional diversity and would deepen NOAA/US-basin concentration. It must not be admitted merely to clear the `<5 series` diagnostic.

### 2. Central Pacific hurricane season — authoritative but deprioritised

**Authority:** NOAA / Central Pacific Hurricane Center  
**Official season:** **1 June–30 November**.  
**Sources:** https://www.nhc.noaa.gov/aboutgloss.shtml ; https://www.weather.gov/hfo/hurricaneOutlook2026  
**Assessment:** `CANONICAL_SEMANTICS_STRONG / POPULATION_DEPRIORITISED`

The season has an explicit official bounded window, but the same institutional/geographic-bias argument applies as for Eastern Pacific.

### 3. Southwest Pacific tropical-cyclone season — high-value candidate, precision issue

**Authority:** Fiji Meteorological Service / RSMC Nadi Tropical Cyclone Centre  
**Regional wording:** tropical-cyclone season in the RSMC Nadi area is **November–April**.  
**Fiji-specific wording:** current official products state the season begins **1 November** and continues until **30 April**.  
**Sources:** https://www.met.gov.fj/climate-services/2025-26-tc-outlook/ ; https://www.met.gov.fj/media/climate_product_files/FSCRO_December_2025.pdf  
**Assessment:** `HIGH_VALUE_SOURCE_CANDIDATE / ONTOLOGY_REVIEW_REQUIRED`

This is a materially better coverage candidate than adding another NOAA basin because it adds Pacific institutional authority and a distinct hazard geography.

But the regional RSMC statement is month-bounded while the exact 1-November/30-April wording is explicit for Fiji. WORLD SIGNALS must not silently promote regional `November–April` precision into exact regional day boundaries.

### 4. North Indian Ocean cyclone seasons — high-value candidate, multi-phase issue

**Authority:** India Meteorological Department / RSMC New Delhi  
**Official wording:** the North Indian Ocean has **two cyclone seasons: April–June and October–December**.  
**Source:** https://rsmcnewdelhi.imd.gov.in/uploads/home/conference/pce.pdf  
**Assessment:** `HIGH_VALUE_SOURCE_CANDIDATE / MULTI_PHASE_ONTOLOGY_REQUIRED`

This candidate is analytically strong because it adds South Asian physical-risk coverage and a new institutional authority rather than duplicating an existing US source family.

It cannot be modelled honestly as one continuous annual risk window. The source explicitly defines **two non-contiguous phases**, and only month precision is supplied. The canonical model therefore needs phase-preserving month-bounded seasonal semantics before population.

### 5. South-West Indian Ocean cyclone season — hold pending semantic resolution

**Authorities examined:** WMO Tropical Cyclone Committee / RSMC La Réunion / Météo-France  
**Sources:** https://wmo.int/content/tropical-cyclone-naming/southwest-indian-ocean-names ; https://meteofrance.re/fr/climat/tendance-saisonniere-dactivite-cyclonique-dans-le-sud-ouest-de-locean-indien-saison-2025  
**Assessment:** `HOLD_SEASON_BOUNDARY_SEMANTICS`

WMO has authoritative named cyclone-season references, including 2026–27. Météo-France also publishes authoritative seasonal tropical-cyclone outlooks. But the material examined distinguishes the administrative/reference cyclone season from the climatological high-risk portion of the year. Météo-France material refers to a season change on **1 July**, while seasonal-risk discussion concentrates activity much later.

WORLD SIGNALS should not choose one of these meanings and call it the physical-risk window without resolving the institutional semantics first.

### 6. Western North Pacific / Hong Kong — dynamic outlook, not stable basin window

**Authority examined:** Hong Kong Observatory  
**General wording:** May–November is *generally* the tropical-cyclone season for Hong Kong.  
**2026 outlook:** the season was expected to start **June or later** and end **October or before**.  
**Sources:** https://www.hko.gov.hk/en/education/tropical-cyclone/tracking/00707-Weather-Systems-Mix-and-Match-Tropical-Cyclone-Track.html ; https://www.hko.gov.hk/en/Whats-New/110457/Annual-Outlook-for-2026  
**Assessment:** `MONITOR_OR_OUTLOOK_OBJECT / NOT_RECURRING_FIXED_WINDOW`

The annual outlook can shift expected start/end timing. A fixed May–November recurring canonical window would overstate certainty and confuse climatological tendency with a deterministic event boundary.

### 7. India southwest monsoon — authoritative climate season, wrong object class

**Authority:** India Meteorological Department  
**Official period:** southwest monsoon season **June–September**.  
**Source:** https://mausam.imd.gov.in/imd_latest/contents/hydrological-services.php  
**Assessment:** `DO_NOT_FORCE_INTO_PHYSICAL_CLIMATE_RISK`

The monsoon is systemically important for agriculture, inflation, hydrology, power demand and growth, but the season itself is a climate-driver period rather than a discrete physical hazard window. Treating the whole monsoon as `PHYSICAL_CLIMATE_RISK` would conflate climatic state with hazard.

If WORLD SIGNALS later admits climate-driver windows, they require a distinct object class and explicit transmission semantics.

## Scheduled risk-information catalysts are separate objects

A tropical-cyclone seasonal outlook, monsoon long-range forecast or climate-risk update is **not the same occurrence** as the season/risk window it describes.

Candidate information-catalyst families include:

- RSMC Nadi tropical-cyclone seasonal outlook;
- NOAA seasonal hurricane outlooks;
- WMO/RSMC La Réunion South-West Indian Ocean tropical-cyclone outlook/miniforum;
- IMD pre-cyclone preparedness/outlook material and southwest-monsoon long-range forecasts.

These should use a separate event type such as `PHYSICAL_RISK_OUTLOOK_RELEASE` if admitted. Where no authoritative future publication date exists, the expected annual publication window belongs in Source/Change Monitor, not as an invented exact canonical date.

## Rights / automation separation

### Fiji Meteorological Service

Current official pages carry **All Rights Reserved** notices and historical-data request terms contain reuse constraints. No production automated-retrieval permission was established in this pass.

**Source-governance state:** manual curated factual provenance may be assessed separately; production automation remains **HOLD** pending fuller rights/access review.

### IMD / RSMC New Delhi

The RSMC copyright policy states that website content may not be reproduced partially or fully without due permission, while requiring attribution where referenced.

**Source-governance state:** authoritative factual source; production automation/reproduction remains **HOLD** pending permission or an authorised alternative route.

These rights states do not negate the factual authority of the source and do not themselves authorise or prohibit a manually reviewed canonical fact. Canonical provenance fitness and automated-monitor permission remain separate gates.

## Ontology finding

The current diagnostic is **partly an ontology artefact**, not merely a missing-data count.

WORLD SIGNALS currently handles exact all-day hazard ranges well, but the high-value missing global sources require at least two additional precision patterns:

1. `MONTH_BOUNDED_SEASON_WINDOW`
   - source asserts named start/end months, not exact dates;
   - preserve `time_precision=MONTH`;
   - do not manufacture first/last-day certainty unless explicitly supplied.

2. `MULTI_PHASE_SEASON_WINDOW`
   - one stable seasonal signal family has two or more non-contiguous authoritative phases;
   - preserve each phase independently and in order;
   - do not collapse phases into one continuous range.

A third class should remain monitor/outlook-only unless explicitly bounded:

3. `DYNAMIC_SEASON_OUTLOOK`
   - authority forecasts when a hazard season is likely to start/end in a particular year;
   - annual outlook is an information assertion, not a permanent recurring calendar boundary.

## Decision

**No canonical population in this pass.**

Do not add Eastern/Central Pacific merely to cross the five-series threshold.

Priority for architecture/source work:

1. add month-bounded seasonal precision semantics without inventing day precision;
2. add non-contiguous phase semantics for recurring physical-risk windows;
3. preserve risk-window and risk-outlook-release object classes separately;
4. then reconsider **Southwest Pacific** and **North Indian Ocean** as the first bounded corrective candidates;
5. keep South-West Indian Ocean under semantic/source review;
6. keep Western North Pacific/Hong Kong as dynamic outlook/monitor material unless an authoritative fixed basin rule is established;
7. keep climate-driver periods such as the southwest monsoon out of `PHYSICAL_CLIMATE_RISK` until a distinct climate-driver ontology is justified.

This decision intentionally prioritises international and Global South/Pacific coverage over mechanically clearing a series-count diagnostic with additional NOAA rows.
