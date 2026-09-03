# WORLD SIGNALS — health / biosecurity institutional audit v0.1

**Audit date:** 2026-09-03  
**Canonical baseline:** v0.18 / 662 occurrences  
**Current category:** `HEALTH_BIOSECURITY` — 10 occurrences / 5 series / 1 institution  
**Canonical mutation authorised by this audit:** **NO**

## Question

Does the one-institution footprint of `HEALTH_BIOSECURITY` reveal a genuine blind spot, or does it partly arise because several distinct meanings of “biosecurity” belong in other canonical domains?

## Current canonical meaning

The existing schema already distinguishes:

- health-governance meetings;
- pandemic-treaty negotiations;
- observed outbreaks / operational health emergencies;
- WHO regional committee sessions;
- potential or TBC IHR emergency-committee meetings.

It also explicitly routes actual outbreaks, PHEIC declarations and operational health emergencies to Live Intelligence / Shock screening rather than treating them as recurring calendar series.

The present `HEALTH_BIOSECURITY` footprint is therefore primarily a **scheduled human-health governance / pandemic preparedness and response layer**, not a complete map of all biological risk governance.

That makes WHO institutional concentration important, but it must not be “fixed” by putting every institution using the word biosecurity into the health category.

## Cross-domain biosecurity map

Biosecurity spans at least four materially different governance systems:

1. **Human health / pandemic preparedness and response**
   - WHO and regional committees;
   - IHR / pandemic agreement institutions;
   - continental or national public-health institutions where a scheduled decision/governance node is material.

2. **Animal health / zoonotic and veterinary biosecurity**
   - World Organisation for Animal Health (WOAH);
   - animal-disease standards, notifications and trade-health rules;
   - One Health interfaces with WHO and FAO.

3. **Plant health / phytosanitary biosecurity**
   - International Plant Protection Convention (IPPC);
   - Commission on Phytosanitary Measures (CPM);
   - pest standards and phytosanitary trade rules.

4. **Dual-use biological security / arms control**
   - Biological Weapons Convention (BWC);
   - UN Office for Disarmament Affairs treaty machinery;
   - compliance, verification, science-and-technology and institutional-strengthening processes.

These systems should be linkable analytically without forcing them into one canonical category.

## Authoritative candidate review

### 1. IPPC Commission on Phytosanitary Measures (CPM) — strong missing biosecurity node, wrong category for a health-count repair

**Authority:** International Plant Protection Convention Secretariat / FAO  
**Institutional role:** CPM is the governing body of the IPPC and adopts international phytosanitary standards affecting plant protection, food security and safe trade.  
**2026 session:** CPM-20, 9–13 March 2026, completed.  
**Forward schedule:** IPPC's official 2027 calendar lists **CPM-21, 5–9 April 2027, FAO Headquarters, Rome**.  
**Sources:** https://ippc.int/en/year/calendar/?year=2027 ; https://ippc.int/en/commission/cpm/cpm-sessions/  
**Assessment:** `HIGH_VALUE_CANONICAL_CANDIDATE / NATURAL_CATEGORY_AGRICULTURE_FOOD / BIOSECURITY_CROSS_DOMAIN`

The IPPC calendar explicitly mixes planned and tentative meetings. CPM-21 is listed with exact dates and is not labelled tentative in the row, but any later population review should preserve the source's planning semantics rather than upgrading certainty reflexively.

Admitting CPM would materially improve the WORLD SIGNALS biosecurity system map, but putting it in `HEALTH_BIOSECURITY` merely to increase the institution count would be taxonomically wrong. Its natural primary domain is plant health / agriculture-food / trade biosecurity.

**Rights/automation:** the IPPC publications surface states FAO copyright, prohibits monetary-gain use and asks that the Secretariat be notified how material is used. This does not establish unrestricted production crawling of the calendar. Manual factual provenance and production automation remain separate gates.

### 2. WOAH World Assembly of Delegates — strong missing animal-health node; exact 2027 dates not yet established

**Authority:** World Organisation for Animal Health (WOAH)  
**Institutional role:** the World Assembly of Delegates adopts international animal-health standards and organisational resolutions.  
**2026 session:** 93rd General Session, **18–22 May 2026**, Paris, completed.  
**2027 evidence:** WOAH governance materials repeatedly confirm the **94th General Session in May 2027** and state that Specialist Commission elections and governance recommendations will go to that Assembly. Exact day-level dates were not established in this pass.  
**Sources:** https://www.woah.org/en/event/93rd-general-session-of-the-world-assembly-of-delegates/ ; https://www.woah.org/en/who-we-are/structure-and-governance/governance-review-committee-grc/  
**Assessment:** `HIGH_VALUE_CANONICAL_CANDIDATE / MONTH_PRECISION_ONLY / NATURAL_CATEGORY_ANIMAL_HEALTH_AGRICULTURE_OR_INSTITUTIONS / BIOSECURITY_CROSS_DOMAIN`

The month-level 2027 evidence is sufficient for an anticipatory monitor and potentially for a month-precision canonical occurrence if later architecture review determines that the annual Assembly belongs in Tier 1. It is not sufficient to manufacture exact dates.

**Rights/automation:** WOAH's general terms state all rights reserved and restrict reproduction/use without written permission except as provided by those terms. Some specific WOAH information products carry separate Creative Commons licences, but those licences must not be generalized to the website/calendar. Production monitoring therefore remains a rights/endpoint review question.

### 3. Biological Weapons Convention Working Group — exact future node, but security/arms-control category

**Authority:** United Nations Office for Disarmament Affairs / BWC meeting service  
**Future session:** **Tenth session of the Working Group on the Strengthening of the Biological Weapons Convention, 7–11 December 2026, Geneva**, with sessions 10:00–13:00 and 15:00–18:00.  
**Source:** https://meetings.unoda.org/bwc-/biological-weapons-convention-working-group-on-the-strengthening-of-the-convention-tenth-session-2026  
**Assessment:** `HIGH_VALUE_CANONICAL_CANDIDATE / NATURAL_CATEGORY_GEOPOLITICS_SECURITY_OR_INSTITUTIONS / BIOSECURITY_CROSS_DOMAIN`

This is clearly relevant to biological security, emerging technology risk, compliance/verification and international institutions. But it is a biological-weapons arms-control process, not a human public-health governance meeting. It should not be imported into `HEALTH_BIOSECURITY` merely to diversify that category.

UNODA materials also point to the **Tenth BWC Review Conference in December 2027**, but an exact authoritative date range was not established in this pass; retain only the precision actually supported.

**Rights/automation:** UN/UNODA terms permit personal non-commercial copying/download under conditions but retain broad copyright and redistribution restrictions. No unrestricted production-crawler permission is inferred.

### 4. Africa CDC / CPHIA 2026 — important continental health-security voice, but current source conflict and event-class question

**Authority:** Africa Centres for Disease Control and Prevention / African Union  
**Institutional role:** Africa CDC is a core continental public-health institution and would materially reduce a WHO-only analytical view of African health security.  
**Event examined:** 5th International Conference on Public Health in Africa (CPHIA 2026), Addis Ababa.  
**Assessment:** `IMPORTANT_SOURCE_FAMILY / CPHIA_CANONICAL_HOLD_SOURCE_CONFLICT_AND_EVENT_CLASS`

Current official surfaces disagree on the dates:

- the current Africa CDC event page and one launch/news item state **23–27 November 2026**;
- another Africa CDC launch/media-advisory page states **1–5 November 2026**;
- an African Union Executive Council decision and a February Africa CDC statement state **8–12 November 2026**.

Because multiple competent official surfaces disagree — including same-period Africa CDC material — this pass does **not** infer a reschedule sequence from publication order alone. It records a source-surface conflict requiring authoritative resolution.

More importantly, CPHIA is a major conference and agenda-setting forum, not obviously the formal deliberative governing body of Africa CDC. WORLD SIGNALS should not add it simply because it supplies a non-WHO institution. A later review should test whether a Governing Board, AU Executive Council/Assembly health-accountability milestone or another formal decision node is the better canonical object.

The Africa CDC 2025 annual report describes its Governing Board as the central deliberative body, but this pass did not establish an authoritative future meeting calendar for that board.

**Rights/automation:** African Union general terms limit ordinary site content to personal/non-commercial copying and impose broader reproduction restrictions. No production crawling permission is inferred for Africa CDC/AU pages.

## What does not belong in the scheduled canonical health layer

The following remain primarily Source/Change Monitor or Live Intelligence objects unless a separately scheduled decision point exists:

- outbreaks and epidemic alerts;
- PHEIC declarations and emergency terminations;
- disease surveillance observations;
- emergency deployments;
- WOAH disease notifications / WAHIS outbreak reports;
- plant-pest outbreak alerts;
- annual or ad-hoc threat assessments without a confirmed release date.

A recurring emergency is not a recurring calendar event.

## Taxonomy finding

The one-institution health-category diagnostic is **partly a genuine concentration finding and partly a category-boundary artefact**.

It is genuine because WORLD SIGNALS currently lacks a scheduled non-WHO human-health institutional series with equally strong Tier-1 justification.

It is an artefact because broader biological risk governance lives across several primary categories. Moving IPPC, WOAH or BWC into `HEALTH_BIOSECURITY` would improve the metric while damaging ontology.

### Recommended cross-domain overlay

Before using category counts as a measure of “biosecurity coverage”, add a derived analytical classification such as `biosecurity_scope` with non-exclusive values:

- `HUMAN_HEALTH_PPPR`
- `ANIMAL_HEALTH_ZOONOTIC`
- `PLANT_PHYTOSANITARY`
- `DUAL_USE_BIOLOGICAL_SECURITY`
- `ONE_HEALTH_CROSS_SECTOR`

This should be an analytical/coverage overlay or cross-domain metadata layer, not a replacement primary event category. One event may have one primary canonical category while appearing in multiple analytical systems.

## Decision

**No canonical population in this audit.**

Priority actions:

1. treat the WHO-only count as a prompt for continued human-health source research, not as a quota;
2. build a cross-domain biosecurity coverage map before judging system-wide institutional diversity;
3. retain **CPM-21 (5–9 Apr 2027)** as a high-value plant-biosecurity candidate in its natural domain;
4. retain **WOAH 94th General Session (May 2027, month precision)** as a high-value animal-health candidate pending exact-date/series review;
5. retain **BWC Working Group Tenth Session (7–11 Dec 2026)** as a high-value biological-security candidate in the security/institutions domain;
6. keep **CPHIA 2026** on canonical hold until the official date conflict and conference-vs-governance object-class question are resolved;
7. continue searching for an authoritative scheduled Africa CDC Governing Board or comparable formal continental human-health decision node rather than substituting a large conference;
8. never use outbreak/live-emergency feeds to inflate scheduled-calendar institutional breadth.

This audit therefore rejects the simplest interpretation — “WHO-only means add three non-WHO biosecurity meetings to the health category” — as methodologically unsound.
