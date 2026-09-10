# WORLD SIGNALS — Live correction / retraction / conflict contract research CM v0.1

**Status:** REVIEWED DESIGN BASIS / NO PRODUCTION POPULATION  
**Reference date:** 2026-09-10  
**Exact base main:** `1e4a6bbc8670fc36a452740401461f28e313c031` (merged PR #120)

## Purpose

CM hardens the executable Live Intelligence grammar for source disagreement, corrections and retractions before broader Live population. It is a contract tranche, not an event-population tranche.

The Project Charter requires WORLD SIGNALS to preserve provenance, never silently resolve conflicting sources, preserve revision history and keep Live factual verification distinct from Analysis. CL supplied a concrete pressure case: credible source formulations around Waqa Moana differed materially, and CL correctly excluded the subject rather than selecting a convenient stronger formulation.

CM does **not** reinterpret Waqa Moana and does not create a production conflict, correction or retraction row merely to exercise code paths.

## Fresh post-CL base

At exact base `1e4a6bbc8670fc36a452740401461f28e313c031`:

- Canonical: v0.42 / 689 occurrences;
- Source Registry: v2.04 / 258 sources;
- Change Ledger: v0.28 / 63 entries;
- Monitor expectations: v0.28 / 26 adapters;
- Live: v0.8 / 8 observations / 11 evidence / 3 Canonical-linked observations;
- Analysis: 22 reviews / 97 evidence / 1 production Live input / 1 production revision;
- automatic ingestion, public Live projection, automatic Canonical commit and Calendar write remain closed;
- OPEC CE quarantine remains present and excluded.

## Existing executable gap

The v0.8 controlled vocabulary already names:

- `CONFLICTING_REPORTS`;
- `CORRECTED`;
- `RETRACTED`;
- evidence role `CORRECTION_OR_REVISION`;
- `revision_of_observation_id`;
- an acyclic revision graph.

The current validator nevertheless leaves material gaps:

1. `CORRECTED` / `RETRACTED` requires a revision pointer but not correction/revision evidence;
2. the revision target is not required to have been observed earlier;
3. `CONFLICTING_REPORTS` does not require multiple unique evidence records;
4. it does not require distinct providers;
5. it does not require an explicit factual description of the disagreement.

A named vocabulary state without these invariants is not yet safe for broader use.

## Chosen conflict field shape

CM selects a narrow required text field:

`conflict_description: <non-empty factual string>`

for observations whose `verification_state == CONFLICTING_REPORTS`.

This is preferred to a new nested claim/winner ontology because CM does not yet have enough production specimens to justify a broader structure. The field records **what is disputed**, not which source should prevail. It must be absent from non-conflicting observations so ordinary verified observations do not acquire ambiguous hidden conflict semantics.

CM does not attempt automated prose adjudication. The contract can structurally require evidence plurality and an explicit disagreement description; deciding whether one claim is ultimately better supported remains a later reviewed factual update or Analysis question depending on the issue.

## Correction / retraction contract

For `verification_state` in `{CORRECTED, RETRACTED}` CM requires all of:

- a non-null `revision_of_observation_id` resolving to an existing prior Live observation;
- at least one referenced Live evidence row carrying `CORRECTION_OR_REVISION`;
- current `observed_at_utc` strictly later than the target observation's `observed_at_utc`;
- self-reference and revision cycles remain prohibited;
- state-update lineage remains distinct from revision lineage.

CM does **not** require every revision pointer to use `CORRECTED` or `RETRACTED`; future reviewed revision semantics may be broader. The new strict evidence/chronology rules are scoped to these two verification states.

## External data revisions remain distinct

`DATA_REVISION` continues to mean an observed revision to externally published data. It may exist without inventing a prior WORLD SIGNALS Live observation, provided it identifies the revised external target and references evidence carrying `CORRECTION_OR_REVISION`.

CM must not collapse this into Live correction/retraction lineage.

## Conflicting-report contract

For `verification_state == CONFLICTING_REPORTS`, CM requires:

- at least two **unique** referenced evidence records;
- at least two **distinct providers**, compared after trimming and case-folding provider names;
- a non-empty `conflict_description`;
- no requirement to identify a winning source or synthetic consensus.

Two reports from the same provider do not establish source plurality merely because they have different URLs/evidence IDs.

CM does not require a revision target for an initial conflict observation. A conflict may be the first Live state known to WORLD SIGNALS.

## Versioning decision

The Live schema materially changes, so CM advances the Live schema/store metadata from v0.8 to **v0.9**. Because the current validator requires schema, observation-store and evidence-store versions to match, observations/evidence dataset metadata must also advance to v0.9.

This is **not population growth**:

- observation objects remain exactly 8 and unchanged;
- evidence objects remain exactly 11 and unchanged;
- Canonical-linked count remains 3;
- the CL population state remains the current populated-state description;
- population ceilings remain 8 / 11;
- no ninth Live observation is authorised.

A `cm_checkpoint` should preserve that v0.9 is a no-population contract hardening descendant of CL.

## Validation strategy

CM should add synthetic fixture tests proving at minimum:

1. valid corrected observation with explicit prior target, correction evidence and later observation time;
2. corrected/retracted observation without correction evidence fails;
3. corrected/retracted observation at or before the target observation time fails;
4. corrected/retracted observation without a revision target fails;
5. valid initial `CONFLICTING_REPORTS` observation with two unique providers and explicit description;
6. one evidence row fails;
7. duplicate evidence IDs do not satisfy plurality;
8. two evidence rows from the same normalised provider fail;
9. missing/blank `conflict_description` fails;
10. `conflict_description` on a non-conflicting observation fails;
11. `DATA_REVISION` remains valid without synthetic prior Live history;
12. state-update/revision separation and cycle guards remain intact;
13. all eight existing observations and eleven evidence rows validate unchanged under v0.9.

## Protected boundary

CM may change only what is required for the Live contract and recovery/audit surfaces. It must not mutate:

- Canonical Registry/schema;
- Source Registry;
- Change Ledger;
- coverage overlays except derived/read-only recovery text if mechanically necessary;
- Monitor expectations/operations;
- Analysis schema/reviews/evidence;
- Calendar/public output authority;
- OPEC quarantine files.

Automatic ingestion, automatic Monitor→Live, automatic Live→Analysis, automatic Canonical commit, Google Calendar write, public Live observation projection and public Analysis projection remain closed.
