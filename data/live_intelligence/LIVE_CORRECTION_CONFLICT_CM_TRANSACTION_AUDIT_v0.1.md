# WORLD SIGNALS — Live correction / retraction / conflicting-report CM transaction audit v0.1

**Status:** MATERIALISED / GUARDED / NO PRODUCTION POPULATION  
**Reference date:** 2026-09-10  
**Exact base main:** `1e4a6bbc8670fc36a452740401461f28e313c031` (merged PR #120)  
**Materialisation commit:** `aafaa2fb3ffe3acce54e587cb69b5d95bd9d9972`

## Purpose and selection

CM implements the post-CL pressure decision recorded in `data/coverage/POST_CL_PRESSURE_AUDIT_CM_v0.1.md`: harden the executable Live Intelligence grammar for corrections, retractions and conflicting reports before broader Live population.

The motivating pressure was not a quota. CL had encountered materially different official/officially indexed wording around Waqa Moana and correctly excluded the disputed formulation rather than silently selecting a stronger claim. CM turns that experience into a safer generic Live contract without resolving Waqa and without creating a production conflict/correction specimen merely to exercise the code.

## Governed transition

CM advances Live contract metadata only:

- Live schema/store: **v0.8 → v0.9**;
- production observations: **8 → 8**;
- production evidence rows: **11 → 11**;
- Canonical-linked observations: **3 → 3**;
- Canonical Registry: unchanged **v0.42 / 689**;
- Source Registry: unchanged **v2.04 / 258**;
- Change Ledger: unchanged **v0.28 / 63**;
- Monitor expectations: unchanged **v0.28 / 26 adapters**;
- Analysis: unchanged **22 reviews / 97 evidence / 1 production Live input / 1 production revision**.

The observation and evidence dataset version metadata advances to v0.9 because the Live validator requires the three Live dataset versions to remain aligned. The underlying eight observation objects and eleven evidence objects are preserved exactly from the merged CL base.

## Correction / retraction contract

For a Live observation whose `verification_state` is `CORRECTED` or `RETRACTED`, v0.9 now requires:

1. `revision_of_observation_id` resolving to an existing Live observation;
2. at least one referenced Live evidence row carrying `CORRECTION_OR_REVISION`;
3. `observed_at_utc` strictly later than the target observation's `observed_at_utc`;
4. the pre-existing self-reference and acyclic-revision protections;
5. continued separation from state-update lineage.

This is append-only correction history. A prior Live row is preserved rather than silently rewritten.

## Conflicting-report contract

For `verification_state == CONFLICTING_REPORTS`, v0.9 requires:

1. at least two unique evidence records;
2. evidence from at least two distinct providers after `strip` + case-fold normalisation;
3. a non-empty factual `conflict_description`;
4. `conflict_description` to be absent from non-conflicting observations.

The contract does **not** require a winning source or synthetic consensus. It records the fact and scope of disagreement while retaining evidence provenance.

Two records from the same provider cannot manufacture source plurality merely by using different evidence IDs or URLs.

## External data revision remains separate

`DATA_REVISION` retains its existing meaning: a newly observed revision to externally published data may be recorded without inventing a prior WORLD SIGNALS Live row, provided it identifies the external revision target and has `CORRECTION_OR_REVISION` evidence.

CM therefore does not collapse external data-vintage revision into correction/retraction of WORLD SIGNALS history.

## Synthetic contract validation

Permanent test file: `tests/test_live_correction_conflict_cm.py`.

The CM fixture suite proves, without production population:

- valid corrected and retracted append-only descendants;
- failure without correction/revision evidence;
- failure when correction/retraction observation time does not strictly follow its target;
- failure without a revision target;
- valid conflicting-report state with two unique providers and explicit description;
- duplicate evidence IDs cannot satisfy plurality;
- differently cased/spaced names for the same provider cannot satisfy provider plurality;
- blank conflict description fails;
- conflict description outside `CONFLICTING_REPORTS` fails;
- `DATA_REVISION` remains valid without synthetic prior Live history;
- policy drift fails closed;
- all eight existing production observations and eleven evidence rows remain valid and unchanged.

Focused guarded validation passed **14 CM tests + 18 AV foundation tests**.

## Successful guarded transaction

Temporary workflow run: `34441432538`  
Job: `102757107224`  
Transaction pre-materialisation head: `80f343f7760f382e964fe693735649aefd930215`  
Materialisation commit: `aafaa2fb3ffe3acce54e587cb69b5d95bd9d9972`

The guarded transaction passed, on its first attempt:

1. exact `origin/main` and merge-base verification against `1e4a6bbc8670fc36a452740401461f28e313c031`;
2. exact v0.8 / 8-observation / 11-evidence CL prestate checks;
3. byte-semantic equality of all production observation/evidence objects to the merged CL base before mutation;
4. ephemeral v0.9 contract materialisation;
5. focused CM and AV tests;
6. Canonical Registry validator;
7. Live Intelligence validator;
8. Analysis validator;
9. derived-state consistency check;
10. complete historical suite: **1,276 tests passed / 68 historical-prestate skips**;
11. Python compilation;
12. seven JavaScript `node --check` checks;
13. static site build;
14. exact post-materialisation equality of every production observation/evidence object to the merged CL base;
15. proof that no current production row uses `CONFLICTING_REPORTS`, `CORRECTED` or `RETRACTED`;
16. protected-layer nonmutation gate;
17. exact bounded final-diff gate;
18. deletion of temporary write-capable workflow/helper before commit.

Only after all gates passed did the transaction commit and push the reviewed v0.9 contract.

## Protected boundaries

The transaction explicitly proved no mutation to:

- `data/canonical/`;
- `data/sources/`;
- `data/changes/`;
- `data/monitor/`;
- `data/analysis/`;
- `data/coverage/biosecurity_overlay.json`;
- `OPEC_QUARANTINE.md`;
- `tests/test_opec_quarantine_cf.py`.

The temporary write-capable files removed before materialisation commit were:

- `.github/workflows/cm-live-correction-conflict-transaction.yml`;
- `scripts/apply_live_correction_conflict_cm_tmp.py`.

## Authority boundary

Still closed:

- automatic Live ingestion;
- public Live observation projection;
- automatic Canonical commit;
- Google Calendar write;
- automatic Monitor→Live promotion;
- automatic Live→Analysis promotion;
- automatic Analysis population;
- public Live-input projection;
- public Analysis revision/latest-head collapse.

CM grants no source automation permission and changes no Monitor route.

## Waqa Moana boundary

CM does not create a Waqa Moana Live row, conflict row, correction row, retraction row or analytical conclusion. The CL discrepancy remains historical motivating evidence only. A future factual resolution requires fresh competent evidence and a separately reviewed population decision.

## Next-step rule

CM completion does not authorise a ninth Live observation or automatically select a correction/retraction specimen. A post-CM read-only pressure audit must choose the next tranche from current evidence, contract novelty, source rights and cross-layer value. Regional/category zeroes remain prompts rather than queues.
