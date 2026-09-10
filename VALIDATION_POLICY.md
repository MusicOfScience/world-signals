# WORLD SIGNALS — validation and compute policy

This policy is subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md` and complements `HANDOFF_PROTOCOL.md`. It governs **how validation is executed**, not what any project layer is allowed to write.

## Purpose

WORLD SIGNALS treats hosted CI capacity as a finite operational resource. Validation must remain fail-closed, exact-head and reproducible without multiplying hosted runners unnecessarily.

The governing design is:

1. one portable validation entry point: `scripts/validate_world_signals.py`;
2. one ordinary PR validation runner;
3. one fail-closed validation profile selected from the actual base/head tree difference;
4. coverage/pressure generation inside the same ordinary validation runner;
5. optional validation-only self-hosted execution without changing project-layer semantics;
6. no relaxation of Canonical, Calendar, Monitor, Live, Analysis or public-projection write gates.

A cheaper profile is **not** a weaker interpretation of a risky change. Unknown, mixed, executable, governed, deleted, renamed or operationally sensitive changes escalate to `FULL`.

## Profiles

### `FULL`

Required whenever the branch changes anything other than the narrowly defined safe-research surface, including:

- Python, JavaScript or web code;
- tests;
- GitHub Actions workflows;
- governed JSON or other machine-readable project state;
- Source Registry, Canonical Registry, Change Ledger, Monitor, Live Intelligence or Analysis data/contracts;
- top-level governance/recovery documents such as the Charter, architecture, roadmap, project status or handoff protocol;
- any deletion, rename or copy;
- any path the classifier does not explicitly recognise as safe research Markdown.

`FULL` runs the historical repository suite and preserves the pre-CR validation surface:

- Canonical validator;
- Live Intelligence validator;
- Analysis validator;
- derived project-state check;
- full unittest discovery;
- selected Python compilation checks;
- all seven browser JavaScript syntax checks;
- static site build;
- canonical/source coverage audit;
- cross-layer coverage/pressure audit.

The full suite remains the default for local/manual validation and for any classifier uncertainty.

### `SAFE_RESEARCH_DOCS`

Available only for a pull request whose **entire net diff** consists only of newly added regular UTF-8 Markdown blobs under `data/` whose filenames are explicitly research/audit surfaces containing one of:

- `_RESEARCH_`;
- `_AUDIT_`;
- `_PRESSURE_`;
- `_CLOSEOUT_`;
- `_DIAGNOSTIC_`.

The fast path rejects modifications to already-merged research records, deletions, renames, copies, executable file modes, non-Markdown files, top-level documents and unknown naming patterns. It also rejects a new research file if its exact path is already referenced by a tracked non-Markdown file. A rejected or unprovable surface escalates to `FULL`.

This append-only rule still permits normal drafting: a research file may be revised repeatedly on its feature branch and remains an `A`dded file relative to `main` until the PR merges.

The safe-research profile still validates the **actual PR head**. It runs:

- `git diff --check` against the exact PR base/head;
- Canonical, Live Intelligence and Analysis validators;
- derived project-state check;
- coverage/cross-layer regression tests;
- canonical/source coverage audit;
- cross-layer coverage/pressure audit.

It does not rebuy the full historical unittest suite, JavaScript checks or static build because the classifier has first proved that none of their executable or governed inputs changed.

A research document may describe a proposed write, but the profile itself has no write authority and cannot make that proposal operational.

### `POST_MERGE`

Used on `main` only when the validator can prove both:

1. the head is a conventional two-parent merge commit; and
2. the merge commit's tree is byte-identical to its second parent (the reviewed PR head).

This proves that the merge introduced no conflict-resolution or additional tree mutation beyond the already validated PR head. `POST_MERGE` reruns the governed validators, state check and coverage/pressure checks but does not rebuy the complete historical suite.

If parent history is unavailable, the commit is not a conventional merge, or tree equivalence cannot be proven, validation escalates to `FULL`.

## Workflow policy

`Validate WORLD SIGNALS` is the ordinary exact-head validation workflow. It:

- checks out the actual PR head rather than a synthetic merge ref;
- obtains the exact base SHA for classification;
- cancels obsolete in-progress runs for the same PR;
- pins Python 3.13 for every validation profile so hosted and self-hosted execution do not silently diverge;
- pins Node 24 only for `FULL`, where browser JavaScript syntax checks are required;
- runs coverage/pressure in the same job;
- uploads a compact validation summary and coverage evidence with 30-day retention.

The job defaults to `ubuntu-latest`. If the repository variable `WORLD_SIGNALS_VALIDATION_RUNNER` is set to a trusted self-hosted runner label, only the ordinary validation job is redirected to that runner. The daily Monitor and Pages deployment remain GitHub-hosted unless a later, separately reviewed operational tranche changes them.

The separate `Audit WORLD SIGNALS coverage` workflow remains available for **manual diagnostic use only**. It is no longer an automatic second runner on every relevant PR/main change.

The scheduled live monitor continues to run daily. Its regression tests run on code/configuration-triggered or manual executions, but not on every routine scheduled poll; ordinary repository CI is responsible for regression testing the monitor code before merge.

Pages deployment and the live-monitor schedule are intentionally not reduced by this tranche. They provide useful current operational output and should be optimised only from measured evidence, not merely because hosted minutes are finite.

## Self-hosted validation boundary

Self-hosting changes only **where the validator executes**. It does not alter:

- the validation profile selected from the exact tree difference;
- the merge-handoff standard;
- source rights or automated-retrieval permissions;
- Canonical/Calendar/Monitor/Live/Analysis write gates;
- production monitoring schedules;
- public projections.

The recommended repository-level runner uses a dedicated custom label such as `world-signals-validation`. The repository variable then contains only that label:

```text
WORLD_SIGNALS_VALIDATION_RUNNER=world-signals-validation
```

Unset/delete the variable to return validation to `ubuntu-latest`.

A self-hosted runner executes repository workflow code with the privileges of the local account running the service/process. It must therefore be used only for trusted WORLD SIGNALS repository work. Do not expose it to untrusted fork pull requests or reuse it casually for unrelated repositories.

The runner does not need to be permanently online. It may be started for a validation session and stopped afterward. The current workflow keeps scheduled Monitor and Pages activity off that machine.

See `SELF_HOSTED_VALIDATION.md` for the operational runbook. Always use GitHub's current runner-registration commands/token shown in repository Settings rather than storing a registration token or generated command in this repository.

## Merge-handoff consequence

`HANDOFF_PROTOCOL.md` remains authoritative for the human merge boundary.

A PR may receive `MERGE NOW` only when the actual final head has a successful ordinary validation run using the profile selected by this policy, including the required read-only coverage/pressure evidence, plus all tranche-specific structural/residue/review gates.

A `SAFE_RESEARCH_DOCS` success is a valid ordinary CI result **only because the exact-head classifier and bounded checks are part of that same successful run**. A stale green base run, an inferred equivalence, or a hosted-runner admission failure is not a substitute.

A successful run on a correctly configured trusted self-hosted runner is an ordinary exact-head validation result; self-hosted execution is not a lower evidence class. Conversely, merely running commands manually without the workflow's exact-head/profile evidence does not silently become a merge-authorising CI result.

If neither GitHub-hosted nor the configured self-hosted runner can execute the required job, the merge state remains `DO NOT MERGE` unless a later reviewed validation policy explicitly authorises another exact-head mechanism.

## Portable local use

Run the complete suite from a repository checkout:

```bash
python3 scripts/validate_world_signals.py --profile FULL
```

Classify and validate a local branch against a known base:

```bash
python3 scripts/validate_world_signals.py \
  --event pull_request \
  --base-ref main \
  --head-ref HEAD
```

Inspect only the selected profile:

```bash
python3 scripts/validate_world_signals.py \
  --event pull_request \
  --base-ref main \
  --head-ref HEAD \
  --classify-only
```

The entry point uses repository-local code plus standard command-line tools. This keeps validation platform-independent; GitHub-hosted, self-hosted and local execution are execution choices rather than architectural dependencies.

## Compute discipline

Operational rules for future development:

- Research and architecture should converge before a PR is opened whenever practical.
- Do not create commits merely to provoke CI.
- Superseded in-progress validation for the same PR should be cancelled automatically.
- Do not run a second coverage workflow when ordinary CI already generated exact-head coverage evidence.
- Do not run daily regression suites merely because a scheduled read-only source poll is occurring.
- A guarded transaction may still require tranche-specific prewrite/postwrite gates; this policy does not remove them.
- Never reduce validation simply to fit a quota. If the required profile cannot run, stop and retain `DO NOT MERGE`.

## Self-hosted runner compatibility

The portable validator is runner-neutral. A GitHub self-hosted runner can execute the same entry point without changing Canonical/Monitor/Live/Analysis architecture or validation semantics. Self-hosting is an operational execution option, not a dependency and not authority to bypass source-rights or write-gate controls.
