# WORLD SIGNALS — EIA WPSR monitor expansion AS research v0.1

**Checkpoint:** exact post-#73 `main` `4b25bb452f3def253cf86254e5ad6abdbe8b9f13`
**Reviewed:** 2026-09-06
**Target source:** `WSSRC-COM-003` — U.S. Energy Information Administration Weekly Petroleum Status Report
**Target series:** `WSER-COM-EIA-WPSR`
**Canonical mutation authorised:** **NO**
**Automatic canonical commit:** **OFF**
**Google Calendar writes:** **OFF**

## Selection rationale

The post-AR pressure audit did not treat monitor geography/category gaps as quotas. AS selects EIA WPSR because it tests a materially different monitor contract:

- `Cross-regional / Global` rather than another Europe route;
- `ENERGY_COMMODITIES` rather than another macro release or legal-rule route;
- an authoritative recurring schedule with explicit holiday exceptions;
- sixteen current canonical dependencies;
- an existing source-governance record already classified `PILOT_VALIDATED_NO_AUTO_COMMIT`;
- a known publication-index lag incident that forces a clean separation between **schedule monitoring** and **publication-completion evidence**.

The route is therefore useful because of marginal operational-contract diversity, not because an empty map cell needs filling.

## Primary official research

### WPSR release schedule

Primary source:

- <https://www.eia.gov/petroleum/supply/weekly/schedule.php>

EIA currently states that `wpsrsummary.pdf`, `overview.pdf`, and Tables 1–14 in CSV/XLS are released **after 10:30 a.m. Eastern time on Wednesday**. Other PDF/HTML files follow after 1:00 p.m. Eastern. The page also publishes explicit holiday exceptions.

The live AS parser observed the current normalized schedule as:

- standard release day: `Wednesday`
- standard release time: `10:30`
- time semantics: `AFTER`
- source timezone: `America/New_York`
- holiday exception rows: `14`
- normalized semantic hash: `8f972e877fdd56dd836f6a0cc7bc0abea73c21bfd01dd8bbc3b784ea7eacec87`

Current 2026 future exceptions material to the canonical series include:

- week ending 2026-09-04 → release 2026-09-10, Thursday, 12:00 ET, Labor Day;
- week ending 2026-10-09 → release 2026-10-15, Thursday, 12:00 ET, Columbus Day;
- week ending 2026-11-06 → release 2026-11-12, Thursday, 12:00 ET, Veterans Day.

The canonical WPSR occurrences already reflect these exception dates/times. AS does not rewrite them.

### Copyright/reuse

Primary source:

- <https://www.eia.gov/about/copyrights_reuse.php>

EIA states that U.S. Government publications on its site are public domain and that its data, files, databases, reports, graphs, charts and other information products may be used/distributed, subject to protected third-party material and attribution guidance.

This supports factual/provenance reuse. It does not by itself mean every EIA webpage is an unrestricted or operationally appropriate polling interface. AS therefore remains route-specific.

### WPSR dissemination redesign

Primary source:

- <https://www.eia.gov/petroleum/supply/weekly/wpsr_notice_06102026.php>

EIA's 1 June 2026 notice says it is considering changes to WPSR data dissemination and is testing consolidated HTML, CSV and JSON formats. The underlying data and methodology are not changing, but the new formats are explicitly still test surfaces.

AS therefore **does not** make a provisional JSON or CSV test format a production dependency. A later route migration can be separately reviewed if EIA adopts a stable machine-readable interface.

## Existing source-governance state

At source registry `v1.78`, `WSSRC-COM-003` already records:

- `monitoring_readiness_status = PILOT_VALIDATED_NO_AUTO_COMMIT`;
- `monitoring_activation_status = PILOT_ONLY_NO_CANONICAL_AUTO_COMMIT`;
- `canonical_dependency_count = 16`;
- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`;
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`;
- `verification_mode = AUTOMATED_PILOT`;
- preferred monitor endpoint = WPSR schedule HTML rule table;
- current-report landing page = corroboration only;
- source-surface relationship = `INDEX_LAGS_DATA_PRODUCT`;
- completion hierarchy gives underlying official data products priority over the publication index and schedule rule page.

The record also preserves the September 2026 incident where the publication index lagged the underlying official data product. AS treats that incident as architectural evidence: the schedule page is not a completion oracle.

## Live runner research

### First probe — intentionally naive landing-page parser

GitHub Actions run `34009035475` proved the exact post-#73 base and fetched the official WPSR landing page successfully (`HTTP 200`). A naive regex expecting the release-date label and value to be adjacent failed because the page inserts markup between them.

Classification: **parser-design failure, not endpoint failure**.

This failure was useful. It prevented AS from conflating an easily fetched publication index with a robust completion contract.

### Second probe — bounded schedule parser

GitHub Actions run `34009176451`, job `101421838658`, passed:

- exact post-#73 base/live-main proof;
- exact source/canonical dependency inspection;
- live official schedule-page fetch;
- semantic parser;
- 2026 Labor Day exception check;
- four fail-closed adapter regressions.

Live snapshot:

- URL: `https://www.eia.gov/petroleum/supply/weekly/schedule.php`
- HTTP status: `200`
- content type: `text/html; charset=UTF-8`
- response bytes: `52283`
- transport body SHA-256: `60d239a4943a2284b48c008510385b57953ac3fd2584b8453459189672c4fa91`
- normalized semantic schedule SHA-256: `8f972e877fdd56dd836f6a0cc7bc0abea73c21bfd01dd8bbc3b784ea7eacec87`

Markup-only differences do not change the semantic hash.

## AS monitor contract

Adapter ID: `EIA_WPSR_SCHEDULE`

Role: **publication schedule rule and holiday-exception sentinel**.

The adapter may:

- fetch the authoritative schedule page;
- parse the standard weekday/time rule;
- preserve the source's `AFTER` timing semantics;
- parse the full published holiday-exception table;
- compare normalized semantic state with the reviewed baseline;
- emit a review-only candidate when the semantic schedule changes;
- report source health.

The adapter may **not**:

- mark an occurrence completed;
- infer completion from elapsed schedule time;
- infer cancellation from absence;
- treat the publication index as authoritative completion evidence by itself;
- rewrite canonical timing automatically;
- use the EIA test JSON/CSV formats as a production dependency;
- auto-commit Canonical or write Google Calendar.

## Source-governance decision

AS clears **only the reviewed WPSR schedule-page sentinel route** for bounded read-only polling.

It does not grant generic automated-retrieval permission across eia.gov.

Post-AS source language should therefore preserve the narrower distinction:

- factual provenance: cleared;
- WPSR schedule sentinel endpoint: reviewed/cleared for read-only pilot monitoring;
- publication completion: separate evidence hierarchy remains in force;
- automatic canonical commit: prohibited;
- future/test WPSR JSON/CSV surfaces: not production dependencies.

## Expected monitor-coverage effect

If promoted, monitor expectations move from 7 to 8 adapters and add the 16 WPSR canonical occurrences explicitly.

Expected read-only monitor coverage becomes:

- adapters: 8
- unique monitor sources: 7
- explicitly scoped occurrences: 43
- scoped series: 11
- scoped institutions: 6
- scoped regions: 4
- scoped categories: 6

The new region is `Cross-regional / Global`; the new category is `ENERGY_COMMODITIES`.

These counts remain descriptive, not completeness targets.
