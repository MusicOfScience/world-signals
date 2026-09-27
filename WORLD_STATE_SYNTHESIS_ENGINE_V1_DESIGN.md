# World State Synthesis Engine v1 — design decision record

**Status:** read/proposal design plus adopted production-history contract;
design-only milestones; no World State engine or production World State dataset
is implemented by this record. The adopted history contract is specified in
`WORLD_STATE_PRODUCTION_HISTORY_CONTRACT_DESIGN.md`.

**Decision date:** 2026-09-27

**Decision scope:** define the smallest coherent read contract, proposal schema,
review boundary and test boundary for a future World State Synthesis Engine v1.

## Decision

World State v1 will be a read-only, as-of synthesis proposal over already
governed layers. It will consume validated snapshots and emit an in-memory or
test-only proposal that is reviewable, hash-pinned and provenance-linked. It
will not create a second observation store, promote a statement into a higher
implementation state, create a Relationship, populate Risk/Regime or
Scenarios, revise a Forecast or Outcome, write Canonical or Live Intelligence,
or publish a projection.

The first implementation boundary is therefore:

```text
validated governed inputs
  -> explicit as-of read manifest
  -> bounded synthesis proposal
  -> human review transaction
  -> no production write
```

The proposal is not itself Canonical truth. A future reviewed World State
population, if authorised, must be a separate milestone with its own immutable
history, admission transaction and public/private policy.

World State is the continuously updated synthesis hub in the wider architecture,
not a terminal product generated only after Forecasts, Outcomes, Evaluation or
Model Learning. An unresolved system with governed observations, Signals,
Relationships and state dimensions can still yield a valid as-of proposal.
Forecast and Outcome state may be read where analytically relevant; later
Outcomes, Evaluation, calibration and Model Learning feed evidence into future
proposals without rewriting an earlier as-of assessment.

## Evidence from the current repository

The decision is constrained by the repository's existing contracts rather than
by a new conceptual data model:

| Existing contract | Evidence relevant to v1 |
| --- | --- |
| `data/live_intelligence/schema.json` v0.13 and `src/world_signals/live_intelligence.py` | Live Intelligence is the factual observation substrate. It keeps event, publication and system-observation time separate; allows unscheduled observations; preserves corrections/conflicts; prohibits causal interpretation and market attribution; and keeps automatic ingestion and public observation projection closed. |
| `data/analysis/schema.json` v0.8 and `src/world_signals/analysis.py` | Analysis already separates what happened, expectations, surprise, movement, connection, noise, alternatives, second-order effects and falsifiers. Its market policy requires measurement and rights evidence for exact timestamp series. Its Live bridge uses explicit `observation_id` values, not story/latest selectors. |
| `data/signals/schema.json` v0.1 and `src/world_signals/signals.py` | Signal revisions pin immutable observation snapshots, require an explicit qualitative baseline and preserve supporting versus contradictory evidence, alternatives, expiry and review provenance. `signal_state_as_of` reports a state without rewriting history. |
| `data/relationships/schema.json` v0.1 and `src/world_signals/relationships.py` | Relationship endpoints are reviewed Signal revisions only. Directionality and epistemic class are explicit; graph traversal cannot create edges; causal classes require reviewed mechanism and evidence. Production population and public projection are closed. |
| `data/risks/schema.json` v0.1 and `src/world_signals/risks.py` | Risk/Regime history is append-only, qualitative and as-of. Contradictory inputs remain separate, convergence is lineage-derived, thresholds require description and provenance, and unsupported numeric scores are prohibited. Production population is closed. |
| `data/scenarios/schema.json` v0.1 and `src/world_signals/scenarios.py` | Scenario Sets require competing members, explicit divergence points, conditional assumptions and signposts. Probability, ranking and forecast fields are prohibited. Production population is closed. |
| `data/forecasts/schema.json` v0.1, `src/world_signals/forecasts.py` and `data/forecasts/forecasts.json` | The four admitted pilot Forecast issuances pin information cutoffs, resolution rules, sources and vintage semantics. Later evidence may not be backdated into an issuance. |
| `data/outcomes/schema.json` v0.1 and `src/world_signals/outcomes.py` | Outcomes resolve one Forecast series under the predeclared rule and preserve event time, evidence-publication time and review time separately. Production Outcomes are empty. |
| `data/evaluation/schema.json` v0.1 and `src/world_signals/evaluation.py` | Evaluation is explicit-as-of and derived. The current state is `NO_SAMPLE`; calibration and Model Learning are not available. |
| `scripts/project_state_snapshot.py` and `tests/test_project_state_snapshot_ch.py` | Recovery surfaces are derived and read-only. They must not become a new authority or mutate governed layers. |

The current production shape confirms the boundary: Live has 12 reviewed
observations and 16 evidence rows; one Signal revision is admitted;
Relationships, Risk/Regime, Scenarios and Outcomes are empty; Forecasts contain
only the bounded prospective pilot; and public downstream projections remain
closed. A World State v1 implementation must represent these empty populations
as empty inputs, not fill them with inferred state.

## Architectural boundaries

### Upstream authority

World State reads the following inputs only through their existing contracts:

1. Canonical occurrence identity, lifecycle, timing and source provenance as
   context. Canonical remains authoritative for scheduled event truth.
2. Reviewed Live Intelligence observations and evidence as the factual current-
   development substrate.
3. Accepted Signal revisions selected by their existing as-of semantics.
4. Accepted Relationship revisions and exact reviewed graph edges selected by
   their existing as-of semantics.
5. Accepted Risk/Regime revisions selected by their existing as-of semantics.
6. Accepted Scenario Set/Scenario revisions as conditional pathways and
   signposts, never as forecasts.
7. Forecast issuance revisions and Outcome revisions as prospective evidence
   products, with their own cutoffs and resolution rules intact.
8. Analysis review and market-measurement evidence where the existing Analysis
   contract permits it. No separate World State market-data store is created.

Raw monitor candidates, OSINT runtime candidates, rejected or withdrawn
analytical objects, private runtime records and unreviewed proposals are not
World State evidence. A graph edge, visual adjacency or repeated report is not
promoted by the reader.

### Downstream authority

The v1 output is a `SYNTHESIS_PROPOSAL`, not a production state row. It may
contain a reviewed proposal decision and a complete read manifest, but the
decision cannot mutate any upstream dataset. A future causal Relationship must
still pass the Relationship contract; a future Scenario must still pass the
Scenario contract; and a future Forecast/Outcome must retain its own immutable
cutoff and resolution semantics.

The product surface remains a projection boundary:

```text
WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH
```

No UI or static site surface is part of v1. A briefing is assembled later from
reviewed state and provenance; it is never a new canonical store.

## Smallest coherent v1 read contract

The future reader should accept one explicit request and return one deterministic
proposal. The contract is intentionally smaller than the long-term World State
model.

### Read request

```text
WorldStateReadRequest {
  contract_version: "0.1",
  as_of_utc: exact UTC timestamp,
  scope: {
    jurisdictions: explicit list,
    dimensions: explicit list,
    actor_ids: optional explicit list
  },
  include_negative_evidence: true,
  input_policy: "ACCEPTED_REVIEWED_HEADS_ONLY"
}
```

`as_of_utc` is the time at which the proposal is known, not an event time,
publication time or Forecast information cutoff. Scope is explicit so an empty
result can mean either “no evidence in the declared scope” or “not queried”; the
reader must never turn an unqueried area into negative evidence.

The adapter must validate each upstream input before selecting a head. It must
call the existing validators/as-of helpers, preserve the selected revision IDs,
and record a SHA-256 manifest of the exact compact JSON objects read. It must
not reimplement upstream history rules or silently select a “latest” object.

### Proposal envelope

The smallest proposal envelope is:

```text
WorldStateSynthesisProposal {
  proposal_id,
  contract_version,
  read_request,
  generated_at_utc,
  source_manifest: [{layer, object_id, revision_id, object_sha256}],
  actors: [ActorAssertion],
  implementation_claims: [ImplementationClaim],
  dimension_assessments: [DimensionAssessment],
  baselines: [Baseline],
  anomalies: [Anomaly],
  negative_evidence: [NegativeEvidence],
  uncertainties: [TypedUncertainty],
  hypotheses: [CompetingHypothesis],
  model_disagreement: [ModelDisagreement],
  transmission_edges: [TransmissionEdge],
  scenario_references: [ScenarioReference],
  forecast_outcome_references: [ForecastOutcomeReference],
  review_transaction: ReviewTransaction
}
```

All arrays may be empty. Empty is a governed result, not a missing-data
invitation. Every non-empty object must point to at least one manifest item or
an explicit `not_yet_supported` reason. Free prose may explain a reviewed
interpretation but cannot replace structured references.

### Actor assertion

There is no governed actor registry in the current repository. v1 therefore
uses a proposal-local `ActorAssertion`, not a new production identity store:

```text
ActorAssertion {
  actor_ref,
  canonical_label,
  actor_type,
  role,
  jurisdiction,
  authority_scope,
  capabilities: [Claim],
  constraints: [Claim],
  incentives: [Claim],
  commitments: [Claim],
  channels: [Claim],
  institutional_relationships: [RelationshipClaim],
  identity_uncertainty: [TypedUncertainty],
  support_refs,
  contradiction_refs
}
```

Each `Claim` carries its own evidence references and uncertainty. Unknown or
unresolved capability, constraint, incentive, commitment or authority must be
represented explicitly as unknown; omission must not be read as absence. A
leader, ministry, legislature, court, military command, party, market
participant and state are different actor types when authority or incentives
differ. Actor aliases cannot be merged merely because names are similar.

### Implementation-state claim

```text
ImplementationClaim {
  claim_id,
  actor_ref,
  proposition,
  state: SAID | DECIDED | AUTHORISED | IMPLEMENTED | OBSERVED,
  state_as_of: exact UTC or supported civil-date precision,
  known_at_utc: exact UTC,
  effective_at: optional supported precision,
  support_refs,
  contradiction_refs,
  uncertainty_refs,
  review_status
}
```

The ladder is evidence classification, not an automatic workflow. `SAID` means
the actor communicated the proposition. `DECIDED` requires evidence of a
decision by the competent actor. `AUTHORISED` requires evidence that the
competent institution granted authority. `IMPLEMENTED` requires evidence that
the authorised act was put into operation. `OBSERVED` requires evidence of the
result or realised condition. No state implies the next state, and the ladder
is not monotonic: reversal, narrowing, contradiction, failure or divergence
from intent are retained as new claims or revisions.

### Dimensions and state memory

`DimensionAssessment.dimension` must use an explicit controlled vocabulary:

- `CONFLICT_MILITARY_ACTIVITY`
- `STRATEGIC_GEOPOLITICAL_TENSION`
- `POLITICAL_INSTITUTIONAL_STABILITY`
- `MACROECONOMIC_FINANCIAL_CONDITIONS`
- `TRADE_CAPITAL_ENERGY_FOOD_FLOWS`
- `DEPENDENCIES_CHOKEPOINTS`
- `MARKETS_AS_SENSORS`
- `CLIMATE_PHYSICAL_RISK`
- `HEALTH_BIOSECURITY`
- `TECHNOLOGY_CRITICAL_INFRASTRUCTURE`

The object contains `state_label`, `scope`, `as_of_utc`, `support_refs`,
`contradiction_refs`, `uncertainty_refs`, `baseline_ref` and
`review_status`. State labels are qualitative and dimension-specific. v1 does
not define a universal severity score.

State memory is append-only in the proposal history: retain `prior_state_ref`,
`transition_type`, `first_detected_at_utc`, `effective_at_utc`, the selected
upstream revision IDs and the review transaction. An as-of query selects the
latest eligible reviewed revision whose effective/decision time is no later
than the request time. It never edits an earlier result and never uses a later
observation to strengthen an earlier proposal.

The existing as-of helpers are the semantic source for populated downstream
layers: `signal_state_as_of`, `relationship_state_as_of`,
`relationship_graph_edges_as_of`, `risk_state_as_of`, `scenario_state_as_of`,
`forecast_state_as_of` and `outcome_state_as_of`. Their small summary returns
are not sufficient as World State evidence by themselves, so the proposal must
retain the selected full revision and hash in its read manifest.

Canonical currently exposes `status_history` in the registry and validates its
shape, but it does not provide a general executable Canonical as-of selector.
Until that contract exists, v1 may use current Canonical records as context and
must not claim a historical Canonical World State from a current flattened
record. This is an explicit limitation, not a reason to infer history.

### Baselines and anomalies

```text
Baseline {
  baseline_id,
  basis: PRIOR_REVIEWED_STATE | OBSERVATION_WINDOW | OFFICIAL_REFERENCE |
         MARKET_MEASUREMENT | EXPLICIT_NO_BASELINE,
  scope,
  reference_window,
  measurement_definition,
  baseline_value_or_label,
  source_refs,
  as_of_utc,
  limitations
}

Anomaly {
  anomaly_id,
  subject_ref,
  baseline_ref,
  observed_ref,
  comparison_method,
  threshold_ref,
  result,
  alternative_explanations,
  uncertainty_refs,
  review_status
}
```

An anomaly is a comparison result, not a World State fact or a forecast. A
baseline must be explicit, scoped and time-compatible. Numeric thresholds are
usable only when their measurement definition and provenance are supplied;
unsupported universal scores are rejected. If no defensible baseline exists,
the proposal records `EXPLICIT_NO_BASELINE` and does not call the movement an
anomaly.

### Negative evidence

Negative evidence is a typed, bounded finding rather than a claim that nothing
happened:

```text
NegativeEvidence {
  negative_evidence_id,
  type: NO_OBSERVED_IMPLEMENTATION |
        NO_EXPECTED_INSTITUTIONAL_FOLLOW_THROUGH |
        NO_MARKET_CONFIRMATION |
        NO_EVIDENCE_OF_ESCALATION |
        NO_EVIDENCE_IN_SCOPED_SOURCES,
  proposition_or_subject_ref,
  search_scope,
  expected_action_or_measure,
  as_of_utc,
  source_coverage,
  support_refs,
  limitations,
  review_status
}
```

`NO_EVIDENCE_IN_SCOPED_SOURCES` is the only form that may be emitted from a
bounded search absence, and it must retain the queried source scope,
completeness and coverage limitations. Source failure, parser failure and
unqueried space cannot produce negative evidence.

### Typed uncertainty, hypotheses and model disagreement

`TypedUncertainty.type` is one of:

`PROVENANCE_SOURCE`, `MEASUREMENT`, `TEMPORAL`, `INTERPRETIVE`, `MODEL`,
`ACTOR_INTENT`, `INSTITUTIONAL_AUTHORITY`.

Each uncertainty records the affected object, description, basis references,
whether it is unresolved or conditionally bounded, and the review status. A
single confidence score cannot replace typed uncertainty.

Competing hypotheses are structured and retain their alternatives:

```text
CompetingHypothesis {
  hypothesis_id,
  subject_ref,
  proposition,
  alternatives: [{hypothesis_ref, relation, rationale}],
  supporting_refs,
  contradictory_refs,
  disposition: UNRESOLVED | REVIEWED_PREFERRED | REJECTED,
  falsifiers,
  uncertainty_refs,
  review_status
}
```

`REVIEWED_PREFERRED` is a human decision, not an automatic ranking. Model
disagreement is separate from factual evidence and records the model/method,
version, cutoff, output or disagreement, scope and underlying evidence refs.
Model-generated prose cannot become independent corroboration merely by being
stored in this field.

### Transmission graph

The World State proposal may contain proposed transmission edges, but it must
not silently create governed Relationships:

```text
TransmissionEdge {
  edge_id,
  source_ref,
  target_ref,
  class: DEPENDENCY | FLOW | CHOKEPOINT | EXPOSURE |
         HYPOTHESISED_TRANSMISSION | MECHANISTIC_SUPPORT |
         CAUSAL_EVIDENCE | FEEDBACK | REFLEXIVE_EFFECT,
  directionality,
  mechanism,
  lag,
  threshold,
  state_condition,
  support_refs,
  contradiction_refs,
  alternative_explanations,
  review_status
}
```

Flows, dependencies and chokepoints are structural descriptions. A
`HYPOTHESISED_TRANSMISSION` edge is not a mechanism; a mechanism is not causal
evidence. `CAUSAL_EVIDENCE`, feedback and reflexive effects require a reviewed
basis and appropriate upstream Relationship treatment. Lags and thresholds
are typed claims with units/precision and provenance where applicable. Graph
proximity, transitive closure and edge count never create or strengthen an
edge; cycles are retained only when explicitly reviewed.

Markets are permitted only as measured sensors. The v1 adapter may consume a
factual Live `MARKET_OBSERVATION` or a reviewed Analysis market measurement,
but an admissible sensor reference must retain instrument/measure, venue,
timestamp or precision, baseline/counterfactual, measurement method, horizon,
liquidity/coverage caveats, alternative explanations and rights evidence when
the Analysis contract requires it. A co-movement cannot create a causal edge.

### Scenarios, Forecasts, Outcomes and calibration

Scenario references carry Scenario Set/Scenario revision IDs, conditional
assumptions, divergence points and signposts. They do not carry probabilities,
rankings or predicted outcomes.

Forecast references carry the Forecast ID, issuance/revision ID, issue time,
information cutoff and resolution rule. Outcome references carry the Outcome
revision ID and resolution status only when an Outcome exists at the World
State as-of time. Evaluation is a separate derived read; the current empty
Outcome set means no calibration claim. World State must never use a later
Outcome or Evaluation result to rewrite a prior Forecast or to make a
retrospective state claim at an earlier cutoff. This preserves the direction of
the feedback loop: Forecasts and Outcomes can inform later World State reads,
but their existence is not required for an as-of World State assessment.

## Review transaction boundary

The first review transaction is a proposal decision, not an upstream mutation:

```text
ReviewTransaction {
  transaction_id,
  transaction_type: WORLD_STATE_SYNTHESIS_REVIEW,
  proposal_sha256,
  input_manifest_sha256,
  created_by,
  created_at_utc,
  reviewed_by,
  reviewed_at_utc,
  decision: ACCEPTED | REJECTED | RETURNED_FOR_REVIEW,
  decision_basis,
  scope,
  write_targets: [],
  public_projection_permitted: false
}
```

The transaction must fail closed if the input manifest changes, an upstream
validator fails, a selected revision is unavailable at the requested as-of
time, a statement is used to imply a higher implementation state, a baseline
is missing, a contradiction is hidden, or a forecast cutoff is crossed. An
accepted proposal remains a reviewed artifact until a separately authorised
World State admission contract exists. No transaction in v1 has a write target.

## Read-only consistency checks

The future validator should check only cross-layer consistency that is safe to
derive without creating new intelligence:

1. Every source manifest item exists, validates under its native validator and
   is effective by the requested `as_of_utc`.
2. Every selected revision ID and evidence reference resolves; every hash
   matches the exact object read.
3. Every implementation claim has actor, state-specific evidence, distinct
   `state_as_of` and `known_at_utc`, and explicit contradictions/uncertainty
   where present.
4. Every dimension assessment has a declared scope and review status; no
   universal severity score or unreviewed synthetic state appears.
5. Every anomaly has an explicit compatible baseline or is marked
   `EXPLICIT_NO_BASELINE`; it does not become a forecast.
6. Every negative-evidence row has a bounded search scope and cannot be
   derived from source failure or an unqueried source.
7. Every market sensor satisfies the applicable Analysis measurement and rights
   contract; no sensor automatically creates a causal edge.
8. Supporting and contradictory references are disjoint; competing hypotheses
   and model disagreement remain visible; no count is used as confidence.
9. Every transmission edge has explicit class, directionality, lag/threshold
   semantics where claimed and reviewed status; transitive edges are not
   generated.
10. Scenario, Forecast, Outcome and Evaluation references preserve their own
    cutoffs, revision IDs and empty/`NO_SAMPLE` states.
11. The read operation is observational: deep hashes of all governed input
    files are identical before and after the proposal.
12. No `data/world_state/` production dataset, public projection or upstream
    write is created by the v1 reader.

## Smallest test-only fixture

This thread should not add a production fixture. The next implementation
tranche should add one synthetic in-memory or test-fixture bundle under
`tests/fixtures/world_state_v1/`, never under a governed production dataset.
It should contain only enough objects to test the boundary:

- two distinct actors with different authority scopes;
- one proposition observed at `SAID`, later `DECIDED`, and explicitly not yet
  `AUTHORISED` or `IMPLEMENTED` at the earlier as-of time;
- one later observation showing that an implementation claim can diverge from
  the earlier statement without rewriting it;
- one explicit baseline and one anomaly comparison;
- one typed negative-evidence finding with bounded search scope;
- two competing hypotheses, one contradiction and one model-disagreement
  record;
- one dependency/flow/chokepoint edge and one hypothesised edge with a lag;
- one market sensor with a baseline and alternative explanation that does not
  generate a causal edge;
- two conditional scenario signposts with no probability;
- one prospective Forecast reference whose later synthetic Outcome is excluded
  from an earlier read by the Forecast cutoff;
- a mutated-input, future-evidence and transitive-edge negative test.

The fixture is valid only as a contract test. It must not be copied into
`data/live_intelligence`, `data/signals`, `data/relationships`, `data/risks`,
`data/scenarios`, `data/forecasts` or `data/outcomes`.

## Migration sequence

1. **Approve this design record.** No code, schema or production World State
   data change is required for this step.
2. **Add the test-only fixture and unit tests.** Prove actor/state semantics,
   as-of exclusion, baseline/anomaly, negative evidence, uncertainty,
   competing hypotheses, market sensing, transmission and Forecast cutoff
   integrity without reading or writing production state.
3. **Implement a read adapter only.** Completed in this tranche by
   `src/world_signals/world_state_read.py` and
   `scripts/validate_world_state_read.py`. They orchestrate existing
   validators/as-of helpers and produce an ephemeral, hash-pinned proposal
   envelope. No `data/world_state/state.json`, production write, or public
   projection is created.
4. **Run a current-repository consistency proposal.** Completed in this
   tranche at the reproducible knowledge cutoff
   `2026-09-27T04:39:04Z`, the verified PR #156 merge timestamp. The retained
   non-governed package and review summary live under
   `data/world_state_audit/` and are explicitly `REVIEW_PENDING`,
   `NOT_PRODUCTION_WORLD_STATE` and `NO_WRITE_TARGETS`. The package retains the
   request, selected results, full hash-pinned manifest, repository provenance,
   semantic fingerprint and mutation proof. Relationships, Risks/Regimes,
   Scenarios and Outcomes remain empty, and Forecast Evaluation remains
   `NO_SAMPLE`.
5. **Conduct a human review transaction.** Completed for the retained proposal
   at `2026-09-27T04:39:04Z`. The separate transaction and decision record
   review authority interpretation, implementation-state classification,
   contradictions, negative-evidence scope, market rights, graph classes,
   forecast-cutoff integrity, empty-layer integrity, the Canonical historical
   limitation and mutation protection. The explicit decision is `ACCEPTED` only
   for `READ_BOUNDARY_CONSISTENCY_ONLY`; it has no write targets, does not
   admit production World State and does not permit public projection. The
   original `REVIEW_PENDING` proposal remains unchanged as non-governed audit
   evidence.
6. **Define the production World State history contract.** Completed as a
   design-only tranche in `WORLD_STATE_PRODUCTION_HISTORY_CONTRACT_DESIGN.md`.
   It adopts componentized immutable history, a reviewed Actor Registry,
   explicit three-time as-of semantics, component-level partial admission,
   separate production admission, retention and private/public projection
   gates. No production population is admitted.
7. **Implement and pressure-test the unpopulated production history contract.**
   This is the next tranche: schemas, validators, synthetic fixtures and a
   temporary-copy admission simulator only. The first production component
   remains a separate later admission decision.

## Deferred implementation questions

Migration Step 6 resolves the architectural questions above. The remaining
questions are bounded implementation experiments, not permission to populate
production state:

1. **Canonical historical selector:** a separate contract must define how
   mixed-precision Canonical `status_history` becomes an executable as-of read
   without manufacturing UTC precision. No World State implementation may
   infer this.
2. **Relationship extension:** a bounded experiment must determine whether
   `FLOW`, `CHOKEPOINT` and `EXPOSURE` fit the existing Relationship schema;
   otherwise the proposal remains non-production transmission only.
3. **Public field allowlist:** Step 7 must pressure-test field-level privacy,
   source-rights and citation rules against a synthetic private/public fixture.
4. **Model metadata availability:** Step 7 must define the minimum reproducible
   model record when a model version or prompt cannot be retained; missing
   provenance blocks model-derived admission rather than being guessed.
5. **First pilot evidence:** the DRC health/biosecurity pilot remains a Step 8
   admission decision and requires a fresh review of current upstream hashes,
   contradiction and uncertainty, not a quota or automatic promotion.

## Consequences and limitations

This design is deliberately conservative. It creates no new intelligence and
cannot yet answer a historical World State query over Canonical records with
full fidelity because Canonical lacks a general as-of selector. It also cannot
populate military, flow, chokepoint or market dimensions where the governed
upstream layers contain no admissible evidence. Those are honest empty results,
not invitations to synthesize plausible content.

The design does make the future implementation tractable: all upstream state
is selected by existing review/history contracts; actor and state semantics
are explicit; market measurements retain their existing rights discipline;
transmission remains separate from Relationship authority; and Forecasts,
Outcomes and calibration remain prospective and cutoff-safe.
