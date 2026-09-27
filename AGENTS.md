# WORLD SIGNALS / 4D CHESS — repository operating instructions

These are durable Codex working rules. The project charter, architecture
documents, schemas, `HANDOFF_PROTOCOL.md`, and `OPEC_QUARANTINE.md` remain the
authoritative specifications for their subjects.

## Scope and architecture

- WORLD SIGNALS is a local-first global intelligence, early-warning, calendar
  and forecasting platform. The calendar is one projection, not the whole
  project.
- Preserve the layer boundaries and distinguish the governed contract inventory
  from the synthesis lifecycle. The lifecycle is a feedback architecture:
  `ACTORS + EVENTS → OBSERVATIONS → SIGNALS + ANOMALIES → RELATIONSHIPS +
  FLOWS + DEPENDENCIES → WORLD STATE → COMPETING HYPOTHESES / REGIMES /
  TRANSMISSION → SCENARIOS + SIGNPOSTS → FORECASTS → OUTCOMES → EVALUATION /
  CALIBRATION / MODEL LEARNING`, with later evaluation and learning feeding
  future World State assessments. Forecasts and Outcomes are not prerequisites
  for an as-of World State assessment.
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

## World State direction

- Treat **World State** as a derived, review-governed synthesis of governed
  observations, Signals, Relationships, Risks/Regimes, Scenarios, market
  observations and Forecast/Outcome evidence. It is not a replacement for
  Canonical, Live Intelligence or Analysis. One narrow internal production
  component and compositional snapshot now exist; the general synthesis
  engine, broad population and public World State projection remain
  unimplemented. The current public brief may expose only the separately
  allowlisted four-series Outlook Forecast pilot.
- Model actors explicitly: identity, role, jurisdiction, authority,
  capabilities, constraints, incentives, commitments, channels and internal
  institutional relationships. A public utterance is evidence of what an
  actor said, not proof that a state decided, authorised, implemented or
  achieved the proposition.
- Preserve the implementation-state ladder:
  `SAID → DECIDED → AUTHORISED → IMPLEMENTED → OBSERVED`. Each transition
  needs appropriate evidence and may remain unresolved or contradictory.
- Make conflict/military activity, strategic/geopolitical tension and
  political/institutional stability first-class world-state dimensions.
  Model flows, dependencies and chokepoints explicitly; treat markets as
  sensors with measurement, timing, baseline and alternative-explanation
  controls rather than as automatic causal proof.
- Preserve state memory and as-of truth. Detect anomalies against explicit
  baselines; retain negative evidence, uncertainty type, competing hypotheses,
  model disagreement, lags, thresholds, feedback loops and reflexivity.
- A future synthesis engine may propose state updates, transmission edges,
  scenarios, signposts or forecasts, but human review, provenance,
  public/private boundaries, prospective cutoff integrity and no-silent-write
  rules remain mandatory.
- The intended human projection is **WORLD STATE | OUTLOOK | CALENDAR | MAP |
  RESEARCH**. The briefing is the final projection, never a new canonical
  store.

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
