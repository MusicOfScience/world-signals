# WORLD SIGNALS — merge handoff protocol

This is a human-operations safety control subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. It does not grant repository write authority, merge authority, or any governed-layer permission.

## Mandatory merge instruction

Every pull-request handoff to the user must contain exactly one unambiguous merge state:

- **MERGE NOW — PR #N**: use only after the actual final PR head has passed the required validation gate in an authorised execution mode, read-only coverage/pressure audit, structural diff/residue checks, and any tranche-specific gates.
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

## Authorised validation modes

Hosted CI is the normal validation mode. Its successful required jobs on the actual final PR head are sufficient execution evidence when every other handoff condition is also satisfied.

A **local exact-head fallback** may be used only when the project owner has explicitly authorised local validation for the affected work because hosted CI is unavailable for a known operational reason, such as an exhausted account allowance or a runner-admission failure. Repository-local convenience, a slow queue, or a failing test is not enough to activate the fallback.

The fallback does not weaken or skip the gate. Before `MERGE NOW` may be issued, all of the following are mandatory:

1. Verify the current remote PR head, current remote `main`, local `HEAD`, merge base, ahead/behind state, and intended diff. The checked-out local head must equal the remote PR head, and the branch must descend from and not be behind current `main`.
2. Start and finish with a clean tracked worktree. Remove only disposable artifacts created by the validation run, then repeat the cleanliness and residue checks.
3. Use the runtime major/minor versions declared by the repository workflows where locally available. Record any unavoidable version difference and keep the state `DO NOT MERGE` unless it is separately reviewed as immaterial.
4. Execute every command in the ordinary validation workflow that applies to the PR head. Execute the read-only coverage workflow when its path filter applies, plus every tranche-specific, transaction-specific, protected-layer, structural-diff, and temporary-machinery cleanup gate that would otherwise be required.
5. Do not replace a genuinely runner-specific or network-specific gate with an offline approximation. If a required live endpoint, permission, clean ephemeral materialisation, deployment, platform integration, or other environment-specific property cannot be tested locally, the state remains `DO NOT MERGE`.
6. Record the validation date and timezone, exact base and head SHAs, activation reason, runtime versions, commands and outcomes, test and skip counts, coverage results, diff boundary, residue result, and any limitations in the PR audit trail without changing the validated head.
7. Treat local results exactly like hosted results under the final-head rule: any later commit invalidates them and requires the complete applicable local gate again.

Local validation is evidence about the checked-out code, not permission to mutate governed layers, relax source rights, reactivate quarantined work, bypass review, or merge automatically.

### One-time adoption rule

The pull request that first introduces this fallback cannot silently authorise itself. While the prior protocol is still active it must remain `DO NOT MERGE` unless hosted CI succeeds. To adopt the fallback without hosted CI, the project owner must review the exact final protocol diff and explicitly state `ADOPT LOCAL VALIDATION FALLBACK — PR #N`. That statement authorises one fallback assessment for the protocol-only adoption PR; it does not perform the merge. The assistant must then rerun the complete applicable local gate on the exact final head and may issue `MERGE NOW` only if every requirement above passes. The user still performs the merge.

## Recovery / next-chat handover requirement

Any recovery prompt or next-chat handover must repeat these controls explicitly:

> MERGE HANDOFF SAFETY: always state either `MERGE NOW — PR #N` or `DO NOT MERGE — PR #N`. Never provide a PR link while the state is `DO NOT MERGE`. Only say `MERGE NOW` after required checks have passed on the actual final head and temporary write machinery/residue has been removed. The user merges; the assistant does not.

This requirement is part of the recovery context precisely because an ambiguous handoff can corrupt otherwise sound guarded-transaction discipline at the final human control point.
