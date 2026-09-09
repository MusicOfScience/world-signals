# WORLD SIGNALS — CF zero-category Monitor route diagnostic v0.1

Purpose: inspect the source-governance state behind Canonical occurrences in Monitor categories that currently have zero explicit configured coverage. This is a diagnostic, not a completeness target or permission to automate.

OPEC remains excluded under `OPEC_QUARANTINE.md`.

Zero-covered categories: CLIMATE_ENVIRONMENT, HEALTH_BIOSECURITY, PHYSICAL_CLIMATE_RISK

| # | Source | Institution | Region(s) | Category | Occ. | Readiness | Automated use | Rights block | Endpoint review |
|---:|---|---|---|---|---:|---|---|---|---|
| 1 | `WSSRC-RISK-002` | NOAA National Hurricane Center | Cross-regional / Global | PHYSICAL_CLIMATE_RISK | 2 | ENDPOINT_REVIEW_REQUIRED | ENDPOINT_REVIEW_REQUIRED | NO | YES |
| 2 | `WSSRC-HEALTH-001` | World Health Organization | Cross-regional / Global, Southeast Asia | HEALTH_BIOSECURITY | 7 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 3 | `WSSRC-CLIM-003` | Convention on Biological Diversity | Cross-regional / Global | CLIMATE_ENVIRONMENT | 4 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 4 | `WSSRC-CLIM-001` | UNFCCC | Cross-regional / Global | CLIMATE_ENVIRONMENT | 3 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 5 | `WSSRC-CLIM-002` | IPCC | Cross-regional / Global | CLIMATE_ENVIRONMENT | 3 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 6 | `WSSRC-RISK-001` | Australian Bureau of Meteorology | Oceania / Pacific | PHYSICAL_CLIMATE_RISK | 3 | RIGHTS_AUDIT_REQUIRED | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 7 | `WSSRC-CLIM-005` | UNFCCC | Cross-regional / Global | CLIMATE_ENVIRONMENT | 1 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 8 | `WSSRC-HEALTH-002` | World Health Organization | Cross-regional / Global | HEALTH_BIOSECURITY | 1 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 9 | `WSSRC-HEALTH-003` | Pan American Health Organization | Cross-regional / Global | HEALTH_BIOSECURITY | 1 | RIGHTS_OR_LICENSE_HOLD | NOT_RECORDED | YES | NO |
| 10 | `WSSRC-HEALTH-004` | WHO Regional Office for the Western Pacific | Oceania / Pacific | HEALTH_BIOSECURITY | 1 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 11 | `WSSRC-HEALTH-005` | WHO Regional Office for Europe | Europe | HEALTH_BIOSECURITY | 1 | RIGHTS_OR_LICENSE_HOLD | NOT_RECORDED | YES | NO |
| 12 | `WSSRC-RISK-004` | Fiji Meteorological and Hydrological Services / RSMC Nadi Tropical Cyclone Centre | Oceania / Pacific | PHYSICAL_CLIMATE_RISK | 1 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |
| 13 | `WSSRC-RISK-005` | India Meteorological Department | South Asia | PHYSICAL_CLIMATE_RISK | 1 | RIGHTS_OR_LICENSE_HOLD | PROHIBITED_OR_RIGHTS_HOLD | YES | NO |

## Detail

### 1. WSSRC-RISK-002 — NOAA National Hurricane Center

- jurisdiction: Atlantic basin
- domain: physical_climate_risk
- regions: Cross-regional / Global
- categories: PHYSICAL_CLIMATE_RISK
- canonical occurrences: 2
- series: WSER-RISK-ATL-HURR
- occurrence ids: WSO-COM-A-0049, WSO-COM-A-0050
- monitoring readiness: ENDPOINT_REVIEW_REQUIRED
- automated monitoring use: ENDPOINT_REVIEW_REQUIRED
- verification mode: MANUAL_AUTHORITATIVE_RECHECK
- already configured Monitor source: NO
- rights/automation block detected: NO
- endpoint review still required: YES

### 2. WSSRC-HEALTH-001 — World Health Organization

- jurisdiction: Global
- domain: health_biosecurity
- regions: Cross-regional / Global, Southeast Asia
- categories: HEALTH_BIOSECURITY
- canonical occurrences: 7
- series: WSER-HEALTH-WHA, WSER-HEALTH-WHO-EB, WSER-HEALTH-WHO-PBAC, WSER-HEALTH-WHO-RC
- occurrence ids: WSO-HEALTH-A-0002, WSO-HEALTH-A-0004, WSO-HEALTH-A-0007, WSO-HEALTH-A-0008, WSO-HEALTH-A-0009, WSO-HEALTH-A-0010, WSO-HEALTH-WHA-079
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 3. WSSRC-CLIM-003 — Convention on Biological Diversity

- jurisdiction: Global
- domain: climate_environment
- regions: Cross-regional / Global
- categories: CLIMATE_ENVIRONMENT
- canonical occurrences: 4
- series: WSER-CLIM-CBD-CART, WSER-CLIM-CBD-COP, WSER-CLIM-CBD-IMPLEMENT, WSER-CLIM-CBD-NAGOYA
- occurrence ids: WSO-CLIM-A-0004, WSO-CLIM-A-0005, WSO-CLIM-A-0006, WSO-CLIM-A-0007
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 4. WSSRC-CLIM-001 — UNFCCC

- jurisdiction: Global
- domain: climate_environment
- regions: Cross-regional / Global
- categories: CLIMATE_ENVIRONMENT
- canonical occurrences: 3
- series: WSER-CLIM-UNFCCC-CMA, WSER-CLIM-UNFCCC-CMP, WSER-CLIM-UNFCCC-COP
- occurrence ids: WSO-CLIM-A-0001, WSO-CLIM-A-0002, WSO-CLIM-A-0003
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 5. WSSRC-CLIM-002 — IPCC

- jurisdiction: Global
- domain: climate_environment
- regions: Cross-regional / Global
- categories: CLIMATE_ENVIRONMENT
- canonical occurrences: 3
- series: WSER-CLIM-IPCC-CDR, WSER-CLIM-IPCC-CITIES, WSER-CLIM-IPCC-SLCF
- occurrence ids: WSO-CLIM-A-0008, WSO-CLIM-A-0009, WSO-CLIM-A-0010
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 6. WSSRC-RISK-001 — Australian Bureau of Meteorology

- jurisdiction: Australia
- domain: physical_climate_risk
- regions: Oceania / Pacific
- categories: PHYSICAL_CLIMATE_RISK
- canonical occurrences: 3
- series: WSER-RISK-AU-TC
- occurrence ids: WSO-COM-A-0051, WSO-COM-A-0052, WSO-RISK-AU-TC-2025-26
- monitoring readiness: RIGHTS_AUDIT_REQUIRED
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 7. WSSRC-CLIM-005 — UNFCCC

- jurisdiction: Global
- domain: climate_environment
- regions: Cross-regional / Global
- categories: CLIMATE_ENVIRONMENT
- canonical occurrences: 1
- series: WSER-CLIM-UNFCCC-SB
- occurrence ids: WSO-CLIM-UNFCCC-SB64-202606
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 8. WSSRC-HEALTH-002 — World Health Organization

- jurisdiction: Global
- domain: health_biosecurity
- regions: Cross-regional / Global
- categories: HEALTH_BIOSECURITY
- canonical occurrences: 1
- series: WSER-HEALTH-WHO-IGWG
- occurrence ids: WSO-HEALTH-A-0001
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 9. WSSRC-HEALTH-003 — Pan American Health Organization

- jurisdiction: Americas
- domain: health_biosecurity
- regions: Cross-regional / Global
- categories: HEALTH_BIOSECURITY
- canonical occurrences: 1
- series: WSER-HEALTH-WHO-RC
- occurrence ids: WSO-HEALTH-A-0003
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: NOT_RECORDED
- verification mode: NOT_RECORDED
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 10. WSSRC-HEALTH-004 — WHO Regional Office for the Western Pacific

- jurisdiction: Western Pacific
- domain: health_biosecurity
- regions: Oceania / Pacific
- categories: HEALTH_BIOSECURITY
- canonical occurrences: 1
- series: WSER-HEALTH-WHO-RC
- occurrence ids: WSO-HEALTH-A-0005
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 11. WSSRC-HEALTH-005 — WHO Regional Office for Europe

- jurisdiction: Europe
- domain: health_biosecurity
- regions: Europe
- categories: HEALTH_BIOSECURITY
- canonical occurrences: 1
- series: WSER-HEALTH-WHO-RC
- occurrence ids: WSO-HEALTH-A-0006
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: NOT_RECORDED
- verification mode: NOT_RECORDED
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 12. WSSRC-RISK-004 — Fiji Meteorological and Hydrological Services / RSMC Nadi Tropical Cyclone Centre

- jurisdiction: South-West Pacific / RSMC Nadi area of responsibility
- domain: physical_climate_risk
- regions: Oceania / Pacific
- categories: PHYSICAL_CLIMATE_RISK
- canonical occurrences: 1
- series: WSER-RISK-SWP-TC
- occurrence ids: WSO-RISK-A-0001
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

### 13. WSSRC-RISK-005 — India Meteorological Department

- jurisdiction: India
- domain: physical_climate_risk
- regions: South Asia
- categories: PHYSICAL_CLIMATE_RISK
- canonical occurrences: 1
- series: WSER-RISK-IN-HEAT-OUTLOOK
- occurrence ids: WSO-RISK-A-0002
- monitoring readiness: RIGHTS_OR_LICENSE_HOLD
- automated monitoring use: PROHIBITED_OR_RIGHTS_HOLD
- verification mode: RIGHTS_HELD_MANUAL_ONLY
- already configured Monitor source: NO
- rights/automation block detected: YES
- endpoint review still required: NO

