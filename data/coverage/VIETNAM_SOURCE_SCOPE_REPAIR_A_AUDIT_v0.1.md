# WORLD SIGNALS — Vietnam Source-Scope Repair A Audit v0.1

**Checkpoint date:** 2026-09-05 (Australia/Melbourne)  
**Production merge:** PR #29  
**Merged main commit:** `1c05406f810caebbb004ccad339d034a3aaa4cc0`

## Purpose

Durable closeout record for the reviewed Vietnam provenance repair affecting `WSO-REG-G-0001` only.

This audit records the production state after the separately prepared and reviewed transaction was merged. It does not create new canonical facts or authorise any new monitoring route.

## Production state

- Canonical registry: **v0.22 / 669 occurrences**.
- Source registry: **v1.63 / 225 sources**.
- Reviewed change ledger: **v0.11**.
- Biosecurity overlay canonical checkpoint: **v0.22 / 669**.
- Governance audit after repair: **67 fully explicit / 158 incomplete / 87 P1 / 71 P2**.
- Automatic canonical commit: **false**.
- Google Calendar write: **false**.

## Provenance repair result

Stable occurrence `WSO-REG-G-0001` remains the same occurrence.

Protected event semantics were preserved:

- opening date remains **2026-10-20**;
- certainty status remains **PROVISIONAL**;
- time status remains **PROVISIONAL**;
- existing session phase-window metadata is preserved;
- no canonical timing field changed anywhere in the registry;
- no canonical occurrence identifier was added, removed or replaced.

Provenance changed only:

- former canonical source `WSSRC-REG5-001` — Government Electronic Newspaper — is retained as historical/secondary official evidence;
- new canonical source `WSSRC-REG5-002` — National Assembly Electronic Portal — is the first-order institutional source;
- derived canonical dependencies moved from `WSSRC-REG5-001: 1` to `0`, and `WSSRC-REG5-002: 0` to `1`.

The National Assembly source remains **manual-only under a rights hold**. First-order authority was not interpreted as permission for automated retrieval.

## Transaction evidence

Guarded transaction workflow run `33910727663` completed successfully before PR #29 was opened.

It verified:

- read-only preflight PASS;
- explicitly gated reviewed apply PASS;
- exact four-file mutation boundary PASS;
- canonical registry validation PASS;
- 253 tests PASS, with 2 intentional skips;
- Python compile PASS;
- browser JavaScript syntax PASS;
- site build PASS;
- bounded transaction commit `827a3789af42a02c55c92ff3989d5975892ef2fa`.

The durable production diff was exactly:

1. `data/canonical/registry.json`;
2. `data/sources/registry.json`;
3. `data/changes/ledger.json`;
4. `data/coverage/biosecurity_overlay.json`.

Both temporary transaction and post-audit workflows were removed before PR review.

## Independent post-audit

Read-only post-audit run `33910962778` passed after correction of one audit-only assumption.

The initial post-audit attempt failed because the audit incorrectly assumed every source row must store a `canonical_dependency_count` helper. That helper is optional legacy/denormalised metadata; canonical-derived dependency counts are authoritative. The corrected audit checks any stored helper only where present.

The successful independent audit verified:

- canonical **v0.22 / 669**;
- source **v1.63 / 225**;
- ledger **v0.11**;
- exactly one changed canonical occurrence: `WSO-REG-G-0001`;
- no canonical timing change;
- stable identities preserved;
- source dependency truth `0 → 1` for the new first-order source relationship;
- historical ledger preserved except for exactly one appended reviewed change;
- overlay changed only by canonical checkpoint advancement;
- transaction replay fails closed;
- exact four-file durable diff;
- 253 tests PASS, 2 intentional skips;
- validation, compile, browser checks and site build PASS;
- both write gates remain false.

No production data changed as a result of the failed first audit attempt or its correction.

## Post-merge runtime alignment

The PR #29 merge itself triggered live-monitor **run 59**, GitHub run id `33911315209`, on exact main commit `1c05406f810caebbb004ccad339d034a3aaa4cc0`.

Observed configuration:

- canonical registry **v0.22**;
- source registry **v1.63**;
- monitor expectations **v0.7**;
- operations policy **v0.1**;
- configuration fingerprint `44f3e3cffd6b2596f2a396ca35790ef24e4df552abeb838f2322e4c0c3066ff4`.

Observed result:

- **6 healthy / 0 degraded** adapters;
- all **6 expected adapters observed**;
- no missing or unexpected adapters;
- **0 review candidates**;
- canonical hash unchanged before/after;
- `NO_CHANGE`;
- automatic canonical commit **false**;
- Google Calendar write **false**.

The initial push-triggered Pages run `33911315259` was cancelled by workflow concurrency. This was not a deployment failure: the live-monitor completion triggered successor Pages run `33911351490`, which completed **successfully** on the same main commit. Runtime and public derived-output alignment are therefore observed and closed.

## Closeout decision

**Vietnam Source-Scope Repair A is COMPLETE.**

The project may now return to critique and selection of the remaining P1 source-governance queue. Do not infer that the next work should be a mechanically numbered tranche; re-rank the queue against forward-horizon relevance, dependency concentration, geographic/domain balance, source-scope quality and governance-field shape first.
