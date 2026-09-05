# WORLD SIGNALS — Japan sovereign financing analysis AA transaction audit v0.1

**Transaction date:** 2026-09-06  
**Canonical checkpoint:** v0.31 / 681 — unchanged  
**Analysis post-state:** schema v0.3; reviews v0.8 / 12; evidence v0.8 / 44

## Added reviewed specimen

- `WSAN-JP-JGB30-20260903-001` — Japan 30-year JGB auction — `FISCAL_FINANCING_EVENT`.
- official auction mechanics are preserved separately from secondary-market yields.
- surprise is `NO_CLEAR_SURPRISE`; previous-auction metrics are not promoted into consensus.
- source-reported 30-year yield movement is -9.5bp on the day to 4.070%, while the same source says the yield was unchanged after the auction.
- connection remains `OBSERVATION_CONTEXT` / `NOT_A_CAUSAL_CLAIM`.
- exact timestamp precision is deliberately not fabricated; canonical UTC remains unresolved.
- global capital reallocation remains `PLAUSIBLE_WATCH_ITEM`, not a one-auction effect.

## Schema decision

- Analysis schema remains v0.3. Existing semantics already support the sovereign-financing case.

## Readiness

- eligible completed occurrences: 14
- reviewed occurrences: 12
- reviewed event-type diversity: 11
- reviewed East Asia occurrences: 1
- broad state: `READY_FOR_CONTROLLED_EXPANSION`

## Remaining eligible unreviewed

- `WSO-MAC-B-0041`
- `WSO-ddb70f8ff05a58fb`

## Protected SHA-256

- canonical registry: `ac95fba1f02c183bbbe8ff5b0df34dec0f44f6aea1728298bc49793f254676da`
- canonical schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- source registry: `4af1acca24ed6fae811c7c134e190768f9f5b881bc82f53ea5b8c69a75565a84`
- change ledger: `d17a531f5be880da73c60142cfad3969b33a2a6591b22a85f5eab9abc0d5139e`
- biosecurity overlay: `76cebee8da0eaaf9d71e73f238b93145dc5f612858e8ee4bc910f9563aa53f4b`
- monitor expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor operations policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`
- Analysis schema: `0e734ab0fb8b3ac427f3dc8e5561d80068e278d5df1217b4a54ba58cc718176a`

Canonical/source/ledger/overlay/monitor and Analysis-schema files were hashed before and after AA and must remain byte-identical.
