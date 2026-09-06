# WORLD SIGNALS — IMD hot-weather / heatwave outlook AT research v0.1

**Research date:** 2026-09-06
**Exact base main:** `92bf6cba7506483dd861680924879b1ded0f4ddc`

## Research question

Can WORLD SIGNALS add one high-value South Asian physical-risk information catalyst without:

- manufacturing a hazard-season boundary;
- forcing the unresolved North Indian Ocean cyclone-season definition;
- inferring a future recurring publication date;
- weakening source-governance controls; or
- opening an unnecessary new Analysis/Monitor tranche?

## Selected first-party occurrence evidence

### India Meteorological Department — 31 March 2026 press release

Primary source:

`https://mausam.imd.gov.in/pdfs/heatcolduser/heat_outlook.pdf`

Official title:

> Updated Seasonal outlook for hot weather season (April to June) 2026 and Monthly Outlook for April 2026 for the Rainfall and Temperature

The first page identifies:

- Government of India;
- Ministry of Earth Sciences;
- India Meteorological Department;
- New Delhi;
- date **31 March 2026**.

The release establishes a discrete publication occurrence on that civil date. No publication clock time is stated in the document and none is inferred.

### Heatwave information content

The release states that:

- the 2026 hot-weather seasonal outlook covers April–June 2026;
- Section 3 is a dedicated heatwave outlook for April–June 2026 and April 2026;
- above-normal numbers of heatwave days were forecast for parts of east, central and northwest India and the southeast peninsula during April–June;
- possible impacts include public health, water resources, power demand, essential services, infrastructure/resource management and agriculture;
- State/district preparedness is explicitly discussed.

This supports `PHYSICAL_CLIMATE_RISK` relevance without turning the forecast period itself into a physical-risk-window occurrence.

## Standing IMD heatwave context

IMD Heat Wave FAQ:

`https://mausam.imd.gov.in/pdfs/heatcolduser/FAQ_heat_wave.pdf`

The FAQ says heat waves in India occur mainly from March to June, with rare July cases, and describes IMD's seasonal/extended-range/medium-range forecast chain.

This is **context only**. It is not converted into a recurring March–June canonical hazard window. The wording is climatological and the 2026 seasonal products themselves use differing forecast periods (including March–May and April–June updates).

## Canonical object-class finding

Existing canonical schema v0.52 already provides:

- `signal_object_class = SCHEDULED_INFORMATION_CATALYST`;
- `publication_time_semantics = DATE_ONLY`;
- `timing_type = CIVIL_DATE`;
- a design decision separating scheduled information catalysts, physical-risk windows and unscheduled physical shocks;
- a design decision that a dynamic annual season outlook is an information assertion and remains separate from a stable `PHYSICAL_RISK_WINDOW` unless the authority explicitly establishes that window.

The earlier physical-risk ontology audit explicitly proposed a separate event type such as `PHYSICAL_RISK_OUTLOOK_RELEASE` for seasonal outlooks.

**Finding:** no schema migration is necessary for this one sample. The new event type can specialize the already-defined `SCHEDULED_INFORMATION_CATALYST` object class.

## Why the North Indian Ocean cyclone season remains deferred

### Current WMO plan inventory

WMO current operational-plan index:

`https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/tropical-cyclone-programme-tcp/tropical-cyclone-operational-plans`

It lists:

- TCP-21;
- WMO/ESCAP Panel on Tropical Cyclones;
- *Tropical Cyclone Operational Plan for the Bay of Bengal and the Arabian Sea*;
- **Edition 2025**.

RSMC New Delhi TCP-21 index:

`https://rsmcnewdelhi.imd.gov.in/report.php?internal_menu=Mjg%3D`

It also lists **TCP-21 Edition 2025** as the current edition.

### Accessible competing definitions

IMD pre-cyclone exercise source reviewed in the earlier physical-risk audit:

`https://rsmcnewdelhi.imd.gov.in/uploads/home/conference/pce.pdf`

Wording recorded by the earlier reviewed audit:

- two cyclone seasons: **April–June** and **October–December**.

Accessible TCP-21 Edition 2021:

`https://rsmcnewdelhi.imd.gov.in/uploads/report/28/28_06dbff_TCP-21_Edition%202021.pdf`

Wording:

- storm season: **April–May** and **October–December**.

The current 2025 plan exists, but the exact current storm-season definition could not be extracted from the reviewed transport in this pass. Existence of a newer plan is not evidence that either older boundary survived unchanged.

**Finding:** retain `WSFR-RISK-NIO-TC` as `OFFICIAL_SOURCE_DEFINITION_CONFLICT`. Do not choose April–May or April–June.

## Source authority

IMD mandate:

`https://mausam.imd.gov.in/imd_latest/contents/mandate.php`

IMD identifies itself as India's National Meteorological Service and principal government agency for meteorology and allied subjects, including warnings for heat waves and other severe weather.

The 31 March press release is therefore competent first-party evidence for the publication event and its forecast content.

## Source-governance / rights finding

Primary publication surface:

- `mausam.imd.gov.in`
- institutional pages and PDF carry Ministry of Earth Sciences / IMD copyright notices;
- no reviewed unrestricted production-automation or redistribution grant was established for the intended route.

IMD disclaimer:

`https://mausam.imd.gov.in/imd_latest/contents/disclaimer.php`

RSMC New Delhi has an explicit copyright policy:

`https://rsmcnewdelhi.imd.gov.in/copyright-policy.php`

which says RSMC website content may not be reproduced partially or fully without permission and requires source acknowledgement when referenced.

However, WORLD SIGNALS **does not inherit that RSMC policy automatically onto the separate mausam.imd.gov.in surface**. The source-governance decision for the new source is conservative because no positive production-automation/reuse grant was established for the actual IMD publication route.

Proposed source state:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`
- `monitoring_readiness_status = RIGHTS_OR_LICENSE_HOLD`

This is an operational governance classification, not a legal opinion.

## Proposed stable identities

- occurrence: `WSO-RISK-A-0002`
- series: `WSER-RISK-IN-HEAT-OUTLOOK`
- source: `WSSRC-RISK-005`

All three were absent from exact post-#74 main at research time.

## Proposed occurrence semantics

- canonical name: `IMD updated hot-weather and heatwave outlook — April–June 2026`
- category: `PHYSICAL_CLIMATE_RISK`
- subcategory: `seasonal_heatwave_outlook_release`
- jurisdiction: `India`
- region: `South Asia`
- institution: `India Meteorological Department`
- event type: `PHYSICAL_RISK_OUTLOOK_RELEASE`
- record class: `OCCURRENCE`
- signal object class: `SCHEDULED_INFORMATION_CATALYST`
- certainty: `CONFIRMED`
- lifecycle: `COMPLETED`
- timing: `CIVIL_DATE`
- start_local: `2026-03-31`
- source timezone: `Asia/Kolkata`
- time precision: `DAY`
- all-day semantics: `true`
- UTC timestamps: null
- publication-time semantics: `DATE_ONLY`
- physical-shock routing: `NO_SHOCK_IN_THIS_RECORD`
- publication bundle: `SOURCE_BUNDLE`

The bundle may describe temperature, heatwave and April rainfall forecast components, but those are products of one publication occurrence and must not be multiplied into separate calendar events.

## Lifecycle finding

`COMPLETED` is supported by direct first-party post-event evidence: the dated IMD press release exists and is the publication itself.

Completion is **not** inferred because 31 March is in the past.

## Forecast / outcome boundary

The canonical event record may preserve what the release contained and the period it covered. It must not store:

- whether the heatwave forecast later verified;
- an observed heatwave outcome;
- an observed market reaction;
- a causal claim about agriculture, power demand or health outcomes.

Those belong to later Observation / Live Intelligence / Analysis work.

## Future-horizon finding

Do not create a 2027 occurrence.

Even if IMD has a recurring operational practice, historical or typical cadence is not an authoritative future schedule. A later 2027 first-party schedule/publication assertion may create or activate a future occurrence under a separate reviewed transaction.

## Population recommendation

Admit exactly one completed 2026 information-catalyst occurrence and one corresponding source/series.

Keep:

- Canonical schema unchanged;
- North Indian Ocean cyclone season deferred;
- Monitor unchanged;
- Analysis unchanged;
- automatic canonical commit prohibited;
- Google Calendar writes off.
