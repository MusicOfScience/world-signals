# WORLD SIGNALS — P1-D source-governance research v0.1

**Reference date:** 2026-09-04  
**Scope:** six bounded canonical-dependent source records selected after measured P1-C audit.  
**Method:** current primary-source review. Factual provenance, automated access and verification mode are assessed separately. Public accessibility, official status, machine readability and successful fetching are not permission grants.

## Selection

P1-D deliberately avoids a mechanical top-N and clears **40 canonical dependencies** across six jurisdictions and three domains:

| Source | Institution | Jurisdiction | Domain | Dependencies |
|---|---|---|---|---:|
| `WSSRC-CB-013` | Reserve Bank of Australia release schedule | Australia | monetary policy | 11 |
| `WSSRC-MAC-003` | U.S. Bureau of Economic Analysis | United States | macro releases | 10 |
| `WSSRC-MAC-024` | Statistics Bureau of Japan | Japan | macro releases | 8 |
| `WSSRC-REG-004` | Bank Indonesia | Indonesia | monetary policy | 4 |
| `WSSRC-REG2-006` | INDEC | Argentina | official statistics | 4 |
| `WSSRC-EL-KE-001` | Kenya Law / Constitution of Kenya | Kenya | elections | 3 |

This mix provides Australia, East Asia, Southeast Asia, Latin America, Africa and the United States, while avoiding another Europe-heavy central-bank tranche.

## `WSSRC-CB-013` — Reserve Bank of Australia release schedule

**Schedule surfaces**
- https://www.rba.gov.au/schedules-events/
- https://www.rba.gov.au/schedules-events/calendar.html?topics=monetary-policy-board
- https://www.rba.gov.au/monetary-policy/rba-board-minutes/2026/

**Rights**
- https://www.rba.gov.au/copyright/

The RBA states that most website material is under CC BY 4.0 subject to exclusions. The release schedule currently states that Monetary Policy Board minutes are published two weeks after each meeting and provides the release time; the topic calendar separately represents meetings, decision statements, media conferences and minutes. The existing WORLD SIGNALS source record already has a pilot HTML calendar monitor and reviewed runtime evidence.

**Governance conclusion**
- canonical provenance: `CLEARED_CURATED_FACTUAL_METADATA`
- automation: `ENDPOINT_REVIEW_REQUIRED`
- verification: `AUTOMATED_PILOT`

CC BY content permission is not treated as independent clearance for production polling. The RBA's distinct meeting-window, decision-release and later-minutes semantics must remain separate.

## `WSSRC-MAC-003` — U.S. Bureau of Economic Analysis

**Schedule**
- https://www.bea.gov/news/schedule

**Rights**
- https://www.bea.gov/help/faq/147

BEA states that, unless otherwise noted, website information is public domain and may be used or reproduced without specific permission. The release schedule is authoritative for GDP, PCE/personal-income and other releases, including estimate-vintage distinctions. No current primary-source evidence reviewed here expressly grants unrestricted schedule-page crawler/polling behaviour, and the registered route has no established live pilot parser.

**Governance conclusion**
- canonical provenance: `CLEARED_CURATED_FACTUAL_METADATA`
- automation: `ENDPOINT_REVIEW_REQUIRED`
- verification: `MANUAL_AUTHORITATIVE_RECHECK`

## `WSSRC-MAC-024` — Statistics Bureau of Japan

**Schedule**
- https://www.stat.go.jp/english/data/kakei/1562.htm

**Rights**
- https://www.stat.go.jp/english/info/riyou.html

The Statistics Bureau applies Japan's Public Data License 1.0 to covered content. It expressly permits free use, copying, public transmission, translation and modification, including commercial use, subject to attribution, change disclosure and third-party exceptions. The household income/expenditure schedule supplies release dates but not clock times; WORLD SIGNALS must not manufacture a time. The source already has a pilot schedule parser and research-verified runtime state.

**Governance conclusion**
- canonical provenance: `CLEARED_CURATED_FACTUAL_METADATA`
- automation: `ENDPOINT_REVIEW_REQUIRED`
- verification: `AUTOMATED_PILOT`

The content licence does not itself specify request/crawler behaviour.

## `WSSRC-REG-004` — Bank Indonesia

**Schedule**
- https://www.bi.go.id/en/publikasi/ruang-media/news-release/Pages/sp_2730825.aspx
- https://www.bi.go.id/en/publikasi/kalender/default.aspx

Bank Indonesia's current official material directly confirms the 2026 monthly two-day Board of Governors meetings. The institution explains that the two days form one integrated decision-making forum; policy determination occurs on day two. Targeted current review located privacy/public-information material but did not locate a source-specific website reuse licence, crawler policy or authorised feed sufficient to clear the schedule route.

**Governance conclusion**
- canonical provenance: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- automation: `PROHIBITED_OR_RIGHTS_HOLD`
- verification: `RIGHTS_HELD_MANUAL_ONLY`

The schedule remains authoritative for manual curated factual verification. Official central-bank status is not used to infer broader rights.

## `WSSRC-REG2-006` — INDEC Argentina

**Schedule**
- https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_2sem2026.pdf

**Rights / dissemination policy**
- https://www.indec.gob.ar/ftp/cuadros/publicaciones/politica_difusion_indec_ingles.pdf

INDEC's dissemination policy states that, except where specifically indicated, website material is under Creative Commons and may be copied and redistributed in any medium or format with primary-source citation and clear notice of modification. The current second-half 2026 dissemination calendar is authoritative for the remaining CPI publication dates and does not supply a clock time; none is inferred. No separate automation licence or request-policy clearance was identified for polling the calendar PDF/site.

**Governance conclusion**
- canonical provenance: `CLEARED_CURATED_FACTUAL_METADATA`
- automation: `ENDPOINT_REVIEW_REQUIRED`
- verification: `MANUAL_AUTHORITATIVE_RECHECK`

## `WSSRC-EL-KE-001` — Kenya Law / Constitution of Kenya

**Authority**
- https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng@2010-09-03

Kenya Law's current Constitution page is the correct legal authority for the fixed constitutional general-election rule and transition dependencies. The site states that, except for specifically licensed material, its contents are in the public domain and free of copyright restrictions. Legislative content is therefore suitable factual provenance. The Constitution supplies rule-based timing; it does not justify fixing a presidential inauguration date before result declaration and petition status resolve. No separate production-crawler permission was identified.

**Governance conclusion**
- canonical provenance: `CLEARED_CURATED_FACTUAL_METADATA`
- automation: `ENDPOINT_REVIEW_REQUIRED`
- verification: `MANUAL_AUTHORITATIVE_RECHECK`

## Held sources remain excluded

### `WSSRC-CB-009` — Swiss National Bank

Still excluded despite 18 dependencies. The registered decisions/history URL does not directly support the forward monetary-policy assessment schedule. Repair the source relationship before governance backfill.

### `WSSRC-EL-BR-001` — Brazil TSE

Still excluded. The electoral-resolution source supports election-cycle milestones but is not the correct provenance basis for the constitutionally grounded `2027-01-05` presidential inauguration/start date.

## Frozen P1-D classifications

| Source | Canonical provenance | Automated monitoring | Verification |
|---|---|---|---|
| `WSSRC-CB-013` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-MAC-003` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-MAC-024` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-REG-004` | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |
| `WSSRC-REG2-006` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-EL-KE-001` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |

These conclusions are operational governance classifications for WORLD SIGNALS, not legal advice. They authorise no registry mutation until the guarded P1-D plan, preflight and transaction gates pass.
