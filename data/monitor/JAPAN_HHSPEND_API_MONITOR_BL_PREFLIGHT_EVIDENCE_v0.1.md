# BL — Japan household-spending API monitor preflight evidence

**Review date:** 2026-09-08  
**Exact post-BK base:** `3952ec1f5a6022fec43210103f7a7244442e3201`  
**Final read-only materialised preflight:** run `34170229831`, job `101888989554` — **SUCCESS**

## Live API response contract confirmed

A dedicated read-only shape probe, run `34170094304`, established the current official Statistics Dashboard `getData` JSON contract:

- successful responses use `GET_STATS.RESULT.status = "0"` with lowercase `errorMsg` and `date` keys;
- a requested month for which data do not yet exist returns HTTP 200 with `status = "1"`, `errorMsg = "It ended normally but data did not exist."`, and no `STATISTICAL_DATA` object;
- July 2026 (`20260700`) returned one validated `DATA_OBJ.VALUE` row for indicator `0704010101000010000`, statistical table `00200561`, nationwide region `00000`, monthly original series, value `301245`;
- August 2026 (`20260800`) returned the normal no-data response before its canonical 9 October 2026 release date.

The adapter therefore accepts the official lowercase result keys, keeps compatibility with the previously modelled uppercase fixture keys, and treats status `1` as an empty result **only** when the exact normal-no-data message is present and statistical data are absent. Other non-zero statuses fail closed.

## Final materialised preflight result

Run `34170229831` re-ran BL from the exact post-BK pre-state and passed every gate:

- exact main and merge-base: `3952ec1f5a6022fec43210103f7a7244442e3201`;
- guarded check-only BL transform: PASS;
- descendant-safe BK monitor ceiling repair: PASS;
- descendant-safe BG source-count ceiling repair: PASS;
- exact local mutation boundary: PASS;
- Canonical validator: 689 occurrences, PASS;
- Live Intelligence validator: schema 0.6, 6 observations, 9 evidence, PASS;
- Analysis validator: 21 reviews, 95 evidence, PASS;
- targeted BL/BK/BG/BI/BJ suite: 44 tests, PASS;
- full regression suite: **905 tests, 40 skipped, PASS**;
- Python compilation and browser JavaScript checks: PASS;
- static build: 689 events, 10 configured monitor routes, 247 governed sources;
- one bounded live Japan API request: HTTP 200, one July value row, no August-or-later value rows, zero review candidates at the review time;
- restoration audit: all governed pre-state files returned byte-for-byte to their original hashes.

The materialised post-state under test was:

- Canonical v0.41 / 689 — unchanged;
- Sources v1.85 / 247;
- Monitor expectations v0.12 / 10 routes;
- new machine source `WSSRC-MAC-030` with zero Canonical dependencies;
- new route `JAPAN_HHSPEND_STATISTICS_DASHBOARD_API` using `WSSRC-MAC-030` while Canonical schedule authority remains `WSSRC-MAC-024`;
- automatic Canonical commit OFF;
- Google Calendar writes OFF;
- Change Ledger, biosecurity overlay, Live Intelligence and Analysis unchanged.

This evidence authorises only the bounded BL transaction described in `JAPAN_HHSPEND_API_MONITOR_BL_PLAN_v0.1.json`. It does not authorise any held Japan MOF JGB, RBA MPB, RBNZ, Kenya Law or other route.
