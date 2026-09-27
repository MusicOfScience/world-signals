# WORLD STATE v1 CURRENT-REPOSITORY CONSISTENCY PROPOSAL

**Status:** `REVIEW_PENDING`
**Package type:** `WORLD_STATE_CONSISTENCY_PROPOSAL`
**Production World State:** `false`
**Write targets:** `[]`
**Public projection permitted:** `false`

This is non-governed audit/review evidence. It is not a production World State record, admission transaction, analytical synthesis, briefing or public projection.

## Repository and cutoff

- Repository ref: `main`
- Repository SHA: `b36a598bd5ebf9663fe245a82dc1c262d1103b58`
- Knowledge cutoff: `2026-09-27T04:39:04Z`
- The cutoff is valid because it is no later than the selected repository snapshot commit time.
- Future cutoffs are rejected by the retention command; a later repository ref may be supplied for historical replay.

## Read result

- Queried jurisdictions: `["*"]`
- Queried dimensions: `["CLIMATE_PHYSICAL_RISK", "CONFLICT_MILITARY_ACTIVITY", "DEPENDENCIES_CHOKEPOINTS", "HEALTH_BIOSECURITY", "MACROECONOMIC_FINANCIAL_CONDITIONS", "MARKETS_AS_SENSORS", "POLITICAL_INSTITUTIONAL_STABILITY", "STRATEGIC_GEOPOLITICAL_TENSION", "TECHNOLOGY_CRITICAL_INFRASTRUCTURE", "TRADE_CAPITAL_ENERGY_FOOD_FLOWS"]`
- Selected counts: `{"analysis_evidence": 97, "analysis_reviews": 22, "canonical_context": 689, "forecasts": 4, "live_evidence": 16, "live_observations": 12, "outcomes": 0, "relationships": 0, "risks_regimes": 0, "scenarios": 0, "signals": 1}`
- Explicitly empty production layers: `["relationships", "risks_regimes", "scenarios", "outcomes"]`
- Forecast Evaluation: `NO_SAMPLE`

## Analytical boundary

No analytical inference was made. Actor assertions, implementation claims, dimension assessments, hypotheses, transmission edges, baselines, anomalies and production negative-evidence assertions remain empty.

- Analytical object counts: `{"actors": 0, "anomalies": 0, "baselines": 0, "dimension_assessments": 0, "hypotheses": 0, "implementation_claims": 0, "negative_evidence": 0, "transmission_edges": 0}`
- Limitations: `["CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED", "WORLD_STATE_ASSESSMENT_NOT_SYNTHESISED", "ACTOR_REGISTRY_UNAVAILABLE", "MARKET_FEED_NOT_INTRODUCED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "DIMENSION_ASSESSMENT_NOT_SUPPORTED", "NO_EXPLICIT_GOVERNED_NEGATIVE_EVIDENCE"]`

## Integrity and review

- Source manifest SHA-256: `10f7657331e1eee930a82dfb0ecf01c66e6e55420c87f95d8cf1c65bd9f54b8a`
- Retained hash-only manifest SHA-256: `3524b2eb8d8d843434ac83b2ce8b70b1ccc3f1f35828e1cca38ce0035f68e3bd`
- Semantic proposal fingerprint: `8d5161ca7e3fccdaf3a8d765a0c27bccb6340b465f61d6f8931f01488170bea2`
- Mutation check: `PASS`
- Review state: `REVIEW_PENDING`; Migration Step 5 has not been conducted.
- Reproducibility requires the same repository source state, request and governed objects.

## Retained files

- Machine-readable package: `data/world_state_audit/CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_PENDING.json`
- This review summary: `data/world_state_audit/CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_SUMMARY.md`

Reproduce with: `python3 scripts/retain_world_state_consistency_proposal.py --as-of 2026-09-27T04:39:04Z`
