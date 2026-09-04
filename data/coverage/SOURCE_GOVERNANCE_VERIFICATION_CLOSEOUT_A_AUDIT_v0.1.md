# WORLD SIGNALS — Source Governance Verification Closeout A Audit v0.1

**Checkpoint date:** 2026-09-05  
**Purpose:** durable post-merge audit for the Verification Closeout A source-governance transaction.

## Status

**COMPLETE / MERGED / POST-MERGE RUNTIME-ALIGNED**

Verification Closeout A is complete on `main` at merge commit `849d4ef6a4b4814ec57235f08189e7a9eaf995c2` (PR #26).

Production state after merge:

- canonical registry: **v0.21 / 669 occurrences**;
- Tier-1 source registry: **v1.62 / 224 sources**;
- reviewed change ledger: **v0.10**;
- monitor expectations: **v0.7**;
- automatic canonical commit: **false / CLOSED**;
- Google Calendar write: **false / OFF**.

## Exact transaction surface

The reviewed production transaction changed exactly one file:

- `data/sources/registry.json`

Source registry advanced **v1.61 / 224 → v1.62 / 224**.

Exactly seven source records changed:

- `WSSRC-INT-010` — APEC Secretariat;
- `WSSRC-INT-017` — Asian Infrastructure Investment Bank;
- `WSSRC-INT-026` — Philippines Presidential Communications Office;
- `WSSRC-REG-011` — Parliament of South Africa;
- `WSSRC-REG2-002` — Royal Thai Government;
- `WSSRC-REG6-001` — Kenya Law / National Treasury;
- `WSSRC-REG6-002` — Morocco MEF / legal portal.

Vietnam `WSSRC-REG5-001` remained unchanged because direct National Assembly provenance is better scoped than the currently registered government-news source and requires separate source-scope review.

APEC's present denormalised `canonical_dependency_count` was corrected **0 → 1**, matching canonical-derived truth. Eight legacy records lacking the optional helper were deliberately not bulk-filled. Independent reconciliation found **zero remaining present helper mismatches**.

## Transaction and independent audit evidence

Guarded transaction workflow:

- run `33907914998`;
- job `101137157742`;
- transaction commit `db4e4b6e3d90d2f97498faaee253ed2775a0ca2b`;
- guarded preflight PASS;
- exact source-registry-only mutation enforcement PASS;
- registry validation PASS;
- **244 tests PASS** (1 skipped);
- Python compilation PASS;
- browser JavaScript checks PASS;
- site build PASS.

Independent read-only post-state audit:

- run `33908030468`;
- job `101137529579`;
- exact seven-source reconciliation PASS;
- Vietnam unchanged PASS;
- APEC 0→1 helper repair PASS;
- zero remaining present helper mismatches PASS;
- canonical v0.21 / 669 unchanged;
- ledger v0.10 unchanged;
- expectations v0.7 unchanged;
- automatic canonical commit false;
- Calendar write false;
- **244 tests PASS** (1 skipped);
- Python/JS/site build PASS.

Both temporary transaction and audit workflows were removed before PR review.

## Measured source-governance state

The generic source-governance audit on the reviewed post-state measured:

- **65** fully explicit governance sources;
- **159** sources missing at least one governance field;
- **88 P1** canonical-dependent sources requiring research/backfill;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **156**;
- missing `automated_monitoring_use`: **156**;
- missing `verification_mode`: **159**.

These are measured post-transaction counts, not arithmetic projections.

## Post-merge live evidence

The merge itself triggered live-monitor run **58** / run id `33908223252` on exact main commit `849d4ef6a4b4814ec57235f08189e7a9eaf995c2`.

Observed configuration:

- canonical registry **v0.21**;
- source registry **v1.62**;
- monitor expectations **v0.7**;
- operations policy **v0.1**;
- configuration fingerprint `34a90ad792b88f66664b989d64d72d713c5eea281c1bf6ac5c96c6365ddcb982`.

Runtime result:

- **6 healthy / 0 degraded** adapters;
- all **6 expected adapters observed**;
- **0 review candidates**;
- status `NO_CHANGE`;
- canonical hash unchanged before/after;
- automatic canonical commit false;
- Google Calendar write false.

The follow-on Pages workflow-run deployment **`33908266777`** completed successfully on the same main commit. The earlier direct push-triggered Pages run was cancelled by workflow concurrency in favour of this later successful deployment; this is not a deployment failure.

## Architectural conclusion

Verification Closeout A did not create monitoring authority, event-state authority or automatic canonical mutation authority. It completed reviewed verification-mode governance for seven already-canonical-dependent sources while preserving the distinction between factual provenance, automation rights and verification method.

The next known integrity-led source-governance item is **Vietnam `WSSRC-REG5-001` source-scope review**, because the currently registered government-news source should not be made governance-complete while a more direct National Assembly source better supports the canonical dependency.

This source-scope review should precede ordinary backfill selection from the remaining 88 P1 queue.
