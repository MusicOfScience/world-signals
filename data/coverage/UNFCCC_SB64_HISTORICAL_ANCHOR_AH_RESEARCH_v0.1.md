# WORLD SIGNALS — UNFCCC SB64 historical-anchor research AH v0.1

Reference date: 2026-09-06
Exact base: `0d55a9dcd877736886dd9ee3e8fcaa8a93a869d1` (merged PR #62)

## Purpose

Post-AG reconnaissance leaves two canonical categories with forward coverage but no completed anchor: `CLIMATE_ENVIRONMENT` and `CORPORATE_FINANCIAL_MARKET_STRUCTURE`. The live exact-base probe finds no past-starting non-terminal occurrence in either category, so neither gap is a stale lifecycle artefact.

AH selects the UNFCCC June Climate Meetings (SB64), Bonn, 8–18 June 2026. This is not FIFO gap-filling. SB64 adds a completed global climate-governance process with first-party schedule and closure evidence and greater marginal analytical diversity than immediately backfilling another derivatives-expiry or index-reconstitution mechanism.

## First-party event evidence

Primary/event page:
- https://unfccc.int/sb64
- UNFCCC identifies the `June Climate Meetings (SB64)` in Bonn from **8 June to 18 June 2026**.
- The event page links the 64th sessions of the Subsidiary Body for Scientific and Technological Advice (SBSTA 64) and Subsidiary Body for Implementation (SBI 64).
- The same first-party page records at 23:45 on 18 June that the UN June Climate Meetings (SB64) had officially closed.

First-party closing statement:
- https://unfccc.int/news/written-statement-of-unfccc-executive-secretary-on-closing-of-un-june-climate-meetings-sb64
- UNFCCC's 18 June closing statement describes progress on some workstreams and continuing divides on others. It is evidence of closure and negotiation state, not evidence that implementation or climate outcomes followed.

## Temporal contract

Canonical timing is the authoritative **8–18 June 2026 local day range** in Bonn:
- `timing_type = MULTI_DAY_LOCAL`
- `start_local = 2026-06-08`
- `end_local = 2026-06-18`
- `source_timezone = Europe/Berlin`
- `time_precision = DAY`
- `all_day_semantics = true`
- `start_utc = null`
- `end_utc = null`.

The 23:45 closing update is completion evidence only. It must not be promoted into a synthetic endpoint for an eleven-day meeting whose authoritative canonical schedule is day-range based.

## Identity and ontology

Proposed occurrence: `WSO-CLIM-UNFCCC-SB64-202606`.
Proposed series: `WSER-CLIM-UNFCCC-SB`.
Proposed source: `WSSRC-CLIM-005`.

`WSSRC-CLIM-004` is already occupied by UNCCD COP17; source identities are immutable and globally unique, so AH must not reuse it.

The existing environmental schema already supports:
- category `CLIMATE_ENVIRONMENT`;
- event type `ENVIRONMENTAL_GOVERNANCE_EVENT`;
- `environmental_process_type = HISTORICAL_CONTEXT_ANCHOR`.

AH therefore does not invent a new taxonomy value. The SB64 umbrella occurrence represents the official June Climate Meetings as one historical context anchor. SBSTA64 and SBI64 remain legally distinct subsidiary-body sessions referenced by the umbrella event; AH does not claim they are one legal treaty-body session or a COP.

Render semantics are standalone: no COP31 conference-complex or coincident-session cluster identity is inherited from the COP31 template.

## Source governance

The existing UNFCCC source family has already been reviewed conservatively:
- official texts/data/documents may be used with source acknowledgement;
- general website-use conditions are more restrictive;
- public accessibility or public-domain status of official documents is not treated as permission for unrestricted automated retrieval.

The SB64-specific source inherits that posture:
- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`;
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`;
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`;
- no production monitor endpoint is introduced.

This is a curated historical provenance source, not a new live crawler route.

## Semantic guardrails

**Meeting completed ≠ negotiations succeeded ≠ parties agreed on every issue ≠ commitments implemented ≠ emissions changed ≠ climate outcomes achieved ≠ observed market response ≠ causal attribution.**

The closing statement's description of progress and unresolved divides belongs to later Analysis if selected. AH records only canonical occurrence identity, authoritative timing, completion and provenance.

SB64 also does not replace or mutate COP31/CMP21/CMA8. Those future occurrences remain independent canonical records.

## Candidate comparison

`CORPORATE_FINANCIAL_MARKET_STRUCTURE` remains a real gap. Existing forward holdings are concentrated in ASX/CME expiry mechanics, Russell reconstitution steps and later UK/EU T+1 implementation transitions. Historical market-structure anchors are feasible, including MSCI review/rebalance or an earlier exchange expiry, but choosing one solely to close the final histogram cell would risk mechanical sample inflation.

After AH, market structure should remain explicitly open for a separate contract-driven selection rather than being auto-filled.

## Mutation boundary

AH should add exactly:
- one canonical occurrence;
- one source record;
- one reviewed change-ledger entry;
- one biosecurity-overlay checkpoint/version advance only.

It should not mutate canonical schema, existing source records, monitoring policy/configuration, Analysis schema/reviews/evidence, Calendar output, Live Intelligence or observed market response.

PR #40 remains untouched. Manual merge only.
