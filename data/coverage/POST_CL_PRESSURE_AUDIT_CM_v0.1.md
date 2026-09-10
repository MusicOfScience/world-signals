# WORLD SIGNALS — post-CL pressure audit / CM selection v0.1

**Status:** READ-ONLY PRESSURE DECISION  
**Reference date:** 2026-09-10  
**CL branch state audited:** Live v0.8 / 8 observations / 11 evidence rows / 3 Canonical-linked observations  
**Coverage workflow:** run `34436436416` / job `102742356855`  
**Coverage artifact:** `world-signals-coverage-audit-34436436416`  
**Artifact digest:** `sha256:4a3d56a45a0a273d5f445769cc13091438474e4ad48110bb8f30be39895b3aab`

## Purpose

Choose the next bounded pressure after CL from the actual post-CL state. Counts are diagnostic only. This audit does not create a Canonical event, Monitor route, Live observation, Analysis review or bridge relationship.

## Post-CL cross-layer result

The read-only audit reports:

- Canonical: **689 occurrences / 203 series**;
- Monitor: **26 adapters / 217 explicitly scoped occurrences / 48 series**;
- Live: **8 observations / 3 Canonical-linked**;
- Analysis: **22 reviews / 1 production Live input / 1 production revision**.

Regional prompts after CL:

- Europe: no controlled Live observation;
- Latin America: no controlled Live observation;
- North America: no controlled Live observation;
- Oceania / Pacific is no longer a zero-Live region because CL adds one reviewed PIF observation.

Category prompts remain:

- `CLIMATE_ENVIRONMENT`: no configured Monitor scope;
- `HEALTH_BIOSECURITY`: no configured Monitor scope;
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE`: no Analysis review.

These are prompts, not queues or quotas.

## Live → Analysis frontier after CL

The frontier changed materially:

- used Live observations: **1** — Japan FIES;
- completed linked observations with an existing Analysis target and not yet used: **0**;
- completed linked observations without an Analysis review: **1** — `WSLI-INST-PIF-PARTNER-FRAMEWORK-20260904-001` → `WSO-INT-A-0001`;
- linked observations whose Canonical target is not completed: **1** — BARMM pre-election context;
- unlinked Live observations: **5**;
- factual same-anchor bridge-ready candidate count: **0**.

PIF is therefore **not currently a second production bridge candidate**. The existing bridge validates `FACTUAL_INPUT` only against an Analysis review with the same Canonical anchor, and no PIF Analysis review exists. The Analysis live-input policy also remains `CONTROLLED_SINGLE_PRODUCTION_LINK` with `maximum_production_live_inputs = 1`, already occupied by Japan FIES.

Creating a PIF Analysis review merely to manufacture a second bridge target would invert the architecture. Analysis must be independently justified by analytical evidence; a graph edge is not a reason to write an analysis.

## Candidate comparison

### A. PIF Analysis / second Live→Analysis link — NOT SELECTED

Why not now:

- no same-anchor Analysis review exists;
- the current bridge population ceiling is already one;
- a standalone PIF Analysis would need a defensible expectation baseline and adequate evidence for surprise, movements, alternatives and second-order assessment on its own merits;
- CL deliberately excluded Waqa Moana because fresh source formulations were not reconciled through directly retrievable final Forum Secretariat evidence;
- creating Analysis to unlock a bridge would be architecture-driven population rather than evidence-driven analysis.

The PIF Live observation remains available for a later independently justified review or bridge audit.

### B. `CORPORATE_FINANCIAL_MARKET_STRUCTURE` Analysis zero — NOT SELECTED

This remains a real coverage prompt, but earlier WORLD SIGNALS audits repeatedly documented why it should not be mechanically closed: easy candidates are concentrated in expiry, reconstitution and settlement-transition mechanics. Selecting an ASX/CME/index-rebalance backfill merely to erase the final category zero would optimise the histogram rather than the intelligence system.

A future market-structure review remains valid if a specific event has materially useful expectation/outcome/market evidence. The zero alone is not permission.

### C. Europe / Latin America / North America zero-Live prompts — NOT SELECTED

CL removed one regional zero without using the zero as its selection rule. Repeating that pattern mechanically would turn the diagnostic into a quota queue. No current candidate in these regions has been established by this audit as more important or contractually novel than the capability pressure below.

### D. Monitor zero categories — NOT SELECTED

`CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` remain constrained by existing source/rights posture. Zero Monitor scope is not unattended-retrieval permission.

## Capability pressure exposed by CL

CL's fresh source review surfaced a concrete disagreement in institutional-status wording around Waqa Moana. The Australian Prime Minister's release used the stronger formulation `unanimously endorsed`; indexed final-communiqué text used `agreed in principle` and noted further national consultations. CL correctly excluded that subject rather than choosing a stronger formulation without direct reconciliation of the final Forum text.

This exposed a more general Live-layer issue.

The Live schema already contains verification states:

- `CONFLICTING_REPORTS`;
- `CORRECTED`;
- `RETRACTED`.

It also contains evidence role `CORRECTION_OR_REVISION`, revision references and a revision graph. However the current executable validator is incomplete for broader use:

1. a `CORRECTED` or `RETRACTED` observation requires `revision_of_observation_id`, but does not also require evidence carrying `CORRECTION_OR_REVISION`;
2. a correction/retraction revision pointer is not required to point to an observation with an earlier `observed_at_utc`;
3. `CONFLICTING_REPORTS` does not require multiple evidence records from distinct providers;
4. `CONFLICTING_REPORTS` has no explicit structured field describing what propositions or source claims are in conflict;
5. the schema names these states but no controlled production specimen has exercised them.

The next safe step is therefore to harden the grammar before increasing Live volume, not to populate a correction merely for test coverage.

## CM selection — Live correction / retraction / conflicting-report contract hardening

**CM is selected for fresh design after CL is merged.**

CM should be a **no-production-population foundation tranche**. Its purpose is to make correction/conflict semantics executable and testable without manufacturing a real-world correction.

Minimum design pressure:

1. start from the exact then-current post-CL `main`;
2. preserve all eight existing Live observations and eleven evidence rows byte-for-byte unless a schema migration absolutely requires otherwise;
3. keep `state_update_of_observation_id` distinct from `revision_of_observation_id`;
4. preserve `DATA_REVISION` as an external-data concept that does not require a synthetic prior Live row;
5. for `CORRECTED` / `RETRACTED`, require an explicit revision target and at least one referenced evidence row with `CORRECTION_OR_REVISION` role;
6. require the correction/retraction observation's `observed_at_utc` to be later than the referenced prior Live observation;
7. prohibit self-reference and revision cycles as today;
8. define a bounded `CONFLICTING_REPORTS` contract requiring at least two supporting evidence records from distinct providers and an explicit factual description of the disagreement;
9. do not require `CONFLICTING_REPORTS` to choose a winner or collapse competing claims into a synthetic consensus;
10. use synthetic/fixture tests to prove valid and invalid shapes; **do not create a production conflict, correction or retraction row merely to exercise the contract**;
11. do not reinterpret Waqa Moana inside CM; the CL exclusion remains historical evidence of pressure, not a queued Live observation;
12. do not alter Canonical, Sources, Change Ledger, Monitor, Analysis, Calendar/public projection or OPEC quarantine;
13. keep automatic ingestion, automatic Canonical commit, automatic Monitor→Live, automatic Live→Analysis and public Live projection closed.

The detailed schema design must still be pressure-tested on the fresh CM branch. In particular, CM must decide whether a structured `conflict_description` object or a narrower required text field is preferable; this audit does not pre-authorise a field shape.

## Why CM now

CM addresses a failure mode that becomes more consequential as Live grows: silently overwriting, over-resolving or under-documenting disagreement. It is directly motivated by a real CL source conflict, already anticipated by the roadmap's requirement to establish correction/retraction handling before high-volume Live ingest, and improves every geography/domain rather than filling one histogram cell.

It also preserves the architecture discipline learned in CK and CL:

- absence does not imply permission;
- linkage does not imply Analysis;
- disagreement does not imply a correction;
- a stronger source formulation is not selected merely because it is more convenient;
- controlled vocabulary without executable invariants is not yet a mature contract.

## Authority boundary

This audit authorises **no CM write on the CL branch**. CM begins only after user merge of the final CL PR and exact verification of the new `main` boundary.

Automatic Canonical commit, Google Calendar write, automatic Monitor→Live, automatic Live→Analysis, public Live projection and public Analysis projection remain closed. OPEC CE quarantine remains excluded.
