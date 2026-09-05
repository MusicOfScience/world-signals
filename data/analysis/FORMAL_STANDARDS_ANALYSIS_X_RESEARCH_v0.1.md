# WORLD SIGNALS — Formal standards analysis X research v0.1

**Reference date:** 2026-09-06  
**Base main:** `1e0a4f51c3c1d860cc463f3abfbd8b3580bd36d5`

## Selection decision

X selects `WSO-WOAH-GS-093`, the 93rd General Session of the World Assembly of Delegates of the World Organisation for Animal Health (WOAH).

This is not backlog completion. Bank of Canada 2 September 2026 remains eligible and deliberately held.

WOAH GS93 is selected because it tests a different analytical failure mode from W. The session produced formal adopted outputs — standards, resolutions and strategic decisions — but those outputs do not all have the same legal, regulatory, trade or implementation consequence. X must preserve the distinction between **adoption** and **downstream effect**.

## Authoritative outcome evidence

### 1. General Session outcome surface

WOAH's official 93rd General Session page states that the Assembly met 18–22 May 2026 in Paris and reports the following main achievements:

- 35 resolutions adopted;
- 51 international standards adopted or revised;
- 3 new and 9 revised Terrestrial Code chapters;
- 17 revised Terrestrial Manual chapters;
- 18 revised Aquatic Code chapters;
- 4 revised Aquatic Manual chapters;
- 6 Members with newly recognised animal-health statuses;
- 3 Members with animal-disease control programmes endorsed.

Source:
- https://www.woah.org/en/event/93rd-general-session-of-the-world-assembly-of-delegates/

The same page links the final report and final resolutions and records adoption of the 8th Strategic Plan.

### 2. 8th Strategic Plan

WOAH states that Members adopted the 8th Strategic Plan on 20 May 2026 for the period 2027–2031. The Plan formally takes effect in 2027 and identifies three strategic orientations: strengthening global standards, empowering national animal-health systems, and elevating animal health as a global priority.

Source:
- https://www.woah.org/en/woah-8th-strategic-plan-adopted-for-2027-2031/

Analytical treatment:
- adoption is an observed institutional outcome;
- implementation from 2027 is prospective and must not be backfilled as an already-observed impact.

### 3. Updated Global Action Plan on AMR 2026–2036

Final Resolution No. 18 adopted the updated Global Action Plan on Antimicrobial Resistance 2026–2036. The final report records that Resolution No. 18 was adopted with no objection or abstention recorded.

Sources:
- https://www.woah.org/app/uploads/2026/06/sg93-final-resolutions-en.pdf
- https://www.woah.org/app/uploads/2026/06/93gs-2026-final-report-en.pdf

WOAH later summarised that adoption as a One Health milestone and noted subsequent WHO adoption two days later.

Source:
- https://www.woah.org/en/woah-members-adopt-the-updated-global-action-plan-on-antimicrobial-resistance/

Analytical treatment:
- WOAH adoption is an observed outcome;
- cross-institutional alignment is context, not proof of implementation success;
- X does not infer health, resistance or economic effects from adoption alone.

## Regulatory and trade differentiation

### 4. WOAH standards and the WTO SPS architecture

WOAH states that the WTO SPS Agreement encourages WTO Members to base sanitary measures on international standards and recognises WOAH as the reference organisation for animal-health and zoonosis standards. WOAH's Terrestrial Code is intended to support animal health, veterinary public health and safe international trade.

Sources:
- https://www.woah.org/en/what-we-do/standards/
- https://www.wto.org/english/thewto_e/coher_e/wto_oie_e.htm

WOAH also states that Members voting to adopt standards commit to translating them into national legislation, while implementation is monitored through the Observatory.

Source:
- https://www.woah.org/en/article/woah-standards-building-a-global-governance-of-animal-health/

### 5. Critical carve-out: animal-welfare standards

WOAH explicitly states that, unlike its animal-health and veterinary-public-health standards, animal-welfare standards are **not recognised in the WTO SPS Agreement**.

Source:
- https://www.woah.org/en/what-we-do/animal-health-and-welfare/animal-welfare/development-of-animal-welfare-standards/

Analytical treatment:
- X must not convert the headline count of 51 adopted/revised international standards into a claim that all 51 have identical WTO SPS status;
- regulatory/trade relevance must be disaggregated by subject matter;
- adoption creates a normative and operational pathway, not automatic domestic legal effect everywhere.

## Concrete cross-domain example: avian influenza

WOAH's 22 May 2026 article on avian influenza states that GS93 revised a trade standard and created a new biosecurity chapter in response to Member requests. The article describes the standards as designed for Members to implement and highlights live-bird markets as a vulnerable setting for disease spread.

Source:
- https://www.woah.org/en/article/how-woahs-new-and-revised-chapters-ensure-better-control-of-avian-influenza/

Analytical treatment:
- this is a concrete animal-health / biosecurity / trade interface;
- it supports `REGULATORY_OVERLAP`, not a claim that GS93 caused a subsequent trade or disease outcome.

## Expectation and surprise discipline

Pre-session working material placed major items — including the Strategic Plan and updated GAP-AMR — before the Assembly for consideration. However, X has not identified a defensible contemporaneous forecast for:

- the number of standards or resolutions that would be adopted;
- the voting outcome across the full package;
- the magnitude or timing of downstream Member implementation.

Accordingly, X uses `NOT_ESTABLISHED` for surprise. An agenda item or draft resolution is not silently converted into a probability forecast.

## Market-response discipline

No market response is promoted. `what_moved` is intentionally empty.

The institutional outputs may ultimately affect veterinary regulation, sanitary trade measures, disease-control practice, food systems, health security and investment. None of those potential channels justifies inventing an event-window market proxy for the General Session itself.

## Connection discipline

The appropriate connection is `REGULATORY_OVERLAP` / `NOT_A_CAUSAL_CLAIM`.

The strong, evidence-backed proposition is structural: a subset of WOAH standards adopted at GS93 sits inside the WTO SPS standard-setting architecture for animal health and zoonoses, while other adopted material — including animal-welfare standards — does not share that legal status. National implementation remains a separate downstream process.

## Second-order treatment

Use `PLAUSIBLE_WATCH_ITEM` for:

- implementation of the 8th Strategic Plan from 2027;
- Member uptake of relevant standards in national veterinary rules and practice;
- WTO SPS notifications or trade measures where relevant;
- future WOAH Observatory evidence on implementation;
- subsequent General Session governance and standards decisions.

No broad success/failure or economic-impact claim is established at X.

## Schema decision

No Analysis schema change is warranted.

Schema v0.3 already permits:
- `NOT_ESTABLISHED` surprise;
- an empty `what_moved` array;
- `REGULATORY_OVERLAP`;
- `NOT_A_CAUSAL_CLAIM`;
- `PLAUSIBLE_WATCH_ITEM`;
- multiple alternative explanations and explicit falsifiers.

The contract pressure is semantic, not structural: X proves the existing schema can distinguish formal adoption from differentiated downstream legal and implementation pathways.

## Expected post-state

- canonical registry: v0.30 / 681 — unchanged
- source registry: v1.72 / 237 — unchanged
- change ledger: v0.17 / 51 — unchanged
- biosecurity overlay: v0.5 @ canonical v0.30 / 681 — unchanged
- Analysis schema: v0.3 — unchanged
- Analysis reviews: v0.7 / 11
- Analysis evidence: v0.7 / 40
- eligible completed occurrences: 12
- reviewed completed occurrences: 11
- reviewed event-type diversity: 10
- remaining eligible unreviewed: Bank of Canada 2 September 2026
- broad state: `READY_FOR_CONTROLLED_EXPANSION`
