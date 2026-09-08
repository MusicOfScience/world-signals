# WORLD SIGNALS — Kenya PFM readiness research BN v0.1

**Exact branch base:** post-BM clean tree at `9b79c93cde36a2e261a134b1259e02ca18096210`  
**Nature:** source-readiness truth repair only; no production monitor activation and no Canonical mutation authority.

## Why this tranche

The post-BL pressure audit still identified Africa as absent from configured Source/Change Monitor occurrence scope. Kenya Law / National Treasury was already singled out as a potentially useful Africa + fiscal/sovereign candidate, but explicitly warned against promotion merely to put Africa on the map.

BN therefore tests readiness rather than manufacturing geographic coverage.

## Existing governed object

`WSSRC-REG6-001` is the Kenya Law / National Treasury source for one existing Canonical occurrence:

- `WSO-REG-I-0001`
- `WSER-REG6-KE-BPS`
- region `Africa`
- category `FISCAL_SOVEREIGN_FINANCE`
- lifecycle `PLANNED`
- precision `DAY`
- statutory rule: Public Finance Management Act section 25(2), Budget Policy Statement due to Parliament by 15 February each year.

The source already permits curated legal/factual provenance while keeping endpoint automation under separate operational review. No production monitor route currently uses this source.

## Primary legal evidence

Kenya Law's Public Finance Management Act section 25(2) states that the National Treasury shall submit the Cabinet-approved Budget Policy Statement to Parliament by 15 February each year. The statutory rule is the authority for the deadline; Treasury process material may corroborate the active budget cycle but does not replace the legal source.

Official Kenya Law source family:

- current route: `https://new.kenyalaw.org/akn/ke/act/2012/18/eng`
- frozen reproducibility route: `https://new.kenyalaw.org/akn/ke/act/2012/18/eng@2025-11-04`

Kenya Law materials also support the existing content-reuse classification: written law is not treated as ordinary copyrighted literary content under the recorded Kenya Copyright Act evidence, while broader website access/automation remains a distinct governance question.

## Endpoint/runtime evidence

Historical evidence recorded in the adapter showed GitHub Actions receiving HTTP 403 from the current route on 3 September 2026.

BN ran a new bounded, identified, read-only GitHub Actions probe on 8 September 2026:

- run `34189112995`
- job `101943332200`
- frozen 2025-11-04 route: HTTP 200
- current unversioned route: HTTP 200
- both identify section `25(2)`
- both extract deadline month/day `2 / 15`
- both produce semantic rule SHA-256 `3121afc21199d121650558d896055e91ab24a6ff01c62a27dfc797baeaaab50c`
- full repository regression: 920 tests passed, 41 skipped.

The 3 September 403 is therefore historical runtime evidence, not a current endpoint-health statement. The 8 September 200/200 result does not prove permanent availability.

## Governance interpretation

BN keeps four propositions separate:

1. **Canonical provenance:** already cleared for curated factual/legal use.
2. **Parser readiness:** now live-validated against both current and versioned official routes.
3. **Runtime reachability:** healthy in the bounded 8 September probe, but historically variable.
4. **Unattended automated retrieval permission:** still not cleared.

Consequently, HTTP 200 and parser success must not be promoted into a recurring production route. `automated_monitoring_use` remains `ENDPOINT_REVIEW_REQUIRED`; `automated_retrieval_permission` remains `ENDPOINT_OPERATIONAL_REVIEW_REQUIRED`.

## Semantic boundary

The adapter hashes the normalized statutory clause rather than page markup. Unrelated page changes therefore do not become rule changes.

If a future official current route diverges from the frozen section 25(2) semantic rule, that difference is review evidence only. It cannot by itself:

- change the Canonical occurrence date;
- mark the occurrence cancelled or completed;
- infer that the statutory deadline has been operationally met;
- infer a Treasury publication or parliamentary submission event;
- create a new recurrence or clock time.

## BN target

BN is permitted to:

- advance Source Registry `v1.86 / 247` to `v1.87 / 247`;
- change only `WSSRC-REG6-001` readiness/runtime metadata;
- record the bounded live-validation evidence;
- advance verification mode to `AUTOMATED_PILOT` as a technical verification capability;
- preserve all endpoint-permission and production-route holds.

BN is not permitted to change Canonical, Monitor expectations, Change Ledger, biosecurity overlay, Live Intelligence or Analysis.

## Main-history housekeeping note

Immediately before BN branch creation, an accidental one-byte `.noop` file was created on `main` and then immediately deleted. The two housekeeping commits have zero net file differences from the BM merge tree. BN is deliberately anchored to the resulting exact clean `main` SHA `9b79c93cde36a2e261a134b1259e02ca18096210` rather than concealing or bypassing that history.
