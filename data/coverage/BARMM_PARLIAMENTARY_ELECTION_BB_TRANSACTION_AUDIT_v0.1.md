# BARMM Parliamentary Election BB — Transaction Audit v0.1

## Transaction identity

- Branch: `feature/post-ba-barmm-election-anchor-bb`
- Exact post-BA main base: `b8c5372198e3141c4c3f79ace13083877447f71b`
- Final green read-only preflight: GitHub Actions run `34032205529`
- Controlled transaction run: GitHub Actions run `34032279867`
- Merge policy: **manual merge only; no auto-merge**

## Pressure-audit decision

BB repairs a first-order elections/governance coverage gap with one bounded BARMM parliamentary-election occurrence. The authoritative date source is the Philippine Commission on Elections (COMELEC) BARMM election calendar. Context from other institutions is not promoted into Canonical date authority.

## Canonical transaction

- Canonical Registry: **v0.38 / 688 → v0.39 / 689**
- Source Registry: **v1.80 / 243 → v1.81 / 244**
- reviewed Change Ledger: **v0.24 / 59 → v0.25 / 60**
- biosecurity overlay: **v0.13 → v0.14 checkpoint alignment only**, with non-version/checkpoint semantics unchanged
- Live Intelligence: **unchanged v0.4 / 4 observations / 6 evidence rows**
- Analysis: **unchanged schema v0.7 / 21 reviews / 95 evidence rows**
- production `live_inputs`: **unchanged at 1**
- production Analysis revisions: **unchanged at 0**
- production `EXACT_TIMESTAMP_SERIES`: **unchanged at 0**

New stable occurrence: `WSO-EL-PH-BARMM-20260914`, series `WSER-EL-PH-BARMM-PE`, source `WSSRC-EL-PH-001`, ledger entry `WSCHANGE-138c3977e91ced60d8`.

The election is represented as **14 September 2026**, `CIVIL_DATE`, `Asia/Manila`, `DAY` precision, `PLANNED`, `CONFIRMED`, milestone `POLL_GENERAL`. No polling clock time, UTC timestamp, result, or observed market response is invented.

## Source governance

COMELEC is admitted for manual authoritative provenance. Automated monitoring remains explicitly closed: `PROHIBITED_OR_RIGHTS_HOLD`, `RIGHTS_AUDIT_REQUIRED`, `RIGHTS_HELD_MANUAL_ONLY`. Candidate-content collection and raw-evidence redistribution are not authorised by BB.

## Mutation boundary

The transaction changed exactly six governed state files:

1. `data/canonical/registry.json`
2. `data/sources/registry.json`
3. `data/changes/ledger.json`
4. `data/coverage/biosecurity_overlay.json`
5. `PROJECT_STATUS.md`
6. `ROADMAP.md`

This audit document is a seventh permanent transaction record, not Canonical/event state. Canonical schema, monitor expectations/operations, Live Intelligence data/schema and Analysis data/schema were hash-protected and unchanged.

## Preflight regressions repaired before transaction

The repeated ephemeral preflights exposed historical tests/helpers that incorrectly treated old checkpoint values as permanent descendant ceilings. Repairs followed the rule **freeze history, not descendants**:

- BA status handling now preserves the frozen Analysis-revision foundation while allowing later valid status checkpoints.
- BB tests validate both exact prestate simulation and reviewed poststate without permitting transaction replay.
- AZ status and CLI guards preserve the inaugural one-input Live→Analysis contract while accepting reviewed Analysis descendants.
- AV public Live projection metadata now reports the actual current Canonical build checkpoint while its AV foundation checkpoint remains separately frozen.

Failed diagnostic/preflight runs did not commit BB governed data; runners restored ephemeral changes and temporary workflows were removed. The final preflight passed the untouched and ephemeral-BB full repository test/build gates, protected-file hashes, exact mutation boundary and clean restoration.

## Validation

The controlled transaction re-ran Live Intelligence validation, Analysis validation, full unittest discovery, Python compilation, JavaScript syntax checks and static-site build before any governed target commit. Protected hashes and the exact six-file governed mutation boundary were rechecked after materialisation.

Automatic Canonical commit remains off outside this reviewed transaction. Calendar writes remain off. No downstream Live or Analysis population is authorised by BB.
