# WORLD SIGNALS — CC research note: HM Treasury UK T+1 Content API sentinel

**Reference date:** 2026-09-09  
**Exact base:** `67de150ac1175c59ccfa3a844c1dcecd1dc2b4ed` (post-CB main)

## Pressure audit

CC began with a fresh post-CB monitor coverage audit rather than selecting another monetary-policy or macroeconomic source by habit. The configured cohort covers all nine Canonical regions but has no configured monitor scope in four Canonical categories: `CLIMATE_ENVIRONMENT`, `CORPORATE_FINANCIAL_MARKET_STRUCTURE`, `HEALTH_BIOSECURITY`, and `PHYSICAL_CLIMATE_RISK`. Those absences are review prompts, not quotas.

The missing-domain drill-down rejected several superficially attractive routes:

- WHO governance dates map cleanly to existing health objects and user-facing calendar export affordances are visible on parts of the WHO event stack, but the reviewed WHO reuse terms do not establish the bounded automated production permission WORLD SIGNALS requires. Existing WHO rights holds therefore remain closed.
- NOAA's Atlantic hurricane-season source is more permissive operationally, but the Canonical objects are standing physical-risk windows rather than discrete event-state objects. A source monitor would risk conflating a climatological exposure window with an actual shock.
- FTSE Russell/LSEG reconstitution dates are operationally relevant, but the reviewed source does not yet provide the same clean first-party machine-interface and rights contract.
- EU T+1 is already a confirmed legal implementation occurrence. Existing EUR-Lex/Cellar legal-monitor patterns remain available, but this is less valuable as a test of a genuinely conditional Canonical object.

The selected CC candidate is the United Kingdom T+1 securities-settlement transition. Existing Canonical source `WSSRC-MKT-012` supplies one conditional occurrence, `WSO-MKT-A-0016`, dated 11 October 2027. It is explicitly `PROVISIONAL`, `CONDITIONAL`, and `PENDING_DEPENDENCY`: the final statutory instrument must be laid, approved and made with that commencement.

## Source decomposition

`WSSRC-MKT-012` remains the Canonical policy/dependency source and is not repurposed as a machine monitor.

CC proposes a separate monitor-only source `WSSRC-MKT-014` for the GOV.UK Content API representation of the exact HM Treasury policy note:

- human page: `https://www.gov.uk/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk`
- Content API endpoint: `https://www.gov.uk/api/content/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk`
- Content API documentation: `https://content-api.publishing.service.gov.uk/`
- API reference: `https://content-api.publishing.service.gov.uk/reference.html`
- GOV.UK terms: `https://www.gov.uk/help/terms-conditions`

GOV.UK documents the Content API as a JSON interface for applications accessing GOV.UK content, including applications that need to keep incorporated content up to date. It requires no authentication and publishes a client rate limit far above the proposed WORLD SIGNALS request budget. The HM Treasury page is Crown copyright material made available under the Open Government Licence v3.0. CC treats that as clearance only for this bounded first-party Content API route; it is not a licence to crawl linked legislation, attachments or unrelated GOV.UK surfaces.

`WSSRC-MKT-014` has **zero direct Canonical dependencies**. The Canonical occurrence remains owned by `WSSRC-MKT-012`; the monitor-only source reaches `WSO-MKT-A-0016` solely through the configured monitor route scope. This distinction is required by the source-registry dependency helpers and prevents a machine-interface identity from being misrepresented as Canonical provenance authority.

## Read-only pressure diagnostics

The first post-CB pressure workflow initially failed before any project diagnostic because the temporary harness used the default shallow checkout and then requested `HEAD^`. That failure is preserved as harness evidence:

- run `34322055392`
- job `102370697091`
- cause: shallow checkout ancestry assertion, not governed-data or source failure
- substantive diagnostic steps skipped

Corrected and deeper read-only audits passed:

- run `34322107218`, job `102370859793`
- run `34322177654`, job `102371081444`
- run `34322353722`, job `102371643902`

They established the exact post-CB governed state and the candidate semantics while leaving governed files unchanged.

## One-request Content API contract diagnostic

Successful live contract diagnostic:

- run `34322468430`
- job `102372012320`
- exactly one Content API request
- zero follow-up requests
- HTTP 200
- content type `application/json; charset=utf-8`
- `content_id`: `b6b2d2f2-eae6-4564-9ed1-338abb8ca2f2`
- exact stable `base_path`: `/government/publications/accelerated-settlement-t1/policy-note-mandating-t1-settlement-in-the-uk`
- `document_type`: `html_publication`
- `schema_name`: `html_publication`
- exact title: `Policy note – Mandating T+1 settlement in the UK`
- `public_updated_at`: `2025-11-20T09:30:10+00:00`
- repository byte-clean outside temporary diagnostics

The live body still contained all baseline pending-dependency markers tested by the diagnostic:

- the SI is draft and should not be treated as final;
- HM Treasury intends to lay the final SI;
- the instrument is subject to the affirmative procedure;
- Parliamentary approval language is present;
- 11 October 2027 remains the stated implementation date.

## Architecture and semantic boundary

The proposed route is `HMT_T1_CONTENT_API`, with monitor role `CONDITIONAL_LEGISLATIVE_DEPENDENCY_SENTINEL`.

It is deliberately **not** a legal-completion detector. A GOV.UK Content API observation cannot by itself prove that a statutory instrument has been laid, approved by both Houses, made, commenced, amended or superseded. Those are legal-state questions requiring separate authoritative verification.

The monitor therefore:

1. makes exactly one GET request to the exact Content API object;
2. fails closed if the stable content identity, base path, title, schema/document type or JSON contract drifts;
3. stores/compares only minimal semantic state needed for change detection;
4. treats unchanged `public_updated_at`, no withdrawal notice and continued presence of the current pending-dependency markers as a non-mutating observation;
5. generates a manual dependency-review candidate if `public_updated_at` advances, a withdrawal notice appears, a required pending marker disappears, or the stated 11 October 2027 marker changes/disappears;
6. does not treat raw transport/body hash change alone as legal-state evidence;
7. does not automatically fetch the human page, parent publication, draft SI attachment, legislation.gov.uk, Parliament, search/discovery routes or any other follow-up;
8. gives source failure no schedule, lifecycle, certainty, condition-state, delay, cancellation or implementation semantics;
9. never automatically changes Canonical condition state, certainty, date/time, lifecycle, occurrence population, Live Intelligence or Analysis;
10. requires manual authoritative UK legal verification before any governed event-state change.

If the HM Treasury page is revised merely for editorial reasons, the candidate remains review-only. If it is revised to report a new legal milestone, that is still only a prompt to verify the legal instrument through the appropriate authoritative source.

## First guarded materialisation attempt

The first guarded materialisation run is intentionally preserved rather than rewritten out of the history:

- run `34323139129`
- job `102374145190`
- exact pre-state and ancestry: PASS
- guarded transaction in the ephemeral workspace: PASS
- registry validator: PASS
- Live Intelligence validator: PASS
- Analysis validator: PASS
- full unittest discovery: FAILED with two failures after 1,196 tests (68 skipped)
- commit/push step: not reached
- therefore no materialised governed changes escaped the workflow workspace

The failures had different meanings:

1. `test_sarb_mpc_rss_activation_cb` froze the repository at CB's exact Sources/Monitor counts (`v2.01/256`, `v0.26/24`). CC correctly advances those descendant layers, so the CB test is being made descendant-safe while retaining exact CB source, route, request-budget and authority-gate assertions.
2. `test_source_governance_verification_closeout_a` exposed a genuine CC governance error: the proposed monitor-only `WSSRC-MKT-014` had been assigned `canonical_dependency_count: 1`, although no Canonical record uses that source ID. The correct value is `0`; the single occurrence is reached only by the monitor route and remains sourced to `WSSRC-MKT-012`.

The first-run failure is therefore useful validation evidence: it caught both a historical test-maintenance problem and a real source-governance classification defect before any production-shaped state was committed.

## Governed target

If implementation survives materialised and live validation:

- Canonical Registry: v0.41 / 689 unchanged
- Sources: v2.01 / 256 → v2.02 / 257
- Monitor expectations: v0.26 / 24 → v0.27 / 25
- automatic Canonical commit OFF
- Google Calendar write OFF
- Change Ledger, Live Intelligence, Analysis and unrelated governed layers unchanged
