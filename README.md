# WORLD SIGNALS — executable thin slice v0.2

This repository is the first executable implementation of the WORLD SIGNALS architecture.

## Layer contract

```text
data/canonical/registry.json     <-- CANONICAL REGISTRY (authoritative input)
             |
             +--> scripts/build_site.py --> docs/ --> GitHub Pages web UX
             |
             +--> monitor engine --> review_candidates/ (NO automatic canonical commit)
             |
             +--> future live-intelligence + analysis layers
```

The browser is **not** the database. GitHub Pages is **not** the canonical registry.

## Current web UX

The Pages site now opens on a **read-only month calendar** backed by the canonical registry, with an **Event index** as the second view.

- exact-date events are placed on calendar days;
- timed events use the browser/device timezone when a canonical UTC timestamp is available, while the native source timezone remains visible;
- expected windows and month-precision events are rendered separately rather than being pinned to an invented day;
- filters apply across calendar and index views;
- clicking an event opens its stable identity, certainty, lifecycle, provenance and monitoring-route details.

This is a projection layer only. It cannot write to the canonical registry.

## Current safety boundary

- Canonical records: 649 at the bundled checkpoint.
- Site: read-only.
- Monitor: dry-run/fixture-capable, review candidates only.
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

## Monitor dry-run

```bash
python scripts/run_monitor_dry.py
```

This compares a controlled source assertion with a canonical occurrence and writes a **review candidate** when a difference exists. It never edits `data/canonical/registry.json`.

## GitHub

- `ci.yml`: validates registry invariants and tests on pushes/PRs.
- `pages.yml`: builds and deploys the static UX to GitHub Pages.
- `monitor-dry-run.yml`: manually executes the monitor harness and uploads review candidates as a workflow artifact.

Live source adapters are added one source family at a time after endpoint/parser and rights validation. The next executable tranche is adapter promotion and review-candidate generation; canonical mutation remains a separate, closed gate.
