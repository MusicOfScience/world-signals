# Transmission Review Packet v0.1

## Purpose

This design adds a small review-only bridge between governed WORLD SIGNALS evidence and later Relationship, Risk/Regime and Scenario review. It does **not** add a new production layer and it does not reopen any population gate.

The reusable causal grammar is:

`SHOCK → EXPOSURE → TRANSMISSION → BUFFER → BEHAVIOURAL_RESPONSE → FEEDBACK → OUTCOME`

The grammar is global. Mechanisms, evidence, lags and materiality remain jurisdiction-specific.

## Analytical levels

### Global State

Shared external conditions and shocks that can affect more than one jurisdiction: energy, food, shipping, trade, sovereign yields, global liquidity, conflict, climate, technology investment and other common drivers.

### Jurisdiction State

The domestic exposure and transmission structure through which global or local shocks are absorbed or amplified: monetary policy, mortgage structure, household leverage, banks, fiscal settings, housing, labour markets, industry composition, buffers and behavioural responses.

### Network State

Reviewed cross-border feedbacks between jurisdictions or systems. Network State is **gated**. A plausible international pathway is not enough to create an edge. Step 16A deliberately leaves Network State deferred until a later packet has reviewed evidence for the specific cross-border connection.

## Why a packet rather than new production objects

The current repository already has governed contracts for Signals, Relationships, Risk/Regime states and Scenarios. Their admission rules intentionally prevent speculative or automatic population. This packet therefore acts as a bounded review artefact under `data/world_state_audit/`:

- it can assemble candidate observations from primary sources;
- it can state candidate transmission hypotheses;
- it can preserve counter-evidence and falsifiers;
- it can draft a Risk/Regime interpretation and competing Scenarios;
- it cannot mutate Canonical, Live Intelligence, Signal, Relationship, Risk/Regime, Scenario or World State production state;
- it cannot publish a public projection;
- it cannot rank scenarios or attach future-outcome probabilities.

Any later admission must use the relevant existing production contract and a separate human-reviewed transaction.

## Source discipline

1. Primary official sources are preferred for candidate factual support.
2. Secondary reporting may be retained for discovery and market context.
3. A secondary source marked `SECONDARY_DISCOVERY` must have `production_support_eligible=false`.
4. Market prices and commentary are sensors, not automatic causal proof.
5. Duplicate reporting or shared provenance does not increase corroboration.
6. Contradictory and resilience evidence stays visible alongside stress evidence.

## Relationship discipline

Candidate Relationships use the controlled class vocabulary already present in the v0.2 Relationship contract. A candidate labelled `MECHANISTICALLY_SUPPORTED` or `CAUSAL_EVIDENCE` must carry an explicit candidate causal basis; it is still not a production Relationship.

No edge is created transitively. A chain such as A → B → C does not authorise A → C. Feedback loops require separate review.

## Risk/Regime discipline

The packet may draft a qualitative Risk/Regime interpretation without writing `data/risks/states.json`. Stage labels are organising heuristics, not scalar scores. Thresholds must be stated qualitatively and preserve disconfirming evidence.

For the initial Australian housing/household implementation:

- Stage 1: affordability and market deterioration;
- Stage 2: household cash-flow compression;
- Stage 3: balance-sheet / forced-sale feedback.

Stage 3 must not be inferred from falling prices alone.

## Scenario discipline

Scenarios are competing conditional pathways, not forecasts. Every scenario should include:

- enabling conditions;
- inhibiting conditions;
- signposts;
- disconfirming signposts;
- a common dated starting condition.

No scenario should be identified as the winner or assigned a rank, odds or future-outcome probability in a review packet.

## Hindsight control

Every packet records a knowledge cutoff and a prospective assessment. Later observations may cause a new candidate or later governed revision, but must not silently rewrite the earlier interpretation. This is necessary for later evaluation of whether the proposed leading relationships had genuine prospective value.

## Step 16A boundary

The first implementation is Australia-only and deliberately small:

- 2 Global State candidates;
- 6 Australian jurisdiction/market candidates;
- 3 candidate Relationships;
- 1 candidate Australian monetary-housing Risk state;
- 3 competing draft Scenarios;
- Network State deferred;
- zero production writes.

This is the smallest useful globalisation step: global causal grammar, local evidence, no spaghetti graph.
