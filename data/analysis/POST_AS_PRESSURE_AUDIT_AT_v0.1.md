# WORLD SIGNALS — post-AS pressure audit AT v0.1

**Reference date:** 2026-09-06
**Exact post-#74 main:** `92bf6cba7506483dd861680924879b1ded0f4ddc`

## Frozen checkpoint

- Canonical Registry: `v0.37 / 687`
- Canonical schema: `v0.52`
- Source Registry: `v1.79 / 242`
- Change Ledger: `v0.24 / 59`
- monitor expectations: `v0.10 / 8 adapters`
- Analysis schema: `v0.4`
- Analysis reviews: `v0.15 / 19`
- Analysis evidence: `v0.15 / 85`
- reviewed event-type diversity: `17`
- production `EXACT_TIMESTAMP_SERIES`: `0`

## Decision

**Select one South Asian physical-risk information-catalyst sample: IMD's dated 31 March 2026 updated hot-weather/heatwave outlook. Do not resolve the North Indian Ocean cyclone-season boundary by assumption. Do not add another monitor route immediately after AS. Do not consume the Japan household-spending Analysis frontier merely to reach twenty reviews.**

This is a bounded coverage correction, not quota filling.

## Why this pressure outranks the alternatives

AR's reviewed coverage baseline identifies two independent weaknesses:

- South Asia: `28 occurrences / 8 series / 6 institutions / 6 sources / 3 categories` — the only region below both current series- and institution-diversity review prompts;
- `PHYSICAL_CLIMATE_RISK`: `6 occurrences / 3 series / 3 institutions / 3 sources` — the only category below the current five-series review prompt.

Those prompts are non-authoritative. Their value here is that one candidate can improve **both** weaknesses while adding a genuinely different information contract: an authoritative hazard outlook release rather than another macro release, central-bank meeting or cyclone exposure window.

The proposed sample does not clear either threshold by itself. Post-sample South Asia would still be only 9 series / 7 institutions, and physical risk only 4 series / 4 institutions. That is desirable evidence that this is not a threshold-clearing exercise.

## Candidate comparison

### A. North Indian Ocean tropical-cyclone season — HOLD

Architecture is no longer the blocker. Canonical v0.52 already supports `MULTI_PHASE_SEASON_WINDOW` with source-native month precision.

The evidence blocker remains unresolved:

- an official IMD pre-cyclone exercise document describes two cyclone seasons as **April–June and October–December**;
- the accessible WMO/ESCAP TCP-21 2021 operational plan defines storm season as **April–May and October–December**;
- WMO and RSMC New Delhi now list TCP-21 **Edition 2025** as the current operational plan, but the exact current glossary/boundary text was not recoverable in this review.

WORLD SIGNALS must not choose April–May or April–June because one is more convenient. The candidate remains `OFFICIAL_SOURCE_DEFINITION_CONFLICT` until a current competent source resolves the boundary or explicitly supports a deliberately less precise representation.

### B. IMD 31 March 2026 hot-weather / heatwave outlook — SELECT

The official dated press release:

- is first-party IMD / Ministry of Earth Sciences evidence;
- is explicitly dated **31 March 2026**;
- publishes an updated April–June 2026 hot-weather seasonal outlook and April 2026 monthly outlook;
- contains a dedicated **heatwave outlook for April–June 2026**;
- identifies possible transmission through public health, water resources, power demand, essential services, infrastructure/resource management and agriculture;
- is a discrete information publication rather than the hazard itself.

The existing canonical ontology already separates `SCHEDULED_INFORMATION_CATALYST` from `PHYSICAL_RISK_WINDOW` and `UNSCHEDULED_PHYSICAL_SHOCK`. The earlier physical-risk ontology audit explicitly anticipated a separate event type such as `PHYSICAL_RISK_OUTLOOK_RELEASE`.

Therefore no schema migration is justified solely to admit this specimen.

### C. Another monitor route — DEFER

AS has just expanded the Source/Change Monitor from 7 to 8 adapters and introduced a new energy/commodities schedule-sentinel contract. Adding another route now would need to demonstrate greater marginal operational novelty than the current coverage correction. None identified in this audit does so.

### D. Japan household-spending Analysis review — DEFER

`WSO-MAC-B-0041` remains the sole completed/unreviewed canonical occurrence. It is valid future Analysis material, but the sample already has repeated macro/data-release semantics. Review number twenty is not a backlog obligation.

### E. Market-structure historical anchor — DEFER

The category has enough canonical series to avoid the raw-depth prompt. Its missing completed Analysis anchor remains an analytical-design opportunity, not a reason to create history for histogram tidiness.

### F. Health/biosecurity institutional deconcentration — IMPORTANT, NOT SELECTED

WHO concentration remains a real structural issue. It does not currently combine regional, hazard-family and information-contract diversification as efficiently as the selected IMD object. It remains a priority for a later pressure audit.

## Object boundary

The selected occurrence is the **publication event**, not an April–June heatwave season.

Proposed semantics:

- category: `PHYSICAL_CLIMATE_RISK`
- event type: `PHYSICAL_RISK_OUTLOOK_RELEASE`
- signal object class: `SCHEDULED_INFORMATION_CATALYST`
- timing type: `CIVIL_DATE`
- source date: `2026-03-31`
- source timezone: `Asia/Kolkata`
- precision: `DAY`
- all-day semantics: true
- UTC timestamps: null
- lifecycle: `COMPLETED`, established from the dated first-party release itself, not elapsed time
- publication time semantics: `DATE_ONLY`

The April–June period belongs in the outlook's reference/forecast scope. It must not become the occurrence's date range.

## Source-governance boundary

Public availability is not automation permission.

The IMD press-release surface carries institutional copyright notices and no reviewed production-automation grant has been established. The new source should therefore be admitted conservatively as manually curated authoritative factual provenance with automated monitoring held.

RSMC New Delhi's explicit copyright policy is useful contextual evidence of restrictive institutional web reuse, but its terms must **not** be imputed automatically to the separate `mausam.imd.gov.in` surface. The new source classification rests on the absence of a demonstrated automation licence for the actual IMD route, not on hostname inheritance.

## Population horizon

Admit exactly one observed 2026 release.

Do not generate:

- a 2027 occurrence from historical cadence;
- a recurring March-31 rule;
- a March–June or April–June hazard window;
- an Analysis review;
- a live monitor route;
- an exact publication timestamp.

IMD's FAQ says seasonal maximum-temperature/heatwave forecasts are normally issued around the beginning of March and then updated through other forecast systems. That is cadence context, not an authoritative 2027 schedule.

## Expected descriptive coverage movement

If the one-occurrence sample validates:

- Canonical: `687 → 688`
- unique series: `201 → 202`
- unique institutions: `126 → 127`
- unique canonical source IDs: `159 → 160`
- South Asia: `28 → 29 occurrences`, `8 → 9 series`, `6 → 7 institutions`, `6 → 7 sources`, `3 → 4 categories`
- `PHYSICAL_CLIMATE_RISK`: `6 → 7 occurrences`, `3 → 4 series`, `3 → 4 institutions`, `3 → 4 sources`
- monetary + macro occurrence count remains `443`; share falls mechanically from `64.48%` to about `64.39%`

These are audit consequences, not success criteria.

## Mutation boundary

AT may mutate only:

- `data/canonical/registry.json`
- `data/sources/registry.json`
- its own transaction-audit artifact

Permanent research/plan/test/apply support files are separately declared branch changes.

AT must not mutate:

- canonical schema;
- Change Ledger;
- monitor expectations or operations policy;
- Analysis schema/reviews/evidence;
- biosecurity overlay;
- Calendar / Google Calendar.

Automatic canonical commit remains prohibited. The transaction is a reviewed one-shot branch write only.

## Next gate

Research → plan → exact-prestate read-only simulation → canonical/source validation → coverage recomputation → targeted regressions → full repository regressions → controlled reviewed transaction → exact mutation audit → ordinary PR CI → manual merge.
