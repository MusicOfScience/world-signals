# WORLD SIGNALS — Exact market measurement contract AK transaction audit v0.1

**Reference date:** 2026-09-06
**Exact base main:** `53e98457b70aa0dda4da490d5fe3210ce333ecae`
**Mutation class:** Analysis methodology/schema validation only

## Pre/post state

- canonical: v0.37 / 687 — unchanged
- sources: v1.78 / 242 — unchanged
- change ledger: v0.24 / 59 — unchanged
- biosecurity overlay: v0.12 @ canonical {'registry_version': '0.37', 'record_count': 687} — unchanged
- Analysis schema: **v0.3 → v0.4**
- Analysis reviews: v0.10 / 14 — unchanged
- Analysis evidence: v0.10 / 54 — unchanged
- existing market-movement rows: 10 — unchanged
- `EXACT_TIMESTAMP_SERIES` rows: **0 — unchanged at zero**

## Contract added

`EXACT_TIMESTAMP_SERIES` now requires independent pre/post values; an existing canonical `start_utc`; an `event_anchor_utc` equal to that canonical timestamp; explicit UTC observations ordered `before < anchor <= after`; market-series identity; valid IANA market timezone; series granularity; qualifying `MARKET_OBSERVATION` evidence; and a reviewed data-use basis whose public-projection permission is backed by referenced `MARKET_DATA_RIGHTS` evidence from a primary/official or market-data-provider record.

Non-exact movement rows may not carry exact-series-only fields. Exact market evidence cannot resolve or replace missing canonical timing. Exact canonical event timing never upgrades market-measurement precision.

## Rights boundary

The schema records that data existence, access authority and redistribution authority are separate. Exact observations stored in the public Analysis dataset require `public_projection_permitted=true` **and** a `data_use_evidence_ref` resolving to qualifying `MARKET_DATA_RIGHTS` evidence; a bare boolean or licensed internal access alone is insufficient.

## Protected-state hash audit

Protected datasets unchanged: **True**

```json
{
  "before": {
    "canonical registry": "5f5fb108e2bd74cce7c372dd1d29d07702a7e597789c09608c8fa492f453f451",
    "canonical schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "source registry": "a3d611b8807c20e663549f3fa2fa3f906eb86c39497941048002484784059f3e",
    "change ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "biosecurity overlay": "9d9302e2ee570838e7cf00e40acaa9f675e12ab1e5ebe67d3802e0d6f1950fdb",
    "monitor expectations": "786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce",
    "monitor operations policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "Analysis reviews": "ebfbefe19c0a54d67831abe56ebae8e513eee5228a48acc1c1f69923524149e8",
    "Analysis evidence": "0b50a9fa5ad23e9fb51a5900029ef661e55763014796db6992b67af66d780eba"
  },
  "after": {
    "canonical registry": "5f5fb108e2bd74cce7c372dd1d29d07702a7e597789c09608c8fa492f453f451",
    "canonical schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "source registry": "a3d611b8807c20e663549f3fa2fa3f906eb86c39497941048002484784059f3e",
    "change ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "biosecurity overlay": "9d9302e2ee570838e7cf00e40acaa9f675e12ab1e5ebe67d3802e0d6f1950fdb",
    "monitor expectations": "786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce",
    "monitor operations policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "Analysis reviews": "ebfbefe19c0a54d67831abe56ebae8e513eee5228a48acc1c1f69923524149e8",
    "Analysis evidence": "0b50a9fa5ad23e9fb51a5900029ef661e55763014796db6992b67af66d780eba"
  }
}
```

## Deliberate non-actions

- no canonical mutation
- no source-registry mutation
- no change-ledger mutation
- no overlay or monitor mutation
- no Analysis review/evidence population
- no exact market-data ingestion
- no Calendar write
- no market-structure historical backfill
- no auto-merge
