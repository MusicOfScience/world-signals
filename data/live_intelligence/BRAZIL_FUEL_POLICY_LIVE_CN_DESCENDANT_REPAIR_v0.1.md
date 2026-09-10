# WORLD SIGNALS — Brazil fuel-policy Live CN descendant repair v0.1

**Status:** FAILED RUN PRESERVED / NARROW DESCENDANT REPAIR  
**Reference date:** 2026-09-10  
**Exact post-CM base:** `9386114de527b117987058cb1b9cd98066dab8e4`  
**CN branch pre-run head:** `f0387cf0b23ce657e6442807d2646c80899d0708`

## Failed guarded run

- workflow: `CN Brazil fuel-policy Live guarded transaction`;
- run: `34446405883`;
- job: `102772043248`;
- conclusion: **FAILURE**;
- transaction behaviour: **fail closed** — no ephemeral governed Live materialisation was committed or pushed.

The run successfully completed the exact-base gate, protected-layer/existing-Live snapshots, CN simulation, focused CN contract tests, ephemeral materialisation, derived recovery-state refresh, CN materialisation verification, Canonical validator, Live validator, Analysis validator and derived-state check. It then stopped at the complete historical suite. Python compilation, JavaScript syntax checks, static build, protected-layer/row-invariance proof, temporary-machinery removal and transaction commit were therefore skipped.

Ephemeral CN state before the historical-suite failure was internally valid:

- Live schema `0.10`;
- 9 Live observations;
- 12 Live evidence rows;
- the CN Brazil observation retained zero Canonical links;
- automatic Canonical commit remained false;
- Google Calendar write remained false;
- Canonical validator passed at 689 occurrences;
- Live validator passed at `0.10 / 9 / 12`;
- Analysis validator passed at 22 reviews / 97 evidence;
- derived-state consistency passed;
- the 12 focused CN tests passed.

## Failure diagnosis

The complete historical suite ran 1,288 tests and reported exactly three failures with 68 historical-prestate skips. None is a Brazil payload or governed-validator failure.

### 1. CM current-state coupling

`tests/test_live_correction_conflict_cm.py::LiveCorrectionConflictCMTests::test_cm_is_no_population_contract_descendant`

The test asserted that the *current* Live stores must remain exactly schema/data version `0.9`, 8 observations and 11 evidence rows. Those numbers are the correct frozen CM checkpoint, but they are not a permanent ceiling on reviewed descendants. CN legitimately advances current Live state to `0.10 / 9 / 12` while preserving the CM correction/conflict policy and `cm_checkpoint` exactly.

Repair rule: keep the historical `cm_checkpoint` assertions exact (`0.9 / 8 / 11`, exact CM base SHA), but make current-store assertions descendant-safe: dotted version at least `0.9`, populations at least 8/11, current policy ceilings at least the current population, and the eight CM observation identities must remain a subset rather than the entire current population.

### 2–3. AW dotted-version parsing bug

`tests/test_nepal_rasuwa_flood_live_intelligence_aw.py` failures:

- `test_target_is_v02_one_observation_two_evidence_rows`;
- `test_public_projection_reports_curated_internal_store_but_zero_public_observations`.

Both use `float(...)` for dotted semantic-ish repository versions. Python evaluates `float("0.10")` as numeric `0.1`, which is incorrectly less than `0.2`. This makes a legitimate later Live version fail an old v0.2 floor assertion.

Repair rule: compare dotted numeric components, e.g. `tuple(int(part) for part in str(value).split(".")) >= (0, 2)`. Do not alter AW's frozen historical base, payload, first-observation identity, time semantics or v0.2 checkpoint facts.

## Boundaries

This repair may change only the descendant-sensitive assertions above plus the CN transaction trigger needed to rerun the guarded transaction. It must not:

- alter any CM research, plan, transaction audit or `cm_checkpoint` historical facts;
- weaken `correction_conflict_policy`;
- alter the Nepal AW payload, time semantics, source facts or historical v0.2 target;
- mutate Canonical, Source Registry, Change Ledger, Monitor or Analysis governed data;
- touch `OPEC_QUARANTINE.md`, `tests/test_opec_quarantine_cf.py`, PR #113 or the quarantined CE branch;
- authorize any automatic ingestion, Canonical commit, Calendar write or public Live projection.

A second guarded CN transaction must start only while `origin/main` remains exact `9386114de527b117987058cb1b9cd98066dab8e4`. The first failed run remains part of the permanent audit trail.
