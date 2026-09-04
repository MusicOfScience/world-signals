# WORLD SIGNALS — P1-F source-governance research v0.1

**Research date:** 2026-09-04  
**Base checkpoint:** `bd348a18d0b67d2b973ec7b61d0e8ede2e35cb9d`  
**Source registry:** v1.57 / 223  
**Canonical registry:** v0.20 / 669  
**Monitor expectations:** v0.7

## Selection method

P1-F is a bounded six-source tranche selected from the measured post-P1-E P1 queue using canonical dependency, active horizon, source-scope integrity, regional breadth, domain diversity and governance-information value. It deliberately does **not** take the next six highest dependency counts: doing so would over-concentrate the tranche in Japanese and Australian macroeconomic series.

`WSSRC-CB-009` Swiss National Bank remains excluded despite its 18 canonical dependencies because the registered decisions/history URL does not directly support the forward assessment schedule. `WSSRC-EL-BR-001` Brazil TSE remains excluded pending provenance-scope repair.

Selected cohort:

| Source | Institution / surface | Dependencies | Jurisdiction / scope |
|---|---|---:|---|
| `WSSRC-MAC-014` | Statistics Bureau of Japan CPI release schedule | 7 | Japan |
| `WSSRC-MAC-012` | Australian Bureau of Statistics Labour Force release surface | 6 | Australia |
| `WSSRC-MKT-010` | CME Group E-mini S&P 500 quarterly expiry rule | 6 | United States / global markets |
| `WSSRC-COM-002` | International Energy Agency Oil Market Report schedule | 4 | Global |
| `WSSRC-CN-012` | ChinaMoney / National Interbank Funding Center LPR rule | 4 | China |
| `WSSRC-EL-NG-001` | Independent National Electoral Commission revised 2027 election timetable | 2 | Nigeria |

Total bounded dependency coverage: **29 canonical dependencies**.

The cohort intentionally contains both positive and negative governance controls: two existing parser/pilot sources, three surfaces whose current rights/access terms prohibit or materially constrain production automation, and one authoritative electoral source that remains manual because its revision endpoint is operationally fragile.

## Source-specific findings

### `WSSRC-MAC-014` — Statistics Bureau of Japan CPI

Authoritative release schedule: `https://www.stat.go.jp/english/data/cpi/1582.html`  
Separate official publication-time rule: `https://www.stat.go.jp/english/data/cpi/1585.htm`  
Rights evidence: `https://www.stat.go.jp/english/info/riyou.html`

The official CPI schedule, last updated 23 January 2026, publishes national and Tokyo CPI release dates through March 2027. The schedule itself is date-based. A separate Statistics Bureau CPI Q&A states that Japan prior-month CPI and Tokyo preliminary CPI are released at **08:30 Japan time** under their respective recurring weekday rules. WORLD SIGNALS must preserve this provenance relationship: the schedule supplies the date while the separate official rule supplies the clock time; the time must not be attributed to the schedule page itself.

Statistics Bureau material is generally available under Public Data License 1.0 and may be used, copied, publicly transmitted, translated or modified subject to the licence conditions. Those content-use terms do not themselves establish production crawler frequency or request behaviour. Existing `jp-stat-cpi-0.1` parser/pilot evidence supports bounded automated verification only, with reviewed canonical commits.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

### `WSSRC-MAC-012` — Australian Bureau of Statistics Labour Force

Authoritative product page: `https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia`  
Monitoring route: `https://www.abs.gov.au/release-calendar/future-releases`  
Rights evidence: `https://www.abs.gov.au/website-privacy-copyright-and-disclaimer`

The current product page publishes Labour Force reference periods and future release datetimes. At the review date it lists, among others, **24 September 2026 11:30 AEST** and **15 October 2026 11:30 AEDT**. The release calendar states that dates may change and that displayed times are Canberra time. WORLD SIGNALS must therefore retain the source's `Australia/Sydney` timezone and derive the correct UTC offset from the actual occurrence date; it must not hard-code AEST, AEDT or Melbourne time.

ABS states that general website material is CC BY 4.0 subject to listed exclusions. This clears curated factual reuse, not unrestricted polling. Existing `abs-release-calendar-0.1` pilot evidence supports bounded automated verification with reviewed commits only.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

### `WSSRC-MKT-010` — CME Group E-mini S&P 500 quarterly futures expiry rule

Authoritative rule surface: `https://www.cmegroup.com/trading/equity-index/eminifaq.html`  
Website/data terms: `https://www.cmegroup.com/tools-information/cme-website-terms-of-use.html`  
Current CME reminder on automated access: `https://www.cmegroup.com/notices/stp/2024/01/20240104.html`

CME's E-mini FAQ states that quarterly E-mini S&P 500 futures trading can occur up to **08:30 Chicago time on the third Friday** of the contract month. This is a standing contract-rule fact, not a market-price feed. WORLD SIGNALS may use the page as a manual authoritative reference for the rule and derive future occurrences only while that rule remains current.

CME's published website/data terms are materially restrictive. CME states that website content is owned or licensed, limits ordinary website use, and expressly prohibits data mining and automated navigation/access/retrieval using scripts, spiders, robots, crawlers or similar mechanisms absent permission. The project therefore does not treat the public FAQ as a production monitoring endpoint. Proprietary price/market data remain entirely out of scope for this source.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-COM-002` — International Energy Agency Oil Market Report

Authoritative product/schedule: `https://www.iea.org/data-and-statistics/data-product/oil-market-report-omr`  
Rights evidence: `https://www.iea.org/terms`

The current OMR product page publishes the 2026 monthly schedule and states that the report is released at **10:00 Paris time**; at the review date the next release is 11 September 2026. These schedule facts are useful contextual metadata, but the Oil Market Report is a licensed product.

IEA's current Terms explicitly exclude the **Oil Market Report** from its general CC BY 4.0 Open Use Terms, and the OMR product page identifies `Terms of Use for Non-CC Material`. WORLD SIGNALS must therefore keep the public schedule as a manual informational reference and must not scrape, ingest or redistribute OMR content/data through the general website route unless an appropriate licensed/authorised route is established.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-CN-012` — ChinaMoney / National Interbank Funding Center LPR

Authoritative rule surface: `https://www.chinamoney.com.cn/chinese/bklpr/`  
Legal statement: `https://www.chinamoney.org.cn/chinese/legaldeclaration/`

The current LPR page states that quote banks submit before **09:00 on the 20th of each month**, with postponement when the 20th falls on a holiday, and that the National Interbank Funding Center publishes LPR at **09:00 that day**. This is a recurring rule, not a guarantee that every occurrence lands on the civil 20th. If the rule or publication time changes, future derived occurrences must be recalculated while retaining stable occurrence identity and change history.

ChinaMoney's legal statement says the site's content and related intellectual property belong to CFETS/NIFC unless otherwise provided, and states that without written authorisation institutions or individuals may not reproduce, copy, distribute, modify, publish, transmit or obtain website content through hard-copy or **electronic retrieval/scraping systems**. That current source-specific statement overrides any temptation to infer automation permission from the official/public nature of the LPR page.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-EL-NG-001` — Independent National Electoral Commission, Nigeria

Current-state authority: `https://www.inecnigeria.org/upcoming-elections/`  
Registered revision identity: `https://www.inecnigeria.org/revised-timetable-and-schedule-of-activities-for-the-2027-general-elections-and-rescheduling-of-osun-state-governorship-election/`

INEC's current `upcoming-elections` surface lists the **Presidential/House of Assembly election for 16 January 2027** and the **Governorship/State House of Assembly election for 6 February 2027**. The registry already records a source-surface hierarchy because the detailed revised-timetable announcement body is fragile in the present research path. The current-state election list therefore controls operative dates; the revision announcement preserves competent revision identity; the earlier February 2026 formal announcement remains superseded historical evidence only.

Current review did not establish a general INEC licence or production bot policy sufficient to clear automated retrieval. Existing source-specific research has, however, already cleared public official electoral facts for curated provenance. The combination of a fragile revision endpoint and unresolved automated-access terms requires manual authoritative recheck rather than an automated pilot.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

## Held-source controls

P1-F must leave both held records byte-identical and must not add modern governance fields to them:

- `WSSRC-EL-BR-001` — Brazil TSE; preserve the canonical `2027-01-05` presidential inauguration as constitutionally grounded.
- `WSSRC-CB-009` — Swiss National Bank; preserve the registered decisions/history URL until the forward-schedule provenance relationship is repaired.

## Transaction boundary

This research freezes a **candidate governance plan only**. It does not authorise a source-registry write by itself.

Any P1-F transaction must:

1. start from canonical v0.20 / 669, source v1.57 / 223 and monitor expectations v0.7;
2. change exactly the six selected source records and the source-registry version only;
3. advance source registry to v1.58 / 223;
4. preserve every non-P1-F source field;
5. preserve Brazil/TSE and SNB holds byte-identically;
6. preserve canonical and monitor files byte-identically;
7. leave automatic canonical commit false and Google Calendar writes false;
8. default to read-only simulation and require a separate explicit environment gate for apply.
