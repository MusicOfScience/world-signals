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
- Live Intelligence: **v0.8 / 8 observations / 11 evidence rows / 3 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
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

## Current pressure interpretation

Raw population counts are not a selection rule. CK has now corrected the most material issue exposed by CJ's Pacific prompt while also demonstrating that coverage diagnostics must query governed identities, not only human-readable names.

- **Canonical:** 689 occurrences. `WSO-INT-A-0001` / `WSER-INT-PIF-LEADERS` was already present with the correct 30 August–4 September 2026 Palau civil range and stable host binding. CK preserves every timing, identity, host and sensitivity field and changes only its evidence-backed lifecycle/provenance state from `ACTIVE` to `COMPLETED`.
- **Sources:** the existing Palau host source `WSSRC-INT-012` remains unchanged. CK adds supporting-only first-party Cook Islands completion source `WSSRC-INT-036`; it has zero primary Canonical dependencies and no unattended-monitoring permission.
- **Monitor:** 26 adapters / 217 scoped occurrences / 48 scoped series. No PIF Monitor route was created. `CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` zero-scope findings remain review prompts rather than automation permission because the relevant source-governance holdings remain restricted/manual-only at this checkpoint.
- **Live Intelligence:** 7 observations / 2 Canonical-linked. CK creates no PIF Live row. Europe, Latin America, North America and Oceania / Pacific remain useful coverage prompts, not quotas.
- **Analysis:** 22 reviews / 1 production Live input / 1 production revision. PIF completion increases the pool of evidence-backed completed Canonical anchors, but it does not itself authorise a new Analysis review or a Live→Analysis bridge.
- **BARMM:** remains a `PLANNED` 14 September 2026 election occurrence. Do not manufacture post-event analysis before authoritative completion/outcome evidence exists.
- **OPEC CE:** remains excluded from ordinary candidate selection and untouched by CK.

CK's permanent transaction evidence is `data/coverage/PIF_LEADERS_MEETING_CK_TRANSACTION_AUDIT_v0.1.md`. The successful guarded transaction also repaired a class of historical descendant tests that had frozen old Canonical/Source/Ledger checkpoints as permanent ceilings while preserving exact historical prestate tests.

### Post-CK re-audit — CL selected for fresh post-merge design

Read-only coverage run `34422209848` confirms that CK does not create a second Live→Analysis candidate: there are still zero unused completed same-anchor Live observations suitable for that bridge. The Monitor category zeroes remain blocked by source/rights posture, and the empty corporate/financial-market Analysis category remains a prompt rather than a queue.

Fresh first-party review of the completed PIF meeting establishes a stronger bounded next candidate: one factual **scheduled institutional outcome** observation linked `OUTCOME_OF` `WSO-INT-A-0001`. Cook Islands PMO reports that the Leaders' Retreat agreed a Pacific-led framework for engagement with partners and that the meeting's outcomes are captured in the 2026 Forum Communiqué; separate Australian ministerial material confirms an additional PIF-endorsed regional security initiative.

CL is therefore selected **for design after CK/#119 merges**, not for mutation on the CK branch. Selection basis:

1. stable HIGH-importance Canonical anchor is now first-party evidence-backed `COMPLETED`;
2. fresh primary outcome evidence is sufficiently specific for a factual Live observation;
3. `OUTCOME_OF` would exercise a new Live contract: scheduled institutional outcome, distinct from the existing scheduled economic outcome and unlinked institutional-development specimens;
4. it would broaden Live into Oceania / Pacific, but the region's zero count is supporting context rather than the selection rule;
5. no market movement, causal attribution, surprise or Analysis judgement needs to be manufactured.

Permanent selection evidence: `data/coverage/POST_CK_PRESSURE_AUDIT_CL_v0.1.md`.

CL must begin from the exact then-current `main` after user merge and reverify official evidence and repository preconditions. CK does not pre-authorise the Live write, any PIF Monitor route, downstream Analysis, public projection, Canonical mutation or Calendar write.

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
