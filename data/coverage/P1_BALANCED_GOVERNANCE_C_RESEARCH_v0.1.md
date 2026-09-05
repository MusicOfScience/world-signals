# WORLD SIGNALS — P1 balanced governance C research v0.1

**Status:** FROZEN FOR REVIEW  
**Reference date:** 2026-09-05  
**Repository base:** `336d7752afe4d6975e3b8399801e55c3e9680327`  
**Canonical registry:** v0.23 / 669  
**Source registry:** v1.64 / 226  
**Change ledger:** v0.12  
**Current governance queue:** 74 fully explicit / 152 missing-any / 81 P1 / 71 P2

## Purpose

The current 81-source P1 queue is not treated as a mechanical dependency ranking. A fresh diagnostic on the exact merged v0.23/v1.64 checkpoint found:

- all 81 remaining P1 sources are forward-active;
- all 81 share the same three missing modern governance fields (`canonical_provenance_use`, `automated_monitoring_use`, `verification_mode`);
- South Asia is the only region below both the project series-diversity and institution-diversity thresholds;
- `PHYSICAL_CLIMATE_RISK` is the only category below five unique canonical series; and
- monetary/macroeconomic occurrences still dominate the canonical registry.

This cohort therefore combines one high-leverage global agricultural source with deliberate regional/category correction. Selection is not a claim that regional representation should override source quality or materiality; every row still had to pass an independent authority/scope audit.

Selected sources:

| Source | Institution / scope | Primary deps | Decision |
|---|---|---:|---|
| `WSSRC-REGJ-002` | Central Bank of Sri Lanka | 2 | Governance completion; announcement dates preserved. |
| `WSSRC-RISK-001` | Australian Bureau of Meteorology cyclone season | 2 | Governance completion; risk-window semantics preserved. |
| `WSSRC-REG2-004` | Banco Central de Chile financial-policy calendar | 2 | Governance completion; canonical dates preserved. |
| `WSSRC-HEALTH-004` | WHO Western Pacific RC77 | 1 | Governance completion; session-specific page remains timing authority. |
| `WSSRC-REG-009` | Malaysia Ministry of Finance Budget 2027 | 1 | Governance completion plus one canonical population-policy semantic correction; date unchanged. |
| `WSSRC-INT-018` | African Development Bank Annual Meetings | 1 | Governance completion; direct 2021 Board resolution added as retained evidence/backup; PROVISIONAL status preserved. |
| `WSSRC-COM-005` | USDA National Agricultural Statistics Service | 5 | Governance completion; manual authoritative verification despite PDF/iCalendar availability. |

## 1. Central Bank of Sri Lanka — `WSSRC-REGJ-002`

Authoritative calendar:  
https://www.cbsl.gov.lk/en/monetary-policy/monetary-policy-communication/monetary-policy-advance-release-calendar

Website-access FAQ:  
https://www.cbsl.gov.lk/en/faq/about-this-website

Findings:

- The current official advance-release calendar distinguishes Monetary Policy Board meeting dates from public monetary-policy announcement dates.
- The two canonical dependencies correctly represent the **public announcement** dates: 30 September 2026 and 20 November 2026, following Board meetings on the preceding day.
- No canonical date, time, identity or occurrence semantics require repair.
- CBSL provides ordinary web/download access but this review found no source-specific unrestricted reuse or automated polling grant for this calendar.
- Public availability therefore does not become an automation permission inference.

Frozen governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 2. Australian Bureau of Meteorology tropical-cyclone season — `WSSRC-RISK-001`

Authoritative monitoring page:  
https://www.bom.gov.au/climate/cyclones/australia/

Bureau copyright policy:  
https://www.bom.gov.au/copyright

Findings:

- The Bureau states that the **official Australian tropical cyclone season runs from 1 November to 30 April**.
- The two existing canonical windows (2026–27 and 2027–28) already represent that institutional risk season correctly.
- These records remain probabilistic/risk windows. They do not predict a cyclone occurrence and do not replace the Shock Register for actual cyclones.
- The cyclone page explicitly applies CC BY 4.0 to maps, graphs and diagrams unless otherwise noted. The Bureau's general copyright policy separately states that, where no specific terms are attached, content may be used personally or within an organisation but not supplied to others or used commercially without permission.
- Consequently the page-element CC licence must **not** be expanded into a blanket licence for all page text/content, and no automated retrieval permission is inferred.

Frozen governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 3. Banco Central de Chile financial-policy calendar — `WSSRC-REG2-004`

Current official calendar:  
https://www.bcentral.cl/en/news-and-publications/press/monetary-and-financial-policy-calendar

Current first-half FPM communiqué corroborating the next meeting:  
https://www.bcentral.cl/en/web/banco-central/content/-/detalle/prensa/comunicados-rpf/reunion-de-politica-financiera-primer-semestre-2026

Findings:

- The Bank's current Financial Policy Calendar lists the second-half 2026 Financial Policy Meeting for 13 and 16 November, the Financial Stability Report for 17 November, and the FPM minutes for 1 December.
- The first-half communiqué independently says the next FPM is 13 and 16 November and that its statement will be released at 18:00 on the second day.
- WORLD SIGNALS correctly uses 16 November for the decision/communiqué occurrence and 17 November for the Financial Stability Report. It does not misrepresent the meeting as a continuous four-day event.
- Existing rights review allows internal/personal factual reference with attribution but restricts external distribution and does not clear production polling.

Frozen governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

No canonical mutation.

## 4. WHO Western Pacific Regional Committee 77 — `WSSRC-HEALTH-004`

Session-specific authority:  
https://www.who.int/westernpacific/about/governance/regional-committee/session-77

WHO permissions/terms family:  
https://www.who.int/about/policies/publishing/permissions  
https://www.who.int/about/policies/publishing/copyright/terms-and-conditions

Findings:

- The session-specific Western Pacific page states **19–22 October 2026 in Manila**.
- A broader WHO governance directory has previously shown a conflicting 19–23 October span. The source record already handles this correctly: the session-specific regional page governs canonical timing and the broader directory is retained only as conflicting aggregator evidence.
- No event mutation is required.
- WHO permissions material confirms that wider reproduction of WHO copyrighted material generally requires permission unless a specific licence applies. No production crawler permission is inferred from the public HTML session page.

Frozen governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 5. Malaysia Budget 2027 — `WSSRC-REG-009` / `WSO-REG-A-0014`

Authoritative Pre-Budget Statement 2027:  
https://www.mof.gov.my/portal/en/news/press-release/pre-budget-statement-2027

Findings:

- The Ministry of Finance explicitly announces that Budget 2027 will be tabled in Parliament on **9 October 2026**.
- The canonical civil date is therefore correct and remains CONFIRMED. No clock time is supplied and none is inferred.
- The source supports an **authoritatively scheduled policy milestone**, not an independently established statutory/legal deadline.
- The current canonical `population_horizon_policy = EXACT_LEGAL_DEADLINE_ONLY` is therefore semantically too narrow/wrong for this occurrence even though the date itself is correct.
- Existing canonical vocabulary already provides `EXACT_LEGAL_OR_POLICY_MILESTONE_ONLY`, used for exact fiscal milestones that need not be statutory deadlines. Reusing that vocabulary avoids taxonomy expansion.
- Ministry pages currently display `Copyright © 2026 Ministry of Finance. All Rights Reserved.` No unrestricted content-reuse or automated retrieval grant has been identified.

Frozen canonical repair:

- preserve `start_local = 2026-10-09`;
- preserve CONFIRMED certainty, stable occurrence ID, source ID and assertion IDs;
- change only `population_horizon_policy` from `EXACT_LEGAL_DEADLINE_ONLY` to `EXACT_LEGAL_OR_POLICY_MILESTONE_ONLY` plus a clarifying note/verification date;
- this is a semantic classification repair, not a date repair.

Frozen governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## 6. African Development Bank 2027 Annual Meetings — `WSSRC-INT-018` / `WSO-INT-A-0014`

Stable source-family index:  
https://www.afdb.org/en/documents/board-documents/board-of-governors-documents/official-records-of-the-annual-meetings

Direct first-order Board resolution / official record:  
https://www.afdb.org/sites/default/files/documents/board-documents/2021_annual_meetings_-_official_record.pdf

AfDB site terms:  
https://www.afdb.org/en/terms-and-conditions

Findings:

- Resolution B/BG/2021/01 – F/BG/2021/01 expressly resolves that the **2027 Annual Meetings take place in Niamey, Niger, 24–28 May 2027**.
- The same resolution notes that Abidjan remains a fallback venue if an unexpected need arises to reconsider a proposed host country.
- The canonical record's PROVISIONAL status is therefore appropriate: the date/host are formally resolved, but an explicit fallback clause exists and the event remains well forward of occurrence.
- No newer official source located in this review supersedes the resolution for 2027.
- The existing source identity is already scoped as an `official_governance_documents` source family for Annual Meetings resolutions/records. The direct resolution is a member of that same authority family, so a new source ID is unnecessary. The direct PDF should instead become retained backup/evidence so the generic index is not the only navigational route.
- AfDB Terms & Conditions permit printing/downloading/copying for personal non-commercial use but restrict commercial redistribution/derivative use without written consent. No crawler permission is inferred.

Frozen governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

No canonical mutation.

## 7. USDA National Agricultural Statistics Service — `WSSRC-COM-005`

Official publication calendar:  
https://www.nass.usda.gov/Publications/Calendar/

Current report-by-date view:  
https://www.nass.usda.gov/Publications/Calendar/reports_by_date.php

Findings:

- NASS publishes a 2026 Agricultural Statistics Board calendar in PDF and iCalendar forms plus HTML date views.
- Current official September 2026 calendar evidence confirms Crop Production on 11 September at 12:00 ET and Grain Stocks on 30 September at 12:00 ET; the canonical source also supports later scheduled Crop Production occurrences.
- Existing source governance already records general NASS information as public-domain factual material with acknowledgement requested, while automated retrieval remains pending endpoint-operational review.
- A repository-wide inspection found **no NASS/USDA parser implementation, fixture or source-specific adapter evidence** despite the source record describing an `ICS+PDF` parser type.
- Machine readability therefore does not earn `AUTOMATED_PILOT`. Verification remains manual until parser code, tests and operating evidence exist.

Frozen governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

No canonical mutation and no monitor activation.

## Frozen transaction architecture

Subject to simulation, the later reviewed transaction is a **four-production-file transaction**:

1. `data/canonical/registry.json`
2. `data/sources/registry.json`
3. `data/changes/ledger.json`
4. `data/coverage/biosecurity_overlay.json`

Target post-state:

- canonical v0.23 → **v0.24**, 669 records unchanged;
- source registry v1.64 → **v1.65**, 226 sources unchanged;
- change ledger v0.12 → **v0.13**;
- biosecurity overlay checkpoint v0.23 → **v0.24**, 669 unchanged;
- governance: **81 fully explicit / 145 missing-any / 74 P1 / 71 P2**.

The change ledger gains exactly one reviewed canonical-semantic entry for Malaysia. `committed_at` is generated only at reviewed apply time.

## Protected invariants

The guarded helper/tests must prove:

- canonical count remains 669 and stable occurrence identity/order is unchanged;
- **only `WSO-REG-A-0014` changes canonically**;
- Malaysia remains exactly `2026-10-09`, CONFIRMED, with no clock time; only the population-policy semantic/clarifying metadata changes;
- CBSL announcement dates remain 2026-09-30 and 2026-11-20;
- BoM cyclone windows remain 1 November–30 April and remain risk-window records rather than deterministic events;
- Chile remains 2026-11-16 decision/communiqué and 2026-11-17 Financial Stability Report;
- WHO WPRO RC77 remains 2026-10-19 through 2026-10-22;
- AfDB 2027 Annual Meetings remain 2027-05-24 through 2027-05-28, Niamey, PROVISIONAL;
- all USDA canonical dates/times remain byte-identical;
- Brazil presidential inauguration remains 2027-01-05;
- India 2027–28 Budget remains unscheduled TBC;
- ASEAN 2027 summit windows remain month-only May/November windows;
- Colombia source decomposition remains intact;
- assertion identities do not change;
- automatic canonical commit remains false;
- Google Calendar write remains false;
- no monitor route is added or activated.

## Research boundary

This document freezes research and architecture only. Production mutation must occur only after preparation tests and a disposable simulated post-state pass, then on a fresh transaction branch from the exact manually merged preparation baseline behind the explicit write gate.
