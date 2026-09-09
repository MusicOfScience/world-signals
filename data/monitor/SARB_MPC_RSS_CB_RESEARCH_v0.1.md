# WORLD SIGNALS — CB research note: SARB MPC statement RSS

**Reference date:** 2026-09-09  
**Exact base:** `1f20c9afbf7d9e295024ce534b3191155d9f674b` (post-CA main)

## Pressure audit

CB was selected by source readiness rather than regional quota. India MoSPI remains held because its current dynamic release-calendar surface and official advance-release-calendar PDF do not provide one internally consistent production route. RBI has an expressly published press-release RSS interface, but WORLD SIGNALS models its remaining 2026 Canonical objects as multi-day MPC meeting windows rather than separate decision-publication occurrences. Banco Central do Brasil likewise has official Copom statement RSS, while the existing Canonical scope is three multi-day Copom meeting processes. Those are useful future architecture candidates but are not clean publication-to-occurrence matches.

The South African Reserve Bank is cleaner. Existing Canonical source `WSSRC-REG-006` supplies two exact public MPC announcement occurrences: 23 September 2026 at 15:00 and 19 November 2026 at 15:00, `Africa/Johannesburg`. Its general website rights classification remains held and is not changed by CB.

SARB separately publishes an RSS subscription page which expressly describes RSS as a way to receive latest SARB content and links the machine endpoint `https://www.resbank.co.za/bin/sarb/solr/publications/rss`. That is a distinct source role, not a clearance of the held schedule/webcast page.

## Read-only diagnostics

Successful source/Canonical/feed contract diagnostic:

- run `34311819558`
- job `102339870513`
- Canonical v0.41 / 689
- Sources v2.00 / 255
- Monitor v0.25 / 23
- `WSSRC-REG-013` confirmed unused
- no existing SARB machine source or monitor route
- exactly two SARB Canonical dependencies: `WSO-REG-A-0009`, `WSO-REG-A-0010`
- RSS HTTP 200
- content type `application/xml;charset=utf-8`
- 25 rolling items
- item field contract: `title`, `link`, `description`, `pubDate`, `category`, `guid`
- repository byte-clean

The current 25-item rolling window contained no MPC statement. CB therefore does not claim that a live target item was observed. First-party SARB historical/current publication pages independently establish the stable statement-title family `Statement of the Monetary Policy Committee <Month> <Year>` and publication path family under `/statements/monetary-policy-statements/<year>/<month>`.

## Architecture

CB creates a separate monitor-only source `WSSRC-REG-013` for the expressly published RSS interface. `WSSRC-REG-006` remains byte-identical Canonical schedule/clock authority.

The monitor:

1. makes exactly one request to the official RSS endpoint;
2. parses the six-field RSS item contract and fails closed on structural drift;
3. ignores ordinary non-MPC publications;
4. treats any item mentioning the Monetary Policy Committee but failing the exact title/path/category contract as source-structure drift;
5. maps only September 2026 and November 2026 statement identities to the two existing stable occurrence IDs;
6. converts `pubDate` to `Africa/Johannesburg` only to compare the observed publication civil date with the configured Canonical date;
7. never treats RSS `pubDate` as Canonical clock authority;
8. never fetches the linked statement page, PDF, webcast page, search results or any other follow-up;
9. creates review candidates only; no automatic lifecycle, certainty, schedule, clock, Canonical, Live Intelligence or Analysis mutation is permitted;
10. gives feed absence no cancellation, delay, completion or certainty meaning.

A target statement published on a different civil date remains mapped by exact year/month statement identity but generates a publication-date-mismatch review candidate rather than silently moving Canonical.

## Rights and machine access

SARB's general disclaimer remains restrictive. CB does not assert a broad reproduction or redistribution right for website content and does not change `WSSRC-REG-006`.

The narrower machine-access finding is that SARB itself publishes an RSS subscription page and directs users to its RSS feed. `WSSRC-REG-013` therefore records permission only for bounded internal monitoring of minimal feed metadata through that supplied machine interface. This does not imply permission to crawl the held schedule source or republish article/PDF content.

## Governed target

- Canonical Registry: v0.41 / 689 unchanged
- Sources: v2.00 / 255 → v2.01 / 256
- Monitor expectations: v0.25 / 23 → v0.26 / 24
- automatic Canonical commit OFF
- Google Calendar write OFF
- all other project layers unchanged
