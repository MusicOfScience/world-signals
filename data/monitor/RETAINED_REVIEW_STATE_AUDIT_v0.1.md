# WORLD SIGNALS — Retained Review State Audit v0.1

**Reference date:** 2026-09-04  
**Canonical checkpoint:** v0.20 / 669 occurrences  
**Source registry checkpoint:** v1.51 / 222 sources  
**Schema:** v0.51  
**Monitor expectations:** v0.6  
**Monitor operations policy:** v0.1

## Purpose

This audit records the first implemented state layer between transient live-monitor review candidates and reviewed canonical change history.

The layer is deliberately named **retained review state**, not a permanent review queue. It is a deterministic read-only reduction of retained GitHub Actions monitor artefacts plus explicitly reviewed manual decision records.

## Contract

`data/monitor/review_candidate_state_contract.json` v0.1 activates prospectively after live-monitor run 47 (`33754900613`). Run 47 is the final pre-contract observation and is not retroactively promoted into review state.

The contract distinguishes:

- `candidate_id`: immutable evidence object emitted by one monitor comparison;
- `review_item_id`: stable review proposition identity, prefixed `WSRV-`;
- reviewed canonical change history: a separate ledger layer.

Repeated observations of the same material proposition aggregate into one review item. A materially different proposition receives a different review item. Absence from a later run does not resolve an existing item. Source/fetch failure does not resolve an item. Rejected or deferred items do not reopen merely because they are reobserved.

## Identity modes

### Canonical field proposition

Identity is derived from:

1. sorted occurrence scope; and
2. only the canonical fields proposed to change, with their proposed values.

This means different monitor `candidate_id` values can correctly aggregate if they express the same material canonical proposition.

### Opaque legal/rule proposition

Legal-rule, clause and topology candidates are hashed from occurrence scope, candidate type and normalized proposed rule state. Raw rule/topology payloads are used only transiently during the build and are not copied into the public review object.

## State reducer

Implemented in `src/world_signals/review_state.py`.

Derived states include:

- `PENDING_REVIEW`
- `DEFERRED`
- `REJECTED`
- `APPROVED_FOR_CANONICAL_COMMIT`
- `COMMITTED`
- `SUPERSEDED`
- `CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION`

A canonical field proposition that already matches current canonical state but lacks an explicit reviewed change-ledger link is **not** silently marked complete. It becomes `CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION`.

Future candidate-driven canonical commits require change-ledger linkage through `origin_review_item_id` and `origin_candidate_ids`. Historical changes are not required to be backfilled.

## Manual decisions

`data/monitor/review_decisions.json` v0.1 is the reviewed manual-decision store.

It is currently empty and may only be changed by a reviewed repository commit. The live monitor and Pages/browser layers have no authority to write it.

## Retained evidence fetch

Implemented in `scripts/fetch_retained_review_state.py`.

The Pages build:

- scans completed live-monitor runs after run 47;
- stays within the declared 90-day retained artefact horizon;
- downloads retained successful-run artefacts with repository credentials removed before following the signed storage redirect;
- requires every successful in-scope run to have its expected non-expired artefact before the horizon may be called complete;
- records unsuccessful runs as evidence gaps and never interprets them as candidate absence;
- validates each monitor artefact against the existing public-runtime safety gate;
- derives review proposition identity only in build memory;
- discards raw candidate/source/legal evidence after reduction;
- has a hard v0.1 ceiling of 400 successful retained runs.

The Pages workflow retains `contents: read` and `actions: read`; no repository contents-write authority was added.

## Public projection safety

The public retained-review object contains only the fields allowed by the contract. Prohibited material includes raw old/new values, source assertions, snapshots, observations, rules, topology, rows, bodies, raw payloads and parser/error content.

The browser remains read-only. Automatic canonical commit remains OFF. Google Calendar writes remain OFF.

## Behavioural tests

Regression tests cover:

- repeated identical propositions aggregate even when monitor candidate IDs differ;
- materially different propositions remain siblings;
- absence from a later run does not resolve an item;
- a rejected item does not automatically reopen when reobserved;
- canonical alignment without reviewed ledger linkage requires reconciliation;
- reviewed ledger linkage marks a proposition committed;
- opaque legal state can be hashed without leaking its payload publicly;
- automatic commit must be explicitly false;
- run 47 and earlier are excluded by the prospective activation boundary;
- the Operations/browser module has no write path.

## First real Pages reduction

The first live Pages execution of the retained reducer completed successfully after activation of the contract.

Observed build result:

- retained successful post-contract runs considered: **0**
- retained review items: **0**
- state counts: `{}`
- unsuccessful post-contract monitor runs: **0**
- evidence horizon: **complete for the presently existing post-contract evidence**

This is a meaningful empty state. It does **not** mean historical monitor experiments contained no candidates; historical runs were deliberately excluded by the prospective activation boundary.

The same build independently continued to publish the latest retained single-run monitor snapshot from run 47 as stale relative to the current canonical/source configuration. The two concepts therefore remain distinct.

## UX

The Operations view now distinguishes:

1. configured monitor routes;
2. latest retained dated run evidence;
3. candidates generated in that single run;
4. retained review state across post-contract retained evidence;
5. source-governance inventory;
6. the closed canonical auto-commit gate.

The Change History view remains the reviewed canonical ledger and is not conflated with pending review state.

## Limitations / next gate

This v0.1 mechanism is deliberately bounded by GitHub Actions artefact retention. At a six-hour monitor cadence, a 90-day horizon can approach roughly 360 runs, so the v0.1 hard ceiling of 400 is a safety bound rather than a permanent architecture.

Before WORLD SIGNALS may claim indefinite pending-review persistence, design an independently constrained durable checkpoint mechanism that:

- does not turn GitHub Actions artefacts into a second canonical database;
- does not grant the monitor or Pages workflow repository contents-write authority merely to persist state;
- preserves proposition identity and reviewed decisions;
- makes evidence loss or incomplete history explicit;
- remains platform-independent in conceptual architecture.

Do not call the current retained state a permanent queue until that gate is passed.
