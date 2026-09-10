# WORLD SIGNALS — merge handoff protocol

This is a human-operations safety control subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. It does not grant repository write authority, merge authority, or any governed-layer permission.

Validation execution profiles are defined in `VALIDATION_POLICY.md`. That policy may reduce duplicated compute only when its fail-closed exact-head classifier proves the relevant change surface. It does not relax this merge boundary.

## Mandatory merge instruction

Every pull-request handoff to the user must contain exactly one unambiguous merge state:

- **MERGE NOW — PR #N**: use only after the actual final PR head has passed the required ordinary validation profile selected under `VALIDATION_POLICY.md`, the required read-only coverage/pressure audit evidence, structural diff/residue checks, and any tranche-specific gates.
- **DO NOT MERGE — PR #N**: use whenever any required gate, closeout write, final-head validation, audit, cleanup, runner execution, or review remains incomplete.

Never use ambiguous wording such as “ready-ish”, “open”, “draft is up”, “awaits review”, “nearly done”, or a narrative from which the user has to infer whether merging is safe.

## Ordinary validation rule

`Validate WORLD SIGNALS` is the ordinary exact-head validation workflow. Its selected profile is part of the evidence:

- `FULL` is required for executable, governed, workflow, operational/governance-document, unknown, deleted, renamed or otherwise non-safe changes;
- `SAFE_RESEARCH_DOCS` is acceptable only when the workflow itself proves that the entire exact base/head diff satisfies the narrow research-Markdown contract and then completes its bounded governed/coverage checks;
- a hosted-runner admission failure, zero-step job, stale base success, inferred tree equivalence or unexecuted local plan is **not** a passing validation result.

Coverage/pressure generation may be performed inside the same ordinary validation job. A separate coverage workflow run is not required when the successful exact-head ordinary run produced the required read-only coverage/pressure evidence.

## Link rule

**Do not provide a PR URL or clickable PR link while the merge state is `DO NOT MERGE`.**

A PR URL may be given only in the same handoff that explicitly says **MERGE NOW**. This prevents a premature merge caused by a convenient link appearing before the branch has reached its reviewed final head.

## Manual-merge boundary

The user performs merges. The assistant must not merge a WORLD SIGNALS pull request unless the user explicitly reverses that standing instruction.

After the user reports a merge, verify the PR's merged state, merge commit, and exact new `main` before creating the next feature branch.

## Final-head rule

Earlier green workflow runs never substitute for validation of the actual final head. Any later documentation, audit, cleanup, recovery-surface, or code commit invalidates the earlier handoff state until the required validation profile and other gates have run again on the new head.

A post-merge lightweight validation is permitted only when `VALIDATION_POLICY.md` mechanically proves that the merge commit is a conventional two-parent merge whose tree is byte-identical to the reviewed PR head. If that equivalence cannot be proved, post-merge validation escalates to `FULL`.

## Recovery / next-chat handover requirement

Any recovery prompt or next-chat handover must repeat these controls explicitly:

> MERGE HANDOFF SAFETY: always state either `MERGE NOW — PR #N` or `DO NOT MERGE — PR #N`. Never provide a PR link while the state is `DO NOT MERGE`. Only say `MERGE NOW` after the required exact-head validation profile, coverage/pressure evidence and tranche-specific gates have passed and temporary write machinery/residue has been removed. A zero-step/unassigned-runner Actions failure is not green. The user merges; the assistant does not.

This requirement is part of the recovery context precisely because an ambiguous handoff can corrupt otherwise sound guarded-transaction discipline at the final human control point.
