# WORLD SIGNALS — AG transaction audit

- tranche: `SOUTH_KOREA_LOCAL_ELECTION_HISTORICAL_ANCHOR_AG`
- committed_at: `2026-09-06T08:41:41+10:00`
- occurrence: `WSO-EL-KR-LGE-20260603`
- new series: `WSER-EL-KR-LGE`
- new official source: `WSSRC-EL-KR-001`
- event taxonomy: reused `ELECTIONS_GOVERNANCE` / `local_government_election` / `ELECTION_MILESTONE`; no schema change
- canonical post-state: `v0.36 / 686`
- source post-state: `v1.77 / 241`
- ledger post-state: `v0.23 / 58`
- overlay post-state: `v0.11 @ canonical v0.36 / 686`
- completed Analysis population: `19`
- reviewed post-event population: `12`
- Analysis mutation: `none`
- timing guardrail: election day is `2026-06-03` in `Asia/Seoul` with CIVIL_DATE/DAY semantics and no synthetic UTC instant
- process guardrail: early voting and 06:00–18:00 polling hours remain supporting detail, not canonical clock boundaries
- result guardrail: nationwide simultaneous local elections are not collapsed into one national winner, vote share or mandate
- completion guardrail: current first-party NEC winner-pledge material; elapsed time alone is insufficient
- automation guardrail: curated factual provenance permitted; production monitoring remains endpoint-review/manual-recheck only
- PR #40: untouched

## Protected SHA-256

- canonical_schema: `0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd`
- monitor_expectations: `786d4bbe60431580a03a14bce91dd20554196f19fd5c3855966fc5931b40ddce`
- monitor_operations_policy: `26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0`
- analysis_schema: `0e734ab0fb8b3ac427f3dc8e5561d80068e278d5df1217b4a54ba58cc718176a`
- analysis_reviews: `406c2debe44b6ad89789e47242a0c38c8d2985f0c7fe2bfa329512437865a8b5`
- analysis_evidence: `523e7c402e92fb619c5dba99a807c74b6e3b05de4b4bcd690e114f74b618942e`
