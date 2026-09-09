# OPEC quarantine

Status: **QUARANTINED / NON-BLOCKING / MANUAL REACTIVATION ONLY**

This record prevents the parked OPEC provenance transaction from silently becoming an active WORLD SIGNALS workstream again.

## Quarantined lineage

- Closed PR: `#113` — `QUARANTINED — CE OPEC primary outcome provenance`
- Preserved branch: `feature/post-cd-pressure-audit-ce`
- Branch head at quarantine: `3c36554fa2fae52e35db0ac6b337e31f19b9685e`
- Base `main` at quarantine: `9552c1db0d212af33524b80b28d91ef7a897e2d8`
- First guarded materialisation failure: run `34337483630`, job `102420174247`

The branch is intentionally retained as an evidence package. It is not an integration branch and must not be mechanically rebased, reopened, copied forward wholesale, cherry-picked, or used as the base for unrelated work.

## Permanent integration guard

`tests/test_opec_quarantine_cf.py` is the executable companion to this record. It must remain in ordinary CI while the quarantine is active. The test fails if known CE transaction machinery is reintroduced on a live branch without a deliberate, separately reviewed change to the quarantine guard itself.

Any future PR that alters or removes this record or its regression guard must explain why OPEC is being deliberately reactivated and satisfy the protocol below. Silence, branch reuse, or incidental conflict resolution is not sufficient authority.

## What is quarantined

The quarantine covers the CE OPEC primary-provenance materialisation transaction and its temporary execution machinery, including the CE-specific plan/research, materialisation script, regression test and temporary `ce-*` workflow files.

It does **not** mean WORLD SIGNALS must ignore OPEC or OPEC-related events forever. It means later OPEC data work must be designed afresh from current `main` and must explicitly account for the lessons below before any new governed mutation is proposed.

## Discovered foibles that future OPEC work must account for

1. **Descendant-safety:** historical OPEC regressions incorrectly treated a prior assertion/status/ledger row as the permanent head. Future tests must verify the historical row by stable identity and semantics rather than assuming it remains the last row after later valid provenance changes.
2. **Transaction timestamps:** the CE harness invented an exact `20:00` Melbourne transaction clock. Future provenance transactions must use an actual execution timestamp or the repository's accepted date-only representation; never fabricate clock precision.
3. **Test integrity:** the CE test contained a stray no-op `assertGreaterEqual` lambda. Future harnesses must not monkey-patch assertions or weaken regression semantics to achieve materialisation.
4. **Primary-source rights are distinct from source competence:** `WSSRC-COM-001` can be a competent OPEC primary source while still carrying automation/rights holds. A future OPEC repair must not relax `PRODUCTION_HOLD_WRITTEN_AUTHORIZATION_REQUIRED`, `RIGHTS_OR_LICENSE_HOLD`, `RIGHTS_HELD_MANUAL_ONLY`, or `BLOCKED` implicitly.
5. **Minimal retention:** the OPEC terms review supported hyperlinking and occasional attributed research use but not treating source-page material as a shared archive. Store only the minimal factual/provenance metadata required by the architecture.
6. **Preserve historical fallbacks:** Reuters `WSSRC-COM-015` and Saudi Press Agency `WSSRC-COM-016` remain historical completion/supporting evidence if the 6 September outcome is revisited. Satisfying a later competent primary source must not erase the earlier evidentiary chain.
7. **Stable event identity:** the 6 September 2026 seven-country voluntary-adjustment review (`WSO-COM-A-0001`) and the separate 4 October 2026 JMMC occurrence (`WSO-COM-A-0002`) must not be merged merely because the 6 September statement also mentioned a 4 October next meeting.
8. **Non-blocking debt:** unresolved OPEC provenance debt must not block unrelated Canonical Registry, Source/Change Monitor, Live Intelligence, Analysis or Calendar work.

## Reactivation protocol

OPEC CE work must remain dormant unless all of the following are true:

1. there is a **fresh architectural or data-quality reason** to revisit OPEC, not merely the existence of the parked debt;
2. work starts from then-current `main`, never from the quarantined CE branch;
3. the engineer/researcher first inspects PR `#113`, branch `feature/post-cd-pressure-audit-ce`, and this file;
4. the proposed change is bounded and independently justified;
5. source rights, provenance hierarchy, event identity and descendant-safe testing are re-audited against current repository state;
6. any deliberate removal or alteration of the quarantine regression guard is explained in the new PR; and
7. ordinary CI plus any transaction-specific gate is green before manual merge.

Until those conditions are deliberately satisfied, **do not reopen PR #113, rerun its OPEC materialisation workflow, or revive its transaction files on an active branch.**

## Current programme direction

Post-CD work proceeds independently from clean `main` via Monitor coverage pressure analysis. OPEC is excluded from candidate selection while this quarantine remains in force.
