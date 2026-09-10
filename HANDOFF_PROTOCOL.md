# WORLD SIGNALS — merge handoff protocol

This is a human-operations safety control subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. It does not grant repository write authority, merge authority, or any governed-layer permission.

## Mandatory merge instruction

Every pull-request handoff to the user must contain exactly one unambiguous merge state:

- **MERGE NOW — PR #N**: use only after the actual final PR head has passed the required ordinary CI, read-only coverage/pressure audit, structural diff/residue checks, and any tranche-specific gates.
- **DO NOT MERGE — PR #N**: use whenever any required gate, closeout write, final-head rerun, audit, cleanup, or review remains incomplete.

Never use ambiguous wording such as “ready-ish”, “open”, “draft is up”, “awaits review”, “nearly done”, or a narrative from which the user has to infer whether merging is safe.

## Link rule

**Do not provide a PR URL or clickable PR link while the merge state is `DO NOT MERGE`.**

A PR URL may be given only in the same handoff that explicitly says **MERGE NOW**. This prevents a premature merge caused by a convenient link appearing before the branch has reached its reviewed final head.

## Manual-merge boundary

The user performs merges. The assistant must not merge a WORLD SIGNALS pull request unless the user explicitly reverses that standing instruction.

After the user reports a merge, verify the PR's merged state, merge commit, and exact new `main` before creating the next feature branch.

## Final-head rule

Earlier green workflow runs never substitute for validation of the actual final head. Any later documentation, audit, cleanup, recovery-surface, or code commit invalidates the earlier handoff state until required checks have run again on the new head.

## Recovery / next-chat handover requirement

Any recovery prompt or next-chat handover must repeat these controls explicitly:

> MERGE HANDOFF SAFETY: always state either `MERGE NOW — PR #N` or `DO NOT MERGE — PR #N`. Never provide a PR link while the state is `DO NOT MERGE`. Only say `MERGE NOW` after required checks have passed on the actual final head and temporary write machinery/residue has been removed. The user merges; the assistant does not.

This requirement is part of the recovery context precisely because an ambiguous handoff can corrupt otherwise sound guarded-transaction discipline at the final human control point.
