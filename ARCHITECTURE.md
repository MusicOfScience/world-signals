# Executable architecture

## Governing rule

`WORLD_SIGNALS_PROJECT_CHARTER.md` is authoritative. The executable repository implements its layers as separate governed contracts rather than one blended event/news database.

Current post-#78 / AX evolving-state Live Intelligence state:

- Canonical `v0.38 / 688`;
- Source Registry `v1.80 / 243`;
- Source/Change Monitor expectations `v0.10 / 8 adapters`;
- Live Intelligence `v0.3 / 3 internal observations / 4 evidence`, controlled multi-snapshot gate; public observations `0`;
- Analysis `v0.16 / 20 reviews / 91 evidence` on schema `v0.4`;
- automatic canonical commit OFF;
- Google Calendar writes OFF.

## Runtime layers

1. **Canonical Registry** — versioned authoritative event identities, lifecycle and timing.
2. **Calendar / Web projection** — derived read-only rendering; never the database.
3. **Source / Change Monitor** — read-only adapters inspect authoritative sources, source health and candidate changes.
4. **Live Intelligence** — factual current-development observations that may be scheduled or unscheduled and may optionally reference Canonical occurrences.
5. **Analysis** — reviewed interpretation of expectations, surprises, market observations, connections, noise, alternatives, second-order effects and falsifiers.

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

Live Intelligence is also not Analysis. It may record a factual market observation, shock, announcement or revision, but it may not claim what was expected, what surprised, what caused a move or which interpretation is preferred.

Unscheduled physical shocks, health emergencies and geopolitical developments can therefore exist without inventing scheduled Canonical occurrences. If a Live observation references Canonical, the occurrence ID must resolve.

## Reviewed Signal contract — population closed

The first Signal milestone is now an executable contract at
`data/signals/schema.json`, `data/signals/signals.json` and
`src/world_signals/signals.py`. It reuses immutable Live Intelligence
`observation_id` and evidence lineage rather than creating a second observation
store. A Signal is a reviewed analytical inference: it records direction,
materiality, novelty, persistence, trend state, corroboration, confidence,
transmission relevance, falsification conditions and explicit lifecycle/review
state without asserting a causal relationship or encoding a forecast.

Production admission (`validate_signals`) rejects **every populated dataset**;
no test flag or population label opens it. `validate_signal_history` is a
separate read-only proposal validator, used by synthetic tests and granting no
storage, promotion or publication authority. The public projection validates
the production gate and returns zero Signals. No dashboard or risk-overlay
consumer was added.

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

## Reviewed Relationship contract — population closed

The generic Relationship layer is now defined as a separate, executable,
zero-population contract in `data/relationships/` and
`src/world_signals/relationships.py`. It consumes reviewed Signal revisions as
its primary nodes, while allowing immutable Live observations/evidence and
Canonical occurrences to provide traceable support or context. Raw monitor
candidates, unreviewed Signals and private runtime records are not eligible
nodes, and no Relationship is stored in production by this tranche.

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
author a new Relationship. Forecast and scenario fields are outside this
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

## Static UX and runtime truth

GitHub Pages cannot honestly claim current monitor health merely because a build was green. The Monitor view exposes configured routes, while runtime source health and review candidates remain timestamped evidence.

Likewise, AX emits `docs/data/live_intelligence.json` only as **curated-store metadata**. It reports three internal observations and four internal evidence rows while exposing zero public observations and explicitly stating that it is not a runtime feed. A browser Live Intelligence feed is not authorised by this tranche.

## 2026-09-26 architecture baseline and migration gap assessment

This assessment is based on the governed registries, executable modules, tests,
local-operation scripts, static build and workflows in this repository. It is a
baseline for the incremental transition to:

```text
EVENTS -> OBSERVATIONS -> SIGNALS -> RELATIONSHIPS -> RISKS
        -> SCENARIOS -> FORECASTS -> OUTCOMES -> MODEL LEARNING
```

| Target layer | Current repository state | Assessment |
| --- | --- | --- |
| Canonical events | `data/canonical/registry.json`, schema `0.52`, stable `series_id`/`occurrence_id`, lifecycle and timing history | Already implemented and sound. Automated monitor and local runtime guards protect it. |
| Calendar projection | `src/world_signals/projection.py`, browser horizon/native-date views and `scripts/build_site.py` | Already implemented and sound as a read-only projection. It intentionally carries more registry context than a subscription feed. |
| ICS subscription output | `src/world_signals/icalendar.py`, `scripts/build_ics.py` and `docs/world-signals.ics` output | Implemented and hardened. It uses governed Canonical records plus the approved change ledger, stable occurrence-based UIDs, source-local timed values, deterministic `VTIMEZONE` components derived from Python's IANA database, governed `SEQUENCE`/`DTSTAMP`/`LAST-MODIFIED`, transparent expected windows, date-only windows and explicit omission of non-dated material. |
| Source registry / health | `data/sources/registry.json`, monitor expectations/adapters, runtime source-health summaries and review candidates | Already implemented and sound, but source health remains runtime evidence rather than event truth. |
| Observations | `data/live_intelligence/` and `src/world_signals/live_intelligence.py` provide reviewed factual observations, evidence, timing separation and correction/revision controls | Implemented but needing extension. This is a bounded Live Intelligence layer, not yet a general observation store or public feed. |
| Signals | `data/signals/` and `src/world_signals/signals.py` define a reviewed Signal over immutable Live observations, with revision, corroboration, contradiction, lifecycle and public-projection guards | Contract implemented and pressure-tested; production population remains closed. |
| Relationships / causal layer | `data/relationships/`, `src/world_signals/relationships.py` and `scripts/validate_relationships.py` define a reviewed, zero-population contract using Signal revisions plus explicit evidence and causal gates | Contract implemented and pressure-tested; production population and public projection remain closed. |
| Risks / regime detection | `src/world_signals/risk_projection.py` remains the existing Canonical-derived presentation lens; `data/risks/`, `src/world_signals/risks.py` and `scripts/validate_risks.py` add a reviewed zero-population Risk/Regime history contract | Contract implemented and pressure-tested; production population and public projection remain closed. The existing overlay remains non-authoritative and unchanged. |
| Scenarios | No governed scenario registry or competing-scenario contract | Missing. Do not infer scenarios from risk-overlay windows. |
| Forecasts | Analysis records preserve expectations and comparisons in bounded post-event packets, but there is no immutable resolvable forecast store | Missing. A future contract must record target, horizon, probability/interval, assumptions, evidence, resolution criteria and version lineage. |
| Forecast evaluation / model learning | No forecast-resolution/evaluation population or scoring pipeline | Missing. This follows the forecast contract and a defensible resolved sample; it is not a prerequisite for the ICS feed. |
| Human review | Monitor candidates, retained review state, review decisions, controlled transactions and protected-layer tests are present | Already implemented and sound for current layers; extension is needed so future signal/scenario/forecast promotion remains review-governed. |
| Public/private boundaries | Canonical, runtime, review, Live, Analysis and static projections are separated; Pages publishes `docs/` only | Already implemented and sound for current layers. The ICS feed is now an additional deliberately publishable projection and excludes runtime/review-only material. |

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
5. Add competing scenario records, then immutable forecast records with
   resolution criteria. Only after resolved forecasts exist should evaluation
   metrics and model-learning surfaces be implemented.

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
  -> regime-state / risk history contract                     [NEXT]
  -> narrow auto-commit classes                              [ONLY IF EMPIRICAL GATE OPENS]
```

A generic guarded reviewed commit/rollback mechanism remains an architectural objective; existing controlled tranche transactions demonstrate the safety pattern but do not open blanket automation authority.

The automatic-canonical-commit gate remains closed. Before it can even be reconsidered, WORLD SIGNALS still requires real prospective evidence including a reschedule detected against a prior canonical snapshot and an explicit cancellation of an already-canonical occurrence, under the governed review process.
