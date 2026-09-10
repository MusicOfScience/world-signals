# WORLD SIGNALS — Brazil fuel-policy Live CN transaction audit v0.1

**Status:** GUARDED MATERIALISATION COMPLETE / USER MERGE REQUIRED  
**Reference date:** 2026-09-10  
**Exact post-CM base main:** `9386114de527b117987058cb1b9cd98066dab8e4`  
**Branch:** `feature/post-cm-brazil-fuel-policy-live-cn`

## Outcome

CN adds exactly one bounded unscheduled Brazilian fuel-policy Live observation and one primary-official evidence row after fresh legal-status review. The resulting governed Live state is:

- Live schema/data version: `0.10`;
- observations: **9**;
- evidence rows: **12**;
- Canonical-linked observations: **3**;
- new observation: `WSLI-POL-BRA-FUEL-POLICY-20260909-001`;
- new evidence: `WSEV-LI-BRA-MF-FUEL-POLICY-20260909`;
- new observation Canonical links: **0**;
- automatic Canonical commit: **OFF**;
- Google Calendar write: **OFF**;
- public Live observation projection: **OFF**;
- Monitor route created: **no**;
- Analysis population changed: **no**.

The specimen records the Brazilian Ministry of Finance's official statement that the Federal Government adopted/signed temporary fuel-policy measures on 9 September 2026. It does not upgrade unresolved legal-publication/effect status: no new substantive decree/measure-provisional identifier is asserted, Diário Oficial publication is not asserted, and entry into force is not asserted. Event and source-publication timing remain at `CIVIL_DATE` precision for 9 September 2026. The source page's displayed `18h47` is not converted to UTC because the reviewed page did not itself establish the source timezone.

Government-stated geopolitical context remains attributed to the government source and is not promoted into independent WORLD SIGNALS causal analysis. No observed pump-price, inflation, supply or market response is asserted.

## Attempt 1 — semantic transaction green, historical suite fail-closed

- workflow run: `34446405883`;
- job: `102772043248`;
- pre-run branch head: `f0387cf0b23ce657e6442807d2646c80899d0708`;
- conclusion: **FAILURE**;
- governed transaction committed/pushed: **no**.

Before the full historical suite, the run passed:

- exact post-CM main/merge-base gate;
- protected-layer and existing-Live pre-write snapshots;
- pure CN target simulation;
- focused CN tests;
- ephemeral reviewed CN materialisation;
- derived recovery-state refresh;
- CN materialisation verification;
- Canonical validator;
- Live validator;
- Analysis validator;
- derived-state consistency.

The complete historical suite ran **1,288 tests**, with **3 failures** and **68 historical-prestate skips**. The three failures were descendant-safety defects rather than CN payload or validator defects:

1. one CM test treated current Live v0.9 / 8 observations / 11 evidence rows as a permanent ceiling rather than a frozen CM checkpoint plus descendant-capable current state;
2. two Nepal AW tests compared dotted repository versions using `float(...)`, so `"0.10"` became numeric `0.1` and incorrectly failed an old `0.2` floor.

The transaction stopped before compilation, JS checks, static build, protected-row proof, cleanup and commit, so the ephemeral governed mutation did not enter branch history.

Permanent diagnosis: `data/live_intelligence/BRAZIL_FUEL_POLICY_LIVE_CN_DESCENDANT_REPAIR_v0.1.md`.

## Descendant repair

The repair preserved historical meaning while removing current-state coupling:

- CM's historical `cm_checkpoint` remains exactly v0.9 / 8 / 11 and retains its exact historical base;
- current Live state may advance through reviewed descendants while retaining the CM contract and CM observation identities as a subset;
- Nepal AW historical v0.2 facts remain unchanged;
- dotted versions are compared component-wise rather than as floating-point decimals.

No CM research/plan/audit historical facts, Nepal payload/source/time semantics, governed population or OPEC quarantine material were relaxed or rewritten.

### Repair infrastructure history

The repair itself exposed two infrastructure-only issues. They are retained here so failed gated activity is not hidden:

- run `34446747175`: workflow-definition failure before jobs because an initial embedded multiline Python repair block produced invalid YAML;
- run `34446811931`: retrigger of the same invalid workflow state, again before jobs;
- run `34446831607`, job `102773340199`: repaired CM/Nepal/CN focused suites all passed, but the final push was rejected because the GitHub Actions token could not create/update a workflow file under the active GitHub App permissions;
- run `34446909463`, job `102773579877`: narrowed test-only repair passed end-to-end and pushed repair commit `3937193d8d1ab4a3f8b91db84e5a89ebf5a10774`.

The temporary repair helper/workflow were then removed through the authenticated repository connector. This permission behaviour is an infrastructure constraint, not a governed-data failure.

## Attempt 2 — successful guarded transaction

- workflow run: `34447059247`;
- job: `102774045356`;
- pre-materialisation branch head: `533a967618b39c4ec5e72779b2757a23d7e893f5`;
- materialisation commit: `65836ac394357e3ee883bfc81bf0a26e3c33d825`;
- conclusion: **SUCCESS**.

The successful run passed:

- exact post-CM base/main gate;
- protected-layer and existing-Live pre-write snapshots;
- CN simulation;
- focused CN tests;
- reviewed materialisation;
- derived recovery-state regeneration;
- CN materialisation verification;
- Canonical validator;
- Live validator;
- Analysis validator;
- derived-state check;
- complete historical suite: **1,288 tests passed / 68 historical-prestate skips**;
- Python compilation;
- all seven JavaScript syntax checks;
- static site build;
- protected-layer byte-hash invariance;
- exact invariance of all eight pre-CN Live observations and all eleven pre-CN evidence rows;
- exact population growth of one observation and one evidence row;
- bounded transaction diff;
- removal of the temporary Python apply helper before commit;
- transaction commit and push.

Because the current GitHub App/Actions permission model does not allow the Actions token to modify workflow files, the one-shot transaction workflow was intentionally removed immediately after success through the repository connector rather than by the runner. Cleanup commit: `da591a3580cf0f9cc4a4994ba3eb4eac03c5ae96`.

## Protected-layer result

CN did not mutate:

- Canonical Registry or schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- Monitor expectations or operations policy;
- Analysis schema, reviews or evidence registry;
- OPEC quarantine record or OPEC quarantine regression test.

No Calendar write, automatic Canonical commit, automatic Live ingestion, public Live projection, Monitor route or Analysis review was created.

## CM contract preservation

CM's correction/retraction/conflicting-report contract remains intact in Live v0.10:

- corrected/retracted observations still require a prior Live target, correction/revision evidence and later observation time;
- conflicting reports still require at least two unique evidence references from at least two distinct normalised providers plus explicit conflict description;
- no winning source or synthetic consensus is introduced;
- `DATA_REVISION` remains a separate concept.

CN is not itself a correction/retraction/conflict specimen.

## Handoff boundary

The branch still requires ordinary PR validation, post-CN read-only coverage audit, final residue review and user merge. A tenth Live observation or any other next governed expansion remains subject to a fresh pressure decision rather than automatic continuation.
