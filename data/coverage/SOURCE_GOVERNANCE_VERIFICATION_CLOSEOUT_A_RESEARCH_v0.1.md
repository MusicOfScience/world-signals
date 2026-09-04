# WORLD SIGNALS — Source Governance Verification Closeout A research v0.1

**Status:** FROZEN FOR REVIEW  
**Research date:** 2026-09-05  
**Baseline:** canonical v0.21 / 669; source v1.61 / 224; monitor expectations v0.7  
**Purpose:** choose the next P1 source-governance work from evidence, not from a mechanical P1-I sequence.

## Selection finding

The post-repair generic audit contains **95 P1 canonical-dependent sources**. A fresh read-only active-horizon diagnostic ranked future dependencies first, then checked source scope, region, domain and governance-information value.

A raw active-horizon top-N is unsuitable: the near-term queue is heavily concentrated in United States, Australia and Europe and in macro/fiscal releases. Selecting mechanically from that ranking would reproduce the geographic bias the project is explicitly designed to resist.

A second diagnostic isolated records where `verification_mode` is the **only** missing modern governance field. It found exactly **8 P1 sources**, and all eight have a future canonical dependency:

| Source | Jurisdiction | Future canonical occurrence | Existing provenance / automation state | Decision |
|---|---|---|---|---|
| `WSSRC-INT-010` APEC Secretariat | Asia-Pacific | 2026-09-10 | cleared factual / rights hold | SELECT |
| `WSSRC-INT-017` AIIB | Global/Asia | 2026-09-28 | manual informational / rights hold | SELECT |
| `WSSRC-REG2-002` Royal Thai Government | Thailand | 2026-10-01 | manual informational / rights hold | SELECT |
| `WSSRC-REG5-001` Government Electronic Newspaper | Vietnam | 2026-10-20 | cleared factual / endpoint review | **HOLD — source-scope review** |
| `WSSRC-REG6-002` Morocco MEF / legal portal | Morocco | 2026-10-20 | manual informational / rights hold | SELECT |
| `WSSRC-REG-011` Parliament of South Africa | South Africa | 2026-10-28 | manual informational / rights hold | SELECT |
| `WSSRC-INT-026` Philippines PCO | ASEAN / Philippines | 2026-11-13 | cleared factual / endpoint review | SELECT |
| `WSSRC-REG6-001` Kenya Law / National Treasury | Kenya | 2027-02-15 | cleared factual / endpoint review | SELECT |

The selected cohort is therefore **seven**, not because seven is a target tranche size, but because seven survive the evidence and source-scope tests.

## Why Vietnam is held

The registered source is a Government Electronic Newspaper article. Current direct National Assembly evidence is now available from the National Assembly portal itself and supports the 20 October 2026 opening of the second session of the 16th National Assembly, including the provisional two-phase sitting window.

Direct official evidence:

- https://quochoi.vn/tintuc/Pages/tin-hoat-dong-cua-quoc-hoi.aspx?ItemID=99777

The National Assembly source is first-order institutional provenance and is materially better scoped than a government-news report. `WSSRC-REG5-001` must therefore **not** be completed merely by adding `verification_mode`; source scope should be reviewed first. This is analogous in principle to the earlier Brazil repair: do not make an incomplete source record look governance-complete when the source identity itself deserves reconsideration.

## Dependency-count integrity finding

A full source-registry check compared stored `canonical_dependency_count` helpers with counts derived from canonical truth:

- 224 source records;
- 152 source IDs actually used by canonical occurrences;
- **0 orphan canonical source IDs**;
- **1 present-but-wrong stored count:** `WSSRC-INT-010` APEC stores 0, canonical truth is 1;
- 8 legacy source records omit the helper field entirely.

Architecture decision:

1. Canonical-derived dependency count is authoritative.
2. Do **not** bulk-fill the eight absent legacy helper fields merely for cosmetic uniformity.
3. If `canonical_dependency_count` is present, it must agree with canonical truth.
4. Because APEC is selected for this transaction, repair its stored helper from **0 → 1** at the same time.
5. Future validation should enforce present-value consistency without turning the denormalised helper into a second canonical truth.

## Current authoritative evidence and verification classifications

### `WSSRC-INT-010` — APEC Secretariat

Current APEC event material lists the Energy Ministerial Meeting for 8–11 September 2026 and the 16th Energy Ministers Meeting for **10–11 September 2026** in Beijing.

- event evidence: https://www.apec.org/
- event calendar: https://www.apec.org/engage-with-us/events-calendar
- terms: https://www.apec.org/termsofuse

APEC permits attributed reproduction under stated conditions but retains website access/control rights and does not provide a specific production-polling grant. Existing `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD` is not reopened.

**Frozen verification mode:** `RIGHTS_HELD_MANUAL_ONLY`.

### `WSSRC-INT-017` — Asian Infrastructure Investment Bank

AIIB's current Annual Meeting pages schedule the 2026 meeting for **28–29 September 2026 in Doha**, while explicitly noting contingency arrangements and that final decisions will be taken nearer the time.

- event evidence: https://www.aiib.org/en/news-events/events/annual-meetings/2026/overview/index.html
- overview: https://www.aiib.org/en/news-events/events/annual-meetings/overview/index.html
- copyright: https://www.aiib.org/en/general/copyright/index.html

AIIB limits website copying to personal/non-commercial use subject to conditions; no production automation permission is inferred. Existing rights hold remains appropriate. The contingency wording also makes human authoritative recheck particularly important.

**Frozen verification mode:** `RIGHTS_HELD_MANUAL_ONLY`.

### `WSSRC-REG2-002` — Royal Thai Government

The Royal Thai Government's current FY2027 budget guidance states that the Budget Act is intended to be promulgated in time for **1 October 2026**.

- event evidence: https://www.thaigov.go.th/en/news/163028
- website policy: https://www.thaigov.go.th/en/policy

The website policy expressly says users must not access or attempt to access services by means other than those provided, including automated methods such as scripts, unless explicitly authorised. Existing automation rights hold is therefore direct rather than inferred.

**Frozen verification mode:** `RIGHTS_HELD_MANUAL_ONLY`.

### `WSSRC-REG6-002` — Morocco Ministry of Economy and Finance / legal portal

The Ministry's official budget-process material states that the annual Finance Bill is deposited at the Chamber of Representatives on **20 October**; current 2027 budget-preparation material is also published on the Ministry portal.

- process evidence: https://www.finances.gov.ma/bsg/ministere/Pages/processus-de-preparation-du-plf-et-de-son-adoption.aspx
- 2027 budget page: https://www.finances.gov.ma/fr/vous-orientez/Pages/plf2027.aspx
- current 2027 preparation context: https://www.finances.gov.ma/en/Pages/detail-actualite.aspx?fiche=7794

The existing source record is already classified `PROHIBITED_OR_RIGHTS_HOLD`; this transaction does not reopen or broaden that rights conclusion.

**Frozen verification mode:** `RIGHTS_HELD_MANUAL_ONLY`.

### `WSSRC-REG-011` — Parliament of the Republic of South Africa

Parliament's official **2026 Parliamentary Programme Framework** explicitly lists tabling of the 2026 Medium-Term Budget Policy Statement and Adjustments Budget on **28 October 2026**.

- programme landing page: https://www.parliament.gov.za/parliament-programme
- framework PDF: https://www.parliament.gov.za/storage/app/media/Programmes/2025/11-12-2025/Parliamentary_Programme_Framework_2026.pdf
- disclaimer: https://parliament.gov.za/disclaimer

Parliament permits website content use for informational/reference and non-commercial purposes while reserving other rights. Existing automation rights hold remains conservative and is not reopened.

**Frozen verification mode:** `RIGHTS_HELD_MANUAL_ONLY`.

### `WSSRC-INT-026` — Presidential Communications Office, Philippines

Recent PCO material states that the 49th ASEAN Summit and Related Meetings will take place in Metro Manila on **13–15 November 2026**.

- event evidence: https://pco.gov.ph/news_releases/president-marcos-welcomes-assessment-of-aseans-growing-global-influence-palace-official/

PCO states that its content is in the public domain unless otherwise stated. That supports curated factual provenance, but public-domain status is not an endpoint-polling licence. Existing `ENDPOINT_REVIEW_REQUIRED` is preserved; no automated pilot is authorised by this work.

**Frozen verification mode:** `MANUAL_AUTHORITATIVE_RECHECK`.

### `WSSRC-REG6-001` — Kenya Law / National Treasury of Kenya

Kenya's Public Finance Management Act requires the National Treasury to submit the Budget Policy Statement to Parliament by **15 February each year**.

- current law: https://new.kenyalaw.org/akn/ke/act/2012/18/eng@2025-11-04
- Copyright Act: https://new.kenyalaw.org/akn/ke/act/2001/12/eng@2022-12-31

Kenyan copyright law excludes written law and judicial decisions from the definition of literary work. That supports use of the legal rule as factual/constitutional provenance, but it does not independently authorise unrestricted automated polling of Kenya Law infrastructure. Existing endpoint-review state remains intact.

**Frozen verification mode:** `MANUAL_AUTHORITATIVE_RECHECK`.

## Frozen transaction boundary

A later guarded transaction may change **only** `data/sources/registry.json`:

- source v1.61 / 224 → v1.62 / 224;
- seven selected sources gain `verification_mode`, review date and review basis;
- APEC additionally repairs stored `canonical_dependency_count` 0 → 1;
- canonical remains v0.21 / 669;
- change ledger remains v0.10;
- monitor expectations remain v0.7;
- no monitor route is activated;
- automatic canonical commit remains false;
- Google Calendar write remains false;
- Vietnam remains untouched and explicitly held for source-scope review.

This is **Verification Closeout A**, not an automatic P1-I conveyor-belt tranche.
