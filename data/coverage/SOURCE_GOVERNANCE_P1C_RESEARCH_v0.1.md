# WORLD SIGNALS — P1-C source-governance research v0.1

**Reference date:** 2026-09-04  
**Repository checkpoint:** `f9f9a5a3f77bd724e6e02cbc1e47e1ee8ac5a358`  
**Canonical registry:** v0.20 / 669  
**Source registry:** v1.54 / 223  
**Monitor expectations:** v0.7  
**Scope:** bounded research for six unresolved P1 canonical-dependent source records, with one high-dependency SNB record explicitly held for provenance-scope repair. No source-registry mutation is authorised by this document.

## Selection rule

The measured post-P1-B audit leaves **133 P1 canonical-dependent** and **71 P2 registry-only** governance records. P1-C is deliberately not the numerical top six.

The cohort combines:

1. canonical dependency;
2. active forward analytical horizon;
3. source-governance information value;
4. regional and institutional breadth; and
5. domain diversity.

Selected cohort:

| Source | Institution / surface | Dependencies | Jurisdiction | Domain |
|---|---|---:|---|---|
| `WSSRC-MAC-005` | Eurostat release calendar | 12 | European Union | macroeconomic releases |
| `WSSRC-CB-008` | Bank of Canada policy-rate schedule | 11 | Canada | monetary policy |
| `WSSRC-FIS-007` | Japan Ministry of Finance JGB auction calendar | 10 | Japan | fiscal / sovereign |
| `WSSRC-EL-NZ-001` | Electoral Commission NZ 2026 General Election timetable | 6 | New Zealand | elections |
| `WSSRC-CN-013` | People's Bank of China financial-statistics publication rule | 5 | China | macroeconomic releases |
| `WSSRC-INT-027` | UN General Assembly mandated events | 5 | Global | international institutions |

This gives P1-C one EU, one Canadian, two East Asian, one Aotearoa New Zealand and one global institutional source across five analytical domains.

## Research method

For each candidate, current official material was rechecked on 2026-09-04. Four questions remain separate:

- may authoritative factual schedule/rule metadata support the canonical registry?
- what reuse conditions apply to the source material?
- is automated retrieval expressly permitted, expressly restricted, supported by an official subscription/API route, or unresolved?
- what verification mode is justified by rights plus current parser/runtime evidence?

Public access, official status, machine readability, `robots.txt`, parser existence and successful fetching are never sufficient on their own to establish automation permission.

## Held before selection — `WSSRC-CB-009` Swiss National Bank

Current registry authoritative URL:  
https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions

Actual forward event schedule:  
https://www.snb.ch/en/services-events/digital-services/event-schedule

Copyright / disclaimer:  
https://www.snb.ch/en/srv/disclaimer_copyright

The post-P1-B audit ranks SNB first among unresolved P1 rows at 18 canonical dependencies. It is **not admitted to P1-C**.

Current research found a source-scope defect: the registry identifies the monetary-policy decisions/history page as the authoritative forward schedule surface, but that page does not provide the future 2026/2027 monetary-policy assessment schedule. The future dates are published on the separate SNB event-schedule page.

This is a provenance-repair issue, not evidence that the existing canonical dates are wrong. P1-C must not backfill modern governance fields onto `WSSRC-CB-009` until the source relationship is repaired and re-audited.

**P1-C status:** `EXCLUDED_PROVENANCE_SCOPE_REPAIR_REQUIRED`.

## `WSSRC-MAC-005` — Eurostat

Authoritative calendar:  
https://ec.europa.eu/eurostat/news/euro-indicators/release-calendar

Official internet-calendar instructions:  
https://ec.europa.eu/eurostat/subscribe/ics.format

Copyright / reuse:  
https://ec.europa.eu/eurostat/help/copyright-notice

Current findings:

- Eurostat's 2026 calendar publishes scheduled releases with weekly planning confirmed each Friday for the following week; planning further ahead remains provisional.
- Eurostat expressly offers its release calendar as an internet calendar in `.ics` format.
- Eurostat states that the internet calendar is updated whenever the release calendar is updated and that those updates are automatically included in the subscriber's calendar.
- The internet calendar provides the same information as the online release calendar and can be filtered by theme/category.
- Eurostat editorial content is CC BY 4.0; statistical data, metadata, publications and other dissemination tools may be reused commercially or non-commercially with source acknowledgement, subject to stated exceptions.
- WORLD SIGNALS already records an ICS-primary parser, pilot research verification and a preferred official ICS endpoint.

The explicit internet-calendar subscription route is materially different from inferring permission from machine readability. Eurostat itself invites automated synchronization through that route. Automation clearance is therefore limited to the official subscription/feed mechanism and its published behaviour; it is not a blanket licence for arbitrary HTML crawling.

**Frozen P1-C classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = CLEARED`
- `verification_mode = AUTOMATED_PILOT`

## `WSSRC-CB-008` — Bank of Canada

Authoritative schedule:  
https://www.bankofcanada.ca/core-functions/monetary-policy/key-interest-rate/

2027 schedule release:  
https://www.bankofcanada.ca/2026/07/bank-canada-publishes-2027-schedule-policy-interest-rate-announcements-other-major-publications/

Terms:  
https://www.bankofcanada.ca/terms/

Current findings:

- the Bank currently publishes policy interest-rate dates for the remainder of 2026 and all of 2027;
- the 27 July 2026 schedule release specifies eight 2027 decisions and states that all interest-rate announcements are at **09:45 ET**;
- Monetary Policy Reports are concurrent with January, April, July and October decisions;
- the Bank's terms permit use/copy/distribution/transmission of its website content subject to attribution, accuracy, paid-service notice and third-party restrictions;
- the terms expressly prohibit circumventing request-frequency limits or accessing the site in ways that disable, damage, overburden or impair it, and refer to Bank services such as the Valet API;
- those operational restrictions do not by themselves establish that unrestricted polling of the policy schedule is permitted;
- the existing source record has post-event pilot research verification.

**Frozen P1-C classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = AUTOMATED_PILOT`

## `WSSRC-FIS-007` — Japan Ministry of Finance JGB auction calendar

Authoritative calendar:  
https://www.mof.go.jp/english/policy/jgbs/auction/calendar/index.htm

Copyright / terms:  
https://www.mof.go.jp/english/about_mof/notice/index.html

Current findings:

- the official auction calendar publishes monthly JGB/T-bill auction schedules and separately records alterations;
- the calendar warns that schedules may be changed or added to and that issue amounts are announced later, so scheduled date, later announcement and result remain separate evidence objects;
- Ministry website content is generally governed by Japan's Public Data License v1.0 unless otherwise indicated, subject to legal and third-party exceptions;
- that content-reuse licence does not itself define or grant unrestricted crawler behaviour;
- WORLD SIGNALS already records a research-verified auction-calendar/announcement monitor and `PILOT_VALIDATED_NO_AUTO_COMMIT` monitoring readiness.

**Frozen P1-C classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = AUTOMATED_PILOT`

## `WSSRC-EL-NZ-001` — Electoral Commission New Zealand

Authoritative timetable:  
https://elections.nz/media-and-news/2026/key-dates-for-2026-general-election

Supporting current candidate timetable:  
https://elections.nz/guidance-and-rules/candidate-hub/key-information-and-dates

Current findings:

- the Electoral Commission confirmed the 2026 General Election timetable after the Prime Minister announced the election date;
- the election is Saturday **7 November 2026**;
- the official timetable includes dissolution, writ day, nominations, overseas voting, advance voting, election day, official results and return-of-writ milestones;
- the candidate timetable states that the timetable is set in accordance with the Electoral Act 1993 and currently extends to the last day for Parliament to meet on 14 January 2027;
- the Commission also publishes media resources and says that, where possible, open data files will be made available for election information such as candidates and voting places;
- the reviewed official-site material displays Electoral Commission copyright but no general website reuse licence or express bot/crawler permission was located during this review.

P1-C therefore preserves a narrow factual-metadata classification only. It does not imply permission to reproduce protected Commission content or to automate the HTML page.

Government formation remains outside this Electoral Commission timetable and must not be fabricated as a fixed Commission milestone.

**Frozen P1-C classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## `WSSRC-CN-013` — People's Bank of China financial-statistics publication rule

Authoritative rule:  
https://www.pbc.gov.cn/en/3688253/3689009/3788456/2025092319414130565/index.html

Current findings:

- Article 21 of the official Administrative Rules for Financial Statistics states that the PBoC releases national financial-statistics data regularly;
- monthly data such as money supply, credit flow and assets/liabilities are to be released **within 20 days after the end of each month** through media and the PBoC website;
- this is a latest-publication-window rule, not an exact scheduled civil day or timestamp;
- the source record already limits reuse to public factual metadata and marks automation pending;
- no current general PBoC website crawler licence was identified in this review, so no automated permission is inferred from the existence of an HTML rule page or parser.

WORLD SIGNALS must preserve the rule as an expected window. It must not convert “within 20 days” into a fabricated exact release date, nor assume that separate aggregate-financing publications occur simultaneously.

**Frozen P1-C classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## `WSSRC-INT-027` — United Nations General Assembly mandated events

Authoritative mandated-events page:  
https://www.un.org/pga/80/mandated-events-80th-session/

UN website terms:  
https://www.un.org/en/about-us/terms-of-use

Current findings:

- the UN General Assembly mandated-events page currently lists the 22–28 September 2026 General Debate and multiple September 2026 high-level meetings;
- it also carries later mandates including a preparatory meeting by January 2027 and several 2027 high-level processes, some still at month/session precision;
- those source-native precision levels must be preserved; a month-only mandate cannot become a fabricated exact day;
- UN website terms permit users to visit, download and copy materials for personal non-commercial use, without rights to resell, redistribute, compile or create derivative works, subject to more specific restrictions;
- those general terms are not an automation grant and are materially narrower than the open-content licences applied to several other P1-C sources;
- no production monitoring evidence exists for this route.

The source remains useful as an authoritative manual informational reference for factual event metadata, but production automation is held unless a specifically authorised route is established.

**Frozen P1-C classification:**

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## Frozen classification table

| Source | Canonical provenance | Automated monitoring | Verification mode |
|---|---|---|---|
| `WSSRC-MAC-005` | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-008` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-FIS-007` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-EL-NZ-001` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-CN-013` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-INT-027` | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |

## Held controls

### Brazil TSE — `WSSRC-EL-BR-001`

Remains excluded. The 5 January 2027 presidential inauguration is constitutionally grounded rather than properly evidenced by the electoral-calendar source relationship. P1-C must not populate its modern governance fields or alter that canonical date.

### Swiss National Bank — `WSSRC-CB-009`

Remains excluded despite 18 dependencies. The registered decisions/history URL does not directly support the forward schedule described by the source record. The source relationship must be repaired before governance backfill.

## Transaction boundary

This research authorises only a frozen candidate plan for review/testing. It does **not** authorise an apply transaction.

Any eventual P1-C transaction must:

- change exactly the six selected source records plus source-registry version/reference metadata;
- preserve source count 223;
- leave canonical v0.20 / 669 byte-identical;
- leave monitor expectations v0.7 and monitor code unchanged;
- leave `WSSRC-EL-BR-001` and `WSSRC-CB-009` unchanged;
- preserve the Brazilian inauguration date `2027-01-05`;
- preserve Eurostat source-native certainty rather than upgrading provisional dates to confirmed;
- preserve PBoC source-native expected-window semantics rather than fabricating exact dates;
- leave automatic canonical commit CLOSED;
- leave Google Calendar writes OFF; and
- fail closed on selected dependency/version/governance-field drift or either held-source guard changing before application.
