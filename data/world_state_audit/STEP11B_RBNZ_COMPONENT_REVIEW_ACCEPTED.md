# Step 11B — RBNZ component review and production admission

Decision: `ACCEPTED`
Decision scope: `RBNZ_SECOND_SPECIMEN`
Review transaction: `WS-STEP11B-RBNZ-COMPONENT-REVIEW-20260928-001`
Admission transaction: `WS-ADMISSION-NZ-RBNZ-OCR-20260928-001`

The human decision accepts exactly two internal Dimension Assessments:

- `WSDIM-MACRO-NZ-RBNZ-OCR-202609-001` — `POLICY_RATE_INCREASED_WITH_MORE_GRADUAL_FORWARD_PATH`
- `WSDIM-MARKETS-NZ-RBNZ-OCR-202609-001` — `SHORT_RATE_AND_FX_PRICING_REPRICED_LOWER_AFTER_POLICY_PATH_SURPRISE`

The Macro assessment preserves UTC-instant effective time at
`2026-09-02T02:00:00Z`, comparative `known_at_utc` at
`2026-09-05T14:40:00Z`, and MEDIUM confidence. The Markets assessment
preserves civil-date effective precision for 2026-09-02, null exact movement
bounds, source-reported endpoints, MEDIUM confidence and
`OBSERVED_ASSOCIATION` without a production Relationship.

The RBNZ actor identity decision is explicitly `DEFERRED`; no Actor Registry
identity, actor relationship, ActorStateAssertion or ImplementationClaim is
admitted. No standalone baseline, Forecast, Outcome or Evaluation object is
created. The two assessments are independent of the existing Health snapshot
series and remain `INTERNAL_ONLY`.

The snapshot is a compositional index over the two admitted RBNZ components.
It does not claim global macro or market coverage, does not create a combined
Health/RBNZ production snapshot, and preserves mixed temporal precision.
Read-time multi-series composition remains non-admitted and marked
`INDEPENDENT_ADMISSIONS`.

Production writes are limited to the two component history rows, the RBNZ
snapshot revision, the production admission transaction, and these retained
Step 11B audit records. Public projection remains prohibited.
