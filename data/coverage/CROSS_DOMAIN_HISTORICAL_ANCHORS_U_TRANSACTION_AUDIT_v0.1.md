# WORLD SIGNALS — Cross-domain historical anchors U transaction audit v0.1

**Transaction date:** 2026-09-06  
**Post-state:** canonical **v0.30 / 681**; sources **v1.72 / 237**; change ledger **v0.17 / 51**; biosecurity overlay **v0.5 @ v0.30/681**  
**Analysis:** reviews **v0.4 / 8**; evidence **v0.4 / 21** — unchanged

## Added completed historical anchors
- `WSO-BWC-WG-2026-S08` — BWC Working Group on the Strengthening of the Convention — eighth session — `TREATY_WORKING_GROUP_SESSION`
- `WSO-WOAH-GS-093` — WOAH 93rd General Session of the World Assembly of Delegates — `GOVERNANCE_ASSEMBLY_SESSION`
- `WSO-FIS-NP-BUDGET-2083` — Nepal Federal Budget 2083/84 — presentation — `FISCAL_POLICY_PROCESS`

## Source changes
- added `WSSRC-INT-034` — UNODA BWC 2026 past-meeting archive — canonical dependency count 1;
- `WSSRC-INT-033` — WOAH final report: dependency count 1 → 2;
- `WSSRC-FIS-026` — Nepal constitutional budget-date authority: dependency count 1 → 2;
- `WSSRC-FIS-027` remains 0: it is supporting completion/publication evidence, not primary legal-date authority;
- no other pre-existing source object changes.

## Analysis readiness after canonical admission
- eligible completed occurrences: **12**;
- reviewed occurrences: **8**;
- reviewed event-type diversity: **7**;
- broad state: **`READY_FOR_CONTROLLED_EXPANSION`**.

This tranche deliberately creates new analytical choice. It does not review the three new anchors and does not promote the previously held Bank of Canada event merely because it was the prior final backlog item.

## Temporal and ontology invariants
- BWC split daily programme hours are not converted into a continuous canonical timestamp;
- WOAH remains `AGRICULTURE_FOOD`; One Health/biosecurity relationships remain cross-domain analytical context;
- Nepal remains source-native `15 Jestha 2083` with `UNRESOLVED_AUTHORITATIVE_CONVERSION` and no fabricated Gregorian or UTC timestamp;
- the Nepal Ministry of Finance CMS publication time is not treated as the constitutional presentation time;
- no new event series or canonical schema vocabulary is introduced;
- all 678 pre-existing canonical records remain byte-structurally unchanged inside the JSON dataset;
- all 48 pre-existing change-ledger rows remain unchanged;
- biosecurity overlay semantic content remains unchanged; only version/checkpoint advances;
- automatic canonical commit remains OFF; Google Calendar writes remain OFF.

## Protected-file SHA-256 before transaction
- canonical schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- monitor expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor operations policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`
- Analysis schema: `ea5acce7848b85febec2cf2f7558a68891ab4973f6b7ad241c890bc93eba94a0`
- Analysis reviews: `5ee732d2bc4ecddcebeb3577d22745a6f6daeccd5c87c370826384b17441fd2b`
- Analysis evidence: `d038b866c30109c7272fa1424e74685086edd395d93f2f5c470f14c19857c600`

## Validator warnings
- WSO-EL-A-0012: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0009: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0010: timed event missing start_utc (legacy/backfill candidate)
