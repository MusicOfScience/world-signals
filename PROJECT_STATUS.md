# WORLD SIGNALS — current recovery checkpoint

This file is a human recovery surface subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Governed registries/contracts remain operational truth. The current-state block below is mechanically derived from those files and checked by CI against `data/status/current_state.json`.

<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->
## Mechanically derived current state

**Reference date:** 2026-09-10  
**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.

- Canonical Registry: **v0.42 / 689 occurrences**; schema **v0.52**.
- Source Registry: **v2.04 / 258 sources**.
- Change Ledger: **v0.28 / 63 entries**.
- Monitor expectations: **v0.28 / 26 configured adapters / 25 unique monitor sources / 217 explicitly scoped Canonical occurrences**.
- Live Intelligence: **v0.11 / 10 observations / 14 evidence rows / 3 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
- Analysis: schema **v0.8**; reviews **v0.18 / 22**; evidence **v0.18 / 97**; production Live inputs **1**; production revisions **1**.
- NHC Atlantic pilot: **PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT**; registered in scheduled Monitor expectations: **true**.
- Automatic Canonical commit: **OFF**. Google Calendar writes: **OFF**. Public Live and Live-input projection: **OFF**. Public Analysis revision metadata/latest-head collapse: **OFF**.
- OPEC CE remains quarantined; `OPEC_QUARANTINE.md` is present and PR #113 is not a selectable unfinished transaction.
<!-- WORLD_SIGNALS_CURRENT_STATE_END -->

## Authoritative recovery order

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`.
2. Current `main` commit and intervening PRs.
3. `data/canonical/registry.json` and schema.
4. `data/sources/registry.json`.
5. `data/changes/ledger.json`.
6. `data/monitor/expectations.json` and `operations_policy.json`.
7. `data/live_intelligence/` governed stores/schema.
8. `data/analysis/` governed stores/schema.
9. `data/status/current_state.json` as a mechanically derived cross-check.
10. Latest pressure and transaction audits.
11. `OPEC_QUARANTINE.md` whenever OPEC is implicated.

The snapshot and prose documents are not permitted to override the governed files. CI should fail if their current-state blocks drift from derivable registry/contract state.

## Recent merged lineage

### PR #112 — CD: first controlled Analysis revision — MERGED

CD materialised one immutable child Analysis revision for the BWC Working Group case. The parent snapshot remains preserved. Public revision metadata projection, automatic latest-head selection and public revision-head collapse remain off.

### PR #113 — CE OPEC primary outcome provenance — CLOSED / UNMERGED / QUARANTINED

This is historical evidence only. Do not reopen, merge, cherry-pick, rebase, materialise or use the CE branch as a base during routine work. OPEC provenance debt is non-blocking for unrelated work.

### PR #114 — CF: Monitor pressure audit + NHC pilot — MERGED

CF recomputed explicit Monitor pressure and validated a bounded NOAA/NHC Atlantic-season route over exactly two existing Canonical occurrences. CF itself stopped at pilot validation; scheduled activation was separately pressure-audited and reviewed in PR #117.

### PR #115 — CG: reviewed BARMM pre-election Live context — MERGED

CG added one primary-confirmed Southeast Asia institutional Live observation linked `CONTEXT_FOR` the existing 14 September 2026 BARMM election occurrence. It did not mutate Canonical timing or provenance and did not create Analysis automatically.

CG also repaired historical tests that incorrectly froze the BF Live checkpoint as the permanent current head. Historical rows remain tested by identity/semantics while reviewed descendants are allowed.

### PR #116 — CH: derived recovery-state truth — MERGED

CH made cross-layer current-state counts mechanically derivable and CI-checked across `README.md`, `PROJECT_STATUS.md`, `ROADMAP.md` and `data/status/current_state.json`. The derived snapshot is explicitly noncanonical and cannot mutate upstream governed layers.

### PR #117 — CI: bounded NHC Atlantic-season Monitor sentinel — MERGED

CI activated the CF-validated NHC route after a fresh source, rights, endpoint, scope and runtime review. The scheduled route remains bounded to two existing Atlantic hurricane-season occurrences; NHC climatology is semantic authority for the season definition and Atlantic RSS is health corroboration only. It grants no automatic Canonical, lifecycle, Calendar, Live or Analysis authority.

### PR #118 — CJ: cross-layer coverage / pressure diagnostic — MERGED

CJ added the read-only Canonical→Monitor→Live→Analysis coverage diagnostic and reconciled the post-#117 recovery prose. Its first regional comparison also exposed and corrected two audit-only taxonomy-granularity artifacts rather than treating them as real coverage gaps.

CJ then flagged the Pacific Islands Forum Leaders Meeting as apparently absent from Canonical. CK subsequently proved that specific absence conclusion wrong: the stable PIF occurrence and series already existed but were not found by the literal-name discovery path used in the pressure review. The CJ audit remains historical evidence; CK adds a stronger identity-discovery control rather than rewriting CJ's frozen artifact.

### PR #119 — CK: PIF lifecycle/provenance completion repair — MERGED

CK corrected CJ's apparent PIF absence finding after an identity-aware probe found the existing stable `WSO-INT-A-0001` / `WSER-INT-PIF-LEADERS` family. It preserved the event's Palau civil-date timing, host binding and sensitivity metadata, moved lifecycle from `ACTIVE` to first-party-evidence-backed `COMPLETED`, added one supporting-only Cook Islands completion source, and repaired descendant-unsafe historical Canonical/Source/Ledger assertions. No PIF Monitor, Live or Analysis row was created in CK.

## Current pressure interpretation

CM is now materialised on the feature branch as a **no-production-population Live contract hardening tranche**. The mechanically derived block above is current: Live is v0.9 while production remains exactly 8 observations / 11 evidence / 3 Canonical-linked.

- **Canonical:** unchanged v0.42 / 689 occurrences. CM creates or mutates no Canonical identity, timing, lifecycle or provenance.
- **Sources / Change Ledger / Monitor:** unchanged v2.04 / 258 sources, v0.28 / 63 changes and v0.28 / 26 Monitor adapters. CM grants no automation permission and creates no route.
- **Live Intelligence:** v0.9 / 8 / 11 / 3 linked. `CORRECTED` / `RETRACTED` now require an explicit prior Live target, correction/revision evidence and strictly later observation time. `CONFLICTING_REPORTS` requires at least two unique evidence records from at least two distinct normalised providers plus a factual `conflict_description`. No winner or synthetic consensus is required. `conflict_description` is prohibited outside the conflict state.
- **Population:** all eight production observation objects and all eleven evidence objects are preserved exactly from merged CL. No current production row uses `CONFLICTING_REPORTS`, `CORRECTED` or `RETRACTED`.
- **External revisions:** `DATA_REVISION` remains distinct and may describe a newly observed revision to external data without inventing prior WORLD SIGNALS Live history.
- **Analysis:** unchanged 22 reviews / 97 evidence / 1 production Live input / 1 production revision. No automatic Live→Analysis relationship was created.
- **Waqa Moana:** remains historical motivating evidence only. CM does not reinterpret, resolve or populate it.
- **BARMM:** remains pre-election context for the planned 14 September 2026 occurrence; no outcome or post-event Analysis is manufactured early.
- **OPEC CE:** remains quarantined and excluded.

CM permanent transaction evidence is `data/live_intelligence/LIVE_CORRECTION_CONFLICT_CM_TRANSACTION_AUDIT_v0.1.md`. Guarded run `34441432538` / job `102757107224` passed on the first attempt, including **1,276 tests** with 68 historical-prestate skips, all governed validators, derived-state consistency, Python compilation, seven JavaScript checks, static build, exact production-row invariance, protected-layer nonmutation and bounded final diff. Temporary transaction machinery was removed before materialisation commit.

### Post-CM pressure — CN selected for fresh post-merge design

Read-only coverage run `34441643238` confirms the expected no-population result. Canonical remains 689 / 203 series, Monitor 26 adapters / 217 occurrences / 48 series, Live 8 / 3 linked, and Analysis 22 reviews / 1 Live input / 1 revision. Europe, Latin America and North America remain zero-Live prompts. PIF remains completed-linked without an Analysis review, but there is still no unused completed same-anchor Analysis target. Monitor category zeroes and the corporate/market Analysis zero remain prompts rather than queues.

Fresh qualitative comparison identifies a stronger next population candidate: Brazil's 9 September 2026 fuel-policy intervention. The Ministério da Fazenda states that the Federal Government adopted measures reducing federal PIS/Pasep and Cofins on gasoline and hydrated ethanol and authorising an adjustable road-diesel subsidy amid international oil-price volatility and supply restrictions that the government associates with geopolitical conflict.

`data/coverage/POST_CM_PRESSURE_AUDIT_CN_v0.1.md` therefore selects **CN — Brazil fuel-policy Live broadening** for fresh design only after CM merges. The candidate is selected because it is independently important and exercises an unscheduled Latin American fiscal/commodity/geopolitical transmission signal, not because Latin America has a zero.

The selection is deliberately conditional. At the time of review, the Ministry announcement is clearer than the fully retrievable final legal-instrument trail. CN must freshly recheck Presidency/Planalto, Diário Oficial and Ministry sources after merge; must revise or abandon the candidate if evidence changes; and must not pre-write `in force`, exact legal numbering, exact UTC publication/event time, observed price/inflation effects, a Canonical occurrence, a Monitor route or an Analysis conclusion without separate support.

Current North American Canada–U.S. tariff escalation and European oil-security context remain credible future Live candidates but are deferred rather than appended mechanically. PIF Analysis and a market-structure review remain unjustified if their only purpose is to manufacture a bridge candidate or erase a histogram zero.

## Write and authority boundaries

Still closed unless a later reviewed architecture explicitly changes them:

- automatic Canonical commit;
- Google Calendar write;
- Monitor lifecycle/certainty/clock authority by default;
- automatic new Canonical occurrence creation from unrecognised monitor items;
- automatic Monitor→Live promotion;
- automatic Live→Analysis promotion;
- public Live observation projection;
- public Live-input projection;
- automatic latest Analysis selection;
- public Analysis revision-head collapse.

Calendar/Pages remain derived outputs. Melbourne remains a display/reference timezone, never a reason to rewrite canonical native/UTC timing.

## Recovery incident note — CH branch initialisation

During the CH state-truth tranche, an empty `data/status/.gitkeep` was accidentally written directly to `main` before the feature branch existed. It touched no governed population or contract file. The file was immediately deleted in the next `main` commit, restoring the post-CG tree before CH implementation proceeded from a fresh branch. This operational mistake is retained here rather than hidden; future branch initialisation must create the branch before any contents write.

## Validation entry point

Run:

```bash
python scripts/validate_registry.py
python scripts/validate_live_intelligence.py
python scripts/validate_analysis.py
python scripts/project_state_snapshot.py --check
python -m unittest discover -s tests -v
python scripts/run_cross_layer_coverage_audit.py
python scripts/build_site.py
```

The derived-state checker must remain read-only in CI. Its explicit `--write` mode is restricted to the derived snapshot and the three marked documentation blocks and requires `WORLD_SIGNALS_WRITE_DERIVED_STATE=YES`. The cross-layer coverage audit is also read-only and writes only disposable artifacts under `artifacts/coverage/`.
