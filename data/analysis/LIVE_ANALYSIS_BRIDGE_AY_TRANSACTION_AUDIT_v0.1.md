# WORLD SIGNALS — Live Intelligence → Analysis bridge AY transaction audit v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `0a7608ab56116d0f65ffd1492a3da87bcbf35f47`  
**Transaction-start branch head:** `29ea3b6179713161566c327a73c4933207cfbe1f`  
**Transaction workflow run:** `34021849610`

## Decision

AY establishes the prospective Live Intelligence → Analysis input grammar while keeping production linkage closed. It does not add a Live observation, Analysis review, Analysis evidence row, Canonical occurrence, source, monitor adapter or market series.

## Preflight history

- Initial read-only preflight run `34021514723` failed closed only after ephemeral Analysis schema v0.5 exposed a stale AK live-descendant ceiling assertion.
- `EXACT_MARKET_MEASUREMENT_CONTRACT_AK_PLAN_v0.1.json` already records the same project rule: freeze the historical contract checkpoint, not legitimate later descendants.
- The narrow repair preserves AK's exact historical v0.3 → v0.4 transform path and every exact-market invariant; it merely exercises AK against unmodified live schemas v0.4 or later instead of treating v0.4 as a permanent maximum.
- Repaired read-only preflight run `34021715088` passed exact ancestry, untouched-descendant validation, ephemeral AY materialisation, the full suite, Python compilation, browser JavaScript checks, static build, exact mutation-boundary proof, protected-data proof, restoration and workflow self-removal.

## Materialised target

- Analysis schema: `v0.5`.
- Analysis reviews: `v0.16 / 20` unchanged.
- Analysis evidence: `v0.16 / 91` unchanged.
- Live Intelligence: schema `v0.3 / 3 observations / 4 evidence` unchanged.
- Canonical Registry: `v0.38 / 688` unchanged.
- production `live_inputs`: exactly `0`.
- production `EXACT_TIMESTAMP_SERIES`: exactly `0`.
- public Live-input projection: closed.
- automatic story expansion / latest-state selection: prohibited.

## Bridge invariants validated

1. Selection is by immutable Live `observation_id`, not `story_id`, `latest` or automatic story expansion.
2. Live inputs are distinct from Analysis evidence; Live evidence is not transitively migrated.
3. Analysis may not mutate or revise upstream Live observations through the relationship.
4. Analysis as-of time may not predate the selected Live observation's WORLD SIGNALS observation time.
5. One Live observation may support multiple analyses.
6. Evolving stories remain snapshot-specific; history requires explicit observation IDs.
7. Production population and public projection remain closed pending a later pressure audit.

## Exact transaction mutation boundary

Existing files materialised by the controlled transaction:

- `.github/workflows/ci.yml`
- `PROJECT_STATUS.md`
- `ROADMAP.md`
- `data/analysis/schema.json`
- `scripts/build_site.py`
- `scripts/validate_analysis.py`
- `tests/test_exact_market_measurement_contract_ak.py`

This transaction audit is the only new permanent file created by the transaction itself. AY planning, bridge implementation, deterministic helpers and regressions were already committed on the tranche branch before the controlled write.

## Protected datasets

SHA-256 equality against the transaction-start branch state was proved for Canonical registry/schema, Source Registry, Change Ledger, monitor expectations/operations policy, all Live Intelligence governed data/schema, and Analysis reviews/evidence. No protected governed dataset changed.

## Validation

The controlled target passed the registry, Live Intelligence and Analysis validators; full repository unittest discovery; Python compilation; standing browser JavaScript checks; static-site build; exact target-state assertions; the exact-series zero invariant; the zero-production-Live-input invariant; and protected-dataset hash equality.

The temporary transaction workflow removes itself after committing the reviewed target. Ordinary pull-request CI remains a separate post-transaction validation gate. Manual merge remains required.
