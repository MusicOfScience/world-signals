# WORLD SIGNALS — capability roadmap

This roadmap is subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Stages describe architectural capability, not permission for bulk population. Current numeric state is mechanically derived and CI-checked rather than manually repeated across historical stage prose.

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

The diagnostic must not produce a blended coverage score, equalise regional/category counts, force Canonical categories and Live tags into one taxonomy, create Monitor routes, populate Live/Analysis, or open write/public-projection gates.

Its artifacts are disposable read-only evidence under `artifacts/coverage/`; governed registries remain authoritative.

The first artifact exposed a cross-layer region-granularity issue rather than two true gaps. CJ v0.2 therefore uses only two explicit audit-only comparison mappings — `Central Africa -> Africa` and `Global -> Cross-regional / Global` — while preserving all governed raw labels. No other geographic parent is inferred.

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

### Stage 10C — post-CK pressure re-audit — DONE / CL SELECTED FOR FRESH DESIGN

Post-CK read-only coverage run `34422209848` confirms:

- Canonical remains 689 occurrences / 203 series;
- Monitor remains 26 adapters / 217 explicitly scoped occurrences / 48 series;
- Live remains 7 observations / 2 Canonical-linked;
- Analysis remains 22 reviews / 1 production Live input / 1 production revision;
- the Live→Analysis frontier still has **zero** unused completed same-anchor candidates;
- Europe, Latin America, North America and Oceania / Pacific remain zero-Live prompts, not queues;
- `CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` Monitor zeroes remain non-authorising under current source/rights posture;
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE` remains an Analysis prompt, not an automatic target.

Fresh first-party PIF outcome research identifies a more specific pressure than any of those zero counts: the completed PIF anchor now has sufficiently specific official evidence that Leaders' Retreat agreed a Pacific-led framework for engagement with partners, with other regional outcomes separately evidenced.

Permanent selection evidence is `data/coverage/POST_CK_PRESSURE_AUDIT_CL_v0.1.md`.

### Stage 10D — CL bounded PIF scheduled institutional-outcome Live specimen — DONE / GUARDED

CL starts from exact post-#119 main `aef4642863438e2170ae9a49160b7368c850b819` and materialises one bounded `PRIMARY_CONFIRMED` `INSTITUTIONAL_DEVELOPMENT`:

- `WSLI-INST-PIF-PARTNER-FRAMEWORK-20260904-001`;
- region `Oceania / Pacific`;
- domain tags `INSTITUTIONS` + `GEOPOLITICS`;
- `OUTCOME_OF` → completed `WSO-INT-A-0001`;
- one primary-official Cook Islands PMO evidence row;
- no manufactured `event_time`;
- no market, surprise, causal or second-order claim.

Live advances from v0.7 / 7 observations / 10 evidence / 2 Canonical-linked to **v0.8 / 8 / 11 / 3**. Canonical, Sources, Change Ledger, Monitor and Analysis remain unchanged.

Fresh preflight narrowed the proposed payload. The Australian Prime Minister's Waqa Moana release used `unanimously endorsed`, while indexed final-communiqué text used `agreed in principle` and noted further national consultations. Because the authoritative Forum Secretariat PDF was not directly retrievable through the controlled automated path, CL excludes Waqa rather than silently choosing the stronger wording. The discrepancy is preserved as evidence pressure, not resolved by assertion.

The guarded transaction also repaired descendant-unsafe CG/CJ/BF/BD tests that had frozen historical Live v0.7 current-state values or population labels as permanent ceilings. Their historical specimen semantics and safety gates remain tested. Successful run `34436154025` passed the complete **1,262-test** suite plus validators, compilation, seven JavaScript checks, static build and bounded/protected-layer gates. Permanent transaction evidence is `data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_TRANSACTION_AUDIT_v0.1.md`.

Automatic ingestion, Canonical commit, Calendar write, PIF Monitor creation, Live→Analysis promotion and public Live projection remain closed.

### Stage 10E — post-CL pressure re-audit — DONE / CM SELECTED

Read-only coverage run `34436436416` reports:

- Canonical 689 occurrences / 203 series;
- Monitor 26 adapters / 217 scoped occurrences / 48 series;
- Live 8 observations / 3 Canonical-linked;
- Analysis 22 reviews / 1 production Live input / 1 production revision;
- completed linked Live observations with an existing unused Analysis target: **0**;
- completed linked Live observations without an Analysis review: **1** — the new PIF outcome;
- linked non-completed observations: **1** — BARMM pre-election context;
- Europe, Latin America and North America remain zero-Live prompts;
- Monitor category zeroes and the corporate/market Analysis zero remain non-authorising prompts.

PIF is not bridge-ready. No same-anchor Analysis review exists, and the current bridge policy remains `CONTROLLED_SINGLE_PRODUCTION_LINK` with its one production slot already occupied by Japan FIES. Creating an Analysis review merely to manufacture a bridge target is prohibited by the evidence-first architecture.

The stronger pressure is correction/conflict handling. CL's Waqa source disagreement demonstrates why named verification states are insufficient without executable semantics. The permanent pressure decision is `data/coverage/POST_CL_PRESSURE_AUDIT_CM_v0.1.md`.

### Stage 10F — CM Live correction / retraction / conflicting-report contract hardening — DONE / GUARDED

CM starts from exact merged #120 main `1e4a6bbc8670fc36a452740401461f28e313c031` and hardens the executable Live correction/retraction/conflict grammar **without production population**.

Result:

- Live contract metadata advances from v0.8 to **v0.9** while remaining exactly **8 observations / 11 evidence rows / 3 Canonical-linked observations**;
- every production observation and evidence object is preserved exactly from the merged CL base;
- `CORRECTED` / `RETRACTED` now require an explicit prior Live target, `CORRECTION_OR_REVISION` evidence and strictly later `observed_at_utc`;
- `CONFLICTING_REPORTS` now requires at least two unique evidence records from at least two distinct normalised providers plus a factual `conflict_description`;
- Live does not choose a winning source or manufacture consensus from disagreement;
- `DATA_REVISION` remains the separate external-data revision concept and does not require synthetic prior Live history;
- no production conflict/correction/retraction row is added and Waqa Moana remains un-reinterpreted historical pressure evidence;
- automatic ingestion, public Live projection, Canonical/Calendar write and automatic downstream promotion remain closed.

Guarded run `34441432538` / job `102757107224` passed on its first attempt, including **1,276 tests / 68 historical-prestate skips**, all governed validators, derived-state consistency, compilation, seven JavaScript checks, static build, exact production-row invariance, protected-layer nonmutation and bounded final diff. Temporary transaction machinery removed itself before commit. Permanent evidence is `data/live_intelligence/LIVE_CORRECTION_CONFLICT_CM_TRANSACTION_AUDIT_v0.1.md`.

### Stage 10G — post-CM pressure re-audit — DONE / CN SELECTED

Read-only coverage run `34441643238` confirms CM changed capability rather than population:

- Canonical remains 689 occurrences / 203 series;
- Monitor remains 26 adapters / 217 scoped occurrences / 48 series;
- Live remains 8 observations / 3 Canonical-linked;
- Analysis remains 22 reviews / 1 production Live input / 1 production revision;
- PIF remains one completed linked observation without an Analysis review;
- no unused completed same-anchor Analysis target exists;
- BARMM remains linked to a non-completed 14 September occurrence;
- Europe, Latin America and North America remain zero-Live prompts, not queues;
- Monitor and market-structure Analysis zeroes remain non-authorising prompts.

The qualitative pressure review compared current North American trade escalation and European oil-security context with a 9 September Brazilian fuel-policy intervention. It selects **CN — Brazil fuel-policy Live broadening** because the Brazilian development is independently important and exercises a novel unscheduled cross-domain combination: fiscal/tax policy + fuel/commodity shock + government-stated geopolitical context in Latin America. Regional diversification is a benefit, not a quota rule.

The selection remains conditional on a fresh post-CM-merge legal-status check. At review time, the Brazilian Finance Ministry announcement clearly supports an announced/adopted policy-development claim, but the complete final legal-instrument trail was not yet cleanly retrievable. CN must not silently upgrade announcement language to `in force`, invent legal numbering, manufacture exact source/event UTC timing or claim observed consumer-price/inflation effects.

Permanent selection evidence is `data/coverage/POST_CM_PRESSURE_AUDIT_CN_v0.1.md`.

### Stage 10H — CN Brazil fuel-policy Live broadening — NEXT AFTER CM MERGE

CN is selected for **fresh post-merge design**, not pre-written population.

Minimum CN pressure:

1. start from exact then-current post-CM `main`;
2. freshly recheck Ministério da Fazenda, Presidency/Planalto and Diário Oficial sources for the 9 September fuel package, including corrections, legal numbers and effective status;
3. revise or abandon the candidate if the post-merge evidence materially changes the package;
4. if retained, keep the Live claim bounded to what competent first-party evidence supports — likely an unscheduled `POLICY_DEVELOPMENT` for Brazil rather than an invented Canonical occurrence;
5. preserve event time no finer than the supported civil date unless a competent source establishes a source-native clock;
6. do not promote the source page's displayed `18h47` to exact UTC without a competently established timezone;
7. distinguish the government's stated geopolitical/oil-shock rationale from WORLD SIGNALS causal attribution;
8. do not claim consumer prices fell, inflation changed, fuel supply improved or markets moved without separate evidence;
9. create no Monitor route or automation permission from public accessibility;
10. keep Analysis population and public projection closed;
11. preserve the CM correction/conflict contract and OPEC CE quarantine.

Canada–U.S. tariff escalation and EU oil-security context remain valid future Live candidates. They are deferred, not discarded, and should be reconsidered by later pressure rather than appended automatically.

## Stage 11 — Calendar export / external write interfaces — ICS IMPLEMENTED / WRITES CLOSED

The first subscription-capable external projection is now implemented. The
existing static build generates `docs/world-signals.ics` from governed
Canonical records and the governed Source Registry. Stable occurrence-based
UIDs survive date changes; timed events retain source-local IANA timezone
semantics; civil dates and explicit expected windows remain date-only; unresolved
TBC, source-native-calendar and monitor-only objects are omitted with an
auditable build count rather than given synthetic appointments.

The feed also emits deterministic RFC 5545 `VTIMEZONE` components for each
referenced source-local TZID, derived from Python's IANA `zoneinfo` data over
the included event horizon. Governed timing or lifecycle revisions advance
`SEQUENCE` and update `LAST-MODIFIED` while preserving UID; `DTSTAMP` remains
the earliest known governed event timestamp. Expected windows are retained and
marked transparent for subscriber free/busy semantics.

GitHub Pages can publish the feed at the intended path:
`https://musicofscience.github.io/world-signals/world-signals.ics`.
Monitoring remains local through the guarded daily runner. The former scheduled
GitHub monitor is manual-dispatch only; CI, static Pages deployment and manual
smoke/audit workflows remain available. Google Calendar writes remain off until
explicitly authorised by a later reviewed architecture.

The next milestone is not a larger calendar. The reviewed Signal contract is
now defined and pressure-tested over immutable Live observations, while its
production population remains closed. It makes novelty, persistence,
corroboration, confidence, contradiction and transmission relevance explicit
without leaking forecasts or causal claims downstream.

## Stage 12 — reviewed Signal contract — IMPLEMENTED / POPULATION CLOSED

The executable contract lives in `data/signals/` and
`src/world_signals/signals.py`. It validates immutable observation/evidence
lineage, review-governed lifecycle and revision history, contradiction and
anti-noise safeguards, explicit transmission hypotheses and forecast-field
exclusion. No candidate or production Signal has been populated, no synthetic
fixture is stored in production data, and public Signal projection remains
closed.

The generic reviewed Relationship contract is implemented in Stage 13 below.

## Stage 13 — reviewed Relationship contract — IMPLEMENTED / POPULATION CLOSED

The executable contract lives in `data/relationships/`,
`src/world_signals/relationships.py` and `scripts/validate_relationships.py`.
It consumes reviewed Signal revisions as analytical nodes and keeps
co-occurrence, association, dependency, common-driver context, hypothesised
transmission, mechanistic support, causal evidence and feedback loops distinct.
It requires explicit directionality, alternatives, contradictory evidence,
review provenance and causal basis for stronger claims; revisions preserve
prior assessments and as-of history; graph traversal cannot create transitive
Relationships. No production Relationship is populated and public projection
remains closed.

## Stage 14 — reviewed Risk / Regime-State history contract — IMPLEMENTED / POPULATION CLOSED

The executable contract lives in `data/risks/`, `src/world_signals/risks.py` and
`scripts/validate_risks.py`. It distinguishes qualitative Risk and Regime state,
records immutable reviewed transitions and as-of history, derives convergence
from distinct upstream lineage without treating shared providers or duplicate
evidence as independent, and requires threshold provenance. The existing
Canonical-derived `risk_projection` remains a separate non-authoritative lens;
no production Risk/Regime state is populated and public projection remains
closed.

## Stage 15 — competing Scenarios contract — IMPLEMENTED / POPULATION CLOSED

The executable contract lives in `data/scenarios/`,
`src/world_signals/scenarios.py` and `scripts/validate_scenarios.py`. Explicit
Scenario Sets preserve common starting conditions, shared assumptions and
divergence points, while member Scenarios preserve conditional assumptions,
transmission epistemics, signposts, disconfirming indicators, competing
members and falsification/retirement history. Probability, ranking, target and
forecast fields are prohibited. Scenario history is append-only and supports
explicit as-of queries without later evidence rewriting earlier pathways. No
production Scenario is populated and public projection remains closed.

## Stage 16 — governed Forecast contract — IMPLEMENTED / POPULATION CLOSED

The executable contract lives in `data/forecasts/`,
`src/world_signals/forecasts.py` and `scripts/validate_forecasts.py`. It
supports binary, categorical and numeric point Forecast issuances with stable
question-series identity, independently scoreable analytical updates,
administrative correction revisions, explicit information cutoffs, resolution
sources, fallback and vintage policies, and governed void semantics. Outcome
resolution, scoring, calibration, automatic generation, model learning and
public projection remain outside this layer. No production Forecast is
populated.

## Stage 17 — Outcomes / Resolution — IMPLEMENTED / POPULATION CLOSED

The executable contract lives in `data/outcomes/`,
`src/world_signals/outcomes.py` and `scripts/validate_outcomes.py`. One stable
Outcome resolves a Forecast question series and can map to many eligible,
independently scoreable issuances. Resolution follows the Forecast's pinned
rule, source/fallback policy and numeric vintage semantics. Pending, resolved,
void, unresolvable and disputed states are explicit; Outcome revisions are
append-only and do not mutate Forecasts. No production Outcome is populated
and public projection remains closed.

## Stage 18 — Forecast Evaluation — IMPLEMENTED / NO SAMPLE

The executable contract lives in `data/evaluation/`,
`src/world_signals/evaluation.py`, `scripts/validate_evaluation.py` and the
versioned evaluation configuration. It scores synthetic Forecast issuances
against governed synthetic Outcomes using compatible binary, categorical and
numeric metrics, preserves infinite log loss for wrong certain forecasts,
reports issuance/series/resolution denominators, derives lead time
deterministically and keeps calibration in explicit no-sample or insufficient-
sample states. Evaluation is derived rather than editable score truth and does
not mutate Forecasts or Outcomes. Production Forecasts, Outcomes and
Evaluation remain empty; no performance, baseline, ranking or Model Learning
claim is made.

The next population milestone is a separately authorised narrow prospective
Forecast pilot. Model Learning must wait until that pilot produces a
defensible resolved sample.

## Stage 19 — evaluate narrow auto-commit classes — GATE CLOSED

Only reconsider after prospective evidence demonstrates narrow, reliable classes such as a same-identity reschedule against prior Canonical state and an explicit authoritative cancellation. Even then, any first auto-commit class requires separate authorisation and must not generalise across heterogeneous source contracts.

## Permanent quarantine

PR #113 / CE OPEC is not a roadmap stage or backlog item. It is quarantined historical evidence. Future OPEC work must start from then-current `main`, inspect `OPEC_QUARANTINE.md`, PR #113 and the preserved CE branch, and use a fresh bounded design.
