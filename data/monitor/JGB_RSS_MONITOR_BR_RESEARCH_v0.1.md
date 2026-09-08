# WORLD SIGNALS — BR Japan MOF JGB RSS monitor research

Reference date: 2026-09-08

## Question

Can the existing Japan Ministry of Finance JGB Canonical schedule scope be given a production Source/Change Monitor route without converting content-reuse permission, public reachability or a successful HTML fetch into blanket automated calendar-polling permission?

## Existing Canonical authority

`WSSRC-FIS-007` remains the authoritative forward-schedule source for `WSER-FIS-JP-JGB`. It has ten Canonical dependencies, all source-native `Asia/Tokyo` civil dates with `DAY` precision. The monthly calendar explicitly warns that dates may be changed or added.

BI already supplied a fail-closed monthly HTML parser and live parser evidence, but deliberately left `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED` and `automated_retrieval_permission = PENDING_ENDPOINT_OPERATIONAL_REVIEW`.

BR does not weaken that hold.

## HTML operational probe

The first BR read-only diagnostic (`34207802533`, job `102001350983`) verified the exact post-BQ governed state and then attempted the conventional MOF crawler-policy path before any monthly calendar polling.

`https://www.mof.go.jp/robots.txt` returned HTTP 404 from the GitHub runner.

WORLD SIGNALS interpretation: absence of a conventional robots file is neither permission nor prohibition. The HTML auction-calendar endpoint therefore remains held for production automation. No calendar HTML was polled after that gate failed.

## Separate first-party machine interface

MOF publishes an official RSS service at:

`https://www.mof.go.jp/english/news.rss`

Its first-party RSS documentation is:

`https://www.mof.go.jp/english/about_mof/rss/index.html`

The documentation expressly describes subscription through RSS-reader / aggregator software. This is a materially different operational interface from the held auction-calendar HTML pages.

The existing MOF content notice remains:

`https://www.mof.go.jp/english/about_mof/notice/index.html`

It identifies Japan's Public Data License v1.0 for general website content subject to stated exclusions. BR keeps content reuse and endpoint-operation evidence separate: PDL evidence does not clear the HTML calendar, while the explicit RSS software interface supports bounded retrieval of the RSS itself.

## Successful RSS diagnostic

Read-only run `34208070604`, job `102002229051` passed end-to-end and left the repository byte-clean.

Observed:

- RSS documentation: HTTP 200;
- RSS feed: HTTP 200;
- RSS Content-Type: `application/rss+xml; charset=UTF-8`;
- rights page: HTTP 200;
- 100 items in the rolling RSS feed;
- 73 items classified broadly as JGB-related during the diagnostic;
- 16 issuance-announcement items;
- 35 auction-result items;
- no calendar-alteration item in the current 100-item window.

The absence of a calendar-alteration item has no semantic meaning because the feed is finite and rolling.

A live current example in the feed is the standard result:

`Auction Result of 5-Year JGBs on September 8, 2026`

with RSS publication timestamp `Tue, 08 Sep 2026 12:35:00 +0900`.

A separate special-participant result for the same auction is also published later. BR treats that second item as corroboration only to avoid duplicate completion propositions.

## Source-role decision

BR creates a separate machine-interface identity, `WSSRC-FIS-029`, for the official MOF RSS.

It does **not** promote `WSSRC-FIS-007` to automated HTML polling.

Roles remain:

- `WSSRC-FIS-007` — Canonical forward schedule authority; HTML automation hold remains;
- `WSSRC-FIS-029` — official RSS publication/change sentinel; zero Canonical dependencies.

The RSS route is one request per daily run and performs no follow-up HTML fetch automatically.

## Review semantics

### Standard auction result

A title of the form `Auction Result of N-Year JGBs on Month D, YYYY` may be matched to the explicit ten-occurrence allow-list by tenor plus the auction date stated in the title.

For a non-completed Canonical occurrence, positive publication evidence creates a review candidate. It does not itself set `COMPLETED`.

For an already manually completed occurrence, the same feed evidence is observation-only.

### Special-participant result

A result suffixed `(For JGB Market Special Participants)` is corroboration-only and cannot create a second lifecycle proposition for the same auction.

### Issuance announcement

`Announcement of N-year JGBs to Be Issued in Month YYYY` is observation-only. The title establishes tenor and reference month, not the auction civil date, so it cannot change the Canonical schedule.

### Calendar-change notice

If a future RSS item explicitly identifies a calendar alteration/change/revision, the route may create a review candidate requiring manual recheck of `WSSRC-FIS-007`. The monitor itself does not fetch the held HTML calendar.

### Feed absence

Absence has no schedule, lifecycle or certainty semantics. The feed is rolling and is not forward schedule authority.

## Time discipline

RSS `pubDate` is the publication timestamp of the MOF feed item. It is not the auction event time.

BR therefore cannot use RSS publication timestamps to create or upgrade a Canonical auction clock. The tracked JGB occurrences remain civil-date events in `Asia/Tokyo` unless a separately authoritative event-time source is reviewed later.

## Scope and non-goals

BR does not:

- add JGB occurrences;
- infer completion from elapsed time;
- automatically complete an auction from a result item;
- change certainty from an announcement or result;
- poll the held HTML calendar;
- infer that no calendar change occurred because no change notice is currently present;
- promote the RSS into Canonical schedule provenance;
- mutate Live Intelligence or Analysis populations;
- touch the quarantined OPEC path.

The intended governed result is Sources `v1.91 / 249` and Monitor expectations `v0.16 / 14`, with Canonical remaining `v0.41 / 689` and all write gates closed.
