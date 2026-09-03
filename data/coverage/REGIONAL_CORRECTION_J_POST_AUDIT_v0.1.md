# WORLD SIGNALS — Regional Correction J post-audit v0.1

**Audit date:** 2026-09-03  
**Canonical migration commit:** `a30b66a93b2734afed0fbbc59183b17065e42844`  
**Post-migration canonical registry:** v0.18 / 662 occurrences  
**Post-migration source registry:** v1.49  
**Coverage-audit workflow run:** `33761038205`  
**Post-audit artifact digest:** `sha256:52af79696cee12e786ba1bcdaaa1727ad161165ba5253afc138cfe9a6d395706`

## Purpose

This record compares the coverage audit before and after Regional Correction J. It is a diagnostic decision record, not a quota target and not authority for further canonical population.

The correction added 13 manually reviewed remaining-2026 monetary-policy occurrences across six previously missing series: Reserve Bank of India, State Bank of Pakistan, Central Bank of Sri Lanka, Bangko Sentral ng Pilipinas, Bank Negara Malaysia and Central Bank of Egypt. Source-rights and automated-monitoring eligibility remained separate from canonical factual provenance.

## Global shape

| Measure | Before — v0.17 | After — v0.18 | Change |
|---|---:|---:|---:|
| Canonical occurrences | 649 | 662 | +13 |
| Unique series | 185 | 191 | +6 |
| Unique institutions | 110 | 116 | +6 |
| Unique canonical source IDs used | 141 | 147 | +6 |
| Occurrences per series | 3.51 | 3.47 | -0.04 |
| Monetary + macro occurrences | 424 | 437 | +13 |
| Monetary + macro occurrence share | 65.33% | 66.01% | +0.68 pp |

The fall in occurrences-per-series is mildly positive for breadth, but the increase in monetary+macro share is a warning: geographic correction improved while category concentration worsened slightly. This is not a reason to remove the new series; it is a reason for the next research tranche to focus on genuinely underrepresented non-monetary signal families.

## Regional effect

| Region | Occurrences | Unique series | Unique institutions | Unique sources | Diagnostic effect |
|---|---:|---:|---:|---:|---|
| South Asia — before | 18 | 4 | 2 | 2 | <10 series; <8 institutions |
| South Asia — after | 25 | 7 | 5 | 5 | Still <10 series and <8 institutions |
| Southeast Asia — before | 14 | 8 | 8 | 9 | <10 series |
| Southeast Asia — after | 17 | 10 | 10 | 11 | Exits <10-series diagnostic |
| Africa — before | 13 | 9 | 9 | 9 | <10 series |
| Africa — after | 16 | 10 | 10 | 10 | Exits <10-series diagnostic |

Interpretation:

- **South Asia:** genuine improvement, but still structurally thin. Further work should not automatically mean more central banks; the next candidates should be selected by missing signal family and systemic importance.
- **Southeast Asia:** the original series-breadth flag is resolved. No country-filling programme is justified.
- **Africa:** the original series-breadth flag is resolved. Further additions require a substantive signal gap, not continental balancing.

## Category effect

Regional Correction J changes only `MONETARY_FINANCIAL_POLICY`:

- occurrences: **233 → 246**;
- unique series: **27 → 33**;
- unique institutions: **14 → 20**;
- unique sources: **16 → 22**;
- occurrences per series: **8.63 → 7.45**.

The coverage audit's only `<5 unique series` category diagnostic remains:

- **PHYSICAL_CLIMATE_RISK:** 4 occurrences / 2 series / 2 institutions / 2 sources.

Two further concentration findings are analytically important even though they do not trip that threshold:

- **HEALTH_BIOSECURITY:** 10 occurrences / 5 series / **1 institution**. Series count disguises institutional concentration.
- **ENERGY_COMMODITIES:** 28 occurrences / 6 series / **3 institutions**. Occurrence density is much stronger than institutional breadth.

For comparison:

- **CLIMATE_ENVIRONMENT:** 10 occurrences / 10 series / 7 institutions — not currently a simple breadth problem.
- **AGRICULTURE_FOOD:** 20 occurrences / 8 series / 5 institutions — materially broader than energy-commodities or health-biosecurity.

## Decision

Regional Correction J is **closed as a successful bounded correction**. It materially reduced geographic blind spots without creating automatic monitoring privileges or Calendar writes.

The next coverage-research priority is therefore **not another general monetary-policy population tranche**. Research should proceed in this order:

1. **Physical climate risk** — determine whether the two-series footprint reflects ontology/source design or a true omission of high-value scheduled risk windows/assessment catalysts.
2. **Health / biosecurity** — test whether the five-series footprint is effectively WHO-only and identify other systemically important authoritative institutions or treaty/regulatory nodes without turning outbreaks into scheduled calendar events.
3. **Energy / commodities** — test institutional and geographic breadth, especially producer-policy, high-value information catalysts and non-OECD/Global South sources, while keeping physical disruptions in the Shock/Live Intelligence layer.
4. **South Asia cross-domain depth** — only after the category review, identify whether fiscal, trade, energy, institutional, climate or governance nodes materially improve the region beyond the now-expanded monetary/macro core.

## Safety / architecture state

Unchanged:

- automatic canonical commit: **CLOSED / prohibited**;
- Google Calendar writes: **OFF / prohibited**;
- coverage thresholds are prompts for qualitative review, not population quotas;
- machine-readability is not an importance score;
- public accessibility or reuse permission does not itself authorize production crawling;
- source-health state remains separate from event state;
- new sources from Regional Correction J were not silently promoted into the scheduled live-monitor cohort.
