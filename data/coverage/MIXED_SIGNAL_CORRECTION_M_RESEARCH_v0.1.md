# WORLD SIGNALS — Mixed-signal correction M research v0.1

**Review date:** 2026-09-05  
**Exact base main:** `01a37513c88d5fd3f4f6dce17d8c91e609016c87`  
**Base state:** canonical v0.26 / 669; source registry v1.67 / 228; biosecurity overlay v0.1  
**Authority boundary:** source/taxonomy freeze for a bounded population transaction; no quota population.

## Why this tranche

The post-#41 coverage audit still shows a structurally thin South Asia, but the currently defensible South Asian physical-risk and fiscal candidates remain blocked by source conflict or timing provenance. Africa and Southeast Asia are low-count but already institutionally diverse. Physical-climate risk remains shallow but must not be repaired by manufacturing or choosing between conflicting hazard-season definitions.

Correction M therefore adds three missing **signal systems**, not one row per country:

1. a systemically relevant African monetary-policy process with exact first-party meeting windows;
2. biological-security arms-control treaty governance that is absent from the canonical calendar but already represented in the analytical biosecurity map;
3. global animal-health standards governance, likewise already represented as a noncanonical analytical candidate.

The mixed tranche is intentionally only **three series / four occurrences**.

## 1. Central Bank of Nigeria MPC

**Primary authority:** Central Bank of Nigeria, 2026 MPC Meeting Calendar  
https://www.cbn.gov.ng/MonetaryPolicy/calendar.html

The official calendar states:

- meeting 307 — 21–22 September 2026;
- meeting 308 — 23–24 November 2026.

CBN describes the MPC as its highest monetary-policy making committee and states that it formulates monetary and credit policy. The current calendar publishes each meeting as a two-day forum. Historical CBN notices may publish separate Day 1 / Day 2 clock times, but those historical times are not a forward timing rule for meetings 307 or 308.

**Canonical treatment:** one `MONETARY_POLICY_DECISION_PROCESS` occurrence per published two-day meeting window. No synthetic day-two decision timestamp and no inferred communiqué time.

**Primary category:** `MONETARY_FINANCIAL_POLICY`.  
**Region:** Africa.  
**Source timezone:** `Africa/Lagos`.

**Rights/source governance:** CBN's Legal Disclaimer permits electronic or paper copying when CBN is expressly stated as the source and prohibits amendment/distortion. That supports curated factual provenance. It does not establish unrestricted automated retrieval.

Frozen governance:

- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

Rights authority: https://www.cbn.gov.ng/Legal.html

## 2. Biological Weapons Convention Working Group — tenth session

**Primary authority:** UNODA official BWC meeting service  
https://meetings.unoda.org/bwc-/biological-weapons-convention-working-group-on-the-strengthening-of-the-convention-tenth-session-2026

The official meeting page states that the tenth session will convene in the Tempus Building, Palais des Nations, Geneva, from **7–11 December 2026**, with daily sessions 10:00–13:00 and 15:00–18:00.

The split daily session hours describe the meeting programme. They are **not** represented as one continuous 10:00–18:00 canonical timestamp. The canonical object is the five-day treaty working-group session.

**Taxonomy:** this is biological security, but its institutional function is multilateral arms-control/disarmament governance. It would be taxonomically wrong to place it in `HEALTH_BIOSECURITY` merely to diversify the WHO-only human-health count.

**Primary category:** `INTERNATIONAL_INSTITUTIONS`.  
**Subcategory:** `biological_security_arms_control`.  
**Event type:** `TREATY_WORKING_GROUP_SESSION`.  
**Biosecurity analytical system:** `BIO-BIOLOGICAL-SECURITY-ARMS-CONTROL`.

**Rights/source governance:** general UN website terms permit personal non-commercial downloading/copying but do not grant redistribution, compilation or derivative-work rights. WORLD SIGNALS therefore uses the page as manually checked authoritative factual provenance only and does not create a production crawler dependency.

Frozen governance:

- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

Rights authority: https://www.un.org/en/about-us/terms-of-use

## 3. WOAH 94th General Session

**Primary authority:** WOAH Final Report of the 93rd General Session, June 2026  
https://www.woah.org/app/uploads/2026/06/93gs-2026-final-report-en.pdf

Under “Dates and venue of the 94th General Session”, the Assembly was informed that the **94th General Session will take place 24–28 May 2027 at the CNIT Forest in Paris, France**. WOAH regional material independently describes the next General Session as Monday 24 to Friday 28 May 2027.

The World Assembly adopts international animal-health standards, status decisions and organisational resolutions. That makes this a material global animal-health governance node with transmission through livestock trade, food security, veterinary standards, zoonotic risk and antimicrobial-resistance policy.

**Taxonomy:** natural primary category is `AGRICULTURE_FOOD`, not human `HEALTH_BIOSECURITY`.

**Primary category:** `AGRICULTURE_FOOD`.  
**Subcategory:** `animal_health_standards_governance`.  
**Event type:** `GOVERNANCE_ASSEMBLY_SESSION`.  
**Biosecurity analytical system:** `BIO-ANIMAL-ZOONOTIC-HEALTH`; `ONE_HEALTH` remains a cross-cutting relationship rather than a primary category.

**Rights/source governance:** WOAH-published terms reviewed in this pass restrict commercial reuse and automated extraction/data-mining on the reviewed WOAH surface. No more permissive licence specific to the General Session final report was established. Factual provenance is therefore manual and production automation remains held.

Frozen governance:

- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

Rights evidence reviewed: https://theanimalecho.woah.org/en/terms-and-conditions/

## Biosecurity-overlay migration

The current overlay correctly treats BWC and WOAH as noncanonical research nodes at v0.26. If Correction M admits their series, leaving those candidate nodes unchanged would become false and should fail closed.

The same transaction must therefore:

- advance the overlay v0.1 → v0.2;
- move BWC into canonical membership of `BIO-BIOLOGICAL-SECURITY-ARMS-CONTROL`;
- move WOAH into canonical membership of `BIO-ANIMAL-ZOONOTIC-HEALTH` and retain the `ONE_HEALTH` analytical relationship in the system map;
- remove `BIO-CAND-BWC` and `BIO-CAND-WOAH` from candidate nodes;
- leave IPPC/CPM and Africa CDC as noncanonical candidates;
- preserve primary canonical categories rather than creating a synthetic omnibus “biosecurity” category.

## Explicit holds

### IPPC CPM-21

Still held. Current first-party surfaces do not provide sufficiently consistent tentative-status semantics for safe canonical certainty assignment. Exact dates do not cure an unresolved status conflict.

### North Indian Ocean tropical cyclone seasons

Still held. The temporal ontology can now represent multi-phase month-bounded windows, but competent IMD material still conflicts on the first phase (`April–June` versus `April–May`). Ontology readiness cannot be used to choose between conflicting official definitions.

## Frozen transaction boundary

Correction M may change only:

- canonical registry: v0.26 / 669 → v0.27 / 673;
- source registry: v1.67 / 228 → v1.68 / 231;
- biosecurity overlay: v0.1 → v0.2;
- checkpoint/public tests required by those changes;
- durable Correction M plan/audit/test artefacts.

It must not change:

- change ledger v0.15;
- monitor expectations/routes;
- live-monitor implementation;
- automatic canonical commit policy;
- Google Calendar write policy.

The transaction must simulate and validate in memory before any branch write, fail closed on identity/version drift, and preserve all 669 pre-existing canonical occurrences byte-for-byte.
