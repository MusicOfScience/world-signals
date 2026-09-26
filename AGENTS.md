# WORLD SIGNALS / 4D CHESS — repository operating instructions

These are durable Codex working rules. The project charter, architecture
documents, schemas, `HANDOFF_PROTOCOL.md`, and `OPEC_QUARANTINE.md` remain the
authoritative specifications for their subjects.

## Scope and architecture

- WORLD SIGNALS is a local-first global intelligence, early-warning, calendar
  and forecasting platform. The calendar is one projection, not the whole
  project.
- Preserve the layer chain and its boundaries:
  `EVENTS → OBSERVATIONS → SIGNALS → RELATIONSHIPS → RISKS → SCENARIOS →
  FORECASTS → OUTCOMES → MODEL LEARNING`.
- Keep Canonical data, local runtime state, review candidates, analytical
  outputs and public projections separate. Public outputs must contain only
  deliberately publishable information.
- Automated monitoring may propose observations, signals or review work, but
  must not silently alter Canonical truth, publish private material, or write
  calendars. Preserve provenance, history and governed exceptions/quarantines.
- Treat the existing reviewed Live Intelligence observation layer as the
  upstream observation substrate. Do not create a competing observation store.
- Do not build speculative downstream layers or synthetic production
  intelligence merely to populate a UI. Keep population gates explicit.

## Working method

- Inspect the existing repository, governance, schemas, tests, workflows and
  operational scripts before changing code. Preserve functioning architecture;
  do not redo solved work without evidence of a defect.
- Work locally first. Keep recurring intelligence operation local; reserve
  GitHub Actions for lean CI, validation, static deployment and deliberate
  maintenance.
- Make the smallest coherent change. Use `apply_patch` for repository edits.
  Keep generated/disposable artefacts out of the tracked worktree unless they
  are deliberate governed outputs.
- Before and after changes, identify the affected layer, provenance path and
  review boundary. Run relevant validators, tests, builds and local HTTP checks
  rather than inferring health from code inspection.
- Never invent precision, causality, corroboration or forecasts. Distinguish
  observations from analytical inference and preserve contradictory evidence.

## Git, safety and handoff

- Reconcile `main` with `origin/main` before a new milestone. Work on a new
  `codex/` feature branch, commit coherently, inspect the final diff, push and
  open a pull request. Do not merge unless the operator explicitly requests it.
- Keep local `main` clean and synchronized when the task permits. Preserve
  unrelated user changes and never use destructive reset/checkout operations
  without explicit authorization.
- Do not reopen, merge, cherry-pick, rebase, materialise or use the quarantined
  OPEC transaction as a base. Future OPEC work starts from then-current `main`
  under a fresh bounded design.
- Follow `HANDOFF_PROTOCOL.md`. State the real merge status and distinguish code,
  governance, hosted-check and external infrastructure blockers. Report actual
  validation only; do not imply unavailable checks ran or passed.
- Completion reports must include the exact branch and head SHA, validation,
  cleanliness state, governed-data impact, genuine limitations, and for every
  pull request its number, title and full clickable GitHub URL.
- The operator's current reporting convention supersedes the older handoff
  protocol's link restriction and merge-label wording. Always provide the PR
  link, including when fixes remain. End with exactly one recommendation:
  `READY TO MERGE — my review found no remaining blockers. You may merge this PR.`
  or `DO NOT MERGE YET — the following issues remain: …` with concrete issues.
- State `I have not merged or closed the PR, as instructed.` separately. This
  describes execution authority; it is not a technical merge blocker.
- Unavailable hosted CI is not automatically a merge prohibition. Verify any
  applicable required-check rule; distinguish test failures, repository rules,
  runner admission failures and account/billing issues using direct evidence.
  Report local validation with its exact head, runtimes, commands, results and
  skips. Never claim an unavailable hosted check passed.
