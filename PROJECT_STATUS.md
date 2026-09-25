# WORLD SIGNALS — current recovery checkpoint

This file is a human recovery surface subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Governed registries/contracts remain operational truth. The current-state block below is mechanically derived from those files and checked by CI against `data/status/current_state.json`.

<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->
## Mechanically derived current state

**Reference date:** 2026-09-10  
**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.

- Canonical Registry: **v0.43 / 689 occurrences**; schema **v0.52**.
- Source Registry: **v2.04 / 258 sources**.
- Change Ledger: **v0.29 / 64 entries**.
- Monitor expectations: **v0.28 / 26 configured adapters / 25 unique monitor sources / 217 explicitly scoped Canonical occurrences**.
- Live Intelligence: **v0.12 / 11 observations / 15 evidence rows / 4 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
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
11. `HANDOFF_PROTOCOL.md` for the human merge-control boundary.
12. `OPEC_QUARANTINE.md` whenever OPEC is implicated.

The snapshot and prose documents are not permitted to override the governed files. CI should fail if their current-state blocks drift from derivable registry/contract state.

## Human merge-control boundary

`HANDOFF_PROTOCOL.md` is a mandatory recovery control. Every pull-request handoff to the user must say exactly one of:

- **MERGE NOW — PR #N**; or
- **DO NOT MERGE — PR #N**.

A PR URL or clickable link must **not** be supplied while the state is `DO NOT MERGE`. Earlier green runs never authorise merging after a later commit; required checks must pass on the actual final head. Hosted CI remains the normal mode. The tightly bounded local exact-head fallback in `HANDOFF_PROTOCOL.md` is available only after explicit project-owner activation for a known hosted-CI outage or allowance limit, with full command parity, evidence and residue controls. The user performs merges. The assistant does not.

Every next-chat or recovery handover must repeat this rule explicitly so ambiguity at the final human control point cannot defeat otherwise guarded repository work.

## Recent merged lineage

### PR #112 — CD: first controlled Analysis revision — MERGED

CD materialised one immutable child Analysis revision for the BWC Working Group case. The parent snapshot remains preserved. Public revision metadata projection, automatic latest-head selection and public revision-head collapse remain off.

### PR #113 — CE OPEC primary outcome provenance — CLOSED / UNMERGED / QUARANTINED

Historical evidence only. Do not reopen, merge, cherry-pick, rebase, materialise or use the CE branch as a base during routine work. OPEC provenance debt is non-blocking for unrelated work.

### PR #114 — CF: Monitor pressure audit + NHC pilot — MERGED

CF recomputed explicit Monitor pressure and validated a bounded NOAA/NHC Atlantic-season route over exactly two existing Canonical occurrences. CF itself stopped at pilot validation; scheduled activation was separately pressure-audited and reviewed in PR #117.

### PR #115 — CG: reviewed BARMM pre-election Live context — MERGED

CG added one primary-confirmed Southeast Asia institutional Live observation linked `CONTEXT_FOR` the existing 14 September 2026 BARMM election occurrence. It did not mutate Canonical timing or provenance and did not create Analysis automatically.

### PR #116 — CH: derived recovery-state truth — MERGED

CH made cross-layer current-state counts mechanically derivable and CI-checked across `README.md`, `PROJECT_STATUS.md`, `ROADMAP.md` and `data/status/current_state.json`. The derived snapshot is explicitly noncanonical and cannot mutate upstream governed layers.

### PR #117 — CI: bounded NHC Atlantic-season Monitor sentinel — MERGED

CI activated the CF-validated NHC route after fresh source, rights, endpoint, scope and runtime review. The scheduled route remains bounded to two existing Atlantic hurricane-season occurrences and grants no automatic Canonical, lifecycle, Calendar, Live or Analysis authority.

### PR #118 — CJ: cross-layer coverage / pressure diagnostic — MERGED

CJ added the read-only Canonical→Monitor→Live→Analysis coverage diagnostic. CK later demonstrated that CJ's literal-name PIF absence check was insufficient, strengthening identity discovery without rewriting the frozen CJ artifact.

### PR #119 — CK: PIF lifecycle/provenance completion repair — MERGED

CK preserved the existing `WSO-INT-A-0001` / `WSER-INT-PIF-LEADERS` identity, repaired stale lifecycle `ACTIVE → COMPLETED` using first-party evidence, added one supporting-only Cook Islands source, and repaired descendant-unsafe historical checkpoint assertions. No PIF Monitor, Live or Analysis row was created in CK.

### PR #120 — CL: bounded PIF Live institutional outcome — MERGED

CL added one primary-confirmed PIF partner-engagement framework outcome linked `OUTCOME_OF` the completed PIF Canonical occurrence. It deliberately excluded Waqa Moana because reviewed official formulations did not align cleanly enough to justify choosing a stronger wording.

### PR #121 — CM: Live correction / retraction / conflict contract hardening — MERGED

CM changed capability rather than population. Live correction/retraction states now require explicit prior-target, evidence and chronology controls; `CONFLICTING_REPORTS` requires genuinely plural source evidence plus a factual conflict description. CM does not adjudicate a winner or manufacture consensus.

### PR #122 — CN: bounded Brazil fuel-policy Live specimen — MERGED

CN added one unscheduled Brazilian fuel-policy development using official Finance Ministry evidence, while refusing to overstate legal publication/effective status, exact UTC timing, inflation effects or market effects. Live advanced to v0.10 / 9 observations / 12 evidence / 3 Canonical-linked.

### PR #123 — CO: bounded Canada counter-tariff Live specimen — MERGED

CO added one Canadian counter-tariff implementation observation using Department of Finance Canada and CBSA evidence, keeping the separate U.S. sovereign response out of the Canadian row. Live advanced to v0.11 / 10 observations / 14 evidence / 3 Canonical-linked.

### PR #124 — CP: bounded ECB monetary-policy outcome — MERGED

CP preserved the existing ECB 10 September monetary-policy decision identity, completed its lifecycle from direct ECB evidence, and added one primary-confirmed Live outcome linked `OUTCOME_OF` that Canonical occurrence. Canonical advanced to v0.43 / 689 with one lifecycle-ledger entry; Live advanced to v0.12 / 11 observations / 15 evidence / 4 Canonical-linked.

### PR #125 — CQ: China–Africa CDEP architecture research — OPEN / SUPERSEDED / DO NOT MERGE

CQ contains two read-only research files on the old post-CP base. It was blocked by hosted-runner admission before CR-CX advanced current main. CY rechecks its substantive thesis from current main and current primary evidence. The stale CQ branch is historical evidence only and is not a merge candidate.

### PR #126 — CR: bounded local exact-head validation fallback — MERGED

CR added the owner-authorised local exact-head validation fallback for known hosted-CI admission/allowance failures. Hosted CI remains normal; the fallback requires exact remote SHA parity, complete applicable command parity, clean-worktree/residue controls, explicit activation and an auditable exact-head record.

### PR #127 — CS: read-only local operations runtime — MERGED

CS added a guarded local operating path that validates governed inputs, polls configured source monitors, retains private local evidence and produces sanitized browser projections without automatic governed writes.

### PR #128 — CT: production cross-domain risk overlay — MERGED

CT added a derived read-only risk/convergence browser layer over Canonical fields. It exposes domain/timing convergence without probability, forecast, composite score, causal attribution or governed mutation.

### PR #129 — CU: rolling-calendar monitor-health repair — MERGED

CU repaired INDEC rolling-calendar semantics and explicitly classified the Elections NZ perimeter block as source-health degradation rather than event-state evidence.

### PR #130 — CV: operator review workspace — MERGED

CV added the retained-review operator workspace and routing metadata while preserving the boundary between review attention, approval and any later governed transaction.

### PR #131 — CW: guarded local operations service — MERGED

CW packaged the guarded local runner and loopback dashboard as reviewable macOS user LaunchAgents. Merge added capability only; installation remained a separate explicit owner action.

### PR #132 — CX: macOS local-service startup-directory repair — MERGED

CX repaired the launchd working-directory failure by moving service execution to a neutral Application Support directory while preserving exact reviewed repository paths, loopback binding, clean-main enforcement and all write prohibitions.

## Current pressure interpretation — CY current-main recovery / CDEP pressure reconciliation

Current main is `5740b5baa33a992e291abc66ce67f0f6172d53a2` after PR #132. The mechanically derived block above is current; the stale portion was the human narrative, which still described CO as the active handoff despite CP and CR-CX already being merged.

CY is a **read-only recovery and pressure tranche**. It mutates no governed population or source/monitor contract.

Current governed state remains:

- Canonical v0.43 / 689 occurrences / 203 series;
- Sources v2.04 / 258;
- Change Ledger v0.29 / 64;
- Monitor v0.28 / 26 adapters / 217 explicitly scoped occurrences;
- Live v0.12 / 11 observations / 15 evidence / 4 Canonical-linked;
- Analysis v0.18 / 22 reviews / 97 evidence / 1 production Live input / 1 production revision.

### CQ recovery decision

Open PR #125 is based on stale post-CP main and must **not** be merged. Its two research files remain historical evidence.

CY independently rechecks that research against current main and current primary sources rather than rebasing/cherry-picking the old branch.

### Fresh China–Africa CDEP finding

Current MOFCOM evidence continues to establish the China–Africa Common Development Economic Partnership as a genuine multi-country programme family:

- Cabo Verde signed a framework agreement on 9 September 2026 and MOFCOM describes it as the 40th African framework agreement;
- the same Cabo Verde release separately records substantive conclusion of early-harvest negotiations, not an early-harvest signing/effectiveness state;
- MOFCOM records a Seychelles Early Harvest Arrangement signed on 10 September 2026, demonstrating a later programme phase.

CY therefore keeps the CQ architecture conclusion while making the implementation sequence stricter:

`research / programme architecture → source governance → bounded sample only if still justified`.

Do not create a 40-country Canonical backfill, a synthetic global CDEP Canonical series, or a Cabo Verde Canonical anchor merely to manufacture an `OUTCOME_OF` link.

Existing `TRADE_SANCTIONS_INDUSTRIAL_POLICY / TRADE_POLICY_PROCESS` grammar remains sufficient at generic category/event-type level.

### Next pressure selected conditionally — CZ

CY selects **CZ — bounded MOFCOM trade-source governance** for fresh post-merge design.

CZ should, at most, establish one appropriately scoped MOFCOM source identity after fresh then-current registry/rights/role review. It should create **no Live observation and no Canonical occurrence**. Unattended monitoring, bulk crawling and treaty mirroring remain closed unless separately justified.

Only after provenance/source governance is stable should a later pressure review consider one Cabo Verde Live sample.

Permanent CY evidence:

- `data/coverage/POST_CX_RECOVERY_PRESSURE_CY_v0.1.md`;
- `data/coverage/CHINA_AFRICA_CDEP_CY_RESEARCH_v0.1.md`.

### Merge-control state

Until CY has its own PR, final-head validation/coverage, structural diff and residue checks, the merge state is **DO NOT MERGE** for any future CY PR. No PR link should be supplied before a later explicit `MERGE NOW — PR #N` handoff.

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

During the CH state-truth tranche, an empty `data/status/.gitkeep` was accidentally written directly to `main` before the feature branch existed. It touched no governed population or contract file. The file was immediately deleted in the next `main` commit, restoring the post-CG tree before CH implementation proceeded from a fresh branch. This operational mistake is retained rather than hidden; future branch initialisation must create the branch before any contents write.

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
