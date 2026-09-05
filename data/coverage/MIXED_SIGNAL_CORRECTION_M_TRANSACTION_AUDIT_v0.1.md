# WORLD SIGNALS — Mixed-signal correction M transaction audit v0.1

**Transaction date:** 2026-09-05  
**Base:** canonical v0.26 / 669; source v1.67 / 228; biosecurity overlay v0.1  
**Post-state:** canonical **v0.27 / 673**; source **v1.68 / 231**; biosecurity overlay **v0.2**

## Added occurrences
- `WSO-CBN-MPC-307`
- `WSO-CBN-MPC-308`
- `WSO-BWC-WG-2026-S10`
- `WSO-WOAH-GS-094`

## Added sources
- `WSSRC-CB-014`
- `WSSRC-INT-032`
- `WSSRC-INT-033`

## Invariants
- all 669 pre-existing canonical objects unchanged;
- all 228 pre-existing source objects unchanged;
- CBN remains a two-day process window with no synthetic decision time or venue;
- BWC remains `INTERNATIONAL_INSTITUTIONS`;
- WOAH remains `AGRICULTURE_FOOD`;
- BWC and WOAH graduate from noncanonical biosecurity candidates to cross-domain memberships;
- IPPC CPM-21 and North Indian Ocean cyclone seasons remain held;
- automatic canonical commit OFF; Google Calendar writes OFF.

## Protected files
Change ledger SHA-256: `47fa0467dd6290b867355c18251cd585d61efa885688e7ecfee30a117fb40738`  
Monitor expectations SHA-256: `4c5ea0ca82741369f4ff7113c47bb64759c32030a71582d5ac9558272bf6c8c6`

## Validator warnings
- WSO-EL-A-0012: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0009: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0010: timed event missing start_utc (legacy/backfill candidate)

This audit authorises no automatic canonical writes, production crawling or analytical causal claims.
