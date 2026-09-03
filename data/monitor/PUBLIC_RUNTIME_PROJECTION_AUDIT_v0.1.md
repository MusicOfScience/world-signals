# WORLD SIGNALS — Public Runtime Projection Audit v0.1

**Reference date:** 2026-09-04  
**Status:** IMPLEMENTED / DEPLOYED READ-ONLY  
**Canonical checkpoint:** v0.20 / 669 occurrences  
**Source registry:** v1.51 / 222 sources  
**Monitor expectations:** v0.6  
**Monitor operations policy:** v0.1  
**Public runtime projection contract:** v0.1

## Purpose

The GitHub Pages Operations layer may surface dated monitor evidence without turning a static browser projection into a claim of current source health and without publishing raw authoritative-source payloads, parser errors or review evidence that belongs in retained Actions artefacts.

The governing distinction is:

`CONFIGURED ROUTE ≠ RECORDED RUN ≠ CURRENT SOURCE HEALTH ≠ CANONICAL EVENT STATE`

## Browser-safe static Operations projection

`src/world_signals/operations.py` projects:

- current canonical/source/monitor versions;
- configured monitor routes;
- source-governance classifications;
- timestamps already committed in monitor baselines/configuration;
- reviewed canonical change count;
- canonical auto-commit gate state.

Older source records lacking the modern provenance/automation governance fields are represented as `NOT_RECORDED_IN_REGISTRY`. Missing governance is not treated as permission.

The full 222-source governance inventory is searchable in the Operations UX.

## Dated monitor runtime projection

The public runtime path is:

`retained GitHub Actions monitor artefact → in-memory fetch → strict sanitizer → public runtime.json → read-only Operations UX`

Raw Actions artefacts are not copied into Pages.

`data/monitor/public_runtime_projection_contract.json` defines the allowed public fields and expressly prohibits raw:

- source snapshots;
- fetch/parser error text;
- observations;
- rule/topology payloads;
- candidate old/new values;
- source assertions;
- raw source bodies/rows.

`src/world_signals/runtime_projection.py` validates and sanitizes the monitor report, manifest and candidate objects. A retained artefact that violates the contract fails the Pages build rather than silently falling back to an older attractive-looking run.

## Latest-run rule

The Pages projection follows the **latest completed monitor run**, not merely the latest successful run.

This prevents a newer failed monitor from being hidden behind an older green observation. If the latest completed run is unsuccessful or its artefact cannot be safely consumed, the UX publishes an explicit runtime-evidence availability state rather than claiming health.

The relevant unavailable states distinguish, among other cases:

- Actions run index unavailable;
- no completed monitor run;
- latest monitor run unsuccessful;
- latest artefact index unavailable;
- successful run with no retained artefact;
- retained artefact download unavailable.

These are evidence-delivery/environment states, not source-health or event-state assertions.

## Secure artefact download correction

Initial Pages execution found monitor runs but reported no retained artefact. A temporary read-only diagnostic proved that recent runs did have unexpired retained artefacts.

The root cause was the GitHub Actions download boundary:

1. the authenticated GitHub API archive endpoint returns HTTP 302;
2. the redirect target is a signed cross-host storage URL;
3. repository Authorization must not be forwarded to that signed storage request.

`fetch_latest_monitor_snapshot.py` now handles the redirect explicitly: repository credentials are used only for the GitHub API request; the signed storage URL is fetched without the GitHub Authorization header.

The temporary diagnostic workflow was removed after this was proved.

## Verified retained run

The first successfully published runtime snapshot came from:

- live-monitor run number: **47**;
- GitHub run ID: `33754900613`;
- observation time: `2026-09-03T12:23:29.227611+00:00`;
- final monitor status: `NO_CHANGE`;
- healthy adapters: **6**;
- degraded adapters: **0**;
- expected adapters observed: **6 / 6**;
- review candidates: **0**;
- canonical SHA guard: unchanged;
- automatic canonical commit: false;
- Google Calendar write: false.

The run used canonical v0.17 and source registry v1.48. The current site is v0.20 / source v1.51, so the Operations UX correctly labels the retained run `STALE_RELATIVE_TO_CURRENT_SITE` rather than presenting it as current configuration evidence.

## Automatic refresh

`.github/workflows/pages.yml` now rebuilds on:

- pushes to `main`;
- manual dispatch;
- completion of `Monitor WORLD SIGNALS live sources`.

Therefore a new completed monitor run automatically refreshes the dated runtime projection. A failed monitor completion also triggers the rebuild, allowing the Operations layer to expose that the latest run did not produce publishable green runtime evidence.

Pages permissions remain bounded:

- `contents: read`;
- `actions: read`;
- `pages: write`;
- `id-token: write` for Pages deployment.

There is no canonical repository write authority in the Pages workflow.

## UX boundaries

The Operations view now separates:

1. **latest retained run** — dated sanitised observation only;
2. **source-health states from that run** — historical at the stated timestamp;
3. **run-generated review-candidate metadata** — not canonical and not a persistent queue;
4. **source-governance inventory** — registry classification/current configuration;
5. **configured monitor routes** — capability/configuration, not runtime health;
6. **auto-commit gate** — remains CLOSED.

The browser has no POST/PUT/DELETE/canonical write path.

## Tests

Regression coverage includes:

- static Operations projection matches canonical/source checkpoint;
- static projection never claims runtime health;
- missing governance remains `NOT_RECORDED_IN_REGISTRY`;
- Fiji source remains manual/rights-held and is not a live monitor route;
- public runtime sanitizer removes prohibited evidence payloads;
- stale configuration is visible;
- canonical guard failure cannot be published as a green runtime snapshot;
- every candidate must explicitly prohibit automatic commit;
- unavailable runtime projection preserves safety boundaries;
- Operations UX has no write path;
- latest retained run semantics are distinct from persistent review state.

## Next architectural problem

A run-generated candidate snapshot is not a durable review queue. The next layer must define stable candidate identity and lifecycle across multiple immutable monitor artefacts without turning the artefact store into a second canonical database.

Proposed direction:

`immutable run artefacts → deterministic candidate identity/reducer → persistent review-state projection → human-reviewed transaction → canonical change ledger`

That reducer remains read-only until its identity, supersession, recurrence, resolution and provenance semantics are audited.
