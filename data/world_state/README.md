# World State production contract schemas

This directory contains the Migration Step 7 contract schemas and the
componentized production-history population. It now contains five admitted
internal components across three independent snapshot series: the original
three Dimension Assessments, one historical climate `BASELINE`, and one
completed-season `CLIMATE_PHYSICAL_RISK` Dimension Assessment. It does not
contain a monolithic `state.json`, an Actor Registry population or a public
projection.

Step 11A adds a retained, non-governed RBNZ Analysis specimen under
`data/world_state_audit/`. Its two narrow Dimension Assessment candidates and
proposal-local central-bank identity remain review-pending. The executable
`WORLD_STATE_ACTOR_IDENTITY_ADMISSION` boundary is identity-only and manual-
review-gated; it does not open Actor Registry population or admit actor claims.

Step 11A.1 adds only a corrected successor audit artifact. It does not rewrite
the original specimen or admit production state. Unknown institutional
effective-from is explicit and separate from identity-known-at; source-reported
market windows use the existing civil-date read precision rather than an
invented exact movement timestamp.

Step 11B admits two corrected RBNZ Dimension Assessment rows and an independent
RBNZ snapshot under separate retained human-review and production-admission
transactions. The actor identity remains deferred and the Actor Registry stays
empty. The existing Health history is preserved; mixed temporal precision and
the market sensor's non-causal association remain explicit. No public projection
or global World State snapshot is created.

Step 11C adds read-only current-applicability semantics. `ACTIVE` is lifecycle
state, not present-tense truth. Health uses its governed freshness policy;
components without such a policy, including the RBNZ assessments, return
`NO_CURRENTNESS_CLAIM` rather than being treated as permanently current.

Step 14C admits the climate Baseline and Dimension as historical internal
state. Their immutable lifecycle is `EXPIRED`, and reads derive
`HISTORICAL_ONLY`; this is distinct from `NO_CURRENTNESS_CLAIM` and is not a
review-required or current-use claim. Step 14C also records the separate
manual-only Treasury source admission and recovered IGR Canonical occurrence
outside this directory. No IGR Analysis, Signal, Forecast, Scenario, Risk,
Relationship or World State object is created by that recovery.

The production history is split across `components.json`, `snapshots.json` and
`admission_transactions.json`. Test data belongs under
`tests/fixtures/world_state_production_v1/` and must not be copied here.
