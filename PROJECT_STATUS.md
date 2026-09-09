# WORLD SIGNALS — current recovery checkpoint

This file is a human recovery surface subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Governed registries/contracts remain operational truth. The current-state block below is mechanically derived from those files and checked by CI against `data/status/current_state.json`.

<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->
## Mechanically derived current state

**Reference date:** 2026-09-10  
**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.

- Canonical Registry: **v0.41 / 689 occurrences**; schema **v0.52**.
- Source Registry: **v2.03 / 257 sources**.
- Change Ledger: **v0.27 / 62 entries**.
- Monitor expectations: **v0.28 / 26 configured adapters / 25 unique monitor sources / 217 explicitly scoped Canonical occurrences**.
- Live Intelligence: **v0.7 / 7 observations / 10 evidence rows / 2 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
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

## Current pressure interpretation

Raw population counts are not a selection rule. CJ's corrected cross-layer audit now gives an evidence-backed next-pressure boundary.

- **Canonical:** 689 occurrences / 203 series. The CJ review identified a likely upstream omission of the annual Pacific Islands Forum Leaders Meeting, an apex 18-member Pacific political institution. This is a stronger repair candidate than bulk Canonical growth.
- **Monitor:** 26 adapters / 217 scoped occurrences / 48 scoped series. Every Canonical region has at least some configured Monitor scope. `CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` remain zero-scope categories, but their underlying WHO / UNFCCC / CBD / IPCC sources are rights-held/manual-only at this checkpoint; zero scope is not automation permission.
- **Live Intelligence:** 7 observations / 2 Canonical-linked. After explicit audit-only regional equivalence, Europe, Latin America, North America and Oceania / Pacific have no controlled Live specimen. These are review prompts, not a population queue.
- **Analysis:** 22 reviews / 1 production Live input / 1 production revision. The sole production Live input remains Japan FIES. `CORPORATE_FINANCIAL_MARKET_STRUCTURE` has no Analysis review, but that count does not itself justify adding one.
- **Live→Analysis frontier:** there are zero unused completed same-anchor candidates. BARMM remains linked to a `PLANNED` 14 September 2026 occurrence and cannot be promoted into post-event Analysis before completion/outcome evidence exists.
- **OPEC CE:** remains excluded from ordinary candidate selection.

CJ implements the read-only diagnostic and records its corrected evidence in `data/coverage/POST_CI_CROSS_LAYER_PRESSURE_CJ_v0.1.md`. The audit uses only two explicit, nonmutating comparison mappings (`Central Africa -> Africa`; `Global -> Cross-regional / Global`) to avoid manufacturing gaps from taxonomy granularity.

### Next selected after CJ merge — CK Pacific Islands Forum upstream repair

Subject to a fresh branch from post-CJ `main`, CK should:

1. confirm no hidden equivalent PIF series/occurrence exists;
2. establish a stable Pacific Islands Forum Leaders Meeting series if the omission is real;
3. add the completed 55th Leaders Meeting in Koror, Palau, **30 August–4 September 2026**, preserving civil-date range precision;
4. register/reuse minimum authoritative provenance sources with current source-governance review;
5. preserve New Zealand/Auckland as confirmed 2027 host context without inventing meeting dates;
6. separately decide whether the 2026 Forum Communiqué justifies one bounded Oceania / Pacific Live `OUTCOME_OF` specimen; CJ does not pre-authorise it;
7. create no automatic Monitor route and open no automatic Canonical/Calendar/Live/Analysis gate.

If primary provenance or identity checks fail, CK must stop or redesign rather than duplicate or fabricate.

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
