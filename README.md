# WORLD SIGNALS

WORLD SIGNALS is a platform-independent global political-economic intelligence system for tracking scheduled events, authoritative-source changes, current developments and structured analytical interpretation across economics, monetary and fiscal policy, politics, elections, geopolitics, institutions, trade, sanctions, markets, commodities, energy, climate, physical risk, health/biosecurity, technology and critical infrastructure.

**Live read-only interface:** https://musicofscience.github.io/world-signals/

`WORLD_SIGNALS_PROJECT_CHARTER.md` is the authoritative architectural and methodological specification. Governed registries/contracts remain operational truth. `data/status/current_state.json`, the current-state block below and the matching blocks in `PROJECT_STATUS.md` / `ROADMAP.md` are mechanically derived recovery surfaces and are checked by CI.

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

## Layer contract

```text
CANONICAL REGISTRY
      |
      +--> Calendar / Pages projections
      |
      v
SOURCE / CHANGE MONITOR
      |
      v
LIVE INTELLIGENCE
      +--> existing reviewed Analysis bridge
      |
      +--> SIGNALS (contract only; production population closed)
               |
               +--> future Relationships / Risks / Scenarios / Forecasts
```

The layers remain deliberately distinct:

1. **Canonical Registry** — what the event is: stable identities, lifecycle, certainty, timing and provenance.
2. **Calendar** — rebuildable human-facing projection from Canonical.
3. **Source / Change Monitor** — source health, authoritative change detection and review candidates; no automatic Canonical mutation.
4. **Live Intelligence** — evidence-backed factual observations around scheduled and unscheduled developments; no causal interpretation.
5. **Signals** — reviewed analytical patterns over immutable observations, with explicit uncertainty, corroboration and transmission hypotheses.
6. **Analysis** — expectations, surprise, market response, relationships, alternatives, uncertainty and second-order effects.

The reviewed Signal contract adds an analytical interface over Live
Intelligence. It is deliberately separate from factual observations and from
the existing Analysis packets: it may record a reviewed pattern or change, but
it may not rewrite observations, assert a causal chain, become a forecast or
populate itself automatically. The current Signal dataset is an executable
zero-population contract with focused synthetic tests only; its public
projection is closed.

The production validator rejects every populated Signal dataset. Proposed
record histories are tested separately with `validate_signal_history`; that
read-only function grants no storage or publication permission. See the
Signal contract section in `ARCHITECTURE.md` for evidence lineage, review,
history and expiry semantics and their limits.

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

## Source and monitoring governance

Source competence and automation permission are independent questions. A source may be authoritative for Canonical provenance while remaining unsuitable or unauthorised for unattended monitoring. Machine-only monitor identities may therefore be separate from Canonical provenance identities.

Configured Monitor routes are governed in `data/monitor/expectations.json`. Route presence does not grant lifecycle, certainty, schedule, clock, Canonical-write, Live-promotion or Analysis-promotion authority unless an explicit reviewed contract says so. Source failure, absence and parser failure remain source-health evidence rather than event-state evidence.

The NOAA/NHC Atlantic-season route was validated as a bounded pilot in CF and activated into scheduled Monitor expectations in PR #117 after a fresh source, rights, endpoint, scope and runtime review. It remains limited to exactly two existing Atlantic hurricane-season Canonical occurrences: NHC climatology is the season-definition semantic authority, Atlantic outlook RSS is source-health corroboration only, and neither source grants automatic lifecycle, schedule, certainty, completion, Canonical-write, Live-promotion or Analysis-promotion authority.

## Live Intelligence

The controlled internal Live layer currently exercises several distinct contracts rather than a general news feed: unscheduled physical shock, evolving health state, scheduled economic outcome, geopolitical development, institutional development and reviewed pre-event Canonical context.

Canonical linking is optional. Unscheduled real-world developments do not acquire invented Canonical identities merely to make the graph denser. Event time, source publication time, state-as-of time and WORLD SIGNALS observation time remain separate concepts.

Automatic ingestion, automatic story clustering, public observation projection, automatic Canonical commit and Calendar writes remain closed.

## Analysis

Analysis is post-event and anchored to existing completed Canonical occurrences. Live observations may be selected only through reviewed immutable `observation_id` relationships under the bridge contract; Live evidence is not transitively promoted into Analysis evidence.

Revision lineage is immutable: a later analytical judgement is a new Analysis snapshot linked to its parent, not an in-place rewrite. Automatic latest-head selection and public revision-head collapse remain prohibited.

## Cross-domain risk overlay

The dashboard includes a derived, read-only risk lens over existing Canonical records. It keeps intrinsic importance, expected market sensitivity, geopolitical sensitivity and transmission channels as separate dimensions, and maps signals non-exclusively across geopolitics, trade, energy, macro/monetary, financial/sovereign, health/biosecurity, climate/physical, technology/infrastructure and food/agriculture domains.

Calendar-week convergence windows show signal density only. They are not probability estimates, severity rankings, causal claims or authority to create or modify events. The overlay does not consume private Live Intelligence or infer Analysis conclusions. Existing Canonical OPEC records may appear mechanically like any other governed event, but the quarantined OPEC provenance transaction remains dormant and unchanged.

## Time and uncertainty

Canonical event time preserves source-native IANA timezone and UTC time when those exist. Australia/Melbourne is a home/reference display context, never canonical storage time. Civil dates, native month windows, recurring rules, provisional timing and unresolved timing remain at their supported precision rather than being promoted to synthetic timestamps.

Intrinsic importance, expected market sensitivity and observed market response remain separate. Analysis must distinguish what happened, what was expected, what surprised, what moved, plausible connections, noise, alternative explanations and second-order effects without post-hoc causal storytelling.

## OPEC quarantine

`OPEC_QUARANTINE.md` and closed/unmerged PR #113 preserve the failed CE provenance transaction as historical evidence. Normal work must not reopen, merge, cherry-pick, rebase, materialise or use that branch as a base. Any future OPEC work starts from then-current `main` under a fresh bounded design.

## Run locally

```bash
python scripts/validate_registry.py
python scripts/validate_live_intelligence.py
python scripts/validate_signals.py
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
