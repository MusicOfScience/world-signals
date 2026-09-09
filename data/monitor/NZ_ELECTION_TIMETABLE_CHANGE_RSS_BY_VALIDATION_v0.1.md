# WORLD SIGNALS — BY New Zealand election timetable RSS validation v0.1

**Reference date:** 2026-09-09  
**Exact post-BX base:** `a3bca03f36eb5af9036017aad926f75f6762267f`

## Governed design under validation

BY introduces an Electoral Commission New Zealand Media & News RSS source-page update sentinel for the six already-modelled 2026 General Election timetable milestones.

The design does **not** promote or modify the existing timetable HTML source `WSSRC-EL-NZ-001`. That source remains the Canonical authority and retains its existing automation/endpoint hold. BY adds a separate monitor-only RSS identity `WSSRC-EL-NZ-002` and route `NZ_ELECTION_TIMETABLE_CHANGE_RSS`.

A positive signal requires exact `link` and `guid` equality to:

`https://elections.nz/media-and-news/2026/key-dates-for-2026-general-election`

A match generates one six-occurrence bundle review only. It does not identify a changed milestone, propose a date, fetch the timetable HTML, or mutate Canonical state.

## Pressure/readiness audit

Run `34299113626`, job `102302051974` — **SUCCESS**, read-only.

Key findings:

- no already-cleared/unrouted Canonical source was available for mechanical activation;
- `ELECTIONS_GOVERNANCE` had 28 Canonical occurrences and zero production monitoring;
- `WSSRC-EL-NZ-001` had six forward confirmed dependencies with factual Canonical reuse cleared but HTML endpoint automation still held;
- BY therefore examined a separate Electoral Commission machine interface rather than relaxing the timetable HTML hold.

## RSS discovery

Run `34299288416`, job `102302572476` — **SUCCESS**, read-only.

Exactly two first-party requests:

1. `https://elections.nz/robots.txt`
2. `https://elections.nz/media-and-news`

Findings:

- robots HTTP 200 `text/plain`;
- declared `Crawl-delay: 2`;
- Media & News path allowed;
- Media & News HTTP 200;
- exactly one advertised first-party feed discovered: `https://elections.nz/media-and-news/rss`;
- no RSS, item, timetable or results-data follow-up request in the discovery run.

## RSS endpoint diagnostic

Run `34299383044`, job `102302861060` — **SUCCESS**, read-only.

The two-second crawl delay was respected. Exactly two requests were made: robots then advertised RSS.

RSS result:

- HTTP 200;
- `application/rss+xml; charset=utf-8`;
- 6,523 bytes;
- SHA-256 `ec3dc5162f2ff4d01e699249c2fa606ea2a7c0c0082e0cb9d39cb77faacf056d`;
- strict well-formed RSS;
- channel title `10 Most Recently Updated Pages`;
- channel description `Shows a list of the 10 most recently updated pages.`;
- exactly 10 items;
- one item-field contract: `title`, `link`, `description`, `pubDate`, `guid`;
- timetable page absent in the snapshot;
- zero item/page follow-ups.

This established the rolling-feed semantics and ruled out treating feed absence as proof that the timetable page had not changed.

## Focused offline parser/comparator gate

Run `34299993872`, job `102304659812` — **SUCCESS**, read-only.

The focused suite covered:

- exact ten-item channel contract;
- malformed XML;
- channel drift;
- item-count drift;
- off-host links;
- link/guid disagreement;
- duplicate identities;
- robots allow/disallow and crawl-delay handling;
- non-policy robots bodies;
- absent-target no-candidate semantics;
- exact timetable identity -> one six-occurrence bundle review;
- ordinary election-news dates not becoming timetable-change evidence;
- duplicate target fail-closed behaviour;
- descendant Canonical date compatibility;
- authority-gate drift;
- Canonical shape drift;
- comparator input immutability.

## Materialised preflight

Run `34300370946`, job `102305798679` — **SUCCESS**.

The helper was applied only inside the ephemeral runner.

Governed materialised post-state:

- Canonical Registry: v0.41 / 689 — unchanged;
- Sources: v1.97 / 253 -> v1.98 / 254;
- Monitor expectations: v0.22 / 20 -> v0.23 / 21;
- automatic Canonical commit: OFF;
- Google Calendar write: OFF.

The materialised mutation boundary was exactly five files:

1. `data/sources/registry.json`
2. `data/monitor/expectations.json`
3. `scripts/run_live_monitor.py`
4. `scripts/run_adapter_smoke.py`
5. `src/world_signals/adapters/__init__.py`

`WSSRC-EL-NZ-001` remained object-for-object identical.

Repository gate:

- registry validator: PASS;
- Live Intelligence validator: PASS;
- Analysis validator: PASS;
- **1,102 unit tests passed; 63 intentionally skipped**;
- Python compilation: PASS;
- all JavaScript syntax checks: PASS;
- static build: PASS;
- protected data-layer hashes unchanged;
- runner restored byte-clean.

No historical checkpoint repair was required.

## Production-shaped live preflight

Run `34300507314`, job `102306205627` — **SUCCESS**.

The fully materialised BY route was exercised against the live Electoral Commission endpoints.

Network contract observed exactly:

- robots requests: 1;
- live robots status: HTTP 200;
- live robots body: 95 bytes;
- live robots SHA-256: `c98676c2e5570065359053fc8c8375d5cebe1da0e2514c7ae174ec7aa7f5d249`;
- inter-request delay: 2.0 seconds;
- RSS requests: 1;
- RSS status: HTTP 200;
- RSS content type: `application/rss+xml; charset=utf-8`;
- RSS body: 6,523 bytes;
- RSS SHA-256: `ec3dc5162f2ff4d01e699249c2fa606ea2a7c0c0082e0cb9d39cb77faacf056d`;
- timetable HTML requests: 0;
- item follow-up requests: 0;
- results-data requests: 0;
- search/discovery requests: 0;
- total external requests: 2.

Live semantic result:

- rolling feed item count: 10;
- exact Canonical timetable page present: **false**;
- review candidate count: **0**;
- observation emitted: `NZ_ELECTION_TIMETABLE_SENTINEL_HEALTHY_ROLLING_WINDOW_OBSERVATION`;
- explicit rolling completeness: `FINITE_ROLLING_WINDOW_NOT_EXHAUSTIVE_CHANGE_LOG`;
- absence has no event-state semantics;
- RSS `pubDate` is not event time;
- no automatic timetable/item fetch;
- no Canonical mutation;
- no Live Intelligence or Analysis promotion.

After the live parse, the complete repository validators/tests/build passed again and the runner restored byte-clean.

## Controlled governed transaction

Run `34301969070`, job `102310582522` — **SUCCESS**.

The controlled transaction re-established the exact post-BX ancestry immediately before applying and immediately before pushing the governed patch. `origin/main` remained:

`a3bca03f36eb5af9036017aad926f75f6762267f`

The transaction:

- ran the helper in check-only mode before materialisation;
- applied only the five previously validated governed/runtime files;
- proved the staged set was exactly those five files;
- preserved `WSSRC-EL-NZ-001` object-for-object;
- created only the monitor identity `WSSRC-EL-NZ-002` and route `NZ_ELECTION_TIMETABLE_CHANGE_RSS` at the governed layer;
- confirmed Canonical v0.41 / 689 unchanged;
- confirmed Sources v1.98 / 254;
- confirmed Monitor expectations v0.23 / 21;
- kept automatic Canonical commit OFF and Google Calendar write OFF;
- passed registry, Live Intelligence and Analysis validators;
- passed **1,102 unit tests with 63 intentionally skipped**;
- passed Python compilation, all JavaScript syntax checks and static build;
- proved protected data layers byte-identical;
- pushed governed commit `cd2ef381665fc583f20ca17a5b4777acd9a3f40b` (`BY: activate NZ election timetable RSS sentinel`).

The temporary controlled-transaction workflow was then removed via the repository contents interface rather than broadening the workflow token's permissions. Its retirement commit was:

`86cd3b04282dce226ab142510689290614169339`

No BY diagnostic, preflight or transaction workflow remains in the branch.

## Validation conclusion

BY's architecture is validated and the governed activation has completed:

**Canonical election timetable authority stays held/manual for HTML retrieval; the separately advertised RSS feed becomes a bounded source-page update sentinel only.**

A future exact timetable-page feed item may create a six-occurrence manual-review bundle. It cannot itself change any milestone date, lifecycle, certainty or clock.
