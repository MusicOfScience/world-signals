# WORLD SIGNALS — CF Monitor candidate shortlist v0.1

This is a source-aware diagnostic shortlist derived from the post-CD Monitor coverage audit. It is **not** a completeness score and does not authorise a route.

Selection rules:
- OPEC source `WSSRC-COM-001` and occurrences `WSO-COM-A-0001` / `WSO-COM-A-0002` are excluded under `OPEC_QUARANTINE.md`.
- Existing configured Monitor sources are excluded; this is a new-route pressure check.
- A zero-covered category is a review prompt, not a quota.
- Source readiness and rights outrank geographic/category balancing.
- Rights-held candidates remain visible only after route-viable candidates.

Current zero-covered Monitor categories: CLIMATE_ENVIRONMENT, HEALTH_BIOSECURITY, PHYSICAL_CLIMATE_RISK

| # | Source | Institution | Region(s) | Category gap | Canonical occ. | Readiness | Automated use | Rights hold |
|---:|---|---|---|---|---:|---|---|---|
| 1 | `WSSRC-CB-008` | Bank of Canada | North America | — | 11 | ENDPOINT_TEST_PRIORITY | ENDPOINT_REVIEW_REQUIRED | NO |
| 2 | `WSSRC-FIS-008` | Bank of Canada / Department of Finance Canada | North America | — | 5 | ENDPOINT_TEST_PRIORITY | ENDPOINT_REVIEW_REQUIRED | NO |
| 3 | `WSSRC-MAC-009` | U.S. Bureau of Labor Statistics | North America | — | 4 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 4 | `WSSRC-MAC-010` | U.S. Bureau of Labor Statistics | North America | — | 4 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 5 | `WSSRC-MAC-018` | U.S. Bureau of Economic Analysis | North America | — | 4 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 6 | `WSSRC-MAC-019` | Federal Reserve Board | North America | — | 4 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 7 | `WSSRC-MAC-020` | U.S. Census Bureau | North America | — | 4 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 8 | `WSSRC-MAC-022` | Australian Bureau of Statistics | Oceania / Pacific | — | 4 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 9 | `WSSRC-FIS-004` | Australian Office of Financial Management | Oceania / Pacific | — | 3 | PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE | NOT_RECORDED | NO |
| 10 | `WSSRC-FIS-007` | Japan Ministry of Finance | East Asia | — | 10 | PILOT_VALIDATED_NO_AUTO_COMMIT | ENDPOINT_REVIEW_REQUIRED | NO |
| 11 | `WSSRC-MAC-024` | Statistics Bureau of Japan | East Asia | — | 8 | PILOT_VALIDATED_NO_AUTO_COMMIT | ENDPOINT_REVIEW_REQUIRED | NO |
| 12 | `WSSRC-MAC-025` | Japan Customs / Ministry of Finance | East Asia | — | 8 | PILOT_VALIDATED_NO_AUTO_COMMIT | ENDPOINT_REVIEW_REQUIRED | NO |
| 13 | `WSSRC-MAC-015` | Statistics Bureau of Japan | East Asia | — | 7 | PILOT_VALIDATED_NO_AUTO_COMMIT | ENDPOINT_REVIEW_REQUIRED | NO |
| 14 | `WSSRC-MAC-016` | Economic and Social Research Institute, Cabinet Office | East Asia | — | 5 | PILOT_VALIDATED_NO_AUTO_COMMIT | ENDPOINT_REVIEW_REQUIRED | NO |
| 15 | `WSSRC-REG-002` | Korea Law | East Asia | — | 1 | PILOT_VALIDATED_NO_AUTO_COMMIT | NOT_RECORDED | NO |
| 16 | `WSSRC-TECH-003` | European Commission / EUR-Lex | Europe | — | 2 | ENDPOINT_TEST_PRIORITY | NOT_RECORDED | NO |
| 17 | `WSSRC-TECH-002` | European Union / EUR-Lex | Europe | — | 1 | ENDPOINT_TEST_PRIORITY | NOT_RECORDED | NO |
| 18 | `WSSRC-CB-013` | Reserve Bank of Australia | Oceania / Pacific | — | 11 | PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | ENDPOINT_REVIEW_REQUIRED | YES |
| 19 | `WSSRC-MAC-011` | Australian Bureau of Statistics | Oceania / Pacific | — | 6 | PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | ENDPOINT_REVIEW_REQUIRED | YES |
| 20 | `WSSRC-MAC-012` | Australian Bureau of Statistics | Oceania / Pacific | — | 6 | PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | ENDPOINT_REVIEW_REQUIRED | YES |
| 21 | `WSSRC-MAC-021` | Australian Bureau of Statistics | Oceania / Pacific | — | 6 | PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | ENDPOINT_REVIEW_REQUIRED | YES |
| 22 | `WSSRC-MAC-023` | Australian Bureau of Statistics | Oceania / Pacific | — | 6 | PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | ENDPOINT_REVIEW_REQUIRED | YES |
| 23 | `WSSRC-MAC-013` | Australian Bureau of Statistics | Oceania / Pacific | — | 5 | PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING | NOT_RECORDED | YES |

## Candidate details

### 1. WSSRC-CB-008 — Bank of Canada

- jurisdiction: Canada
- regions: North America
- categories: MONETARY_FINANCIAL_POLICY
- zero-covered category hits: none
- canonical occurrences: 11
- series: WS.CB.BOC.POLICY_RATE_ANNOUNCEMENT
- occurrence ids: WSO-2cdc822808f15774, WSO-5bdbd194702e505a, WSO-670a12974d7c51d0, WSO-69baf115df815137, WSO-749ca6e3326b5da0, WSO-965c6475e37e526d, WSO-984c781317165f59, WSO-9c5198a309695094, WSO-a1380d6b86c55d26, WSO-a1ae6c266f2c54f3, WSO-ddb70f8ff05a58fb
- readiness: ENDPOINT_TEST_PRIORITY
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 2. WSSRC-FIS-008 — Bank of Canada / Department of Finance Canada

- jurisdiction: Canada
- regions: North America
- categories: FISCAL_SOVEREIGN_FINANCE
- zero-covered category hits: none
- canonical occurrences: 5
- series: WSER-FIS-CA-BOND
- occurrence ids: WSO-FIS-A-0025, WSO-FIS-A-0026, WSO-FIS-A-0027, WSO-FIS-A-0028, WSO-FIS-A-0029
- readiness: ENDPOINT_TEST_PRIORITY
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 3. WSSRC-MAC-009 — U.S. Bureau of Labor Statistics

- jurisdiction: United States
- regions: North America
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 4
- series: WSER-MAC-US-CPI
- occurrence ids: WSO-MAC-A-0001, WSO-MAC-A-0002, WSO-MAC-A-0003, WSO-MAC-A-0004
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 4. WSSRC-MAC-010 — U.S. Bureau of Labor Statistics

- jurisdiction: United States
- regions: North America
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 4
- series: WSER-MAC-US-EMP
- occurrence ids: WSO-MAC-A-0005, WSO-MAC-A-0006, WSO-MAC-A-0007, WSO-MAC-A-0008
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 5. WSSRC-MAC-018 — U.S. Bureau of Economic Analysis

- jurisdiction: United States
- regions: North America
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 4
- series: WSER-MAC-US-PIO
- occurrence ids: WSO-MAC-B-0001, WSO-MAC-B-0002, WSO-MAC-B-0003, WSO-MAC-B-0004
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 6. WSSRC-MAC-019 — Federal Reserve Board

- jurisdiction: United States
- regions: North America
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 4
- series: WSER-MAC-US-IP
- occurrence ids: WSO-MAC-B-0009, WSO-MAC-B-0010, WSO-MAC-B-0011, WSO-MAC-B-0012
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 7. WSSRC-MAC-020 — U.S. Census Bureau

- jurisdiction: United States
- regions: North America
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 4
- series: WSER-MAC-US-RETAIL
- occurrence ids: WSO-MAC-B-0005, WSO-MAC-B-0006, WSO-MAC-B-0007, WSO-MAC-B-0008
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 8. WSSRC-MAC-022 — Australian Bureau of Statistics

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 4
- series: WSER-MAC-AU-WPI
- occurrence ids: WSO-MAC-B-0025, WSO-MAC-B-0026, WSO-MAC-B-0027, WSO-MAC-B-0028
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 9. WSSRC-FIS-004 — Australian Office of Financial Management

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: FISCAL_SOVEREIGN_FINANCE
- zero-covered category hits: none
- canonical occurrences: 3
- series: WSER-FIS-AU-CGT
- occurrence ids: WSO-FIS-A-0003, WSO-FIS-A-0004, WSO-FIS-A-0005
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_ROUTE_CANDIDATE
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 10. WSSRC-FIS-007 — Japan Ministry of Finance

- jurisdiction: Japan
- regions: East Asia
- categories: FISCAL_SOVEREIGN_FINANCE
- zero-covered category hits: none
- canonical occurrences: 10
- series: WSER-FIS-JP-JGB
- occurrence ids: WSO-FIS-A-0015, WSO-FIS-A-0016, WSO-FIS-A-0017, WSO-FIS-A-0018, WSO-FIS-A-0019, WSO-FIS-A-0020, WSO-FIS-A-0021, WSO-FIS-A-0022, WSO-FIS-A-0023, WSO-FIS-A-0024
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 11. WSSRC-MAC-024 — Statistics Bureau of Japan

- jurisdiction: Japan
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 8
- series: WSER-MAC-JP-HHSPEND
- occurrence ids: WSO-MAC-B-0041, WSO-MAC-B-0042, WSO-MAC-B-0043, WSO-MAC-B-0044, WSO-MAC-B-0045, WSO-MAC-B-0046, WSO-MAC-B-0047, WSO-MAC-B-0048
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 12. WSSRC-MAC-025 — Japan Customs / Ministry of Finance

- jurisdiction: Japan
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 8
- series: WSER-MAC-JP-TRADE-PRELIM
- occurrence ids: WSO-MAC-C-0001, WSO-MAC-C-0002, WSO-MAC-C-0003, WSO-MAC-C-0004, WSO-MAC-C-0005, WSO-MAC-C-0006, WSO-MAC-C-0007, WSO-MAC-C-0008
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 13. WSSRC-MAC-015 — Statistics Bureau of Japan

- jurisdiction: Japan
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 7
- series: WSER-MAC-JP-LF
- occurrence ids: WSO-MAC-A-0057, WSO-MAC-A-0058, WSO-MAC-A-0059, WSO-MAC-A-0060, WSO-MAC-A-0061, WSO-MAC-A-0062, WSO-MAC-A-0063
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 14. WSSRC-MAC-016 — Economic and Social Research Institute, Cabinet Office

- jurisdiction: Japan
- regions: East Asia
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 5
- series: WSER-MAC-JP-GDP
- occurrence ids: WSO-MAC-A-0064, WSO-MAC-A-0065, WSO-MAC-A-0066, WSO-MAC-A-0067, WSO-MAC-A-0068
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: NO

### 15. WSSRC-REG-002 — Korea Law

- jurisdiction: South Korea
- regions: East Asia
- categories: FISCAL_SOVEREIGN_FINANCE
- zero-covered category hits: none
- canonical occurrences: 1
- series: WSER-REG-KR-BUDGET
- occurrence ids: WSO-REG-A-0003
- readiness: PILOT_VALIDATED_NO_AUTO_COMMIT
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 16. WSSRC-TECH-003 — European Commission / EUR-Lex

- jurisdiction: European Union
- regions: Europe
- categories: TECHNOLOGY_CRITICAL_INFRASTRUCTURE
- zero-covered category hits: none
- canonical occurrences: 2
- series: WSER-TECH-EU-AIACT
- occurrence ids: WSO-TECH-A-0003, WSO-TECH-A-0006
- readiness: ENDPOINT_TEST_PRIORITY
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 17. WSSRC-TECH-002 — European Union / EUR-Lex

- jurisdiction: European Union
- regions: Europe
- categories: TECHNOLOGY_CRITICAL_INFRASTRUCTURE
- zero-covered category hits: none
- canonical occurrences: 1
- series: WSER-TECH-EU-CHIPS
- occurrence ids: WSO-TECH-A-0002
- readiness: ENDPOINT_TEST_PRIORITY
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: NO

### 18. WSSRC-CB-013 — Reserve Bank of Australia

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MONETARY_FINANCIAL_POLICY
- zero-covered category hits: none
- canonical occurrences: 11
- series: WS.CB.RBA.MPB_MINUTES
- occurrence ids: WSO-0f044fd899005da9, WSO-2ab726f35230524f, WSO-723839c3553a5a08, WSO-8d62481833075169, WSO-a7c66c42517f5649, WSO-a9615ec64e235120, WSO-b52bb5efa4d95686, WSO-d9dc751b12bc5e36, WSO-e21cbbc6dfd45213, WSO-f124183ede6a52dc, WSO-f23f920db2ad57c8
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: YES

### 19. WSSRC-MAC-011 — Australian Bureau of Statistics

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 6
- series: WSER-MAC-AU-CPI
- occurrence ids: WSO-MAC-A-0013, WSO-MAC-A-0014, WSO-MAC-A-0015, WSO-MAC-A-0016, WSO-MAC-A-0017, WSO-MAC-A-0018
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: YES

### 20. WSSRC-MAC-012 — Australian Bureau of Statistics

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 6
- series: WSER-MAC-AU-LF
- occurrence ids: WSO-MAC-A-0019, WSO-MAC-A-0020, WSO-MAC-A-0021, WSO-MAC-A-0022, WSO-MAC-A-0023, WSO-MAC-A-0024
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: YES

### 21. WSSRC-MAC-021 — Australian Bureau of Statistics

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 6
- series: WSER-MAC-AU-MHSI
- occurrence ids: WSO-MAC-B-0019, WSO-MAC-B-0020, WSO-MAC-B-0021, WSO-MAC-B-0022, WSO-MAC-B-0023, WSO-MAC-B-0024
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: AUTOMATED_PILOT
- rights/automation hold: YES

### 22. WSSRC-MAC-023 — Australian Bureau of Statistics

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 6
- series: WSER-MAC-AU-TRADE
- occurrence ids: WSO-MAC-B-0029, WSO-MAC-B-0030, WSO-MAC-B-0031, WSO-MAC-B-0032, WSO-MAC-B-0033, WSO-MAC-B-0034
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: MANUAL_AUTHORITATIVE_RECHECK
- rights/automation hold: YES

### 23. WSSRC-MAC-013 — Australian Bureau of Statistics

- jurisdiction: Australia
- regions: Oceania / Pacific
- categories: MACROECONOMIC_RELEASE
- zero-covered category hits: none
- canonical occurrences: 5
- series: WSER-MAC-AU-GDP
- occurrence ids: WSO-MAC-A-0025, WSO-MAC-A-0026, WSO-MAC-A-0027, WSO-MAC-A-0028, WSO-MAC-A-0029
- readiness: PILOT_RESEARCH_VALIDATED_AUTOMATION_RIGHTS_PENDING
- automated monitoring use: NOT_RECORDED
- verification mode: not recorded
- rights/automation hold: YES

