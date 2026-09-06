# WORLD SIGNALS — post-AY pressure audit AZ v0.1

**Reference date:** 2026-09-06  
**Exact post-#80 main:** `bc8e588624e8a76f6847d7c80aef7e7fa5ecafa9`

## Verified starting state

PR #80 / AY is merged. Main preserves Canonical v0.38 / 688, Source Registry v1.80 / 243, Change Ledger v0.24 / 59, monitor expectations v0.10 / 8 adapters, Live Intelligence v0.3 / 3 observations / 4 evidence rows, and Analysis v0.16 / 20 reviews / 91 evidence rows with schema v0.5. Production `live_inputs` and `EXACT_TIMESTAMP_SERIES` are both zero.

AY established a prospective Live Intelligence → Analysis grammar but intentionally left production population closed. It requires immutable `observation_id` selection, no story/latest selector, no transitive Live-evidence migration, no upstream Live mutation, explicit snapshot selection for evolving stories, and another pressure audit before the first real relationship.

## Competing pressures

### 1. Populate the new bridge with Nepal or DRC

**Reject for now.**

All three existing Live observations deliberately have zero Canonical links. The mature Analysis layer requires every reviewed packet to resolve to a real Canonical occurrence. Retrofitting a Canonical anchor merely to exercise the bridge would reverse the Live contract that unscheduled observations may legitimately remain non-Canonical and would create identity work not justified by the source facts.

### 2. Add another DRC evolving-state snapshot

**Reject for now.**

AX already proved state evolution ≠ revision, civil-date `state_as_of`, manual story identity and explicit state-update lineage. Another snapshot currently adds less contract pressure than using the downstream bridge AY created.

### 3. Broaden Monitor/source or geographic coverage

**Hold, not dismiss.**

Monitor/source governance and international coverage remain continuing pressures. They are not acute defects at the post-AY checkpoint. Coverage diagnostics remain prompts rather than quotas; no weak population is justified merely to flatten a distribution.

### 4. Populate a new Live class only

A controlled scheduled economic-data observation would exercise a new Live class and Canonical linkage. On its own, however, this would stop immediately before the bridge pressure AY was designed to test.

### 5. Japan July 2026 Family Income and Expenditure Survey as one bounded cross-layer specimen

**Selected.**

`WSO-MAC-B-0041` is the sole completed/unreviewed Analysis-eligible occurrence. It already has a governed stable identity, is `COMPLETED` on competent first-party evidence, and preserves day precision in `Asia/Tokyo` with null UTC. It therefore provides the cleanest available anchor for a first Canonical-linked Live observation and first production Live→Analysis relationship without manufacturing or retiming an event.

## Fresh source findings

Statistics Bureau of Japan identifies the July 2026 Family Income and Expenditure Survey as released on **4 September 2026**. For two-or-more-person households it reports average monthly consumption expenditure of JPY 301,245, down 1.5% nominally and 3.6% in real terms year on year; workers' household income averaged JPY 689,476, down 3.8% in real terms.

The Japanese monthly-result surface reports July real consumption expenditure down 3.6% year on year and up 0.5% month on month on a seasonally adjusted basis. It explicitly states that April, May and June 2026 real-change figures were retrospectively revised because of the CPI 2025-base revision.

The Statistics Bureau had announced on **7 July 2026** that this retrospective revision would be made with the July-data publication scheduled for 4 September. Therefore the rebasing is a known data-vintage boundary, not an ex-post surprise invented by WORLD SIGNALS.

Reuters reported market expectations of -1.6% year on year and +2.6% seasonally adjusted month on month, against released readings of -3.6% and +0.5%. Those reported forecasts are a defensible ex-ante benchmark, but WORLD SIGNALS cannot reconstruct every contributing forecaster's exact deflator/vintage treatment. Surprise language must preserve that limitation.

## Architectural decision

AZ may open **exactly one** production Live input.

The sequence is:

`completed Canonical occurrence`
→ `reviewed ECONOMIC_DATA_OBSERVATION with OUTCOME_OF link`
→ `reviewed Analysis packet selecting that immutable observation_id`

This is not:

`Analysis evidence copied into Live`
or
`Live evidence transitively becoming Analysis evidence`
or
`headline → inferred cause`.

The Live row and Analysis evidence may cite the same public source endpoints, but they remain separately governed evidence records serving different layers.

## Data revision boundary

The July observation is an `ECONOMIC_DATA_OBSERVATION`, not a `DATA_REVISION` row.

The 4 September publication also carries evidence that April-June real-change figures were retrospectively revised. AZ preserves that as factual data-vintage context. It does **not** invent historical Live observations for April-June and does not imply that the July observation revises a prior WORLD SIGNALS observation.

A later dedicated `DATA_REVISION` specimen remains available if it creates additional contract pressure.

## First production bridge constraints

AZ should require:

1. production `live_inputs` count exactly 1;
2. maximum one Live input in any review in this tranche;
3. the sole populated input selects immutable `observation_id`;
4. a `FACTUAL_INPUT` must share the Analysis review's Canonical occurrence through the Live observation's `canonical_links`;
5. Live evidence remains separate from Analysis evidence;
6. public Live-input projection remains closed;
7. public Live-observation projection remains closed;
8. no automatic ingestion, story expansion, Canonical commit or Calendar write;
9. no market movement is added without evidence;
10. further production-link population requires another pressure audit.

The same-Canonical-anchor requirement is role-specific to factual event input. It should not preclude future cross-occurrence contextual Live inputs after separate pressure testing.

## Analytical treatment

### WHAT HAPPENED
Use first-party Statistics Bureau values and preserve the retrospective-revision note.

### WHAT WAS EXPECTED
Use the Reuters-reported consensus as a separately governed analytical benchmark.

### WHAT SURPRISED
A downside data surprise is supportable relative to those reported forecasts. Do not label the CPI rebasing itself a surprise.

### WHAT MOVED
Leave empty. No defensible event-specific market observation has been established for this packet.

### WHAT APPEARS CONNECTED
Household demand is relevant policy context for the BOJ, but the packet must remain `NOT_A_CAUSAL_CLAIM`.

### WHAT MAY BE NOISE / ALTERNATIVES
Preserve survey volatility, category composition, price pressure and data-vintage/rebasing limitations.

### SECOND-ORDER EFFECTS
Not established.

### FALSIFIERS
Include later statistical correction, benchmark-vintage incompatibility, subsequent consumption rebound, divergence from broader consumption measures, and any later high-quality market evidence.

## Historical-descendant pressure

AZ will legitimately grow both Live and Analysis descendants. Known stale live-state assertions include:

- AX tests that treat v0.3 / 3 observations / 4 evidence rows as a permanent Live ceiling;
- AY tests that treat the AX three-row population and zero production links as permanent descendants;
- AU tests that treat 20 reviews / 91 evidence rows as a permanent live Analysis ceiling.

Historical base SHAs, plans, payloads and exact tranche target checkpoints must remain frozen. Repairs may touch only current-descendant assertions and must retain the original tranche invariants.

## Decision

Proceed with one bounded AZ cross-layer specimen.

Do not add a second Live observation, do not create a synthetic April-June revision history, do not add a market series, do not modify Canonical/Source/Monitor data, and do not open public projection.

After AZ, run another pressure audit before any second production Live→Analysis relationship.
