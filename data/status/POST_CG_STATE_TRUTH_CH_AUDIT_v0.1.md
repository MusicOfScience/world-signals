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

## 8. Validation and failure history

Failure history was not squashed or hidden. GitHub Actions retains the unsuccessful CH branch runs alongside the final successful run. At final temporary-workflow retirement, 23 completed failed runs remained visible in Actions. They include iterative preflight failures, short-lived bounded repair harnesses used to correct descendant compatibility, and one final expected closeout-whitelist anomaly described below. The important failure classes were:

1. historical BA and AZ helpers treated obsolete recovery prose as if it were permanent governed state;
2. BD, BF and BG historical regressions likewise froze historical `PROJECT_STATUS.md` / `ROADMAP.md` bodies rather than their substantive historical contracts;
3. one BA repair attempt introduced an accidental helper-call/API mismatch, then a subsequent repair harness lost nested Python indentation before execution;
4. one successful focused BA repair was initially reported failed only because the harness expected an unstaged ` M` status while `git checkout origin/main -- file` left the intended helper change staged as `M `;
5. the BG/OPEC descendant test needed to recognise the current CH recovery surface without invoking quarantined OPEC transaction/materialisation machinery;
6. after the permanent audit closeout commit, temporary preflight run #18 / Actions run `34400466760` passed the exact-base assertion, governed/derived validators, all 1,228 repository tests, compilation and static build, then failed only in the temporary exact diff whitelist because that soon-to-be-retired workflow still expected `.github/workflows/ch-state-truth-preflight.yml` to appear among changed paths. The actual changed-path set already omitted that temporary workflow. This was a harness retirement mismatch, not a governed-state, validation, test or build failure. The workflow had `contents: read` only and no write authority, and it was deleted immediately afterward.

The full CH preflight workflow itself was read-only: it had `contents: read`, no commit gate and no authority to mutate repository state. Temporary write-capable repair workflows were deliberately narrow, branch-only and used only to commit the explicitly inspected helper/test repairs; they were deleted after use. None had authority to mutate the protected governed layers listed in §5. Their commits and failed/successful Action runs remain in branch history as evidence.

The repairs did **not** weaken the substantive contracts. Historical checkpoint fixtures, event identities, source/provenance assertions, population ceilings where genuinely contractual, write gates and OPEC quarantine all remain tested. The repair was to stop treating later recovery prose as a frozen descendant invariant.

### Final successful read-only preflight

- workflow: `CH state-truth preflight`;
- run number: `17`;
- Actions run ID: `34399941325`;
- branch head tested: `889fe053b238033ab062855621fe1a7e3b75af03`;
- exact base asserted: `f3415e7c748957fadec4d1665b032167fd067a03`;
- result: **PASS**.

The successful run established:

- Canonical validation: `689` occurrences PASS, with only the three pre-existing legacy/backfill `start_utc` warnings;
- Live Intelligence validation: schema `0.7`, `7` observations, `10` evidence PASS;
- Analysis validation: `22` reviews, `97` evidence, Live-input bridge and revision contract PASS;
- derived-state snapshot check PASS;
- 7 CH-specific state-truth tests PASS;
- 2 OPEC quarantine tests PASS;
- complete repository suite: **1,228 tests PASS, 68 skipped**;
- Python compilation PASS;
- JavaScript syntax checks PASS;
- static site build PASS for `689` events and `25` configured Monitor routes;
- byte identity PASS for every protected governed path in §5;
- bounded CH diff-path audit PASS.

The temporary `ch-state-truth-preflight.yml` workflow is a transaction/pre-merge verification artifact, not a permanent project capability. It is removed before PR handoff. Ordinary repository CI retains the permanent `python scripts/project_state_snapshot.py --check` regression gate.

## 9. Merge handoff condition

CH is eligible for merge handoff only after:

1. the temporary preflight workflow has been removed from the feature branch;
2. the PR is opened against the exact current `main` lineage;
3. ordinary PR CI, including the permanent derived-state check, completes successfully;
4. the PR diff confirms no protected governed path changed.

No merge is to be represented as complete until the user performs or confirms the merge.
