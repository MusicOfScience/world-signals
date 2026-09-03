# WORLD SIGNALS — executable thin slice v0.1

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

Open `http://localhost:8000`.

## Monitor dry-run

```bash
python scripts/run_monitor_dry.py
```

This compares a controlled source assertion with a canonical occurrence and writes a **review candidate** when a difference exists. It never edits `data/canonical/registry.json`.

## GitHub

- `ci.yml`: validates registry invariants and tests on pushes/PRs.
- `pages.yml`: builds and deploys the static UX to GitHub Pages.
- `monitor-dry-run.yml`: manually executes the monitor harness and uploads review candidates as a workflow artifact.

Live source adapters are intentionally a later step, added one source family at a time after endpoint/parser and rights validation.
