# WORLD SIGNALS — CBN MPC monitor activation BQ research v0.1

**Review date:** 2026-09-08  
**Exact base main:** `65e9ceb07d0c5175db61f9251a730a9bcf563d04`  
**Boundary:** Source/Change Monitor activation only. No Canonical, Live Intelligence or Analysis population.

## Pressure selection

At the post-BP checkpoint the 12 configured production monitor routes cover Europe, North America, Latin America, East Asia, Oceania/Pacific and a cross-regional energy schedule. No configured route has an Africa Canonical occurrence in its explicit allow-list. This is a structural coverage pressure, not a quota requiring population.

The existing Central Bank of Nigeria MPC series is a suitable candidate because the Canonical Registry already contains two high-importance 2026 meeting-window occurrences backed by `WSSRC-CB-014`; BQ does not create new events to improve the regional count.

## Canonical contract

The tracked occurrences remain:

- `WSO-CBN-MPC-307`: 21–22 September 2026;
- `WSO-CBN-MPC-308`: 23–24 November 2026.

Both are `MONETARY_POLICY_DECISION_PROCESS` occurrences with `MULTI_DAY_LOCAL` timing, `DAY_RANGE` precision and source timezone `Africa/Lagos`.

The official calendar supplies a **two-day MPC meeting window**. It does not supply a forward decision publication clock. BQ must not infer that Day 2 is a decision-release timestamp, must not import historical meeting notice times into future occurrences, and must not invent a venue.

## Official operational surfaces

Primary schedule page:  
`https://www.cbn.gov.ng/MonetaryPolicy/calendar.html`

The current official 2026 table lists meetings 304–308 and continues to show:

- 307 — Sep. 21 / Sep. 22, 2026;
- 308 — Nov. 23 / Nov. 24, 2026.

Robots policy:  
`https://www.cbn.gov.ng/robots.txt`

The current `User-agent: *` policy allows the site root and does not disallow `/MonetaryPolicy/calendar.html`.

Rights evidence:  
`https://www.cbn.gov.ng/Legal.html`

The CBN legal notice permits copying from the Internet address electronically or on paper when CBN is expressly stated as source, while prohibiting amendment or distortion. WORLD SIGNALS treats this as content-reuse governance. The robots result is separately treated as endpoint operational evidence. Neither is silently substituted for the other.

## Read-only operational diagnostic

Corrected diagnostic run `34205403293`, job `101993598863` passed from the exact post-BP base.

Observed:

- robots HTTP 200, SHA-256 `a28e1810a23c0cb48b57f050d394687b0337efaca2e43c24a499773c775e0ff6`;
- legal notice HTTP 200, SHA-256 `14ac5116e938c45cfff85324037fe760858534a7fc9d86b52505898603c70a51`;
- MPC calendar HTTP 200, SHA-256 `a91d3e74e69bb0629c39f305403736714c9e02ec3a42a56de0b771a655f07160`;
- robots permitted the calendar path;
- all five 2026 meeting-number/date pairs were present;
- the repository remained byte-clean.

The earlier diagnostic run `34205246260` failed before any CBN request because BQ initially guessed `DATE_RANGE` rather than the Canonical controlled token `DAY_RANGE`. That failure changed no data and is retained as evidence of fail-closed behaviour.

## Activation contract

BQ may activate `CBN_MPC_CALENDAR` only as a bounded review monitor:

- exact allow-list: the two existing CBN occurrences only;
- maximum two requests per run: robots first, then the calendar only if permitted;
- no legal-page request during routine production monitoring;
- no broad CBN crawl;
- exact meeting-number identity;
- observed date-range change generates a review candidate only;
- a future tracked row absent from the page is review evidence only and never cancellation, delay, completion or certainty change;
- elapsed occurrence presence/absence has no lifecycle semantics;
- a future CBN meeting not in the allow-list is observation-only and requires separate scope review;
- no automatic Canonical commit;
- no Google Calendar write;
- no automatic promotion to Live Intelligence or Analysis.

The activation advances only the operational governance of `WSSRC-CB-014`. Its Canonical provenance role remains unchanged.

## Expected governed state

- Canonical: `v0.41 / 689` unchanged;
- Sources: `v1.89 / 248` → `v1.90 / 248`;
- Monitor expectations: `v0.14 / 12` → `v0.15 / 13`;
- Ledger, biosecurity overlay, Live Intelligence and Analysis unchanged;
- all write gates remain closed.
