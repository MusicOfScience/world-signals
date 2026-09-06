# WORLD SIGNALS — Japan FIES Live→Analysis AZ transaction audit v0.1

## Transaction identity

- Stage: AZ — first bounded production Live Intelligence → Analysis input.
- Exact base `main`: `bc8e588624e8a76f6847d7c80aef7e7fa5ecafa9`.
- Branch: `feature/post-ay-first-live-analysis-link-az`.
- Canonical anchor: `WSO-MAC-B-0041`.
- Live observation: `WSLI-MAC-JPN-FIES-202607-001`.
- Analysis review: `WSAN-JP-FIES-202607-001`.
- Reviewed target commit: `0055902779a90d3d8c81b48a403c4ce701024c6b`.
- Transaction-workflow self-removal commit: `a70969e` (full commit is the descendant branch head created by the successful transaction run).
- Merge policy: manual PR merge only; no auto-merge authority.

## Preflight history

### Descendant test repair

The first ephemeral AZ materialisation exposed a stale Y historical-audit regression: the historical `QUEUE_COMPLETION_IS_NOT_THE_OBJECTIVE` finding was incorrectly required to remain a live descendant finding even when a later legitimate review reduced the current completed/unreviewed frontier to zero.

The repair is test-only. Y's frozen checkpoint and methodological warning remain frozen. The live Y audit code is unchanged and descendants may legitimately exhaust a historical frontier without redefining queue completion as a research objective.

### Preflight v2 — fail closed

Workflow run `34023908427` reached a fully valid ephemeral AZ state: the untouched descendant, AZ materialisation, validators, full regression suite and static build passed. It then failed in the harness's mutation-boundary proof because the harness duplicated an incomplete `live_inputs.analysis_sections` list rather than reading the reviewed payload. The fail-safe cleanup hard-restored the branch and self-removed the temporary workflow. No AZ governed target write survived.

### Preflight v3 — success

Workflow run `34024297041` corrected only that proof by comparing the materialised `live_inputs` directly with `JAPAN_FIES_LIVE_ANALYSIS_AZ_PAYLOAD_v0.1.json`. It passed:

- exact post-AY ancestry;
- ephemeral AZ materialisation;
- Canonical Registry, Live Intelligence and Analysis validators;
- exact payload identity;
- exactly one production Live input;
- the eight-file governed mutation boundary;
- protected upstream hashes; and
- temporary-workflow self-removal.

## Controlled transaction history

### Transaction run 1 — harness-only failure, no target commit

Workflow run `34024343324` passed exact ancestry, AZ materialisation, all three validators, the full 794-test descendant suite (`39` skipped), Python compilation, JavaScript syntax checks and the static-site build. It then failed on `git checkout -- docs` because `docs/` is generated untracked build output rather than a tracked repository path.

This failure occurred before the transaction's mutation proof or target commit. It changed no governed repository state. It was classified as a transaction-harness cleanup defect, not an AZ data, schema or analysis failure.

### Transaction run 2 — success

Workflow run `34024441410` replaced the invalid tracked-path restore with explicit deletion of generated `docs/` output and reran the complete transaction from the same exact post-AY base lineage.

The successful run proved:

- `origin/main == bc8e588624e8a76f6847d7c80aef7e7fa5ecafa9` and the branch merge-base was exactly that SHA;
- AZ materialisation succeeded;
- Canonical validation passed for 688 occurrences;
- Live Intelligence validation passed at schema v0.4 with 4 observations and 6 evidence rows;
- Analysis validation passed at schema v0.6 with 21 reviews and 95 evidence rows;
- the full repository suite passed: 794 tests, 39 skipped;
- Python compilation, JavaScript checks and static-site build passed;
- generated build output was removed before mutation accounting;
- production Live input count was exactly 1;
- `maximum_production_live_inputs == 1` and `maximum_live_inputs_per_review == 1`;
- public Live-input projection remained closed;
- the Japan review's Live input exactly matched the reviewed AZ payload;
- `what_moved` remained empty and `canonical_release_utc` remained null;
- `EXACT_TIMESTAMP_SERIES` remained 0; and
- the only uncommitted governed target mutations were the eight authorised files below.

The target commit was then created as `0055902779a90d3d8c81b48a403c4ce701024c6b`, changing exactly eight files (405 insertions, 33 deletions). The temporary transaction workflow was removed in the following commit and the branch push succeeded.

## Exact governed target mutations

1. `PROJECT_STATUS.md`
2. `ROADMAP.md`
3. `data/live_intelligence/schema.json`
4. `data/live_intelligence/observations.json`
5. `data/live_intelligence/evidence_registry.json`
6. `data/analysis/schema.json`
7. `data/analysis/event_reviews.json`
8. `data/analysis/evidence_registry.json`

## Protected layers

The transaction proved byte-level immutability against its transaction HEAD for:

- `data/canonical/registry.json`
- `data/canonical/schema.json`
- `data/sources/registry.json`
- `data/changes/ledger.json`
- `data/coverage/biosecurity_overlay.json`
- `data/monitor/expectations.json`
- `data/monitor/operations_policy.json`

Therefore AZ does not mutate Canonical identity/timing/lifecycle, Source Registry governance, Change Ledger history, biosecurity overlay semantics or Monitor configuration/policy.

## Reviewed post-AZ state

- Canonical Registry: v0.38 / 688 occurrences — unchanged.
- Live Intelligence: schema v0.4 / 4 observations / 6 evidence rows.
- Live population: `CONTROLLED_CANONICAL_LINKED_ECONOMIC_SPECIMEN`.
- Analysis: schema v0.6 / reviews v0.17 with 21 reviews / evidence v0.17 with 95 rows.
- Production Live→Analysis inputs: exactly 1.
- Exact-timestamp market series: 0.
- Public Live observation projection: closed.
- Public Live-input projection: closed.
- Automatic ingestion, automatic Canonical commit and Google Calendar writes: not opened by AZ.
- Further production Live-input population: requires a new pressure audit; AZ does not establish an automatic expansion rule.

## Interpretation boundary

AZ is a bounded cross-layer specimen, not a general opening of the Live→Analysis pipeline. The selected Live observation is factual input tied to the same existing Canonical occurrence as the Analysis review. Live evidence is not transitively promoted into Analysis evidence. The Statistics Bureau CPI-base revision context is preserved as a data-vintage caveat rather than collapsed into a synthetic prior Live revision history. No market response or Bank of Japan policy causality is manufactured.

## Remaining gate

After this audit file is committed, the branch must receive a fresh final-head validation covering exact ancestry, validators, full regression suite, compilation, browser checks, static build, final governed state, protected-layer immutability, permanent diff audit and temporary-workflow self-removal. Only after that passes may one ordinary pull request be opened for manual merge.
