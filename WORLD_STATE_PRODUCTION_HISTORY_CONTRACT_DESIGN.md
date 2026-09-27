# World State production history contract — design decision record

**Status:** adopted design; design-only Migration Step 6; no production World
State population is admitted by this record.

**Decision date:** 2026-09-27

**Depends on:** `WORLD_STATE_SYNTHESIS_ENGINE_V1_DESIGN.md`, the retained Step 4
consistency proposal and the Step 5 review transaction.

**Next implementation boundary:** Migration Step 7 — implement and pressure-test
the unpopulated contract, validators and admission simulation. A separate
transaction is required before the first production component is admitted.

## Decision summary

World State production history will be **compositional and immutable**. It will
not be one mutable `data/world_state/state.json` record containing everything
the project believes. Independently reviewed component revisions will be
admitted through an explicit transaction; immutable snapshot revisions will
index exact component revisions and exact upstream governed revisions.

```text
reviewed proposal
      ↓
component-level review and disposition
      ↓
WORLD_STATE_PRODUCTION_ADMISSION
      ↓
immutable component revisions + immutable snapshot revision
      ↓
explicit knowledge/effective as-of queries
      ↓
allowlisted private or public projection
```

The accepted Step 5 transaction remains only
`READ_BOUNDARY_CONSISTENCY_ONLY`. It is not a production admission and cannot
be used as one. This record defines the contract needed before any governed
World State component exists; it does not create that component, an Actor
Registry, a public projection or a new production directory.

## Evidence and architectural constraints

The design reuses repository patterns rather than inventing a parallel
governance system:

| Existing evidence | Decision consequence |
| --- | --- |
| `src/world_signals/signals.py`, `relationships.py`, `risks.py`, `scenarios.py`, `forecasts.py` | Stable IDs, immutable revisions, contiguous revision numbers, predecessor links, explicit review states and as-of helpers are the baseline history pattern. |
| `src/world_signals/outcomes.py` and `evaluation.py` | Resolution and evaluation remain separate from Forecast issuance; later evidence cannot rewrite earlier prospective state. |
| `data/signals/signal_admission_transaction_v1.json` and `data/forecasts/admission_transaction.json` | A populated layer requires an explicit accepted transaction with pre/post identity and hash evidence. |
| `data/world_state_audit/` and Step 5 review transaction | A reviewed proposal is not admission; write targets and public permission must be explicit. |
| `src/world_signals/world_state_read.py` | The read manifest, exact revision references, mutation proof and Canonical historical limitation are reusable inputs, not production state. |
| `data/*/schema.json` public policies | Admitted does not mean publishable. Existing public gates are closed by default and remain so for World State. |

The production namespace is reserved for a later tranche. The implementation
plan may use separate component datasets such as
`data/world_state/actor_registry.json`,
`data/world_state/components/` and
`data/world_state/admission_transactions/`; none is created in Migration Step
6. Separate files prevent unrelated dimension changes from rewriting one
large state object and allow validators to retain exact pre-state hashes.

## 1. Actor identity governance

### Decision: a reviewed Actor Registry is required for production identity

Production World State may reference only an `actor_id` admitted by a reviewed
Actor Registry contract. Proposal-local actor references remain valid for
Step 2–5 fixtures and proposals, but they cannot become durable production
identity merely through a World State admission.

The future registry is identity-only and append-only. An identity record may
contain:

- stable `actor_id` and canonical label;
- controlled `actor_type` such as `PERSON`, `OFFICE`, `INSTITUTION`, `STATE`,
  `MINISTRY`, `REGULATOR`, `CENTRAL_BANK`, `LEGISLATURE`, `COURT`,
  `MILITARY_COMMAND`, `ALLIANCE`, `MULTILATERAL_INSTITUTION`, `CORPORATION`
  or `NON_STATE_ORGANISATION`;
- jurisdiction and aliases;
- parent/child institutional relationships;
- office or organisation association;
- supported effective dates;
- identity provenance, review state and identity-revision history.

The registry must not contain mutable beliefs, intentions, capabilities,
constraints, policy positions or implementation claims. Those are separate
temporal assertions with their own provenance and review. Alias similarity is
never identity equivalence. An unresolved identity is represented as
`UNKNOWN` or remains proposal-local; it is not auto-merged.

### Person, office, institution and state

`PERSON`, `OFFICE`, `INSTITUTION` and `STATE` are distinct identities. A
bounded membership/tenure relation connects a person to an office:

```text
PERSON --occupies [effective_at, ended_at, evidence]--> OFFICE
OFFICE --part_of [effective_at, evidence]--> INSTITUTION
INSTITUTION --jurisdiction/authority [effective_at, evidence]--> STATE
```

The office persists when its occupant changes. The institution's authority is
not inferred from the person's authority, and an office-holder's statement is
not an institutional decision. Membership corrections create new relationship
revisions; they do not destroy the historical person, office or institution.

## 2. Component model

World State production consists of independently reviewable components. A
component has a stable series identity and immutable revisions:

```text
ComponentSeries: stable component_id
ComponentRevision: component_id + revision_id + revision_number
```

Every revision contains `previous_revision_id` when it is not the initial
revision, a revision kind, review state, lifecycle state, temporal fields,
lineage, uncertainty, and a deterministic object hash. Revision numbers are
contiguous per series. An accepted revision is never edited or removed.

### Required v1 component families

1. **`DimensionAssessmentRevision`** — a reviewed qualitative assessment of
   one controlled World State dimension and explicit scope.
2. **`ActorStateAssertionRevision`** — a time-varying claim about a governed
   actor's role, capability, constraint, incentive, commitment, channel or
   institutional relation.
3. **`ImplementationClaimRevision`** — a proposition classified separately as
   `SAID`, `DECIDED`, `AUTHORISED`, `IMPLEMENTED` or `OBSERVED`.
4. **`BaselineRevision`** — a reusable, explicit comparison basis.
5. **`NegativeEvidenceRevision`** — a bounded search finding, never inferred
   from absence or source failure.
6. **`CompetingHypothesisRevision`** — an explicit set of alternatives that
   keeps support, contradiction, assumptions and falsifiers visible.
7. **`ModelDisagreementRevision`** — a record of materially different model or
   analytical-lens outputs, distinct from factual evidence.

### Anomaly ownership

Anomaly is a subordinate comparison result in a
`DimensionAssessmentRevision` or other component that declares its subject.
It is not a new Signal, Risk, Forecast or causal claim. A reusable baseline is
separate because several assessments may reference it; an anomaly receives a
stable local `anomaly_id` and revision lineage only when it is independently
reviewed or reused. Otherwise it remains embedded in the owning assessment.
This is the smallest design that preserves reproducibility without creating a
second anomaly admission system.

### Minimum DimensionAssessmentRevision contract

The future machine-readable contract must support:

```text
DimensionAssessmentRevision {
  assessment_series_id,
  revision_id,
  revision_number,
  previous_revision_id,
  revision_kind,
  dimension,
  scope: {jurisdictions, systems, boundaries},
  effective_at,
  known_at_utc,
  reviewed_at_utc,
  admitted_at_utc,
  state_label,
  direction: optional or UNKNOWN,
  persistence: optional or NOT_ASSESSED,
  breadth: optional or NOT_ASSESSED,
  supporting_refs,
  contradictory_refs,
  uncertainty_refs,
  baseline_ref,
  anomaly_refs,
  prior_revision_ref,
  transition_type,
  reviewer,
  source_proposal_id,
  source_manifest_sha256,
  review_transaction_id,
  admission_transaction_id,
  lifecycle_state,
  visibility,
  revision_reason,
  object_sha256
}
```

`dimension` uses the ten existing controlled dimensions. State labels remain
dimension-specific qualitative labels. `direction`, `persistence` and
`breadth` are optional because evidence may not support them. `UNKNOWN` and
`NOT_ASSESSED` are valid values. A universal severity, pressure or world-risk
score is prohibited.

The same temporal and lineage requirements apply to the other component
families, with only fields meaningful to that family required. No component
may use narrative alone as provenance.

Market sensing is not a new component family in this contract. Instrument,
venue, timestamp/precision, baseline or counterfactual, measurement method,
horizon, liquidity/coverage caveat, alternative explanation and rights
evidence remain governed by Live Intelligence or Analysis. World State may
reference an eligible market observation or reviewed Analysis measurement in a
component, but co-movement never becomes causality and no World State admission
creates a market feed.

Implementation claims retain the explicit ladder
`SAID → DECIDED → AUTHORISED → IMPLEMENTED → OBSERVED`. Each state is a
separately evidenced classification; no state implies the next. A statement by
a person cannot establish an institutional decision, an institutional decision
cannot establish authorisation, and authorisation cannot establish operation
or observed effect. Narrowing, reversal, failure and contradiction create new
claims or revisions while preserving the earlier claim.

## 3. Identity and revision semantics

Component identity is separate from claim content. A revised claim retains its
stable series ID and receives a new immutable revision ID. A revision ID is
never reused. The full prior object remains available, and the successor
declares its predecessor.

Recommended controlled revision kinds are:

`INITIAL`, `UPDATE`, `CORRECTION`, `SUPERSESSION`, `WITHDRAWAL`, `EXPIRY`.

The exact vocabulary may vary by component where false equivalence would be
misleading, but every change must state what changed, why, who reviewed it,
and which earlier revision it preserves or supersedes. Administrative
metadata corrections must not silently alter substantive content. A correction
retains the original evidence cutoff and adds a new known/reviewed/admitted
time; it never backdates knowledge.

`SUPERSEDED`, `CORRECTED`, `WITHDRAWN` and `EXPIRED` are historical states,
not deletion commands. A withdrawn or expired component remains queryable as
history and is excluded from an active snapshot only by explicit lifecycle
semantics.

## 4. Three-time and as-of semantics

Every production claim distinguishes:

- **`effective_at`** — when the assessed condition applies, with supported
  precision only;
- **`known_at_utc`** — the earliest time WORLD SIGNALS had admissible evidence
  supporting the claim;
- **`reviewed_at_utc` / `admitted_at_utc`** — when human review and production
  admission occurred.

These times obey `known_at <= reviewed_at <= admitted_at` when all are present.
An event discovered later may have an earlier effective date, but it cannot
appear in a historical knowledge query before its known/admitted time. No
later evidence may strengthen an earlier assessment.

The production query contract must not overload one timestamp:

```text
WorldStateHistoryQuery {
  query_mode: KNOWLEDGE_AS_OF | EFFECTIVE_AS_OF,
  knowledge_cutoff_utc: exact UTC,
  effective_as_of_utc: exact UTC, // required for EFFECTIVE_AS_OF
  scope,
  include_withdrawn_history: boolean
}
```

`KNOWLEDGE_AS_OF` selects revisions admitted and supported by the knowledge
cutoff. `EFFECTIVE_AS_OF` selects only revisions whose effective time is at or
before the requested effective time and whose evidence and admission were
available by the declared knowledge cutoff. A caller must state which view it
wants; there is no implicit “latest”. Existing upstream helpers remain
authoritative for Signal, Relationship, Risk, Scenario, Forecast and Outcome
selection.

## 5. Snapshot contract

### Decision: snapshots are immutable indexes, not copies

`WorldStateSnapshotRevision` is a composition record containing exact
component references. It does not copy component content into one mutable
document.

```text
WorldStateSnapshotRevision {
  snapshot_series_id,
  snapshot_revision_id,
  revision_number,
  previous_snapshot_revision_id,
  snapshot_kind,
  scope,
  knowledge_cutoff_utc,
  effective_as_of_utc,
  component_refs: [{component_type, component_id, revision_id, object_sha256}],
  upstream_refs: [{layer, object_id, revision_id, object_sha256}],
  source_manifest_sha256,
  proposal_id,
  review_transaction_id,
  admission_transaction_id,
  limitations,
  empty_queried_domains,
  lifecycle_state,
  visibility,
  reviewer,
  admitted_at_utc,
  object_sha256
}
```

A snapshot can legitimately omit a dimension. It must distinguish unqueried,
queried-but-empty, unsupported and `UNKNOWN`. A snapshot containing no
Forecast or Outcome remains valid. Existing Signal, Relationship, Risk,
Scenario, Forecast and Outcome references are exact immutable references, not
copied claims; their own contracts retain authority.

The same snapshot series can therefore evolve compositionally:

```text
Snapshot 10: Growth D7, Energy D12, Conflict D4
Snapshot 11: Growth D7, Energy D13, Conflict D4
```

The new snapshot revision changes only the Energy reference. Snapshot 10 is
not rewritten and unrelated dimensions are not silently reassessed.

## 6. Admission transaction and partial admission

### Decision: production admission is a separate atomic transaction

The future transaction type is exactly distinct from Step 5:

`WORLD_STATE_PRODUCTION_ADMISSION`

It must pin:

- candidate/proposal ID and semantic fingerprint;
- source-manifest and retained component fingerprints;
- reviewer and decision times;
- exact component revision IDs admitted;
- component dispositions: `ADMITTED`, `REJECTED`, `DEFERRED`;
- rejected/deferred reasons and contradiction handling;
- snapshot revision identity;
- write targets and pre/post governed hashes;
- visibility/public-eligibility decision;
- admission timestamp and validator version.

Admission is fail-closed and atomic: all intended writes are prepared against
the declared pre-state and committed only if every hash, native validator,
revision reference and transaction field still matches. A failed transaction
leaves all governed layers unchanged.

### Decision: partial admission is allowed at component level

A multidisciplinary proposal may admit a macro Dimension Assessment while
returning an actor-authority assertion and deferring a conflict assessment.
The transaction must explicitly record all three dispositions. A rejected or
deferred component cannot be silently included through the snapshot, and an
accepted component cannot imply acceptance of a related component or upstream
layer. Existing Signal, Relationship, Risk, Scenario, Forecast and Outcome
admissions remain separate transactions under their native contracts.

Step 5's accepted consistency proposal cannot satisfy this transaction because
it has no production component revisions and no production write targets.

## 7. Ownership of Relationships, hypotheses and baselines

### Transmission ownership

The existing governed Relationship contract owns production transmission
semantics. A proposed World State edge becomes a Relationship revision when
its endpoints, class, directionality, mechanism, alternatives, contradiction,
lag and review requirements fit that contract. The Relationship schema should
be extended in a later bounded tranche if `FLOW`, `CHOKEPOINT` or `EXPOSURE`
are needed; they must not be duplicated as a second production graph.

World State may retain a proposal-local `transmission_candidate` during
analysis, but no production World State transmission component is admitted in
v1. Graph proximity, A→B→C traversal and correlation never create A→C or a
causal Relationship.

### Hypothesis ownership

Analysis remains the factual/evidentiary substrate. World State owns a reviewed
`CompetingHypothesisRevision` when the hypothesis is a synthesis-level
interpretation needed to compare dimensions, actors or transmission paths.
It references Analysis reviews/evidence and upstream revisions but is not a
Signal, Relationship, Scenario or Forecast. `REVIEWED_PREFERRED` is a human
disposition, not automatic ranking; alternatives, contradictions, assumptions
and falsifiers remain retained.

### Baseline and anomaly ownership

`BaselineRevision` is reusable and independently hash-pinned. Anomalies remain
subordinate comparison results unless a later design demonstrates a need for
independent reuse. Neither is allowed to create a Signal, Risk, Scenario or
Forecast automatically. A baseline is explicit, compatible and time-bounded;
otherwise the result is `EXPLICIT_NO_BASELINE`, not a fabricated anomaly.

## 8. Evidence lineage and model provenance

Every admitted component and snapshot must trace to:

1. `source_proposal_id` and proposal semantic fingerprint;
2. source-manifest SHA-256 and exact governed layer/object/revision pins;
3. evidence object hashes and supporting/contradictory reference sets;
4. native upstream review/admission transactions;
5. World State review transaction and production admission transaction;
6. reviewer identity, role, decision basis and timestamps.

Where a model or LLM contributes a proposal, retain model family/identity,
version or unavailable-version marker, configuration, analytical lens,
prompt/procedure or pipeline version, generation time, input manifest and
output fingerprint. Model output is an interpretation and never an
independent factual source or corroboration. No external model vendor is an
architectural dependency; a missing model registry record blocks admission of
model-derived claims or records the model provenance as unresolved.

## 9. Uncertainty and negative evidence

Typed uncertainty remains mandatory:
`PROVENANCE_SOURCE`, `MEASUREMENT`, `TEMPORAL`, `INTERPRETIVE`, `MODEL`,
`ACTOR_INTENT` and `INSTITUTIONAL_AUTHORITY`. Qualitative confidence is
permitted only with structured reasons; a universal numerical confidence or
world-risk score is prohibited. Probability is used only for a proposition
that is genuinely probabilistic and contractually defined.

`NegativeEvidenceRevision` admission requires:

- expected observable indicator or institutional action;
- bounded source/search scope and relevant time window;
- source-health and coverage/completeness assessment;
- rationale for why absence is informative;
- limitations, uncertainty and review status;
- explicit distinction between source failure, unqueried sources and no
  observed indicator.

`No record found` alone fails admission. A negative-evidence revision does not
prove absence and does not automatically weaken a competing hypothesis without
the explicit reviewed interpretation.

## 10. Private/public boundary and projections

### Decision: internal/private is the default

Every production component and snapshot begins as `INTERNAL_ONLY`. Admission
does not imply publication. Visibility transitions are explicit:

`INTERNAL_ONLY → PUBLIC_ELIGIBLE → PUBLIC_PROJECTED`

`PUBLIC_ELIGIBLE` is an allowlist decision, not a promise that a projection
exists. `PUBLIC_PROJECTED` is recorded only by a separate projection
transaction. Private evidence, actor-sensitive details, search coverage,
model prompts and restricted source locators never become public merely
because a high-level assessment is eligible.

Future projections may use:

| Surface | Potentially eligible fields |
| --- | --- |
| WORLD STATE | reviewed dimension label, material change, high-level explanation, typed uncertainty and citations from an allowlist |
| OUTLOOK | reviewed scenarios, conditional signposts and prospective Forecast references |
| CALENDAR | governed scheduled events and deliberately publishable next events |
| MAP | reviewed, public-eligible Relationship/transmission structure only |
| RESEARCH | methods, public provenance, source citations and revision history |

Projection code must select an allowlisted public view, not strip fields from
the private object opportunistically. Citations must label the epistemic class
of each item: factual source, reviewed Signal, inferred Relationship,
hypothesis, Scenario or Forecast. A citation cannot make an inference appear
to be a source fact.

## 11. Retention and corrections

Production history is append-only and retained for audit, as-of reconstruction
and future calibration. Normal retention includes:

- all admitted component and snapshot revisions;
- accepted, rejected and deferred admission transactions;
- proposals and review transactions referenced by admitted objects;
- withdrawn, corrected, expired and superseded objects;
- source manifests, evidence hashes and model-provenance records;
- public-eligibility and projection transactions.

Deletion is not a correction semantic. If privacy, legal or source-rights
constraints require removing payload material, a separately reviewed retention
exception must preserve the object ID, revision identity, hash, redaction
reason, authority, time and lineage tombstone. The analytical history must
remain distinguishable from the unavailable payload.

## 12. Canonical historical dependency

The existing Canonical contract does not provide a general executable
historical selector for mixed-precision `status_history`. Migration Step 6
does not manufacture UTC precision or solve that contract indirectly.

A separate Canonical historical-selector tranche is required before a World
State component may make a historical Canonical claim that depends on precise
status history. Until then, World State may reference current Canonical context
under the Step 3 limitation, or explicitly record the historical Canonical
domain as unsupported. This dependency does not block World State components
whose lineage is fully supported by Live, Analysis and reviewed downstream
contracts.

## 13. First production admission gate

The first actual World State component may be admitted only when all of the
following hold:

1. the scope and component type are explicit and narrow;
2. every factual input is governed, eligible and pinned to exact revisions;
3. effective, known, reviewed and admitted times are valid and non-backdating;
4. supporting and contradictory references are disjoint and inspected;
5. typed uncertainty, unknowns, alternatives and limitations are retained;
6. the relevant native validators pass and no duplicate Relationship semantics
   are introduced;
7. the proposal and model provenance are complete or the model-derived claim
   is excluded;
8. a human review transaction records component dispositions;
9. a separate `WORLD_STATE_PRODUCTION_ADMISSION` transaction pins the exact
   pre-state, post-state, write targets and visibility decision;
10. the atomic write simulation passes without mutating upstream inputs.

No population quota, universal score or complete ten-dimension coverage is a
gate. If any criterion fails, admission fails closed.

## 14. Recommended first pilot dimension

The first pilot should be a narrow
`HEALTH_BIOSECURITY` Dimension Assessment scoped to the existing DRC
Bundibugyo observation/Signal specimen, subject to a fresh Step 7 review. This
is preferable to a conflict or geopolitical pilot because the repository
already contains two time-separated governed observations, an admitted Signal
with explicit baseline and shared-origin limitations, and a bounded factual
proposition. It can test effective/known/admitted time, contradiction and
typed uncertainty without requiring ambiguous actor authority or a new market
feed. The pilot must not be admitted in Step 6 and must not imply a general
health-risk score or causal claim.

## 15. Exact Migration Step 7 boundary

Step 7 should implement, in a fresh bounded tranche:

- unpopulated machine-readable schemas and native validators for the Actor
  Registry, component revisions, snapshots and production admission
  transaction;
- test-only synthetic fixtures for person/office/institution/state identity,
  component revisions, corrections, partial admission and both as-of modes;
- a read-only admission simulator that writes only temporary copies and proves
  pre-state hashes are unchanged on success or failure;
- exact references to existing Signal, Relationship, Risk, Scenario, Forecast,
  Outcome and Evaluation revisions without copying or mutating them;
- private/public allowlist validation and citation epistemic-class checks;
- a negative test for duplicate transmission semantics and a separate
  dependency check for Canonical historical selection.

Step 7 must not admit the DRC pilot, create a broad Actor Registry, create
`data/world_state/state.json`, publish a World State page, alter existing
governed populations, run a new OSINT sweep or implement synthesis reasoning.
Step 8 is the later human-reviewed first-component admission decision after
Step 7's executable contract is green.

## Required Step 7 test matrix

The implementation tranche must prove at least:

- immutable component and snapshot revisions, contiguous numbers and retained
  predecessors;
- separate person, office, institution and state identities with bounded
  tenure;
- effective/known/reviewed/admitted time and no hindsight leakage;
- `KNOWLEDGE_AS_OF` versus `EFFECTIVE_AS_OF` selection;
- correction, supersession, withdrawal and expiry without destructive edits;
- partial admission and explicit rejected/deferred component exclusion;
- exact component/upstream references and manifest hashes;
- Signal/Relationship/Risk/Scenario/Forecast/Outcome ownership without
  duplicate graph or forecast semantics;
- hypothesis, model disagreement, baseline, anomaly and negative-evidence
  boundaries;
- typed uncertainty and valid `UNKNOWN`/`NOT_ASSESSED` values;
- internal-only default, allowlisted public eligibility and private-field
  exclusion;
- admission transaction atomicity, no upstream mutation and no public output;
- Canonical historical limitation and explicit unsupported result;
- reproducibility of proposal, admission and snapshot fingerprints.

## Consequences and limitations

This decision makes production history auditable without creating a second
observation store or a monolithic mutable World State file. It permits
incremental, component-level progress and preserves honest emptiness. It adds
the cost of an Actor Registry, component admission transactions and explicit
projection allowlists before production convenience is available.

The first pilot remains conditional on Step 7. Canonical historical
reconstruction remains a separate dependency. Relationships currently have a
zero production population and may need a bounded schema extension for flow
and chokepoint semantics; until then World State cannot admit a duplicate
transmission graph. No production World State object exists as a result of
this design record.
