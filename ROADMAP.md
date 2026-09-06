# WORLD SIGNALS — code promotion roadmap

This roadmap is subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`. Stages are architectural capabilities, not a licence for bulk population.

## Stage 0 — research architecture and source governance — ACTIVE / MATURE

Implemented foundations include:

- canonical identity, lifecycle, certainty and time semantics;
- source registry and rights/automation separation;
- conflict and provenance rules;
- coverage audits and noncanonical analytical overlays;
- change history and review-candidate contracts;
- fail-closed validation and controlled transaction patterns.

Research remains continuous because future schedules, institutions, rights and endpoints change.

## Stage 1 — executable Canonical Registry and read-only web projection — DONE

The repository can:

- validate the canonical registry;
- enrich events from the source registry;
- build browser-safe projections;
- render Calendar, Event Index, Operations, Change History and Analysis views;
- deploy via GitHub Actions / Pages;
- preserve source-native and UTC timing without making Melbourne canonical.

Calendar/Pages remain disposable projections.

## Stage 2 — heterogeneous Source / Change Monitor, review-only — DONE / EXPANDING CAUTIOUSLY

Eight configured adapters currently exercise materially different source contracts:

- RBA FSR RSS/RDF;
- Colombia SUIN / Socrata legal sentinel;
- EU Cyber Resilience Act / Cellar;
- three EU CBAM legal-rule routes;
- ONS release-calendar RSS;
- EIA WPSR schedule.

Shared pattern:

`fetch -> snapshot -> parse -> assert -> match -> diff -> review candidate`

No adapter receives automatic canonical-write authority. Route presence does not erase source-specific rights, endpoint and parser gates.

## Stage 3 — scheduled monitoring and retained operational evidence — DONE

GitHub Actions executes the governed monitor cohort on a schedule under read-only repository permissions. Runtime source health, review candidates and retained review-state evidence remain distinct from Canonical state.

Source failure, parser failure and absence are never event cancellations/completions/reschedules.

## Stage 4 — controlled reviewed transactions — PARTIALLY IMPLEMENTED / GUARDED

WORLD SIGNALS already uses exact-prestate, fail-closed controlled transactions for reviewed tranches. These prove a safety pattern:

`reviewed proposal -> exact prestate -> controlled mutation -> validators -> full suite -> mutation audit -> reviewed PR`

A generic platform-independent candidate-to-canonical commit/rollback tool remains a future consolidation task. Existing tranche scripts do not constitute blanket commit authority.

Automatic canonical commit remains prohibited.

## Stage 5 — Analysis foundation and controlled sample — DONE / PAUSED FOR AUDIT

Analysis schema `v0.4` currently supports 20 reviewed post-event specimens, 91 analytical evidence rows and 18 reviewed event types.

The sample exercises macro data, monetary policy, institutions, elections, sovereign financing, physical-risk windows/outlooks, financial stability, climate governance, health governance and sanctions without treating review count as representativeness.

Further Analysis population is paused after AU because the remaining completed/unreviewed Japan macro release adds less immediate contract pressure than the missing Live Intelligence layer.

## Stage 6 — Live Intelligence foundation — AV

AV establishes `data/live_intelligence/` as an executable but intentionally empty layer.

Foundation capabilities:

- factual current-development observation identity;
- explicit verification state;
- evidence registry separate from canonical and analytical provenance;
- optional canonical links;
- unscheduled observations without fabricated canonical identities;
- separate observation time, publication time and event time;
- append-only revision/correction relationships;
- validation that rejects causal/analytical fields;
- metadata-only static projection;
- CI integration.

**AV v0.1 deliberately prohibits production observation/evidence population.**

## Stage 7 — first Live Intelligence specimen — NEXT AFTER AV MERGE

Run a fresh pressure audit after AV. Choose one real development because it stresses the contract, not because it is convenient or prominent.

Candidate stress classes include:

- unscheduled physical shock;
- health emergency;
- geopolitical/policy development;
- economic-data revision;
- factual market observation linked to a canonical occurrence.

The first specimen should test identity, revision, timing, provenance and rights semantics before the population gate is opened more broadly.

## Stage 8 — prospective Live Intelligence → Analysis linkage — LATER

Once the Live Intelligence contract survives a real specimen, test whether Analysis can reference factual Live observations without copying them into analytical evidence or allowing Analysis to rewrite upstream observations.

The target relationship is:

`factual observation -> optional canonical context -> analytical interpretation`

not:

`headline -> inferred cause -> rewritten event`.

## Stage 9 — broader Live Intelligence population / monitoring — ONLY AFTER AUDIT

Do not build a high-volume news ingest by default. Expansion must establish:

- source families and rights;
- observation identity/deduplication;
- correction/retraction handling;
- geographic/domain balance;
- noise controls;
- retention and provenance;
- separation of current observation from analytical inference.

Platform independence remains mandatory.

## Stage 10 — calendar export — LATER

Generate ICS/Google Calendar output from Canonical only. Calendar remains rebuildable output; deleting an export never deletes canonical data.

## Stage 11 — evaluate narrow auto-commit classes — GATE CLOSED

Only reconsider after the empirical commit gate is met, including prospective evidence of:

- a reschedule detected against a prior canonical snapshot on the same stable occurrence; and
- an explicit cancellation of an existing canonical occurrence from positive authoritative evidence.

Even if that evidence arrives, any first auto-commit class must be narrow and separately authorised. No blanket automation follows from monitor or parser maturity.
