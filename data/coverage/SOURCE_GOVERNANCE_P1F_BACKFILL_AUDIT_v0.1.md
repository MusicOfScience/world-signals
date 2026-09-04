# WORLD SIGNALS — P1-F source-governance backfill audit v0.1

**Audit date:** 2026-09-04  
**Merged checkpoint:** `21665ddce58cf9c7c7e868727ad4c2e19e6dce62`  
**Source registry:** v1.58 / 223  
**Canonical registry:** v0.20 / 669  
**Monitor expectations:** v0.7

## Transaction reconciliation

P1-F infrastructure PR #14 merged as signed commit `b92858008bb2897e49f7c6959ab9b1d55dd09fab`. The guarded registry-only transaction ran as GitHub Actions run `33871313942`, passed preflight, exact registry-only diff enforcement, registry validation, the full unit suite, Python compilation, browser JavaScript checks and site build, and produced transaction commit `f24e35deca5c99a43eea7ef054a272c59572fa12` on the transaction branch. Transaction PR #15 then merged as signed main commit `21665ddce58cf9c7c7e868727ad4c2e19e6dce62`.

The merged transaction advanced the Tier-1 source registry **v1.57 → v1.58 / 223** and changed only the six frozen P1-F source records plus the registry version. Canonical v0.20 / 669, monitor expectations v0.7, automatic canonical commit and Google Calendar write state were unchanged.

## Independent post-transaction audit

Independent read-only audit run `33872209871` measured the merged v1.58 state:

- **43** sources fully explicit for all modern governance fields;
- **180** sources still missing at least one modern governance field;
- **0 P0** configured-monitor dependencies;
- **109 P1** canonical-dependent sources;
- **71 P2** registry-only sources;
- missing `canonical_provenance_use`: **170**;
- missing `automated_monitoring_use`: **170**;
- missing `verification_mode`: **180**;
- all **223** records already retain `monitoring_readiness_status`.

This is exactly the expected six-record reduction from the measured post-P1-E state. No anomalous source-count or priority migration occurred.

## P1-F source outcomes retained

The six P1-F classifications remain explicit and semantically intact:

- `WSSRC-MAC-014` — Statistics Bureau of Japan CPI: cleared curated factual metadata / endpoint review required / automated pilot.
- `WSSRC-MAC-012` — ABS Labour Force: cleared curated factual metadata / endpoint review required / automated pilot.
- `WSSRC-MKT-010` — CME E-mini S&P 500 quarterly expiry: manual informational reference / prohibited-or-rights-hold / rights-held manual only.
- `WSSRC-COM-002` — IEA Oil Market Report schedule: manual informational reference / prohibited-or-rights-hold / rights-held manual only.
- `WSSRC-CN-012` — ChinaMoney / NIFC LPR rule: manual informational reference / prohibited-or-rights-hold / rights-held manual only.
- `WSSRC-EL-NG-001` — Nigeria INEC revised 2027 timetable: cleared curated factual metadata / endpoint review required / manual authoritative recheck.

The negative controls remain intentional: official/public availability did not override explicit rights restrictions for CME, IEA OMR or ChinaMoney.

## Held-source controls

The two standing provenance-scope holds remain unchanged:

- `WSSRC-EL-BR-001` — Brazil TSE. The canonical `2027-01-05` presidential inauguration remains constitutionally grounded and must not be sourced to the electoral-calendar record.
- `WSSRC-CB-009` — Swiss National Bank. The registered decisions/history URL still does not directly support the forward assessment schedule and must be repaired before governance backfill.

## Next bounded tranche

P1-G research is frozen separately in `SOURCE_GOVERNANCE_P1G_RESEARCH_v0.1.md` and its guarded plan. The P1-F audit itself authorises no registry write.
