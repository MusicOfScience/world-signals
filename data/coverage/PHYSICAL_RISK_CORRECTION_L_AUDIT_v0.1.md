# WORLD SIGNALS — Physical Risk Correction L Audit v0.1

**Reference date:** 2026-09-04  
**Status:** COMPLETE — REVIEWED CANONICAL TRANSACTION APPLIED AND INDEPENDENT CI/PAGES CHECKS PASSED  
**Canonical checkpoint:** v0.20 / 669 occurrences  
**Source registry checkpoint:** v1.51 / 222 sources  
**Schema:** v0.51

## Purpose

Correction L is the first population test of the source-native month-bounded physical-risk ontology introduced in schema v0.50 and tightened in v0.51. Its purpose is not to maximise cyclone-season records. It tests whether a useful Pacific structural risk window can enter canonical state without inventing civil-day precision, conflating a season with an actual cyclone, or weakening source-rights discipline.

## Canonical result

Correction L admitted exactly one new occurrence and one new source:

- `WSO-RISK-A-0001` — South-West Pacific tropical cyclone season 2026–27;
- `WSER-RISK-SWP-TC` — new recurring risk series;
- `WSSRC-RISK-004` — Fiji Meteorological and Hydrological Services / RSMC Nadi Tropical Cyclone Centre.

One candidate remains deliberately noncanonical:

- `WSFR-RISK-NIO-TC` — North Indian Ocean tropical cyclone season / IMD-RSMC New Delhi — `OFFICIAL_SOURCE_DEFINITION_CONFLICT`.

No 2027–28 Fiji occurrence was added merely to mirror existing two-year NOAA/BoM examples. One current relevant cycle was sufficient to prove the ontology.

## Fiji / RSMC Nadi — admission rationale

Official Fiji Meteorological Service / RSMC Nadi material describes the regional tropical-cyclone season as **November–April** and states that cyclones can occur outside that period.

Primary authoritative reference:

- https://www.met.gov.fj/climate-services/2025-26-tc-outlook/

Supporting official reference:

- https://www.met.gov.fj/tropical-cyclone/tropical-cyclone-reports/

The canonical object is therefore a **structural exposure window**, not a forecast that a cyclone will occur.

Canonical timing preserves source precision:

- `timing_type = MONTH_BOUNDED_SEASON_WINDOW`
- `season_window_model = MONTH_BOUNDED_SINGLE_PHASE`
- `source_native_window_label = November–April`
- phase: `2026-11` → `2027-04`
- `time_precision = MONTH`
- `publication_time_semantics = SEASONAL_MONTH_RANGE`
- no `start_local`, `end_local`, UTC timestamp, `date_earliest`, `date_latest`, or synthetic first/last civil day.

No 2026–27 forecast cyclone count or probability was imported. A later seasonal outlook is a separate factual product and must not retrospectively turn the structural season definition into a forecast object.

Actual cyclones continue to route to the Shock / Live Intelligence layer through `ROUTE_ACTUAL_EVENT_TO_SHOCK_REGISTER`.

## IMD / RSMC New Delhi — deferred source conflict

Canonical population was rejected because competent official material does not provide one unambiguous first-phase boundary.

Official assertion A:

- IMD pre-cyclone exercise material: **April–June and October–December**
- https://rsmcnewdelhi.imd.gov.in/uploads/home/conference/pce.pdf

Official assertion B:

- WMO/ESCAP Tropical Cyclone Operational Plan hosted by RSMC New Delhi: **April–May and October–December**
- https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F28%2F28_06dbff_TCP-21_Edition+2021.pdf

WORLD SIGNALS does not resolve this by majority vote, convenience, or by choosing the wording that best fits the ontology. The candidate remains `OFFICIAL_SOURCE_DEFINITION_CONFLICT` until a competent current operational source resolves the difference or demonstrates that a deliberately coarser representation is more faithful.

Its provisional WORLD SIGNALS region remains **Cross-regional / Global**, not South Asia.

## Source governance

The Fiji source is retained under the modern split between factual provenance fitness and automated-monitor permission:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`
- `monitoring_readiness_status = RIGHTS_OR_LICENSE_HOLD`

The reviewed Fiji website surface states **All Rights Reserved**. Curated factual metadata can support manual authoritative reference; no production crawler permission is inferred.

IMD also remains manual/reference-only with automated monitoring on a rights hold.

## Identity decision

Legacy physical-risk occurrences retain immutable `WSO-COM-A-0049` through `0052` identities even though their series IDs are `WSER-RISK-*`.

New physical-risk occurrences begin the dedicated `WSO-RISK-*` namespace with `WSO-RISK-A-0001`. `WSSRC-RISK-003` was already occupied by the Tropical Storm Edouard advisory archive, so Fiji correctly entered as `WSSRC-RISK-004`.

## Executable preflight

The check-only executable `scripts/check_physical_risk_correction_l.py` constructed proposed v0.20 / 669 and source v1.51 / 222 clones entirely in memory. It had no write path.

Preflight passed:

1. exact checkpoint/schema/identity preconditions;
2. Fiji month-native timing invariants;
3. rejection of synthetic day/time fields;
4. source-rights invariants;
5. preservation of both conflicting IMD assertions;
6. proof no IMD occurrence/source leaked into canonical state;
7. full registry validation;
8. Correction-L regression tests;
9. temporal-window regression tests;
10. `git diff --exit-code` proof of zero mutation.

The temporary preflight workflow was removed after success.

## Reviewed canonical transaction

A one-shot write-capable GitHub workflow was then opened for the reviewed transaction. It was bounded to:

- `data/canonical/registry.json`: v0.19 / 668 → **v0.20 / 669**;
- `data/sources/registry.json`: v1.50 / 221 → **v1.51 / 222**;
- `tests/test_registry.py`: checkpoint lock 0.19/668 → **0.20/669**.

Before commit it passed:

- the check-only preflight again;
- exact Correction L postconditions;
- full registry validation and Python test suite;
- JavaScript syntax checks;
- static Pages build at 669 records;
- proof that the Fiji projection exposes `November–April` without a synthetic day;
- protected hashes for schema, monitor expectations, monitor operations policy, change ledger, plan and audit;
- exact changed-file whitelist.

Reviewed migration commit: `d398ff464a77c0178743951f255482aa75068010`.

The one-shot write workflow was immediately deleted in commit `ba1e716a5dc5e9422f305411f514e5eb5fb58cd8`.

Because a GitHub Actions token push does not recursively trigger ordinary push workflows, the workflow-deletion commit — immediately on top of the same v0.20 canonical state — supplied the independent post-commit check. Normal WORLD SIGNALS CI passed and the Pages build/deployment also passed.

## Safety result

- Automatic canonical commit: **OFF**.
- Google Calendar writes: **OFF**.
- No scheduled monitor route was added for Fiji.
- No IMD canonical population occurred.
- No second Fiji year was invented.
- No write-capable migration workflow remains in the repository.

## Interpretation

Correction L's strongest result is not the addition of one record. It is that the executable system admitted one justified object while rejecting or deferring superficially tidy alternatives. The registry can now preserve a source's real month-level temporal precision rather than rewarding sources that happen to publish exact civil-day boundaries.
