# WORLD SIGNALS — Source-governance P1-G backfill audit v0.1

**Audit date:** 2026-09-04  
**Layer:** source-governance / post-transaction evidence  
**Canonical mutation authority:** none  
**Calendar mutation authority:** none  
**Monitor-route mutation authority:** none

## Scope

This audit records the completed bounded P1-G source-governance transaction and its independent post-transaction checks. It does not infer permissions from public access, official status, machine readability or successful fetching, and it does not authorise a P1-H tranche.

The frozen P1-G cohort covered exactly six canonical-dependent source records and 28 canonical dependencies:

- `WSSRC-MAC-015` — Statistics Bureau of Japan Labour Force Survey — 7 dependencies;
- `WSSRC-MKT-011` — ASX SPI 200 expiry rules — 6;
- `WSSRC-FIS-008` — Bank of Canada / Department of Finance Canada bond auctions — 5;
- `WSSRC-COM-012` — JODI Oil + Gas World Database updates — 4;
- `WSSRC-INT-029` — WTO reform checkpoints — 3;
- `WSSRC-REGJ-001` — State Bank of Pakistan FY27 MPC dates — 3.

Brazil TSE `WSSRC-EL-BR-001` and Swiss National Bank `WSSRC-CB-009` remained excluded pending provenance-scope repair.

## Transaction outcome

PR #16 merged the reviewed research, frozen plan, guarded helper and lifecycle tests into `main` at `6afe78c93286fa897ce3f134598b91b65d90d1b9` without mutating the source registry.

The registry-only transaction then ran on a branch rooted exactly at that merged checkpoint. Guarded workflow run `33875500751` passed:

- read-only P1-G preflight;
- explicit environment-gated apply;
- exact one-file diff enforcement;
- registry validation;
- full unit suite — 217 tests PASS;
- Python compilation;
- browser JavaScript checks;
- derived-site build;
- protected-diff reconfirmation;
- registry-only commit and push.

Transaction commit: `d43291bd352d28ae302fc3bdc1a5273d63705698`.

The transaction changed exactly `data/sources/registry.json` and advanced source registry **v1.58 / 223 → v1.59 / 223**. Canonical registry remained **v0.20 / 669** and monitor expectations remained **v0.7**. Automatic canonical commit remained false and Google Calendar writes remained false.

The temporary write-capable workflow was removed before review. PR #17 therefore presented a one-file net diff and merged to `main` as signed merge commit `29363b2f7b2c387bf983350939d7e56d9d045cc7`.

## Independent post-transaction audit

Separate read-only workflow run `33875701696` used the generic source-governance completeness audit rather than the migration helper. It independently measured source registry **v1.59 / 223**:

- **49** fully explicit governance sources;
- **174** sources still missing at least one governance field;
- **0 P0** configured-monitor dependencies;
- **103 P1** canonical-dependent sources;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **164**;
- missing `automated_monitoring_use`: **164**;
- missing `verification_mode`: **174**.

It also independently confirmed:

- canonical registry v0.20 / 669;
- monitor expectations v0.7;
- automatic canonical commit false;
- Google Calendar write false;
- Brazil inauguration remains `2027-01-05`;
- `WSSRC-EL-BR-001` and `WSSRC-CB-009` remained unbackfilled and held.

The temporary post-audit workflow was removed after the run.

## Frozen classifications

The six reviewed classifications remain exactly as authorised:

- Japan Labour Force: `CLEARED_CURATED_FACTUAL_METADATA` / `ENDPOINT_REVIEW_REQUIRED` / `AUTOMATED_PILOT`;
- ASX SPI 200: `MANUAL_INFORMATIONAL_REFERENCE_ONLY` / `PROHIBITED_OR_RIGHTS_HOLD` / `RIGHTS_HELD_MANUAL_ONLY`;
- Canada bond auctions: `CLEARED_CURATED_FACTUAL_METADATA` / `ENDPOINT_REVIEW_REQUIRED` / `AUTOMATED_PILOT`;
- JODI Oil + Gas: `MANUAL_INFORMATIONAL_REFERENCE_ONLY` / `PROHIBITED_OR_RIGHTS_HOLD` / `RIGHTS_HELD_MANUAL_ONLY`;
- WTO reform checkpoints: `CLEARED_CURATED_FACTUAL_METADATA` / `ENDPOINT_REVIEW_REQUIRED` / `MANUAL_AUTHORITATIVE_RECHECK`;
- SBP FY27 MPC: `MANUAL_INFORMATIONAL_REFERENCE_ONLY` / `PROHIBITED_OR_RIGHTS_HOLD` / `RIGHTS_HELD_MANUAL_ONLY`.

The mixed-rights cohort remains deliberate evidence that factual-provenance fitness, authoritative status, machine readability and automated-access permission are separate questions.

## Post-merge operational evidence

Merge-side CI run `33876083010` passed on `29363b2f7b2c387bf983350939d7e56d9d045cc7`. Coverage audit run `33876083215` also passed, and the subsequent Pages workflow-run deployment `33876115556` completed successfully.

Live monitor run **55** / GitHub run id `33876083123`, recorded `2026-09-04T13:04:57.341065+00:00`, ran directly against the merged checkpoint and reported:

- canonical registry v0.20;
- source registry v1.59;
- monitor expectations v0.7;
- 6 healthy adapters / 0 degraded;
- all 6 expected adapters observed;
- 0 review candidates;
- `NO_CHANGE`;
- canonical hash unchanged;
- automatic canonical commit false;
- Google Calendar write false.

The Colombia machine sentinel reported source id `WSSRC-REG4-002` and `HEALTHY`, while `WSSRC-REG4-001` remained the separate manual SUIN legal-verification authority. This closes the earlier operational identity-validation gate without collapsing machine inventory and legal authority into one source.

The Pages build following run 55 independently reduced the retained review horizon across **8 monitor runs** and reported:

- **0 retained review items**;
- **0 unsuccessful-run evidence gaps**;
- `horizon_complete=True`;
- runtime `AVAILABLE` and aligned with the current site;
- retained review state `AVAILABLE_RETAINED_HORIZON(0)`.

This closes the earlier “wait for the first genuine post-contract run 48+” observation gate. It does **not** prove candidate persistence through a real non-zero candidate yet; the persistence contract remains tested but awaits natural future candidate evidence rather than a manufactured event.

## Held controls

`WSSRC-EL-BR-001` remains held because the electoral-calendar source is not the correct provenance basis for the constitutionally grounded 5 January 2027 presidential inauguration. No Brazilian canonical date was altered.

`WSSRC-CB-009` remains held because its registered decisions/history URL does not directly support the forward monetary-policy assessment schedule described by the source record. Repair source scope before governance backfill.

Neither hold should be bypassed merely to reduce the numerical P1 backlog.

## Residual backlog and next decision

The measured unresolved backlog is **103 P1 canonical-dependent + 71 P2 registry-only** sources. P1-H is **not automatically authorised** as another six-source tranche.

The next source-governance step should first re-run/inspect the current P1 queue and select a bounded research cohort using active horizon, canonical dependency, source-scope integrity, regional breadth, domain diversity and governance-information value. Mechanical top-N selection, Western institutional concentration and cosmetic backlog reduction remain prohibited selection methods.

## Safety result

**PASS.** P1-G completed as a source-registry-only governance transaction. Canonical registry, Calendar, monitor expectations, monitor routes, automatic canonical commit and held provenance-scope controls remained outside the mutation boundary. Post-merge runtime evidence is aligned and healthy, but no monitor evidence has been promoted automatically into canonical state.
