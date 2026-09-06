# WORLD SIGNALS — reviewed Source/Change Monitor coverage audit AR v0.1

**Checkpoint:** exact post-#72 `main` `2c215ce4d3ff70001af4733fce797f166bab2a46`  
**Canonical registry:** v0.37 / 687  
**Source registry:** v1.78 / 242  
**Monitor expectations:** v0.9  
**Monitor-coverage audit dataset:** v0.1  
**Nature:** read-only scope audit; no route-creation or canonical-write authority

## Boundary

This audit asks a narrow operational question:

> What part of the canonical system is explicitly inside configured Source/Change Monitor scope today?

It does **not** answer:

- what proportion of the world is "monitored";
- whether every uncovered region/category should receive a route;
- whether a source is legally or technically ready for automation;
- whether a configured route is currently healthy at runtime;
- whether a missing route implies missing canonical coverage;
- whether a source-registry holding with no current canonical dependency counts as coverage.

Configured monitor scope, source governance, runtime health, canonical breadth and Analysis coverage remain separate layers.

## Current configured shape

The exact v0.9 monitor configuration resolves to:

- configured adapters: **7**
- unique configured monitor source IDs: **6**
- distinct explicitly scoped canonical occurrences: **27**
- distinct scoped series: **10**
- distinct scoped institutions: **5**
- scoped regions: **3**
- scoped categories: **5**

No coverage percentage is calculated. The denominator would imply a completeness model that WORLD SIGNALS has not defined.

## Geographic concentration

The 27 explicitly scoped occurrences are distributed as:

- Europe: **24**
- Oceania / Pacific: **2**
- Latin America: **1**

Canonical regions with no explicit configured monitor occurrence scope at this checkpoint are:

- Africa
- Cross-regional / Global
- East Asia
- North America
- South Asia
- Southeast Asia

This is a **review prompt**, not a six-route backlog.

Several reasons can legitimately produce a zero:

- authoritative sources may still be on rights or endpoint hold;
- the canonical object may not benefit materially from automated change detection;
- a manual authoritative recheck may be the correct verification mode;
- the relevant source may be stable/immutable rather than a live schedule;
- route implementation may not yet have been stress-tested;
- a region may have canonical breadth without a mature machine-readable source family.

## Category concentration

Configured monitor occurrence scope currently covers:

- `MACROECONOMIC_RELEASE`: **19 occurrences**
- `TRADE_SANCTIONS_INDUSTRIAL_POLICY`: **3**
- `FINANCIAL_STABILITY_REGULATION`: **2**
- `TECHNOLOGY_CRITICAL_INFRASTRUCTURE`: **2**
- `FISCAL_SOVEREIGN_FINANCE`: **1**

Canonical categories with no explicit configured monitor occurrence scope are:

- `AGRICULTURE_FOOD`
- `CLIMATE_ENVIRONMENT`
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE`
- `ELECTIONS_GOVERNANCE`
- `ENERGY_COMMODITIES`
- `HEALTH_BIOSECURITY`
- `INTERNATIONAL_INSTITUTIONS`
- `MONETARY_FINANCIAL_POLICY`
- `PHYSICAL_CLIMATE_RISK`

Again, these are not automatic route requirements.

The most important observation is structural: a Source/Change Monitor that began with a few tractable legal/publication/calendar routes should not silently become the project's operational definition of importance. Canonical significance must continue to be set upstream.

## Explicit-scope rule

The AR monitor-coverage audit counts only `canonical_occurrence_ids` explicitly attached to each adapter.

It does **not** infer that:

- every occurrence in the same series is monitored;
- every event supported by the same source is monitored;
- every event in the same institution/category/region is monitored.

This prevents a one-occurrence sentinel from being reported as series-wide coverage.

Unknown canonical occurrence IDs, missing configured source IDs, duplicate adapter IDs and duplicate occurrence IDs within one adapter fail closed.

## Source-governance counterweight

A geographic/category gap should only become a route-development candidate after source governance is considered.

At the current canonical checkpoint, 159 source IDs are in active canonical use, with large cohorts still at:

- `ENDPOINT_REVIEW_REQUIRED`: 55
- `RIGHTS_AUDIT_REQUIRED`: 34
- `RIGHTS_OR_LICENSE_HOLD`: 33

There are also more mature cohorts, including:

- 13 `PILOT_VALIDATED_NO_AUTO_COMMIT`;
- 7 `PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE`;
- 7 `PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING`;
- 5 `ENDPOINT_TEST_PRIORITY`.

These labels must not be collapsed into one generic "ready" state.

## Candidate-route observations

The read-only candidate inventory identifies several source families with current canonical dependencies that may deserve later route-specific review.

### Potential diversity gains

- **U.S. Energy Information Administration / Weekly Petroleum Status Report** — pilot validated, Cross-regional / Global, `ENERGY_COMMODITIES`, 16 canonical occurrences. This could test a non-European, non-legal, high-frequency commodity monitor contract, but production route viability still requires a dedicated review.
- **Japan Ministry of Finance JGB source** — pilot validated, East Asia, `FISCAL_SOVEREIGN_FINANCE`, 10 canonical occurrences. This could test sovereign-financing monitoring outside Europe.
- **Japanese statistical source families** — several pilot-validated CPI, labour, GDP, household-spending and trade series. They would add East Asian monitor scope but risk merely reproducing a macro-release-heavy operational layer.
- **Kenya Law / National Treasury** — endpoint-test priority, Africa, fiscal/sovereign. It is currently marked for manual authoritative recheck and should not be promoted merely to put Africa on the monitor map.

### Easy-but-distorting candidates

Several U.S. macro sources are already labelled `PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE`. Adding all of them could improve North American route presence while simultaneously increasing the monitor's macroeconomic concentration. Geography alone is therefore an inadequate selection rule.

### Rights-pending candidates

Multiple RBA/ABS sources are research-validated but explicitly `AUTOMATION_RIGHTS_PENDING`. Their strong Australian relevance does not override the rights gate.

### Unbound source-registry holdings

Some source-registry entries have promising endpoint/readiness labels but **zero current canonical occurrences using that source ID**. The audit classifies these separately as `UNBOUND_SOURCE_REGISTRY_HOLDING_NOT_MONITOR_COVERAGE`.

They may be useful future provenance/route resources, but they do not count as current monitor coverage and cannot repair a canonical gap by themselves.

## Current operational bias assessment

The configured Source/Change Monitor is best described as a **narrow, successful pilot portfolio rather than a representative global monitoring mesh**.

Its strongest biases are:

1. **European concentration** — 24 of 27 explicitly scoped occurrences.
2. **Macro-release concentration** — 19 of 27 scoped occurrences.
3. **Institutional concentration** — 27 occurrences resolve to only five scoped institutions.
4. **Route-history bias** — tractable RSS/legal/calendar endpoints are over-represented relative to the breadth of Canonical.
5. **Source-governance asymmetry** — many internationally useful source families remain constrained by rights, endpoint or verification status.

These are not failures. They are the expected shape of an intentionally cautious pilot. The risk would be forgetting that the pilot's shape is contingent and allowing it to drive the canonical research agenda.

## Next route-selection discipline

A later monitor-expansion tranche should score candidates qualitatively against at least:

- systemic importance of the canonical series;
- marginal region diversity;
- marginal domain/category diversity;
- source rights status;
- endpoint stability and machine readability;
- verification mode;
- false-positive / ambiguity risk;
- whether the route tests a genuinely new adapter contract;
- whether it would reduce or deepen existing monitor concentration;
- operational maintenance burden;
- value of change detection versus periodic manual recheck.

No single factor should be sufficient.

A good next route may therefore be neither the easiest endpoint nor the most under-represented geography.

## AR conclusion

Do not change monitor expectations in AR.

The correct AR output is the audit instrument and this reviewed baseline. A fresh post-AR pressure audit should decide whether the next tranche is:

- targeted monitor expansion;
- source-rights/endpoint resolution;
- South Asia or physical-risk canonical depth;
- a high-value market-structure historical anchor;
- a new interaction-class Analysis specimen;
- or another architecture/quality-control task.

That decision should be made from the combined Canonical + Source Governance + Monitor + Analysis evidence, not from any single gap count.
