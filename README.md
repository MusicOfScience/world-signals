# WORLD SIGNALS

WORLD SIGNALS is a platform-independent political-economic intelligence system for tracking scheduled events, authoritative-source changes, review candidates and their interactions across economics, politics, geopolitics, markets, trade, commodities, climate and institutions.

**Live read-only interface:** https://musicofscience.github.io/world-signals/

The repository is the operational implementation. `WORLD_SIGNALS_PROJECT_CHARTER.md` is the authoritative architectural specification; `PROJECT_STATUS.md` is the durable recovery checkpoint.

## Current checkpoint

- Canonical registry: **v0.20 — 669 occurrences**
- Source registry: **v1.51 — 222 sources**
- Canonical schema: **v0.51**
- Live monitor expectations: **v0.6**
- Monitor operations policy: **v0.1**
- Automatic canonical commits: **OFF / gate closed**
- Google Calendar writes: **OFF**

These numbers are a checkpoint, not a substitute for the registry itself. When this README and `PROJECT_STATUS.md` disagree, recover from the latter and then verify the canonical files.

## Layer contract

```text
AUTHORITATIVE SOURCES
        |
        v
read-only source adapters
FETCH -> SNAPSHOT -> PARSE -> ASSERT
        |
        v
MATCH -> DIFF -> REVIEW CANDIDATE
        |
        v
REVIEW / REVIEW STATE / CHANGE LEDGER
        |
        |  no automatic canonical commit
        v
data/canonical/registry.json      <-- CANONICAL REGISTRY
        |
        +--> scripts/build_site.py --> GitHub Pages web UX
        +--> future calendar exports
        +--> Live Intelligence
        +--> Analysis
```

The browser is **not** the database. GitHub Pages is **not** the canonical registry. Source health is **not** event state. A missing or failed source observation cannot itself cancel, complete or reschedule an event.

## Web UX

The Pages application is a read-only projection built from `web/` and repository data by `.github/workflows/pages.yml`. GitHub Actions is the sole Pages publishing path; generated `docs/` output is build-time material and is not tracked.

Current visible layers include:

- **Calendar** — exact-date events on civil days; timed events display in device timezone when canonical UTC exists while preserving native source timezone; uncertain/month-native windows are not pinned to invented days.
- **Event index** — searchable/filterable canonical event inventory.
- **Monitor routes** — configured read-only source/change routes, explicitly not current runtime health.
- **Operations** — source governance, dated retained monitor evidence, single-run candidate evidence and retained review state.
- **Change history** — reviewed canonical ledger showing what changed and why.

The Operations view deliberately distinguishes a dated monitor observation from current health, and retained review state from a permanent queue.

## Monitoring and review state

The scheduled live monitor currently exercises six heterogeneous read-only routes, including RBA, Colombia SUIN, EU Cyber Resilience Act and EU CBAM milestones. It can fetch, parse, compare and generate review candidates; it cannot mutate canonical state.

Review-candidate identity is separate from monitor-run identity. Stable `WSRV-*` review propositions can aggregate repeated equivalent observations while preserving materially different proposals as siblings. Retained Actions evidence is explicitly bounded by its retention horizon; durable checkpoint architecture exists separately and remains noncanonical.

## Time and uncertainty

Canonical event time preserves the source's native IANA timezone and UTC timestamp where available. Australia/Melbourne is a default reference/display context, never canonical storage time. The schema also supports source-native date/month windows without manufacturing false civil-day precision.

## Run locally

```bash
python scripts/validate_registry.py
python -m unittest discover -s tests -v
python scripts/build_site.py
```

`python scripts/build_site.py` generates `docs/` locally. The directory is intentionally ignored; Pages builds a fresh projection in GitHub Actions.

## Recovery

For continuation after a chat/thread interruption, read in this order:

1. `WORLD_SIGNALS_PROJECT_CHARTER.md`
2. `PROJECT_STATUS.md`
3. canonical/source/monitor registries and contracts referenced there
4. latest relevant audits
5. current `main` commits and Actions runs

Do not reconstruct operational truth from this README or from conversation history alone.
