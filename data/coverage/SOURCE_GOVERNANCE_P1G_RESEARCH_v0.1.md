# WORLD SIGNALS — P1-G source-governance research v0.1

**Research date:** 2026-09-04  
**Base checkpoint:** `21665ddce58cf9c7c7e868727ad4c2e19e6dce62`  
**Source registry:** v1.58 / 223  
**Canonical registry:** v0.20 / 669  
**Monitor expectations:** v0.7

## Selection method

P1-G is a bounded six-source tranche selected from the measured post-P1-F P1 queue using canonical dependency, active horizon, source-scope integrity, regional breadth, domain diversity and governance-information value. It is not a mechanical top-N pass.

`WSSRC-CB-009` Swiss National Bank remains excluded despite 18 canonical dependencies because the registered decisions/history URL does not directly support the forward assessment schedule. `WSSRC-EL-BR-001` Brazil TSE also remains excluded pending provenance-scope repair.

Selected cohort:

| Source | Institution / surface | Dependencies | Jurisdiction / scope |
|---|---|---:|---|
| `WSSRC-MAC-015` | Statistics Bureau of Japan Labour Force Survey schedule | 7 | Japan |
| `WSSRC-MKT-011` | ASX SPI 200 futures contract specification / expiry rule | 6 | Australia |
| `WSSRC-FIS-008` | Bank of Canada / Department of Finance Canada bond-auction schedule | 5 | Canada |
| `WSSRC-COM-012` | JODI / International Energy Forum Oil + Gas World Database update schedule | 4 | Global |
| `WSSRC-INT-029` | WTO General Council reform-workplan checkpoints | 3 | Global |
| `WSSRC-REGJ-001` | State Bank of Pakistan FY27 MPC advance calendar | 3 | Pakistan |

Total bounded dependency coverage: **28 canonical dependencies**.

## Source-scope audit

A dedicated read-only canonical dependency extraction was run before classifications were frozen. It confirmed that the registered sources support the precision actually stored in canonical records:

- Japan Labour Force Survey occurrences are confirmed **date-only** releases; no clock time is admitted because the audited English schedule does not publish one.
- Canada bond-auction schedule rows remain **provisional**. A bidding deadline is retained only where the source explicitly exposes it; other schedule rows remain date-only.
- ASX SPI 200 quarterly expiries are rule-derived market-structure events, not predictive signals. The official ASX 24 specification states that trading in expiring SPI 200 contracts ceases at **12.00pm on the third Thursday of the settlement month**, with Australian Eastern Standard/Daylight Time applying as appropriate.
- JODI’s official combined 2026 Oil + Gas schedule states that the first monthly World Database updates occur at **noon London time** and that supplementary updates can follow. WORLD SIGNALS therefore models the first combined monthly update as the canonical occurrence, not every supplementary load.
- WTO December 2026 and February 2027 reform checkpoints are stored as **provisional month-level expected windows**, while the 2027 mid-term ministerial review remains **year-level TBC/unscheduled**. No exact date has been manufactured.
- SBP’s FY27 advance calendar confirms remaining 2026 MPC meeting / Monetary Policy Statement dates on **14 September, 26 October and 14 December 2026**. They remain date-only; no announcement clock time is inferred.

## Source-specific findings

### `WSSRC-MAC-015` — Statistics Bureau of Japan Labour Force Survey

Authoritative schedule: `https://www.stat.go.jp/english/data/roudou/1543.html`  
Results surface: `https://www.stat.go.jp/english/data/roudou/result.html`  
Rights basis: Statistics Bureau / Government of Japan Public Data License 1.0.

The official release schedule supplies the seven canonical publication dates currently in horizon. The audited English endpoint does not state a release clock time, so canonical precision must remain civil-date / source-time-unspecified.

Government of Japan Public Data License 1.0 supports copying, public transmission, adaptation and commercial reuse with required source attribution and stated exceptions. It does not independently grant unrestricted production crawling. WORLD SIGNALS already has a validated basic schedule parser and pilot evidence, so bounded automated verification is justified while production endpoint behaviour still requires review.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

### `WSSRC-MKT-011` — ASX SPI 200 futures expiry rule

Authoritative specification: `https://www2.asx.com.au/content/dam/asx/participants/derivatives-market/ird/asx24-contract-specifications.pdf`  
Website terms: ASX Terms of Use / Conditions of Use.

The current ASX 24 Contract Specifications state that all trading in expiring SPI 200 contracts ceases at 12.00pm on the third Thursday of the settlement month and identify trading-hour times as Australian Eastern Standard Time / Australian Eastern Daylight Time. This directly supports the existing Australia/Sydney rule-derived canonical occurrences.

ASX website terms explicitly prohibit spiders, screen scrapers, robots or similar automated processes from accessing, monitoring, downloading or copying website content except where permitted or with prior written consent; they also restrict unauthorised manual monitoring/copying. Official/public availability therefore cannot be treated as automation permission. The source remains a bounded authoritative informational reference under a rights hold, not a systematic monitoring endpoint.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-FIS-008` — Bank of Canada / Department of Finance Canada bond auctions

Authoritative schedule: `https://www.bankofcanada.ca/markets/government-securities-auctions/calls-for-tenders-and-results/bond-auction-schedule/`  
Rights / operational terms: `https://www.bankofcanada.ca/terms/`

The official schedule exposes Government of Canada bond-auction information and structured CSV/JSON/XML access; the Bank’s Valet ecosystem provides a machine-oriented data context. The schedule itself states that details are subject to change. Canonical rows correctly preserve provisional status and retain an exact bidding deadline only where explicitly provided.

Bank of Canada content/data reuse is permitted subject to attribution and stated conditions. Its terms prohibit circumvention of request-frequency limits and overburdening the service. This is consistent with the earlier P1-C treatment of the Bank’s monetary-policy schedule: existing parser/pilot evidence supports automated-pilot verification, while endpoint-specific production review remains mandatory rather than treating the API’s existence as unrestricted polling permission.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

### `WSSRC-COM-012` — JODI Oil + Gas World Database update schedule

Authoritative schedule: `https://www.jodidata.org/oil/support/update-calendar.aspx`  
Combined 2026 schedule: `https://www.jodidata.org/_resources/files/downloads/jodi-update-schedule-2026.pdf?v=dates-for-2026`  
Terms: `https://www.jodidata.org/terms-of-use.aspx`

JODI’s current site and combined 2026 schedule state that publication occurs at **noon London time**. The combined schedule explicitly describes these as the first JODI-Oil and JODI-Gas World Database updates of each month and notes that supplementary updates may follow. The existing canonical bundle semantics are therefore sound.

JODI terms reserve intellectual-property rights and the existing registry correctly treats this route as permission/restriction sensitive. No production automation entitlement is inferred from the public calendar or downloadability of the schedule.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-INT-029` — World Trade Organization reform checkpoints

Authoritative workplan/news surface: `https://www.wto.org/english/news_e/news26_e/gc_26jun26_432_e.htm`  
Copyright / permissions: `https://www.wto.org/english/info_e/copyrights_permissions_e.htm`

The WTO source supports a December 2026 General Council reform checkpoint, a February 2027 checkpoint and a 2027 mid-term ministerial review, but it does not provide exact dates for those future events. Canonical modelling already preserves that limitation as month-level provisional windows and year-level TBC where appropriate.

The WTO encourages broad dissemination; unrestricted official WTO documents/legal texts are free for public use, while other website/publication material is subject to non-commercial attribution/notification or commercial permission requirements. The factual institutional timing metadata can be curated as provenance, but the news/web route supplies no express unrestricted automated-access licence. Exact future dates must be verified from later authoritative calendar/convening notices before any occurrence precision is upgraded.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

### `WSSRC-REGJ-001` — State Bank of Pakistan FY27 MPC calendar

Authoritative surface: `https://www.sbp.org.pk/our-operations/monetary-policy`  
Fallback official surface: `https://www.sbp.org.pk/m_policy/About.asp`

The current official monetary-policy page publishes an **Advance Calendar of Monetary Policy Committee Meetings & Communications** for FY27. It confirms MPC Meeting / Monetary Policy Statement dates of 14 September, 26 October and 14 December 2026, and provides subsequent FY27 dates into June 2027. The schedule also states that unforeseen events can cause a meeting date to be changed and communicated later.

The main SBP website currently carries an “All Rights Reserved” copyright notice, and no permissive general website reuse or automated-access licence was located in the reviewed official material. The modern route has also shown intermittent 403 access in tooling. WORLD SIGNALS may retain the already-verified factual dates as an authoritative informational reference, but systematic automated monitoring remains rights-held absent clearer permission.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

## Held-source controls

P1-G must leave both standing held records byte-identical and must not add modern governance fields to them:

- `WSSRC-EL-BR-001` — Brazil TSE; preserve the canonical `2027-01-05` presidential inauguration as constitutionally grounded.
- `WSSRC-CB-009` — Swiss National Bank; preserve the registered decisions/history URL until the forward-schedule provenance relationship is repaired.

## Transaction boundary

This research freezes a **candidate governance plan only**. It does not authorise a source-registry write by itself.

Any P1-G transaction must:

1. start from canonical v0.20 / 669, source v1.58 / 223 and monitor expectations v0.7;
2. change exactly the six selected source records and the source-registry version only;
3. advance source registry to v1.59 / 223;
4. preserve every non-P1-G source field;
5. preserve Brazil/TSE and SNB holds byte-identically;
6. preserve canonical and monitor files byte-identically;
7. leave automatic canonical commit false and Google Calendar writes false;
8. default to read-only simulation and require a separate explicit environment gate for apply.
