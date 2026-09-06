# WORLD SIGNALS — post-AQ pressure audit AR v0.1

## Frozen checkpoint

- exact post-#72 `main`: `2c215ce4d3ff70001af4733fce797f166bab2a46`
- canonical registry: `v0.37 / 687`
- source registry: `v1.78 / 242`
- change ledger: `v0.24 / 59`
- monitor expectations: `v0.9`
- Analysis schema: `v0.4`
- Analysis reviews: `v0.15 / 19`
- Analysis evidence: `v0.15 / 85`
- reviewed event-type diversity: `17`
- production `EXACT_TIMESTAMP_SERIES`: `0`

AR is a pressure audit, not an instruction to consume the remaining completed occurrence.

## Selection result

**Pause Analysis population. Refresh the canonical coverage baseline and formalise a read-only monitor-coverage audit.**

Do not populate a twentieth Analysis review merely to produce `20/20`. Do not create a market-structure historical anchor merely to close a categorical zero. Do not add monitor routes merely to make geographic distributions look balanced.

The current methodological pressure is that the system's reviewed coverage interpretation is stale while Canonical, Source Governance, Source/Change Monitor and Analysis have all advanced.

## Why Japan household spending is held

The sole completed/unreviewed canonical occurrence is:

- `WSO-MAC-B-0041` — Japan Family Income and Expenditure Survey — July 2026
- region: `East Asia`
- category: `MACROECONOMIC_RELEASE`
- event type: `DATA_RELEASE`

It is a valid future Analysis specimen. It is not a backlog obligation. The current sample already contains three `MACROECONOMIC_RELEASE` reviews and two `DATA_RELEASE` reviews; another clean macro surprise would add less marginal contract value than an audit of the machinery surrounding the 19-specimen sample.

## Stale coverage baseline

The durable reviewed file `data/coverage/COVERAGE_BIAS_AUDIT_v0.1.md` was frozen at canonical `v0.17 / 649`, with 185 series, 110 institutions and 141 used source IDs.

The live coverage engine has since advanced to audit dataset `v0.3`, while canonical has advanced to `v0.37 / 687`. A fresh exact-base recomputation reports:

- 687 occurrences
- 201 unique series
- 126 unique institutions
- 159 unique canonical source IDs used
- 443 monetary-policy + macroeconomic-release occurrences
- monetary + macro occurrence share: `64.48%`

The stale reviewed interpretation should therefore not remain the working coverage baseline.

## Current canonical breadth — important changes

Mechanical threshold prompts now identify:

- `South Asia` as the only region with fewer than 10 distinct series;
- `South Asia` as the only region with fewer than 8 distinct institutions;
- `PHYSICAL_CLIMATE_RISK` as the only category with fewer than 5 distinct series.

These are **review prompts only**, not quotas.

### Regions requiring interpretation

- South Asia: 28 occurrences / 8 series / 6 institutions / 6 sources / 3 categories.
- Africa: 19 / 11 / 11 / 11 / 4. Africa has moved beyond the old mechanical low-series flag, but breadth remains modest and should not be mistaken for completion.
- Southeast Asia: 18 / 10 / 10 / 11 / 5. It too has moved beyond the old threshold while remaining a relatively small holding.

### Categories requiring interpretation

- `PHYSICAL_CLIMATE_RISK`: 6 occurrences / 3 series / 3 institutions / 3 sources — genuinely shallow.
- `HEALTH_BIOSECURITY`: 11 / 5 / **1 institution** / 5 sources — series count masks strong institutional concentration.
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE`: 17 / 5 / 5 / 5 — no longer below the raw `<5 series` threshold, but still lacks a completed Analysis-eligible historical anchor. That is a separate lifecycle/sample-design issue, not a raw-coverage zero.
- `ENERGY_COMMODITIES`: 34 / 9 / 6 / 7 — occurrence density is materially higher than institutional diversity.

## Source-governance pressure

Among the 159 source IDs currently used by canonical occurrences, monitoring readiness remains mixed:

- `ENDPOINT_REVIEW_REQUIRED`: 55
- `ENDPOINT_TEST_PRIORITY`: 5
- `PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING`: 7
- `PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE`: 7
- `PILOT_VALIDATED_NO_AUTO_COMMIT`: 13
- `RIGHTS_AUDIT_REQUIRED`: 34
- `RIGHTS_OR_LICENSE_HOLD`: 33
- other explicit hold/live states: 5 total
- missing used source IDs from Source Registry: 0

Machine readability, canonical use and monitor permission remain separate questions.

## Calendar-projection boundary

Two canonical Nepal budget occurrences retain unresolved source-native dates:

- `WSO-FIS-NP-BUDGET-2083`
- `WSO-FIS-NP-BUDGET-2084`

They count as canonical breadth. They must not be placed on fabricated Gregorian days merely to increase calendar schedulability.

## Source/Change Monitor concentration

Monitor expectations `v0.9` contain 7 configured adapters with 27 distinct explicitly scoped canonical occurrences.

Those occurrences currently fall in only three regions:

- Europe: 24
- Latin America: 1
- Oceania / Pacific: 2

Configured occurrence scope is concentrated in five categories:

- `MACROECONOMIC_RELEASE`: 19
- `TRADE_SANCTIONS_INDUSTRIAL_POLICY`: 3
- `FINANCIAL_STABILITY_REGULATION`: 2
- `TECHNOLOGY_CRITICAL_INFRASTRUCTURE`: 2
- `FISCAL_SOVEREIGN_FINANCE`: 1

There is no explicit configured occurrence scope at this checkpoint in East Asia, South Asia, Southeast Asia, Africa, North America or Cross-regional / Global holdings.

This is a **concentration finding, not a route quota**. A missing region does not imply an adapter should be added.

## Route-readiness counterweight

The Source Registry already contains plausible non-European monitor holdings, but their states differ materially.

Examples with current canonical dependencies include:

- U.S. macro sources marked `PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE`;
- AOFM and ABS Wage Price Index holdings in the same route-candidate state;
- Bank of Canada and Kenya Law holdings marked `ENDPOINT_TEST_PRIORITY`;
- Federal Reserve, EIA, Japan Ministry of Finance and multiple Japanese statistical sources marked `PILOT_VALIDATED_NO_AUTO_COMMIT`;
- several RBA/ABS sources marked `PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING`.

These labels are not interchangeable. In particular:

- route-candidate status is not automatic route authority;
- pilot validation is not production deployment;
- rights-pending is a hard reason not to promote;
- an endpoint-test priority is not a command to configure an adapter;
- adding several U.S. macro feeds could improve North American route presence while worsening domain concentration.

Source-registry holdings with zero current canonical dependencies must not be counted as monitor coverage.

## Analysis sample after AQ

The 19 reviewed specimens already span all nine canonical regions and 13 categories, with 17 distinct event types. That is a useful controlled sample, not a representative model of the world.

The current need is to audit the sampling and monitoring machinery before further expansion.

## AR architecture decision

AR should add no canonical occurrence, source, change-ledger entry, Analysis review or monitor route.

It should:

1. refresh the reviewed canonical coverage interpretation at `v0.37 / 687`;
2. align the coverage runner with the engine's `v0.3` output, including source-governance and calendar-projection readiness;
3. introduce a reusable read-only monitor-coverage audit based only on explicit configured occurrence scope;
4. keep monitor concentration distinct from source readiness and from canonical breadth;
5. expose candidate-source holdings without promoting any candidate;
6. preserve all write gates and `EXACT_TIMESTAMP_SERIES = 0`;
7. rerun a fresh pressure audit after AR before choosing any population or monitor-expansion tranche.

## Explicit non-goals

AR does **not**:

- close the Japan Analysis frontier;
- backfill market structure for histogram tidiness;
- claim balanced global coverage;
- claim monitor completeness;
- infer monitor coverage from a series when only one occurrence is configured;
- convert a source-readiness label into automation permission;
- resolve source-native dates;
- mutate Canonical, Source Registry, Change Ledger, monitor expectations, Analysis or Calendar.
