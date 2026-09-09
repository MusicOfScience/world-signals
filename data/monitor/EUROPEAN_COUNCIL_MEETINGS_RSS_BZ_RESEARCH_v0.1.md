# WORLD SIGNALS — BZ European Council meetings RSS research v0.1

**Reference date:** 2026-09-09  
**Exact post-BY base:** `3ccb20539c10d0965de84efa298ba75634c19249`

## Decision

BZ selects the Council of the EU's dedicated **European Council meetings RSS feed** as a separate monitor-only machine interface for the three already-modelled forward European Council occurrences.

The architecture deliberately keeps source roles separate:

- `WSSRC-INT-003` remains the Canonical schedule authority and is not modified;
- its direct meeting-calendar HTML route remains under endpoint review;
- proposed `WSSRC-INT-035` is a monitor-only RSS source with zero Canonical dependencies;
- proposed route: `EUROPEAN_COUNCIL_MEETINGS_RSS`.

The RSS route is allowed to compare the meeting date/range encoded in a first-party RSS item link against the **current** Canonical date/range for the same configured GUID. It has no authority to write Canonical state.

## Why this emerged after BY

The post-BY source-aware pressure audit (`34303098682` / `102314052499`) showed that `INTERNATIONAL_INSTITUTIONS` had 38 Canonical occurrences and **zero configured production-monitor occurrences**. The audit also showed that the lowest-covered regions remained South Asia, Africa and Southeast Asia, but those gaps were not treated as quotas.

Several candidate routes remained materially blocked:

- India MoSPI: dynamic endpoint/parser conflict remains unresolved;
- Central Bank of Egypt: prior WAF/rejection failure remains a technical hold;
- Bank of Thailand and Bank Negara Malaysia: rights/automation holds remain material;
- WHO, UNFCCC, CBD and IPCC candidates remain rights-held;
- OPEC remains quarantined technical debt and was not retried.

BZ first tested Bangko Sentral ng Pilipinas because it offered two confirmed Southeast Asian monetary-policy occurrences and permissive factual reuse. That route was **not** promoted: its robots endpoint changed within minutes from a valid policy body to an HTML body, making the crawler-policy prerequisite operationally unstable. BZ therefore classified BSP as a technical/crawler-policy hold rather than repeatedly retrying until a favourable response appeared.

European Council monitoring was then examined because it opened a previously unmonitored event class and had a purpose-built machine interface distinct from the direct HTML calendar.

## Existing Canonical authority

Existing source: `WSSRC-INT-003`  
Institution: European Council / Council of the EU  
Canonical calendar: `https://www.consilium.europa.eu/en/meetings/calendar/`

The exact post-BY source object is already cleared for Council website reuse with attribution, while automated retrieval remains `PENDING_ENDPOINT_OPERATIONAL_REVIEW` and monitoring readiness remains `ENDPOINT_REVIEW_REQUIRED`.

The three Canonical dependencies are:

| Occurrence | Canonical name | Current date/range | Timing |
|---|---|---|---|
| `WSO-INT-B-0102` | European Council | 2026-10-15 → 2026-10-16 | `MULTI_DAY_LOCAL` / `DAY` |
| `WSO-INT-B-0103` | Informal meeting of EU heads of state or government | 2026-11-13 | `CIVIL_DATE` / `DAY` |
| `WSO-INT-B-0104` | European Council | 2026-12-17 → 2026-12-18 | `MULTI_DAY_LOCAL` / `DAY` |

All three are all-day, `Europe/Brussels`, `PLANNED`, `CONFIRMED`, `INSTITUTIONAL_MEETING`, category `INTERNATIONAL_INSTITUTIONS`, series `WSER-INT-EUCO` at the frozen BZ base.

The namespace inspection (`34304030657` / `102316864765`) also established that `WSSRC-INT-030` through `WSSRC-INT-034` are already occupied. The first unused international-source identity is `WSSRC-INT-035`.

## Direct calendar HTML remains held

BZ did **not** infer that the existing copyright/reuse permission grants unrestricted automated polling.

The bounded direct-route diagnostic (`34303557384` / `102315410273`) requested only:

`https://www.consilium.europa.eu/robots.txt`

That request returned HTTP 403. The diagnostic therefore made **zero** calendar-HTML requests and stopped fail-closed.

This is not a claim that the public calendar is inaccessible to humans. It means WORLD SIGNALS could not establish its crawler-policy prerequisite for direct HTML automation, so `WSSRC-INT-003` remains endpoint-held.

## Separate official RSS machine interface

Consilium separately publishes an RSS information page at:

`https://www.consilium.europa.eu/en/about-site/rss/`

The Council describes RSS as machine-readable material that can be loaded automatically onto computers or websites and advertises a dedicated **European Council meetings** feed:

`https://www.consilium.europa.eu/en/rss/meetings.ashx?cat=euco`

BZ treats that express RSS interface as machine-access evidence for the **RSS endpoint only**. It is not projected onto the blocked HTML calendar or item pages.

The Council copyright/reuse page remains the content-reuse evidence:

`https://www.consilium.europa.eu/en/about-site/copyright/`

The existing registry classification records that Council website content may be reproduced when the source is acknowledged, original meaning is not distorted and changes are indicated, subject to specific/third-party exceptions.

This is an operational WORLD SIGNALS governance classification, not legal advice.

## Live RSS diagnostics

### Initial one-request endpoint diagnostic

Run `34303674628`, job `102315763120` — **SUCCESS**, read-only.

Exactly one external request was made, to the dedicated European Council RSS endpoint. There were no robots, calendar-HTML, item-followup or search/discovery requests.

Live result:

- HTTP 200;
- `text/xml; charset=utf-8`;
- 19,201 bytes;
- SHA-256 `e66b98f10784ae653b83b306bc982824c6664c8593d2163f13d3b70c08b2422e`;
- strict RSS;
- channel title `Council of the EU`;
- 50 items in the observed snapshot.

The first three items were exactly the three forward Canonical meetings.

### Field-contract diagnostic

Run `34304095590`, job `102317059187` — **SUCCESS**, read-only.

The live channel child sequence consisted of `title`, `link`, `description`, `language`, then items. Every live item shared the exact child sequence:

`guid`, `link`, `title`, `description`, `updated`

There is no `pubDate` field in the live feed. The current forward items have empty `description` and empty `updated` values. BZ therefore does **not** manufacture publication-time semantics from those fields.

The current feed count of 50 is a snapshot fact, not a permanent parser invariant. The proposed parser uses a defensive non-empty bounded range rather than requiring exactly 50 items forever.

## Stable configured identity and date-bearing URL

The configured current identities are:

| RSS GUID | Canonical occurrence | Required title | Official meeting link | Observed date/range |
|---|---|---|---|---|
| `147805` | `WSO-INT-B-0102` | European Council | `/en/meetings/european-council/2026/10/15-16/` | 15–16 Oct |
| `147983` | `WSO-INT-B-0103` | Informal meeting of heads of state or government | `/en/meetings/european-council/2026/11/13/` | 13 Nov |
| `147844` | `WSO-INT-B-0104` | European Council | `/en/meetings/european-council/2026/12/17-18/` | 17–18 Dec |

The monitor uses:

- numeric RSS GUID as configured feed identity;
- exact HTTPS `www.consilium.europa.eu` meeting-link path as the only observed date/range source;
- title as an identity corroborator, not a Canonical-name mutation source.

A valid meeting path must be one of:

- `/en/meetings/european-council/YYYY/MM/DD/`
- `/en/meetings/european-council/YYYY/MM/DD-DD/`

The parser validates real civil dates. A two-day path is required to stay within the encoded month; BZ does not invent cross-month semantics absent evidence of such a feed shape.

## Comparator semantics

For each configured GUID:

### Exact current date/range

If the GUID is present exactly once, title matches the configured identity and the observed link date/range equals the **current Canonical** `start_local` / `end_local`, emit:

`EUROPEAN_COUNCIL_RSS_DATE_MATCH_OBSERVATION`

No review candidate is created.

### Same GUID, changed date/range

If the configured GUID is present exactly once but the date/range encoded in its official link differs from the current Canonical date/range, create:

`EUROPEAN_COUNCIL_RSS_DATE_CHANGE_REVIEW`

The review records old and observed values but does not mutate Canonical state. The comparison is against current Canonical values, not against BZ's frozen baseline dates, so a manually reviewed future descendant update will not be repeatedly rediscovered merely because it differs from the September checkpoint.

### Configured GUID missing

If a configured GUID is absent and its Canonical occurrence is not `COMPLETED`, create:

`EUROPEAN_COUNCIL_RSS_CONFIGURED_GUID_MISSING_REVIEW`

Absence is **not** interpreted as cancellation, completion, postponement or loss of certainty.

If the Canonical occurrence is already `COMPLETED`, absence produces corroborative/health observation only and no event-state claim.

### Unconfigured future meeting item

An unconfigured European Council feed item on or after the BZ review floor may be surfaced as:

`EUROPEAN_COUNCIL_RSS_UNCONFIGURED_FUTURE_MEETING_OBSERVATION`

It cannot create a Canonical occurrence automatically. This exists only to reveal that the institution may have added a future meeting outside the current three-occurrence allow-list.

Historical unconfigured feed items are not treated as candidate additions.

### Structural drift

Duplicate GUIDs, malformed XML, off-host links, invalid date paths, configured-GUID title drift or impossible dates fail closed as source-health evidence. They do not become guessed event changes.

## Why GUID is not overclaimed

The current RSS snapshot demonstrates that each configured meeting has a compact numeric GUID and a date-bearing link. It does **not** prove from historical rescheduling evidence that the GUID is guaranteed to remain unchanged through every possible meeting move.

BZ therefore uses GUID persistence as a **configured monitoring identity assumption with fail-closed behaviour**, not as an institutional guarantee. If a reschedule causes a new GUID and removes the configured GUID, the monitor produces a missing-GUID review rather than guessing that the new item is the same meeting.

## Authority gates

The proposed RSS route has no authority over:

- Canonical date writes;
- event clocks or UTC timestamps;
- lifecycle;
- certainty;
- Canonical name;
- automatic creation of new European Council occurrences;
- direct calendar HTML retrieval;
- item-page retrieval;
- Live Intelligence or Analysis promotion;
- automatic commits.

RSS `updated` and `description` are not event time. No clock is inferred from page or feed metadata.

## Request boundary

Per production monitor run:

- RSS requests: 1;
- robots requests: 0;
- direct calendar HTML requests: 0;
- item-link followups: 0;
- search/discovery requests: 0;
- total external request budget: 1.

The absence of a robots request is deliberate for this route: the machine-access basis is the Council's explicit dedicated RSS subscription/automatic-loading interface. This does not relax the direct-calendar HTML hold.

## Expected governed post-state

If the later offline, materialised and live gates succeed:

- Canonical Registry: v0.41 / 689 — unchanged;
- Sources: v1.98 / 254 → v1.99 / 255;
- Monitor expectations: v0.23 / 21 → v0.24 / 22;
- existing `WSSRC-INT-003`: object-for-object unchanged;
- Change Ledger: unchanged;
- Biosecurity: unchanged;
- Live Intelligence: unchanged;
- Analysis: unchanged;
- automatic Canonical commit: OFF;
- Google Calendar writes: OFF.
