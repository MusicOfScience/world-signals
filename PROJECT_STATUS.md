# WORLD SIGNALS — current recovery checkpoint

This file is a human recovery surface subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Governed registries/contracts remain operational truth. The current-state block below is mechanically derived from those files and checked by CI against `data/status/current_state.json`.

<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->
## Mechanically derived current state

**Reference date:** 2026-09-10  
**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.

- Canonical Registry: **v0.41 / 689 occurrences**; schema **v0.52**.
- Source Registry: **v2.02 / 257 sources**.
- Change Ledger: **v0.27 / 62 entries**.
- Monitor expectations: **v0.27 / 25 configured adapters / 24 unique monitor sources / 215 explicitly scoped Canonical occurrences**.
- Live Intelligence: **v0.7 / 7 observations / 10 evidence rows / 2 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
- Analysis: schema **v0.8**; reviews **v0.18 / 22**; evidence **v0.18 / 97**; production Live inputs **1**; production revisions **1**.
- NHC Atlantic pilot: **PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT**; registered in scheduled Monitor expectations: **false**.
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

CF recomputed explicit Monitor pressure and validated a bounded NOAA/NHC Atlantic-season route over exactly two existing Canonical occurrences. The route remains a pilot: validated architecture does not equal scheduled Monitor activation.

### PR #115 — CG: reviewed BARMM pre-election Live context — MERGED

CG added one primary-confirmed Southeast Asia institutional Live observation linked `CONTEXT_FOR` the existing 14 September 2026 BARMM election occurrence. It did not mutate Canonical timing or provenance and did not create Analysis automatically.

CG also repaired historical tests that incorrectly froze the BF Live checkpoint as the permanent current head. Historical rows remain tested by identity/semantics while reviewed descendants are allowed.

## Current pressure interpretation

Raw population counts are not a selection rule.

- **Canonical** is broad enough that no current evidence justifies bulk population.
- **Monitor** is comparatively mature at the current configured cohort. The NHC pilot remains a legitimate activation candidate, but only after a fresh source/rights/endpoint review and a new pressure decision.
- **Live Intelligence** is still intentionally small. Two observations now link to Canonical occurrences, exercising both `OUTCOME_OF` and `CONTEXT_FOR` relationships.
- **Analysis** remains conservative. A second production Live→Analysis link is not currently authorised by mere count pressure. In particular, the BARMM occurrence is still pre-event and therefore cannot support a reviewed post-event Analysis packet under the present schema.
- **OPEC CE** is excluded from ordinary candidate selection.

The next tranche after the current state-truth hardening must recompute pressure from then-current `main`; it should not assume NHC activation, another Live observation or another Analysis revision in advance.

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
python scripts/build_site.py
```

The derived-state checker must remain read-only in CI. Its explicit `--write` mode is restricted to the derived snapshot and the three marked documentation blocks and requires `WORLD_SIGNALS_WRITE_DERIVED_STATE=YES`.
