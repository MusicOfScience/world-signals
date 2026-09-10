# WORLD SIGNALS — CR validation-compute architecture audit v0.1

**Status:** IMPLEMENTATION BRANCH / NOT MERGE-AUTHORISED  
**Exact base:** `166bd14341ca6689dbc9b75d16500f3e176346cd`  
**Branch:** `feature/low-compute-validation-cr`  
**Tranche:** `CR`

## Problem

WORLD SIGNALS' rapid research/transaction cadence exposed a structural CI inefficiency: hosted-runner usage was being multiplied by overlapping workflow triggers rather than reserved for the validation work that actually changed.

This audit records the repository-side architecture only. It deliberately does not store account billing details, payment information or personal entitlement data.

## Pre-CR runner multiplication

Before CR:

- `Validate WORLD SIGNALS` ran the full historical validation suite on every pull-request event and again on every push to `main`;
- `Audit WORLD SIGNALS coverage` started a separate hosted runner for changes including any `data/coverage/**` path, so research-only pressure/audit Markdown could trigger a second runner even though the coverage executables do not consume those documents;
- ordinary CI had no same-PR `cancel-in-progress` concurrency rule, so superseded commits could continue consuming runner time;
- the daily live monitor reran its adapter/monitor regression modules on every scheduled poll even though those tests had already been exercised when the monitor code/configuration was reviewed;
- Pages also rebuilds after the daily live monitor, but that relationship provides current operational visibility and is not changed by CR.

For a typical research-only PR under `data/coverage/`, the old trigger graph could therefore create:

1. full ordinary CI on the PR head;
2. separate coverage audit on the same PR head;
3. full ordinary CI again after merge;
4. separate coverage audit again after merge.

Intermediate PR commits could multiply that further.

## CR design

CR introduces `scripts/validate_world_signals.py` as the single portable validation entry point and keeps `Validate WORLD SIGNALS` as the ordinary handoff workflow.

### `FULL`

Any executable, test, workflow, governed/machine-readable, top-level governance, deleted, renamed, copied or unknown change runs the historical suite plus coverage generation.

CR itself necessarily belongs to this profile because it changes workflows, validation code, tests and the handoff contract.

### `SAFE_RESEARCH_DOCS`

A cheaper exact-head profile is available only when the entire PR net diff consists of **newly added** regular UTF-8 Markdown research/audit evidence under `data/` with an approved research filename marker.

The fast path rejects:

- modification of an already-merged research record;
- deletion, rename or copy;
- executable file mode;
- non-Markdown or top-level files;
- unknown research naming;
- a new research path already referenced by a tracked non-Markdown file.

It then runs Canonical/Live/Analysis validators, the derived-state check, coverage regression tests and both read-only coverage/pressure generators on the exact PR head.

This preserves the common workflow where a new research document is revised many times on its feature branch: it remains one net-added file relative to `main` until merge.

### `POST_MERGE`

A `main` push may use the lightweight post-merge profile only when Git proves that:

- the head is a conventional two-parent merge; and
- the merge tree is byte-identical to parent 2, the reviewed PR head.

If this cannot be proved, the push escalates to `FULL`.

### Workflow consolidation

CR also:

- enables same-PR `cancel-in-progress` on ordinary validation;
- moves exact-head coverage/pressure generation into ordinary validation;
- leaves the standalone coverage workflow available only for deliberate manual diagnostics;
- removes daily regression-test repetition from scheduled monitor polls while retaining those tests on code/configuration-triggered and manual monitor runs;
- leaves Pages and the daily monitor schedule themselves unchanged.

## Structural savings

CR is designed to reduce runner multiplication without reducing the merge gate.

For a qualifying new research-only PR and its conventional merge, the normal shape changes from up to **four automatically triggered runners** (CI + coverage on PR, then CI + coverage on merge) to **two lightweight runners** (one exact-head research validation and one tree-proved post-merge verification).

For a governed/code PR, the expensive historical suite should normally run once on the final PR head. Coverage is generated in the same runner, and a conventional merge receives the lightweight post-merge verification rather than rebuying the historical suite.

When multiple commits are pushed while one PR validation is still executing, the obsolete run is cancelled.

The daily live monitor keeps one scheduled runner but no longer rebuying its regression suite on a routine poll reduces execution time inside that runner.

These are structural reductions, not a promise of a fixed monthly minute count. Guarded transactions, deliberate live-source probes and manual workflows remain real compute costs and must still be justified by their tranche contracts.

## Safety invariants

CR does not change:

- Canonical Registry;
- Source Registry;
- Change Ledger;
- Monitor expectations or operations policy;
- Live Intelligence schema/population;
- Analysis schema/population;
- Calendar projection state;
- automatic write gates;
- OPEC CE quarantine.

No profile has Canonical, Calendar, Live, Analysis or public-projection write authority.

`SAFE_RESEARCH_DOCS` is not available merely because a file ends in `.md`; it is a narrowly proved net-new evidence surface. Any uncertainty escalates to `FULL`.

A GitHub Actions hosted-runner admission failure remains a failed merge gate. CR does not convert an unexecuted job into a success.

## Local preflight completed during CR design

Before repository validation is available, the new classifier/contract was exercised in a temporary local Git repository:

- net-new approved research Markdown -> `SAFE_RESEARCH_DOCS`;
- ordinary/unknown Markdown -> `FULL`;
- a mixed research + JSON change -> `FULL`;
- conventional merge with head tree equal to parent 2 -> `POST_MERGE`;
- non-equivalent merge -> `FULL`.

The CR unit module also passed seven local contract tests covering safe-path recognition, fail-closed escalation, merge-tree classification, full-profile contents and write-gate absence. The three edited YAML workflow files were parsed successfully as YAML.

These local checks are **development evidence only**. They are not a substitute for the required final-head GitHub Actions run under `HANDOFF_PROTOCOL.md`.

## Activation / handoff

Do not open a PR merely to consume a hosted-runner attempt while hosted execution is unavailable.

When runner capacity is available again, CR should be opened from its exact branch head and must receive `FULL` ordinary validation because the tranche changes workflow, executable validation code, tests and merge-governance documents. Only after that exact-head run, integrated coverage evidence and structural diff/residue review pass may CR receive a `MERGE NOW` handoff.

After CR merges, the blocked CQ research PR can be reconciled onto the new `main`; because its intended net change is two newly added unreferenced research Markdown files, it should then be eligible for `SAFE_RESEARCH_DOCS` if and only if the exact-head classifier independently proves that state.
