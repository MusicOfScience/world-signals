# WORLD SIGNALS — Japan MOF JGB monitor readiness BI v0.1

**Status:** REVIEWED READ-ONLY READINESS TRANCHE  
**Reference date:** 2026-09-08  
**Exact base:** post-BG `main` `eb0845c791133bb8262692c8ebe38ab362dfeff1`  
**Canonical:** v0.41 / 689  
**Sources:** v1.83 / 246  
**Monitor expectations:** v0.10 / 8 configured adapters  
**Scope:** East-Asia monitor-capability readiness only. No production route activation and no Canonical, Source Registry, Change Ledger, Live Intelligence or Analysis mutation.

## Pressure selection

The post-BG monitor cohort is operationally narrow. EIA WPSR repaired part of the earlier energy/global gap, but the executable monitor still has no configured East-Asia occurrence scope. A seventh Live observation would be easy to add, but population count is not itself evidence of system pressure.

BI therefore tests a more structural pressure: whether an already-governed, systemically useful East-Asian authoritative schedule can support a robust read-only adapter contract without prematurely granting production automation rights.

The selected source is `WSSRC-FIS-007`, Japan Ministry of Finance, JGB auction calendar.

This selection is not a geographic quota. It is justified because the source combines:

- existing Canonical dependency and stable series identity (`WSER-FIS-JP-JGB`);
- East-Asia geographic diversity;
- sovereign-financing rather than another macro-release route;
- an official monthly schedule whose publisher explicitly says the calendar may be changed or added to;
- prior research classification `PILOT_VALIDATED_NO_AUTO_COMMIT` / `AUTOMATED_PILOT`;
- a still-open `ENDPOINT_REVIEW_REQUIRED` automation gate that BI deliberately does not override.

The quarantined OPEC competent-primary repair is not a dependency of BI and is not retried here.

## Current authoritative-source verification

Japan Ministry of Finance current official surfaces reviewed on 8 September 2026:

- JGB auction calendar index: https://www.mof.go.jp/english/policy/jgbs/auction/calendar/index.htm
- September 2026 monthly calendar: https://www.mof.go.jp/english/policy/jgbs/auction/calendar/2609e.htm
- MOF website use / copyright notice: https://www.mof.go.jp/english/about_mof/notice/index.html

The September calendar currently lists, among other rows:

- 1 September — 10-year JGB (383);
- 3 September — 30-year JGB (91);
- 8 September — 5-year JGB;
- 10 September — liquidity-enhancement auction, remaining maturities 1–5 years;
- 15 September — 20-year JGB;
- 29 September — 40-year JGB;
- 30 September — 2-year JGB.

The page explicitly states that the calendar may be changed or added to in light of circumstances and that changes will be announced in advance. That makes semantic schedule-diff detection operationally valuable.

MOF states that website content is generally governed by Japan's Public Data License v1.0 unless otherwise indicated, subject to legal and third-party exceptions. This supports factual-content reuse under the stated licence, but BI does not reinterpret content-reuse terms as blanket crawler or polling permission. No specific JGB calendar subscription/API route was established in this review.

## Adapter contract

BI adds `src/world_signals/adapters/japan_mof_jgb.py` as a read-only parser/fetch candidate.

The parser:

1. requires an English monthly heading of the form `Auction Calendar <Month> <Year>`;
2. selects the Government Bonds / Treasury Discount Bills table by semantic headers including `Auction Date`, `Issue` and `Auction Result`;
3. extracts only auction date + issue identity from that table;
4. excludes the separate borrowing table;
5. preserves source-native `Asia/Tokyo` and `CIVIL_DATE` precision;
6. rejects rows falling outside the page's stated month;
7. rejects duplicate semantic rows;
8. produces a stable semantic hash over the month, timezone, precision and auction date/issue rows;
9. ignores result-link and presentation markup so ordinary post-auction link activation does not masquerade as a schedule change.

A changed date or changed issue identity changes the semantic hash. Such a future difference would still be review evidence only; it would not itself mutate Canonical state.

## Production boundary

BI deliberately leaves all operational authority unchanged:

- `data/monitor/expectations.json` remains v0.10 / 8 adapters;
- no `JAPAN_MOF_JGB_AUCTION_CALENDAR` adapter is configured in production;
- `WSSRC-FIS-007.automated_monitoring_use` remains `ENDPOINT_REVIEW_REQUIRED`;
- `WSSRC-FIS-007.verification_mode` remains `AUTOMATED_PILOT`;
- automatic Canonical commit remains false;
- Google Calendar write remains false;
- no Canonical occurrence is added, completed, rescheduled or assigned a clock time;
- no Live Intelligence or Analysis row is added.

## Why this is not yet Monitor v0.11

A technically robust parser is necessary but not sufficient for production activation. The source-governance contract intentionally separates:

`authoritative factual reuse` from `automated endpoint access`.

BI proves parser semantics and can support a bounded GitHub-runner endpoint probe. It does not silently convert `ENDPOINT_REVIEW_REQUIRED` to `CLEARED` merely because the public page is fetchable or because PDL 1.0 governs content reuse.

A later activation tranche would require a fresh decision on endpoint/automation permission plus live-run evidence, and would then need an explicit scoped occurrence set rather than silently treating every JGB-series occurrence as monitored.

## Mutation boundary

Permanent BI changes are limited to:

- `src/world_signals/adapters/japan_mof_jgb.py`;
- `src/world_signals/adapters/__init__.py`;
- `tests/test_japan_mof_jgb_adapter.py`;
- this reviewed readiness note;
- `data/monitor/JGB_MONITOR_READINESS_BI_PLAN_v0.1.json`.

No governed population file is changed.
