# WORLD SIGNALS — DRC Bundibugyo evolving-state Live Intelligence AX research v0.1

**Research date:** 2026-09-06  
**Selected class:** evolving health emergency / repeated as-of state

## Primary official source sequence

### WHO Disease Outbreak News — 28 August 2026

Source: https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON616

WHO states that, as of **26 August 2026**, the Democratic Republic of the Congo had reported:

- **5,794 confirmed cases**;
- **2,786 confirmed deaths**;
- crude CFR **48.1%**;
- **60 affected health zones**;
- **six affected provinces**.

WHO describes continued geographic expansion and sustained transmission. This is a dated epidemiological state snapshot, not the time at which the outbreak began.

### WHO African Region Weekly External Situation Report 16 — data as of 30 August 2026

Source: https://afro.who.int/countries/uganda/publication/ebola-bundibugyo-virus-disease-outbreak-democratic-republic-congo-uganda-weekly-external-situation

WHO reports that, as of **30 August 2026**, the DRC cumulative state had become:

- **6,100 confirmed cases**;
- **2,950 confirmed deaths**;
- crude CFR **48.4%**;
- **60 affected health zones**;
- **six affected provinces**.

The report describes sustained transmission, high mortality and an increasingly heterogeneous geographic pattern, with persistent transmission in Ituri and intensification/expansion elsewhere.

## Why these two rows belong to one developing story

The two sources refer to the same DRC Bundibugyo virus disease outbreak and provide successive cumulative snapshots four days apart. The second source does not retract or correct the first source; it reports a later state of the same evolving outbreak.

Therefore:

- same story: yes;
- same observation: no;
- later state update: yes;
- revision/correction: no;
- silent replacement of the earlier observation: prohibited.

## Time semantics

The source sequence exposes four distinct time concepts:

1. **real-world outbreak/event time** — the outbreak began/developed before these reports;
2. **state-as-of time** — 26 August and 30 August 2026;
3. **source publication time** — 28 August and 30 August 2026 respectively;
4. **WORLD SIGNALS observation time** — when the evidence was reviewed/recorded on 6 September 2026.

The source gives the epidemiological state on civil dates, not clock times. AX must preserve `CIVIL_DATE` precision and must not manufacture midnight UTC.

## Broader current context — not separate production observations in AX

WHO's current DRC Ebola situation page shows the outbreak remained active in early September and lists additional governance/response developments, including:

- the second IHR Emergency Committee meeting in late August;
- updated WHO vaccine guidance published 1 September 2026;
- WHO Director-General briefings on 1–2 September 2026.

Source: https://www.who.int/emergencies/situations/ebola-outbreak---drc-2026

Africa CDC reported on 4 September 2026 that the DRC and partners launched a revised 180-day multisectoral response plan.

Source: https://africacdc.org/news-item/la-rdc-et-ses-partenaires-lancent-un-plan-revise-de-180-jours-pour-intensifier-la-reponse-a-lepidemie-debola-causee-par-le-virus-bundibugyo-et-sauver-des-milliers-de-vies/

These developments are relevant context but are deliberately **not** added as extra Live Intelligence observations in AX. Doing so would conflate the narrow evolving-state test with response-policy and governance observations.

## Attribution discipline

AX records only verified outbreak state. It does not infer:

- why transmission accelerated;
- which intervention changed case growth;
- whether vaccine policy caused any observed epidemiological change;
- whether insecurity, mobility or response constraints explain a particular increment;
- any market effect.

Those are analytical questions and remain outside Live Intelligence.

## Source hierarchy and provenance

Both production evidence rows are `PRIMARY_OFFICIAL` WHO records. They have `canonical_provenance_effect = NONE`. They do not create or modify Canonical events.

## Resulting contract requirement

The contract needs an explicit state-update relationship distinct from revision/correction semantics and a manual story grouping key. It does **not** yet need automatic clustering, a separate story registry, continuous ingestion or public projection.
