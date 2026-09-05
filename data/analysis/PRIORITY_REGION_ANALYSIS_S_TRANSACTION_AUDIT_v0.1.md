# WORLD SIGNALS — Priority-region Analysis S transaction audit v0.1

**Transaction date:** 2026-09-06  
**Canonical checkpoint:** v0.29 / 678 — unchanged  
**Analysis post-state:** reviews v0.3 / 6; evidence v0.3 / 14

## Added reviewed stress samples

- `WSAN-IN-GDP-2026Q1-001` — South Asia — India GDP — UPSIDE — one source-reported FX change+endpoint — LOW-confidence observed association.
- `WSAN-ID-BI-202608-001` — Southeast Asia — Bank Indonesia — NO_CLEAR_SURPRISE — no discrete market move promoted.
- `WSAN-EG-CBE-20260820-001` — Africa — Central Bank of Egypt — NO_CLEAR_SURPRISE — no discrete market move promoted.
- `WSAN-AR-CPI-202607-001` — Latin America — Argentina CPI — UPSIDE — no discrete market move promoted.

## Readiness result

Broad state: **`READY_FOR_CONTROLLED_EXPANSION`**.

This means only that the four priority geographic stress regions each contain at least one audited post-event sample and the minimum reviewed event-type-diversity gate is satisfied. It does **not** mean regional analytical completeness, representativeness or permission for uncontrolled population.

Priority-region state after S:

- Africa: 1 eligible / 1 reviewed / `REVIEWED_SAMPLE_PRESENT`
- South Asia: 1 eligible / 1 reviewed / `REVIEWED_SAMPLE_PRESENT`
- Southeast Asia: 1 eligible / 1 reviewed / `REVIEWED_SAMPLE_PRESENT`
- Latin America: 1 eligible / 1 reviewed / `REVIEWED_SAMPLE_PRESENT`

## Null-result discipline

Three of the four new packets intentionally carry `what_moved: []`. WORLD SIGNALS does not require a completed event to produce a discrete tradable reaction. India is the only new movement observation, and its GDP-to-rupee connection is LOW confidence because Reuters identifies RBI intervention and flow-related dollar supply as stronger immediate drivers.

## Protected upstream SHA-256

- canonical registry: `4f0ecfb36cf87cacba3c0e9ca24736bf9f37d497306aacbc0de3f6efab72a66b`
- canonical schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- source registry: `061711467b5f985a9bee8e90cd65b48e3329e407fd481f00beaaf69d91afa252`
- change ledger: `3003414a672af936fd29bcef3758c46233d2f3a75665df27c49257645b7b92a0`
- biosecurity overlay: `f6bd601e1c502732ac82f61f57f719fe7f2bf054a510eb9a58fe5a48f9a389a9`
- monitor expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor operations policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`
- Analysis schema: `ea5acce7848b85febec2cf2f7558a68891ab4973f6b7ad241c890bc93eba94a0`

All are required to remain byte-identical through S.

## Write gates

- automatic canonical commit: **OFF**
- Google Calendar write: **OFF**
- canonical mutation from Analysis: **PROHIBITED**
