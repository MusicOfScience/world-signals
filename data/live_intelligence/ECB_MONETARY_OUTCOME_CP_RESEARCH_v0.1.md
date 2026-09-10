# CP — ECB monetary-policy outcome readiness research v0.2

## Status

**READ-ONLY / POST-RELEASE EVIDENCE BLOCKED / NO OUTCOME POPULATION AUTHORISED**

Reviewed after merge of PR #123 from exact `main` commit `e1f5c97c183381f7d29bf6957aecd87cacaa96a0` on 10 September 2026. Post-release recheck updated at approximately `2026-09-10T13:56Z` (`23:56` Australia/Melbourne).

## Why CP was selected

The post-CO pressure audit left Europe as the only Canonical region without a Live specimen, but that zero is only diagnostic. CP was selected conditionally because the 10 September ECB monetary-policy decision is independently systemically important and, once authoritatively established, could exercise a scheduled monetary-policy `OUTCOME_OF` Live contract using an already-stable Canonical identity. Regional diversification is a benefit, not the selection rule.

## Exact Canonical identity

Identity-aware inspection of the actual post-#123 `main` Canonical registry resolves the scheduled decision as:

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
- time status: `CONFIRMED`
- time basis: `AUTHORITATIVE_STANDARD_PUBLICATION_RULE`
- schedule source: `WSSRC-CB-003`
- primary schedule assertion: `WSA-901c19618e13196f`
- lifecycle in merged `main`: `PLANNED`
- certainty: `CONFIRMED`
- parent meeting window: `WSO-b2fa91dfcbae5c38`
- related occurrence: `WSO-90f504a4e4925486` (separate linked event; do not collapse it into the decision)

This exact identity and timing contract must be preserved. No duplicate ECB decision occurrence may be created, and Live evidence may not rewrite Canonical timing.

## Source roles

### `WSSRC-CB-003` — schedule authority

ECB Governing Council meeting calendar: `https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html`.

It is the Canonical schedule source for the decision family. Existing source governance classifies factual schedule metadata for curated use, while unattended retrieval remains endpoint-review-required.

### `WSSRC-CB-004` — outcome publication authority

ECB monetary-policy decisions/accounts publication surface: `https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html`.

This is the registered primary source family for the actual decision outcome. Existing source governance clears ECB factual website information for curated use with attribution/accuracy conditions, but unattended retrieval remains endpoint-review-required. CP therefore uses manual authoritative recheck unless a separately reviewed Monitor route is later authorised.

## Initial official preflight

ECB official pages reviewed on 10 September 2026 stated:

- Governing Council monetary-policy meeting: 9–10 September 2026 in Berlin;
- publication of monetary-policy decisions: 14:15 Europe/Berlin time on 10 September;
- press conference: 14:45;
- macroeconomic projections: 15:45.

At the initial CP preflight point (approximately `2026-09-10T11:30Z`, 21:30 Australia/Melbourne), the 14:15 Europe/Berlin decision-release point had not yet occurred and no 10 September decision outcome was available on the reviewed official decision surface.

The scheduled clock is not completion evidence. Elapsed time must never be used as a substitute for a published result.

## Post-release authoritative recheck — 13:56Z

The scheduled release point has now passed. Fresh official-domain checks were run against:

- the ECB weekly schedule, which still records the 10 September monetary-policy meeting and the scheduled 14:15 decision publication;
- the ECB press-conference surface for 10 September, which at review time still rendered pre-release wording and the previously effective 17 June rates;
- the ECB monetary-policy decision publication family and exact-date/prefix searches for a 10 September 2026 decision release;
- exact-text searches derived from contemporaneous reporting, constrained to `ecb.europa.eu`.

At approximately `2026-09-10T13:56Z`, the reviewed official ECB web/search surfaces still did **not** expose a retrievable 10 September monetary-policy decision press release or monetary-policy statement. Exact searches continued to resolve earlier 2026 decision releases rather than the 10 September outcome.

This is treated as an authoritative-retrieval/indexing gap, **not** as evidence that the Governing Council made no decision and **not** as permission to infer completion from schedule passage.

## Secondary reporting observed but not admitted as CP outcome evidence

Reuters published contemporaneous reporting at `2026-09-10T12:19:12Z` stating that the ECB raised its benchmark deposit rate by 25 basis points to 2.50% and attributing language to an ECB statement:

`https://www.reuters.com/business/ecb-raises-interest-rates-fight-off-inflation-jump-2026-09-10/`

A later Reuters press-conference report also described a quarter-point increase to 2.50%:

`https://www.reuters.com/markets/us/lagarde-comments-ecb-press-conference-2026-09-10/`

These reports strongly indicate that a decision and press conference occurred, but they are **not** substituted for the registered ECB primary outcome source in CP. They do not authorise:

- Canonical lifecycle completion;
- a Live `OUTCOME_OF` observation;
- a rate-value payload;
- expectation/surprise classification;
- market-reaction or causal claims.

Their role in this research file is diagnostic only: they show that the remaining blocker is primary-source retrieval, not mere passage of the scheduled release time.

## Lifecycle architecture decision

The current Live readiness contract correctly fails closed while `WSO-ad4d0618a65059f2` remains `PLANNED`.

Existing WORLD SIGNALS precedent supports an explicit lifecycle transaction rather than a Live side effect:

1. obtain first-party ECB result evidence from the registered outcome family;
2. record a bounded Canonical `LIFECYCLE_COMPLETION` for the existing occurrence, preserving stable identity and every timing field;
3. append normal status history and Change Ledger provenance;
4. do not add a Source Registry identity unless fresh evidence proves the existing source contract is insufficient;
5. only after the anchor is `COMPLETED`, review one bounded Live factual observation linked `OUTCOME_OF` that occurrence.

Whether the lifecycle and Live mutations are committed atomically or as two guarded steps inside CP must be decided in the frozen production plan before materialisation. In either design, no Live row may exist against a still-`PLANNED` anchor.

## Required sequence once primary ECB evidence is retrievable

If and only if a fresh official recheck retrieves the 10 September monetary-policy decision:

1. verify the exact publication against `WSSRC-CB-004` and preserve the source wording;
2. verify that the publication corresponds to stable Canonical occurrence `WSO-ad4d0618a65059f2`;
3. inspect whether the source supplies an exact publication timestamp or only a civil publication date; do not fabricate precision;
4. freeze the evidence-backed lifecycle change, Change Ledger row and protected-field set;
5. freeze the bounded Live evidence/payload separately from any expectation, surprise or market interpretation;
6. run focused pre-write contract tests before any governed mutation;
7. materialise only through the established guarded transaction path;
8. keep press conference, macroeconomic projections, meeting window and later account/minutes as separate source/event concepts unless the factual decision release itself explicitly requires otherwise;
9. do not create an ECB Monitor route merely because the page is publicly reachable;
10. preserve automatic Canonical commit, Calendar write, automatic Monitor→Live, automatic Live→Analysis and public projections as closed.

## Abort / defer conditions

CP remains no-write or must be reselected if any of the following holds on fresh review:

- the official 10 September decision cannot be retrieved from a competent ECB primary surface;
- outcome wording cannot be cleanly matched to the stable Canonical occurrence;
- source timing/provenance materially differs from the existing Canonical contract;
- an official correction/retraction/conflict is present and requires the CM contract;
- lifecycle completion cannot be supported independently of elapsed schedule time.

## Current conclusion

CP remains substantively well selected, but it is **BLOCKED ON PRIMARY ECB OUTCOME RETRIEVAL AND NOT READY FOR GOVERNED OUTCOME POPULATION**.

The stable identity, timing, source roles and lifecycle boundary are resolved. Secondary reporting is explicitly quarantined from production evidence. No Canonical, Source Registry, Change Ledger, Monitor, Live, Analysis, Calendar or OPEC-quarantine governed state is authorised to change from this recheck alone.
