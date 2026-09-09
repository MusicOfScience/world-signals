# WORLD SIGNALS — monitor coverage audit v0.1

Canonical registry: **v0.41**
Source registry: **v2.02**
Monitor expectations: **v0.27**

## Methodological boundary

This is a read-only audit of explicitly configured Source/Change Monitor scope. It is not a monitor-completeness score and does not authorise route creation, source promotion or canonical writes.

- Occurrence density is not route diversity.
- Missing regions or categories are qualitative review prompts, not quotas.
- Only explicit `canonical_occurrence_ids` are counted; the audit does not infer scope from a series.
- Source rights and monitoring readiness remain separate constraints on route viability.

## Configured scope

- configured_adapter_count: **25**
- unique_monitor_source_count: **24**
- scoped_occurrence_count: **215**
- scoped_series_count: **47**
- scoped_institution_count: **22**
- scoped_region_count: **9**
- scoped_category_count: **11**

## Configured source readiness

### monitoring_readiness_status_counts

- LIVE_VALIDATED_NO_AUTO_COMMIT: 16
- PILOT_VALIDATED_NO_AUTO_COMMIT: 6
- LIVE_VALIDATED_FIRST_PARTY_CONTENT_API_NO_AUTO_COMMIT: 1
- LIVE_VALIDATED_ROBOTS_CONFORMANT_NO_AUTO_COMMIT: 1

### automated_monitoring_use_counts

- CLEARED: 19
- CLEARED_BOUNDED_OFFICIAL_ICAL: 1
- CLEARED_BOUNDED_OFFICIAL_RSS: 1
- CLEARED_BOUNDED_RELEASE_CALENDAR: 1
- CLEARED_BOUNDED_RELEASE_SCHEDULE: 1
- ENDPOINT_REVIEW_REQUIRED: 1

### verification_mode_counts

- AUTOMATED_PILOT: 24

## Diagnostic prompts

Regions with canonical signals but no explicit configured monitor occurrence scope: none

Categories with canonical signals but no explicit configured monitor occurrence scope: CLIMATE_ENVIRONMENT, HEALTH_BIOSECURITY, PHYSICAL_CLIMATE_RISK

Absence from configured monitor scope is a qualitative review prompt, not evidence that a route should be added.

## Region scope

| Region | Canonical series | Monitored occurrences | Monitored series | Monitored institutions |
|---|---:|---:|---:|---:|
| Africa | 11 | 4 | 2 | 2 |
| Cross-regional / Global | 54 | 27 | 5 | 4 |
| East Asia | 29 | 61 | 12 | 3 |
| Europe | 35 | 40 | 16 | 6 |
| Latin America | 11 | 5 | 2 | 2 |
| North America | 21 | 22 | 2 | 1 |
| Oceania / Pacific | 25 | 52 | 6 | 2 |
| South Asia | 9 | 2 | 1 | 1 |
| Southeast Asia | 11 | 2 | 1 | 1 |

## Category scope

| Category | Canonical series | Monitored occurrences | Monitored series | Monitored institutions |
|---|---:|---:|---:|---:|
| AGRICULTURE_FOOD | 9 | 11 | 4 | 3 |
| CLIMATE_ENVIRONMENT | 11 | 0 | 0 | 0 |
| CORPORATE_FINANCIAL_MARKET_STRUCTURE | 5 | 1 | 1 | 1 |
| ELECTIONS_GOVERNANCE | 14 | 6 | 1 | 1 |
| ENERGY_COMMODITIES | 9 | 16 | 1 | 1 |
| FINANCIAL_STABILITY_REGULATION | 5 | 2 | 1 | 1 |
| FISCAL_SOVEREIGN_FINANCE | 30 | 11 | 2 | 2 |
| HEALTH_BIOSECURITY | 5 | 0 | 0 | 0 |
| INTERNATIONAL_INSTITUTIONS | 22 | 3 | 1 | 1 |
| MACROECONOMIC_RELEASE | 45 | 86 | 24 | 5 |
| MONETARY_FINANCIAL_POLICY | 34 | 74 | 10 | 6 |
| PHYSICAL_CLIMATE_RISK | 4 | 0 | 0 | 0 |
| TECHNOLOGY_CRITICAL_INFRASTRUCTURE | 5 | 2 | 1 | 1 |
| TRADE_SANCTIONS_INDUSTRIAL_POLICY | 5 | 3 | 1 | 1 |

## Adapter inventory

### BSP_MONETARY_POLICY_RSS

- source: `WSSRC-REGJ-006` — Bangko Sentral ng Pilipinas
- role: OFFICIAL_BSP_MONETARY_POLICY_STANCE_PUBLICATION_RSS_SENTINEL
- cadence: DAILY
- explicit occurrences: 2
- scoped series: 1
- regions: Southeast Asia
- categories: MONETARY_FINANCIAL_POLICY
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### CBN_MPC_CALENDAR

- source: `WSSRC-CB-014` — Central Bank of Nigeria
- role: OFFICIAL_CBN_MPC_MEETING_WINDOW_SCHEDULE_SENTINEL
- cadence: DAILY_WHILE_FUTURE_TRACKED_OCCURRENCES_REMAIN
- explicit occurrences: 2
- scoped series: 1
- regions: Africa
- categories: MONETARY_FINANCIAL_POLICY
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### CBSL_MONETARY_POLICY_RSS

- source: `WSSRC-REGJ-007` — Central Bank of Sri Lanka
- role: OFFICIAL_CBSL_MONETARY_POLICY_REVIEW_PUBLICATION_RSS_SENTINEL
- cadence: DAILY
- explicit occurrences: 2
- scoped series: 1
- regions: South Asia
- categories: MONETARY_FINANCIAL_POLICY
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### CHINA_NBS_LATEST_RELEASES_RSS

- source: `WSSRC-MAC-031` — National Bureau of Statistics of China
- role: OFFICIAL_NBS_NATIVE_LATEST_RELEASES_RSS_PUBLICATION_SENTINEL
- cadence: DAILY
- explicit occurrences: 36
- scoped series: 9
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### COLOMBIA_SUIN_DECREE_111_1996

- source: `WSSRC-REG4-002` — Colombia Open Data / Ministry of Justice and Law
- role: LEGAL_INSTRUMENT_PRESENCE_VERSION_SENTINEL
- cadence: DAILY_DURING_ACTIVE_BUDGET_PROCESS
- explicit occurrences: 1
- scoped series: 1
- regions: Latin America
- categories: FISCAL_SOVEREIGN_FINANCE
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EIA_WPSR_SCHEDULE

- source: `WSSRC-COM-003` — U.S. Energy Information Administration
- role: PUBLICATION_SCHEDULE_RULE_AND_EXCEPTION_SENTINEL
- cadence: DAILY
- explicit occurrences: 16
- scoped series: 1
- regions: Cross-regional / Global
- categories: ENERGY_COMMODITIES
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EUROPEAN_COUNCIL_MEETINGS_RSS

- source: `WSSRC-INT-035` — European Council / Council of the EU
- role: OFFICIAL_EUROPEAN_COUNCIL_MEETINGS_RSS_DATE_CHANGE_SENTINEL
- cadence: daily
- explicit occurrences: 3
- scoped series: 1
- regions: Europe
- categories: INTERNATIONAL_INSTITUTIONS
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EUROSTAT_RELEASE_CALENDAR_ICS

- source: `WSSRC-MAC-005` — Eurostat
- role: EXACT_RELEASE_TITLE_CIVIL_DATE_SENTINEL
- cadence: DAILY
- explicit occurrences: 12
- scoped series: 6
- regions: Europe
- categories: MACROECONOMIC_RELEASE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EU_CBAM_ANNUAL_DEADLINE_RULE

- source: `WSSRC-TRD-006` — European Commission — Taxation and Customs Union
- role: PAIRED_RECURRING_DEADLINE_RULE_PLUS_PARENT_ACT_CELLAR_RDF_LEGAL_TOPOLOGY_SENTINEL
- cadence: MONTHLY; WEEKLY_INSIDE_120_DAYS_OF_2027_09_30
- explicit occurrences: 1
- scoped series: 1
- regions: Europe
- categories: TRADE_SANCTIONS_INDUSTRIAL_POLICY
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EU_CBAM_CERTIFICATE_SALE_RULE

- source: `WSSRC-TRD-005` — European Commission — Taxation and Customs Union
- role: IMMUTABLE_AMENDING_RULE_PLUS_PARENT_ACT_CELLAR_RDF_LEGAL_TOPOLOGY_SENTINEL
- cadence: MONTHLY; WEEKLY_INSIDE_90_DAYS_OF_2027_02_01
- explicit occurrences: 1
- scoped series: 1
- regions: Europe
- categories: TRADE_SANCTIONS_INDUSTRIAL_POLICY
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EU_CBAM_VERIFICATION_RULE

- source: `WSSRC-TRD-005` — European Commission — Taxation and Customs Union
- role: IMMUTABLE_MILESTONE_RULE_PLUS_CELLAR_RDF_LEGAL_TOPOLOGY_SENTINEL
- cadence: MONTHLY; WEEKLY_INSIDE_90_DAYS_OF_2027_01_01
- explicit occurrences: 1
- scoped series: 1
- regions: Europe
- categories: TRADE_SANCTIONS_INDUSTRIAL_POLICY
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### EU_CELLAR_CRA_ARTICLE_71

- source: `WSSRC-TECH-001` — European Union / EUR-Lex
- role: IMMUTABLE_RULE_BASELINE_PLUS_CELLAR_RDF_LEGAL_TOPOLOGY_SENTINEL
- cadence: DAILY_AROUND_APPLICATION_BOUNDARIES_ELSE_MONTHLY
- explicit occurrences: 2
- scoped series: 1
- regions: Europe
- categories: TECHNOLOGY_CRITICAL_INFRASTRUCTURE
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### FAO_RELEASE_CALENDAR

- source: `WSSRC-COM-010` — Food and Agriculture Organization of the United Nations
- role: OFFICIAL_FAO_FFPI_AMIS_RELEASE_DATE_CHANGE_SENTINEL
- cadence: DAILY
- explicit occurrences: 6
- scoped series: 2
- regions: Cross-regional / Global
- categories: AGRICULTURE_FOOD
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED_BOUNDED_RELEASE_CALENDAR

### FED_MONETARY_POLICY_RSS

- source: `WSSRC-CB-015` — Board of Governors of the Federal Reserve System
- role: OFFICIAL_FOMC_STATEMENT_AND_MINUTES_PUBLICATION_SENTINEL
- cadence: DAILY
- explicit occurrences: 22
- scoped series: 2
- regions: North America
- categories: MONETARY_FINANCIAL_POLICY
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### HMT_T1_CONTENT_API

- source: `WSSRC-MKT-014` — HM Treasury / GOV.UK
- role: CONDITIONAL_LEGISLATIVE_DEPENDENCY_SENTINEL
- cadence: DAILY
- explicit occurrences: 1
- scoped series: 1
- regions: Europe
- categories: CORPORATE_FINANCIAL_MARKET_STRUCTURE
- readiness: LIVE_VALIDATED_FIRST_PARTY_CONTENT_API_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### INDEC_CPI_CALENDAR

- source: `WSSRC-REG2-009` — INDEC
- role: OFFICIAL_INDEC_CPI_INTERACTIVE_CALENDAR_SCHEDULE_AND_CLOCK_SENTINEL
- cadence: DAILY
- explicit occurrences: 4
- scoped series: 1
- regions: Latin America
- categories: MACROECONOMIC_RELEASE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### JAPAN_CPI_RELEASE_SCHEDULE

- source: `WSSRC-MAC-014` — Statistics Bureau of Japan
- role: OFFICIAL_JAPAN_NATIONAL_CPI_RELEASE_DATE_DRIFT_SENTINEL
- cadence: WEEKLY; DAILY_INSIDE_7_DAYS_OF_CONFIGURED_RELEASE
- explicit occurrences: 7
- scoped series: 1
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED_BOUNDED_RELEASE_SCHEDULE

### JAPAN_HHSPEND_STATISTICS_DASHBOARD_API

- source: `WSSRC-MAC-030` — Statistics Bureau of Japan / Ministry of Internal Affairs and Communications
- role: REFERENCE_PERIOD_DATA_AVAILABILITY_SENTINEL
- cadence: DAILY
- explicit occurrences: 8
- scoped series: 1
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### JAPAN_MOF_JGB_RSS

- source: `WSSRC-FIS-029` — Japan Ministry of Finance
- role: OFFICIAL_JAPAN_MOF_JGB_PUBLICATION_AND_CHANGE_RSS_SENTINEL
- cadence: DAILY
- explicit occurrences: 10
- scoped series: 1
- regions: East Asia
- categories: FISCAL_SOVEREIGN_FINANCE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### NZ_ELECTION_TIMETABLE_CHANGE_RSS

- source: `WSSRC-EL-NZ-002` — Electoral Commission New Zealand
- role: OFFICIAL_ELECTIONS_NZ_RSS_TIMETABLE_PAGE_UPDATE_SENTINEL
- cadence: EVERY_6_HOURS_DURING_ELECTION_PERIOD
- explicit occurrences: 6
- scoped series: 1
- regions: Oceania / Pacific
- categories: ELECTIONS_GOVERNANCE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### ONS_RELEASE_CALENDAR_RSS

- source: `WSSRC-MAC-006` — Office for National Statistics
- role: UPCOMING_RELEASE_DATETIME_SENTINEL
- cadence: DAILY
- explicit occurrences: 19
- scoped series: 6
- regions: Europe
- categories: MACROECONOMIC_RELEASE
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### RBA_FSR_RSS

- source: `WSSRC-FIN-001` — Reserve Bank of Australia
- role: PUBLICATION_COMPLETION_SENTINEL
- cadence: DAILY
- explicit occurrences: 2
- scoped series: 1
- regions: Oceania / Pacific
- categories: FINANCIAL_STABILITY_REGULATION
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED

### RBA_MPB_CALENDAR

- source: `WSSRC-CB-002` — Reserve Bank of Australia
- role: RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL
- cadence: DAILY
- explicit occurrences: 44
- scoped series: 4
- regions: Oceania / Pacific
- categories: MONETARY_FINANCIAL_POLICY
- readiness: LIVE_VALIDATED_ROBOTS_CONFORMANT_NO_AUTO_COMMIT
- automated monitoring use: CLEARED

### SARB_MPC_STATEMENTS_RSS

- source: `WSSRC-REG-013` — South African Reserve Bank
- role: OFFICIAL_SARB_MPC_STATEMENT_PUBLICATION_RSS_SENTINEL
- cadence: DAILY
- explicit occurrences: 2
- scoped series: 1
- regions: Africa
- categories: MONETARY_FINANCIAL_POLICY
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED_BOUNDED_OFFICIAL_RSS

### USDA_NASS_ASB_ICAL

- source: `WSSRC-COM-005` — USDA NASS
- role: OFFICIAL_NASS_ASB_ICAL_DATETIME_CHANGE_SENTINEL
- cadence: daily
- explicit occurrences: 5
- scoped series: 2
- regions: Cross-regional / Global
- categories: AGRICULTURE_FOOD
- readiness: LIVE_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: CLEARED_BOUNDED_OFFICIAL_ICAL

## Candidate source holdings

These are source-governance states only. Inclusion here does not authorise a route.

- candidate/pilot/endpoint-status sources with current canonical dependencies: **28**
- candidate/pilot/endpoint-status source holdings with no current canonical dependency: **9**


## CF quarantine boundary

- OPEC CE provenance work is quarantined under `OPEC_QUARANTINE.md`.
- Closed PR: `#113`; preserved branch: `feature/post-cd-pressure-audit-ce`.
- OPEC and occurrences `WSO-COM-A-0001` / `WSO-COM-A-0002` are excluded from CF candidate selection.
- This exclusion is non-blocking technical-debt management, not a claim that OPEC is analytically unimportant.
- Any future OPEC reactivation must follow the explicit protocol in `OPEC_QUARANTINE.md`.

