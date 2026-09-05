# WORLD SIGNALS — Priority-region historical anchors R transaction audit v0.1

**Transaction date:** 2026-09-06  
**Post-state:** canonical **v0.29 / 678**; sources **v1.71 / 236**; change ledger **v0.16 / 48**; biosecurity overlay **v0.4 @ v0.29/678**

## Added completed historical anchors
- `WSO-HIST-R-IN-GDP-2026Q1` — India GDP — Q1 FY2026-27 quarterly estimate — South Asia — `DATA_RELEASE`
- `WSO-HIST-R-ID-BI-202608` — Bank Indonesia Board of Governors meeting — August 2026 — Southeast Asia — `MONETARY_POLICY_DECISION_PROCESS`
- `WSO-HIST-R-EG-CBE-20260820` — Central Bank of Egypt MPC decision — 20 August 2026 — Africa — `MONETARY_POLICY_DECISION`
- `WSO-HIST-R-AR-CPI-202607` — Argentina national CPI — July 2026 — Latin America — `OFFICIAL_STATISTICAL_RELEASE`

## Added completion/outcome source surfaces
- `WSSRC-MAC-028` — GDP press-note publication / completed-release verification
- `WSSRC-REG-012` — Monetary-policy decision press releases / completed-meeting verification
- `WSSRC-REG2-008` — Consumer Price Index technical reports / completed-release verification

## Existing schedule-source dependency updates
- `WSSRC-MAC-017`: 17 → 18
- `WSSRC-REG-004`: 4 → 5
- `WSSRC-REGJ-005`: 3 → 4
- `WSSRC-REG2-006`: 4 → 5

No other pre-existing source object changes.

## Analysis readiness after canonical admission
- Africa: 1 completed; ELIGIBLE_UNREVIEWED
- South Asia: 1 completed; ELIGIBLE_UNREVIEWED
- Southeast Asia: 1 completed; ELIGIBLE_UNREVIEWED
- Latin America: 1 completed; ELIGIBLE_UNREVIEWED

Broad population state: **`BLOCKED_PRIORITY_REGION_REVIEW_GAP`**.

This is intentionally still blocked: R supplies canonical anchors but does not add reviewed Analysis packets.

## Invariants
- all 674 pre-existing canonical records unchanged;
- all 44 pre-existing change-ledger records unchanged;
- no new event series;
- completion is supported by first-party post-event evidence, never elapsed time alone;
- BI remains one two-day decision-process occurrence rather than a duplicate meeting + announcement pair;
- no clock time is inferred for BI, CBE or INDEC;
- MoSPI 16:00 local is occurrence-specific first-party evidence only, not a series-wide rule;
- biosecurity semantic membership unchanged; overlay advances checkpoint only;
- automatic canonical commit OFF; Google Calendar writes OFF.

## Protected-file SHA-256 before transaction
- canonical schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- monitor expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor operations policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`

## Validator warnings
- WSO-EL-A-0012: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0009: timed event missing start_utc (legacy/backfill candidate)
- WSO-REG-A-0010: timed event missing start_utc (legacy/backfill candidate)
