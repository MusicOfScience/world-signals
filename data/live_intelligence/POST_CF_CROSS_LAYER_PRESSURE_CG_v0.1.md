# WORLD SIGNALS — post-CF cross-layer pressure audit CG v0.1

**Reference date:** 2026-09-10  
**Exact base `main`:** `6c96794cb553c6b34df93536141340c2af8db44a`  
**Branch:** `feature/post-cf-live-pressure-cg`

## 1. Verified merged boundary

CG begins from the exact merge of PR #114, `CF: audit Monitor pressure and validate NHC climate-risk pilot`.

Verified governed state relevant to pressure selection:

- Canonical Registry: `v0.41 / 689` occurrences;
- Source Registry: `v2.02 / 257` sources;
- Monitor expectations: `v0.27 / 25` configured adapters;
- explicitly Monitor-scoped Canonical occurrences: `215`;
- monitored regions: all `9` current Canonical regions;
- Live Intelligence: `v0.6 / 6` reviewed observations / `9` evidence rows;
- directly Canonical-linked Live observations: `1`;
- directly Canonical-linked Live occurrences: `1` (`WSO-MAC-B-0041`, Japan July 2026 household spending);
- Analysis: `v0.18 / 22` reviews / `97` evidence rows;
- production Analysis revisions: `1`;
- production Live→Analysis inputs: `1`.

CF did not register the validated NHC route into scheduled Monitor expectations and did not mutate Canonical, Source Registry, Change Ledger, Live Intelligence or Analysis populations.

## 2. OPEC exclusion

The quarantined CE OPEC provenance transaction is explicitly excluded from candidate selection.

`OPEC_QUARANTINE.md`, closed/unmerged PR #113 and `tests/test_opec_quarantine_cf.py` remain governing evidence. The existence of unresolved OPEC provenance debt is not a reason to reactivate CE and is not counted as a pressure advantage for any candidate.

## 3. Pressure critique

Raw population size is not a sufficient selection rule.

### Canonical

Canonical is comparatively broad at 689 occurrences. CG does not identify a first-order omission that is more urgent than downstream architecture pressure.

### Monitor

Monitor is no longer the clearest thin layer. Twenty-five configured adapters explicitly scope 215 occurrences across all nine regions. Three categories remain at zero configured scope (`CLIMATE_ENVIRONMENT`, `HEALTH_BIOSECURITY`, `PHYSICAL_CLIMATE_RISK`), but CF correctly treated those as review prompts rather than quotas.

The NOAA/NHC physical-climate-risk pilot is a validated future activation option, not an automatic next task. Registering it now would add one more route without testing the much thinner Canonical→Live bridge.

### Live Intelligence

Live remains deliberately small at six reviewed observations. Five zero-link observations are not defects: they represent genuinely unscheduled shocks or developments that should not acquire invented Canonical identities.

The actual architectural pressure is narrower: only one reviewed Live observation currently links to a real Canonical occurrence, and that link is an `OUTCOME_OF` relationship for an East Asian macroeconomic release. The schema already defines `CONTEXT_FOR`, but production has not yet exercised it.

This is a real frontier because pre-event factual context must be able to relate to a scheduled occurrence without:

- rewriting Canonical provenance or timing;
- treating context as an outcome;
- manufacturing an Analysis conclusion;
- promoting Monitor evidence automatically;
- creating a new Canonical identity.

### Analysis

Analysis has 22 reviews, 97 evidence rows and now one governed revision descendant. CD deliberately exercised the previously unused revision contract. A second revision immediately after that would add less architectural information than exercising a new reviewed Live→Canonical relationship.

The sole production Live→Analysis input remains intentionally controlled. CG does not expand it at the same time as the new Live relationship.

## 4. Candidate comparison

### NHC activation — hold

The NHC route is technically validated but not scheduled. It remains a good future Monitor candidate, subject to a fresh source/rights/endpoint check at activation time. CG holds it because Monitor route count is not the strongest current pressure.

### BARMM pre-election context — select

Canonical already contains the first BARMM parliamentary election polling occurrence:

- occurrence: `WSO-EL-PH-BARMM-20260914`;
- series: `WSER-EL-PH-BARMM-PE`;
- date: `2026-09-14`;
- native timezone: `Asia/Manila`;
- timing precision: `CIVIL_DATE` / day;
- lifecycle: `PLANNED`;
- certainty: `CONFIRMED`.

A previous post-BC audit deliberately held August BARMM peace/normalisation material because backfilling old context merely to exercise `CONTEXT_FOR` would have been population-for-population's-sake.

That hold is now resolved by new first-party government reporting published 9 September 2026. Philippine Information Agency reporting records government and MILF stakeholders signing ceasefire-related coordination guidelines and a pledge to promote a peaceful electoral process for the upcoming 14 September BARMM parliamentary election. The same current source surface identifies PIA as the Government of the Philippines' grassroots communications arm.

Primary current evidence:

- `https://pia.gov.ph/news/gph-milf-forge-commitment-to-promote-peaceful-electoral-process-during-the-barmm-polls/`

Current rights/source-use check:

- `https://pia.gov.ph/about/`
- PIA states: `All content is in the public domain unless otherwise stated.`

The selected Live record will retain only minimal factual/provenance metadata and the source URL; it will not mirror page bodies.

### PIA energy-security article — reject as evidentiary basis

A separate PIA article published 9 September describes energy-security preparations but states the election date as 15 September. That conflicts with the existing competent COMELEC-based Canonical date of 14 September and with the selected PIA peace-process article itself.

CG does not silently reconcile that disagreement, does not use the conflicting article as date authority, and does not let Live evidence mutate Canonical timing.

## 5. Selected bounded contract

CG may add exactly one reviewed Live observation:

- type: `INSTITUTIONAL_DEVELOPMENT`;
- verification: `PRIMARY_CONFIRMED`;
- jurisdiction: Philippines;
- region: Southeast Asia;
- domain tags: `POLITICS`, `INSTITUTIONS`;
- Canonical relationship: `CONTEXT_FOR` `WSO-EL-PH-BARMM-20260914`;
- evidence: one PIA primary-official row;
- real-world event clock: not manufactured; no `event_time` is required because the article says stakeholders `recently` signed/reaffirmed the arrangement without a source-native exact date/time for that act;
- source publication precision: `CIVIL_DATE 2026-09-09`;
- Canonical provenance effect: `NONE`.

CG must not claim that the coordination guarantees a peaceful election, changes electoral integrity, resolves the Bangsamoro peace process, alters election timing, predicts the result or causes any market outcome.

## 6. Governed target and protected layers

Target Live state:

- schema `v0.6 → v0.7`;
- observations `6 → 7`;
- evidence `9 → 10`;
- public observation projection remains closed;
- automatic ingestion remains closed;
- automatic Canonical commit remains off;
- Google Calendar writes remain off.

Protected from CG mutation:

- Canonical Registry and schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- Monitor expectations and operations policy;
- Analysis schema, reviews and evidence;
- NHC CF pilot implementation/validation state;
- OPEC quarantine record and regression guard.

A second CG Live observation, automatic context linkage, second production Live→Analysis input, Analysis revision, NHC activation or any Canonical mutation requires a separate reviewed decision.
