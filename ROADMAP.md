# WORLD SIGNALS — code promotion roadmap

## Stage 0 — research architecture (completed enough to encode)

Research artifacts define the canonical schema, lifecycle, source rights, monitor state machine, conflict rules, rollback expectations and coverage discipline.

## Stage 1 — executable read-only thin slice (THIS REPOSITORY)

**Can do**
- load and validate the canonical registry;
- enrich events from the source registry;
- build a static searchable/filterable web projection;
- deploy that projection to GitHub Pages;
- run CI validation;
- compare a source assertion with a canonical occurrence;
- emit a review candidate without mutating canonical state.

**Cannot do**
- live scheduled crawling;
- automatic canonical writes;
- Google Calendar writes;
- causal/market analysis in calendar objects.

## Stage 2 — live adapters, still review-only

Add one adapter per validated source family, e.g.:
- ONS RSS/calendar;
- RBA RSS;
- EUR-Lex/CELLAR;
- Colombia Socrata inventory + SUIN clause verification;
- EIA data-product surface.

Each adapter implements:

`fetch -> snapshot -> parse -> assert`

The shared engine then performs:

`match -> diff -> review candidate`

No adapter receives write access to canonical JSON.

## Stage 3 — guarded reviewed commit transaction

Implement an explicit command/tool:

`candidate -> human approval -> apply to clone -> validate protected identity -> write change ledger -> atomic canonical replacement -> rebuild site`

Every commit must be reversible from the ledger/snapshot.

## Stage 4 — scheduled monitoring

Enable GitHub Actions `schedule` only for routes that pass endpoint/parser and rights gates. Workflows produce review artifacts or pull requests. Schedule cadence is source-specific; not every source needs hourly polling.

## Stage 5 — calendar projection/export

Generate ICS/Google Calendar output from canonical records. Calendar remains disposable/rebuildable output; deleting a calendar never deletes canonical data.

## Stage 6 — Live Intelligence / Analysis

Store observations, surprises, revisions and market-response evidence in separate datasets. Join them to occurrence IDs in the UX without embedding them into event timing.

## Stage 7 — evaluate narrow auto-commit classes

Only reconsider after prospective reschedule/cancellation evidence and executed heterogeneous endpoint parsers satisfy the commit gate. Even then, auto-commit should begin with a very narrow evidence class, not blanket permissions.
