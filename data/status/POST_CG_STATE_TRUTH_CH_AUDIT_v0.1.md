# WORLD SIGNALS — post-CG state-truth hardening audit CH v0.1

**Reference date:** 2026-09-10  
**Post-CG merge commit:** `9b179878785669b61290ed482e2d234ab8665afd`  
**CH exact repaired `main` base:** `f3415e7c748957fadec4d1665b032167fd067a03`  
**Branch:** `feature/post-cg-state-truth-ch`

## 1. Why CH was selected

The first post-CG pressure review did not mechanically choose the next lowest count.

A second production Live Intelligence → Analysis relationship is not presently a valid immediate target merely because production `live_inputs` remains at one. The newly added CG BARMM observation links `CONTEXT_FOR` the 14 September 2026 BARMM election occurrence, which remains pre-event. The current Analysis contract is post-event and requires reviewed Analysis packets to resolve to an existing `COMPLETED` Canonical occurrence. Forcing the BARMM observation into Analysis now would violate the layer contract.

The NOAA/NHC Atlantic-season Monitor pilot remains a legitimate future activation candidate, but CF deliberately stopped at `PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT`. Activation still requires a fresh source, rights, endpoint, scope and pressure decision.

The more immediate cross-layer governance defect was the repository's own recovery surface. `PROJECT_STATUS.md`, `README.md` and `ROADMAP.md` materially lagged governed state: they still described older Monitor, Live and Analysis populations and older architectural boundaries. Because these files are explicitly used for recovery and continuation, that drift could contaminate future pressure selection even while the underlying governed registries remained correct.

CH therefore fixes recovery-state truth before adding another governed population increment.

## 2. OPEC exclusion

The quarantined CE OPEC transaction is explicitly excluded from CH candidate selection and implementation.

CH does not reopen, merge, cherry-pick, rebase, materialise or use PR #113 / `feature/post-cd-pressure-audit-ce` as a base. `OPEC_QUARANTINE.md` remains governing historical evidence and OPEC provenance debt remains non-blocking for unrelated work.

The CH state snapshot checks only that the quarantine record remains present. It does not interpret unresolved OPEC debt as a current work queue.

## 3. CH architecture

CH introduces a derived noncanonical recovery-state surface:

- `data/status/current_state.json`;
- `scripts/project_state_snapshot.py`;
- identical marked current-state blocks in `README.md`, `PROJECT_STATUS.md` and `ROADMAP.md`;
- a permanent regression suite in `tests/test_project_state_snapshot_ch.py`;
- an ordinary CI gate that runs `python scripts/project_state_snapshot.py --check`.

The snapshot is derived from governed Canonical, Source, Change Ledger, Monitor, Live Intelligence and Analysis files plus bounded overlay/readiness contracts. It is not itself Canonical state, Calendar state, Monitor runtime evidence, Live Intelligence or Analysis.

The script's normal `--check` path is read-only. A deliberate refresh requires both `--write` and `WORLD_SIGNALS_WRITE_DERIVED_STATE=YES`, and is restricted to:

- `data/status/current_state.json`;
- the marked current-state block in `README.md`;
- the marked current-state block in `PROJECT_STATUS.md`;
- the marked current-state block in `ROADMAP.md`.

It has no authority to mutate upstream governed datasets.

## 4. Derived state at the CH boundary

Expected exact derived state from repaired post-CG `main`:

- Canonical Registry `v0.41 / 689`; schema `v0.52`;
- Source Registry `v2.02 / 257`;
- Change Ledger `v0.27 / 62`;
- biosecurity overlay `v0.16 @ Canonical v0.41 / 689`;
- Monitor expectations `v0.27 / 25 configured adapters`;
- 24 unique configured Monitor sources;
- 215 explicitly scoped Canonical occurrences;
- Live Intelligence `v0.7 / 7 observations / 10 evidence`;
- 2 Canonical-linked Live observations covering 2 Canonical occurrences;
- Analysis schema `v0.8`;
- Analysis reviews `v0.18 / 22`;
- Analysis evidence `v0.18 / 97`;
- production Live→Analysis inputs: `1`;
- production Analysis revisions: `1`;
- NHC Atlantic pilot verdict `PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT` and not registered in scheduled Monitor expectations;
- automatic Canonical commit OFF;
- Google Calendar writes OFF;
- automatic Live ingestion OFF;
- public Live observation projection OFF;
- public Live-input projection OFF;
- public Analysis revision metadata/latest-head selection OFF.

The derived state deliberately does not claim current Monitor source health or latest runtime candidate state. Those are dated operational evidence, not static recovery truth.

## 5. Protected governed layers

CH must leave the following byte-identical to its exact repaired `main` base:

- `data/canonical/registry.json`;
- `data/canonical/schema.json`;
- `data/sources/registry.json`;
- `data/changes/ledger.json`;
- `data/coverage/biosecurity_overlay.json`;
- `data/monitor/expectations.json`;
- `data/monitor/operations_policy.json`;
- `data/live_intelligence/schema.json`;
- `data/live_intelligence/observations.json`;
- `data/live_intelligence/evidence_registry.json`;
- `data/analysis/schema.json`;
- `data/analysis/event_reviews.json`;
- `data/analysis/evidence_registry.json`;
- `OPEC_QUARANTINE.md`;
- `tests/test_opec_quarantine_cf.py`.

CH changes no event identity, occurrence time, lifecycle, certainty, source rights status, monitor route population, Live observation/evidence population or Analysis review/evidence population.

## 6. Branch-initialisation incident — preserved, not hidden

Before the CH feature branch existed, an empty `data/status/.gitkeep` was accidentally written directly to `main`:

- accidental commit: `f3d044505299b82f653a630f6aa8d56a0bb56d44`;
- immediate restoration commit: `f3415e7c748957fadec4d1665b032167fd067a03`.

The file contained no data and no governed or contract file was touched. The second commit deleted it, restoring the post-CG repository tree before CH implementation began. CH then branched from the repaired `main` commit `f3415e7c748957fadec4d1665b032167fd067a03`.

This is an operational-control failure rather than a governed-state mutation. It is recorded permanently because failure history is evidence. The procedural lesson is simple: create the feature branch before the first contents write.

## 7. CI and regression contract

CH adds mechanical checks that fail when:

- the checked-in snapshot differs from a fresh derivation of governed files;
- any of the three marked current-state blocks differs from the derived state;
- NHC is silently registered into Monitor expectations while the snapshot still claims pilot-only status;
- core write/public projection gates unexpectedly open;
- OPEC quarantine record disappears;
- known current counts regress or stale pre-CG counts return.

The tests intentionally distinguish the derived recovery surface from governed truth. The correct repair for future drift is to regenerate the derived surface after a reviewed governed change, not to edit governed files to satisfy documentation.

## 8. Validation history

Preflight and ordinary PR CI evidence will be appended here before merge handoff. Any failed validation run is to be retained with run/job identity, failure cause, whether any commit/write gate existed, and the repair made.

At this authoring boundary no CH workflow has authority to mutate Canonical, Source, Change Ledger, Monitor, Live or Analysis state.
