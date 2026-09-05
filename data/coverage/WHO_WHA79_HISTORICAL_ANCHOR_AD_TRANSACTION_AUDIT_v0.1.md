# WORLD SIGNALS — WHO WHA79 historical anchor AD transaction audit v0.1

**Transaction date:** 2026-09-06  
**Canonical post-state:** v0.33 / 683  
**Source registry post-state:** v1.74 / 240  
**Change ledger post-state:** v0.20 / 55  
**Analysis:** schema v0.3; reviews v0.8 / 12; evidence v0.8 / 44 — unchanged

## Added historical anchor

- `WSO-HEALTH-WHA-079` — 79th World Health Assembly
- series `WSER-HEALTH-WHA` — reused
- primary schedule source `WSSRC-HEALTH-001` — reused
- supporting completion source `WSSRC-HEALTH-006` — new, supporting-only
- category `HEALTH_BIOSECURITY`
- event type `HEALTH_GOVERNANCE_EVENT`
- local date range `2026-05-18` to `2026-05-23`, `Europe/Zurich`
- UTC endpoints intentionally null; the 09:00 opening-session time is not the whole Assembly timestamp
- lifecycle `COMPLETED`, certainty `CONFIRMED`
- completion established from WHO first-party archive/closing evidence, not elapsed time

## Source mutation scope

- `WSSRC-HEALTH-001.canonical_dependency_count`: 6 → 7
- actual canonical primary dependencies for `WSSRC-HEALTH-001`: 7
- `WSSRC-HEALTH-006` added with canonical dependency count 0
- `WSSRC-HEALTH-006` primary canonical dependencies: 0
- supporting source inherits WHO manual-information / rights-held automation posture and has no forward monitor endpoint

## Population effect

- completed Analysis-eligible occurrences: 16
- reviewed completed occurrences: 12
- `HEALTH_BIOSECURITY` is now present in completed anchors
- `HEALTH_GOVERNANCE_EVENT` is now present in completed event types
- WHO-only institutional concentration is not claimed repaired
- no Analysis review is added by AD

## Protected SHA-256

- canonical_schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- monitor_expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor_operations_policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`
- analysis_schema: `0e734ab0fb8b3ac427f3dc8e5561d80068e278d5df1217b4a54ba58cc718176a`
- analysis_reviews: `406c2debe44b6ad89789e47242a0c38c8d2985f0c7fe2bfa329512437865a8b5`
- analysis_evidence: `523e7c402e92fb619c5dba99a807c74b6e3b05de4b4bcd690e114f74b618942e`

Biosecurity overlay semantic SHA-256: `03b32278ada1b886131fd4fa938377a9b82bdaa1989467216f6e777892fd173d`

## Discipline

- no new series
- primary schedule provenance and supporting outcome provenance remain distinct
- no PABS/IGWG completion inference
- no Analysis mutation
- no monitor-configuration mutation
- no Calendar mutation
- no completion inference from elapsed time
- no conversion of an opening-session clock into a synthetic whole-event timestamp
