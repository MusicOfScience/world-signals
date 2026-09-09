# WORLD SIGNALS — CD first controlled Analysis revision transaction audit v0.1

## Boundary
- Tranche: CD
- Exact merged base: `c186835d9d6b36620177badfff604f309ceb35d4` (post-CC / PR #111)
- Guarded materialisation commit: `a954f29262144b7ccb29db35cad89808e9e4d4b7`
- Successful materialisation run/job: `34326983574` / `102386403830`
- First closeout run: `34332089238` (semantic checks passed; broad Markdown whitespace check failed before cleanup)
- Successful closeout run: `34332330591`
- First PR validation run/job: `34332466247` / `102404026387` (governed validators passed; two CD tests failed because the pull-request checkout was depth 1 and did not contain the exact historical base commit object)
- Successful post-repair PR validation run/job: `34332785822` / `102405055413`

## Architectural decision
Post-CC pressure recomputation showed Monitor was no longer the thinnest layer: 25 configured routes covered 215 Canonical occurrences across all nine regions, while Analysis had 21 reviewed snapshots and zero production revision descendants. CD therefore exercised the existing controlled revision contract rather than quota-filling another monitor category.

## Production revision
`WSAN-BWC-WG8-2026-002` is a `NEW_EVIDENCE` child of `WSAN-BWC-WG8-2026-001`, bound to the same Canonical occurrence `WSO-BWC-WG-2026-S08`. Newly admitted ninth-session BWC evidence changes the second-order process assessment from `PLAUSIBLE_WATCH_ITEM` to `OBSERVED` institutional follow-through. It does not establish final substantive consensus, market movement, or event causality.

New Analysis-only evidence:
- `WSEV-BWC-WG9-UN-INDICO-20260817` — primary official ninth-session evidence;
- `WSEV-BWC-WG9-SHIB-REV7-20260827` — institutional catalogue evidence used only for document-process observation, not PDF-body inference.
Neither has Canonical provenance effect.

## Governed post-state
- Canonical `v0.41 / 689` unchanged
- Sources `v2.02 / 257` unchanged
- Monitor `v0.27 / 25` unchanged; automatic Canonical commit OFF; Google Calendar write OFF
- Live Intelligence `v0.6 / 6 observations / 9 evidence` unchanged
- Analysis schema `0.7 → 0.8`
- Analysis reviews `0.17 / 21 → 0.18 / 22`
- Analysis evidence `0.17 / 95 → 0.18 / 97`
- Production Analysis revisions `0 → 1`
- Production Live→Analysis inputs remains exactly `1`
- Revision ceiling: one production revision, one child per parent; public lineage metadata OFF; automatic latest-head selection OFF; public revision-head collapse OFF.

## Immutability and projection proof
Closeout proved all 21 pre-existing review objects and all 95 pre-existing Analysis evidence objects are unchanged from the exact merged base. Only one review and two Analysis evidence objects were appended. Canonical, Sources, Monitor, Changes and Live Intelligence are unchanged. Public projection preserves both analytical snapshots while stripping revision-lineage metadata and deriving no latest head.

For pull-request CI, the same immutability proof is checkout-depth independent. The parent snapshot is checked against its original frozen W payload, and every protected upstream file is checked against its exact Git blob identity from post-CC base `c186835d9d6b36620177badfff604f309ceb35d4`. This preserves the proof when GitHub checks out only the synthetic pull-request merge commit.

## Preserved failure history
The first guarded materialisation attempt exposed six historical tests that had incorrectly treated Analysis `0.17 / 21` as a permanent ceiling; commit was gated off. Those tests were repaired only for descendant safety. A later guarded run `34326705152` exposed one CD-only test replaying the deliberately one-shot simulator after in-job materialisation; commit was again gated off. The final repair compares protected files to the exact post-CC base instead of replaying the transaction. Successful run `34326983574` then passed the exact pre/post-state gates, full suite, protected-layer audit and commit gate.

First closeout run `34332089238` passed exact post-state, immutability, public-boundary and full repository validation, then stopped because `git diff --check` treated intentional two-space Markdown hard breaks in the permanent research note as trailing-whitespace errors. No audit or cleanup commit occurred. The closeout harness was narrowed to semantic protected-path checks; the research document was not altered to satisfy the harness.

After PR #112 opened, ordinary PR validation run `34332466247` independently passed the Canonical, Live Intelligence and Analysis validators. Its unit-test step then failed exactly two CD immutability tests. GitHub's `pull_request` checkout used `fetch-depth: 1` and checked out synthetic merge commit `e52b4072acb9cd5dc8af1b548cf623b5d61ad392`; the historical base commit object was therefore absent, so `git show c186835d9d6b36620177badfff604f309ceb35d4:<path>` failed before either equality assertion could execute. This was a validation-harness history-depth assumption, not governed-data, revision-contract or merge-conflict failure.

The repair did not skip those tests and did not broaden CI checkout history. Instead it made their evidence depth-independent: the immutable parent is compared with its original frozen `NONMARKET_INSTITUTIONAL_ANALYSIS_W_PAYLOAD_v0.1.json`, while all seven protected upstream files are compared with the exact post-CC Git blob hashes recorded from the base commit. Post-repair PR run `34332785822`, job `102405055413`, then passed the full ordinary PR gate including all 1,206 tests.

## Validation
Successful materialisation and closeout each validated Canonical 689, Live Intelligence 0.6 / 6 / 9, Analysis 22 / 97, the Live→Analysis bridge and revision contract, 1,206 unit tests with 68 skips and no failures, Python compilation, JavaScript syntax and the static site build.

Post-repair ordinary PR run `34332785822` additionally passed the same governed validators, all 1,206 tests, Python compilation, every JavaScript syntax check and the static site build under GitHub's depth-1 pull-request checkout.

Google Calendar remains an output/interface layer only. No automatic Canonical mutation, automatic Analysis-head selection, or auto-merge capability was enabled.