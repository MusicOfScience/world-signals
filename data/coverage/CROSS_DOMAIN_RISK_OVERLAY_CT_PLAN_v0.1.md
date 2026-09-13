# WORLD SIGNALS — cross-domain risk overlay CT plan v0.1

**Status:** DERIVED READ-ONLY RISK LENS / NO GOVERNED POPULATION

**Reference date:** 2026-09-13 Australia/Melbourne

**Exact base:** `13c8cc4ab3154b932d5ee336f48da24646ea9107`

## Charter alignment

The project charter calls for a reliable political-economic context and early-warning system while requiring Canonical, Calendar, Monitor, Live Intelligence and Analysis to remain separate. It also requires event importance, expected market impact and observed market impact to remain distinct, and warns against post-hoc causal stories. CT implements a new browser lens consistent with those controls rather than creating a sixth governed truth store.

## Product purpose

Provide a usable cross-domain view of the existing Canonical horizon:

- preserve intrinsic importance, expected market sensitivity and geopolitical sensitivity as separate axes;
- expose already-governed transmission channels without treating them as realised effects;
- map events non-exclusively into nine risk domains without changing their Canonical primary categories;
- preserve expected-date, month-bounded and source-native windows without inventing a single event day;
- show calendar-week convergence only where at least two planned or active events from at least two Canonical categories have exact Gregorian start anchors;
- allow horizon, domain, region, geopolitical-sensitivity and text filtering in the static dashboard.

## Hard boundaries

- No scalar or composite risk score, probability, likelihood, severity estimate, forecast or causal status.
- No Canonical, Sources, Change Ledger, Monitor, Live Intelligence, Analysis or biosecurity-overlay mutation.
- No private Live Intelligence projection and no inferred Analysis conclusion.
- No event creation, admission, reprioritisation or lifecycle mutation.
- No automatic Git commit, merge or Google Calendar write.
- OPEC quarantine remains unchanged. Existing Canonical OPEC occurrences may flow through the generic mechanical projection; no OPEC-specific research, provenance repair, candidate selection or transaction machinery is activated.

## Production surface

`src/world_signals/risk_projection.py` creates and validates the browser-safe projection. `scripts/build_site.py` writes the derived `docs/data/risk_overlay.json`. `web/risk.js` and `web/risk.css` add a responsive read-only dashboard view. The local operating runner hashes `data/coverage/` before and after each cycle so the new layer cannot be mutated by monitoring.

## Validation target

The tranche must prove Canonical referential integrity and field fidelity, non-exclusive domain mapping, exact-date-only convergence, absence of scalar/causal output fields, browser read-only behaviour, build integration, responsive syntax, OPEC quarantine preservation, full repository regression safety and a clean exact-head diff.
