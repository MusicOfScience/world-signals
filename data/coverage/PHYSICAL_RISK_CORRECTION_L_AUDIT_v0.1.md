# WORLD SIGNALS — Physical Risk Correction L Audit v0.1

**Reference date:** 2026-09-04  
**Status:** REVIEWED PREFLIGHT PASS — CANONICAL TRANSACTION NOT YET APPLIED  
**Canonical checkpoint tested:** v0.19 / 668 occurrences  
**Source registry checkpoint tested:** v1.50 / 221 sources  
**Schema:** v0.51

## Purpose

Correction L is the first population test of the source-native month-bounded physical-risk ontology introduced in schema v0.50 and tightened in v0.51. Its purpose is not to maximise the number of cyclone-season records. It tests whether a genuinely useful Pacific structural risk window can enter canonical state without inventing civil-day precision, conflating a season with an actual cyclone, or weakening source-rights discipline.

## Result

The reviewed sample is deliberately narrow:

- **one proposed canonical occurrence:** `WSO-RISK-A-0001` — South-West Pacific tropical cyclone season 2026–27;
- **one proposed new series:** `WSER-RISK-SWP-TC`;
- **one proposed new source:** `WSSRC-RISK-004` — Fiji Meteorological and Hydrological Services / RSMC Nadi Tropical Cyclone Centre;
- **one deferred noncanonical candidate:** `WSFR-RISK-NIO-TC` — North Indian Ocean tropical cyclone season / IMD-RSMC New Delhi.

No 2027–28 Fiji occurrence is added merely to mirror the existing two-year NOAA/BoM examples. The current relevant recurring cycle is sufficient to test the repaired ontology.

## Fiji / RSMC Nadi — admission rationale

Current official Fiji Meteorological Service / RSMC Nadi material describes the regional tropical-cyclone season as **November–April** and also states that cyclones can occur outside that period.

Primary authoritative reference:

- https://www.met.gov.fj/climate-services/2025-26-tc-outlook/

Supporting official reference:

- https://www.met.gov.fj/tropical-cyclone/tropical-cyclone-reports/

The canonical object is therefore a **structural exposure window**, not a forecast that any cyclone will occur.

The proposed timing is preserved at the source's relevant precision:

- `timing_type = MONTH_BOUNDED_SEASON_WINDOW`
- `season_window_model = MONTH_BOUNDED_SINGLE_PHASE`
- `source_native_window_label = November–April`
- phase: `2026-11` → `2027-04`
- `time_precision = MONTH`
- `publication_time_semantics = SEASONAL_MONTH_RANGE`
- no `start_local`, `end_local`, UTC timestamp, `date_earliest`, `date_latest`, or synthetic first/last civil day.

The 2026–27 annual activity outlook was not located in the current official search surface during this review. No forecast cyclone count, probability, or expected activity level is therefore imported into the occurrence. A later seasonal outlook is a separate factual product and must not retrospectively turn the structural season definition into a forecast object.

Actual cyclones continue to route to the Shock / Live Intelligence layer through `ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER`.

## IMD / RSMC New Delhi — deferred source conflict

Canonical population was **rejected for now** because competent official material does not provide one unambiguous first-phase boundary.

Official assertion A:

- IMD pre-cyclone exercise material: **April–June and October–December**
- https://rsmcnewdelhi.imd.gov.in/uploads/home/conference/pce.pdf

Official assertion B:

- WMO/ESCAP Tropical Cyclone Operational Plan hosted by RSMC New Delhi: **April–May and October–December**
- https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F28%2F28_06dbff_TCP-21_Edition+2021.pdf

WORLD SIGNALS does not resolve this by majority vote, convenience, or by choosing the wording that best fits the new ontology. The candidate remains `OFFICIAL_SOURCE_DEFINITION_CONFLICT` until a competent current operational source resolves the difference or demonstrates that a deliberately coarser canonical representation is more faithful.

The provisional region is **Cross-regional / Global**, not South Asia. The RSMC New Delhi area of responsibility spans the North Indian Ocean and serves countries across more than one WORLD SIGNALS analytical region; forcing the object into South Asia would trade source truth for neat geography.

## Source governance

Fiji and IMD source-governance fitness was assessed separately from factual authority.

For the proposed Fiji source:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`
- `monitoring_readiness_status = RIGHTS_OR_LICENSE_HOLD`

The Fiji Met website surface reviewed states **All Rights Reserved**. Curated factual metadata can support manual authoritative reference, but no production crawler or automated-monitor permission is inferred.

For IMD, the official copyright policy requires permission for reproduction and does not clear the intended production monitoring route. The deferred candidate therefore also remains manual/reference-only with automated monitoring on a rights hold.

Source authority, canonical provenance use and automated monitoring permission remain separate gates.

## Identity decision

The four legacy physical-risk occurrences use `WSO-COM-A-0049` through `0052` even though their series IDs are `WSER-RISK-*`. Those occurrence IDs are immutable historical identities and will not be renamed.

No `WSO-RISK-*` occurrence currently exists. New physical-risk occurrences therefore begin a dedicated namespace with `WSO-RISK-A-0001`. This avoids perpetuating a commodity-era namespace collision while preserving every existing stable identity.

`WSSRC-RISK-003` is already occupied by the Tropical Storm Edouard advisory archive. The next safe source identity is consequently `WSSRC-RISK-004`, not `003`.

## Executable preflight

The check-only executable `scripts/check_physical_risk_correction_l.py` constructs the proposed post-transaction registry and source registry entirely in memory. It has no write path.

The GitHub Actions preflight passed all of the following:

1. exact checkpoint, schema and identity preconditions;
2. construction of canonical clone v0.20 / 669;
3. construction of source clone v1.51 / 222;
4. Fiji month-native timing invariants;
5. rejection of all synthetic day/time fields;
6. Fiji source-rights invariants;
7. explicit retention of the two conflicting IMD official assertions;
8. proof that no IMD occurrence/source leaked into canonical state;
9. full `validate_registry` validation;
10. Correction-L-specific regression tests;
11. temporal-window regression tests;
12. validation of the untouched live 668-record checkpoint;
13. `git diff --exit-code` proof that preflight produced zero repository mutation.

The ordinary WORLD SIGNALS CI suite also passed on the same executable-preflight commit, including Python tests, JavaScript syntax validation and static-site build.

## Proposed reviewed transaction

If the transaction gate is opened, it is bounded to exactly two source-of-truth files:

- `data/canonical/registry.json`: v0.19 / 668 → v0.20 / 669
- `data/sources/registry.json`: v1.50 / 221 → v1.51 / 222

Expected additions:

- one occurrence: `WSO-RISK-A-0001`
- one source: `WSSRC-RISK-004`

No schema change.  
No monitor-route change.  
No automatic canonical commit.  
No Google Calendar write.  
No IMD canonical population.  
No invented second Fiji year.

## Interpretation

Correction L's most important result is not that one event can be added. It is that three superficially convenient additions were rejected or deferred for defensible reasons. The ontology now allows the registry to preserve the authority's actual temporal precision instead of rewarding sources that happen to publish exact civil-day boundaries.
