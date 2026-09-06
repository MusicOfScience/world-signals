# WORLD SIGNALS — post-AX pressure audit AY v0.1

**Exact post-#79 main:** `0a7608ab56116d0f65ffd1492a3da87bcbf35f47`  
**Reference date:** 2026-09-06  
**Decision class:** architecture / contract pressure; no production population

## Verified starting checkpoint

PR #79 (`Live Intelligence AX: add DRC evolving-state story specimen`) is merged. The merge commit is `0a7608ab56116d0f65ffd1492a3da87bcbf35f47` with parents:

1. pre-AX main `721206169033eb0ceb695075d44fb38e7fa2edc3`;
2. AX head `6c6fd7f6ed189f47d001adfad315c651f9538eda`.

Ordinary pull-request CI on the AX head passed in run `34020627789`; post-merge main CI passed in run `34020733267`.

Governed state at this checkpoint:

- Canonical schema `v0.52`;
- Canonical Registry `v0.38 / 688`;
- Source Registry `v1.80 / 243`;
- reviewed Change Ledger `v0.24 / 59`;
- biosecurity overlay `v0.13 @ Canonical v0.38 / 688`;
- monitor expectations `v0.10 / 8 configured adapters`;
- monitor operations policy `v0.1`;
- Live Intelligence schema `v0.3`;
- Live Intelligence `3` internal observations / `4` evidence rows / public observations `0`;
- Analysis schema `v0.4`;
- Analysis `v0.16 / 20 reviews / 91 evidence / 18 reviewed event types`;
- production `EXACT_TIMESTAMP_SERIES = 0`.

The three Live observations remain:

1. Nepal Bhote Koshi / Rasuwa flood physical shock;
2. DRC Bundibugyo outbreak state as of 26 August 2026;
3. DRC Bundibugyo outbreak state as of 30 August 2026.

The DRC observations share `WSSTORY-HEALTH-COD-BVD-2026`; the later snapshot uses `state_update_of_observation_id`, not `revision_of_observation_id`.

## Pressure question

After AX has proved repeated as-of state, what creates the highest marginal architectural value now?

The immediate candidate is a prospective **Live Intelligence → Analysis** relationship. The question is not whether Analysis can merely copy a Live observation. It is whether a reviewed Analysis packet can select an immutable upstream factual observation as input while preserving all layer boundaries, as-of provenance and existing analytical evidence semantics.

## Candidate comparison

### A. Directly link Nepal or DRC into a production Analysis review — DEFER

This is superficially attractive because the Live specimens already exist. It is not yet a clean production case.

All three Live observations deliberately have zero Canonical links. Current Analysis requires every reviewed post-event packet to resolve to a real Canonical occurrence. Forcing Nepal or DRC into production Analysis now would therefore require one of three bad moves:

- inventing a Canonical occurrence solely to satisfy Analysis referential integrity;
- weakening the existing Analysis canonical-anchor rule merely because the first Live specimens are unscheduled;
- attaching the Live facts to an unrelated completed Canonical occurrence as context and pretending that this proves a meaningful production bridge.

None is justified. The absence of a natural Canonical anchor is informative contract pressure, not a defect in the Live observations.

### B. Japan Family Income and Expenditure Survey, July 2026 — HOLD, STRONG FUTURE CANDIDATE

`WSO-MAC-B-0041` remains the sole completed/unreviewed Canonical occurrence and is a genuinely strong future bridge candidate.

Fresh 6 September verification confirms the official Statistics Bureau release of 4 September 2026:

- average monthly consumption expenditure for two-or-more-person households: `301,245 yen`;
- nominal year-on-year: `-1.5%`;
- real year-on-year: `-3.6%`;
- seasonally adjusted real month-on-month: `+0.5%`.

Primary official sources:

- `https://www.stat.go.jp/english/data/kakei/156.htm`
- `https://www.stat.go.jp/data/kakei/`

The Statistics Bureau also explicitly records that the 4 September household-survey publication retrospectively revised real-change figures for April-June 2026 following the CPI transition to the 2025 base. The CPI authority states that the 2025-base CPI began publication in August 2026 and that historical data were recalculated/linked under the new base while published rates of change for each base period retain their own treatment.

Primary official CPI source:

- `https://www.stat.go.jp/english/data/cpi/2025plan.html`

Reuters reported contemporaneous expectations of about `-1.6%` y/y and `+2.6%` m/m, making the July result a clear negative consumption surprise:

- `https://www.reuters.com/world/asia-pacific/japan-year-on-year-household-spending-drops-8-straight-months-2026-09-03/`

Japan is nevertheless **not selected for AY**. Using it now would conflate too many firsts in one transaction:

1. first scheduled/economic-data Live observation;
2. first Live observation with a Canonical relationship;
3. first production Live → Analysis input;
4. a new Analysis review;
5. a live statistical-vintage/rebasing issue.

Those are all valuable, but combining them would make it harder to identify which contract failed if validation exposed a problem.

### C. Prospective bridge contract with zero production linkage — SELECT

This is the highest-value next step.

AY should establish the executable grammar and fail-closed validator behavior for future Live inputs while leaving every production Analysis review unchanged.

The contract should prove:

- Analysis selects **specific immutable `observation_id` values**, never `story_id`, “latest”, or automatic story expansion;
- Live inputs occupy a dedicated `live_inputs` field and are not Analysis evidence rows;
- each input records only the Live observation identity, reviewed input role(s), and the Analysis section(s) it supports;
- Live evidence does not become Analysis evidence transitively merely because its observation is selected;
- the selected observation must exist in the supplied Live dataset;
- `analysis_as_of_utc` cannot predate the selected observation's `observed_at_utc`;
- one Live observation may support multiple analyses; the bridge is many-to-many by reference, not by ownership;
- Analysis cannot mutate, revise or relabel the upstream Live observation;
- a developing story is preserved snapshot-by-snapshot: if Analysis needs history, it must name the snapshots it uses rather than asking the bridge for “the latest story state”;
- public projection of Live inputs remains closed until separately audited;
- no production review may contain `live_inputs` in AY.

This creates a real bridge contract without pretending there is already a justified production relationship.

### D. Fourth Live observation — HOLD

AX deliberately capped production at three observations / four evidence rows pending another audit. No current candidate creates more contract pressure than the bridge boundary itself.

A fourth observation would increase sample breadth but would not answer how Live Intelligence actually becomes a governed factual input to downstream interpretation.

### E. Monitor/source-governance expansion — IMPORTANT, NOT SELECTED

The monitor cohort remains deliberately narrow at eight configured adapters. Source rights, endpoint maturity and governance backlogs remain real operational pressures, but no adjacent route identified in this audit outranks the architectural discontinuity between the now-populated Live layer and Analysis.

Coverage diagnostics remain prompts, not quotas.

### F. Market-data rights/provenance architecture — IMPORTANT, DEFER

Production `EXACT_TIMESTAMP_SERIES` remains zero by design. Factual market-data rights, access and redistribution provenance remain unresolved enough that a market-observation bridge would introduce a second major rights architecture into AY.

Do not use market data to make the bridge look more realistic before the reference contract itself is stable.

## AY decision

**Establish a production-closed Live Intelligence → Analysis bridge foundation. Do not add a fourth Live observation. Do not add a twenty-first Analysis review. Do not consume Japan household spending.**

The target is Analysis schema `v0.5` with explicit `live_input_policy`, validator support, static-build wiring and regression tests. The production datasets remain:

- Live Intelligence `v0.3 / 3 observations / 4 evidence`;
- Analysis reviews `v0.16 / 20`;
- Analysis evidence `v0.16 / 91`.

Production `live_inputs` count remains exactly `0`.

## Required bridge semantics

### Identity

A Live input is selected by `observation_id` only. A story grouping key is not a substitute for observation identity.

No selector grammar for `story_id`, `latest`, current-state lookup or automatic descendant expansion is admitted in AY.

### Input object

The prospective object is deliberately narrow:

```json
{
  "observation_id": "WSLI-...",
  "roles": ["FACTUAL_INPUT"],
  "analysis_sections": ["what_happened"]
}
```

The bridge must reject copied Live headline/summary/state/evidence fields. Analysis dereferences the immutable Live record; it does not create a shadow copy.

### Analysis evidence remains separate

`data/analysis/evidence_registry.json` remains the store for sources directly reviewed as Analysis evidence. A Live observation reference is an upstream factual input identity, not a hidden shortcut for adding all of that observation's evidence rows to Analysis.

### Time

The observation's own `observed_at_utc`, source-publication time, event time and state-as-of semantics remain owned by Live Intelligence. AY adds only one downstream temporal guard: an Analysis packet cannot claim to have selected a Live observation before WORLD SIGNALS had observed it.

### Evolving stories

The DRC pair is the critical regression case. The bridge may select either snapshot when only that snapshot is relevant. If an analysis needs evolution across time, it must explicitly select both observation identities. AY must not infer a story history from the later row or silently replace the earlier row with the later state.

### Public surface

AY keeps Live input projection closed. The public Analysis projection must not expose internal `live_inputs` merely because the validator understands them prospectively.

### Production gate

The schema must explicitly remain in `FOUNDATION_ONLY_NO_PRODUCTION_LINKS` state with production Live inputs disabled. A later pressure audit is required to open the gate and select the first real production relationship.

## Why this is not needless abstraction

The bridge already exists conceptually in the Charter and in Analysis's declared upstream layers. What does not exist is executable identity/provenance grammar.

Adding a minimal closed contract now reduces risk in the first real case because it separates two questions:

1. **Can the repository safely express and validate a Live input relationship?** — AY.
2. **Which real event should first exercise that relationship in production?** — later pressure audit.

That ordering is consistent with the project's established method: architecture and invariants before population.

## Protected state for AY

AY must not modify:

- `data/canonical/registry.json`;
- `data/canonical/schema.json`;
- `data/sources/registry.json`;
- `data/changes/ledger.json`;
- `data/monitor/expectations.json`;
- `data/monitor/operations_policy.json`;
- `data/live_intelligence/schema.json`;
- `data/live_intelligence/observations.json`;
- `data/live_intelligence/evidence_registry.json`;
- `data/analysis/event_reviews.json`;
- `data/analysis/evidence_registry.json`.

Only the Analysis schema/validator/build contract, tests and AY audit/recovery documentation may change.

## Next pressure after AY

After AY merges, run another pressure audit before opening production Live inputs.

Japan household spending is likely to be a strong candidate because a single scheduled release can naturally bind:

`Canonical occurrence → factual Live outcome → reviewed Analysis`

while also exposing real statistical-vintage pressure. That is **not** pre-authorisation. A different event should win if it offers cleaner or more consequential marginal contract value.