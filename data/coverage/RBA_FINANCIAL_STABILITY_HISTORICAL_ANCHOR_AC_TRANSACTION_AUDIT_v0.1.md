# WORLD SIGNALS — RBA financial-stability historical anchor AC transaction audit v0.1

**Transaction date:** 2026-09-06  
**Canonical post-state:** v0.32 / 682  
**Source registry:** v1.73 / 239 — unchanged  
**Change ledger post-state:** v0.19 / 54  
**Analysis:** schema v0.3; reviews v0.8 / 12; evidence v0.8 / 44 — unchanged

## Added historical anchor

- `WSO-FIN-B-0004` — RBA Financial Stability Review — March 2026
- series `WSER-FIN-AU-RBA-FSR` — reused
- source `WSSRC-FIN-001` — reused; source registry byte-identical
- category `FINANCIAL_STABILITY_REGULATION`
- event type `FINANCIAL_STABILITY_REPORT`
- source-native time `2026-03-19T11:30:00` `Australia/Sydney` (AEDT)
- canonical UTC `2026-03-19T00:30:00Z`
- lifecycle `COMPLETED`, certainty `CONFIRMED`
- completion established by first-party RBA publication/release evidence, not elapsed time

## Population effect

- completed Analysis-eligible occurrences: 15
- reviewed completed occurrences: 12
- `FINANCIAL_STABILITY_REGULATION` is now present in completed anchors
- `FINANCIAL_STABILITY_REPORT` is now present in completed event types
- no Analysis review is added by AC

## Mutation boundary

Allowed production mutations:
1. `data/canonical/registry.json` — append one occurrence and bump checkpoint version/count
2. `data/changes/ledger.json` — append one reviewed historical-admission change
3. `data/coverage/biosecurity_overlay.json` — checkpoint/version metadata only; semantic payload unchanged
4. this generated transaction audit

Protected files remain byte-identical:
- canonical_schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- source_registry: `4af1acca24ed6fae811c7c134e190768f9f5b881bc82f53ea5b8c69a75565a84`
- monitor_expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor_operations_policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`
- analysis_schema: `0e734ab0fb8b3ac427f3dc8e5561d80068e278d5df1217b4a54ba58cc718176a`
- analysis_reviews: `406c2debe44b6ad89789e47242a0c38c8d2985f0c7fe2bfa329512437865a8b5`
- analysis_evidence: `523e7c402e92fb619c5dba99a807c74b6e3b05de4b4bcd690e114f74b618942e`

Biosecurity overlay semantic SHA-256: `03b32278ada1b886131fd4fa938377a9b82bdaa1989467216f6e777892fd173d`

## Discipline

- no new series
- no new source
- no source-registry rewrite for a legacy dependency counter
- no Analysis mutation
- no Calendar mutation
- no inference of completion from elapsed time
