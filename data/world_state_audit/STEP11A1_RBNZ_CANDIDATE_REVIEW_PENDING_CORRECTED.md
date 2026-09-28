# Step 11A.1 — RBNZ temporal-integrity correction

Status: `REVIEW_PENDING`

This is a corrected successor audit artifact. The original
`STEP11A_RBNZ_CANDIDATE_REVIEW_PENDING.json` and brief remain unchanged.

## Human review dispositions

- `MACROECONOMIC_FINANCIAL_CONDITIONS`: `DEFER_TEMPORAL_CORRECTION`
- `MARKETS_AS_SENSORS`: `DEFER_TEMPORAL_CORRECTION`
- `ACTOR_IDENTITY`: `DEFER_IDENTITY_TEMPORAL_CONTRACT`

These are contract and timing corrections, not rejection of the underlying
governed evidence.

## Corrections

The Macro candidate keeps the official policy decision's effective instant,
`2026-09-02T02:00:00Z`, but moves the complete comparative proposition's
`known_at_utc` to `2026-09-05T14:40:00Z`, the reviewed Analysis boundary. The
official-only decision and the comparative forward-path interpretation remain
separate proposition parts.

The Markets candidate no longer claims that the event release instant is the
movement onset. It uses `effective_date: 2026-09-02` with `CIVIL_DATE`
precision, retains a source-reported window description, and leaves exact
window start/end null. The existing production reader already supports this
precision; no unsupported source-window query semantics were introduced.

The proposal-local RBNZ identity no longer claims that the institution began
at the decision time. It uses `effective_from: null`,
`effective_from_precision: UNKNOWN`, and a separate identity knowledge time of
`2026-09-05T14:40:00Z`. Historical effective queries fail closed when this
bound is unknown.

## Preserved analytical boundary

The OCR increase, consensus expectation, more-gradual-than-market-pricing
interpretation, source-reported swap/NZD moves, null before-values,
alternative explanations, `MEDIUM` qualitative confidence and non-causal
market association are unchanged. No ActorStateAssertion, ImplementationClaim,
Relationship, Forecast, production component, snapshot, admission or public
projection was created.

The corrected package remains `INTERNAL_ONLY`, has no production write targets,
and preserves the original source manifest fingerprint. Its actor admission is
temporary simulation only; the Actor Registry remains empty. Step 11B remains
a separate human component-review/admission decision.
