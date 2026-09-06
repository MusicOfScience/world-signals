# WORLD SIGNALS — RBA FSR monitor alignment AL transaction audit v0.1

**Reference date:** 2026-09-06
**Exact base main:** `72103267f90475b04c80129e03b41b605d4b7f58`
**Architecture layer:** Source/Change Monitor only

## Mutation

- monitor expectations: **v0.8 → v0.9**
- `RBA_FSR_RSS.canonical_occurrence_ids`: `['WSO-FIN-B-0001']` → `['WSO-FIN-B-0001', 'WSO-FIN-B-0004']`
- matching window, source identity, monitor role and automatic-commit prohibition: unchanged

## Regression contract

The official March 2026 RBA FSR item now resolves against `WSO-FIN-B-0004` as `RBA_PUBLICATION_ALREADY_REFLECTED` and generates no review candidate. A synthetic 1 October 2026 publication at the canonical clock time still resolves to `WSO-FIN-B-0001` and generates a non-automatic lifecycle review candidate, proving that adding the historical occurrence does not hijack the forward match.

## Protected-state hash audit

Protected datasets unchanged: **True**

```json
{
  "before": {
    "canonical_registry": "5f5fb108e2bd74cce7c372dd1d29d07702a7e597789c09608c8fa492f453f451",
    "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "source_registry": "a3d611b8807c20e663549f3fa2fa3f906eb86c39497941048002484784059f3e",
    "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "biosecurity_overlay": "9d9302e2ee570838e7cf00e40acaa9f675e12ab1e5ebe67d3802e0d6f1950fdb",
    "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf",
    "analysis_reviews": "ebfbefe19c0a54d67831abe56ebae8e513eee5228a48acc1c1f69923524149e8",
    "analysis_evidence": "0b50a9fa5ad23e9fb51a5900029ef661e55763014796db6992b67af66d780eba"
  },
  "after": {
    "canonical_registry": "5f5fb108e2bd74cce7c372dd1d29d07702a7e597789c09608c8fa492f453f451",
    "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "source_registry": "a3d611b8807c20e663549f3fa2fa3f906eb86c39497941048002484784059f3e",
    "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "biosecurity_overlay": "9d9302e2ee570838e7cf00e40acaa9f675e12ab1e5ebe67d3802e0d6f1950fdb",
    "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf",
    "analysis_reviews": "ebfbefe19c0a54d67831abe56ebae8e513eee5228a48acc1c1f69923524149e8",
    "analysis_evidence": "0b50a9fa5ad23e9fb51a5900029ef661e55763014796db6992b67af66d780eba"
  }
}
```

## Deliberate non-actions

- no canonical registry/schema mutation
- no source-registry mutation
- no change-ledger mutation
- no biosecurity-overlay mutation
- no monitor-operations-policy mutation
- no Analysis schema/review/evidence mutation
- no exact market-data ingestion
- no Calendar write
- no dynamic all-series monitor-scope expansion
- no auto-merge
