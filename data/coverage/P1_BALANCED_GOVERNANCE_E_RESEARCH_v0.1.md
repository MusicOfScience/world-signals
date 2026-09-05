# WORLD SIGNALS — Balanced P1 source-governance cohort E research v0.1

**Status:** FROZEN FOR REVIEW  
**Reference date:** 2026-09-05  
**Repository base:** `8a9938314e475faf8ac72559b6e2698ce0208fd0`  
**Canonical registry:** v0.25 / 669  
**Source registry:** v1.66 / 227  
**Change ledger:** v0.14  
**Scope:** seven unresolved P1 source records selected after the exact post-#37 66-P1 diagnostic. This document freezes research and transaction architecture only; it does not authorise production mutation.

## Selection logic

The post-#37 governance audit contains 66 P1 source records, 62 of which still have at least one forward/non-completed primary canonical dependency. All 66 are missing the same three modern governance fields:

- `canonical_provenance_use`
- `automated_monitoring_use`
- `verification_mode`

The remaining queue is still heavily concentrated in macroeconomic/monetary sources and US/European institutions. Cohort E therefore deliberately combines dependency leverage with geographic and domain diversity rather than taking the mechanical top seven.

Selected sources:

| Source | Jurisdiction / institutional scope | Primary canonical dependencies | Decision |
|---|---|---:|---|
| `WSSRC-MAC-023` | Australia / ABS | 6 | Governance completion only; canonical byte-identical. |
| `WSSRC-REG-008` | Brazil / Banco Central do Brasil | 3 | Governance completion only; canonical byte-identical. |
| `WSSRC-COM-006` | Australia / ABARES | 2 | Governance completion only; canonical byte-identical. |
| `WSSRC-CLIM-002` | Global / IPCC | 3 | Governance completion plus two lifecycle precision refinements to December 2027; Cities remains unchanged. |
| `WSSRC-INT-024` | Africa / African Union | 1 | Governance completion only; unscheduled 2027 Assembly remains TBC. |
| `WSSRC-INT-011` | Asia-Pacific / APEC China 2026 | 1 | Governance completion plus provenance decomposition: host-year page remains month-level evidence; exact 18–19 November dates move to China MFA source. |
| `WSSRC-INT-028` | Global South / New Development Bank | 1 | Governance completion plus semantic precision repair `DAY -> TBC`; India host remains confirmed and date/city remain unscheduled. |

This cohort does **not** claim to repair the remaining South Asia or physical-climate-risk canonical breadth deficits. Governance backfill and canonical population are separate layers.

## 1. ABS International Trade in Goods — `WSSRC-MAC-023`

Authoritative product page:  
https://www.abs.gov.au/statistics/economy/international-trade/international-trade-goods

Future release calendar:  
https://www.abs.gov.au/release-calendar/future-releases

Copyright / reuse:  
https://www.abs.gov.au/website-privacy-copyright-and-disclaimer

Findings:

- The current ABS product page explicitly lists forward releases through January 2027 reference-period data, including 1 October, 5 November and 3 December 2026 and 11 January, 4 February and 4 March 2027 publication dates.
- The six canonical primary dependencies remain consistent with the official release family; no date/time mutation is required in this transaction.
- ABS general website material is CC BY 4.0 subject to stated exceptions.
- Legacy metadata claims a pilot parser/runtime state, but repository inspection found **no source-specific parser, fixture, adapter or monitor route** for this source. Parser labels are not implementation evidence.

Frozen modern governance classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

No canonical ABS occurrence may change in this transaction.

## 2. Banco Central do Brasil Copom calendar — `WSSRC-REG-008`

Authoritative 2026 schedule:  
https://www.bcb.gov.br/detalhenoticia/20739/nota

BCB website terms:  
https://www.bcb.gov.br/en/about/privacystatement

Findings:

- BCB explicitly lists the remaining 2026 Copom meeting pairs as 15–16 September, 3–4 November and 8–9 December.
- All three canonical occurrences already match the first-order schedule and remain CONFIRMED multi-day local processes.
- BCB's website terms permit total or partial reproduction while preserving information integrity and citing the source.
- That content-reuse permission does not prove a production polling route, and repository inspection found no BCB-specific implementation despite the legacy parser-version label.

Frozen modern governance classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

No Copom canonical timing or identity field may change.

## 3. ABARES December 2026 releases — `WSSRC-COM-006`

Release schedule:  
https://www.agriculture.gov.au/abares/products/release-schedule

Australian Crop Report:  
https://www.agriculture.gov.au/abares/research-topics/agricultural-outlook/australian-crop-report

Department copyright notice:  
https://www.agriculture.gov.au/about/copyright

Findings:

- ABARES explicitly schedules the December 2026 Australian Crop Report for **8:00 am AEST Tuesday 1 December 2026**.
- ABARES schedules the December 2026 Agricultural Commodities Report for the same date/time.
- The two canonical records already use that exact local datetime and render-cluster relationship; no timing repair is required.
- Department website material is CC BY 4.0 unless otherwise stated, subject to Commonwealth branding and third-party exceptions.
- No ABARES-specific production adapter/fixture exists in WORLD SIGNALS.

Frozen modern governance classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## 4. IPCC AR7 products — `WSSRC-CLIM-002`

AR7 programme:  
https://www.ipcc.ch/assessment-report/ar7/

Current report catalogue:  
https://www.ipcc.ch/reports/

Short-lived Climate Forcers report page:  
https://www.ipcc.ch/report/methodology-report-on-short-lived-climate-forcers/

IPCC copyright regime:  
https://www.ipcc.ch/copyright/

Findings:

- The Special Report on Climate Change and Cities remains scheduled for **March 2027**. Its existing month-bounded canonical representation is correct and must remain byte-identical.
- The current IPCC report catalogue and working-group surfaces now label the **Methodology Report on Inventories for Short-lived Climate Forcers** as **December 2027**. This is more precise first-order current evidence than the older second-half-2027 formulation.
- The current IPCC catalogue likewise labels the **Methodology Report on Carbon Dioxide Removal Technologies, Carbon Capture, Utilization and Storage** as **December 2027**, narrowing the existing year-only window.
- Neither current source supplies an exact publication day. The correct lifecycle move is therefore to December month windows, not representative or inferred dates.
- IPCC website material remains restricted to personal/non-commercial use absent broader permission. Production automation stays rights-held.

Frozen lifecycle updates:

For `WSO-CLIM-A-0009`:

- `date_earliest = 2027-12-01`
- `date_latest = 2027-12-31`
- `time_precision = MONTH`
- preserve `timing_type = EXPECTED_DATE_WINDOW`
- preserve CONFIRMED certainty/time status
- preserve source identity and assertion IDs

For `WSO-CLIM-A-0010`:

- same December 2027 month bounds and `MONTH` precision
- preserve source identity and assertion IDs

`WSO-CLIM-A-0008` (Cities) must remain byte-identical.

Frozen modern governance classification:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 5. African Union 2027 Assembly — `WSSRC-INT-024`

Authoritative Assembly page:  
https://au.int/en/assembly

AU Legal Notice:  
https://au.int/en/legal_notice

Findings:

- The source supports the standing annual ordinary-session rule but does **not** establish a specific 2027 date or host.
- The canonical `WSO-INT-A-0015` correctly remains `UNSCHEDULED_TBC`, `time_precision=TBC`, hidden until scheduled, with `AUTHORITATIVE_RECURRING_RULE` activation.
- AU general website material is rights-restricted; written permission is required for ordinary content outside stated exceptions. News use has a separate credited-use condition.
- No AU source-specific production implementation exists despite a legacy parser-version label.

Frozen modern governance classification:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

No AU canonical mutation is authorised.

## 6. APEC Economic Leaders' Meeting 2026 — `WSSRC-INT-011` plus new `WSSRC-INT-031`

Existing APEC China host-year meetings page:  
https://www.apec2026.cn/node_196.html

Exact-date first-order source: Ministry of Foreign Affairs of the People's Republic of China, 12 December 2025 press conference:  
https://www.mfa.gov.cn/eng/xw/fyrbt/202512/t20251212_11771774.html

Findings:

- The APEC China host-year page supports **Shenzhen / November 2026** at month level.
- China MFA explicitly announced that the APEC Economic Leaders' Meeting would be held in Shenzhen on **18–19 November 2026**.
- Therefore the existing canonical dates are correct. The defect is provenance scope: `WSSRC-INT-011` no longer independently supports the stored day precision.
- Stable event identity is preserved by assigning the existing occurrence to a new event-specific China MFA source rather than changing the dates or forcing the host-year page to claim more precision than it supplies.
- The China MFA site carries copyright notice but no unrestricted reuse/automation licence was identified in this review; the source remains manual/rights-held.

Frozen source decomposition:

- retain `WSSRC-INT-011` as the APEC China 2026 host-year programme/month-level source;
- add `WSSRC-INT-031` for the China MFA exact-date announcement;
- reassign only `WSO-INT-A-0012` primary `source_id` to `WSSRC-INT-031`;
- preserve 18–19 November 2026, Shenzhen, CONFIRMED status, stable occurrence/series identity and all non-provenance semantics;
- because assertion identity hashes `source_id`, update primary and last-successful assertion IDs to `WSA-070677934abbc0f0`.

Frozen modern governance for both APEC sources:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 7. New Development Bank 2027 Annual Meeting — `WSSRC-INT-028`

Authoritative host confirmation:  
https://www.ndb.int/news/new-development-bank-11th-annual-meeting-in-moscow-charted-course-for-ndbs-growth-and-strategic-evolution/

Findings:

- NDB confirms India will host the Twelfth Annual Meeting in 2027.
- It does **not** state a date or city.
- The canonical occurrence correctly remains TBC, unscheduled and hidden until scheduled, with India as confirmed host jurisdiction.
- Its current `time_precision=DAY` is inconsistent with the record's complete lack of a date and with comparable host-confirmed/undated institutional records, which use `TBC` precision.
- This is a semantic hygiene repair only: `DAY -> TBC`. No date/window/city is added.
- NDB public material does not provide a clear general reuse/production-automation grant; bank publications commonly reserve rights. Verification therefore remains conservative and manual.

Frozen canonical update for `WSO-INT-B-0113`:

- `time_precision = TBC`
- preserve `timing_type = UNSCHEDULED_TBC`
- preserve null dates/times and null city
- preserve `host_confirmed=true`, `host_jurisdiction=India`
- preserve TBC certainty/time status and assertion IDs

Frozen modern governance classification:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## Implementation-evidence audit

A repository-wide read-only search of `src`, `scripts`, `tests`, `fixtures` and `data/monitor` found **no actual adapter/fixture/monitor implementation** for any of the seven selected source IDs or their legacy parser labels (`abs-release-calendar-0.1`, `regional-a-0.1`, `inst-a-0.1`, `inst-b-0.1`).

Consequently:

- machine readability is not treated as automation permission;
- parser-version strings are not treated as implementation evidence;
- no selected source is promoted to `AUTOMATED_PILOT` in cohort E.

## Frozen transaction architecture

If later reviewed and applied, cohort E is a four-production-file transaction:

1. `data/canonical/registry.json`
2. `data/sources/registry.json`
3. `data/changes/ledger.json`
4. `data/coverage/biosecurity_overlay.json`

No monitor configuration, parser, UI, Calendar output or expectations file may change.

Target versions, subject to simulation:

- canonical v0.25 -> **v0.26**, 669 occurrences unchanged;
- source registry v1.66 -> **v1.67**, 227 -> **228** sources;
- change ledger v0.14 -> **v0.15**;
- biosecurity overlay checkpoint v0.25 -> **v0.26**, 669 unchanged.

Expected governance post-state, subject to simulation:

- fully explicit: **98**;
- missing any: **130**;
- P1 canonical-dependent: **59**;
- P2 registry-only: **71**.

The ledger gains exactly four reviewed entries:

- APEC: `PROVENANCE_SCOPE_REPAIR`;
- IPCC SLCF: `LIFECYCLE_AND_CERTAINTY_UPDATE`;
- IPCC CDR/CCUS: `LIFECYCLE_AND_CERTAINTY_UPDATE`;
- NDB: `CANONICAL_SEMANTIC_CLASSIFICATION_REPAIR`.

`committed_at` is created only at reviewed apply time.

## Protected invariants

The guarded helper/tests must prove:

- canonical occurrence count remains 669 and occurrence identity/order is unchanged;
- exactly four canonical occurrences change;
- every selected ABS, BCB, ABARES and AU occurrence remains byte-identical;
- IPCC Cities remains byte-identical;
- the two IPCC methodology reports become December 2027 month windows only, with no synthetic day;
- APEC remains exactly 18–19 November 2026 in Shenzhen and CONFIRMED; only provenance/assertion identity plus explanatory metadata may change;
- NDB remains completely undated, city-TBC and host-country-confirmed; only precision/explanatory metadata may change;
- Brazil presidential inauguration remains `2027-01-05`;
- Colombia manual/machine source split remains intact;
- automatic canonical commit remains `false`;
- Google Calendar write remains `false`;
- no live monitor route is added;
- no selected source is labelled `AUTOMATED_PILOT` without implementation evidence.

## Research boundary

This document freezes evidence and architecture only. Production mutation requires a fresh branch from the exact merged preparation baseline, an explicit write gate, exact-diff enforcement and an independent committed-state audit. Google Calendar remains an output layer and receives no write authority from this work.
