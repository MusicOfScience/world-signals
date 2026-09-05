# WORLD SIGNALS — Priority-region historical anchors R PR evidence v0.1

**Evidence date:** 2026-09-06  
**Base main:** `a8bfb87bb7e889381ba67ab83c5f32218e6c2bd2`  
**Reviewed transaction commit:** `04c059701de346dbaa85b51d03eebf0ab5a183fb`

## Disposable full post-state simulation

GitHub Actions run `33974225020`: **SUCCESS**.

The disposable runner applied the reviewed R transaction only in its ephemeral working tree and then validated the complete proposed post-state:

- canonical registry: **v0.29 / 678** — PASS;
- source registry: **v1.71 / 236**;
- reviewed change ledger: **v0.16 / 48**;
- biosecurity overlay: **v0.4 @ canonical v0.29 / 678**, semantic membership unchanged;
- Analysis validator: PASS;
- full repository suite: **395 tests, OK, 15 skipped**;
- Python compile: PASS;
- browser JavaScript syntax checks: PASS;
- static site build: PASS for 678 events / 236 governed sources / 7 configured live monitor routes / 2 analytical reviews;
- exact simulated mutation boundary: PASS.

Post-state Analysis readiness from that run:

- eligible completed occurrences: **9**;
- Africa: **1 eligible / 0 reviewed — ELIGIBLE_UNREVIEWED**;
- South Asia: **1 eligible / 0 reviewed — ELIGIBLE_UNREVIEWED**;
- Southeast Asia: **1 eligible / 0 reviewed — ELIGIBLE_UNREVIEWED**;
- Latin America: **1 eligible / 0 reviewed — ELIGIBLE_UNREVIEWED**;
- broad population state: **`BLOCKED_PRIORITY_REGION_REVIEW_GAP`**.

No Analysis review was added by R.

## Reviewed feature-branch apply

GitHub Actions run `33974288530`: **SUCCESS**.

The reviewed apply:

- fetched and proved `origin/main` still exactly `a8bfb87bb7e889381ba67ab83c5f32218e6c2bd2` before mutation;
- re-ran the fail-closed CHECK_ONLY transaction;
- applied the transaction on `feature/priority-region-historical-anchors-r` only;
- revalidated canonical v0.29 / 678 and the Analysis layer;
- ran the focused R regression suite successfully;
- asserted the exact generated write boundary;
- committed canonical registry, change ledger, transaction audit, biosecurity checkpoint alignment and source registry only;
- self-removed the temporary write workflow in the same feature-branch transaction commit.

The resulting reviewed transaction commit is `04c059701de346dbaa85b51d03eebf0ab5a183fb`.

## Permanent-PR validation requirement

The reviewed transaction commit used `[skip ci]` so the write workflow could self-remove without starting redundant branch CI. GitHub also honours that token for the initial `pull_request` workflow event, so PR #47 did not receive ordinary permanent CI on that commit.

This evidence commit intentionally has **no skip token**. Its purpose is both to preserve the execution evidence durably and to trigger the repository's normal `pull_request` validation workflow on the final PR head. The PR must not be handed off for merge until that permanent CI run succeeds and mergeability is rechecked.

## Safety invariants

- automatic canonical commit remains OFF;
- Google Calendar write remains OFF;
- no live-monitor route is added or changed;
- no Analysis review is fabricated;
- no elapsed date implies completion;
- no temporary R workflow remains in the branch;
- merge remains manual only.
