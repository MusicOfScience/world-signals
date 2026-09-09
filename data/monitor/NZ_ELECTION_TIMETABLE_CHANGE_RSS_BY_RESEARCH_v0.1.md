# WORLD SIGNALS — BY New Zealand election timetable RSS change-sentinel research v0.1

**Reference date:** 2026-09-09  
**Exact post-BX base:** `a3bca03f36eb5af9036017aad926f75f6762267f`

## Decision

BY selects the Electoral Commission New Zealand's advertised Media & News RSS interface as a **source-page update sentinel** for the already-modelled 2026 General Election timetable.

This is deliberately not an RSS-to-election-date parser.

The architecture keeps two source roles separate:

- `WSSRC-EL-NZ-001` remains the Canonical authority for the six 2026 election-timetable milestones and remains under its existing HTML endpoint/automation hold;
- proposed `WSSRC-EL-NZ-002` is a monitor-only RSS identity with zero Canonical dependencies;
- proposed route: `NZ_ELECTION_TIMETABLE_CHANGE_RSS`.

The RSS route watches only for the exact Canonical timetable page to appear in the Commission's rolling list of recently updated pages. If it appears, WORLD SIGNALS generates one **bundle review candidate** covering the six stable occurrence IDs. The monitor does not guess which milestone changed and does not fetch the timetable page automatically.

## Why this emerged after BX

The post-BX pressure audit (`34299113626` / `102302051974`) found no Canonical source that was both fully cleared and merely waiting for mechanical routing. It also showed that `ELECTIONS_GOVERNANCE` still had 28 Canonical occurrences and zero production monitoring.

BY therefore examined election-source architecture rather than simply promoting another high-dependency macro source. `WSSRC-EL-NZ-001` was attractive because:

- it has six confirmed forward Canonical dependencies;
- its factual Canonical use is already cleared;
- the Electoral Commission is the issuing electoral authority;
- its prior hold concerned HTML automation, not the truth of the timetable;
- the Commission separately advertises an RSS subscription route for Media & News.

This selection is not a regional quota. It opens a previously unmonitored event class with a source-role design that respects the existing HTML hold.

## Existing Canonical authority

Existing source: `WSSRC-EL-NZ-001`  
Institution: Electoral Commission New Zealand  
Authoritative timetable: `https://elections.nz/media-and-news/2026/key-dates-for-2026-general-election`

The six current Canonical occurrences are:

| Occurrence | Milestone | Canonical civil date |
|---|---|---|
| `WSO-EL-A-0005` | Parliament dissolution | 2026-10-01 |
| `WSO-EL-A-0006` | Writ day | 2026-10-04 |
| `WSO-EL-A-0007` | General Election | 2026-11-07 |
| `WSO-EL-A-0008` | Official results | 2026-11-27 |
| `WSO-EL-A-0009` | Return-of-writ deadline | 2026-12-03 |
| `WSO-EL-A-0010` | Last day for new Parliament to meet | 2027-01-14 |

All six are `CIVIL_DATE` / `DAY`, `Pacific/Auckland`, all-day, `PLANNED`, `CONFIRMED` at the frozen BY base.

Government formation remains outside this timetable and is not synthesized by BY.

## Historical P1-C governance truth

P1-C correctly classified `WSSRC-EL-NZ-001` on 2026-09-04 as:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

That historical classification remains true and the source object is not promoted or rewritten by BY.

The reason is important: P1-C did not identify a general website automation permission for the timetable HTML. BY does not retroactively infer one.

## Separate official RSS machine interface

The Electoral Commission's 2026 General Election media kit tells media users to subscribe to the RSS feed on `elections.nz/media-and-news` to receive notifications. The live Media & News HTML exposes one first-party feed:

`https://elections.nz/media-and-news/rss`

BY treats that invitation as evidence for use of the **specific RSS subscription interface only**. It is not a general crawler licence for the Commission website.

### Discovery diagnostic

Run `34299288416`, job `102302572476` — SUCCESS, repository-read-only.

Exactly two first-party requests were made:

1. `https://elections.nz/robots.txt`
2. `https://elections.nz/media-and-news`

Findings:

- robots: HTTP 200 `text/plain`;
- declared `Crawl-delay: 2`;
- Media & News path allowed;
- Media & News HTML: HTTP 200;
- one advertised feed discovered: `https://elections.nz/media-and-news/rss`;
- no feed, item or timetable follow-up was made in this discovery run.

### RSS endpoint diagnostic

Run `34299383044`, job `102302861060` — SUCCESS, repository-read-only.

The diagnostic respected the two-second crawl delay and made exactly two requests:

1. robots policy;
2. advertised RSS feed.

No item link was followed.

Live RSS result:

- HTTP 200;
- `application/rss+xml; charset=utf-8`;
- 6,523 bytes;
- SHA-256 `ec3dc5162f2ff4d01e699249c2fa606ea2a7c0c0082e0cb9d39cb77faacf056d`;
- strict well-formed RSS;
- channel title: `10 Most Recently Updated Pages`;
- channel description: `Shows a list of the 10 most recently updated pages.`;
- exactly 10 items;
- one stable item-field contract: `title`, `link`, `description`, `pubDate`, `guid`.

The live snapshot contained ordinary election news and campaign-administration pages but did not contain the Canonical timetable page.

## Why BY does not parse election news

The feed is a publication/update stream, not a structured election timetable. Its items include enrolment reminders, candidate nominations, regulated-period notices, accessibility material and other election administration news.

Trying to infer timetable changes from those titles or descriptions would introduce brittle semantic matching and false event-state claims.

BY therefore rejects these possible designs:

- fuzzy matching election-related prose to individual Canonical milestones;
- parsing dates from RSS descriptions into Canonical schedule changes;
- interpreting RSS `pubDate` as a milestone timestamp;
- treating the absence of a milestone page from a ten-item rolling feed as evidence that a milestone is delayed, cancelled, completed or uncertain;
- automatically fetching item pages, including the Canonical timetable page.

## Exact change-sentinel contract

Canonical timetable page identity:

`https://elections.nz/media-and-news/2026/key-dates-for-2026-general-election`

The permanent comparator may act only on an RSS item whose normalized `link` **and** `guid` both equal that exact first-party URL.

If the exact timetable page is present once:

- generate one `NZ_ELECTION_TIMETABLE_PAGE_UPDATED_REVIEW` candidate;
- attach the exact six stable Canonical occurrence IDs as one review bundle;
- include the RSS page-update metadata as source-change evidence;
- require manual authoritative recheck of the timetable page;
- do not infer which milestone changed;
- do not propose a replacement date;
- do not automatically fetch the timetable HTML;
- do not mutate Canonical, lifecycle, certainty or clock fields;
- do not automatically promote the item to Live Intelligence or Analysis.

If the exact timetable page is absent:

- generate a healthy sentinel observation only;
- record the rolling-window limitation;
- make no event-state inference.

If the exact timetable page appears more than once, or `guid` and `link` disagree, fail closed.

## Rolling-window limitation

The channel is explicitly the ten most recently updated pages. This monitor is therefore a **bounded change sentinel**, not an exhaustive audit trail.

A fast-moving election-news period could push a timetable-page update out of the feed before a later monitor run. The route must preserve this limitation in governance metadata. A suitable production cadence is frequent during the election period, but the monitor expectation describes cadence rather than creating a new scheduling subsystem.

Absence from a finite rolling feed is never evidence that the source page did not change.

## Rights and machine-access separation

`WSSRC-EL-NZ-001` retains its prior factual-metadata rights classification and HTML automation hold unchanged.

The proposed RSS machine source is narrower:

- machine access basis: Commission-advertised RSS subscription route plus live robots compatibility;
- request discipline: robots request, respect declared two-second crawl delay, one RSS request;
- content retained: minimal factual feed metadata needed to detect an exact source-page update;
- no article-body redistribution;
- no item/page follow-up;
- no inference that the RSS invitation grants arbitrary HTML crawling rights.

This is an operational governance classification for WORLD SIGNALS, not a legal opinion.

## Proposed request boundary

Per monitor run:

- robots requests: 1;
- minimum delay before RSS request: 2 seconds, or a greater live robots-declared delay;
- RSS requests: 1;
- timetable HTML requests: 0;
- item/article requests: 0;
- candidate/result-data requests: 0;
- search/discovery requests: 0;
- total external request budget: 2.

If robots becomes invalid or disallows the RSS endpoint, the route degrades to source-health evidence only and does not request the feed.

## Expected governed post-state

If BY activation passes all later gates:

- Canonical Registry: v0.41 / 689 — unchanged;
- Sources: v1.97 / 253 → v1.98 / 254;
- Monitor expectations: v0.22 / 20 → v0.23 / 21;
- Change Ledger: unchanged;
- Live Intelligence: unchanged;
- Analysis: unchanged;
- automatic Canonical commit: OFF;
- Google Calendar writes: OFF.
