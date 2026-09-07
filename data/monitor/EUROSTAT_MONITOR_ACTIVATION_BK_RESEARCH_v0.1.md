# WORLD SIGNALS — Eurostat monitor activation BK research v0.1

**Reference date:** 2026-09-08  
**Exact base main:** `2510ca6aa46f4e172b87ced5f2015488c655be75`  
**Scope:** recover the official Eurostat internet-calendar endpoint and determine whether `WSSRC-MAC-005` can move from endpoint-identity hold to a ninth read-only review monitor. No Canonical, Live Intelligence or Analysis population is authorised by this research record.

## Why this pressure was selected

Post-BJ pressure review found Eurostat to be the strongest unexploited monitor candidate because the source-governance layer had already separated and cleared the relevant automation permission while the production route remained blocked by one operational defect: the generated `.ics` endpoint identity had not been recovered. This is not a geographic quota decision; it is the clearest case where existing governance authority and canonical dependency can be converted into a real review-only capability without weakening source standards.

`WSSRC-MAC-005` entered BK with:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`;
- `automated_monitoring_use = CLEARED`;
- `verification_mode = AUTOMATED_PILOT`;
- `monitoring_activation_status = ENDPOINT_IDENTITY_HOLD_NO_LIVE_ROUTE`;
- 12 existing Canonical dependencies.

BK does **not** infer new permission from successful fetching. It relies on the already-reviewed Eurostat subscription mechanism and resolves the remaining endpoint/identity question.

## Official endpoint recovery

Eurostat's official subscription page is:

`https://ec.europa.eu/eurostat/subscribe/ics.format`

A read-only GitHub-runner probe inspected the live first-party page implementation. The page's own URL-generator code constructs the subscription route from the current origin plus:

`/eurostat/o/calendars/eventsIcal?theme=<theme>&category=<category>`

For the complete subscription surface, the page's own selector values resolve to:

`https://ec.europa.eu/eurostat/o/calendars/eventsIcal?theme=0&category=0`

This endpoint was therefore recovered from Eurostat's live implementation, not guessed from URL patterns.

### Research evidence

- run `34160965654` — PASS: exact post-BJ base, 12 canonical dependencies and prior hold state introspected; official subscription page and first-party assets inspected; no governed mutation;
- run `34161096050` — PASS: narrowed inspection recovered the live generator contract and all-category URL construction;
- run `34161197856` — PASS: recovered all-category endpoint returned HTTP 200 and a semantic RFC 5545 VCALENDAR with 2,397 VEVENTs at the observation point; the tracked Eurostat release names were visible on their canonical dates;
- run `34161294980` — intentional negative-control FAILURE: `category=2` (Euro indicator release) carried several tracked releases but omitted the 20 October 2026 `GDP main aggregates and employment - update` item. This proves the filtered route is incomplete for WORLD SIGNALS' 12-occurrence scope and must not be promoted merely because it is semantically attractive;
- run `34161741308` — PASS: complete read-only BK preflight, including check-only post-state, live all-category feed against proposed nine-route contract, full repository suite, static build and governed byte-identity check.

## Feed semantics

The recovered endpoint currently returns `Content-Type: text/plain`, but its body is a complete VCALENDAR (`BEGIN:VCALENDAR` / `END:VCALENDAR`, Eurostat release-calendar PRODID, VEVENT records). BK therefore validates semantic format rather than trusting the HTTP media type alone.

For the tracked releases, the feed currently publishes `DTSTART` as civil `DATE` values. Four existing international-trade Canonical occurrences contain richer 11:00 Europe/Luxembourg timestamps from authoritative schedule evidence. The ICS route may corroborate their civil date, but **cannot remove, replace or downgrade those clocks**.

The generated VEVENT `UID` was also observed to vary between full-feed and filtered-feed views. BK consequently treats UID as evidence only. WORLD SIGNALS stable occurrence IDs remain authoritative; source-side matching uses exact official release title plus a bounded nearest-date window.

## Tracked source identities

The explicit allow-list is:

| Occurrence | Eurostat feed title |
|---|---|
| `WSO-MAC-A-0030` | `Inflation (HICP)` |
| `WSO-MAC-A-0031` | `Flash estimate inflation euro area` |
| `WSO-MAC-A-0032` | `Unemployment` |
| `WSO-MAC-A-0033` | `GDP main aggregates and employment` |
| `WSO-MAC-A-0034` | `GDP main aggregates and employment - update` |
| `WSO-MAC-A-0035` | `Preliminary flash estimate GDP - EU and euro area` |
| `WSO-MAC-A-0036` | `Flash estimate GDP and employment - EU and euro area` |
| `WSO-MAC-B-0053` | `Retail trade` |
| `WSO-MAC-B-0054` | `International trade in goods` |
| `WSO-MAC-B-0055` | `International trade in goods` |
| `WSO-MAC-B-0056` | `International trade in goods` |
| `WSO-MAC-B-0057` | `International trade in goods` |

The repeated trade title is disambiguated by bounded nearest civil date, not UID.

## Fail-closed production contract

The proposed route is `EUROSTAT_RELEASE_CALENDAR_ICS` and remains review-only:

- exact tracked occurrence allow-list must equal the configured canonical scope;
- exact official feed title is required;
- among exact-title events, one unique nearest event must exist within a maximum 10-day window;
- a tied nearest match is ambiguity, not an arbitrary selection;
- date drift creates a review candidate only;
- absence/out-of-window creates a review candidate only;
- elapsed occurrences are not presence-checked against the current feed;
- absence or drift never means cancellation, completion or certainty change;
- feed DATE precision cannot downgrade a richer Canonical timestamp;
- source failure is source-health state only;
- automatic Canonical commit remains OFF;
- Google Calendar writes remain OFF.

## Geographic critique

Adding Eurostat does not remedy the monitor layer's geographic concentration. BI and BJ improved East-Asia/Australia readiness but remain non-production because their endpoint-governance gates are unresolved. Africa still lacks a production monitor route. That remains a genuine structural pressure after BK; it should be addressed by finding a source with both valid access governance and executable endpoint semantics, not by lowering standards to fill a map.
