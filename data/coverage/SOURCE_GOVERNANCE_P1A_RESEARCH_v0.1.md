# WORLD SIGNALS — P1-A source-governance research v0.1

**Reviewed:** 2026-09-04  
**Scope:** six high-dependency canonical source identities selected from the P1 backlog  
**Canonical mutation authorised:** **NO**  
**Source-registry mutation in this infrastructure tranche:** **NO**  
**Automatic canonical commit:** **OFF**  
**Google Calendar writes:** **OFF**

## Purpose

P1-A is a bounded governance-backfill tranche. It records explicit modern source-governance classifications only where the existing source record plus current primary terms support them. It does **not** infer automated-monitoring permission from official status, public accessibility, machine readability, open factual content, or successful fetching/parsing.

The six approved sources are:

- `WSSRC-MAC-007` — National Bureau of Statistics of China — 36 canonical dependencies;
- `WSSRC-MAC-017` — India MoSPI — 17;
- `WSSRC-COM-003` — U.S. EIA Weekly Petroleum Status Report — 16;
- `WSSRC-COM-010` — FAO data-release calendar — 9;
- `WSSRC-HEALTH-001` — WHO governance calendar — 6;
- `WSSRC-CLIM-001` — UNFCCC COP31 — 3.

`WSSRC-EL-BR-001` / Brazil TSE is explicitly **held out** and is not part of P1-A.

This is operational source governance for WORLD SIGNALS, not a legal opinion.

## Research findings

### China NBS — `WSSRC-MAC-007`

Primary terms: <https://www.stats.gov.cn/english/nbs/200701/t20070104_59236.html>

NBS expressly permits users to download and use statistical data on its website and permits reasonable good-faith reprint/quotation subject to attribution and exclusions. The same terms contain security restrictions but do not expressly grant crawler/scraper access or define acceptable automated request behaviour.

Result:

- curated factual/schedule provenance: **cleared**;
- automated monitoring: **endpoint review required**;
- verification: **manual authoritative recheck** until a bounded endpoint route is separately cleared.

### India MoSPI — `WSSRC-MAC-017`

Primary guidance: <https://mospi.gov.in/faq>

MoSPI's revised 2026 Guidelines for Statistical Data Dissemination classify aggregated/analyzed information and publications such as National Accounts and CPI as Category A open-access data, available free of cost without registration, including for commercial use. This supports the curated factual content already used by WORLD SIGNALS. It does not by itself license arbitrary automated retrieval of the website.

The source also has a known operational conflict: the authoritative Advance Release Calendar PDF carries scheduled releases while the dynamic release-calendar surface has returned an empty state. Absence on that dynamic surface is not cancellation evidence.

Result:

- curated factual/schedule provenance: **cleared**;
- automated monitoring: **endpoint review required**;
- verification: **manual authoritative recheck** while the endpoint/parser conflict remains open.

### U.S. EIA — `WSSRC-COM-003`

Primary reuse source: <https://www.eia.gov/about/copyrights_reuse.php>

EIA states that U.S. Government publications on its site are public domain and may be used and distributed, subject to third-party exceptions. EIA also provides documented data services, but that does not make every HTML schedule page an unrestricted polling endpoint. The existing WPSR route has already demonstrated that publication-index state can lag underlying official data products.

Result:

- curated factual provenance: **cleared**;
- automated monitoring: **endpoint review required** for the schedule-page route;
- verification: **automated pilot**, reflecting existing validated read-only operational use without claiming general automation rights;
- automatic canonical commit remains prohibited.

### FAO — `WSSRC-COM-010`

Primary terms: <https://www.fao.org/contact-us/terms/en/>

FAO distinguishes its general website content from publications under its Open Access policy and statistical databases under a separate Open Data Licensing Policy. General website content may be copied/downloaded for private study, research and teaching and for non-commercial products/services with attribution. The WORLD SIGNALS release-calendar page is therefore not treated as though the separate statistical-database licence automatically governs it.

Result:

- canonical factual provenance: **manual informational reference only**;
- automated monitoring: **endpoint review required**;
- verification: **manual authoritative recheck**;
- no statistical-database licence is projected onto the release-calendar HTML surface.

### WHO — `WSSRC-HEALTH-001`

Primary terms: <https://www.who.int/about/policies/terms-of-use>

WHO's general website terms permit extracts for research/private study and require prior written authorization for substantial or other uses outside the stated educational/non-commercial scope. The observed user-facing iCal export on WHO event pages is a transport convenience, not evidence of a stable subscription feed or production automation permission.

Result:

- canonical factual provenance: **manual informational reference only**;
- automated monitoring: **rights hold**;
- verification: **rights-held manual only**.

Dataset-specific WHO licences are not projected onto this governance-calendar webpage.

### UNFCCC — `WSSRC-CLIM-001`

Primary terms: <https://unfccc.int/this-site/disclaimer>

UNFCCC states that official texts, data and documents are in the public domain with source acknowledgement, while the website terms separately govern site use and some material remains protected. The COP31 event page is authoritative for schedule facts, but WORLD SIGNALS does not infer that a general event webpage is therefore a cleared production polling endpoint.

Result:

- canonical factual provenance: **manual informational reference only**;
- automated monitoring: **rights hold**;
- verification: **rights-held manual only**;
- a future automated route would require a separately reviewed official document/feed/interface.

## Explicit Brazil/TSE hold — `WSSRC-EL-BR-001`

TSE Resolution 23.760 is the 2026 electoral calendar and was amended by Resolution 23.771 of 3 August 2026:

- <https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-760-de-2-de-marco-de-2026>
- <https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-771-de-3-de-agosto-de-2026>

The four existing WORLD SIGNALS milestones remain date-correct: first round 4 October 2026; conditional second round 25 October; diplomation deadline 18 December; presidential inauguration/start of mandate 5 January 2027.

The 5 January 2027 date is grounded in Constitution art. 82 as amended by Constitutional Amendment 111/2021, not in the TSE electoral-calendar source:

- <https://www4.planalto.gov.br/legislacao/portal-legis/legislacao-1/constituicao>
- <https://planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc111.htm>

Therefore this is a **source-scope/provenance defect, not a date defect**. P1-A must not backfill governance fields on `WSSRC-EL-BR-001`. Its source relationship must be repaired in a separate reviewed tranche. The canonical inauguration date must remain `2027-01-05` throughout P1-A.

## Frozen P1-A classifications

| Source | Canonical provenance | Automated monitoring | Verification mode |
|---|---|---|---|
| `WSSRC-MAC-007` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-MAC-017` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-COM-003` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-COM-010` | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-HEALTH-001` | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |
| `WSSRC-CLIM-001` | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |

## Transaction boundary

The later reviewed P1-A transaction may modify only `data/sources/registry.json`, and within that registry only the six approved records plus registry-level version/reference metadata. It must:

- leave the canonical registry byte-identical at v0.20 / 669;
- leave monitor expectations v0.7 byte-identical;
- leave monitor code byte-identical;
- leave `WSSRC-EL-BR-001` byte-identical;
- preserve the Brazil presidential inauguration/start date as `2027-01-05`;
- keep automatic canonical commit CLOSED;
- keep Google Calendar writes OFF.

Infrastructure in this branch supplies research, a frozen plan, a guarded migration script and regression tests only. It does not execute the source-registry transaction.
