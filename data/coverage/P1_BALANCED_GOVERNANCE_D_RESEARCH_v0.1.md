# WORLD SIGNALS — P1 balanced source-governance D research v0.1

**Status:** FROZEN FOR REVIEW  
**Reference date:** 2026-09-05  
**Repository base:** `ccb8c3aae742b20d0930cde89766fb8dbe481b90` (merged PR #35)  
**Canonical registry:** v0.24 / 669  
**Source registry:** v1.65 / 226  
**Change ledger:** v0.13

## Selection logic after cohort C

The current source-governance audit contains 74 P1 canonical-dependent records with incomplete modern governance. A fresh production diagnostic showed that only 70 have a still-forward, non-completed primary dependency from 2026-09-05; four remain P1 by the governance audit definition but have no forward-starting dependency.

The diagnostic also established two important scope boundaries:

1. **South Asia:** no forward-active P1 source remains in South Asia after CBSL was closed in cohort C. The continuing canonical South Asia diversity deficit is therefore a **coverage/population research problem**, not something source-governance backfill can repair.
2. **Physical climate risk:** only one forward-active P1 source remains in the category, NOAA/NHC Atlantic hurricane climatology. Closing its governance contract does **not** add canonical series diversity; the category's remaining breadth deficit also belongs to later coverage/population work.

This cohort is therefore selected for source-governance leverage and cross-domain balance without claiming to repair canonical coverage merely by filling governance fields.

Research cohort:

| Source | Domain | Primary dependencies | Decision |
|---|---|---:|---|
| `WSSRC-RISK-002` | physical climate risk | 2 | Governance completion only. |
| `WSSRC-COM-009` | energy | 5 | Governance completion only; no automated-pilot claim. |
| `WSSRC-COM-008` | agriculture/food | 4 | Governance completion only; no automated-pilot claim. |
| `WSSRC-INT-013` | international institutions / BRICS | 1 | Governance completion plus stronger event-specific PIB evidence retained under the existing year-specific host-source family. |
| `WSSRC-HEALTH-002` | health/biosecurity | 1 | Complete modern governance under existing WHO rights hold. |
| `WSSRC-TRD-002` | trade | 1 | Provenance decomposition: dispute-status source remains primary; add separate WTO DSU legal-authority source. Timing window unchanged. |
| `WSSRC-REG2-003` | Chile fiscal | 1 | Governance completion only. |
| `WSSRC-EL-VIC-001` | Australian elections | 3 | Governance completion only. |

## Implementation-evidence audit

A repository-wide scan of `src`, `scripts`, `tests`, `fixtures` and `data/monitor` found **no source-specific implementation or fixture evidence for any of the eight selected sources**. In particular, legacy values such as `commodity-a-0.1`, `trade-a-0.1`, `regional-b-0.1` and `election-a-0.1` are registry metadata, not proof of an operating parser.

Frozen rule for this cohort:

- machine-readable formats or a stored `parser_version` do not justify `AUTOMATED_PILOT`;
- a source receives automated-pilot verification only after actual implementation, fixture and operating evidence exists;
- otherwise an authoritative, rights-compatible source remains `MANUAL_AUTHORITATIVE_RECHECK` with `ENDPOINT_REVIEW_REQUIRED`;
- sources with unresolved or restrictive production rights remain `RIGHTS_HELD_MANUAL_ONLY`.

## 1. NOAA/NHC Atlantic hurricane season — `WSSRC-RISK-002`

Authority:

- https://www.nhc.noaa.gov/climo/
- NHC explicitly states the Atlantic hurricane season runs **1 June to 30 November** and notes that storms can occur outside the official season.

Rights benchmark:

- https://www.weather.gov/disclaimer/
- NOAA/NWS states government-server information is public domain unless specifically annotated otherwise and may be used freely subject to non-endorsement/misrepresentation restrictions.

Canonical conclusion:

- existing 2026 and 2027 `ALL_DAY_RANGE` season records are correctly modeled;
- the climatological season is a **risk window**, not a forecast that a storm will occur;
- no canonical mutation is authorised.

Governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## 2. EIA Short-Term Energy Outlook — `WSSRC-COM-009`

Authority:

- https://www.eia.gov/outlooks/steo/release_schedule.php
- current schedule confirms 9 Sep, 6 Oct, 10 Nov and 8 Dec 2026 plus 12 Jan 2027, with the normal 12:00–12:15 ET release window. The page now extends further into 2027, but **this governance transaction does not populate additional occurrences**.

Rights and machine route:

- https://www.eia.gov/about/copyrights_reuse.php
- https://www.eia.gov/opendata/terms-of-service.php
- EIA states US government publications are public domain and may be used/distributed with acknowledgement; its API terms expressly permit programmatic retrieval of API data.
- The existence of the EIA API does not prove that the STEO release-schedule proposition is exposed through a reviewed API route.
- Repository inspection found no STEO-specific parser/fixture implementation.

Governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

No canonical mutation or new monitor route is authorised.

## 3. USDA WASDE — `WSSRC-COM-008`

Authority:

- https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report
- the current USDA page explicitly lists 2026 WASDE releases at 12:00 ET, including **11 Sep, 9 Oct, 10 Nov and 10 Dec**.
- no 2027 WASDE dates are manufactured until USDA publishes them.

Rights:

- official-duty USDA works are US Government works and generally not subject to US copyright; USDA sites also warn that third-party material can have separate rights.
- only factual schedule metadata is retained here.

Implementation:

- report outputs exist in PDF/XML/Excel/Text, but repository inspection found no WASDE-specific parser/fixture implementation.

Governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

No canonical mutation is authorised.

## 4. BRICS India 2026 — `WSSRC-INT-013`

Existing source identity:

- Government of India / BRICS India 2026 host-government source family.
- registered primary URL: https://www.pib.gov.in/

Stronger event-specific evidence:

- https://www.pib.gov.in/PressReleasePage.aspx?PRID=2305262&lang=2&reg=48
- the Prime Minister states he looks forward to welcoming President Putin to the **18th BRICS Summit on 12–13 September 2026**.

Rights:

- https://www.pib.gov.in/content/132_2_Copyright-Policy.aspx?lang=1&reg=1
- PIB permits reproduction of its material free of charge without prior approval, excluding third-party content, provided it is reproduced accurately and the source is prominently acknowledged.

Architecture decision:

- **do not create a new BRICS source ID.** `WSSRC-INT-013` is already explicitly a 2026 host-government source family, so the event-specific PIB release is retained as stronger backup evidence inside that stable identity.
- no date, host or certainty mutation is authorised.

Governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

## 5. WHO Pandemic Agreement IGWG — `WSSRC-HEALTH-002`

Authority:

- https://www.who.int/about/governance/world-health-assembly/intergovernmental-working-group-on-the-who-pandemic-agreement
- WHO's current meeting timeline confirms the eighth IGWG meeting on **14–18 September 2026**.

Rights:

- https://www.who.int/about/policies/terms-of-use
- WHO allows extracts for research/private study but not sale or commercial use; substantial or other use requires prior written authorisation.
- the existing source already records a production rights hold and a manual-only activation state.

Governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

No canonical mutation is authorised.

## 6. WTO DS646 — `WSSRC-TRD-002` plus new legal source

Dispute-status authority:

- existing source: https://www.wto.org/english/news_e/news26_e/ds646rfc_30jul26_468_e.htm
- current WTO case page: https://www.wto.org/english/tratop_e/dispu_e/cases_e/ds646_e.htm
- WTO records that Brazil requested consultations on **27 July 2026** and that the request was circulated on **30 July 2026**.

Legal authority:

- https://www.wto.org/english/tratop_e/dispu_e/dsu_e.htm
- DSU Article 4.7 states that if consultations fail, panel-request eligibility arises after **60 days from the date of receipt of the consultation request**.

Existing canonical handling is correct:

- `WSO-TRD-A-0002` is conditional and PROVISIONAL;
- its 25–28 September 2026 date window is explicitly evidence-bounded because the accessible official evidence establishes request/circulation dates but not the US receipt date;
- the previous exact 28 September derivation was already withdrawn;
- **no timing, window, condition or certainty change is authorised now.**

Provenance architecture:

- retain `WSSRC-TRD-002` as the primary dispute-status source;
- add `WSSRC-TRD-008` as a separate first-order WTO DSU legal-text source;
- add `legal_basis_source_id = WSSRC-TRD-008` and `governing_instrument = WTO Dispute Settlement Understanding, Article 4.7` to the existing occurrence;
- preserve assertion identities and stable occurrence identity.

Rights distinction:

- https://www.wto.org/english/info_e/copyrights_permissions_e.htm
- WTO states unrestricted official documents and legal texts are free for public use; ordinary WTO website material has tighter non-commercial/commercial-permission rules.
- that difference reinforces the source split rather than collapsing news/status and legal authority into one source contract.

Existing dispute-source governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

New DSU legal source governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`
- no production monitor activation.

## 7. Chile Budget 2027 — `WSSRC-REG2-003`

Authority:

- https://www.dipres.gob.cl/598/w3-article-419249.html
- DIPRES states that the 2027 Budget process culminates with submission of the bill to Congress **no later than 30 September 2026**.

Rights:

- no general DIPRES reuse or crawler permission was identified in this review;
- DIPRES publications commonly carry explicit `Todos los derechos reservados` copyright notices;
- public accessibility and transparency obligations are not treated as a content-reuse or production-automation licence.

Governance:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`

The existing 30 September legal/policy latest boundary remains unchanged.

## 8. Victoria 2026 State Election — `WSSRC-EL-VIC-001`

Authority:

- https://www.vec.vic.gov.au/voting/types-of-elections/state-elections
- VEC confirms the 28 November 2026 election and the 3 November writ milestone; current information-session material explicitly states the writs are issued at **6 pm on 3 November**.
- VEC also confirms return of writs on or before 19 December.

Rights:

- https://vec.vic.gov.au/legal
- VEC provides website material under **CC BY 4.0**, except images/video/branding and third-party material.

Implementation:

- repository inspection found no VEC-specific parser/fixture implementation despite the legacy `election-a-0.1` registry label.

Governance:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

No canonical date/time mutation is authorised.

## Deferred/inactive P1 note

Four governance-P1 sources had no forward-starting dependency under the 2026-09-05 diagnostic. They are not silently discarded:

- AOFM: elapsed 3–4 Sep issuance occurrences;
- Pacific Islands Forum: meeting already active from 30 Aug;
- USTR US–Mexico negotiating-round window: expected start had elapsed;
- EU Chips Act review: legitimately `COMPLETED_BEFORE_DEADLINE`; canonical evidence records Commission completion on 3 Jun 2026 ahead of the 20 Sep statutory latest date.

They can be closed in a later inactive/elapsed governance pass, but they are not allowed to displace current forward-active source work merely because the audit labels them P1.

## Frozen transaction architecture

If later reviewed and applied, cohort D is a **four-production-file transaction**:

1. `data/canonical/registry.json`
2. `data/sources/registry.json`
3. `data/changes/ledger.json`
4. `data/coverage/biosecurity_overlay.json`

Target post-state, subject to simulation:

- canonical v0.24 → **v0.25**, 669 occurrences unchanged;
- sources v1.65 → **v1.66**, 226 → **227** sources;
- ledger v0.13 → **v0.14**;
- biosecurity overlay checkpoint v0.24 → **v0.25**, 669 unchanged;
- governance: **90 fully explicit / 137 incomplete / 66 P1 / 71 P2**.

Exactly one existing canonical occurrence changes: `WSO-TRD-A-0002`, and only to add explicit legal-basis provenance. Its timing/window/certainty/condition/assertion identity remains unchanged.

No monitor configuration, parser implementation, web UI, Calendar output or expectations file changes are authorised.

## Protected invariants

The guarded helper/tests must prove:

- canonical occurrence count and ordering remain 669;
- only `WSO-TRD-A-0002` changes canonically;
- its `2026-09-25` → `2026-09-28` expected window remains byte-identical;
- it stays CONDITIONAL, PROVISIONAL, `condition_state=PENDING`, `procedural_eligibility_only=true`;
- all assertion IDs remain unchanged;
- every selected non-WTO canonical occurrence remains byte-identical;
- Malaysia Budget stays 9 Oct 2026 CONFIRMED with cohort-C semantics intact;
- Brazil inauguration stays 5 Jan 2027;
- India Budget 2027–28 remains unscheduled TBC;
- Colombia source split remains intact;
- automatic canonical commit remains false;
- Google Calendar write remains false;
- no live-monitor route is added;
- new `WSSRC-TRD-008` is legal provenance only and has zero primary `source_id` dependencies.

This research freezes evidence and architecture only. Production mutation requires a fresh branch from the exact merged preparation baseline, an explicit write gate, exact-diff enforcement and independent committed-state audit.
