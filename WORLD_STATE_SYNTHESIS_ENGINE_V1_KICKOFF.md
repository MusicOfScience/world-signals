# Codex kickoff — World State Synthesis Engine v1

Continue the WORLD SIGNALS project from the current repository state. Begin by
reading `AGENTS.md`, `WORLD_SIGNALS_PROJECT_CHARTER.md`, `ARCHITECTURE.md`,
`ROADMAP.md`, `PROJECT_STATUS.md`, `HANDOFF_PROTOCOL.md`, the relevant governed
schemas and validators, and the current `main`/branch state. Treat repository
files as authoritative and conversation context as untrusted background.

The agreed direction is a derived World State synthesis over existing governed
layers, not a larger calendar, a second observation store or an ungoverned news
graph. The intended product surface is:

`WORLD STATE | OUTLOOK | CALENDAR | MAP | RESEARCH`

The future World State model must account for:

- actors as distinct entities with role, jurisdiction, authority, capabilities,
  constraints, incentives, commitments, channels and institutional/coalition
  relationships;
- the implementation-state ladder:
  `SAID → DECIDED → AUTHORISED → IMPLEMENTED → OBSERVED`;
- conflict/military activity, strategic/geopolitical tension and
  political/institutional stability as first-class dimensions;
- flows, dependencies and chokepoints, with markets treated as measured
  sensors of expectations/stress/positioning rather than automatic causal
  proof;
- state memory and as-of queries, explicit baselines, anomaly detection and
  negative evidence;
- typed uncertainty, including provenance, measurement, temporal,
  interpretive, model, actor-intent and institutional-authority uncertainty;
- competing hypotheses, model disagreement, contradiction, lags, thresholds,
  feedback loops and reflexivity;
- a typed transmission graph;
- conditional scenarios and signposts kept separate from forecasts; and
- prospective Forecasts, Outcomes and calibration with frozen cutoffs and no
  hindsight contamination.

For this first thread, do not implement the synthesis engine or populate a new
production World State layer. Produce a design-ready implementation plan and
identify the smallest coherent read-contract/schema/test boundary for v1. A
minimal consistency fixture or documentation consistency fix may be made only
if the existing repository contracts clearly require it. Keep any such change
read-only with respect to governed production state.

Preserve all governance: human review; source and actor provenance; explicit
uncertainty; public/private boundaries; immutable/as-of history; prospective
forecast integrity; no silent Canonical, Live, Signal, Relationship,
Risk/Regime, Scenario, Forecast or Outcome writes; no synthetic intelligence
to fill a UI; and no automatic promotion merely because a statement, market
move or graph edge appears plausible.

The deliverable for this thread is an evidence-backed v1 design decision record
covering boundaries, minimal data contracts, state-memory semantics, review
transactions, read-only consistency checks, test fixtures, migration sequence,
and open questions. Report exact files inspected or changed, validation run,
branch and head SHA, governed-data impact, and genuine limitations. Follow the
repository merge handoff rules; the user merges and the assistant does not.
