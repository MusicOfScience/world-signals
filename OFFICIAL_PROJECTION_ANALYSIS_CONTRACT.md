# Native official-projection Analysis contract — Step 14E

## Step 14F adoption / object-publication gate

The original contract-only tranche below is preserved as design history.
Step 14F separately admits the owner-reviewed IGR copy internally under schema
0.9; retained Step 14D artifacts remain immutable. The official inventory/audit
is governed internal Analysis, not future actuals or a Forecast. The independent
backtest is DEFERRED; qualified historical checks remain supporting only and
dependency edges remain INTERNAL_MODEL_STRUCTURE, never Relationships.

`event_reviews.json.publication_decisions` is the sole review-level publication
authority. Every production review must have exactly one PUBLIC / INTERNAL_ONLY
decision; absent, invalid or dangling entries block native production validation
and public builds. Draft in-memory native-extension checks do not grant population
or publication authority. Public projection always requires the decision table,
including for in-memory inputs, and also applies the existing field allowlist.
Public evidence and readiness use only public rows. The 22 legacy reviews remain
PUBLIC; IGR remains INTERNAL_ONLY. Dataset versions advance to 0.19, not the
schema. Human dispositions and pre/post hashes are separately retained in the
Step 14F audit records. Production admission and publication are distinct acts.

`scripts/admit_igr_internal_analysis.py --check` validates the retained admission
read-only. Construction requires the explicit owner decision and genuine UTC
review/admission times; `--write` uses the repository's staged bounded transaction
primitive with temporary-copy preflight and rollback, not an automatic admission
trigger. No retrieval, monitoring activation or downstream writes are available.

Status: **adopted contract only**. Schema 0.9 adds optional
`official_projection_review` contract 0.1. No IGR Analysis/evidence is admitted;
Step 14D artifacts remain immutable DRAFT / REVIEW_PENDING / INTERNAL_ONLY.
Validation is neither human acceptance nor production admission.

## Publication decision

`analysis_publication.FIELD_CLASSIFICATIONS` is the single executable top-level
publication authority for ordinary and revision-aware public projection.
Unknown keys fail native validation/build with
`UNCLASSIFIED_ANALYSIS_PUBLICATION_FIELD`, rather than leak or silently disappear.

PUBLIC: analysis_id, review_state, review_phase, analysis_as_of_utc,
canonical_occurrence_id, canonical_series_id, canonical_event_type,
canonical_institution, canonical_release_utc, scope, what_happened,
what_was_expected, what_surprised, what_moved, what_appears_connected,
what_may_be_noise, alternative_explanations, second_order_effects, falsifiers,
analytical_conclusion, canonical_mutation_prohibited, google_calendar_write.
Canonical context and existing allowlisted evidence metadata are generated
separately. Evidence selection uses the public spine, never internal asset refs.

INTERNAL_ONLY: official_projection_review, assumption_audit,
internal_dependency_map, internal_evidence_manifest, internal_review_notes,
candidate_dispositions, live_inputs, revision_of_analysis_id,
analysis_revision_kind, analysis_revision_reason. No additional tier exists.
Legacy nested public sections retain their established semantics: this policy
is not a generalized nested secret scanner. New internal structures must not be
embedded inside those public sections.

Migration preserves all 22 analytical spines and public evidence entries. Schema
metadata changes 0.8 → 0.9. One exposed `live_inputs` link on the Japan FIES review
is removed: that schema publication gate was already closed. This removes
internal linkage metadata, not public factual or analytical content. Revision
metadata and head collapse remain closed. Opening an internal field later needs
another deliberate publication contract.

## Native representation

The extension is generic to institutional model publications, not Treasury.
Required: contract_version, INTERNAL_ONLY visibility, projection_framework,
projection_outputs, model_assumptions, sensitivity_cases, assumption_audit,
comparison_baseline, limitations, source_manifest with exact hashes and manifest
fingerprint, and explicit corroboration/error policies. Every source ref resolves
an asset ID and page/table/chart locator; source families and private hashes stay
internal. Ordinary event reviews need no extension.

Classes: PUBLICATION_FACT, OBSERVED_EVIDENCE, MODEL_ASSUMPTION,
OFFICIAL_PROJECTION, SENSITIVITY_CASE, POLICY_CLAIM, PRIOR_OFFICIAL_PROJECTION.
Future projections, assumptions and sensitivities cannot enter actuals.
Publication/model metadata facts use PUBLICATION_FACT, not OFFICIAL_PROJECTION.
Validation cannot independently discover deliberate misclassification; human
review remains mandatory.

- Output: projection_id, metric, numeric / bounded lower–upper / qualitative
  value, unit, projection_horizon, reference_period, OFFICIAL_PROJECTION,
  source_refs, assumption_refs, optional sensitivity_refs/comparison_refs,
  limitations. Optional value_basis retains source real/nominal/price convention.
- Assumption: assumption_id/type, domain, statement, value_or_rule, unit,
  reference_period, projection_horizon, issuer_rationale, source_refs,
  output_dependencies, optional sensitivity_refs/limitations. basis_kind separates
  EMPIRICAL_EXTRAPOLATION, MAINTAINED_POLICY_SETTING, TECHNICAL_CONVENTION and
  CONDITIONAL_MODEL_MECHANISM. Policy closure is not empirical validation.
- Sensitivity: sensitivity_id, changed assumption_refs, source-native shock,
  unit (including per-input units), projection_horizon, results,
  affected_output_refs where inventoried, source_refs, limitations. Qualitative
  shocks stay qualitative. Probability and Scenario/Forecast identity are closed;
  source-provided probabilities require a separately reviewed representation.
- Periods: source-native string containing a year, ordered civil-date range, or
  explicit `{source_native_period: ...}` description. No fabricated UTC precision
  is required for fiscal years or model-relative windows.

IDs are distinct review-local identities. A later review uses existing immutable
Analysis revision governance; no model output becomes independent corroboration,
an Observation, Signal, World State, Forecast, Scenario or Outcome.

## Audit and comparisons

Each material assumption has one audit with exactly ten axes:
historical_plausibility, current_trajectory, structural_break_risk,
implementation_dependency, circularity_endogeneity, sensitivity,
downside_alternative, upside_alternative, signposts, revision_conditions.
Each has finding, source_refs and limitations. NOT_ESTABLISHED requires an
explanation. Recursive validation rejects score/rating/grade fields including
overall_score and assumption_quality_score. No numerical quality or global score.

Prior baseline preserves vintage, horizon and provenance. Optional
projection_comparison/historical_backtest rows carry comparison_id, prior/original
and current/observed vintages, horizons/periods, units, method_basis,
method_compatibility and DIRECTLY_COMPARABLE / QUALIFIED_COMPARISON /
NOT_DIRECTLY_COMPARABLE. Numeric error/difference requires calculation_basis and
finite correct arithmetic. Prior-projection subtraction needs matching horizons;
method_compatibility is COMPATIBLE / QUALIFIED / INCOMPATIBLE / NOT_ESTABLISHED;
the latter two block calculation, and direct comparisons require COMPATIBLE.
monetary subtraction needs explicitly equal prior/current value bases.
NOT_DIRECTLY_COMPARABLE prohibits both error and difference. Qualified
source-reported checks are not independent backtest acceptance. Model misses do
not establish bias, negligence, dishonesty or manipulation.

## Model dependencies

Optional internal dependency_map edges retain ID, exact local endpoints,
mechanism, sources, limitations, production_relationship=false. Classes:
MODEL_DEFINED, ASSUMED_MECHANISM, SENSITIVITY_SUPPORTED,
EXTERNAL_EVIDENCE_SUPPORTED, HYPOTHESISED. Self-cycles and undeclared cycles fail.
Explicit sourced MODEL_DEFINED feedback may be declared as closed node paths;
all edges must already exist. No transitive edge, Relationship or confidence
uplift is generated. Dependent outputs do not confirm their input independently.

## Read-only Step 14D compatibility

`step14d_native_extension()` verifies retained fingerprints and assembles the
hash-linked inventory/audit in memory. It renames projection_class →
epistemic_class, horizon → projection_horizon, reference_year → reference_period.
Relative source periods are wrapped, not resolved. Values, findings, limitations
and locators survive. Reverse sensitivity refs and comparison IDs are structural.
Matched-horizon revisions and source-reported checks become QUALIFIED_COMPARISON,
preserving original labels in source_comparability and method qualifications.
Existing explicit debt/interest feedback is declared without creating edges;
unassociated comparison refs remain empty. Native DRAFT validation does not
rewrite, re-seal, admit or publish any artifact.

Recommended dispositions remain unmaterialized: Analysis DEFER; inventory ACCEPT
as internal material; audit ACCEPT internally with unresolved coverage; independent
backtest DEFER; dependency map ACCEPT internally with no Relationship promotion.
Future admission requires separate human decisions. Public extension projection
also needs its own schema, rights and human publication review.

## Impact and tests

Only Analysis schema changes among governed contracts/data. Derived recovery
version metadata follows that bump, not an intelligence population write.
Analysis/evidence, Step 14D artifacts, source holds, all downstream populations,
Forecasts and public Brief remain unchanged. World State stays 5 components / 3
snapshots / 3 admissions / 0 actors, internal only. Tests cover native generic and
exact candidate material, refs/horizons/values, scores, bases, cycles, public
equivalence, tampering, revision policy and read-only hashes. Historical CD schema
assertions use a version floor while keeping the exact single-revision population
and every policy gate; schema evolution does not authorize another revision.
