# WORLD SIGNALS — local exact-head validation fallback CR plan v0.1

**Status:** GOVERNANCE TRANSITION PROPOSAL / NO SELF-AUTHORISATION / NO MERGE OR GOVERNED POPULATION AUTHORITY  
**Reference date:** 2026-09-13 Australia/Melbourne  
**Exact base:** `166bd14341ca6689dbc9b75d16500f3e176346cd`  
**Trigger:** GitHub-hosted Actions allowance exhaustion and repeated zero-step runner-admission failures

## Problem

WORLD SIGNALS was migrated to a local working model after the GitHub-hosted Actions allowance was exhausted. The existing merge handoff protocol still names ordinary CI as the only successful validation path. That mismatch leaves locally reproducible work permanently blocked even when the repository's declared validation commands can be executed exactly on the PR head.

This proposal adds a constrained local execution mode. It does not declare local checks automatically equivalent, waive tests, change any governed dataset, or grant merge authority.

## Proposed boundary

Hosted CI remains normal. Local fallback requires explicit project-owner activation for a known hosted operational failure and must preserve:

- exact remote base/head and ancestry verification;
- a clean worktree before and after validation;
- repository-declared runtime versions;
- command parity with every applicable ordinary, coverage and tranche-specific gate;
- refusal to approximate required runner-, network-, permission- or deployment-specific evidence;
- PR audit-trail evidence tied to the exact validated SHA;
- complete invalidation after any later commit;
- structural diff and temporary-machinery residue checks;
- the existing no-link rule while `DO NOT MERGE` applies; and
- the user-only merge boundary.

## Adoption safety

The proposal does not bootstrap itself silently. Until it is adopted, the prior protocol remains authoritative. If hosted CI remains unavailable, the project owner must explicitly approve the exact protocol diff with the adoption phrase specified in `HANDOFF_PROTOCOL.md`. Only then may the complete local gate be rerun for the protocol-only adoption PR and assessed for a possible `MERGE NOW` handoff. The user still performs any merge.

## Explicit non-effects

This change does not:

- alter Canonical, Sources, Change Ledger, Monitor, Live Intelligence, Analysis, Calendar or public projections;
- activate any automatic write;
- relax source rights, endpoint permission or evidence standards;
- revive or modify the OPEC CE quarantine;
- make local validation a substitute for a required live or platform-specific test;
- permit the assistant to merge; or
- change PR #125 or treat its earlier local evidence as retroactively authorised.

## Required validation for this proposal

Before an adoption handoff, verify the exact branch boundary and run locally with the repository-declared Python version:

```bash
python scripts/validate_registry.py
python scripts/validate_live_intelligence.py
python scripts/validate_analysis.py
python scripts/project_state_snapshot.py --check
python -m unittest discover -s tests -v
python -m py_compile scripts/fetch_latest_monitor_snapshot.py scripts/fetch_retained_review_state.py scripts/validate_live_intelligence.py scripts/validate_analysis.py scripts/project_state_snapshot.py scripts/run_cross_layer_coverage_audit.py scripts/apply_analysis_revision_contract_ba.py src/world_signals/live_intelligence.py src/world_signals/analysis.py src/world_signals/analysis_revision.py src/world_signals/analysis_revision_projection.py src/world_signals/live_analysis_bridge.py src/world_signals/cross_layer_coverage.py
node --check web/app.js
node --check web/horizon.js
node --check web/native-calendar.js
node --check web/history.js
node --check web/operations.js
node --check web/biosecurity.js
node --check web/analysis.js
python scripts/build_site.py
python -m unittest tests.test_coverage tests.test_cross_layer_coverage_cj -v
python scripts/run_coverage_audit.py
python scripts/run_cross_layer_coverage_audit.py
```

The final audit must additionally show that the only intended branch changes are this plan, the protocol, the recovery-surface wording and its regression test; OPEC quarantine and all governed/runtime files remain unchanged.
