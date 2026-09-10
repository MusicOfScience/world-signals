# CP — ECB monetary-policy outcome readiness research v0.1

## Status

**READ-ONLY / NO OUTCOME POPULATION AUTHORISED**

Reviewed after merge of PR #123 from exact `main` commit `e1f5c97c183381f7d29bf6957aecd87cacaa96a0` on 10 September 2026.

## Why CP was selected

The post-CO pressure audit left Europe as the only Canonical region without a Live specimen, but that zero is only diagnostic. CP was selected conditionally because the 10 September ECB monetary-policy decision is independently systemically important and, once published, could exercise a scheduled monetary-policy `OUTCOME_OF` Live contract using an already-stable Canonical identity. Regional diversification is a benefit, not the selection rule.

## Exact Canonical identity

Identity-aware inspection of the Canonical registry resolves the scheduled decision as:

- occurrence: `WSO-ad4d0618a65059f2`
- series: `WS.CB.ECB.MONETARY_POLICY_DECISION`
- name: `ECB Governing Council monetary policy decision — 2026-09-10`
- category: `MONETARY_FINANCIAL_POLICY`
- subcategory: `MONETARY_POLICY_DECISION`
- region: `Europe`
- jurisdiction: `Euro area`
- institution: `European Central Bank`
- timing type: `LOCAL_DATETIME`
- native time: `2026-09-10T14:15:00`
- native IANA timezone: `Europe/Berlin`
- canonical UTC: `2026-09-10T12:15:00Z`
- precision: `MINUTE`
- source: `WSSRC-CB-003`
- lifecycle at CP preflight: `PLANNED`
- certainty: `CONFIRMED`
- parent meeting window: `WSO-b2fa91dfcbae5c38`
- related occurrence: `WSO-90f504a4e4925486` (separate linked event; do not collapse it into the decision)

This exact identity must be preserved. No duplicate ECB decision occurrence may be created.

## Source roles

### `WSSRC-CB-003` — schedule authority

ECB Governing Council meeting calendar. It is the Canonical schedule source for the decision family. Existing source governance classifies factual schedule metadata for curated use, while unattended retrieval remains endpoint-review-required.

### `WSSRC-CB-004` — outcome publication authority

ECB monetary-policy decisions/accounts publication surface. This is the appropriate primary source family for the actual decision outcome. Existing source governance clears ECB factual website information for curated use with attribution/accuracy conditions, but unattended retrieval remains endpoint-review-required. CP therefore uses manual authoritative recheck unless a separately reviewed Monitor route is later authorised.

## Fresh official preflight

ECB official pages reviewed on 10 September 2026 state:

- Governing Council monetary-policy meeting: 9–10 September 2026 in Berlin;
- publication of monetary-policy decisions: 14:15 Europe time on 10 September;
- press conference: 14:45;
- macroeconomic projections: 15:45.

At the CP preflight point (approximately `2026-09-10T11:30Z`, 21:30 Australia/Melbourne), the 14:15 Europe/Berlin decision-release point had not yet occurred and no 10 September decision outcome was available on the reviewed official decision surface.

Therefore the scheduled clock is **not** completion evidence. Elapsed time must never be used as a substitute for a published result.

## Required post-release sequence

If and only if a fresh official recheck finds the 10 September monetary-policy decision:

1. verify the publication against the ECB primary outcome surface (`WSSRC-CB-004`) and preserve the exact source wording;
2. verify that the published decision corresponds to stable Canonical occurrence `WSO-ad4d0618a65059f2`;
3. update Canonical lifecycle from `PLANNED` to `COMPLETED` only with evidence-backed provenance and normal Change Ledger/history treatment;
4. only after the Canonical anchor is completed, consider one bounded factual Live observation linked `OUTCOME_OF` that existing occurrence;
5. keep press conference, macroeconomic projections, meeting window and later account/minutes as separate source/event concepts;
6. do not infer surprise, market reaction, causal transmission or second-order effects in the Live row;
7. do not create an ECB Monitor route merely because the page is publicly reachable;
8. preserve automatic Canonical commit, Calendar write, automatic Monitor→Live, automatic Live→Analysis and public projections as closed.

## Abort / defer conditions

CP must remain no-write or be reselected if any of the following holds on fresh post-release review:

- no official 10 September decision is available;
- outcome wording cannot be cleanly matched to the stable Canonical occurrence;
- source timing/provenance materially differs from the existing Canonical contract;
- an official correction/retraction/conflict is present and requires the CM contract;
- lifecycle completion cannot be supported independently of elapsed schedule time.

## Current conclusion

CP is **READY FOR POST-RELEASE EVIDENCE RECHECK, NOT READY FOR GOVERNED OUTCOME POPULATION**. The architecture and stable identity are resolved; the missing input is the actual authoritative 10 September ECB decision.