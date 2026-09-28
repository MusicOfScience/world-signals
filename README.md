# WORLD SIGNALS

WORLD SIGNALS is a platform-independent global political-economic intelligence system for tracking scheduled events, authoritative-source changes, current developments and structured analytical interpretation across economics, monetary and fiscal policy, politics, elections, geopolitics, institutions, trade, sanctions, markets, commodities, energy, climate, physical risk, health/biosecurity, technology and critical infrastructure.

**Live read-only interface:** https://musicofscience.github.io/world-signals/

`WORLD_SIGNALS_PROJECT_CHARTER.md` is the authoritative architectural and methodological specification. Governed registries/contracts remain operational truth. `data/status/current_state.json`, the current-state block below and the matching blocks in `PROJECT_STATUS.md` / `ROADMAP.md` are mechanically derived recovery surfaces and are checked by CI.

<!-- WORLD_SIGNALS_CURRENT_STATE_BEGIN -->
## Mechanically derived current state

**Reference date:** 2026-09-29
**Authority:** this block and `data/status/current_state.json` are derived recovery surfaces. Governed registries/contracts remain operational truth.

- Canonical Registry: **v0.44 / 690 occurrences**; schema **v0.52**.
- Source Registry: **v2.05 / 260 sources**.
- Change Ledger: **v0.29 / 64 entries**.
- Monitor expectations: **v0.28 / 26 configured adapters / 25 unique monitor sources / 217 explicitly scoped Canonical occurrences**.
- Live Intelligence: **v0.13 / 12 observations / 16 evidence rows / 4 Canonical-linked observations**; automatic ingestion and public observation projection remain closed.
- Analysis: schema **v0.8**; reviews **v0.18 / 22**; evidence **v0.18 / 97**; production Live inputs **1**; production revisions **1**.
- Signals: schema **v0.1 / 1 admitted revision(s)**; population **CONTROLLED_REVIEWED_SIGNAL_SPECIMEN**; admission transaction required; maximum production population **1**; public projection **closed**.
- NHC Atlantic pilot: **PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT**; registered in scheduled Monitor expectations: **true**.
- Automatic Canonical commit: **OFF**. Google Calendar writes: **OFF**. Public Live and Live-input projection: **OFF**. Public Analysis revision metadata/latest-head collapse: **OFF**.
- OPEC CE remains quarantined; `OPEC_QUARANTINE.md` is present and PR #113 is not a selectable unfinished transaction.
<!-- WORLD_SIGNALS_CURRENT_STATE_END -->

## Layer contract

```text
ACTORS + EVENTS
      |
      v
OBSERVATIONS
      |
      v
SIGNALS + ANOMALIES
      |
      v
RELATIONSHIPS + FLOWS + DEPENDENCIES
      |
      v
WORLD STATE (continuously updated, as-of, derived)
      |
      +--> COMPETING HYPOTHESES / REGIMES / TRANSMISSION
      |          |
      |          v
      |     SCENARIOS + SIGNPOSTS
      |          |
      |          v
      |     FORECASTS
      |          |
      |          v
      |     OUTCOMES
      |          |
      |          v
      |     EVALUATION / CALIBRATION / MODEL LEARNING
      |          |
      |          +------ feeds future WORLD STATE assessments
      |
      +--> WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH
                           |
                           v
                        BRIEFING
```

Canonical Registry, Source / Change Monitor and the existing reviewed Analysis
bridge remain governed inputs or parallel projections around this lifecycle;
they do not turn World State into a terminal downstream layer. The contract
inventory below is deliberately distinct from runtime dependency order:

1. **Canonical Registry** — what the event is: stable identities, lifecycle, certainty, timing and provenance.
2. **Calendar** — rebuildable human-facing projection from Canonical.
3. **Source / Change Monitor** — source health, authoritative change detection and review candidates; no automatic Canonical mutation.
4. **Live Intelligence** — evidence-backed factual observations around scheduled and unscheduled developments; no causal interpretation.
   The local OSINT v1 engine sits upstream as a candidate-only retrieval and
   normalisation layer; it does not write this governed store.
5. **Signals** — reviewed analytical patterns over immutable observations, with explicit uncertainty, corroboration and transmission hypotheses.
6. **Analysis** — expectations, surprise, market response, relationships, alternatives, uncertainty and second-order effects.
7. **Relationships** — reviewed analytical connections between Signal revisions,
   with explicit epistemic class, directionality, alternatives, contradiction,
   mechanism and causal-evidence gates. The executable contract is currently
   zero-population; it does not promote plausible transmission into causation,
   and its public projection is closed.
8. **Risks / Regimes** — reviewed qualitative state and transition history over
   Signals and Relationships. Convergence is lineage-derived and explicit;
   numeric danger scores, forecasts, scenarios and public projection remain
   prohibited. The production state population is currently zero.
9. **Scenarios** — reviewed conditional pathways grouped into competing
   Scenario Sets. Shared assumptions, divergence points, signposts and
   disconfirming indicators remain explicit; probability, ranking and forecast
   fields are prohibited. The production Scenario population and public
   projection are currently closed.
10. **Forecasts** — immutable, review-governed and resolvable claims with
    explicit question, horizon, information cutoff, resolution rule and
    probability/estimate semantics. Analytical updates are separate issuances;
    administrative corrections cannot rewrite substantive content. Outcome
   resolution, scoring and broad public projection remain deferred. A separate
   allowlisted public Outlook projection now exposes the four reviewed,
   unresolved monetary-policy pilot issuances; the governed Forecast dataset
   remains private and its broader population remains closed.
11. **Outcomes / Resolution** — one governed real-world result per immutable
    Forecast question series, linked to every eligible issuance without
    duplicating reality. Resolution follows the Forecast's original rule,
    source, fallback and vintage semantics. Scoring, evaluation and public
    projection remain deferred, and production Outcome population is closed.
12. **Forecast Evaluation** — deterministic derived scoring of each Forecast
    issuance against the governed Outcome, with explicit metric compatibility,
    lead time, resolution coverage and denominator states. Brier/log loss,
    categorical proper scores and numeric errors are supported for synthetic
    fixtures only; calibration claims, baselines, rankings, Model Learning and
    public performance projection remain closed while production populations
    are empty.

The reviewed Signal contract adds an analytical interface over Live
Intelligence. It is deliberately separate from factual observations and from
the existing Analysis packets: it may record a reviewed pattern or change, but
it may not rewrite observations, assert a causal chain, become a forecast or
populate itself automatically. The first tranche admits one reviewed Signal
from two immutable governed health observations through
`data/signals/signal_admission_transaction_v1.json`; the public projection and
general population remain closed by default.

`validate_signal_history` remains a read-only proposal validator. Populated
production state requires the explicit reviewed admission transaction, retained
pre/post hashes, reviewer provenance and the hard one-Signal tranche limit.
The five machine Signal Candidates from the OSINT bootstrap run were reviewed
but none was treated as sufficient admission evidence. See the Signal contract
section in `ARCHITECTURE.md` for lineage, review, history, expiry and
candidate-disposition semantics.

The static build also publishes a read-only subscription projection,
`world-signals.ics`, from the governed Canonical/calendar state. It is not a
second event database: stable occurrence identities become stable iCalendar
UIDs, source-local timed events retain their IANA timezone, explicit date
windows remain windows, and unresolved TBC/native-calendar/runtime/review
material is not exported. The feed includes deterministic `VTIMEZONE`
definitions generated from Python's system IANA timezone database only for
zones used by included timed events. Expected windows use
`TRANSP:TRANSPARENT`: they remain visible as uncertainty windows without
claiming the whole interval as subscriber free/busy time.

Google Calendar, GitHub Pages, retained Actions evidence and prose status documents are interfaces or derived evidence surfaces, not canonical databases.

The public brief follows the reader sequence `OUTLOOK → RESOLUTION CLOCK →
REVIEWED ANALYSIS → FULL HORIZON → RESEARCH`. Calendar counts remain available
with the Calendar, while World State coverage remains an internal Research
boundary. The Outlook projection keeps each Forecast's own information cutoff
and uses only exact reviewed Calendar occurrence links.

### World State direction

The next product boundary is a derived **World State**, not a larger event
calendar or an ungoverned news graph. World State will assemble reviewed
evidence into as-of views of actor behaviour, implementation status,
capabilities and constraints, conflict/military activity,
strategic/geopolitical tension, political/institutional stability, flows,
dependencies, chokepoints and market-sensed conditions. Its design must also
retain baselines and anomalies, negative evidence, typed uncertainty,
competing hypotheses, model disagreement, lags, thresholds, feedback loops and
reflexivity.

Actor statements must not be promoted directly into state policy. The required
ladder is:

`SAID → DECIDED → AUTHORISED → IMPLEMENTED → OBSERVED`

Each step requires appropriate evidence and can remain disputed or diverge
from the others. Conflict and military activity are first-class domains;
markets are sensors with explicit timing, baseline and alternative-explanation
metadata; transmission edges are typed rather than inferred from proximity.

World State is the continuously updated synthesis hub, not a terminal stage
after Forecast Evaluation or Model Learning. A system with observations,
Signals, Relationships and state dimensions can still produce an as-of World
State assessment when no Forecast or Outcome exists. Later Outcomes,
Evaluation, calibration and Model Learning provide time-indexed feedback for
subsequent World State assessments.

The World State Synthesis Engine v1 is not implemented by the current
repository state. Its completed read-boundary milestones include a test-only
fixture, a read-only adapter, a retained consistency proposal and a human
review limited to `READ_BOUNDARY_CONSISTENCY_ONLY`. Migration Step 6 now defines
the production history contract in
`WORLD_STATE_PRODUCTION_HISTORY_CONTRACT_DESIGN.md`: componentized immutable
revisions, reviewed Actor Registry identity, explicit three-time semantics,
component-level admission and private/public gates. No production World State
population or Actor Registry exists. The next implementation tranche is
contract validation and temporary admission simulation; Scenarios/signposts,
Forecasts, Outcomes and calibration remain governed by their own contracts,
and the briefing remains a projection rather than a new database.

The intended human product surface is:

```text
WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH
```

## Local OSINT candidate engine

`data/osint/source_cohort.json` defines a deliberately small eight-route cohort
of first-party machine interfaces whose retrieval and ingestion permissions are
explicitly cleared in the Source Registry. `python scripts/run_osint_engine.py
--once` performs one local read-only pass and writes retrieval metadata,
Observation Candidates, story clusters, Signal Candidates and a review queue to
the ignored `.world-signals-runtime/osint/` directory. The runner has no daemon
mode and can be invoked by a local scheduler at source-appropriate cadences.

This is intentionally not a second Live Intelligence database:

```text
MONITOR (governed surface changed?)
    != OSINT CANDIDATE ENGINE (what factual development may deserve review?)
    != LIVE INTELLIGENCE (reviewed immutable Observation)
    != SIGNAL (reviewed analytical inference)
```

Fetch failure, parser failure, empty feeds and permission holds produce source
health evidence only. Candidate queues are private and non-governed; automatic
Canonical, Observation, Signal, Relationship, Risk, Scenario and Forecast
promotion is closed. See `OSINT_RUNBOOK.md` for the source cohort, lineage and
review boundary.

The runtime distinguishes a first `BOOTSTRAP` history inventory from later
`INCREMENTAL` checks. Retained source-native identities and record hashes keep
feed replay, parser-version changes and historical discovery from masquerading
as current novelty. On 27 September 2026 the retained checkpoint produced
seven unchanged routes, one source-specific BSP 403 and no new candidates;
governed populations were unchanged.

## Source and monitoring governance

Source competence and automation permission are independent questions. A source may be authoritative for Canonical provenance while remaining unsuitable or unauthorised for unattended monitoring. Machine-only monitor identities may therefore be separate from Canonical provenance identities.

Configured Monitor routes are governed in `data/monitor/expectations.json`. Route presence does not grant lifecycle, certainty, schedule, clock, Canonical-write, Live-promotion or Analysis-promotion authority unless an explicit reviewed contract says so. Source failure, absence and parser failure remain source-health evidence rather than event-state evidence.

The NOAA/NHC Atlantic-season route was validated as a bounded pilot in CF and activated into scheduled Monitor expectations in PR #117 after a fresh source, rights, endpoint, scope and runtime review. It remains limited to exactly two existing Atlantic hurricane-season Canonical occurrences: NHC climatology is the season-definition semantic authority, Atlantic outlook RSS is source-health corroboration only, and neither source grants automatic lifecycle, schedule, certainty, completion, Canonical-write, Live-promotion or Analysis-promotion authority.

## Live Intelligence

The controlled internal Live layer currently exercises several distinct contracts rather than a general news feed: unscheduled physical shock, evolving health state, scheduled economic outcome, geopolitical development, institutional development, reviewed pre-event Canonical context and one OSINT-originated Federal Reserve policy-decision observation. The OSINT promotion is bounded by an explicit reviewed transaction and preserves candidate/source hashes; it does not open automatic ingestion or downstream Signal promotion.

Canonical linking is optional. Unscheduled real-world developments do not acquire invented Canonical identities merely to make the graph denser. Event time, source publication time, state-as-of time and WORLD SIGNALS observation time remain separate concepts.

Automatic ingestion, automatic story clustering, public observation projection, automatic Canonical commit and Calendar writes remain closed.

## Analysis

Analysis is post-event and anchored to existing completed Canonical occurrences. Live observations may be selected only through reviewed immutable `observation_id` relationships under the bridge contract; Live evidence is not transitively promoted into Analysis evidence.

Revision lineage is immutable: a later analytical judgement is a new Analysis snapshot linked to its parent, not an in-place rewrite. Automatic latest-head selection and public revision-head collapse remain prohibited.

## Cross-domain risk overlay

The dashboard includes a derived, read-only risk lens over existing Canonical records. It keeps intrinsic importance, expected market sensitivity, geopolitical sensitivity and transmission channels as separate dimensions, and maps signals non-exclusively across geopolitics, trade, energy, macro/monetary, financial/sovereign, health/biosecurity, climate/physical, technology/infrastructure and food/agriculture domains.

Calendar-week convergence windows show signal density only. They are not probability estimates, severity rankings, causal claims or authority to create or modify events. The overlay does not consume private Live Intelligence or infer Analysis conclusions. Existing Canonical OPEC records may appear mechanically like any other governed event, but the quarantined OPEC provenance transaction remains dormant and unchanged.

This existing `risk_projection` output is a read-only Canonical-derived
presentation lens, not governed Risk/Regime truth. The separate reviewed
Risk/Regime contract in `data/risks/` records current and historical states over
reviewed Signals and Relationships, remains zero-population, and does not feed
the overlay or publish a risk state yet.

## Time and uncertainty

Canonical event time preserves source-native IANA timezone and UTC time when those exist. Australia/Melbourne is a home/reference display context, never canonical storage time. Civil dates, native month windows, recurring rules, provisional timing and unresolved timing remain at their supported precision rather than being promoted to synthetic timestamps.

Intrinsic importance, expected market sensitivity and observed market response remain separate. Analysis must distinguish what happened, what was expected, what surprised, what moved, plausible connections, noise, alternative explanations and second-order effects without post-hoc causal storytelling.

## OPEC quarantine

`OPEC_QUARANTINE.md` and closed/unmerged PR #113 preserve the failed CE provenance transaction as historical evidence. Normal work must not reopen, merge, cherry-pick, rebase, materialise or use that branch as a base. Any future OPEC work starts from then-current `main` under a fresh bounded design.

## Run locally

### Public site and local operator cockpit

The public site is built from deliberately publishable projections only:

```bash
python scripts/build_site.py
python scripts/validate_public_site.py
```

The build writes disposable output to `docs/`. It includes the Canonical
calendar projection, `world-signals.ics`, a dedicated allowlisted Outlook
projection, source metadata and public layer status. The
`docs/data/outlook.json` contract contains only the four reviewed
monetary-policy pilot Forecasts and public-safe fields; the build does not
include `.world-signals-runtime`, monitor checkpoints, Observation Candidates,
Signal Candidates, retained review state, private Forecast metadata or the
governed Forecast file.

The private read-only operator cockpit is a separate local artefact:

```bash
python scripts/build_operator_site.py
python -m http.server 8765 --directory operator
```

Open `http://127.0.0.1:8765/operator.html`. This surface may include local
runtime/review evidence and internal Forecast detail, but it is ignored by Git
and is never copied into `docs/`.

### Explicit Pages publication

Hosted Actions are not required for publication. After the source PR has been
merged, synchronize local `main` with `origin/main` and run:

```bash
python scripts/publish_pages.py --source-branch main --publication-branch gh-pages
```

The command requires a clean checkout whose `HEAD` equals `origin/main`, runs
the deterministic build and public-boundary validation, then commits only
generated `docs/` output to `gh-pages` without mutating `main`. Use
`--check-only` to validate without pushing. The repository Pages setting must
be changed once, outside this repository, to **Deploy from a branch** →
`gh-pages` → `/ (root)`. Until that setting is changed, the existing
Actions-based Pages configuration remains the external publication blocker.

```bash
python scripts/validate_registry.py
python scripts/validate_live_intelligence.py
python scripts/validate_signals.py
python scripts/validate_relationships.py
python scripts/validate_risks.py
python scripts/validate_analysis.py
python scripts/project_state_snapshot.py --check
python -m unittest discover -s tests -v
python scripts/run_cross_layer_coverage_audit.py
python scripts/build_site.py
```

`python scripts/build_site.py` generates derived site output locally. Generated site material is not Canonical state. `python scripts/run_cross_layer_coverage_audit.py` generates read-only diagnostic artifacts under `artifacts/coverage/`; those artifacts do not authorise population or writes.

To build only the governed subscription feed after a registry/source change:

```bash
/opt/homebrew/bin/python3.13 scripts/build_ics.py
```

The feed is written to `docs/world-signals.ics` and can be checked locally
alongside the dashboard at `http://127.0.0.1:8765/world-signals.ics` after
building the site. The intended static subscription URL is
`https://musicofscience.github.io/world-signals/world-signals.ics`, subject to
the existing Pages deployment succeeding.

Each VEVENT keeps a stable occurrence-based `UID`. `SEQUENCE` is derived from
that occurrence's governed status history and approved change-ledger entries,
so timing and lifecycle revisions advance the subscription revision without
using build count or wall-clock state. `DTSTAMP` is the earliest known governed
event timestamp and `LAST-MODIFIED` is the latest known governed revision
timestamp; neither is set from feed-build execution time.

Lifecycle semantics are conservative: a governed `CANCELLED` occurrence keeps
its stable UID and original date for auditability, emits `STATUS:CANCELLED`,
and is transparent. `POSTPONED` emits RFC-valid `STATUS:TENTATIVE` with an
explicit date-not-confirmed summary and is also transparent, so an old date is
not presented as a confirmed appointment. Dated `PROVISIONAL`/`TBC` records
use `STATUS:TENTATIVE`; `COMPLETED` is not forced into an unrelated RFC status.

The reviewed Relationship contract is also defined and pressure-tested with
production population and public projection closed. It preserves alternatives
and disconfirming evidence and does not infer transitive or causal edges.
The reviewed Risk/Regime-State contract is now also defined and pressure-tested
with production population and public projection closed. It preserves state
history, contradiction, qualitative convergence and explicit expiry without
becoming a danger score, scenario or forecast. The reviewed Scenario contract
is now also defined and pressure-tested with explicit Scenario Sets, conditional
assumptions, divergence points, signposts, disconfirming indicators and
immutable as-of history. Its production population and public projection remain
closed. The reviewed Forecast contract is now also defined and pressure-tested
with production population and public projection closed. Outcomes/Resolution
and the deterministic Forecast Evaluation contract are now also defined with
production populations and public projections closed. Evaluation deliberately
reports `NO_SAMPLE`/`INSUFFICIENT_SAMPLE` rather than making performance claims.
The current operating milestone is a separately authorised, narrow prospective
Forecast pilot that can create a defensible resolved sample; Model Learning
must wait until after that sample exists. A first bounded prospective pilot of
four institutional decisions is admitted through
`data/forecasts/admission_transaction.json`; Outcomes remain empty and every
issuance is a permanent future evaluation-denominator obligation.
The read-only operational watch is available through
`python scripts/forecast_operations.py`; its runbook is
`FORECAST_OPERATIONS_RUNBOOK.md`. It derives review and resolution states
without changing Forecasts or creating Outcomes.

### Local operating loop

GitHub Actions is an execution shell, not an architectural dependency. To validate the governed state, run all configured read-only monitors, retain private local evidence, produce sanitized Operations projections and rebuild the dashboard in one command:

```bash
/opt/homebrew/bin/python3.13 scripts/run_local_operations.py
```

To serve the freshly built dashboard on loopback after the run completes:

```bash
/opt/homebrew/bin/python3.13 scripts/run_local_operations.py --serve
```

Open `http://127.0.0.1:8765/`. Local runtime history is stored under ignored `.world-signals-runtime/`; disposable build inputs remain under ignored `artifacts/` and `review_candidates/`. The runner requires a clean tracked worktree and hash-protects Canonical, Sources, Change Ledger, Monitor contracts, Live Intelligence, Analysis, analytical/coverage overlays and the OPEC quarantine. It never commits, changes Canonical, writes Google Calendar or promotes Monitor evidence automatically.

The Operations view reduces repeated candidates into stable `WSRV-*` review propositions and provides read-only operator routing: attention class, controlled next step, recurrence, evidence-object IDs, filters and deterministic ordering. Those labels organise human review only. Decisions remain reviewed repository records, and any approved Canonical change still requires a separate transaction plus explicit change-ledger linkage.

The recurring monitor runtime is local. The GitHub live-monitor workflow is
manual-dispatch only; CI, adapter smoke, coverage audits and the Pages static
deployment remain useful validation/publication workflows.

### Guarded macOS local service

The local stack can be packaged as two user-level LaunchAgents: a daily governed refresh and a persistent dashboard bound only to `127.0.0.1:8765`. Both services start from a neutral working directory under `~/Library/Application Support/WORLD SIGNALS` so macOS does not stall interpreter startup inside the protected `Documents` folder; repository scripts and dashboard files remain exact absolute inputs. Review the generated manifests without changing machine settings:

```bash
/opt/homebrew/bin/python3.13 scripts/manage_local_service.py render
```

Installation is deliberately separate from code review and requires a clean reviewed `main` plus `WORLD_SIGNALS_INSTALL_LOCAL_SERVICE=YES`. Every scheduled refresh also fails closed unless the checkout is still clean `main` and exactly matches its tracked upstream head; feature work is never published as a production run. Uninstallation has its own `WORLD_SIGNALS_UNINSTALL_LOCAL_SERVICE=YES` gate. The service manager never grants Canonical, Calendar, Live/Analysis promotion, Git commit or merge authority.

```bash
WORLD_SIGNALS_INSTALL_LOCAL_SERVICE=YES /opt/homebrew/bin/python3.13 scripts/manage_local_service.py install
/opt/homebrew/bin/python3.13 scripts/manage_local_service.py status
WORLD_SIGNALS_UNINSTALL_LOCAL_SERVICE=YES /opt/homebrew/bin/python3.13 scripts/manage_local_service.py uninstall
```

To deliberately refresh the derived status snapshot and the three marked documentation blocks after a reviewed governed change:

```bash
WORLD_SIGNALS_WRITE_DERIVED_STATE=YES python scripts/project_state_snapshot.py --write
```

That command updates derived recovery surfaces only. It grants no authority to mutate Canonical, Sources, Change Ledger, Monitor, Live or Analysis governed populations.

## Recovery order

For continuation after a thread, branch or deployment interruption:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`;
2. current `main` commit and intervening PRs;
3. governed Canonical / Source / Change Ledger / Monitor / Live / Analysis files;
4. `data/status/current_state.json` and the CI-validated current-state blocks;
5. latest relevant pressure / transaction audits;
6. `OPEC_QUARANTINE.md` whenever OPEC is implicated.

Do not reconstruct operational truth from conversation history or stale prose when governed files can be checked directly.
