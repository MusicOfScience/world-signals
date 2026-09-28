# Step 11A — RBNZ second World State specimen

Status: `REVIEW_PENDING` / `READY_FOR_HUMAN_COMPONENT_REVIEW`

This is non-governed audit evidence. It is not a production World State
component, snapshot, Actor Registry identity or public projection.

## What happened

The governed Analysis review `WSAN-NZ-OCR-20260902-001` records the RBNZ's
25-basis-point increase to 2.75 percent on 2 September 2026. The headline
decision matched the economist consensus. The reviewed forward-path reading
was more gradual than market pricing.

## Candidate scope

The package proposes two independent, narrow `DIMENSION_ASSESSMENT` candidates:

- `MACROECONOMIC_FINANCIAL_CONDITIONS`: the official decision and bounded
  forward-path comparison, with known-at `2026-09-02T02:00:00Z`;
- `MARKETS_AS_SENSORS`: source-reported two-year swap and NZD/USD moves, with
  known-at `2026-09-05T14:40:00Z`, preserving null before values and the
  Analysis review's alternative explanations.

The candidates do not assert a global macro condition, causal transmission,
future trajectory, forecast, implementation state or broad market regime.

## Actor boundary

The proposal-local `Reserve Bank of New Zealand` identity candidate is
identity-only. It contains no intent, policy position, capability, constraint,
commitment or implementation claim. The identity admission transaction is a
temporary simulation contract only; the production Actor Registry remains
empty and no actor-linked component is admitted.

## What was considered and refused

The economist consensus and forward market pricing remain separate comparison
bases; no standalone baseline or anomaly component was invented. Market
co-movement remains an Analysis-owned observed association, not a Relationship
or transmission edge. No `ActorStateAssertion`, `ImplementationClaim`,
Forecast, Scenario, Risk/Regime or public Outlook object was created.

## Review and limitations

Confidence remains qualitative and bounded (`MEDIUM` for these candidate
propositions); model runtime identity/version/reasoning configuration are
`UNAVAILABLE`, and model output is not factual corroboration. The package is
ready for explicit human component review while actor identity remains a
separate unadmitted gate. Production counts remain actors 0, components 1,
snapshots 1 and admissions 1. `write_targets: []` and
`public_projection_permitted: false`.

The package's source manifest and semantic fingerprints are in the JSON audit
artifact alongside this brief.
