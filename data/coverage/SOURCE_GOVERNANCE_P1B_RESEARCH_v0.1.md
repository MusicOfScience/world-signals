# WORLD SIGNALS — P1-B source-governance research v0.1

**Reference date:** 2026-09-04  
**Repository checkpoint:** `8078240bf7d4ae04106b612f3c044b92d631fd76`  
**Canonical registry:** v0.20 / 669  
**Source registry:** v1.53 / 223  
**Monitor expectations:** v0.7  
**Scope:** bounded research for six unresolved P1 canonical-dependent source records. No source-registry mutation is authorised by this document.

## Selection rule

The post-P1-A audit left 139 P1 canonical-dependent source records. Selection for P1-B is not a mechanical top-N by dependency. The cohort combines:

1. high canonical dependency;
2. active forward analytical horizon;
3. institutional/source-surface coherence;
4. regional balance; and
5. governance information value, especially sources that clarify the distinction between factual provenance and automated retrieval permission.

Selected cohort:

| Source | Institution | Canonical dependencies | Region | Reason for inclusion |
|---|---|---:|---|---|
| `WSSRC-CB-001` | Federal Reserve Board / FOMC | 44 | United States | Joint-highest unresolved dependency; public-domain factual content but automation remains a separate endpoint question. |
| `WSSRC-CB-006` | Bank of Japan | 44 | Japan | Joint-highest unresolved dependency; authoritative multi-day MPM schedule with non-commercial reproduction terms and no express automation grant. |
| `WSSRC-CB-002` | Reserve Bank of Australia | 33 | Australia | High dependency and home-region importance; general RBA content is CC BY 4.0 but website automation is not thereby licensed. |
| `WSSRC-CB-003` | European Central Bank | 22 | Euro area | High dependency; free reuse with attribution, while automated retrieval remains operationally separate. |
| `WSSRC-MAC-006` | Office for National Statistics | 19 | United Kingdom | High dependency and a deliberately useful positive-control case: ONS explicitly publishes bot/crawler guidance and official release-query/feed routes. |
| `WSSRC-CB-007` | Reserve Bank of New Zealand | 11 | New Zealand | Not numerical top-six, selected to prevent a mechanically US/European cohort and because RBNZ explicitly prohibits automated access without prior written permission. |

Regional mix is therefore three Indo-Pacific institutions, two European institutions and one US institution. This does **not** cure broader WORLD SIGNALS coverage imbalance; source-governance backlog priority is operational dependency, not a substitute for coverage architecture.

## Research method

For each source, current official material was rechecked on 2026-09-04. The research keeps four questions separate:

- may authoritative factual schedule metadata support the canonical registry?
- may the source material be redistributed and under what conditions?
- is automated retrieval expressly permitted, expressly restricted, or unresolved?
- what verification mode follows from both rights and current parser/runtime evidence?

Public accessibility, official status, machine readability, `robots.txt`, an existing parser, or a successful fetch is never treated by itself as automation permission.

## `WSSRC-CB-001` — Federal Reserve Board / FOMC

Authoritative schedule:  
https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

Rights/disclaimer:  
https://www.federalreserve.gov/disclaimer.htm

Current factual findings:

- the FOMC calendar currently carries 2026 and 2027 regular meeting dates;
- the Board states that each listed future meeting date is tentative until confirmed at the immediately preceding meeting;
- the Board disclaimer states that, unless otherwise indicated, information on the Board website is in the public domain and may be copied/distributed without permission, with Board citation requested;
- third-party material and Board seals/logos remain outside that general rule;
- the reviewed official terms do not expressly grant unrestricted crawler/scraper polling of the FOMC schedule surface.

Existing repository evidence already records a research-verified HTML parser/pilot and monitor endpoints. That supports an `AUTOMATED_PILOT` verification mode while keeping the rights/endpoint gate unresolved.

**Frozen P1-B classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = AUTOMATED_PILOT`

## `WSSRC-CB-006` — Bank of Japan

Authoritative schedule:  
https://www.boj.or.jp/en/mopo/mpmsche_minu/

Release schedule:  
https://www.boj.or.jp/en/about/calendar/index.htm

Copyright/disclaimer:  
https://www.boj.or.jp/en/copyright.htm

Current factual findings:

- the BoJ Monetary Policy Meetings page currently publishes two-day MPM windows for the remainder of 2026 and all of 2027, together with linked release dates for Outlook Reports, Summary of Opinions and minutes;
- BoJ states that regular MPMs are held eight times per year and each meeting runs over two days;
- BoJ permits copying/reproduction of website information with explicit source attribution except for commercial purposes, specially restricted content and images/graphics, for which advance permission is required;
- the reviewed terms do not expressly grant automated retrieval of the MPM schedule.

The source is therefore suitable for curated factual schedule provenance within the project's current non-commercial/public-information use, but automation remains unresolved. No live production parser evidence currently justifies automated verification status.

**Frozen P1-B classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## `WSSRC-CB-002` — Reserve Bank of Australia

Authoritative board schedule:  
https://www.rba.gov.au/schedules-events/board-meeting-schedules.html

Monetary-policy calendar:  
https://www.rba.gov.au/schedules-events/calendar.html?topics=monetary-policy-board

2026 decision-timing release:  
https://www.rba.gov.au/media-releases/2025/mr-25-02.html

Copyright notice:  
https://www.rba.gov.au/copyright/

Robots policy checked operationally:  
https://www.rba.gov.au/robots.txt

Current factual findings:

- the RBA currently publishes Monetary Policy Board meeting windows for 2026 and 2027;
- for 2026 the RBA expressly states that the policy outcome is announced at **2.30 pm on the second day** of each Board meeting and the Governor holds a **3.30 pm** media conference;
- the current monetary-policy calendar separately exposes the multi-day Board meeting, decision statement, media conference, Statement on Monetary Policy and minutes where applicable;
- most RBA material is licensed under CC BY 4.0, subject to expressly excluded material and third-party content;
- the current `robots.txt` does not disallow the board-schedule/calendar paths, but `robots.txt` is treated only as an operational signal, not as a licence grant;
- the copyright notice does not expressly grant automated polling.

WORLD SIGNALS must preserve the distinction between the advertised multi-day meeting window and the separately timed decision-release occurrence. The historical heuristic that the final advertised day is the decision day is unnecessary where the RBA publishes the decision timing directly, and must never replace current authoritative evidence.

Existing repository parser/runtime evidence is sufficient for pilot verification, but not for clearing production automated access.

**Frozen P1-B classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = AUTOMATED_PILOT`

## `WSSRC-CB-003` — European Central Bank

Authoritative schedule:  
https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html

Copyright/disclaimer:  
https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html

Robots policy checked operationally:  
https://www.ecb.europa.eu/robots.txt

Current factual findings:

- the ECB schedule currently publishes Governing Council monetary-policy meeting days, non-monetary meetings, General Council meetings and related press conferences through 2028;
- the surface therefore requires event-class filtering and must not treat every Governing Council entry as a monetary-policy occurrence;
- ECB copyright terms permit free use of information obtained directly from the website subject to accuracy/source citation and modification conditions, with authored-document exceptions;
- the current `robots.txt` publishes a general crawl delay of 5 seconds and does not disallow the monetary-policy calendar path, but that is an operational constraint rather than an express automation licence;
- the reviewed reuse terms do not expressly grant automated website retrieval.

**Frozen P1-B classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## `WSSRC-MAC-006` — Office for National Statistics

Authoritative release calendar:  
https://www.ons.gov.uk/releasecalendar

Terms and conditions:  
https://www.ons.gov.uk/help/terms-conditions

Fair-use / bot policy:  
https://www.ons.gov.uk/help/fair-use-policy

Developer release search:  
https://developer.ons.gov.uk/search/search-releases/

Current factual findings:

- the ONS release calendar exposes item-level `Confirmed`, `Provisional`, `Published` and `Cancelled` states and provides RSS, email-alert and add-to-calendar surfaces;
- most ONS content is under the Open Government Licence v3.0, subject to stated exceptions;
- ONS expressly addresses bots, crawlers and scrapers: automated users must follow technical guidance and identify themselves with an appropriate user-agent/contact, and ONS may restrict abusive/high-volume use;
- the official Developer Hub exposes a `GET /search/releases` route specifically for published/cancelled releases and upcoming Release Calendar Entries;
- the repository already records a fault-contained RSS-primary/calendar parser and successful controlled failure-injection validation.

This is the strongest current P1-B case for clearing automated monitoring **subject to the published technical/fair-use conditions**. `CLEARED` does not mean unbounded request volume and does not authorise canonical auto-commit.

**Frozen P1-B classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = CLEARED`
- `verification_mode = AUTOMATED_PILOT`

## `WSSRC-CB-007` — Reserve Bank of New Zealand

Authoritative schedule:  
https://www.rbnz.govt.nz/news-and-events/how-we-release-information/ocr-decision-dates-and-financial-stability-report-dates-to-feb-2028

Terms of use:  
https://www.rbnz.govt.nz/about-our-site/terms-of-use

Current factual findings:

- RBNZ publishes OCR/MPS and Financial Stability Report dates through February 2028;
- the current schedule explicitly records that a previously announced February 2027 decision was moved one week earlier, illustrating why snapshots/change history are required rather than treating the current page as a complete historical record;
- RBNZ permits reproduction/use of its own website material without specific permission when the Bank is acknowledged, the material is accurate/not misleading and third-party rights are respected;
- RBNZ expressly states that automated access such as robots, botnets or scrapers is **not allowed** except for public search engines under `robots.txt` or with RBNZ's prior written permission;
- even permitted bots are subject to stated maximum request allowances;
- WORLD SIGNALS has no recorded prior written RBNZ automation permission.

This is a clean example of canonical factual provenance remaining valid while the automated route is rights-held.

**Frozen P1-B classification:**

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

## Frozen classification table

| Source | Canonical provenance | Automated monitoring | Verification mode |
|---|---|---|---|
| `WSSRC-CB-001` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-006` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-CB-002` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-003` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-MAC-006` | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-007` | `CLEARED_CURATED_FACTUAL_METADATA` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |

## Held control — Brazil TSE

`WSSRC-EL-BR-001` remains excluded from P1-B. The provenance-scope defect identified in P1-A is unresolved: the electoral-calendar source is not the proper basis for the constitutionally grounded 5 January 2027 presidential inauguration. P1-B must not populate its modern governance fields or alter the canonical date.

## Transaction boundary

This research record authorises only a frozen **candidate plan** for review/testing. It does **not** authorise an apply transaction.

Any eventual P1-B transaction must:

- change exactly the six selected source records and source-registry version/reference metadata;
- preserve source count 223;
- leave canonical v0.20 / 669 byte-identical;
- leave monitor expectations v0.7 and monitor code unchanged;
- leave `WSSRC-EL-BR-001` byte-identical and governance-unbackfilled;
- preserve the Brazilian inauguration date `2027-01-05`;
- leave automatic canonical commit CLOSED;
- leave Google Calendar writes OFF;
- fail closed if any selected dependency count, source identity, governance field, or protected version has drifted before application.
