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

## Stage 6 — Live Intelligence foundation — DONE / AV

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

**AV v0.1 deliberately prohibited production observation/evidence population; that frozen foundation checkpoint remains preserved through AW v0.2 and AX v0.3.**

## Stage 7 — controlled Live Intelligence specimens — DONE / AW + AX

AW selected the 26 August 2026 Bhote Koshi / Rasuwa flood in Nepal after comparing physical-shock, health-emergency, geopolitical/policy, economic-revision and market-observation candidates. Live Intelligence v0.2 proved unscheduled identity, native event time, civil-date publication precision and zero Canonical links without opening public projection.

AX then selected the 2026 DRC Bundibugyo outbreak because successive WHO snapshots stress a different contract boundary: **state evolution is not revision**. Live Intelligence v0.3 preserves the Nepal row and adds two DRC `HEALTH_EMERGENCY` observations sharing one manually reviewed story key. The 30 August state points to the 26 August state with `state_update_of_observation_id`, while both retain null revision links.

AX also makes state-as-of time explicit and distinct from event, publication and WORLD SIGNALS observation time. Manual story identity is a grouping key only; automatic clustering, public projection and continuous ingestion remain closed. AX's frozen checkpoint is three observations and four primary-official evidence rows. AZ v0.4 adds one separately pressure-audited Japan economic-data observation and two primary-official evidence rows, taking the current bounded internal population to four observations and six evidence rows.

AZ completed the required pre-fourth-observation audit before adding the Japan FIES specimen. Before any fifth observation or broader ingestion, run another pressure audit.

## Stage 8 — prospective Live Intelligence → Analysis linkage — AZ FIRST PRODUCTION LINK DONE / PUBLIC CLOSED

AY established the executable bridge grammar with production population closed. AZ then pressure-audited and populated exactly one relationship: the completed July 2026 Japan FIES Canonical occurrence -> one reviewed Live `ECONOMIC_DATA_OBSERVATION` -> one Analysis review selecting that immutable observation as `FACTUAL_INPUT`.

The relationship remains:

`factual observation -> optional canonical context -> analytical interpretation`

not:

`headline -> inferred cause -> rewritten event`.

Live evidence is not transitively migrated into Analysis evidence, upstream Live records remain immutable, and story/latest selectors remain prohibited. The inaugural factual input must share the review's Canonical occurrence. Production `live_inputs` are capped at one and public Live-input projection remains closed. Another pressure audit is required before any second production relationship.

## Stage 8A — Analysis revision lineage — BA FOUNDATION DONE / PRODUCTION CLOSED

BA establishes the prospective grammar for changing an analytical judgement without rewriting the prior snapshot. Production revision population remains zero.

A future revision must be a new immutable `analysis_id` linked by `revision_of_analysis_id`, preserve the parent row, remain on the same Canonical occurrence and advance `analysis_as_of_utc`. Revision kind and reason are explicit. Cycles and first-mode branching are prohibited. `NEW_LIVE_EVIDENCE` revisions must identify at least one novel immutable Live observation relative to the parent.

Live observations never automatically revise Analysis. Live correction/state-update lineage and Analysis revision lineage remain separate. No public latest-head collapse or revision-metadata projection is opened by BA. The first production Analysis revision requires another pressure audit.

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
