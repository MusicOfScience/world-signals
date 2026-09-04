# WORLD SIGNALS — P1-D source-governance post-audit v0.1

**Audit date:** 2026-09-04  
**Merged checkpoint:** `fbd95ede5a02daebfa6271e101a2e006ae9ca4ac`  
**Source registry:** v1.56 / 223  
**Canonical registry:** v0.20 / 669  
**Monitor expectations:** v0.7

## Transaction result

P1-D applied the six frozen source-governance records reviewed in `SOURCE_GOVERNANCE_P1D_RESEARCH_v0.1.md` and advanced the Tier-1 source registry from v1.55 to v1.56. The transaction PR changed only `data/sources/registry.json`.

Merged sources:

- `WSSRC-CB-013` — Reserve Bank of Australia release schedule — 11 canonical dependencies;
- `WSSRC-MAC-003` — U.S. Bureau of Economic Analysis — 10;
- `WSSRC-MAC-024` — Statistics Bureau of Japan — 8;
- `WSSRC-REG-004` — Bank Indonesia — 4;
- `WSSRC-REG2-006` — INDEC Argentina — 4;
- `WSSRC-EL-KE-001` — Kenya Law / Constitution — 3.

Total bounded dependency coverage: **40 canonical dependencies**.

## Independent post-P1-D measurement

Read-only audit workflow run `33866450058` measured the merged v1.56 state:

- **31** fully explicit governance sources;
- **192** sources still missing at least one modern governance field;
- **0 P0** configured-monitor dependencies requiring governance backfill;
- **121 P1** canonical-dependent sources;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **182**;
- missing `automated_monitoring_use`: **182**;
- missing `verification_mode`: **192**;
- source count unchanged: **223**;
- unique sources used by canonical registry: **151**;
- unique sources used by configured monitor: **5**.

This is exactly the six-source delta expected from the pre-P1-D state (25 fully explicit / 127 P1).

## Held-source controls

Two provenance-scope holds remain intentionally unresolved and excluded from ordinary governance backfill:

- `WSSRC-EL-BR-001` — Brazil TSE: preserve the electoral-resolution scope and keep the `2027-01-05` presidential inauguration constitutionally grounded rather than treating it as a TSE calendar date.
- `WSSRC-CB-009` — Swiss National Bank: the registered decisions/history URL does not directly support the forward monetary-policy assessment schedule; source relationship repair is required before governance backfill.

Neither hold gained modern governance fields in P1-D.

## Invariants

P1-D did **not** alter:

- canonical registry v0.20 / 669;
- monitor expectations v0.7;
- automatic canonical commit policy (remains CLOSED / false);
- Google Calendar write policy (remains OFF / false);
- live-monitor runner;
- held-source records.

The next source-governance tranche must be selected from the measured v1.56 queue, not from a stale pre-P1-D ranking.
