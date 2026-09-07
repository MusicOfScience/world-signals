# WORLD SIGNALS — RBA Monetary Policy Board monitor readiness BJ v0.1

**Status:** REVIEWED READ-ONLY READINESS TRANCHE  
**Reference date:** 2026-09-08  
**Exact base:** post-BI `main` `ba3f36f1f75733654f3783a2b609590186eb4971`  
**Canonical:** v0.41 / 689 occurrences  
**Sources:** v1.83 / 246  
**Monitor expectations:** v0.10 / 8 configured adapters  
**Scope:** RBA monetary-policy schedule capability only. No production route activation and no Canonical, Source Registry, Change Ledger, Live Intelligence or Analysis mutation.

## Pressure selection

Post-BI pressure was re-audited rather than mechanically activating the Japan MOF JGB candidate or adding a seventh Live observation.

The selected pressure is `WSSRC-CB-002`, Reserve Bank of Australia, because it combines:

- high intrinsic and expected market sensitivity;
- a large existing Canonical dependency footprint;
- home-region operational importance;
- four already-distinct Canonical series identities;
- two complementary primary official schedule surfaces; and
- an architecturally important timing boundary that WORLD SIGNALS must not collapse.

The boundary is:

`Monetary Policy Board meeting window != decision statement != Governor media conference != minutes publication`

This directly preserves the project's established RBA rule: the advertised multi-day meeting is not itself the decision-release occurrence. Historical heuristics about the final meeting day are unnecessary where current RBA material states the release timing directly.

The quarantined OPEC BH repair is not a dependency of BJ and is not retried here.

## Current authoritative-source verification

Primary RBA material rechecked on 8 September 2026:

- Monetary Policy Board topic calendar: https://www.rba.gov.au/schedules-events/calendar/?topics=monetary-policy-board
- Board meeting schedules: https://www.rba.gov.au/schedules-events/board-meeting-schedules.html
- copyright/disclaimer notice: https://www.rba.gov.au/copyright/
- robots policy: https://www.rba.gov.au/robots.txt

The current official schedule exposes the September monetary-policy sequence separately:

- Monetary Policy Board meeting: **28–29 September 2026**;
- Monetary Policy Decision Statement: **29 September 2026, 2.30 pm AEST**;
- Monetary Policy Decision media conference: **29 September 2026, 3.30 pm AEST**;
- Minutes of the September 2026 Monetary Policy Board Meeting: **13 October 2026, 11.30 am AEDT**.

The board-schedule page independently carries the 28–29 September meeting window. The topic calendar additionally carries the separately timed decision, conference and minutes.

The calendar also demonstrates the daylight-saving transition that makes source-native timezone handling material: September decision-day entries are labelled AEST, while the October minutes and November/December decision-day entries are labelled AEDT. BJ preserves the IANA source timezone `Australia/Sydney` and the publisher's AEST/AEDT label; it does not store Melbourne time as canonical truth.

## Rights / automation boundary

The existing source-governance classification is retained exactly:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`;
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`;
- `verification_mode = AUTOMATED_PILOT`.

The RBA states that most website material is available under CC BY 4.0, subject to identified exclusions and special conditions. The reviewed robots policy does not disallow the selected schedule paths. Neither fact is promoted into a blanket production polling licence.

BJ therefore performs one bounded read-only endpoint probe for validation but grants **no** new production automation authority.

## Adapter contract

BJ adds `src/world_signals/adapters/rba_mpb.py`.

The adapter has two read-only parsers:

1. the Monetary Policy Board topic calendar parser; and
2. the Board meeting schedule parser.

The topic-calendar parser recognises only four governed event classes:

| Event kind | Existing Canonical series |
|---|---|
| `MEETING_WINDOW` | `WS.CB.RBA.MPB_MEETING_WINDOW` |
| `DECISION_STATEMENT` | `WS.CB.RBA.MONETARY_POLICY_DECISION` |
| `PRESS_CONFERENCE` | `WS.CB.RBA.MPB_PRESS_CONFERENCE` |
| `MINUTES` | `WS.CB.RBA.MPB_MINUTES` |

It deliberately ignores unrelated calendar items and does not turn `Statement on Monetary Policy`, Chart Pack, speeches or holidays into monetary-policy decision identities.

The parser:

- preserves source-native `Australia/Sydney`;
- preserves published AEST/AEDT labels on timed events;
- stores meeting windows as civil-date ranges, not fabricated timestamps;
- stores separately published decision/conference/minutes local times as separate semantic events;
- produces a stable semantic schedule hash;
- ignores cosmetic audio-file metadata;
- changes the hash when governed schedule semantics change;
- rejects duplicate semantic events;
- cross-checks topic-calendar meeting windows against the independent Board schedule;
- fails closed if a parsed meeting window lacks a separate decision statement or media conference on the meeting end date.

This last rule is intentionally stronger than a date heuristic: it prevents a future parser regression from silently treating the second meeting day as equivalent to the decision occurrence.

## Read-only live preflight

Temporary GitHub Actions workflow `BJ RBA MPB readiness preflight` ran once on branch commit `4ccc5ebc41e9077595bd24937147c8116b080095`.

Run: **34150448326** — PASS.

Evidence from the run:

- exact `origin/main` and merge-base both matched post-BI `ba3f36f1f75733654f3783a2b609590186eb4971`;
- 7 targeted BJ tests passed;
- full repository suite passed: **883 tests**, **40 skipped** historical/prestate-only tests;
- Python compilation passed;
- both current official RBA endpoints returned HTTP **200**;
- live topic-calendar parser returned **31 governed target events**;
- live Board schedule parser returned **16 MPB meeting windows**;
- cross-surface alignment passed;
- September meeting / decision / conference / October minutes assertions passed;
- live semantic schedule hash: `c7be2be9424706b936f5f1b9557947366cb90d0043373e39d5ad3c4b863831dc`;
- every protected governed file was byte-identical before/after the probe;
- production-gate assertions passed;
- static build passed for 689 events, 8 configured monitor routes and 246 governed sources.

The temporary workflow was removed after the successful run.

## Production boundary

BJ does **not** create Monitor v0.11.

After BJ:

- Canonical remains v0.41 / 689;
- Source Registry remains v1.83 / 246;
- Change Ledger remains v0.27 / 62;
- Monitor expectations remain v0.10 / 8 configured adapters;
- no `RBA_MPB_CALENDAR` production route exists;
- `WSSRC-CB-002.automated_monitoring_use` remains `ENDPOINT_REVIEW_REQUIRED`;
- `WSSRC-CB-002.verification_mode` remains `AUTOMATED_PILOT`;
- automatic Canonical commit remains false;
- Google Calendar write remains false;
- Live Intelligence remains v0.6 / 6 observations / 9 evidence rows;
- Analysis remains v0.17 / 21 reviews / 95 evidence rows;
- no event lifecycle, date, clock time or stable identity is changed.

A later production activation would require a fresh explicit endpoint/automation decision and an explicit occurrence scope. It must not dynamically monitor every RBA-series descendant merely because a parser exists.

## Permanent mutation boundary

Permanent BJ changes are limited to:

- `src/world_signals/adapters/rba_mpb.py`;
- `src/world_signals/adapters/__init__.py`;
- `tests/test_rba_mpb_adapter.py`;
- `data/monitor/RBA_MPB_MONITOR_READINESS_BJ_PLAN_v0.1.json`;
- this reviewed readiness note.

No governed population file changes.
