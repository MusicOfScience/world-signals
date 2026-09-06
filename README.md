# WORLD SIGNALS

WORLD SIGNALS is a platform-independent political-economic intelligence system for tracking scheduled events, authoritative-source changes, current developments and their interactions across economics, politics, geopolitics, markets, trade, commodities, climate, health and institutions.

**Live read-only interface:** https://musicofscience.github.io/world-signals/

The repository is the operational implementation. `WORLD_SIGNALS_PROJECT_CHARTER.md` is the authoritative architectural specification; `PROJECT_STATUS.md` is the durable recovery checkpoint. Registry and contract files remain the final source of operational truth.

## Current checkpoint

Post-#76 / AV foundation checkpoint:

- Canonical Registry: **v0.38 — 688 occurrences**
- Canonical schema: **v0.52**
- Source Registry: **v1.80 — 243 sources**
- reviewed Change Ledger: **v0.24 — 59 entries**
- Source/Change Monitor expectations: **v0.10 — 8 configured adapters**
- Monitor operations policy: **v0.1**
- Live Intelligence: **v0.1 foundation — 0 observations / 0 evidence; population gate closed**
- Analysis schema: **v0.4**
- Analysis: **v0.16 — 20 reviews / 91 evidence rows / 18 reviewed event types**
- production `EXACT_TIMESTAMP_SERIES`: **0**
- Automatic canonical commits: **OFF / gate closed**
- Google Calendar writes: **OFF**

These numbers are a checkpoint, not a substitute for the governed files. After later merges, verify the registries/contracts on `main` before relying on prose documentation.

## Layer contract

```text
AUTHORITATIVE SOURCES
        |
        v
Source / Change Monitor
FETCH -> SNAPSHOT -> PARSE -> ASSERT -> MATCH -> DIFF
        |
        +--> source health / review candidates
        |
        v
reviewed canonical transaction when authorised
        |
        v
CANONICAL REGISTRY ------------------> Calendar / Pages projections
        |
        +-----------------------------> Live Intelligence links/context

current developments / observations --> LIVE INTELLIGENCE --> ANALYSIS
                                      factual layer          interpretation
```

The layers are deliberately separate:

1. **Canonical Registry** — authoritative event identities, lifecycle and timing.
2. **Calendar** — disposable human-facing projection from Canonical.
3. **Source / Change Monitor** — authoritative-source verification, source health and review candidates.
4. **Live Intelligence** — factual current-development observations; AV v0.1 is foundation-only and intentionally empty.
5. **Analysis** — expectations, surprise, market response, connections, alternatives, second-order effects and falsifiers.

The browser is **not** the database. GitHub Pages is **not** the canonical registry. Source health is **not** event state. Live Intelligence is **not** Analysis. A source failure or absence cannot itself cancel, complete or reschedule an event, and it cannot itself create a Live Intelligence fact.

## Web UX

The Pages application is a read-only projection built from `web/` and repository data by `.github/workflows/pages.yml`. GitHub Actions is the sole Pages publishing path; generated `docs/` output is build-time material and is not tracked.

Current visible layers include:

- **Calendar** — exact-date events on civil days; timed events display in device timezone when canonical UTC exists while preserving native source timezone; uncertain/month-native windows are not pinned to invented days.
- **Event index** — searchable/filterable canonical event inventory.
- **Monitor routes** — configured read-only Source/Change Monitor routes, explicitly not current runtime health.
- **Operations** — source governance, dated retained monitor evidence, candidate evidence and retained review state.
- **Biosecurity system map** — noncanonical cross-domain coverage overlay inside Operations.
- **Change history** — reviewed canonical ledger showing what changed and why.
- **Analysis** — reviewed post-event analytical specimens linked to canonical occurrences.

AV also emits `docs/data/live_intelligence.json`, but **only as foundation metadata**. It contains no public observations and makes no claim to be a current-news or runtime intelligence feed.

## Monitoring and review state

The scheduled Source/Change Monitor currently has **8 heterogeneous configured adapters**:

- RBA Financial Stability Review RSS;
- Colombia SUIN / Socrata Decree 111/1996 sentinel;
- EU Cyber Resilience Act Article 71 / Cellar topology sentinel;
- EU CBAM verifier-report milestone;
- EU CBAM certificate-sale milestone;
- EU CBAM annual declaration / surrender deadline;
- ONS release-calendar RSS;
- EIA Weekly Petroleum Status Report schedule.

These routes are review-only. They can fetch, parse, compare and generate evidence/review candidates under route-specific permissions; they cannot mutate canonical state automatically.

Review-candidate identity is separate from monitor-run identity. Stable `WSRV-*` propositions can aggregate repeated equivalent observations while preserving materially different proposals as siblings. Retained Actions evidence is bounded by its retention horizon; durable checkpoint architecture remains noncanonical.

## Live Intelligence foundation

AV v0.1 makes the Charter's missing Live Intelligence layer executable without populating it prematurely.

The foundation:

- allows genuinely unscheduled observations to exist without fabricated canonical events;
- allows optional links to existing canonical occurrences;
- separates observation time, source-publication time and real-world event time;
- preserves corrections/revisions rather than silently rewriting history;
- prohibits causal interpretation and market-move attribution;
- prohibits Live evidence from altering canonical provenance or resolving missing canonical time;
- prohibits retrospective migration of Analysis evidence merely to make the new layer appear populated;
- deliberately rejects production observation/evidence population until a later pressure-audited specimen opens that gate.

## Analysis state

Analysis currently contains **20 reviewed post-event specimens across 18 event types**, with **91 analytical evidence rows**. The sole completed/unreviewed canonical occurrence at the post-AU checkpoint is `WSO-MAC-B-0041` (Japan Family Income and Expenditure Survey, July 2026). It is a valid future specimen, not a backlog obligation.

## Time and uncertainty

Canonical event time preserves the source's native IANA timezone and UTC timestamp where available. Australia/Melbourne is a default home/reference display context, never canonical storage time. The schema also supports source-native date/month windows and civil-date objects without manufacturing false clock precision.

## Run locally

```bash
python scripts/validate_registry.py
python scripts/validate_live_intelligence.py
python scripts/validate_analysis.py
python -m unittest discover -s tests -v
python scripts/build_site.py
```

`python scripts/build_site.py` generates `docs/` locally. The directory is intentionally ignored; Pages builds a fresh projection in GitHub Actions.

## Recovery

For continuation after a chat/thread interruption, read in this order:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. the current override at the top of `PROJECT_STATUS.md`
3. Canonical / Source / Monitor / Live Intelligence / Analysis governed files referenced there
4. latest relevant pressure audits and transaction audits
5. current `main` commit and Actions runs

Do not reconstruct operational truth from prose checkpoints or conversation history alone when the governed files can be checked directly.
