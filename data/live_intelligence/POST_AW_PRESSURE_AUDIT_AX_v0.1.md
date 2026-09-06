# WORLD SIGNALS — post-AW Live Intelligence pressure audit AX v0.1

**Base:** post-#78 `main` at `721206169033eb0ceb695075d44fb38e7fa2edc3`
**Reference date:** 2026-09-06

## Question

After AW proved one unscheduled physical-shock observation, what real-world specimen creates the highest-value next pressure on the Live Intelligence contract without turning the layer into a general news feed?

## Candidate classes

### DRC Bundibugyo Ebola outbreak — SELECTED

Strengths:

- primary official WHO evidence exists as a sequence of dated, comparable outbreak snapshots;
- the same real-world developing situation changes materially across successive as-of dates;
- later cumulative counts do not make earlier snapshots false;
- later situation reports are not corrections/retractions of prior reports;
- state-as-of time is distinct from event time, publication time and WORLD SIGNALS observation time;
- repeated observations need a stable reviewed grouping key without automatic clustering;
- the outbreak is unscheduled and does not require a fabricated Canonical occurrence;
- the specimen materially improves African / Global South coverage.

Contract pressure:

1. `state evolution != revision`;
2. a later as-of snapshot must preserve the earlier snapshot;
3. a manual story key may group repeated observations but is not a Canonical event identity or causal claim;
4. automatic story clustering remains prohibited;
5. state-as-of precision must be explicit and must not be promoted from a civil date to a fabricated timestamp;
6. source publication date, state-as-of date and system observation time remain separate;
7. the first Live Intelligence specimen, Nepal, must remain unchanged and ungrouped.

### Japan household spending release — not selected

This remains analytically useful, especially for quantified surprise, but it is a scheduled macro release and would mostly repeat already-exercised release/surprise semantics. It does not pressure story identity or evolving-state semantics as strongly.

### Geopolitical/policy development — not selected

Potentially useful later for conflicting reports and confirmation-state transitions, but current candidates do not provide the same clean primary-source sequence for testing non-revision state evolution.

### Market observation — not selected

Still blocked by the need for a separately pressure-audited market-data rights/provenance contract. It would introduce licensing and attribution complexity before basic evolving-state semantics are stable.

## Selected bounded design

AX should add exactly two DRC outbreak observations to the existing Nepal observation:

- WHO Disease Outbreak News published 28 August 2026, state as of 26 August 2026;
- WHO African Region Weekly External Situation Report 16, state as of 30 August 2026.

The two DRC observations share one manually reviewed `story_id`. The second points to the first with `state_update_of_observation_id`. Both retain `revision_of_observation_id = null`.

No automatic clustering is opened. No story registry is created. No continuous ingest is opened. No public observations are projected.

## Required schema pressure

AX should add minimal grammar for:

- optional reviewed `story_id`;
- optional `state_as_of` with explicit precision;
- optional `state_update_of_observation_id`;
- validation that a state-update target exists, belongs to the same story and has an earlier state-as-of value;
- validation that state updates are not revision links;
- explicit policy that story identity is a grouping key only, not Canonical identity, causal attribution or analytical conclusion.

## Population ceiling

Target production state after AX:

- schema `v0.3`;
- observations: `3` total (Nepal + two DRC snapshots);
- evidence: `4` total (two Nepal + two WHO DRC rows);
- public observations: `0`;
- automatic ingestion: `false`;
- automatic story clustering: `false`;
- automatic Canonical commit: `false`;
- Google Calendar writes: `false`.

A later pressure audit is required before any fourth observation or broader story ingestion.

## Decision

**Proceed with the DRC Bundibugyo outbreak as AX.** The novelty is not Ebola itself; it is the distinction between a changing state of the world and a correction to history.
