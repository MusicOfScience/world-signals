# WORLD SIGNALS — capability roadmap

This roadmap is subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Stages describe architectural capability, not permission for bulk population. Current numeric state is mechanically derived and CI-checked rather than manually repeated across historical stage prose.

<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->
## Mechanically derived current state

**Reference date:** 2026-09-10  
**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.

- Canonical Registry: **v0.42 / 689 occurrences**; schema **v0.52**.
- Source Registry: **v2.04 / 258 sources**.
- Change Ledger: **v0.28 / 63 entries**.
- Monitor expectations: **v0.28 / 26 configured adapters / 25 unique monitor sources / 217 explicitly scoped Canonical occurrences**.
- Live Intelligence: **v0.7 / 7 observations / 10 evidence rows / 2 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
- Analysis: schema **v0.8**; reviews **v0.18 / 22**; evidence **v0.18 / 97**; production Live inputs **1**; production revisions **1**.
- NHC Atlantic pilot: **PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT**; registered in scheduled Monitor expectations: **true**.
- Automatic Canonical commit: **OFF**. Google Calendar writes: **OFF**. Public Live and Live-input projection: **OFF**. Public Analysis revision metadata/latest-head collapse: **OFF**.
- OPEC CE remains quarantined; `OPEC_QUARANTINE.md` is present and PR #113 is not a selectable unfinished transaction.
<!-- WORLD_SIGNALS_CURRENT_STATE_END -->

## Stage 0 — research architecture and source governance — ACTIVE / MATURE

Maintain the Charter disciplines for identity, lifecycle, certainty, time, provenance, rights, international coverage and analytical uncertainty. Research remains continuous because schedules, institutions, endpoints and rights change.

Coverage balance remains diagnostic rather than quota-driven. Machine-interface convenience must not masquerade as importance or permission.

## Stage 1 — Canonical Registry and derived projections — DONE / GUARDED

The repository validates stable Canonical event identities and produces rebuildable browser/calendar projections. Date changes update existing identities with history rather than creating duplicates. Civil dates, native windows, recurring rules and conditional states retain their supported precision.

Google Calendar is not canonical state and write access remains off.

## Stage 2 — heterogeneous Source / Change Monitor — DONE / EXPANDING CAUTIOUSLY

The governed Monitor cohort now spans multiple source contracts and regions. The authoritative route list is `data/monitor/expectations.json`; current count is in the derived state block above.

Shared boundary:

```text
fetch -> snapshot -> parse -> assert -> match -> diff -> review candidate
```

Adapters do not receive schedule, lifecycle, certainty, clock or Canonical-write authority merely because they can observe a source. Source competence and unattended-monitoring permission remain separate decisions.

### CF / CI — NOAA/NHC Atlantic-season route — VALIDATED IN CF / ACTIVATED IN PR #117

CF validated a bounded physical-climate-risk pilot for exactly two existing Atlantic hurricane-season Canonical occurrences. NHC climatology is the season-definition authority; RSS is source-health/operational corroboration only.

PR #117 separately rechecked current source competence, endpoint behaviour, robots/appropriate-use conditions, automation rights, exact scope and registered runtime before activating the route into scheduled Monitor expectations. The route remains review-only: storm activity, RSS presence/absence and elapsed season time have no lifecycle, schedule, certainty, completion, Canonical-write, Calendar-write, Live-promotion or Analysis-promotion authority.

## Stage 3 — scheduled monitoring and retained operational evidence — DONE

Scheduled read-only monitoring produces dated source-health and review evidence. Runtime failures, parser failures and source absence remain distinct from Canonical event state. Retained Actions evidence is not a database and does not silently become Canonical, Live or Analysis state.

## Stage 4 — reviewed controlled transactions — IMPLEMENTED / GUARDED

WORLD SIGNALS uses fail-closed reviewed transaction patterns:

```text
reviewed proposal -> exact prestate -> bounded mutation -> validators -> full suite -> mutation audit -> PR
```

Historical checkpoints remain frozen as history while later reviewed descendants are validated against tranche-owned invariants rather than obsolete permanent count ceilings.

A generic automatic candidate-to-Canonical commit system is not authorised. Automatic Canonical commit remains off.

## Stage 5 — controlled Live Intelligence — IMPLEMENTED / BOUNDED

Live Intelligence has moved beyond its zero-population foundation through deliberately different specimens rather than a general news feed. The controlled population has exercised:

- unscheduled physical shock without invented Canonical identity;
- evolving health state where later state is not silent revision;
- scheduled economic outcome linked `OUTCOME_OF` Canonical;
- unscheduled geopolitical development;
- institutional development without synthetic Canonical anchoring;
- reviewed pre-event institutional context linked `CONTEXT_FOR` an existing Canonical election occurrence.

Live remains factual. Causal interpretation, market attribution, automatic ingestion, public observation projection, automatic story clustering and automatic downstream promotion remain closed.

### CG — BARMM pre-election context — DONE / BOUNDED

CG adds one reviewed Southeast Asia `CONTEXT_FOR` relationship to the existing 14 September 2026 BARMM election occurrence. Live evidence has no authority to rewrite COMELEC-governed timing or provenance. No real-world signing clock was manufactured from publication timing.

## Stage 6 — Live Intelligence → Analysis bridge — FIRST PRODUCTION LINK DONE / PUBLIC CLOSED

The bridge selects immutable Live `observation_id` values explicitly. Live evidence is not transitively migrated into Analysis evidence, upstream Live rows remain immutable, and story/latest selectors remain prohibited.

Exactly one production Live input is currently populated. A second relationship requires a fresh pressure audit and a valid post-event Analysis target. The BARMM context cannot be forced downstream while its Canonical occurrence remains pre-event under the current Analysis contract.

## Stage 7 — Analysis revision lineage — FIRST PRODUCTION REVISION DONE / PUBLIC CLOSED

Analysis revisions are immutable descendants, not in-place rewrites. CD materialised the first controlled child revision for the BWC Working Group case while preserving the parent snapshot.

Automatic latest-head selection, public revision metadata and public head collapse remain off. A second production revision requires a new pressure audit.

## Stage 8 — recovery/status truth surfaces — DONE / GUARDED

CH addresses an operational governance weakness exposed after CG: `README.md`, `PROJECT_STATUS.md` and `ROADMAP.md` contained materially stale counts and checkpoint language even though governed registries were correct.

CH introduces `data/status/current_state.json` plus `scripts/project_state_snapshot.py` so CI derives current cross-layer state from governed files and fails when the checked-in snapshot or the marked current-state blocks drift.

The snapshot is explicitly noncanonical and may not mutate upstream layers. Its write mode is limited to derived recovery surfaces and requires an explicit environment gate.

## Stage 9 — CI NHC activation — DONE / GUARDED

The post-CH pressure review selected the CF-validated NHC Atlantic-season route because it exercised a genuinely new scheduled `PHYSICAL_CLIMATE_RISK` Monitor contract, not because Monitor had the smallest count. PR #117 activated the exact bounded route after fresh official-source, rights, endpoint, scope and runtime validation.

Result:

- NHC is now registered in scheduled Monitor expectations;
- the route covers exactly two existing Atlantic hurricane-season Canonical occurrences;
- semantic drift creates review evidence only;
- Canonical, Change Ledger, Monitor operations policy, Live and Analysis populations were not mutated;
- all automatic write/promotion gates remain closed;
- OPEC CE quarantine remained untouched.

Stage 9 is therefore complete. NHC activation is no longer an unfinished roadmap candidate.

## Stage 10 — cross-layer coverage audit before broader population — ACTIVE / AUDIT-GUIDED

The architecture is mature enough that the principal expansion risk is **population bias**: adding whatever is easy to monitor, easy to source or already familiar. Broader Live, Monitor or Analysis growth therefore follows current cross-layer evidence rather than raw counts or convenience.

### Stage 10A — CJ cross-layer coverage / pressure diagnostic — DONE / CI-GENERATED

CJ adds a reusable read-only audit comparing:

- Canonical occurrence and series breadth by region and Canonical category;
- explicit configured Monitor occurrence/series scope;
- Live observation presence by declared region and Live domain tag;
- Analysis review coverage by the Canonical region/category of its anchor;
- production Live-input use;
- the Live→Analysis frontier, distinguishing used Live observations, completed same-anchor linked observations, linked observations whose Canonical target is not completed, and unlinked Live observations.

The diagnostic must not:

- produce a blended coverage score;
- equalise counts between regions or categories;
- force Canonical categories and Live domain tags into one taxonomy;
- create Monitor routes;
- populate Live or Analysis;
- open Canonical/Calendar/public-projection gates;
- convert a review prompt into an automatic finding of undercoverage.

Its artifacts are disposable read-only evidence under `artifacts/coverage/`; governed registries remain authoritative.

The first artifact exposed a cross-layer region-granularity issue rather than two true gaps. CJ v0.2 therefore uses only two explicit audit-only comparison mappings — `Central Africa -> Africa` and `Global -> Cross-regional / Global` — while preserving all governed raw labels. No other geographic parent is inferred.

Corrected CJ run `34412482858` reported the post-#117 boundary: 689 Canonical occurrences / 203 series, 26 Monitor adapters / 217 explicitly scoped occurrences / 48 series, 7 Live observations / 2 Canonical-linked, 22 Analysis reviews / 1 production Live input / 1 production revision, and zero unused completed same-anchor Live→Analysis candidates.

The permanent CJ audit and evidence trail are in `data/coverage/POST_CI_CROSS_LAYER_PRESSURE_CJ_v0.1.md`.

### Stage 10B — CK Pacific Islands Forum lifecycle/provenance repair — DONE / GUARDED

CJ's Pacific prompt initially appeared to reveal a missing Pacific Islands Forum Leaders Meeting family. CK's first guarded transaction disproved that specific conclusion before any write: the stable Canonical occurrence `WSO-INT-A-0001` and series `WSER-INT-PIF-LEADERS` already existed, sourced by `WSSRC-INT-012` and host-bound by `WSHB-PIF-2026-PW`.

The actual defect was narrower and operationally important: the 55th Pacific Islands Forum Leaders Meeting retained `ACTIVE` lifecycle state after its authoritative 30 August–4 September 2026 Palau meeting window had concluded.

CK therefore:

1. preserves the existing PIF occurrence, series, source and host-binding identities;
2. preserves the exact `MULTI_DAY_LOCAL`, DAY-precision, `Pacific/Palau` civil range without synthetic UTC endpoints;
3. changes lifecycle only from `ACTIVE` to `COMPLETED` using first-party post-event evidence rather than elapsed-time inference;
4. adds supporting-only Cook Islands PMO source `WSSRC-INT-036` with zero primary Canonical dependencies and no unattended-monitoring permission;
5. appends one reviewed lifecycle change to the Change Ledger;
6. preserves New Zealand/Auckland as 2027 host context only and creates no dated 2027 occurrence;
7. creates no PIF Monitor, Live or Analysis row and opens no automatic write/promotion gate;
8. leaves OPEC CE quarantine untouched.

CK also adds a material identity-discovery control: a claim that an important family is absent must interrogate stable IDs, source dependencies, institution keys and host bindings where available, not only literal human-readable names.

The guarded transaction exposed and repaired historical descendant assertions that had accidentally turned old Canonical/Source/Ledger checkpoints into permanent ceilings. Exact historical prestate tests remain exact; descendant/coherence tests now validate lineage floors and tranche-owned invariants. The successful transaction passed all 1,256 historical tests plus validators, compilation, seven JavaScript checks, static build and bounded-diff/protected-layer gates.

Permanent transaction evidence is in `data/coverage/PIF_LEADERS_MEETING_CK_TRANSACTION_AUDIT_v0.1.md`.

### Stage 10C — post-CK re-audit and bounded broadening/deepening — NEXT

Do **not** carry forward CJ's old candidate ranking mechanically. Rerun the read-only cross-layer diagnostic against the post-CK governed state, then select the next bounded tranche from current evidence.

Candidate classes are deliberately unordered:

1. **Live expansion** where a new observation exercises a missing or materially useful factual contract and has adequate first-party provenance;
2. **Monitor expansion** where important existing Canonical scope has a competent, rights-cleared, bounded machine route;
3. **Canonical/source repair** where identity-aware discovery establishes a real upstream omission, stale lifecycle or provenance defect;
4. **Live→Analysis** only where an immutable Live observation is already linked to a completed same-anchor Canonical occurrence and fresh pressure justifies another production input;
5. **Analysis revision** only where later evidence changes an existing analytical judgement rather than merely adding chronology.

The 2026 PIF Forum Communiqué may be considered as one possible Oceania / Pacific Live outcome candidate because the underlying Canonical occurrence is now evidence-backed `COMPLETED`, but neither the regional zero count nor CK itself authorises that row. The audit must compare it against other current pressures.

BARMM remains pre-event until the 14 September 2026 election occurs and is authoritatively established as completed. Do not pre-write its post-event Analysis or infer an outcome from pre-election context.

Broader population must continue to establish correction/retraction handling, geographic/domain balance, noise controls, retention and provenance before any high-volume Live ingest is considered. Platform independence remains mandatory.

## Stage 11 — Calendar export / external write interfaces — LATER / WRITE GATE CLOSED

ICS or other calendar outputs must be generated from Canonical. External calendar state remains disposable and rebuildable. User travel changes display-local rendering, not canonical event time.

Google Calendar writes remain off until explicitly authorised by a later reviewed architecture.

## Stage 12 — evaluate narrow auto-commit classes — GATE CLOSED

Only reconsider after prospective evidence demonstrates narrow, reliable classes such as a same-identity reschedule against prior Canonical state and an explicit authoritative cancellation. Even then, any first auto-commit class requires separate authorisation and must not generalise across heterogeneous source contracts.

## Permanent quarantine

PR #113 / CE OPEC is not a roadmap stage or backlog item. It is quarantined historical evidence. Future OPEC work must start from then-current `main`, inspect `OPEC_QUARANTINE.md`, PR #113 and the preserved CE branch, and use a fresh bounded design.
