# WORLD SIGNALS — Analysis sample audit Y v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `f05b9623f973aed84a420354d273e039a4b61f8e`  
**Canonical checkpoint:** v0.30 / 681  
**Analysis checkpoint:** schema v0.3; reviews v0.7 / 11; evidence v0.7 / 40

## Audit purpose

This is the charter's **sample population → audit** checkpoint. It is descriptive and diagnostic, not a quota engine. It does not mutate the canonical registry, source registry, change ledger, monitor configuration, Analysis schema, Analysis reviews/evidence or Calendar.

## Current readiness

- completed Analysis-eligible occurrences: **12**
- reviewed completed occurrences: **11**
- reviewed event-type diversity: **10**
- schema readiness state: **`READY_FOR_CONTROLLED_EXPANSION`**
- interpretation: this is a minimum controlled-expansion gate, **not** evidence of representative global coverage.

## Reviewed-sample shape

- regions — Cross-regional / Global: 3, Oceania / Pacific: 2, South Asia: 2, Africa: 1, Europe: 1, Latin America: 1, Southeast Asia: 1
- categories — MACROECONOMIC_RELEASE: 3, MONETARY_FINANCIAL_POLICY: 3, AGRICULTURE_FOOD: 1, ENERGY_COMMODITIES: 1, FISCAL_SOVEREIGN_FINANCE: 1, INTERNATIONAL_INSTITUTIONS: 1, TECHNOLOGY_CRITICAL_INFRASTRUCTURE: 1
- event types — DATA_RELEASE: 2, DECISION: 1, FISCAL_POLICY_PROCESS: 1, GOVERNANCE_ASSEMBLY_SESSION: 1, INFORMATION_RELEASE: 1, MONETARY_POLICY_DECISION: 1, MONETARY_POLICY_DECISION_PROCESS: 1, OFFICIAL_STATISTICAL_RELEASE: 1, TECHNOLOGY_POLICY_MILESTONE: 1, TREATY_WORKING_GROUP_SESSION: 1
- intrinsic importance — HIGH: 9, MEDIUM_HIGH: 1, UNRATED_PENDING_CALIBRATION: 1
- expected market sensitivity — HIGH: 5, MEDIUM: 3, LOW: 1, MEDIUM_HIGH: 1, UNRATED_PENDING_CALIBRATION: 1

## Analytical semantics actually exercised

- surprise states — MIXED: 3, NO_CLEAR_SURPRISE: 3, UPSIDE: 3, NOT_ESTABLISHED: 2
- benchmark types — MARKET_FORECAST: 6, OTHER_DEFENSIBLE_EXPECTATION: 5, MARKET_CONSENSUS_DECISION: 3, OFFICIAL_PRIOR_GUIDANCE: 2; reviews with no benchmark: 1
- interaction types — OBSERVATION_CONTEXT: 4, TRANSMISSION_CHANNEL: 3, LEGAL_OR_OPERATIONAL_DEPENDENCY: 1, POLICY_RESPONSE_CONTEXT: 1, REGULATORY_OVERLAP: 1, TEMPORAL_COINCIDENCE_ONLY: 1
- causal statuses — NOT_A_CAUSAL_CLAIM: 7, OBSERVED_ASSOCIATION: 4
- second-order states — NOT_ESTABLISHED: 8, PLAUSIBLE_WATCH_ITEM: 2, OBSERVED: 1
- reviews with market movement: 5; without: 6
- market movement rows: 7; precision — SOURCE_REPORTED_CHANGE_AND_ENDPOINT: 6, SOURCE_REPORTED_PRE_POST: 1
- exact-timestamp-series market rows: **0**
- minimum falsifier count in any review: 2

The absence of a vocabulary state is not a defect by itself. In particular, the audit must not manufacture a downside surprise, stronger causal status or market move merely to make the distribution look balanced.

## Evidence profile

- referenced evidence rows: **40**
- evidence classes — PRIMARY_OFFICIAL: 25, REPUTABLE_NEWSWIRE: 8, REPUTABLE_MEDIA: 6, OTHER_REVIEWED: 1
- primary-official share: **62.5%**
- evidence roles — CONTEXT_OR_ALTERNATIVE: 26, OFFICIAL_OUTCOME: 19, EXPECTATION_BENCHMARK: 13, SECOND_ORDER_OBSERVATION: 8, MARKET_OBSERVATION: 6
- largest single provider: **Reuters** — 8 rows / 20.0% of referenced evidence

Provider concentration is a provenance diagnostic, not a claim that the dominant provider is unreliable.

## Upstream population gaps

These are **completed-anchor gaps**, not permission to invent historical events and not quotas.

- canonical regions present somewhere in the registry but absent from the current completed-anchor population: East Asia
- categories present in the registry but absent from completed anchors: CLIMATE_ENVIRONMENT, CORPORATE_FINANCIAL_MARKET_STRUCTURE, ELECTIONS_GOVERNANCE, FINANCIAL_STABILITY_REGULATION, HEALTH_BIOSECURITY, PHYSICAL_CLIMATE_RISK, TRADE_SANCTIONS_INDUSTRIAL_POLICY
- event types present in the registry but absent from completed anchors: ELECTION_MILESTONE, ENVIRONMENTAL_GOVERNANCE_EVENT, FINANCIAL_STABILITY_POLICY_EVENT, FINANCIAL_STABILITY_REPORT, FISCAL_FINANCING_EVENT, FISCAL_PROCESS, HEALTH_GOVERNANCE_EVENT, INDUSTRIAL_TRADE_POLICY_PROCESS, INFORMATION_CATALYST_MEETING, INSTITUTIONAL_MEETING, LEADERSHIP_TRANSITION_PROCESS, LEGISLATIVE_FISCAL_POLICY_SESSION, LEGISLATIVE_SESSION_OPENING, MARKET_STRUCTURE_EVENT, MEETING, MONETARY_POLICY_REFERENCE_RATE_PUBLICATION, PHYSICAL_RISK_WINDOW, POLITICAL_CONSULTATIVE_SESSION, POLITICAL_DECISION_PROCESS, PRESS_CONFERENCE, PRODUCER_POLICY_MEETING, PRUDENTIAL_STANDARD_EFFECTIVE_DATE, PUBLICATION, SANCTIONS_PROCESS, SCIENTIFIC_ASSESSMENT_RELEASE, SECTORAL_MINISTERIAL_MEETING, SYSTEMIC_TAX_REFORM_IMPLEMENTATION_BOUNDARY, TRADE_POLICY_PROCESS
- regions with a completed anchor but no reviewed sample: North America

## Current eligible-unreviewed frontier

- `WSO-ddb70f8ff05a58fb` — Bank of Canada policy interest rate announcement — 2026-09-02 — North America / MONETARY_FINANCIAL_POLICY / DECISION; novel region=True, category=False, event type=False, institution=True

Finishing this list is **not** the objective. Each item remains eligible, but selection must be based on marginal analytical pressure and source quality.

## Material audit findings

- **CONTROLLED_EXPANSION_GATE_IS_NOT_REPRESENTATIVE_COVERAGE** (METHOD): The schema readiness state is a minimum gate. The audit must not interpret READY_FOR_CONTROLLED_EXPANSION as evidence that the reviewed sample or completed-anchor population is globally representative.
- **UPSTREAM_COMPLETED_ANCHOR_REGION_GAPS** (MATERIAL): Some canonical regions represented in the registry have no completed anchor in the current Analysis-eligible population.
  - East Asia
- **MARKET_MEASUREMENT_PRECISION_GAP** (MATERIAL): The reviewed sample contains market-response rows but none currently use EXACT_TIMESTAMP_SERIES precision. Future market-sensitive specimens should test higher-frequency measurement where defensibly obtainable, rather than merely adding more source-reported session moves.
- **EVIDENCE_PROVIDER_CONCENTRATION_DESCRIPTIVE** (WATCH): The most-used referenced evidence provider is Reuters at 20.0% of referenced evidence rows. This is a concentration diagnostic, not a quality judgment or quota.
- **QUEUE_COMPLETION_IS_NOT_THE_OBJECTIVE** (METHOD): The remaining completed-but-unreviewed frontier must be selected by marginal analytical value. Exhausting the current queue is not itself a research objective.

## Recommended next stage

1. Prefer an authoritative **upstream historical anchor** that reduces a material completed-anchor geographic/domain gap, rather than treating the final current queue item as compulsory.
2. The next genuinely market-sensitive Analysis specimen should, where possible, improve **measurement precision** beyond source-reported session moves; the current sample has no `EXACT_TIMESTAMP_SERIES` market row.
3. Keep Bank of Canada eligible. Review it when it adds a distinct contract test, closes a meaningful coverage gap, or supplies better market-measurement evidence — not merely because it is last in the queue.

The audit therefore recommends **controlled expansion with upstream gap repair**, followed by a fresh audit before any broad/full population step.
