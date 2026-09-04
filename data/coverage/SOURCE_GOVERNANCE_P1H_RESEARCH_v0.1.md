# WORLD SIGNALS — Source-governance P1-H research v0.1

**Review date:** 2026-09-04  
**Base:** canonical v0.20 / 669; source registry v1.59 / 223; monitor expectations v0.7  
**Authority boundary:** research/frozen-classification evidence only; no registry mutation is authorised by this document.

## Purpose

Select and research the next bounded P1 canonical-dependent source-governance cohort after P1-G without mechanically taking the highest dependency counts. The selection diagnostic ranked all **103 unresolved P1 sources** by near-term active horizon, active non-completed dependencies and total dependency, then applied source-scope integrity, regional/domain balance and governance-information value as independent constraints.

The unresolved P1 dependency footprint remains materially concentrated in Europe, North America and Oceania/Pacific. P1-H therefore deliberately samples underrepresented regions while retaining near-term analytical relevance.

## Frozen P1-H cohort

| Source | Region / jurisdiction | Domain | Canonical dependencies | Near-term reason |
|---|---|---|---:|---|
| `WSSRC-COM-001` — OPEC | Global / OPEC+ | Energy & commodities | 3 | Three active near-term OPEC/OPEC+ institutional occurrences |
| `WSSRC-MAC-016` — ESRI, Cabinet Office Japan | East Asia / Japan | Macroeconomic releases | 5 | GDP preliminary releases; next schedule date 2026-09-08 |
| `WSSRC-CB-011` — Reserve Bank of India | South Asia / India | Monetary policy | 2 | FY2026-27 MPC meeting windows; next window 2026-10-05–07 |
| `WSSRC-REG-006` — South African Reserve Bank | Africa / South Africa | Monetary policy | 2 | 2026 MPC announcements; next 2026-09-23 at 15:00 local source time |
| `WSSRC-REG-010` — Cámara de Diputados / Constitution of Mexico | Latin America / Mexico | Fiscal / sovereign finance | 2 | Constitutional budget submission and approval deadlines |
| `WSSRC-INT-001` — UN General Assembly | Global | International institutions | 2 | 81st-session opening and High-level Week in September 2026 |

**Total frozen canonical dependencies: 16.**

This lower dependency total is deliberate. It is preferable to a higher-count Europe/US/Australia tranche that would reproduce the very geographic skew WORLD SIGNALS is meant to audit.

## Source-by-source findings

### `WSSRC-COM-001` — OPEC

**Source scope:** the registered OPEC press-release / meeting-announcement surface is authoritative for OPEC and OPEC+ institutional announcements and current press releases. It is suitable as a manual factual reference for the canonical meeting occurrences already linked to it.

**Rights:** OPEC's current Terms and Conditions state that site Material is copyrighted by OPEC; without specific written authorisation users may not reproduce/distribute/display/publish/circulate Material to third parties and may not store Material in a shared electronic archive or database. Occasional attributed use in internal reports, educational/research work and client reports is separately permitted.

**Governance conclusion:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

No crawler/database permission is inferred from public accessibility or from the press-room HTML being parseable.

### `WSSRC-MAC-016` — Economic and Social Research Institute, Cabinet Office Japan

**Source scope:** the official ESRI Quarterly Estimates of GDP release schedule currently gives exact source-native dates and **08:50 JST** release times, including 8 September, 16 November and 8 December 2026, and expressly warns that the schedule may change.

**Rights:** Cabinet Office terms allow content to be freely used, copied, publicly transmitted, translated or modified subject to attribution and other stated conditions; the English terms are compatible with CC BY 4.0, and the current Japanese terms apply the Public Data License 1.0 unless a specific exception applies.

**Automation:** content reuse permission is not treated as crawler permission. The existing source record has pilot research/parser evidence, so verification may remain an automated pilot while production endpoint polling still requires review.

**Governance conclusion:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

Source-native **08:50 JST** precision and provisional/change caveats must be preserved.

### `WSSRC-CB-011` — Reserve Bank of India

**Source scope:** RBI's 23 March 2026 press release expressly schedules the FY2026-27 MPC meetings as multi-day windows: 6–8 April, 3–5 June, 3–5 August, **5–7 October**, 2–4 December 2026 and 3–5 February 2027.

The registered source supports the **meeting window**. It does not by itself authorise converting the final meeting day into a separately timed decision-release occurrence or inventing a clock time.

**Rights:** RBI's current Disclaimer and Website Policies state that material is protected by copyright; reproduction must be accurate and sourced, while unauthorised reproduction/distribution/commercial use is prohibited. RBI also reserves the right to restrict access. Internal-page hyperlinking requires specific permission. These terms are not a safe basis for automated production retrieval.

**Governance conclusion:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-REG-006` — South African Reserve Bank

**Source scope:** SARB's official MPC webcast page lists 2026 announcement dates and presentation times, including **23 September 2026 at 15:00** and **19 November 2026 at 15:00**.

**Rights:** SARB's current website disclaimer says its website material is protected by SARB intellectual-property rights and may not be copied, reproduced, adapted, published or distributed without prior written consent. It also reserves the ability to restrict access or change data formats.

**Governance conclusion:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-REG-010` — Cámara de Diputados / Constitution of Mexico

**Source scope:** the Cámara de Diputados publishes the current Constitution as an official legislative text; its current legislative library identifies the Constitution as amended through **3 March 2026**. Article 74 establishes the recurring federal expenditure-budget timetable: submission by 8 September and Chamber approval by 15 November (subject to the constitutional exceptions applicable in a presidential-inauguration year).

**Rights:** Article 14(VIII) of Mexico's Federal Copyright Law states that legislative, regulatory, administrative and judicial texts, and their official translations, are not subject to copyright protection under that law; publication must adhere to the official text and does not confer an exclusive edition right. This supports curated factual/legal deadline metadata, not wholesale reproduction of commentary or site design.

**Automation:** the copyright exclusion does not itself authorise automated polling of the Cámara website. No specific machine subscription/API route for this constitutional source is being cleared in P1-H.

**Governance conclusion:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

### `WSSRC-INT-001` — United Nations General Assembly

**Source scope:** the official 81st-session page says the session opens **8 September 2026**. The official high-level-meetings page labels its schedule **Provisional** and lists the 22–28 September general debate and the individual high-level meetings.

**Rights:** general UN website terms allow users to visit and download/copy Materials for personal, non-commercial use but do not grant resale, redistribution, compilation or derivative-work rights. UN copyright material remains otherwise all-rights-reserved. This is the same general rights environment already applied to the governed UNGA mandated-events source `WSSRC-INT-027`.

**Governance conclusion:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

The provisional label must remain source-native status; publication on an official UN page is not a reason to silently upgrade it to confirmed.

## Explicit exclusions / negative controls

### Brazil TSE — `WSSRC-EL-BR-001`

Still excluded. The electoral-calendar source relationship is not the correct provenance basis for the constitutionally grounded **2027-01-05** presidential inauguration/start date. P1-H must not modify the source record or canonical date.

### Swiss National Bank — `WSSRC-CB-009`

Still excluded despite high dependency. The registered decisions/history URL does not directly support the forward monetary-policy assessment schedule described by the source record. Repair source scope first.

## Selection critique

The diagnostic's raw top ranks included several Europe/US/Australia sources with greater dependency counts. They are not rejected; they are deferred. P1-H intentionally tests whether the governance backlog can be reduced without allowing a dependency metric to become a hidden geographic-weighting rule.

The six-source size is a bounded engineering convenience, not a standing quota. Future tranches may be smaller or larger when evidence warrants it.

## Transaction boundary

If this research is reviewed and merged, the subsequent P1-H transaction must:

1. be source-registry-only;
2. advance source registry **v1.59 → v1.60** without changing source count 223;
3. change exactly the six frozen source IDs above;
4. preserve canonical v0.20 / 669 byte-for-byte;
5. preserve monitor expectations v0.7 and live-monitor runner byte-for-byte;
6. preserve Brazil TSE and SNB held sources byte-for-byte;
7. preserve Brazil inauguration `start_local=2027-01-05`;
8. keep automatic canonical commit `false` and Google Calendar write `false`;
9. default to read-only preflight and require an explicit environment gate for apply.

No registry mutation is performed in the research/infrastructure PR.