# Executable architecture

## Governing rule

`WORLD_SIGNALS_PROJECT_CHARTER.md` is authoritative. The executable repository implements its layers as separate governed contracts rather than one blended event/news database.

Current reconciled `main` state (27 September 2026):

- Canonical `v0.43 / 689 occurrences`, schema `v0.52`;
- Source Registry `v2.04 / 258 sources`;
- Source/Change Monitor `v0.28 / 26 configured adapters / 25 unique monitor sources`;
- Live Intelligence `v0.13 / 12 observations / 16 evidence`, with automatic ingestion and public observation projection closed;
- Analysis `v0.18 / 22 reviews / 97 evidence` on schema `v0.8`;
- Signals schema `v0.1`, one admitted reviewed revision, population and public projection closed by default;
- automatic Canonical commit OFF; Google Calendar writes OFF.

## Runtime layers

1. **Canonical Registry** — versioned authoritative event identities, lifecycle and timing.
2. **Calendar / Web projection** — derived read-only rendering; never the database.
3. **Source / Change Monitor** — read-only adapters inspect authoritative sources, source health and candidate changes.
4. **Live Intelligence** — factual current-development observations that may be scheduled or unscheduled and may optionally reference Canonical occurrences.
5. **Analysis** — reviewed interpretation of expectations, surprises, market observations, connections, noise, alternatives, second-order effects and falsifiers.
6. **World State Synthesis** — future derived, continuously updated, as-of synthesis over governed evidence, actor state, world-state dimensions and transmission; not implemented by this tranche. It is a synthesis hub for scenarios and forecasts, not a terminal stage after model learning.
7. **Briefing projections** — the public reader sequence is `OUTLOOK →
   RESOLUTION CLOCK → REVIEWED ANALYSIS → CALENDAR → RESEARCH`.
   `WORLD STATE | MAP` remain internal/future public surfaces. These views are
   projections, not additional governed stores.

Supporting operational contracts include source governance, review-candidate state, reviewed Change Ledger, runtime evidence and noncanonical analytical/coverage overlays.

## Source / Change Monitor contract

```text
official endpoint
   |
   v
FETCH -> SNAPSHOT -> PARSE
   |          |
   |          +--> payload hash / source health
   v
normalized positive evidence
   |
   v
MATCH -> DIFF
   |
   +--> NO_CHANGE
   |
   +--> REVIEW CANDIDATE

Never:
source failure -> event cancellation
source absence -> event completion
parser success -> canonical write
```

The scheduled GitHub monitor runs with `contents: read` permission. It protects canonical bytes and cannot make direct canonical changes.

### Current configured adapter cohort

`data/monitor/expectations.json` v0.10 configures eight heterogeneous adapters:

1. **RBA Financial Stability Review RSS/RDF** — publication-completion sentinel.
2. **Colombia SUIN / Socrata Decree 111/1996** — typed legal-instrument sentinel with manual clause verification.
3. **EU Cyber Resilience Act Article 71 / Cellar** — legal-rule baseline and topology sentinel.
4. **EU CBAM verifier-report milestone** — legal milestone / Cellar topology sentinel.
5. **EU CBAM certificate-sale milestone** — amending-rule / parent-act topology sentinel.
6. **EU CBAM annual declaration / surrender deadline** — recurring legal-rule / topology sentinel.
7. **ONS release-calendar RSS** — publication schedule/date-change sentinel with official HTML verification requirement.
8. **EIA Weekly Petroleum Status Report schedule** — energy/publication-schedule sentinel.

Configuration does not mean every governed source is automation-cleared. Source rights, endpoint health, parser validation and route authority remain distinct gates.

## OSINT Observation & Signal Engine v1 — candidate-only

The first OSINT engine is a local operational layer above selected Source
Registry routes and beside, rather than inside, the governed Monitor:

```text
selected first-party route
  -> raw retrieval metadata / payload hash
  -> normalised Observation Candidate
  -> lineage-aware deduplication
  -> operational story cluster
  -> Signal Candidate / review queue
  -> [human reviewed transaction required]
  -> governed Live Intelligence / Signal
```

The v1 cohort is explicit in `data/osint/source_cohort.json` and contains eight
first-party RSS/JSON routes. A route is eligible only when its registry record
has explicit cleared automated monitoring use and non-held retrieval and
ingestion permissions. Registry `ACTIVE`, institutional authority or machine
readability alone never grants OSINT retrieval permission. Calendar-only routes,
held/uncleared routes, paid/licensed market and newswire feeds, and the
quarantined OPEC material remain outside the cohort.

Raw retrievals retain route identity, retrieval time, HTTP state, content type,
payload hash, source publication time, native identifiers and parser versions.
Normalisation preserves publication/effective/retrieval time distinctions.
Immediate provider and ultimate origin are separate lineage fields; syndicated,
translated or mirrored copies do not count as independent corroboration.
Clustering is an operational aid, not factual identity, and conservative
candidate heuristics nominate review work rather than establish materiality,
confidence, causation or a governed Signal.

Runtime output is local and ignored under `.world-signals-runtime/osint/`.
OSINT v0.13 has now exercised one genuine reviewed promotion from an authorised
retrieval into the governed Live store. The promotion is append-only and
audited in `data/live_intelligence/osint_promotion_transaction_v1.json` with
candidate/source lineage and pre/post fingerprints. There is no public
candidate projection, no automatic promotion and no write
authority over Canonical, Live Intelligence, Signals, Relationships, Risks,
Scenarios or Forecasts. The four prospective Forecasts remain outside the OSINT
engine and their information cutoffs cannot be revised by retrieval.

The v0.2 runtime contract makes `BOOTSTRAP` versus `INCREMENTAL` explicit.
Bootstrap inventory is labelled historical runtime material and cannot create
current persistence or Signal Candidates. Incremental checkpoints retain route
retrieval state, source-native identities and per-record hashes, so feed replay
and parser-version changes do not replay an entire history as current novelty.
Same-identity content changes become revision/correction candidates with their
own first-seen time and prior-candidate link. A 27 September 2026 check of the
retained post-bootstrap checkpoint returned seven unchanged routes and one
source-specific BSP 403, with zero new candidates and zero promotions.

## Live Intelligence controlled population

AV introduced the executable Live Intelligence contract at `data/live_intelligence/`; AW v0.2 admitted the first reviewed internal specimen, and AX v0.3 adds a bounded evolving-state story test without opening broad ingestion.

```text
current development / observation
        |
        v
FACTUAL OBSERVATION
  - identity
  - verification state
  - domains / geography
  - evidence
  - optional canonical links
  - separate observation/event/publication time
  - explicit revision history
        |
        v
ANALYSIS may later interpret it
```

The frozen AV v0.1 and AW v0.2 checkpoints remain recorded inside the v0.3 schema. AX uses `CONTROLLED_MULTI_SNAPSHOT_SPECIMEN`: maximum three observations and four evidence rows, automatic ingestion disabled, automatic story clustering disabled and public observation projection closed. The DRC observations demonstrate that a later state snapshot is not automatically a correction of the earlier snapshot, and that a manual story key is only a grouping identity.

Live Intelligence is not a synonym for the Source/Change Monitor. The monitor asks whether governed authoritative inputs changed; Live Intelligence records consequential factual developments in the world. A monitor parser failure is not a Live Intelligence fact.

Live Intelligence is also not Analysis. It may record a factual market observation, shock, announcement or revision, but it may not claim what was expected, what surprised, what caused a move or which interpretation is preferred. The first OSINT-originated production row is a Federal Reserve policy-decision fact; its promotion retains the originating candidate and successful RSS retrieval metadata. A separate reviewed Signal specimen exists only through its explicit admission transaction and does not cause downstream analytical promotion.

Unscheduled physical shocks, health emergencies and geopolitical developments can therefore exist without inventing scheduled Canonical occurrences. If a Live observation references Canonical, the occurrence ID must resolve.

## Reviewed Signal contract — one controlled specimen / population closed by default

The first Signal milestone is now an executable contract at
`data/signals/schema.json`, `data/signals/signals.json` and
`src/world_signals/signals.py`. It reuses immutable Live Intelligence
`observation_id` and evidence lineage rather than creating a second observation
store. A Signal is a reviewed analytical inference: it records direction,
materiality, novelty, persistence, trend state, corroboration, confidence,
transmission relevance, falsification conditions and explicit lifecycle/review
state without asserting a causal relationship or encoding a forecast.

Production admission remains closed by default. A populated dataset is valid
only when it uses the controlled specimen state and is accompanied by
`data/signals/signal_admission_transaction_v1.json`, which records the reviewed
decision, exact empty pre-state, admitted post-state, validator result and a
hard maximum of one production Signal. No test flag or population label opens
general admission. `validate_signal_history` remains a separate read-only
proposal validator. The public projection stays closed and no dashboard or
risk-overlay consumer was added.

Each full revision snapshot contains an explicit evidence-backed baseline and
qualitative justifications for materiality, novelty, persistence, trend,
confidence, source quality, coverage bias and alternatives. Supporting and
contradictory evidence must be classified explicitly. Lineage names ultimate
collection/reporting origins with a review basis; same-provider, same-document
or shared-origin evidence collapses into a connected component. Independent
corroboration is bounded by a matching between supporting observations and
those components. Contradictions never add support. Counts do not set confidence
or materiality, and a single observation cannot establish persistence.

The Live evidence model has provider labels but no generic syndicated-source
lineage; the Signal's reviewed lineage assessment supplies that missing
information without changing upstream facts. This validator checks consistency,
not the factual truth of analyst-supplied origins, prose, review identities or
claims of independence. A reviewer must check syndication, common institutional
origins, media density, language/geographic bias, alternative explanations and
whether repeated observations represent a persistent change. Model-generated
text and context-only evidence cannot provide independent supporting evidence.
Uncertainty is not converted into a numerical score. The existing post-event
Analysis bridge remains separate and does not depend on Signals.

The first controlled specimen is
`WSSIG-HEALTH-COD-BVD-BURDEN-202609-001`: a low-confidence persistent-change
assessment over two time-separated WHO snapshots of the DRC Bundibugyo
outbreak. Shared WHO origin is explicitly treated as partial rather than
independent corroboration. The Signal describes an observed increase in
reported burden, not cause, risk state, scenario or forecast.

Revision numbers are contiguous, predecessor links resolve, creation time
advances past the prior decision, and decision timestamps/reasons are required
for acceptance and rejection. Terminal states require reopening review before
reactivation. SHA256 pins check complete immutable observation snapshots.
`validate_signal_history(..., previous_revisions=retained_prestate)` rejects
removed or rewritten prior revisions. An isolated snapshot cannot prove its own
history: supplying a trusted retained prestate is mandatory for any future
admission transaction. No production transaction is authorized here.

Assessments cannot use observations or known source publications from after
their creation time. `signal_state_as_of` takes an explicit UTC timestamp and
selects the revision effective at that time (decision time for reviewed rows,
creation time for unresolved rows). It reports stale/review-required states
without rewriting a stored assessment or automatically accepting a new one.
`STALE_AFTER` expires from the latest supporting observation; `EXPLICIT_DATE`
and `REVIEW_REQUIRED` use explicit UTC deadlines. Revision activity or contrary
evidence cannot refresh the supporting-evidence clock. Conditional withdrawal
triggers remain for human review rather than arbitrary executable expressions.

CM corrections/retractions are new observations pointing to the unchanged
ancestor via `revision_of_observation_id`. Reverse dependency lookup preserves
historical references. A later correction makes an active dependent Signal
require review while the earlier as-of assessment remains intact; an active
replacement must acknowledge the correction and drop invalid ancestor support.
Transmission entries may describe hypotheses or observed association only;
reviewed causal mechanisms belong to the later Relationship contract. Structured
forecast/scenario fields and unknown fields are rejected, while disguised
forecasts in free prose still require human review. The production Signal count
remains zero; synthetic fixtures are confined to tests.

## Reviewed Relationship contract — controlled historical specimen

The generic Relationship layer is now defined as a separate, executable,
zero-population contract in `data/relationships/` and
`src/world_signals/relationships.py`. The Step 12A candidate contract is
versioned as `data/relationships/schema_v0.2.json`; the existing empty
`schema.json`/dataset remain the hash-pinned v0.1 read contract so prior
consistency evidence is not rewritten. v0.2 supports reviewed Signal
revisions and exact immutable admitted World State component revisions as
endpoint nodes. Live observations, Analysis, evidence and Canonical
occurrences remain supporting/contextual lineage only; Analysis and
`WORLD_STATE_COMPOSITION_VIEW` are never endpoint nodes. Raw monitor
candidates, unreviewed Signals and private runtime records are not eligible
nodes. Step 12B admits exactly one historical RBNZ specimen in the separate
v0.2 controlled store; the v0.1 checkpoint remains empty and public
Relationship projection remains closed.

Relationship classes distinguish co-occurrence, association, dependency,
common-driver context, hypothesised transmission, mechanistic support, causal
evidence and reviewed feedback loops. Directionality is explicit. Stronger
classes require an explicit reviewed evidentiary basis; plausible transmission
does not silently become mechanism or causation. Alternatives, confounders,
common drivers and contradictory evidence remain first-class fields rather than
being overwritten by a selected pathway.

Relationship revisions retain predecessor snapshots, review decisions,
timestamps, reasons and as-of state. Later observations or evidence cannot be
used to inflate an earlier assessment. Direction changes require a reviewed
revision, terminal states cannot silently reactivate, and graph helpers emit
only exact reviewed edges: visual proximity and transitive traversal never
author a new Relationship. A separate explicit temporal-lineage DAG rejects
`C1 → R1 → C1` and multi-hop revision cycles; it does not infer edges from
snapshot co-occurrence. Forecast and scenario fields are outside this
contract, and public Relationship projection remains closed.

## Reviewed Risk / Regime-State contract — population closed

The Risk/Regime layer is now defined as a separate executable history contract
in `data/risks/`, `src/world_signals/risks.py` and
`scripts/validate_risks.py`. It uses reviewed Signal and Relationship revisions
as primary analytical inputs, with immutable observations and evidence as
supporting lineage. It does not promote the existing Canonical-derived risk
overlay, mutate upstream records or populate a public risk feed.

One versioned state object distinguishes `RISK_STATE` from `REGIME_STATE` and
records its current state, prior state, transition type/direction, persistence,
trend, materiality, confidence, contradiction, alternative interpretation,
expiry and review provenance. Risk states use qualitative states such as
`EMERGING`, `ELEVATED`, `INTENSIFYING`, `PERSISTENT`, `EASING` and `BASELINE`;
regime states use `BASELINE`, `TRANSITIONING`, `ESTABLISHED` and `EXITING`.
Transitions are reviewed and append-only, so return to baseline, weakening,
expiry and uncertainty remain historical assessments rather than deletion or
in-place status changes.

Convergence is qualitative and lineage-derived, not a universal score. Duplicate
upstream revisions are rejected; distinct observations, providers, domains and
relationship mechanisms are counted from traceable support; shared providers do
not become independent corroboration; contradictory inputs remain outside the
support counts. Thresholds are qualitative unless they carry explicit type,
description and provenance, and numeric risk scores are prohibited. As-of
queries use explicit UTC assessment times and cannot use later evidence to
rewrite earlier states. Forecast, scenario and probability fields are outside
the contract, and public Risk/Regime projection remains closed.

## Reviewed Scenario contract — population closed

The Scenario layer is now defined as a separate executable contract in
`data/scenarios/`, `src/world_signals/scenarios.py` and
`scripts/validate_scenarios.py`. It introduces explicit Scenario Sets rather
than a single favoured pathway. A Set retains shared starting conditions,
assumptions and divergence points; member Scenarios retain their own
conditional assumptions, enabling/inhibiting conditions, transmission
pathways, signposts, disconfirming signposts and retirement/falsification
criteria.

Scenario assumptions are structured objects and remain distinct from observed
facts. Signposts describe future observable evidence classes but are not scored
automatically. Transmission pathways preserve contextual, hypothesised and
reviewed-mechanism status without creating a forecast or silently upgrading a
Relationship. Probability, likelihood, target, expected-value, ranking and
forecast fields are prohibited. Scenario Sets and Scenarios are review-governed
and append-only; revisions, falsified pathways and retired pathways remain
recoverable through explicit as-of queries. Production population and public
projection remain closed, and no upstream layer is mutated.

## Reviewed Forecast contract — population closed

The Forecast layer is now defined as a separate executable contract in
`data/forecasts/`, `src/world_signals/forecasts.py` and
`scripts/validate_forecasts.py`. It supports binary event, mutually exclusive
categorical and numeric point forecasts. A stable Forecast ID identifies the
question series; each analytical update is a distinct issuance that remains
independently scoreable, while administrative corrections preserve the
issuance's substantive content and revision history.

Every issuance fixes its question, target, horizon, resolution rule,
authoritative resolution sources, fallback policy and information cutoff at
creation. Numeric forecasts require units and an explicit data-vintage policy.
Late-published evidence cannot be attached to an earlier issuance. Void
semantics are explicit and governed. Outcome resolution, scoring, calibration,
automatic generation and model learning remain outside this layer. The
separate Step 10A public Outlook contract exposes only the four accepted,
open monetary-policy pilot issuances; the governed Forecast dataset, broader
population, private review metadata and political/electoral Forecast
projection remain closed.

## Reviewed Outcome / Resolution contract — population closed

The Outcome layer is now defined as a separate executable contract in
`data/outcomes/`, `src/world_signals/outcomes.py` and
`scripts/validate_outcomes.py`. One stable Outcome identity belongs to one
Forecast question series, so a single governed real-world result can resolve
many independently scoreable Forecast issuances. Administrative corrections
and genuine source/result corrections append Outcome revisions; they do not
duplicate reality or mutate the original Forecast.

Resolution uses the Forecast's pinned target, timing window, source policy,
fallback policy, cancellation semantics and numeric vintage rule. Binary,
categorical and numeric results are checked against those original semantics.
Event time, evidence publication time and WORLD SIGNALS review time remain
distinct. Pending, resolved, void, unresolvable and disputed states are
explicit, and deterministic due-state helpers expose overdue resolution work
without resolving or scoring it. Evaluation metrics, public Outcome
projection, automatic resolution and model learning remain outside this
layer. Production Outcomes remain zero.

## Reviewed Forecast Evaluation contract — population closed

Forecast Evaluation is a deterministic derived layer in `data/evaluation/`,
`src/world_signals/evaluation.py` and `scripts/validate_evaluation.py`. It
scores each independently scoreable Forecast issuance against the Outcome
revision available at an explicit evaluation timestamp. It never mutates
Forecasts or Outcomes and does not replace issuance-level results with only a
final update.

The versioned configuration supports binary Brier and log loss, multiclass
Brier and log loss, and numeric signed, absolute and squared error. A wrong
certain probability retains its exact `0` or `1` input and reports infinite
log loss rather than silently clipping the Forecast. Numeric aggregates keep
target and unit boundaries explicit. Issuances from one question series are
scored separately but are never presented as independent target questions.

Evaluation records are regenerated derived artefacts rather than editable
score truth. Explicit denominator accounting retains pending, overdue, void,
unresolvable, disputed and ineligible issuances. Lead time is derived from
resolution-window end minus issue time. Calibration remains `NO_SAMPLE` or
`INSUFFICIENT_SAMPLE` until fixed, versioned thresholds are met; no baseline,
ranking or performance claim is produced. Production Forecasts, Outcomes and
Evaluation remain zero/closed, so the next population milestone is a
separately authorised prospective Forecast pilot, not Model Learning.

## Analysis contract

Analysis remains downstream interpretation. `data/analysis/schema.json` explicitly treats `LIVE_INTELLIGENCE` as upstream and preserves the Charter's separation between:

- what happened;
- what was expected;
- what surprised;
- what moved;
- what appears connected;
- what may be noise;
- alternatives;
- second-order effects;
- falsifiers.

Analysis evidence is not retrospectively migrated to Live Intelligence. Historical analytical packets remain frozen in their governed layer.

## World State Synthesis direction — design target, engine not implemented

World State is the project's next synthesis boundary. It is not a second
observation store, a replacement for Analysis, or a general-purpose narrative
field. A v1 engine must consume governed Canonical, Live Intelligence, Signal,
Relationship, Risk/Regime, Scenario, market-observation and Forecast/Outcome
inputs through explicit read contracts, then emit a review candidate or a
versioned synthesis proposal. It must not silently mutate those inputs or
publish a canonical state.

The runtime relationship is a feedback loop, not a terminal linear chain:

```text
ACTORS + EVENTS
      ↓
OBSERVATIONS
      ↓
SIGNALS + ANOMALIES
      ↓
RELATIONSHIPS + FLOWS + DEPENDENCIES
      ↓
WORLD STATE
      ↓
COMPETING HYPOTHESES / REGIMES / TRANSMISSION
      ↓
SCENARIOS + SIGNPOSTS
      ↓
FORECASTS
      ↓
OUTCOMES
      ↓
EVALUATION / CALIBRATION / MODEL LEARNING
      ↺ feeds future WORLD STATE

WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH
      ↓
BRIEFING
```

Forecasts and Outcomes may be read where analytically relevant, but they are
not prerequisites for a World State assessment. An unresolved system with
governed observations, Signals, Relationships and state dimensions remains a
valid as-of synthesis input. Later Outcomes, Evaluation and Model Learning
provide feedback for subsequent assessments without rewriting earlier state.

### Actor model

Every material proposition should identify the relevant actor or institution,
including role, jurisdiction, authority, capabilities, constraints,
commitments, incentives, internal/coalition relationships and communication or
action channel. The model must distinguish a leader, ministry, agency,
legislature, court, military command, party, market participant and state as
different actors where their authority or incentives differ.

Actor evidence is resolved through an implementation-state ladder:

```text
SAID -> DECIDED -> AUTHORISED -> IMPLEMENTED -> OBSERVED
```

The ladder is not assumed to be monotonic. A statement can be contradicted,
sidelined, narrowed or reversed; a decision can lack authorisation; an
authorised act can fail in implementation; and an observed result can diverge
from intent. Each state needs its own provenance, time, uncertainty and
contradiction record.

### World-state dimensions and sensing

The first-class dimensions are conflict/military activity,
strategic/geopolitical tension, political/institutional stability,
macroeconomic/financial conditions, trade/capital/energy/food flows,
dependencies/chokepoints, markets as sensors, climate/physical risk,
health/biosecurity, and technology/critical infrastructure. The exact v1
schema must retain extensibility without turning dimensions into an
unexplained universal score.

Markets are sensors of expectations, positioning, stress and transmission, not
automatic causal verdicts. A market observation requires instrument, venue,
timestamp, baseline or counterfactual, measurement method, relevant horizon,
liquidity/coverage caveats and alternative explanations. Conflict and military
activity are a first-class domain with actor, capability, action, geography,
intensity, constraint and escalation/de-escalation evidence rather than a
news-label overlay.

### Memory, inference and transmission

World State must be queryable as-of a time and must retain prior state,
transition, evidence and reviewer history. Anomaly detection compares current
conditions with an explicit baseline and preserves negative evidence: no
observed implementation, no expected institutional follow-through, no market
confirmation and no evidence of escalation are distinct findings, not proof of
absence.

Uncertainty is typed at minimum as provenance/source, measurement, temporal,
interpretive, model, actor-intent and institutional-authority uncertainty.
Competing hypotheses, model disagreement, contradictory observations and
unknowns remain explicit. The transmission graph distinguishes dependency,
flow, chokepoint, exposure, hypothesised transmission, mechanistic support,
causal evidence and feedback/reflexive effects. It must represent lags,
thresholds and state-dependent pathways; graph proximity never creates a
relationship.

Scenarios and signposts remain conditional pathways, separate from forecasts.
Forecasts retain prospective information cutoffs and immutable issuances;
Outcomes resolve them under their predeclared rules; Evaluation and
calibration must use resolved denominators and must never backfill hindsight
into a prior forecast. World State may reference these products but cannot
rewrite them.

### Review and projection boundary

The first implementation milestones are now the test-only consistency fixture,
the private read-only adapter, the retained non-governed consistency proposal,
the Step 5 read-boundary review and the Step 6 production-history design under
`WORLD_STATE_PRODUCTION_HISTORY_CONTRACT_DESIGN.md`, not broad population or
UI completion. The retained proposal is pinned to
`2026-09-27T04:39:04Z`; its review is accepted only for
`READ_BOUNDARY_CONSISTENCY_ONLY` and has no write targets. The adapter and
history design do not infer or admit substantive World State. Human review
remains required for state transitions, actor authority interpretation,
transmission classification, competing-hypothesis selection, scenario
signposts, production admission and any promotion into a public projection.
The final briefing is a projection assembled from reviewed state and
provenance; it is not canonical truth. The current public product leads with
the bounded Outlook pilot, its Resolution Clock, reviewed Analysis, Calendar
and Research. The
intended full product surface is:

```text
WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH
```

Migration Step 10B keeps the public Forecast allowlist deliberately narrow,
retains each Forecast's own information cutoff, and links a Forecast to a
Calendar occurrence only through an exact reviewed occurrence mapping. The
homepage no longer uses Calendar counts, concentration themes or the internal
World State boundary as intelligence headlines; those remain supporting
Calendar/Research material. A feature-branch Pages deployment may be rejected
solely by the repository's GitHub Pages environment protection even when the
static build succeeds. That known branch-policy condition is distinct from a
build, privacy or content-validation failure; post-merge Pages deployment on
`main` remains required.

## Static UX and runtime truth

GitHub Pages cannot honestly claim current monitor health merely because a build was green. The Monitor view exposes configured routes, while runtime source health and review candidates remain timestamped evidence.

Likewise, AX emits `docs/data/live_intelligence.json` only as **curated-store metadata**. It reports three internal observations and four internal evidence rows while exposing zero public observations and explicitly stating that it is not a runtime feed. A browser Live Intelligence feed is not authorised by this tranche.

## 2026-09-26 architecture baseline and migration gap assessment

This assessment is based on the governed registries, executable modules, tests,
local-operation scripts, static build and workflows in this repository. It is a
baseline for the incremental transition to:

```text
ACTORS + EVENTS -> OBSERVATIONS -> SIGNALS + ANOMALIES
        -> RELATIONSHIPS + FLOWS + DEPENDENCIES -> WORLD STATE
        -> COMPETING HYPOTHESES / REGIMES / TRANSMISSION
        -> SCENARIOS + SIGNPOSTS -> FORECASTS -> OUTCOMES
        -> EVALUATION / CALIBRATION / MODEL LEARNING
        ↺ feeds future WORLD STATE
WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH -> BRIEFING
```

This is the conceptual runtime relationship. The migration sequence below is
an implementation order for governed contracts, not a claim that Forecasts,
Outcomes or Model Learning must exist before World State can be assessed.

| Target layer | Current repository state | Assessment |
| --- | --- | --- |
| Canonical events | `data/canonical/registry.json`, schema `0.52`, stable `series_id`/`occurrence_id`, lifecycle and timing history | Already implemented and sound. Automated monitor and local runtime guards protect it. |
| Calendar projection | `src/world_signals/projection.py`, browser horizon/native-date views and `scripts/build_site.py` | Already implemented and sound as a read-only projection. It intentionally carries more registry context than a subscription feed. |
| ICS subscription output | `src/world_signals/icalendar.py`, `scripts/build_ics.py` and `docs/world-signals.ics` output | Implemented and hardened. It uses governed Canonical records plus the approved change ledger, stable occurrence-based UIDs, source-local timed values, deterministic `VTIMEZONE` components derived from Python's IANA database, governed `SEQUENCE`/`DTSTAMP`/`LAST-MODIFIED`, transparent expected windows, date-only windows and explicit omission of non-dated material. |
| Source registry / health | `data/sources/registry.json`, monitor expectations/adapters, runtime source-health summaries and review candidates | Already implemented and sound, but source health remains runtime evidence rather than event truth. |
| Observations | `data/live_intelligence/` and `src/world_signals/live_intelligence.py` provide reviewed factual observations, evidence, timing separation and correction/revision controls | Implemented but needing extension. This is a bounded Live Intelligence layer, not yet a general observation store or public feed. |
| Signals | `data/signals/`, `src/world_signals/signals.py` and `src/world_signals/signal_admission.py` define a reviewed Signal over immutable Live observations, with revision, corroboration, contradiction, lifecycle, admission-transaction and public-projection guards | Contract implemented and pressure-tested; one controlled reviewed specimen is admitted, general population remains closed by default and public projection remains closed. |
| Relationships / causal layer | `data/relationships/schema.json` retains the hash-pinned empty v0.1 checkpoint; `data/relationships/schema_v0.2.json`, `src/world_signals/relationships.py`, `src/world_signals/world_state_relationship_candidate.py` and `src/world_signals/relationship_admission.py` define typed endpoints, exact lineage pins, historical reads and guarded admission | One RBNZ `ASSOCIATION` is admitted in the controlled v0.2 store with `EXPIRED` historical lifecycle; active graph edges and public projection remain zero/closed. |
| Risks / regime detection | `src/world_signals/risk_projection.py` remains the existing Canonical-derived presentation lens; `data/risks/`, `src/world_signals/risks.py` and `scripts/validate_risks.py` add a reviewed zero-population Risk/Regime history contract | Contract implemented and pressure-tested; production population and public projection remain closed. The existing overlay remains non-authoritative and unchanged. |
| Scenarios | `data/scenarios/`, `src/world_signals/scenarios.py` and `scripts/validate_scenarios.py` define reviewed Scenario Sets and conditional competing pathways | Contract implemented and pressure-tested; production population and public projection remain closed. It is not a forecast engine and does not infer scenarios from risk-overlay windows. |
| Forecasts | `data/forecasts/`, `src/world_signals/forecasts.py`, `src/world_signals/forecast_admission.py` and `scripts/validate_forecasts.py` define immutable, resolvable Forecast issuances with explicit information cutoffs, resolution sources and revision semantics | Contract implemented and pressure-tested; a bounded four-series prospective pilot is admitted only through an explicit transaction with pre/post hashes. `src/world_signals/forecast_operations.py` provides a read-only watch, while `src/world_signals/public_forecast_projection.py` exposes a separate four-series public Outlook allowlist. Outcome resolution, scoring, broader population and private metadata projection remain closed. |
| Outcomes / resolution | `data/outcomes/`, `src/world_signals/outcomes.py` and `scripts/validate_outcomes.py` record one governed result per Forecast series and map it to eligible issuances | Contract implemented and pressure-tested; production population, public projection and scoring remain closed. |
| Forecast evaluation | `data/evaluation/`, `src/world_signals/evaluation.py`, `scripts/validate_evaluation.py` and versioned configuration define deterministic issuance-level scoring and denominator/coverage summaries | Contract implemented and pressure-tested with four unresolved pilot issuances and zero Outcomes; state remains `NO_SAMPLE`, with public projection, baselines, rankings, calibration claims and Model Learning closed. |
| Model learning | No resolved production sample or learning pipeline | Missing and intentionally deferred. A resolved sample from the controlled prospective Forecast pilot must precede any learning claim. |
| World State synthesis | No general synthesis engine; `src/world_signals/world_state_read.py`, `src/world_signals/world_state_history.py`, `src/world_signals/world_state_production.py`, `src/world_signals/world_state_composition.py`, `src/world_signals/world_state_successor.py`, `src/world_signals/world_state_candidate.py`, `src/world_signals/world_state_admission.py`, `src/world_signals/world_state_rbnz_admission.py`, `data/world_state/` and `data/world_state_audit/` provide the private evidence/read boundary, immutable production-history validators, admitted-history read, explicit non-atomic composition view, component admissions, lineage-aware successor review, current-applicability derivation and retained evidence | Migration Steps 1–7 and Step 8A are complete. Step 8B admitted one narrow internal `HEALTH_BIOSECURITY` Dimension Assessment and snapshot; Step 11B adds narrow RBNZ `MACROECONOMIC_FINANCIAL_CONDITIONS` and `MARKETS_AS_SENSORS` assessments plus a second independent snapshot. Step 9A provides explicit knowledge/effective reads, derived freshness and deterministic deltas; Step 9B derives successor review from exact admitted lineage; Step 9C composes independently admitted series only at read time, preserves exact provenance, fails closed on component-head conflicts and keeps false atomicity out of production history. Step 11C keeps lifecycle, freshness and current applicability distinct: Health can be current-use eligible under policy, while RBNZ remains historical with `NO_CURRENTNESS_CLAIM`. Actor Registry, downstream analytical populations and public projection remain closed; this is not a general synthesis judgment. |
| Human review | Monitor candidates, retained review state, review decisions, controlled transactions and protected-layer tests are present | Already implemented and sound for current layers; extension is needed so future signal/scenario/forecast promotion remains review-governed. |
| Public/private boundaries | Canonical, runtime, review, Live, Analysis and static projections are separated; Pages publishes `docs/` only | Already implemented and sound for current layers. The ICS feed is now an additional deliberately publishable projection and excludes runtime/review-only material. |

Migration Step 11A adds a retained RBNZ Analysis specimen as review evidence,
not production state. The package contains two scoped Dimension Assessment
candidates: a narrow monetary-policy condition and a market-sensor reading. It
preserves separate economist-consensus and market-pricing comparison bases,
source-reported market endpoints and alternative explanations. The observed
association remains Analysis-owned; World State creates no Relationship or
transmission edge. The separate `WORLD_STATE_ACTOR_IDENTITY_ADMISSION`
boundary validates identity-only, manual-review-gated candidates and temporary
simulation while the Actor Registry remains empty. Production remains one
component, snapshot and admission, and public projection remains closed.

Step 11A.1 records a temporal-integrity correction to that specimen. Effective
time is not knowledge time: the Macro candidate retains the official decision
instant while the comparative proposition uses the reviewed Analysis boundary;
the Markets candidate falls back to executable civil-date precision for its
source-reported window; and the proposal-local actor identity carries an
explicit unknown historical effective-from plus separate identity-known time.
The original audit artifact remains immutable, all candidates remain pending,
and no production or public state is changed.

Step 11B admits exactly two corrected RBNZ Dimension Assessment revisions and
one independent compositional snapshot through a distinct human component
review and `WORLD_STATE_PRODUCTION_ADMISSION` transaction. Macro and Markets
are accepted narrowly; the proposal-local actor identity is explicitly
deferred. The production snapshot preserves Macro `UTC_INSTANT` and Markets
`CIVIL_DATE` precision, while the market association remains Analysis-owned
and non-causal. Health history is not rewritten, no Relationship or public
projection is created, and read-time multi-series composition remains
`INDEPENDENT_ADMISSIONS` rather than a jointly admitted global state.

Step 11C keeps current applicability as a derived read field rather than
production metadata. `ACTIVE` means not superseded, corrected, withdrawn or
expired; it does not mean present tense. Missing freshness policy maps to
`NO_CURRENTNESS_CLAIM`, invalid policy maps to `UNKNOWN`, and Health freshness
transitions are exposed separately from component/effective-state deltas.

Step 12A advances the Relationship contract to schema `0.2`. Reviewed Signals
remain supported, and exact immutable admitted World State component revisions
may now be endpoint nodes. Analysis/evidence remain supporting lineage and
composition views are prohibited as nodes. The retained RBNZ candidate is a
directed `ASSOCIATION` with source-reported temporal precision, not causal
evidence or an active transmission channel. An explicit temporal dependency
DAG rejects direct and multi-hop self-support cycles. Step 12B admits one
RBNZ Macro → Markets Relationship as a historical `ASSOCIATION` with
`DIRECTED` ordering, `MEDIUM` confidence and `EXPIRED` lifecycle. `EXPIRED`
means the event-bounded observation period is complete, not that the evidence
is false or withdrawn. The two endpoint components were separately reviewed
but admitted in the same Step 11B transaction and are not independent
corroboration. Active current graph edges and public projection remain zero.

### Implemented but needing extension

The strongest reusable foundations are the stable Canonical identity/timing
contract, the source-health versus event-truth separation, the reviewed Live
observation/evidence grammar, immutable Analysis snapshots and the protected
local-operation loop. The next layers should extend those contracts rather than
introducing a second event database. Live observations can become the upstream
observation substrate; the existing Analysis interaction fields can inform a
future relationship contract; and the risk overlay can remain a read-only
consumer while a separate regime-state contract is designed.

### Legacy, obsolete or potentially conflicting surfaces

- The old architecture text described calendar export as “optional” or
  “later”; the governed ICS projection is now the first completed external
  read interface, while Google Calendar writes remain prohibited.
- `scripts/run_local_operations.py` and the guarded macOS LaunchAgents are the
  recurring intelligence runtime. The scheduled GitHub monitor cron was
  redundant with that local operating model and is now manual-dispatch only;
  CI, Pages deployment, adapter smoke tests and coverage audits remain intact.
- GitHub Pages may publish a static `.ics` file, but it must not become the
  monitoring runtime or a source of canonical truth. The feed is rebuilt from
  the governed registry during the existing site build.
- The browser Operations/runtime and retained-review projections remain dated
  evidence surfaces. They are not inputs to the ICS builder and are never
  promoted into public calendar events.

### Subscription-feed interoperability contract

The iCalendar projection is generated by the local site build from governed
Canonical records and the approved occurrence change ledger. A timed event
with `source_timezone` emits that IANA TZID and the feed emits a matching
`VTIMEZONE`; definitions are limited to the zones and event-year range needed
by the included events, with offsets/transitions read from Python `zoneinfo`.
This preserves source-local semantics without hand-maintained DST rules.

`UID` is the stable occurrence identity. `SEQUENCE` is the sum of governed
status-history revisions and occurrence-specific approved ledger transactions,
so timing-only changes do not depend on `status_history` length and unrelated
registry changes do not revise another event. `DTSTAMP` uses the earliest
known governed timestamp and `LAST-MODIFIED` the latest governed revision
timestamp; rebuild execution time is never used. Expected date windows remain
date ranges and are marked `TRANSP:TRANSPARENT` so they are visible without
blocking subscriber free/busy time. A governed `CANCELLED` event remains
auditable under its stable UID with `STATUS:CANCELLED` and transparent
availability. `POSTPONED` uses RFC-valid `STATUS:TENTATIVE`, an explicit
date-not-confirmed summary and transparent availability; an old date is never
presented as a confirmed appointment. Dated `PROVISIONAL`/`TBC` events are
also tentative, while `COMPLETED` is not mapped to an unrelated RFC status.

### Smallest sensible migration sequence

1. Complete and validate the governed ICS projection (completed), including
   static publication and omission tests.
2. Define and pressure-test a minimal reviewed `signal` contract (completed)
   that references
   one or more immutable observations and records direction, novelty,
   persistence, corroboration, confidence and transmission relevance. The
   executable contract now exists, but population remains closed until a
   separate reviewed admission transaction is justified.
3. Define and pressure-test a generic reviewed Relationship contract (completed)
   with explicit relationship class, directionality, alternatives,
   disconfirming evidence and revision history, reusing existing Analysis and
   overlay semantics without making either overlay canonical. Production
   population remains closed.
4. Define and pressure-test a governed Risk/Regime-State history contract
   (completed) that consumes reviewed Signals and Relationships while
   preserving the current risk overlay as a non-authoritative projection.
5. Define and pressure-test explicit Scenario Sets and competing conditional
   pathways (completed), keeping assumptions, divergence points, signposts and
   falsification separate from forecasts.
6. Define and pressure-test immutable Forecast records with explicit
   resolution criteria (completed); keep analytical updates scoreable without
   replacing earlier issuances.
7. Add Outcomes/Resolution and Evaluation contracts (completed) without
   populating production. Authorise a narrow prospective Forecast pilot only
   after review; do not begin Model Learning until a defensible resolved sample
   and evaluation denominator exist.
8. Define the World State Synthesis Engine v1 read contracts and minimal
   consistency fixture: actor model, implementation-state ladder, dimensions,
   baselines/anomalies, negative evidence, typed uncertainty, competing
   hypotheses, model disagreement, transmission graph, scenarios/signposts and
   forecast/outcome/calibration references. Keep the engine unimplemented until
   the fixture and review boundary are approved. This implementation step does
   not make Forecasts, Outcomes or Model Learning prerequisites for a World
   State assessment; their later evidence feeds the synthesis loop.
9. Define the production World State history contract as a separate,
   componentized immutable design with Actor Registry identity, snapshot
   references, explicit three-time semantics, partial admission, retention and
   private/public gates (completed in Migration Step 6; no population).
10. Implement and pressure-test the unpopulated production history contract
    and temporary-copy admission simulator (completed in Migration Step 7);
    construct and preflight one narrow real-evidence candidate in Step 8A;
    keep review-pending snapshot candidates distinct from admitted snapshots;
    admit the first narrow component through Step 8B human review and a
    production admission transaction; defer broader population and synthesis.

No synthetic observations, signals, scenarios or forecasts are added by this
baseline tranche.

## GitHub is an execution shell, not the architecture

GitHub Actions runs validation and monitors, GitHub Pages hosts read-only projections, and pull requests/commits provide review and audit history. The Python/JSON contracts remain portable to another CI/host. GitHub Actions artefacts are evidence surfaces, not canonical storage.

## Current promotion path

```text
Research / taxonomy / source governance                    [ONGOING]
  -> executable Canonical Registry + read-only UX           [DONE]
  -> review-candidate / source-health contracts              [DONE]
  -> heterogeneous live Source/Change adapters, review-only  [DONE: 8 configured]
  -> scheduled monitor execution / retained evidence         [DONE]
  -> controlled Analysis foundation + diverse sample         [DONE: 20 reviews / 18 event types]
  -> Live Intelligence executable zero-population foundation [DONE: AV]
  -> first pressure-audited Live Intelligence specimen       [DONE: AW — Nepal flood]
  -> evolving-state / manual story semantics                  [DONE: AX — DRC Bundibugyo]
  -> test prospective Live Intelligence -> Analysis linkage  [NEXT AUDIT CANDIDATE]
  -> broader Live Intelligence population                    [ONLY AFTER AUDIT]
  -> governed subscription calendar export                    [DONE]
  -> reviewed Signal contract / zero-population gate          [DONE]
  -> reviewed Relationship contract / zero-population gate     [DONE]
  -> regime-state / risk history contract                     [DONE: zero-population]
  -> World State Synthesis Engine v1 read adapter / proposal   [DONE: private, read-only]
  -> admitted World State history read / freshness / delta      [DONE: internal, read-only]
  -> narrow auto-commit classes                              [ONLY IF EMPIRICAL GATE OPENS]
```

A generic guarded reviewed commit/rollback mechanism remains an architectural objective; existing controlled tranche transactions demonstrate the safety pattern but do not open blanket automation authority.

The automatic-canonical-commit gate remains closed. Before it can even be reconsidered, WORLD SIGNALS still requires real prospective evidence including a reschedule detected against a prior canonical snapshot and an explicit cancellation of an already-canonical occurrence, under the governed review process.
