# WORLD SIGNALS — P1-E source-governance post-audit v0.1

**Audit date:** 2026-09-04  
**Merged checkpoint:** `bd348a18d0b67d2b973ec7b61d0e8ede2e35cb9d`  
**Source registry:** v1.57 / 223  
**Canonical registry:** v0.20 / 669  
**Monitor expectations:** v0.7

## Transaction result

P1-E applied the six frozen source-governance records reviewed in `SOURCE_GOVERNANCE_P1E_RESEARCH_v0.1.md` and advanced the Tier-1 source registry from v1.56 to v1.57. The transaction PR changed only `data/sources/registry.json`.

Merged sources:

- `WSSRC-CB-004` — ECB monetary-policy decisions/accounts publication surface — 11 canonical dependencies;
- `WSSRC-CB-005` — Bank of England upcoming MPC dates — 11;
- `WSSRC-MAC-025` — Japan Customs / Ministry of Finance trade-statistics release calendar — 8;
- `WSSRC-MAC-011` — Australian Bureau of Statistics CPI — 6;
- `WSSRC-CLIM-003` — Convention on Biological Diversity COP — 4;
- `WSSRC-REGJ-005` — Central Bank of Egypt MPC schedule — 3.

Total bounded dependency coverage: **43 canonical dependencies**.

## Independent post-P1-E measurement

Read-only audit workflow run `33869947061` measured the merged v1.57 state:

- **37** fully explicit governance sources;
- **186** sources still missing at least one modern governance field;
- **0 P0** configured-monitor dependencies requiring governance backfill;
- **115 P1** canonical-dependent sources;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **176**;
- missing `automated_monitoring_use`: **176**;
- missing `verification_mode`: **186**;
- source count unchanged: **223**;
- unique sources used by canonical registry: **151**;
- unique sources used by configured monitor: **5**.

This is exactly the six-source delta expected from the pre-P1-E state (31 fully explicit / 121 P1).

## Held-source controls

Two provenance-scope holds remain intentionally unresolved and excluded from ordinary governance backfill:

- `WSSRC-EL-BR-001` — Brazil TSE: preserve the electoral-resolution scope and keep the `2027-01-05` presidential inauguration constitutionally grounded rather than treating it as a TSE calendar date.
- `WSSRC-CB-009` — Swiss National Bank: the registered decisions/history URL does not directly support the forward monetary-policy assessment schedule; source relationship repair is required before governance backfill.

Neither hold gained modern governance fields in P1-E.

## Invariants

P1-E did **not** alter:

- canonical registry v0.20 / 669;
- monitor expectations v0.7;
- automatic canonical commit policy (remains CLOSED / false);
- Google Calendar write policy (remains OFF / false);
- live-monitor runner;
- held-source records.

The next source-governance tranche must be selected from the measured v1.57 queue, not from a stale pre-P1-E ranking.
