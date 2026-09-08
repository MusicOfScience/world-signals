# WORLD SIGNALS — Federal Reserve Monetary Policy RSS monitor BP v0.1

**Exact base:** `edc800a694370b66d4c5c6d0a465fb3e5e554218`  
**Mode:** separate official machine publication sentinel; review-only; no FOMC HTML schedule activation.

## Why this tranche

Post-BO, WORLD SIGNALS has eleven configured production-monitor routes and now includes Australian monetary-policy schedule monitoring. The remaining pressure set includes Africa production coverage, North American monetary policy, Japan sovereign financing and other held/readiness sources.

Nigeria's Central Bank remains important and its reviewed site terms support attributed factual reuse, but the existing CBN source still lacks an explicitly reviewed machine-subscription interface. BP therefore does not activate CBN merely to fill the Africa gap.

The Federal Reserve provides a materially different governance situation. Its RSS documentation explicitly describes feeds being consumed by RSS reader/aggregator software that automatically incorporates updates, while the Board's disclaimer states that Board-produced website information is public domain unless otherwise indicated and may be copied and distributed without permission. That supports a narrow official machine-interface route without lifting the separate unresolved automation status of the FOMC HTML schedule pages.

## Source decomposition

`WSSRC-CB-001` remains the Canonical FOMC schedule authority. It continues to own all 44 existing Canonical FOMC occurrences and retains:

- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`;
- `automated_retrieval_permission = PENDING_ENDPOINT_OPERATIONAL_REVIEW`;
- `monitoring_activation_status = ENDPOINT_PERMISSION_HOLD_NO_PRODUCTION_ROUTE`.

BP introduces `WSSRC-CB-015` solely as the official Monetary Policy RSS publication sentinel. It has zero Canonical schedule dependencies.

The distinction is deliberate: a machine publication feed can provide evidence that a scheduled statement or minutes release has appeared without becoming authority for the meeting schedule itself.

## Official surfaces

- Monetary Policy RSS: `https://www.federalreserve.gov/feeds/press_monetary.xml`
- RSS documentation: `https://www.federalreserve.gov/feeds/feeds.htm`
- Board disclaimer / public-domain policy: `https://www.federalreserve.gov/disclaimer.htm`
- Canonical schedule authority retained separately: `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm`

Third-party material, logos, seals or linked material are not swept into the BP clearance.

## Read-only diagnostic

GitHub Actions run `34201995068`, job `101982693680`, on 8 September 2026:

- exact post-BO ancestry and governed pre-state: PASS;
- Canonical FOMC family: 44 occurrences;
- exact publication subset: 22 occurrences — 11 policy decisions + 11 minutes;
- RSS: HTTP 200, `text/xml`;
- RSS documentation: HTTP 200;
- disclaimer: HTTP 200;
- current feed items: 15;
- FOMC-related current feed items: 10;
- current RSS SHA-256: `29f22f648e90461f404d2da6b90e068544ca35891e27d567d61ade7ed9978015`;
- statement and minutes publication forms both observed;
- repository mutation: none.

Historical statement items use the exact title `Federal Reserve issues FOMC statement`. Historical minutes items use titles beginning `Minutes of the Federal Open Market Committee,` followed by the related meeting dates.

Observed 2026 statement and minutes `pubDate` timestamps align exactly to 2:00 p.m. `America/New_York` after conversion from the feed's GMT timestamp. This is evidence for matching, not a newly inferred schedule rule.

## Canonical publication scope

The BP allow-list contains exactly 22 already-scheduled `WSSRC-CB-001` occurrences from September 2026 through December 2027:

- `WS.CB.FED.FOMC_POLICY_DECISION`: 11;
- `WS.CB.FED.FOMC_MINUTES`: 11.

Every tracked row remains `MINUTE` precision in `America/New_York` and remains Canonically sourced to `WSSRC-CB-001`.

Meeting windows and press conferences are deliberately excluded from this RSS route.

## Matching semantics

The feed carries an explicit timezone-aware publication timestamp. BP normalises that timestamp to UTC and compares it with the already-scheduled Canonical occurrence converted from `America/New_York`.

Classification is intentionally narrow:

1. exact statement title/description → FOMC policy-decision publication;
2. `Minutes of the Federal Open Market Committee, ...` → minutes publication;
3. other FOMC-related feed items → nonsemantic observation only;
4. other monetary-policy items → ignored by this route.

A classified publication is matched only to the same series and the nearest occurrence inside the configured timestamp tolerance. A tied nearest match is never guessed. Multiple RSS items mapping to the same occurrence fail closed.

Historical or otherwise out-of-scope publication items remain observations only.

## Lifecycle boundary

A matching official RSS publication is strong evidence that the publication is available. BP nevertheless does **not** write `COMPLETED` automatically. Instead it creates a review candidate:

`FED_FOMC_PUBLICATION_EVIDENCE_AVAILABLE`

with review state:

`PENDING_AUTHORITATIVE_FOMC_PUBLICATION_REVIEW`.

This keeps publication evidence and Canonical lifecycle mutation separate.

The finite rolling feed is not a schedule. Absence therefore has no cancellation, delay, completion, certainty or date semantics.

## Runtime discipline

BP uses one dedicated Monetary Policy RSS request per daily monitor run. It does not crawl the wider Federal Reserve site, does not request the FOMC HTML calendar as part of this route and does not alter BM's endpoint-permission hold.

Feed fetch or parse failure becomes source-health evidence only.

## Governed target

BP may advance:

- Sources `v1.88 / 247` → `v1.89 / 248` by adding only `WSSRC-CB-015`;
- Monitor expectations `v0.13 / 11` → `v0.14 / 12` by appending only `FED_MONETARY_POLICY_RSS`;
- bounded runtime/smoke wiring for that one feed.

BP may not change Canonical, Change Ledger, biosecurity overlay, Live Intelligence datasets or Analysis datasets. Automatic Canonical commit and Google Calendar writes remain disabled.

## Coverage interpretation

If activated, BP provides a first North American central-bank publication sentinel and complements, rather than replaces, the separate FOMC schedule-readiness adapter. It does not solve the still-open Africa production-monitor deficit exposed by BN; that pressure remains explicit.
