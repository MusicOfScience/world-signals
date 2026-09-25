# WORLD SIGNALS — CY hosted-validation blocker audit v0.1

**Status:** EXECUTION ADMISSION BLOCKER — NOT A REPOSITORY TEST FAILURE  
**Merge state:** DO NOT MERGE  
**Reference date:** 2026-09-25 Australia/Melbourne  
**CY pre-audit head tested by hosted trigger:** `471a220fe4a71ee2d1897a4600b01026494cb33f`

## Triggered hosted runs

The CY draft PR triggered both required hosted workflows on exact head `471a220fe4a71ee2d1897a4600b01026494cb33f`:

- ordinary validation run `36142658551`;
- read-only coverage run `36142658347`.

Both workflow runs completed with conclusion `failure`, but their jobs contain **no executed workflow steps**:

- validation job `108096006484`: `steps = null`;
- coverage job `108096004946`: `steps = null`.

No checkout, runtime setup, validator, unittest, compile, JavaScript, build or coverage command executed.

Decoded job-log retrieval returns no runner log blob, consistent with no hosted runner having executed the job.

## Interpretation

This is **not evidence of a failing CY test or repository defect**.

The signature resembles the known hosted-runner admission condition documented during CQ and CR-CX, but CY does not assert a current billing, payment, allowance or spending-limit cause without direct current account-side evidence.

## Protocol consequence

Under `HANDOFF_PROTOCOL.md`:

- hosted CI remains the normal validation path;
- a zero-step hosted failure cannot be relabelled as successful validation;
- earlier green runs on older heads do not authorise merge;
- local exact-head validation may substitute only after explicit project-owner activation for the affected work under the adopted fallback conditions;
- the user performs merges; the assistant does not.

No no-op commit or repeated runner retry is justified merely to consume attempts.

## Repository-side evidence already established

Before opening the draft PR, CY proved:

- branch created from exact current main `5740b5baa33a992e291abc66ce67f0f6172d53a2`;
- merge base equals that exact main;
- branch was 4 commits ahead / 0 behind at the pre-audit head;
- the pre-audit diff contained only:
  - `PROJECT_STATUS.md`;
  - `ROADMAP.md`;
  - `data/coverage/POST_CX_RECOVERY_PRESSURE_CY_v0.1.md`;
  - `data/coverage/CHINA_AFRICA_CDEP_CY_RESEARCH_v0.1.md`;
- no Canonical, Source Registry, Change Ledger, Monitor, Live, Analysis, Calendar, workflow or OPEC-quarantine path was changed;
- stale PR #125 was closed unmerged and marked superseded.

This structural evidence is informative but is **not a substitute for the execution gate**.

## Exit conditions

CY remains `DO NOT MERGE` until either:

1. required hosted workflows execute successfully on the actual final CY head; or
2. the project owner explicitly activates the adopted local exact-head fallback for CY and the complete applicable gate is executed and recorded on the unchanged final remote head.

Any later commit invalidates earlier validation evidence and requires the applicable gate again.
