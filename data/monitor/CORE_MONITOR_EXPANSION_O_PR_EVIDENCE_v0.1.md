# WORLD SIGNALS — Core monitor expansion O final validation evidence v0.1

**Base main:** `03b6255cdc121062816b39073e3c88dd049db29c`  
**Durable branch head after reviewed transaction:** `2c0b332ea8e78f4d6470b254cabba3a663d46693`  

## Live identity research

GitHub Actions run `33969711355`: **SUCCESS**.

- official ONS upcoming RSS fetched to exhaustion in four pages;
- 343 upcoming items observed at that run;
- 19/19 configured canonical ONS occurrences matched exactly once by explicit feed title;
- 19/19 feed datetimes matched canonical UTC timestamps;
- no fuzzy matching used.

## Exact transaction simulation

GitHub Actions run `33970301870`: **SUCCESS**.

Pre-state:

- canonical v0.28 / 674;
- sources v1.69 / 233;
- monitor expectations v0.7 / 6 routes;
- 367 tests PASS, 13 skipped;
- registry validator, Python compile checks, browser JavaScript checks and static build PASS.

Ephemeral post-state:

- canonical v0.28 / 674 unchanged;
- sources v1.70 / 233;
- monitor expectations v0.8 / 7 routes;
- 367 tests PASS, 14 skipped;
- static build PASS with seven configured live monitor routes;
- live ONS comparison: 343 upcoming items / four pages / 19 no-change observations / zero review candidates;
- generated transaction boundary exactly five files;
- ephemeral changes discarded.

## Reviewed apply

GitHub Actions run `33970396136`: **SUCCESS**.

- reran pre-state checks;
- reran exact post-state validation and live ONS comparison;
- committed the reviewed post-state to the feature branch;
- removed all temporary probe, patch and transaction workflows/triggers in the same commit.

Permanent pull-request CI should validate the durable head after PR creation.
