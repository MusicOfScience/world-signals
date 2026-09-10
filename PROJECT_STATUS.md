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
- Live Intelligence: **v0.9 / 8 observations / 11 evidence rows / 3 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
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

CL is now materialised on the feature branch as one bounded scheduled institutional-outcome Live specimen. Population counts remain diagnostic rather than selection rules.

- **Canonical:** unchanged v0.42 / 689. The completed PIF anchor `WSO-INT-A-0001` remains byte-semantically unchanged by CL: 30 August–4 September 2026, `Pacific/Palau`, DAY precision, confirmed lifecycle completion from CK.
- **Sources / Change Ledger / Monitor:** unchanged v2.04 / 258 sources, v0.28 / 63 changes and v0.28 / 26 Monitor adapters. CL creates no PIF Monitor route and acquires no automation permission from the Cook Islands evidence page.
- **Live Intelligence:** v0.8 / 8 observations / 11 evidence / 3 Canonical-linked. CL adds exactly one `PRIMARY_CONFIRMED` `INSTITUTIONAL_DEVELOPMENT`, `WSLI-INST-PIF-PARTNER-FRAMEWORK-20260904-001`, linked `OUTCOME_OF` the completed PIF anchor. Its factual scope is the Leaders' Retreat resolution of a Pacific-led framework for engagement with partners. It does not represent the whole Forum Communiqué and contains no Analysis fields.
- **Fresh evidence correction:** CL excluded Waqa Moana after finding unreconciled institutional-status wording: the Australian PM release used `unanimously endorsed`, while indexed final-communiqué text used `agreed in principle` and noted further national consultations. The final Forum Secretariat PDF was not directly retrievable through the controlled automated path, so CL did not choose a stronger formulation or invent a reconciliation.
- **Analysis:** unchanged 22 reviews / 1 production Live input / 1 production revision. The post-CL frontier now contains one completed linked Live observation without an Analysis review — PIF — but still **zero bridge-ready completed same-anchor candidates**. PIF is not automatically promoted into Analysis.
- **BARMM:** remains linked pre-election context for the `PLANNED` 14 September 2026 occurrence; no post-event outcome or Analysis is manufactured before authoritative completion evidence.
- **OPEC CE:** remains quarantined and excluded.

CL's permanent transaction evidence is `data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_TRANSACTION_AUDIT_v0.1.md`. Successful guarded run `34436154025` passed exact-base gating, focused CL tests, all governed validators, derived-state consistency, **1,262 tests** with 68 historical-prestate skips, Python compilation, seven JavaScript checks, static build and bounded/protected-layer gates. Temporary write-capable scaffolding was removed after materialisation.

### Post-CL pressure — CM selected for fresh post-merge design

Read-only coverage run `34436436416` confirms Live is now 8 / 3 linked and removes Oceania / Pacific from the zero-Live prompt set. Europe, Latin America and North America remain prompts only. `CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` still have no configured Monitor scope, and `CORPORATE_FINANCIAL_MARKET_STRUCTURE` still has no Analysis review; none is a queue.

The stronger current pressure is a capability weakness exposed by CL's source disagreement. Live already names `CONFLICTING_REPORTS`, `CORRECTED` and `RETRACTED`, but the executable contract is not mature enough for broader population: correction/retraction does not yet require correction-role evidence or later chronology, and conflicting-report state does not yet require distinct providers plus an explicit factual disagreement description.

`data/coverage/POST_CL_PRESSURE_AUDIT_CM_v0.1.md` therefore selects **CM — Live correction / retraction / conflicting-report contract hardening** for fresh design only after CL is merged. CM should be a no-production-population foundation: strengthen schema/validator invariants and prove them with synthetic fixtures, while preserving all eight Live rows and eleven evidence rows. It must not reinterpret Waqa, create a synthetic conflict specimen, open public projection, create another Live→Analysis link, or mutate Canonical/Monitor/Analysis state.

The post-CL audit also explicitly rejects two tempting shortcuts: creating a PIF Analysis review merely to manufacture a bridge target, and backfilling a mechanical market-structure event merely to erase the last Analysis category zero.

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
