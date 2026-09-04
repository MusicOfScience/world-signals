# WORLD SIGNALS — P1 forward source-governance triage A research v0.1

**Status:** FROZEN FOR REVIEW  
**Reference date:** 2026-09-05  
**Repository checkpoint:** `5926dc8e86beac57a3684df89d411833ea0ca4f5`  
**Canonical registry:** v0.22 / 669  
**Source registry:** v1.63 / 225  
**Scope:** read-only diagnosis of the remaining P1 source-governance queue plus bounded current-source research on a deliberately international six-source test cohort. No source-registry, canonical-registry, ledger, monitor, calendar or write-gate mutation is authorised by this document.

## Executive finding

The remaining P1 queue is not a mixed collection of seven-field governance gaps. It is a much narrower late-stage queue:

- **87 P1 source rows** remain;
- **87/87 have active/future canonical dependencies** as of 2026-09-05;
- **0 are historical-only**;
- **all 87 share the same unresolved three-field shape**:
  - `canonical_provenance_use`
  - `automated_monitoring_use`
  - `verification_mode`.

That apparent uniformity is deceptive. A source row can be missing the same three governance fields for very different reasons: routine unreviewed official publication, endpoint-rights ambiguity, weak source scope, legal/date semantics, forecast-versus-confirmed status, or a registered page that is official but does not actually support the exact canonical proposition.

The next stage therefore must not be a blind three-field backfill transaction. Each candidate must first pass a **provenance-scope assertion**: does this exact source support the exact occurrence identity, date/window, certainty status and event semantics currently attributed to it?

## Queue topology

### Unresolved P1 source rows by jurisdiction — largest concentrations

| Jurisdiction | Source rows |
|---|---:|
| Australia | 10 |
| United States | 9 |
| European Union | 7 |
| Global | 5 |
| China | 4 |
| United States / Global | 3 |
| Brazil | 2 |
| G20 | 2 |
| South Korea | 2 |
| Chile | 2 |
| European Union / Russia | 2 |
| France | 2 |
| United Kingdom | 2 |
| Malaysia | 2 |

The remainder is distributed across single-source or small jurisdictions including ASEAN, Thailand, Sri Lanka, Philippines, South Africa, Japan, India, Indonesia, Argentina, Peru, Pacific, Africa, APEC, African Union, BRICS and other regional/global groupings.

### Active/future canonical dependencies by jurisdiction — largest concentrations

| Jurisdiction | Dependencies |
|---|---:|
| Australia | 32 |
| United States | 25 |
| European Union | 13 |
| United States / Global | 12 |
| Global | 10 |
| United States/Global | 5 |
| Germany | 5 |
| Brazil | 4 |
| China | 4 |
| Victoria, Australia | 3 |
| G20 | 3 |
| South Korea | 3 |
| Chile | 3 |
| European Union / Russia | 3 |

This is why a mechanical dependency ranking would again pull the work toward the United States and Europe even though the Charter explicitly requires a corrective international lens.

### Unresolved P1 source rows by domain

| Domain | Source rows |
|---|---:|
| international_institutions | 16 |
| fiscal_sovereign | 14 |
| macroeconomic_releases | 9 |
| fiscal_sovereign_finance | 7 |
| monetary_policy | 5 |
| elections | 4 |
| technology_critical_infrastructure | 4 |
| trade_sanctions_industrial_policy | 4 |
| china_political_economy | 4 |
| health_biosecurity | 4 |
| agriculture_food | 3 |
| energy_commodities | 3 |
| financial_market_structure | 3 |
| financial_stability_regulation | 3 |
| physical_climate_risk | 2 |
| climate_environment | 1 |
| monetary_financial_policy | 1 |

### Active/future canonical dependencies by domain

| Domain | Dependencies |
|---|---:|
| macroeconomic_releases | 41 |
| fiscal_sovereign | 25 |
| international_institutions | 23 |
| agriculture_food | 11 |
| monetary_policy | 10 |
| energy_commodities | 7 |
| fiscal_sovereign_finance | 7 |
| elections | 6 |
| financial_market_structure | 5 |
| technology_critical_infrastructure | 5 |
| trade_sanctions_industrial_policy | 5 |
| financial_stability_regulation | 4 |
| physical_climate_risk | 4 |
| china_political_economy | 4 |
| health_biosecurity | 4 |
| climate_environment | 3 |
| monetary_financial_policy | 2 |

## Selection rule

This cohort intentionally does **not** take the mechanical top six. It applies seven tests:

1. active/future dependency;
2. temporal relevance;
3. institutional significance;
4. governance-information value;
5. source-type diversity;
6. geographic corrective value; and
7. provenance-scope risk.

Selected test cohort:

| Source | Institution / surface | Region | Source class | Why selected |
|---|---|---|---|---|
| `WSSRC-MAC-021` | Australian Bureau of Statistics — Monthly Household Spending Indicator | Australia | official statistical product/release schedule | Tests a repeatable ABS publication pattern without assuming authority-level inheritance. |
| `WSSRC-REG2-005` | Ministerio de Economía / Argentina.gob.ar — Budget 2027 process regulation | Latin America | official legal/regulatory text | Imminent fiscal boundary and a direct test of date-language semantics. |
| `WSSRC-REG-005` | Indonesia Ministry of Finance / DJPb — APBN cycle | Southeast Asia | official explanatory process page | Tests whether a generic official explainer is sufficiently precise for a legal-latest canonical boundary. |
| `WSSRC-EL-ZA-001` | South African COGTA — 2026 local-government election date | Africa | official government election-date notice | Tests legal/public election-date provenance and endpoint resilience. |
| `WSSRC-INT-021` | Singapore MFA / ASEAN Chair 2027 | Southeast Asia / ASEAN | official host-government announcement | Tests forecast windows versus exact-date canonical semantics for a major regional institution. |
| `WSSRC-FIS-023` | Ministry of Finance, Government of India — Union Budget portal | India | official budget portal | Tests the distinction between an official publication portal and an authoritative legal/scheduling source. |

The cohort contains no US or EU source. That is deliberate for this bounded research tranche; it is a corrective to the queue's dependency-weighted pull, not a claim that US/EU sources are unimportant.

## Research standard

For each source, current official material was rechecked on 2026-09-05. The research keeps four questions separate:

- does the source support the exact canonical factual proposition?
- does it support the date/window and certainty status currently represented?
- does any reuse/right statement support curated factual provenance without implying automated retrieval permission?
- what verification mode follows from the source surface and existing runtime evidence?

Official status, public accessibility, HTML availability, a successful fetch, `robots.txt`, an open-content licence, or an existing parser is never by itself treated as an unrestricted automation grant.

## `WSSRC-MAC-021` — Australian Bureau of Statistics / Monthly Household Spending Indicator

Authoritative product and forward-release surface:  
https://www.abs.gov.au/statistics/economy/finance/monthly-household-spending-indicator

ABS forward-release calendar:  
https://www.abs.gov.au/release-calendar/future-releases-calendar

ABS website copyright / Creative Commons terms:  
https://www.abs.gov.au/website-privacy-copyright-and-disclaimer

Current findings:

- the product page currently publishes future MHSI releases, including 29 September 2026 at 11:30 AEST, 4 November 2026 at 11:30 AEDT, 3 December 2026 at 11:30 AEDT and subsequent releases;
- the ABS release calendar independently exposes the same series and warns that future release dates may change;
- the general ABS website material is licensed under CC BY 4.0 subject to stated exceptions including third-party material, microdata, marks and branding;
- the reviewed general website terms do not turn the MHSI HTML product page into an unrestricted automated-polling endpoint;
- the separate ABS Indicator API has its own access terms and cannot be silently treated as permission to crawl this product page or as a substitute release-calendar endpoint.

**Frozen candidate classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

**Decision:** candidate is suitable for a later guarded governance transaction, provided the row and dependency surface have not drifted.

## `WSSRC-REG2-005` — Argentina Budget 2027 process regulation

Registered authoritative surface:  
https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-446-2026-424520/texto

Argentina.gob.ar terms:  
https://www.argentina.gob.ar/terminos-y-condiciones

Current findings:

- Resolution 446/2026 is an official Ministry of Economy instrument establishing the 2027 national-budget formulation timetable;
- the resolution expressly recites Article 26 of Law 24.156 as requiring presentation of the Budget Bill to the Chamber of Deputies **before 15 September** of the preceding year;
- the current canonical dependency is named `Argentina Budget 2027 — statutory submission boundary` and is represented at `2026-09-15`;
- that creates a date-semantics question that must be resolved against the underlying statute and authoritative legal interpretation before the current occurrence is treated as a settled 15 September civil-date boundary;
- Argentina.gob.ar states that its own digital content is licensed under CC BY 4.0 unless otherwise indicated;
- open-content licensing does not itself authorise unrestricted automated polling.

**Frozen decision:** **HOLD — CANONICAL DATE / LEGAL-SEMANTICS REVIEW REQUIRED.**

No write to the three unresolved governance fields is authorised in this tranche. The immediate task is to determine whether `2026-09-15` is intended as a presentation day, an inclusive legal deadline, a display convention, or an off-by-one representation of the statutory phrase “before 15 September”. The project must not silently reinterpret the law to make the existing date fit.

## `WSSRC-REG-005` — Indonesia APBN cycle

Registered surface:  
https://djpb.kemenkeu.go.id/portal/id/layanan/kantor-pusat/sistem-manajemen-investasi/157-layanan/siklus-apbn.html

Stronger official legal authority identified during this review:  
https://jdih.kemenkeu.go.id/dok/uu-17-tahun-2003

Current findings:

- the registered DJPb page is an official Ministry of Finance treasury explainer of the APBN cycle;
- it describes budget discussion as August–October and establishment at the end of October;
- the page also contains historical/example material and cites non-primary explanatory sources alongside official material, so it is not the cleanest authority for an exact legal boundary;
- Ministry of Finance JDIH carries Law No. 17 of 2003 on State Finances as a direct legal source;
- Article 15(4) states that the DPR decision on the APBN bill is taken no later than two months before the relevant fiscal year begins;
- the current canonical dependency `Indonesia APBN 2027 — DPR approval legal-latest boundary` is represented at `2026-10-31`;
- translating “no later than two months before” into one exact civil date requires explicit legal/date semantics, not an inference from the generic explainer alone.

**Frozen decision:** **HOLD — PROVENANCE-SCOPE / LEGAL-DATE REVIEW REQUIRED.**

The registered generic explainer should not be backfilled as though it were the strongest legal authority. Review whether the occurrence should point directly to the JDIH statute, whether a distinct legal source record is needed, and how the two-month rule maps to the canonical civil date. No governance-field write is authorised yet.

## `WSSRC-EL-ZA-001` — South Africa 2026 Local Government Elections

Registered COGTA notice:  
https://www.cogta.gov.za/index.php/2026/08/07/minister-hlabisa-gazzetes-the-date-for-the-2026-local-government-elections/

Independent current official COGTA confirmation reviewed on 2026-09-05:  
https://www.cogta.gov.za/index.php/2026/09/04/minister-hlabisa-notes-encouraging-progress-during-follow-up-visit-to-ditsobotla-local-municipality/

Current findings:

- current COGTA material expressly confirms the 2026 Local Government Elections for **4 November 2026**;
- the date is presented as a scheduled election date, not merely an expected window;
- the originally registered August notice was not reliably retrievable in the bounded web check, while a 4 September COGTA release was available and independently confirmed the same date;
- no reviewed site-wide term expressly grants unrestricted automated retrieval of this COGTA HTML route;
- endpoint instability and the legal importance of the election date favour manual authoritative recheck plus an official backup source rather than assuming a production crawler route.

**Frozen candidate classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

**Decision:** candidate is suitable for a later guarded governance transaction, but the source row should retain or add an authoritative backup route rather than pretending the registered article is operationally robust.

## `WSSRC-INT-021` — Singapore MFA / ASEAN Chair 2027

Registered MFA surface:  
https://www.mfa.gov.sg/newsroom/announcements-and-highlights/invitation-for-proposals-for-sponsorship-of-food-and-drinks--furniture--audio-visual-equipment--event-tokens-and-medical-services-for-high-level-meetings-and-conferences-in-2027/

Earlier MFA announcement with more specific forecast ranges:  
https://www.mfa.gov.sg/newsroom/announcements-and-highlights/invitation-for-proposals-for-sponsorship-of-luxury-saloon-vehicles-for-high-level-meetings-and-conferences-in-2027-/

MFA terms of use:  
https://www.mfa.gov.sg/terms-of-use/

Current findings:

- MFA confirms Singapore will chair ASEAN in 2027 and identifies the high-level meeting sequence;
- the currently registered 27 August 2026 sponsorship notice describes event timing mostly at month level and explicitly calls the table a **forecast**;
- an earlier 1 April 2026 MFA sponsorship notice provides more specific forecast date ranges for the Foreign Ministers’ Retreat, 50th ASEAN Summit, 60th ASEAN Foreign Ministers’ Meeting and 51st ASEAN Summit;
- therefore the source family is authoritative, but the exact registered page may not support every exact date/range that downstream canonical occurrences could carry;
- MFA terms state that website materials are protected by intellectual-property law and commercial reproduction/reuse requires prior written permission; the terms reviewed do not expressly grant unrestricted automated polling.

**Frozen decision:** **HOLD — DEPENDENCY/SOURCE-SCOPE AUDIT REQUIRED.**

Before backfill, inspect every canonical occurrence attributed to `WSSRC-INT-021` and verify whether its exact date/window is supported by the 27 August page, the earlier 1 April page, another official host-government announcement, or only a forecast inference. Preserve `PROVISIONAL` / `EXPECTED_WINDOW` semantics where the source itself says forecast. No governance-field write is authorised in this tranche.

## `WSSRC-FIS-023` — India Union Budget portal

Official portal:  
https://www.indiabudget.gov.in/

Terms of use:  
https://www.indiabudget.gov.in/termsofuse.php

Current findings:

- the Ministry of Finance portal is an authoritative publication repository for Union Budget documents and currently exposes the 2026–27 budget corpus and historical budgets;
- it does not, merely by being the official budget portal, establish a future 2027–28 presentation date or legal deadline;
- its terms explicitly say that website content should not be construed as a statement of law and advise verification with the relevant department or other source where ambiguity exists;
- the portal is therefore a strong publication/result source, but a potentially weak sole provenance source for an undated or rule-derived future budget occurrence;
- the reviewed terms do not expressly grant unrestricted automated monitoring of the portal.

**Frozen decision:** **HOLD — SOURCE-ROLE REVIEW REQUIRED.**

Determine whether the current canonical dependency uses this source as a publication portal, an expectation source, or an asserted schedule/legal authority. If the occurrence represents a statutory or customary future date, identify and register the issuing legal/scheduling authority rather than promoting the portal beyond what it says. No governance-field write is authorised in this tranche.

## Cohort outcome

| Source | Outcome | Later governance transaction? |
|---|---|---|
| `WSSRC-MAC-021` ABS MHSI | clean curated factual provenance; automation unresolved | **candidate** |
| `WSSRC-REG2-005` Argentina budget process | date/legal semantics conflict requires review | **hold** |
| `WSSRC-REG-005` Indonesia APBN cycle | stronger legal source identified; exact-date semantics require review | **hold** |
| `WSSRC-EL-ZA-001` South Africa local elections | clean current official confirmation; endpoint robustness weak | **candidate** |
| `WSSRC-INT-021` Singapore MFA / ASEAN Chair 2027 | forecast/exact-date source-scope audit required | **hold** |
| `WSSRC-FIS-023` India Union Budget portal | publication portal should not be promoted to legal/schedule authority without evidence | **hold** |

Only **2 of 6** are currently suitable candidates for a simple three-field guarded governance transaction. **4 of 6** should remain held pending source/date/status repair or clarification.

This is a strong warning against treating the remaining 87 P1 rows as a clerical backfill queue.

## Architecture decision

Add the following precondition to subsequent P1 governance research, without changing the schema in this document:

> Before filling `canonical_provenance_use`, `automated_monitoring_use`, or `verification_mode`, verify that the registered source supports the exact canonical proposition attributed to it: occurrence identity, date/window, certainty status and source role.

This is a research/transaction gate, not a new canonical field and not an authority-level inheritance mechanism.

Authority-level rights evidence may be reused as evidence where genuinely applicable, but dataset/source-specific operational facts — endpoint role, date semantics, publication cadence, parser suitability, forecast status and verification mode — remain row-specific.

## Recommended next stage

Proceed in this order:

1. **Argentina canonical-date semantics audit** against Law 24.156 and current 2027 budget-process authority.
2. **Indonesia provenance-scope audit** using Ministry of Finance JDIH Law 17/2003 and any current 2027 APBN procedural instrument.
3. **ASEAN 2027 dependency audit** across every occurrence attributed to `WSSRC-INT-021`, preserving forecast/provisional semantics.
4. **India source-role audit** to distinguish publication portal from legal/scheduling authority.
5. Only after those are settled, prepare a guarded transaction for clean rows such as ABS MHSI and South Africa COGTA, alongside any repaired rows that become transaction-ready.
6. Re-run the P1 queue topology after each reviewed production transaction; do not assume a six-row research cohort maps one-to-one to six registry writes.

## Protected invariants

This research checkpoint must leave unchanged:

- canonical registry v0.22 / 669;
- source registry v1.63 / 225;
- all canonical dates/times and stable IDs;
- Brazil presidential inauguration `2027-01-05`;
- Colombia machine/manual source split;
- automatic canonical commits OFF;
- Google Calendar writes OFF.

No production transaction is authorised by this document.
