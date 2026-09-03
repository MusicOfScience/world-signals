# WORLD SIGNALS — executable thin slice v0.4

This repository is the executable implementation of the WORLD SIGNALS architecture.

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
        |  no automatic commit
        v
data/canonical/registry.json     <-- CANONICAL REGISTRY
        |
        +--> scripts/build_site.py --> docs/ --> GitHub Pages web UX
        |
        +--> future calendar exports
        |
        +--> future live-intelligence + analysis layers
```

The browser is **not** the database. GitHub Pages is **not** the canonical registry. Source health is **not** event state.

## Current web UX

The Pages site opens on a **read-only month calendar** backed by the canonical registry, with an **Event index** and **Monitor routes** view.

- exact-date events are placed on calendar days;
- timed events use the browser/device timezone when a canonical UTC timestamp is available, while the native source timezone remains visible;
- expected windows and month-precision events are rendered separately rather than being pinned to an invented day;
- filters apply across calendar and index views;
- clicking an event opens its stable identity, certainty, lifecycle, provenance and monitoring-route details;
- Monitor routes describes what is configured to run and what each adapter is allowed to infer. It deliberately does **not** pretend that a static Pages build contains current runtime health.

This is a projection layer only. It cannot write to the canonical registry.

## Operational live monitor

`live-monitor.yml` runs a read-only official-source monitor daily and can also be started manually. It currently exercises three deliberately heterogeneous routes:

1. **Reserve Bank of Australia — Financial Stability Review RSS/RDF**
   - positive publication evidence can generate a completion/date review candidate;
   - absence from the feed cannot cancel or complete an occurrence.

2. **Colombia SUIN / Datos Abiertos — Decree 111 of 1996 sentinel**
   - the Socrata API watches the typed legal instrument (`DECRETO` + number + year) for presence/version fields;
   - a change generates a legal-input review candidate;
   - the inventory cannot directly alter the canonical budget deadline: operative clause-level SUIN verification remains required.

3. **European Union Publications Office Cellar — Cyber Resilience Act Article 71**
   - CELEX `32024R2847` is retrieved through the credential-free Cellar dissemination route as English XHTML;
   - the monitor extracts Article 71 application dates semantically rather than treating the whole-document hash as the legal rule;
   - an amended application date generates a `LEGAL_RULE_CHANGED` review candidate against the same stable CRA occurrences;
   - transport or parser failure affects source health only and cannot alter an event.

Every run hashes `data/canonical/registry.json` before and after. A changed hash fails the monitor. The workflow token has `contents: read` only.

The first three-route operational run completed with **3 healthy routes, 0 degraded routes, 0 review candidates, `NO_CHANGE`, and an identical canonical SHA before/after**. Source Registry v1.46 records all three routes as pilot-validated, review-only monitors.

## Current safety boundary

- Canonical records: 649 at the bundled checkpoint.
- Calendar/site: read-only projection.
- Live monitor: official-source fetch/parse/compare, review candidates only.
- Source failure: source-health state only; no event mutation.
- Automatic canonical commits: prohibited.
- Google Calendar writes: prohibited.

## Run locally

```bash
python scripts/validate_registry.py
python -m unittest discover -s tests -v
python scripts/build_site.py
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000` **on the same computer that is running the server**. From another device, use that computer's reachable network address or the deployed GitHub Pages site.

## Monitor commands

Controlled fixture/dry-run comparison:

```bash
python scripts/run_monitor_dry.py
```

Live official-source review-only monitor:

```bash
python scripts/run_live_monitor.py
```

Neither command edits `data/canonical/registry.json`.

## GitHub workflows

- `ci.yml` — registry validation, regression tests and static-site build.
- `pages.yml` — validates, builds and deploys GitHub Pages.
- `monitor-dry-run.yml` — manual controlled monitor harness.
- `adapter-smoke.yml` — live transport/parser checks against official RBA, Colombia and EU Cellar routes.
- `live-monitor.yml` — scheduled read-only live monitor; uploads source-health report and review-candidate artefacts.

Live source adapters are promoted one source family at a time after rights, endpoint and parser validation. Automatic canonical mutation remains a separate closed gate: working software is not permission to remove review.
