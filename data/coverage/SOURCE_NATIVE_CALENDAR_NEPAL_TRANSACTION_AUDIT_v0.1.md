# WORLD SIGNALS — Nepal source-native calendar transaction audit v0.1

**Transaction date:** 2026-09-05  
**Base:** schema v0.51; canonical v0.27 / 673; source v1.68 / 231; biosecurity overlay v0.2 @ v0.27/673  
**Post-state:** schema **v0.52**; canonical **v0.28 / 674**; source **v1.69 / 233**; biosecurity overlay **v0.3 @ v0.28/674**

## Added canonical occurrence
- `WSO-FIS-NP-BUDGET-2084` — `Nepal Federal Budget 2084/85 — presentation`
- authoritative native date: `15 Jestha 2084`
- Gregorian resolution: `UNRESOLVED_AUTHORITATIVE_CONVERSION`

## Added sources
- `WSSRC-FIS-026`
- `WSSRC-FIS-027`

## Analytical-overlay checkpoint alignment
- biosecurity overlay version advances from v0.2 to v0.3 solely to record the new canonical checkpoint;
- canonical checkpoint advances from v0.27 / 673 to v0.28 / 674;
- systems, relationships, canonical-series memberships, candidate nodes, principles and notes remain unchanged;
- Nepal receives no biosecurity membership.

## Invariants
- all 673 pre-existing canonical objects unchanged;
- all 231 pre-existing source objects unchanged;
- no Gregorian/local/UTC date field populated for the Nepal occurrence;
- source-native event certainty remains independent from Gregorian conversion readiness;
- North Indian Ocean cyclone-season candidate remains held under first-party definition conflict;
- automatic canonical commit OFF; Google Calendar writes OFF.

## Protected files
Change ledger SHA-256: `47fa0467dd6290b867355c18251cd585d61efa885688e7ecfee30a117fb40738`  
Monitor expectations SHA-256: `4c5ea0ca82741369f4ff7113c47bb64759c32030a71582d5ac9558272bf6c8c6`

## Validator warnings
- WSO-EL-A-0012: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0009: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0010: timed event missing start_utc (legacy/backfill candidate)

This audit authorises no automatic canonical writes, no third-party calendar conversion dependency and no production crawler promotion.
