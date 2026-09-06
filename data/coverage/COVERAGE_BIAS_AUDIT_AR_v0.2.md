# WORLD SIGNALS — reviewed coverage and bias audit AR v0.2

**Checkpoint:** exact post-#72 `main` `2c215ce4d3ff70001af4733fce797f166bab2a46`
**Canonical registry:** v0.37 / 687 occurrences
**Coverage engine:** v0.3
**Nature:** reviewed interpretation of reproducible canonical coverage metrics; no population authority

## Why this refresh exists

The earlier durable reviewed audit `COVERAGE_BIAS_AUDIT_v0.1.md` remains a valid historical checkpoint, but it describes canonical v0.17 / 649. Canonical is now v0.37 / 687 and the coverage engine itself has advanced to v0.3.

This file becomes the current reviewed coverage baseline without rewriting the historical audit.

## Executive assessment

WORLD SIGNALS is broader than the earlier audit suggested, but it is still structurally uneven.

The main change is not that the system has become "balanced". Rather:

- Africa and Southeast Asia have gained enough distinct series/institutions to leave the old mechanical low-diversity warning;
- South Asia remains distinctly thin;
- physical climate risk remains the clearest category-depth weakness;
- health/biosecurity has adequate raw series count for the current threshold but is concentrated in one institution;
- monetary policy and macro releases still dominate occurrence volume;
- the Source Registry shows substantial rights/endpoint work still separating canonical provenance from scalable monitoring;
- canonical breadth is broader than Gregorian calendar schedulability because source-native dates remain legitimate canonical objects.

## Current totals

- occurrences: **687**
- unique series: **201**
- unique institutions: **126**
- unique canonical source IDs used: **159**
- occurrences per series: **3.42**
- monetary-policy + macroeconomic-release occurrences: **443**
- monetary + macro occurrence share: **64.48%**

The occurrence share is descriptive only. Recurring central-bank and statistical schedules create dense row counts and must not be mistaken for equivalent diversity.

## Region shape

| Region | Occurrences | Series | Institutions | Sources | Categories | Occ/series |
|---|---:|---:|---:|---:|---:|---:|
| East Asia | 143 | 29 | 14 | 18 | 4 | 4.93 |
| Europe | 126 | 35 | 14 | 25 | 10 | 3.60 |
| Oceania / Pacific | 119 | 25 | 15 | 22 | 10 | 4.76 |
| Cross-regional / Global | 108 | 54 | 35 | 41 | 8 | 2.00 |
| North America | 105 | 21 | 14 | 16 | 5 | 5.00 |
| South Asia | 28 | 8 | 6 | 6 | 3 | 3.50 |
| Latin America | 21 | 11 | 11 | 11 | 5 | 1.91 |
| Africa | 19 | 11 | 11 | 11 | 4 | 1.73 |
| Southeast Asia | 18 | 10 | 10 | 11 | 5 | 1.80 |

### Interpretation

**South Asia remains the strongest regional depth concern.** Eight series across six institutions and three categories is too small a base from which to infer broad political-economic coverage. The appropriate response is institution/source review, not equal-count population.

**Africa has improved materially** since the earlier audit and no longer trips the current `<10 series` / `<8 institutions` prompts. That does not establish adequate African coverage. Nineteen occurrences across eleven one-ish-per-series holdings remain sparse compared with the system's largest regions, and several important institutional/economic channels may still be absent.

**Southeast Asia has also improved**, reaching ten series and ten institutions. Its relatively low occurrence density is not itself a defect; it partly reflects one-off or lower-frequency institutional objects rather than repeated monthly/meeting calendars.

**East Asia has substantial row volume but only four categories.** Its high occurrence density is heavily shaped by recurring monetary and macroeconomic series. Volume should not be interpreted as thematic breadth.

**Oceania / Pacific is comparatively broad by category**, but Australia supplies much of the institutional density. Pacific-island depth should continue to be examined separately rather than allowing Australian volume to stand in for the region.

## Category shape

| Category | Occurrences | Series | Institutions | Sources | Occ/series |
|---|---:|---:|---:|---:|---:|
| MONETARY_FINANCIAL_POLICY | 250 | 34 | 21 | 23 | 7.35 |
| MACROECONOMIC_RELEASE | 193 | 45 | 15 | 23 | 4.29 |
| FISCAL_SOVEREIGN_FINANCE | 56 | 30 | 27 | 30 | 1.87 |
| INTERNATIONAL_INSTITUTIONS | 38 | 22 | 18 | 24 | 1.73 |
| ENERGY_COMMODITIES | 34 | 9 | 6 | 7 | 3.78 |
| ELECTIONS_GOVERNANCE | 27 | 13 | 13 | 15 | 2.08 |
| AGRICULTURE_FOOD | 22 | 9 | 6 | 5 | 2.44 |
| CORPORATE_FINANCIAL_MARKET_STRUCTURE | 17 | 5 | 5 | 5 | 3.40 |
| CLIMATE_ENVIRONMENT | 11 | 11 | 7 | 4 | 1.00 |
| HEALTH_BIOSECURITY | 11 | 5 | 1 | 5 | 2.20 |
| TRADE_SANCTIONS_INDUSTRIAL_POLICY | 9 | 5 | 4 | 6 | 1.80 |
| TECHNOLOGY_CRITICAL_INFRASTRUCTURE | 7 | 5 | 3 | 5 | 1.40 |
| FINANCIAL_STABILITY_REGULATION | 6 | 5 | 4 | 4 | 1.20 |
| PHYSICAL_CLIMATE_RISK | 6 | 3 | 3 | 3 | 2.00 |

### Interpretation

**Physical climate risk is the clearest raw-depth gap.** Three series and three institutions are not a broad representation of acute and seasonal physical risk. Future work should examine cyclone, flood, drought, heat, wildfire, hydrological and other source families across multiple regions, while avoiding event-count inflation from named hazards.

**Health/biosecurity is institutionally concentrated.** Five series sourced through one institution means the category passes the series threshold while remaining narrow in institutional perspective. One Health, animal health, agriculture/biosecurity, regional public-health bodies and other relevant systems should be evaluated as separate institutional relationships rather than relabelled into a single primary ontology.

**Market structure is no longer a mechanical zero.** It has five series across five institutions. The remaining concern is different: there is no completed Analysis-eligible historical anchor in this category. That should be solved only when a high-value object provides a useful analytical contract, not by backfilling a date to improve a histogram.

**Energy/commodities remains concentrated relative to its occurrence volume.** Thirty-four occurrences arise from nine series and six institutions. This warrants qualitative review of commodity families, geographic production/consumption centres, shipping/logistics and benchmark infrastructure, not simple multiplication of weekly data rows.

**Monetary/macro dominance remains real.** Together they account for 64.48% of occurrences. Their distinct-series share is much lower than their row share, reinforcing the need to use series/institution diversity rather than event count as the primary bias diagnostic.

## Mechanical review prompts

At this checkpoint the v0.3 audit flags:

- regions with fewer than 10 unique series: **South Asia**;
- regions with fewer than 8 unique institutions: **South Asia**;
- categories with fewer than 5 unique series: **PHYSICAL_CLIMATE_RISK**.

These thresholds are deliberately non-authoritative. Crossing a threshold does not prove adequate coverage; failing it does not automatically authorise population.

## Source-governance readiness

The 159 source IDs currently used by canonical occurrences have these monitoring-readiness states:

| State | Used sources |
|---|---:|
| ENDPOINT_REVIEW_REQUIRED | 55 |
| RIGHTS_AUDIT_REQUIRED | 34 |
| RIGHTS_OR_LICENSE_HOLD | 33 |
| PILOT_VALIDATED_NO_AUTO_COMMIT | 13 |
| PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | 7 |
| PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | 7 |
| ENDPOINT_TEST_PRIORITY | 5 |
| MANUAL_ONLY_RIGHTS_HOLD | 2 |
| HOLD_GENERATED_ICS_ENDPOINT_REDISCOVERY_REQUIRED | 1 |
| LIVE_VALIDATED_NO_AUTO_COMMIT | 1 |
| PARSER_OR_ENDPOINT_HOLD | 1 |

No used canonical source ID is missing from the Source Registry.

This distribution is an operational constraint, not a quality score. It reinforces the project's provenance/automation split: a source may be good enough to support a canonical date while still being unsuitable for automated monitoring.

## Calendar-projection readiness

Two Nepal federal-budget occurrences retain authoritative source-native dates without a resolved Gregorian conversion:

- `WSO-FIS-NP-BUDGET-2083`
- `WSO-FIS-NP-BUDGET-2084`

They are valid canonical signals and count toward coverage. They are not Gregorian-calendar ready. No synthetic conversion should be introduced to make the calendar appear more complete.

## Bias cautions retained

The refreshed counts do not remove the core methodological cautions:

1. **High-frequency recurring systems distort occurrence volume.**
2. **A region can pass simple thresholds and remain conceptually thin.**
3. **Institution count matters separately from series count.**
4. **Source count is not source independence.** Multiple records may ultimately sit inside the same institutional information ecosystem.
5. **Thematic categories differ structurally.** Elections, treaties and physical-risk windows should not be expected to have the same recurrence density as CPI releases or central-bank meetings.
6. **Global/cross-regional objects can hide geographic asymmetry.** They should not be allocated pro rata to regions merely to improve balance.
7. **Canonical breadth is not monitor coverage.** Source/Change Monitor scope is audited separately in AR.
8. **Canonical breadth is not Analysis representativeness.** The 19 reviewed specimens are a controlled analytical sample, not a statistically representative sample of the registry.

## Current priority questions

The refreshed audit changes the next questions from "add more rows" to:

- Which South Asian institutions and signal families are materially absent?
- Which physical-risk systems can be represented with authoritative, source-native and internationally diverse windows?
- How should health/biosecurity institutional concentration be reduced without distorting the primary taxonomy?
- Which market-structure historical object would genuinely test a new analytical contract?
- Which source-governance bottlenecks are worth resolving because they unlock high-value monitoring, rather than because they are easy?
- Does Source/Change Monitor scope reflect the project's international breadth, or merely the subset of routes that were easiest to operationalise first?

The last question is addressed by the separate AR monitor-coverage audit.
