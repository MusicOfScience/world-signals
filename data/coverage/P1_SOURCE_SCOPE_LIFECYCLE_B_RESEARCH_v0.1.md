# WORLD SIGNALS — P1 source-scope and lifecycle B research v0.1

**Status:** FROZEN FOR REVIEW  
**Reference date:** 2026-09-05  
**Repository base:** `2982a734e6d742f79c50f419bde4acf5ed0a3f41` (tree identical to signed PR #31 merge)  
**Canonical registry:** v0.22 / 669  
**Source registry:** v1.63 / 225  
**Change ledger:** v0.11  
**Scope:** six P1 source records selected by Forward Triage A. This document freezes research and transaction architecture only; it does not authorise production mutation by itself.

## Why this is not a routine six-row backfill

Forward Triage A established that all 87 remaining P1 source rows are forward-active and all 87 share the same three missing modern governance fields. That apparent uniformity is deceptive. The six-source international test cohort exposed three distinct problems:

1. straightforward source-governance completion;
2. canonical provenance / legal-authority semantics that need clarification without changing the event date; and
3. normal event-lifecycle advancement from unscheduled TBC to an authoritative month-level expected window.

The architecture therefore keeps source governance, canonical provenance and lifecycle timing separate rather than treating the queue as clerical metadata completion.

Selected sources:

| Source | Jurisdiction | Canonical dependencies | Decision |
|---|---|---:|---|
| `WSSRC-MAC-021` | Australia | 6 | Governance completion only; canonical byte-identical. |
| `WSSRC-REG2-005` | Argentina | 1 | Preserve 15 Sep 2026; clarify legal-basis semantics and governance. |
| `WSSRC-REG-005` | Indonesia | 1 | Preserve 31 Oct 2026; clarify legal-basis semantics and governance. |
| `WSSRC-EL-ZA-001` | South Africa | 1 | Governance completion only; canonical byte-identical. |
| `WSSRC-INT-021` | ASEAN / Singapore | 2 | Upgrade two stable summit occurrences from unscheduled TBC to month-level forecast windows; governance completion. |
| `WSSRC-FIS-023` | India | 1 | Keep 2027–28 presentation date unscheduled; separate constitutional legal authority from Budget publication monitor; governance completion. |

## 1. ABS Monthly Household Spending Indicator — `WSSRC-MAC-021`

Authoritative product page:  
https://www.abs.gov.au/statistics/economy/finance/monthly-household-spending-indicator

Future release calendar:  
https://www.abs.gov.au/release-calendar/future-releases

Copyright / Creative Commons notice:  
https://www.abs.gov.au/website-privacy-copyright-and-disclaimer

Findings:

- ABS currently publishes rolling future publication dates for the Monthly Household Spending Indicator.
- The source already has six canonical dependencies and a research-validated pilot parser, but automated production access remains an endpoint question distinct from copyright.
- ABS states that website material is generally licensed CC BY 4.0, subject to stated exceptions including logos, trademarks, microdata and third-party material.
- No unrestricted production polling permission is inferred from CC BY 4.0 or parser success.

Frozen modern governance classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = AUTOMATED_PILOT`

No canonical occurrence mutation is authorised for ABS in this transaction.

## 2. Argentina Budget 2027 — `WSSRC-REG2-005` / `WSO-REG-B-0007`

Annual 2026 formulation resolution:  
https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-446-2026-424520/texto

Argentina.gob terms:  
https://www.argentina.gob.ar/terminos-y-condiciones

Official budget-process explainer used as corroboration:  
https://www.argentina.gob.ar/onp/presupuesto-ciudadano/proceso-presupuestario

Findings:

- Law 24.156 Article 26 and Resolution 446/2026 use wording equivalent to presentation **before 15 September**.
- Argentina's own budget-process material operationally describes formulation as culminating on 15 September when the bill is sent to Congress, and official parliamentary practice has treated 15 September as the latest presentation boundary.
- The existing `2026-09-15` canonical date is therefore retained. It is a civil-date legal/operational boundary, not a prediction of the filing time.
- The current record should make the literal statutory wording and official operational interpretation explicit rather than silently conflating them.
- Argentina.gob states that its content is licensed under CC BY 4.0 unless otherwise indicated; automated retrieval remains separately unreviewed.

Frozen canonical decision:

- preserve stable occurrence ID, `2026-09-15`, CONFIRMED status, record class and assertion IDs;
- add `legal_basis_source_id = WSSRC-REG2-005`;
- add `governing_instrument = Law 24.156 Article 26 / Resolution 446/2026 budget formulation process`;
- clarify notes; no timing mutation.

Frozen modern governance classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## 3. Indonesia APBN 2027 — `WSSRC-REG-005` / `WSO-REG-A-0008`

Authoritative Ministry of Finance / Directorate General of Treasury budget-cycle guidance:  
https://djpb.kemenkeu.go.id/portal/id/layanan/kantor-pusat/sistem-manajemen-investasi/157-layanan/siklus-apbn.html

Findings:

- Law No. 17 of 2003 Article 15(4) requires the DPR decision on the APBN bill no later than two months before the budget year begins.
- Current official Treasury budget-cycle guidance operationalises the legislative period through August–October and identifies APBN enactment at **end October**.
- This directly supports the existing `2026-10-31` civil-date legal-latest boundary without inventing a day by subtracting two calendar months.
- Government Regulation No. 90/2010 must **not** be used as current authority: it was revoked by Government Regulation No. 6/2023.
- The current Treasury page contains legacy examples/references and should be treated as an authoritative process explainer with explicit limitations, not as a current parliamentary vote calendar.
- Source-specific reuse and automation terms remain unresolved.

Frozen canonical decision:

- preserve stable occurrence ID, `2026-10-31`, CONFIRMED status, record class and assertion IDs;
- add `legal_basis_source_id = WSSRC-REG-005`;
- add `governing_instrument = Law No. 17 of 2003 Article 15(4); current Ministry of Finance APBN-cycle operationalisation`;
- clarify notes and exclude revoked PP 90/2010; no timing mutation.

Frozen modern governance classification:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 4. South Africa 2026 Local Government Elections — `WSSRC-EL-ZA-001`

Authoritative COGTA proclamation notice:  
https://www.cogta.gov.za/index.php/2026/08/07/minister-hlabisa-gazzetes-the-date-for-the-2026-local-government-elections/

General South African Government web terms used as a conservative reuse benchmark:  
https://www.gov.za/terms-and-conditions-use-0

Findings:

- COGTA's official notice records the formally gazetted 4 November 2026 election date.
- The canonical occurrence is already correctly CONFIRMED and requires no date/provenance mutation.
- General South African Government web terms permit copying/distribution for non-commercial informational/reference purposes and require permission for commercial use.
- No production crawler permission is inferred for the COGTA endpoint.

Frozen modern governance classification:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

No canonical occurrence mutation is authorised for South Africa in this transaction.

## 5. ASEAN Chair 2027 — `WSSRC-INT-021` / `WSO-INT-A-0018` / `WSO-INT-A-0019`

Current Singapore MFA host-government forecast:  
https://www.mfa.gov.sg/newsroom/announcements-and-highlights/invitation-for-proposals-for-sponsorship-of-food-and-drinks--furniture--audio-visual-equipment--event-tokens-and-medical-services-for-high-level-meetings-and-conferences-in-2027/

MFA Terms of Use:  
https://www.mfa.gov.sg/terms-of-use/

Findings:

- The current MFA notice describes the meeting timetable explicitly as a **forecast**.
- It identifies the 50th ASEAN Summit in **May 2027** with an estimated duration of five days and the 51st ASEAN Summit and Related Summits in **November 2027** with an estimated duration of six days.
- The estimated durations do not establish exact start/end dates. Older logistics/procurement windows must not be treated as summit dates.
- The two existing stable occurrences are therefore advanced from unscheduled TBC to authoritative **month-level expected windows**, not to provisional exact dates.
- Existing canonical precedent represents month-only institutional timing as `EXPECTED_DATE_WINDOW` with `MONTH` precision, null `start_local`/`end_local`, first/last-day month bounds, and a non-exact time status.
- MFA terms reserve website intellectual property and prohibit commercial reuse without prior written permission apart from statutory fair dealing; no production crawler grant was identified.

Frozen lifecycle update:

For `WSO-INT-A-0018`:

- `certainty_status = PROVISIONAL`
- `timing_type = EXPECTED_DATE_WINDOW`
- `time_precision = MONTH`
- `time_status = PROVISIONAL`
- `time_basis = EXPLICIT_AUTHORITATIVE_MONTH`
- `date_earliest = 2027-05-01`
- `date_latest = 2027-05-31`
- preserve null `start_local`, `end_local`, UTC fields and existing assertion IDs.

For `WSO-INT-A-0019`:

- same semantics with `date_earliest = 2027-11-01` and `date_latest = 2027-11-30`.

Both remain `PLANNED`, retain `EXPLICITLY_SCHEDULED` activation, gain a 2026-09-05 status-history entry, and remain visibly marked as forecast/provisional rather than exact dates.

Frozen modern governance classification:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 6. India Union Budget 2027–28 — `WSSRC-FIS-023` / `WSO-FIS-B-0011`

Budget publication portal:  
https://www.indiabudget.gov.in/

Budget Website Policies:  
https://www.indiabudget.gov.in/website-policies.php

Budget Terms of Use:  
https://www.indiabudget.gov.in/termsofuse.php

Official Constitution source family:  
https://legislative.gov.in/constitution-of-india/

Official Constitution PDF reference:  
https://www.legislative.gov.in/static/uploads/2025/07/359f70a69695affb9d72f8393102bd2e.pdf

Findings:

- Article 112 of the Constitution requires the President to cause an Annual Financial Statement to be laid before both Houses for every financial year.
- Article 112 establishes recurring constitutional existence but **does not establish a 2027 presentation date**.
- The Budget portal remains the correct publication/announcement monitor for the eventual 2027–28 schedule, but its own Terms say website content should not be construed as a statement of law.
- The Budget portal currently publishes the 2026–27 cycle; no 1 February 2027 date may be inferred from convention.
- Current website policy states that Budget-site content may not be reproduced partially or fully without Ministry permission and requires source acknowledgement when referred to elsewhere.
- Stable source identity therefore requires a separate legal-authority source rather than repurposing the Budget portal as constitutional authority.

Frozen canonical decision:

- preserve stable occurrence ID, TBC certainty, unscheduled timing, null date/window, hidden-until-scheduled render policy, and assertion IDs;
- correct `activation_mode` from `EXPLICITLY_SCHEDULED` to `AUTHORITATIVE_RECURRING_RULE`;
- add `legal_basis_source_id = WSSRC-FIS-025`;
- add `governing_instrument = Constitution of India, Article 112`;
- keep `source_id = WSSRC-FIS-023` for future publication/schedule evidence.

New source identity:

- `WSSRC-FIS-025` — Legislative Department, Ministry of Law and Justice, Government of India; official constitutional text, Article 112.
- It is a legal-authority source, not a new production monitor route.
- No unrestricted content-reuse or automated retrieval right is inferred for the Legislative Department endpoint; minimal factual legal metadata remains manual.

Frozen modern governance for both India sources:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## Frozen transaction architecture

If later approved and applied, Source-Scope/Lifecycle B is a **four-production-file transaction**:

1. `data/canonical/registry.json`
2. `data/sources/registry.json`
3. `data/changes/ledger.json`
4. `data/coverage/biosecurity_overlay.json`

No monitor configuration, parser, web UI, Calendar output or expectations file may change.

Target versions, subject to simulation:

- canonical v0.22 → **v0.23**, 669 records unchanged;
- source registry v1.63 → **v1.64**, 225 → **226** sources;
- change ledger v0.11 → **v0.12**;
- biosecurity overlay checkpoint v0.22 → **v0.23**, 669 unchanged.

The ledger gains exactly five reviewed entries: three provenance-scope repairs (Argentina, Indonesia, India) and two lifecycle/certainty updates (ASEAN). `committed_at` must be created only at reviewed apply time.

## Protected invariants

The guarded helper/tests must prove:

- canonical occurrence count stays 669 and stable occurrence ordering/identity is unchanged;
- Argentina remains exactly `2026-09-15` CONFIRMED;
- Indonesia remains exactly `2026-10-31` CONFIRMED;
- South Africa remains exactly `2026-11-04` CONFIRMED and byte-identical canonically;
- ABS canonical occurrences remain byte-identical;
- ASEAN gets month windows only, never invented representative days or duration-derived start/end dates;
- India remains unscheduled TBC with no inferred 1 February date;
- all existing primary/last-successful assertion IDs remain unchanged because no assertion-hash identity field changes;
- Brazil presidential inauguration remains `2027-01-05`;
- Colombia source split remains intact;
- automatic canonical commit remains `false`;
- Google Calendar write remains `false`;
- no production monitoring route is activated.

## Research boundary

This research freezes architecture and evidence. It does **not** authorise an apply transaction. Production mutation must occur only on a fresh branch from the exact merged preparation baseline, behind an explicit write gate, with exact-diff enforcement and independent post-transaction audit.
