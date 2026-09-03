# WORLD SIGNALS — Durable Review Checkpoint Architecture v0.1

**Reference date:** 2026-09-04  
**Canonical checkpoint:** v0.20 / 669 occurrences  
**Source registry:** v1.51 / 222 sources  
**Schema:** v0.51

## Problem

The retained review-state reducer is intentionally bounded by GitHub Actions artefact retention. A 90-day artefact horizon is useful operational evidence but is not a defensible permanent pending-review store.

WORLD SIGNALS therefore needs durable review-state continuity without:

- turning Actions artefacts into a second canonical database;
- granting the live monitor or Pages routine repository-write authority;
- conflating pending review state with reviewed canonical change history;
- retaining raw source/legal evidence in an operational checkpoint;
- changing stable review proposition identities across persistence layers.

## Implemented architecture

### 1. Durable checkpoint contract

`data/monitor/durable_review_checkpoint_contract.json` v0.2 defines a versioned, noncanonical review-operational dataset.

The checkpoint is not:

- the canonical registry;
- the reviewed change ledger;
- a monitor artefact;
- a browser-write target.

The primary item key remains the existing stable `WSRV-*` `review_item_id` defined by `review_candidate_state_contract.json`.

### 2. Baseline checkpoint

`data/monitor/review_checkpoint.json` seeds checkpoint sequence 0 at monitor run 47 / GitHub run id `33754900613`.

It contains zero review items. This preserves the prospective activation boundary: pre-contract experiments are not retroactively promoted.

### 3. Checkpoint-private minimum state

For `CANONICAL_FIELD_PROPOSITION` items, the durable checkpoint may retain `canonical_proposed_values` containing only the canonical fields named in `proposed_change_fields`.

This minimum private state is necessary to determine later whether canonical state has come into alignment after the originating monitor artefact has expired.

It is **not** a copy of raw source evidence and is removed from any public projection.

For opaque legal/rule/topology propositions:

- `canonical_proposed_values` must be null;
- the stable proposition digest persists;
- raw legal/rule/topology payloads do not enter the checkpoint.

### 4. Merge engine

`src/world_signals/review_checkpoint.py` implements:

- checkpoint validation;
- stable checkpoint SHA-256 linkage;
- post-checkpoint delta aggregation;
- same-proposition merge without duplicate identity;
- sibling preservation for materially different propositions;
- observation-count advancement only from runs strictly after the covered-through boundary;
- persistence of items absent from later runs;
- reapplication of reviewed manual decisions even without re-observation;
- canonical-alignment reconciliation using checkpoint-private canonical proposed values;
- `COMMITTED` state only with explicit `origin_review_item_id` change-ledger linkage;
- safe public projection with checkpoint-private values removed.

### 5. Evidence-gap rule

The retained-horizon fetcher was tightened during this work.

A successful monitor run missing its expected retained artefact remains a hard build failure.

An unsuccessful post-contract monitor run now makes `evidence_horizon_complete = false` and is recorded in `evidence_gaps`. It is never interpreted as candidate absence.

The durable checkpoint contract therefore prohibits advancing `covered_through_monitor_run_number` across unresolved evidence gaps.

## Behavioural tests

`tests/test_review_checkpoint.py` covers:

- first durable persistence of a new proposition;
- same-proposition update across checkpoint boundaries without duplication;
- persistence through later candidate absence;
- reviewed decisions applied without re-observation;
- later canonical alignment reconstructed from checkpoint-private proposed values;
- reviewed ledger linkage producing `COMMITTED`;
- opaque legal state remaining opaque in checkpoint storage;
- public projection stripping checkpoint-private values;
- rejection of an already-covered delta run;
- rejection of prohibited/unexpected checkpoint state;
- preservation of the exact `WSRV-*` identity established by the retained review layer.

Full WORLD SIGNALS CI passed with the merge engine and tests.

## Authority boundary

There is deliberately **no checkpoint-writing workflow yet**.

Current authority remains:

- live monitor: read source / compare / emit artefact; no checkpoint or canonical write;
- Pages: read repository + Actions and publish sanitized derived state; no checkpoint or canonical write;
- checkpoint proposal logic: non-writing;
- reviewed checkpoint transaction: future, separately constrained capability;
- canonical automatic commit: OFF;
- Google Calendar writes: OFF.

## Future reviewed checkpoint transaction

Before any checkpoint write capability is introduced, it must satisfy all of the following:

1. exact prior `review_checkpoint.json` SHA-256 precondition;
2. hash protection for canonical registry, source registry, schema, monitor expectations, operations policy and change ledger;
3. proposal validation against `durable_review_checkpoint_contract.json`;
4. prohibited-field scan;
5. full WORLD SIGNALS CI;
6. changed-file whitelist allowing only `data/monitor/review_checkpoint.json`;
7. ephemeral write-capable workflow removed immediately after reviewed use.

Routine scheduled repository writes are not authorized by v0.1.

## Retention policy

The retained monitor evidence horizon is presently 90 days and the retained reducer has a hard ceiling of 400 successful runs. At a six-hour cadence, this is intentionally close to the maximum expected retained run count rather than an invitation to scale indefinitely.

A durable checkpoint should be reviewed before uncheckpointed source evidence approaches expiry. If required evidence has expired or an unresolved failed-run gap exists, the checkpoint must not advance across that gap.

## Platform independence

The persistence concept is a versioned review-operational checkpoint plus evidence deltas. GitHub repository files and Actions are the present implementation transports. They are not architectural requirements for WORLD SIGNALS.

## Current gate status

**Architecture:** implemented and regression-tested.  
**Baseline durable checkpoint:** created.  
**Checkpoint merge/projection:** implemented and tested.  
**Routine checkpoint write:** NOT authorized.  
**Reviewed checkpoint transaction workflow:** NOT yet created.  
**First post-contract live monitor evidence:** not yet observed at this checkpoint.
