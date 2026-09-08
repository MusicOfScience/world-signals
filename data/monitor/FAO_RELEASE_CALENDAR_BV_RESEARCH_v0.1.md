# BV — FAO 2026 data-release calendar monitor research

Reference date: 2026-09-08
Exact post-BU main: `525d44f0e83c58efd6308900740c5677d962a9f4`

## Selection rationale

The post-BU pressure audit found Cross-regional / Global coverage structurally thin: 108 Canonical occurrences are represented by one configured production route and 16 unique monitored occurrences. This is evidence of a monitoring gap, not a quota.

`WSSRC-COM-010` is a materially different candidate from another central-bank route. It is the existing Canonical schedule source for global food/agriculture releases, including the FAO Food Price Index (FFPI) and Agricultural Market Information System (AMIS) Market Monitor. These signals connect agricultural commodities, inflation, food security, trade, logistics and climate-sensitive supply conditions.

BV selects only six already-existing future Canonical occurrences:

- `WSO-COM-A-0042` — FAO Food Price Index — October 2026 — 2026-10-02
- `WSO-COM-A-0043` — AMIS Market Monitor — October 2026 — 2026-10-02
- `WSO-COM-A-0044` — FAO Food Price Index — November 2026 — 2026-11-06
- `WSO-COM-A-0045` — AMIS Market Monitor — November 2026 — 2026-11-06
- `WSO-COM-A-0046` — FAO Food Price Index — December 2026 — 2026-12-04
- `WSO-COM-A-0047` — AMIS Market Monitor — December 2026 — 2026-12-04

The September pair (`WSO-COM-A-0040`, `0041`) is past at the BV reference date and is not placed in the live route. `WSO-COM-A-0048` (Food Outlook) is a month-level expected window rather than an exact-day release and is deliberately excluded.

## Existing source governance

`WSSRC-COM-010` already exists and has nine Canonical dependencies. Its source identity is not duplicated for monitoring because the Canonical authority and the proposed monitor inspect the same first-party FAO schedule page:

`https://www.fao.org/statistics/data-releases/upcoming-data-releases/`

The earlier P1-A governance review correctly distinguished FAO general website content from the separate FAOSTAT/statistical-database licensing regime. BV preserves that distinction. No CC-BY database licence is projected onto the HTML release-calendar page.

Existing content/reuse classification remains factual-metadata only. BV changes only automation/readiness metadata after separate endpoint review.

## Current authoritative schedule evidence

FAO's official 2026 Calendar of Data Releases currently lists:

- October 2026: FFPI and Commodity Price Indices — 2 October; AMIS Market Monitor — 2 October.
- November 2026: FFPI and Commodity Price Indices — 6 November; AMIS Market Monitor — 6 November.
- December 2026: FFPI and Commodity Price Indices — 4 December; AMIS Market Monitor — 4 December.

The dedicated FAO Food Price Index page independently publishes the 2026 monthly FFPI release sequence, including 2 October, 6 November and 4 December. This is corroboration only; BV does not add an automatic follow-up request to that page.

## Rights and automation are separate

Primary FAO terms:

`https://www.fao.org/contact-us/terms/`

FAO states that it encourages the use, reproduction and dissemination of text, multimedia and data; general website content may be copied/downloaded for private study, research and teaching and for non-commercial products/services with appropriate attribution, except where otherwise indicated. Statistical databases have their own separate terms.

BV therefore preserves the existing restricted factual-metadata reuse classification and does not infer broad redistribution rights.

Automation is reviewed separately:

`https://www.fao.org/robots.txt`

The current robots file is a valid `text/plain` robots policy. It contains specific disallow rules but no disallow for `/statistics/data-releases/upcoming-data-releases/`.

FAO also launched an official FAOSTAT API developer portal in 2026 expressly supporting automated extraction and reproducible workflows. This is contextual evidence that automation is not institutionally prohibited; it is not treated as permission for arbitrary FAO website crawling and is not used as the release-calendar endpoint.

## Production-shaped endpoint diagnostic

Read-only GitHub Actions diagnostic:

- run: `34234241294`
- job: `102087743209`
- repository permission: contents read only
- request count: exactly 2
  - one `https://www.fao.org/robots.txt` request
  - one exact FAO release-calendar request
- robots: HTTP 200, `text/plain`, 1056 bytes, valid `User-agent` syntax, schedule path allowed
- calendar: HTTP 200, `text/html; charset=utf-8`, 64232 bytes, valid FAO calendar body
- no WAF/rejection masquerading as HTTP 200
- six configured Canonical dates matched six official visible schedule dates
- no release clock is exposed
- no follow-up requests
- no repository mutation

This diagnostic deliberately includes the HTTP-200/body-validity hardening learned from the CBE BV investigation: status 200 alone is not accepted as endpoint health.

## CBE comparison / rejected alternative

CBE was investigated first because its content reuse terms are comparatively clear. Its production-shaped runner returned 269-byte `Request Rejected` WAF HTML for both `robots.txt` and the schedule URL despite HTTP 200. That makes CBE endpoint-held; the invalid robots body must not be interpreted as an allow policy. No separate official RSS/API fallback was established.

Bank Indonesia and Bank Negara Malaysia remain rights-held. India MoSPI remains parser/endpoint-held. BV does not activate a held institution for geographic balance.

## Frozen BV monitor contract

The FAO monitor will:

- use the existing source identity `WSSRC-COM-010`;
- request robots first on every run;
- stop before the calendar request if a valid current robots policy disallows it;
- fetch exactly one official FAO schedule page if allowed;
- validate resolved official HTTPS host, content type, minimum body structure and rejection/WAF signatures;
- parse only FFPI and AMIS rows inside the configured October, November and December 2026 month sections;
- map each configured product/month slot to exactly one stable Canonical occurrence identity;
- generate review candidates for official date changes or a missing configured row;
- treat structural/parser/source failure as source health only;
- preserve date-only semantics; there is no clock to promote;
- never follow FAO, AMIS, FAOSTAT, PDF, news or other links automatically;
- never infer `COMPLETED`, cancellation, certainty change or lifecycle state from presence/absence;
- never write Canonical or Google Calendar;
- never automatically promote evidence to Live Intelligence or Analysis.

Maximum request budget per run: 2.

This is an operational governance classification for WORLD SIGNALS, not legal advice.
