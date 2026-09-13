# WORLD SIGNALS — local operations runtime CS plan v0.1

**Status:** LOCAL READ-ONLY OPERATIONS SPINE / NO AUTOMATIC GOVERNED WRITE

**Reference date:** 2026-09-13 Australia/Melbourne

**Exact base:** `92d471b7c880c286d4bdeb4f6efa3f3479d9a1a3`

## Purpose

Replace the unavailable GitHub Actions execution shell with a platform-local operating path while preserving every layer boundary. The local runner validates governed inputs, executes all 26 configured source monitors, archives private run evidence outside Git, produces sanitized dashboard projections, rebuilds the static site and optionally serves it on loopback.

## Safety boundary

- Canonical, Sources, Change Ledger, Monitor contracts, Live Intelligence, Analysis and OPEC quarantine are hashed before and after every run.
- The live monitor retains its existing Canonical byte guard and cannot commit automatically.
- Local run history lives under ignored `.world-signals-runtime/`; raw monitor evidence is never projected directly into the browser.
- Browser output receives only the existing sanitized runtime and review-candidate fields.
- Pre-migration GitHub Actions evidence is not silently inferred as complete local history.
- Source failure remains source-health evidence, never event cancellation, completion or rescheduling.
- Google Calendar writes, automatic Canonical writes, automatic Live/Analysis promotion and public internal-Live projection remain off.

## Initial local diagnostic

The pre-implementation diagnostic on merged main completed successfully with all 26 configured adapters accounted for, 24 healthy and two degraded. Canonical remained byte-identical. Four candidates were generated for human review. The degraded routes were New Zealand election RSS content-type drift and an INDEC September CPI identity mismatch. Those are operational evidence for later bounded repairs, not permission for automatic event mutation.

## Operator entry point

```bash
/opt/homebrew/bin/python3.13 scripts/run_local_operations.py
```

Add `--serve` to host the freshly built dashboard on `127.0.0.1:8765`. The command requires a clean tracked worktree, prevents concurrent runs, uses a local monotonic run namespace, preserves private history, emits sanitized projections and fails closed if protected files change.

## Deferred work

Automated background scheduling and the proposed cross-domain risk overlay are separate tranches. Scheduling must not be installed until this local execution path has passed exact-head review. Risk overlay design must consume governed/read-only signals without collapsing Canonical, Monitor, Live Intelligence and Analysis into a single score.
