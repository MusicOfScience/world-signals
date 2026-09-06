# WORLD SIGNALS — RBA Financial Stability Analysis AM transaction audit v0.1

**Reference date:** 2026-09-06
**Exact base main:** `fd8b69b5edf95a1c7d14c1e236e1a2e8891c74f9`
**Architecture layer:** Analysis only

## Mutation

- Analysis reviews: **v0.10 / 14 → v0.11 / 15**
- Analysis evidence: **v0.10 / 54 → v0.11 / 59**
- added `WSAN-AU-RBA-FSR-20260319-001` for canonical `WSO-FIN-B-0004`
- Analysis schema remains **v0.4**
- production `EXACT_TIMESTAMP_SERIES` remains **0**

## Analytical boundary

- October 2025 official guidance remains baseline context, not March consensus.
- surprise remains `NOT_ESTABLISHED`.
- `what_moved` remains empty: same-session market moves are not attributed to the FSR.
- connection is `COMMON_DRIVER_CONTEXT` / `NOT_A_CAUSAL_CLAIM`.
- prospective financial-stability transmission channels remain watch items, not publication-caused outcomes.

## Protected-state hash audit

Protected upstream/configuration datasets unchanged: **True**

```json
{
  "before": {
    "canonical_registry": "5f5fb108e2bd74cce7c372dd1d29d07702a7e597789c09608c8fa492f453f451",
    "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "source_registry": "a3d611b8807c20e663549f3fa2fa3f906eb86c39497941048002484784059f3e",
    "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "biosecurity_overlay": "9d9302e2ee570838e7cf00e40acaa9f675e12ab1e5ebe67d3802e0d6f1950fdb",
    "monitor_expectations": "8ae28b966c76cd46e4ad06a07b270d99f358a6c18901c1e699a9bca4362557c4",
    "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf"
  },
  "after": {
    "canonical_registry": "5f5fb108e2bd74cce7c372dd1d29d07702a7e597789c09608c8fa492f453f451",
    "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "source_registry": "a3d611b8807c20e663549f3fa2fa3f906eb86c39497941048002484784059f3e",
    "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "biosecurity_overlay": "9d9302e2ee570838e7cf00e40acaa9f675e12ab1e5ebe67d3802e0d6f1950fdb",
    "monitor_expectations": "8ae28b966c76cd46e4ad06a07b270d99f358a6c18901c1e699a9bca4362557c4",
    "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf"
  }
}
```

## Deliberate non-actions

- no canonical registry/schema mutation
- no source-registry mutation
- no change-ledger mutation
- no biosecurity-overlay mutation
- no monitor configuration/policy mutation
- no Analysis schema mutation
- no exact market-data ingestion
- no Calendar write
- no auto-merge
