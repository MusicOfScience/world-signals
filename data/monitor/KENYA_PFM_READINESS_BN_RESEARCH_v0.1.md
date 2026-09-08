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

The runtime evidence is deliberately preserved as a sequence rather than collapsed into a single health claim.

1. Existing adapter evidence records the current Kenya Law route returning HTTP 403 from GitHub Actions on 3 September 2026.
2. BN bounded read-only probe run `34189112995`, job `101943332200`, on 8 September returned HTTP 200 from both the frozen and current routes. Both parsed section `25(2)`, deadline `2 / 15`, and semantic SHA-256 `3121afc21199d121650558d896055e91ab24a6ff01c62a27dfc797baeaaab50c`.
3. BN materialised read-only preflight run `34189687457`, job `101945016694`, again passed the current/frozen semantic comparison together with repository validation and byte-clean restoration.
4. The first controlled write attempt, run `34189781916`, job `101945294642`, subsequently received HTTP 403 from the **frozen** 2025-11-04 route before the current route was requested. The source transform and semantic post-state audit had passed, but the workflow stopped at that live gate; no commit or repository write occurred.

The correct runtime conclusion is therefore **variable 403/200/403 access from GitHub Actions**, not either “healthy” or “blocked”. A successful request does not prove durable availability, and a 403 does not alter the statutory rule.

## Governance interpretation

BN keeps four propositions separate:

1. **Canonical provenance:** already cleared for curated factual/legal use.
2. **Parser readiness:** technically live-validated against both current and versioned official routes and regression-tested fail-closed offline.
3. **Runtime reachability:** demonstrably variable from GitHub Actions.
4. **Unattended automated retrieval permission:** still not cleared.

Consequently, HTTP 200 and parser success must not be promoted into a recurring production route. `automated_monitoring_use` remains `ENDPOINT_REVIEW_REQUIRED`; `automated_retrieval_permission` remains `ENDPOINT_OPERATIONAL_REVIEW_REQUIRED`.

The failed live-gated transaction changes the transaction method as well as the status label. BN will not repeatedly hit Kenya Law merely to obtain a green write run while unattended endpoint permission is unresolved. The final source-registry transaction may rely on the already captured live evidence, plus offline parser regression, exact semantic mutation checks, protected-layer checksums and the full repository suite.

## Semantic boundary

The adapter hashes the normalized statutory clause rather than page markup. Unrelated page changes therefore do not become rule changes.

If a future official current route diverges from the frozen section 25(2) semantic rule, that difference is review evidence only. It cannot by itself:

- change the Canonical occurrence date;
- mark the occurrence cancelled or completed;
- infer that the statutory deadline has been operationally met;
- infer a Treasury publication or parliamentary submission event;
- create a new recurrence or clock time.

Likewise, an HTTP 403 or HTTP 200 cannot itself change any event state.

## BN target

BN is permitted to:

- advance Source Registry `v1.86 / 247` to `v1.87 / 247`;
- change only `WSSRC-REG6-001` readiness/runtime metadata;
- record the bounded successful live validation and subsequent 403 evidence;
- advance verification mode to `AUTOMATED_PILOT` as a technical verification capability;
- classify runtime health as variable rather than healthy;
- preserve all endpoint-permission and production-route holds.

BN is not permitted to change Canonical, Monitor expectations, Change Ledger, biosecurity overlay, Live Intelligence or Analysis.

## Historical test repairs

BN exposed two historical checkpoint assumptions that had become descendant ceilings:

- BM's FOMC readiness test treated Source Registry v1.86 as permanent; it now accepts later reviewed descendants while preserving every FOMC substantive invariant.
- Verification Closeout A historically established Kenya `MANUAL_AUTHORITATIVE_RECHECK`; its descendant branch now permits Kenya to advance to `AUTOMATED_PILOT` only when the explicit endpoint-permission hold, no-production-route status and monitoring hold remain intact. Other Closeout A source expectations remain exact.

## Main-history housekeeping note

Immediately before BN branch creation, an accidental one-byte `.noop` file was created on `main` and then immediately deleted. The two housekeeping commits have zero net file differences from the BM merge tree. BN is deliberately anchored to the resulting exact clean `main` SHA `9b79c93cde36a2e261a134b1259e02ca18096210` rather than concealing or bypassing that history.
