# WORLD SIGNALS — Source-native fiscal analysis V research v0.1

**Reference date:** 2026-09-06  
**Base:** post-U main `1bfa947d1fbd86e945349991778944094a78e5ed`

## Research question

Which unreviewed completed occurrence creates the strongest next pressure on the Analysis contract without turning controlled expansion into backlog completion?

The post-U frontier contains four eligible unreviewed occurrences: Bank of Canada 2 September, BWC Working Group session 8, WOAH General Session 93 and Nepal Federal Budget 2083/84. Nepal is selected because it combines an event type not yet reviewed with a canonical temporal model the current public Analysis projection does not faithfully expose.

## Architectural finding: canonical date is being lost at the Analysis projection boundary

The canonical Nepal occurrence is `COMPLETED` and `CONFIRMED`. Its temporal truth is not missing:

- `timing_type = SOURCE_NATIVE_CALENDAR_DATE`
- `source_native_date_label = 15 Jestha 2083`
- `native_calendar_system = BIKRAM_SAMBAT_NEPAL`
- `gregorian_resolution_status = UNRESOLVED_AUTHORITATIVE_CONVERSION`
- `start_local = null`
- `start_utc = null`

The existing Analysis validator correctly permits `canonical_release_utc = null` when canonical `start_utc` is null. The defect is downstream: `_canonical_context()` currently projects only `start_local`, `start_utc` and `source_timezone`, so the public Analysis surface cannot distinguish “authoritatively dated in a source-native calendar, Gregorian mapping unresolved” from “no canonical date known”.

V therefore evolves the Analysis contract before adding the Nepal review. This is an Analysis projection/schema change only. It does not mutate canonical timing or use analysis evidence to manufacture a Gregorian conversion.

## Outcome evidence

### Ministry of Finance, Government of Nepal

Source: `https://www.mof.gov.np/category/budget-speech/`

The Ministry's budget-speech archive lists the FY2083/84 Nepali budget statement on `15 Jestha 2083` and separately lists the later English budget speech. The website's CMS publication-time field is not treated as the constitutional presentation clock time. This evidence is useful in Analysis for the official publication surface and for reinforcing the canonical temporal boundary; it does not resolve the canonical Gregorian date.

### Public Service Broadcasting / Radio Nepal — 29 May 2026

Source: `https://radionepalonline.com/en/2026/05/29/430550.html`

Radio Nepal reported the announced FY2083/84 budget as NPR 2,124.34 billion, comprising:

- current expenditure: NPR 1,270.58 billion;
- capital expenditure: NPR 431.10 billion;
- financial management: NPR 422.64 billion;
- revenue estimate: about NPR 1,405 billion;
- foreign grants: NPR 61.74 billion;
- deficit: NPR 657.29 billion;
- foreign loans: NPR 247.28 billion;
- internal loans: NPR 410 billion.

This is analytical outcome evidence. The canonical occurrence remains governed by its separate legal/publication provenance.

## Expectation history: do not freeze the earliest ceiling

A simple post-event comparison against NPR 1.89 trillion would be misleading.

### Earlier planning envelope

Source: `https://radionepalonline.com/en/2026/05/29/430529.html`

On the morning of presentation, Radio Nepal reported that the National Planning Commission had set an NPR 1.89 trillion ceiling and that a senior Finance Ministry official expected a budget in roughly the NPR 1.89–2.00 trillion range.

An earlier 30 April Radio Nepal report also described NPR 1.89 trillion as the planning limit communicated to ministries.

### Later pre-event revision

Source: `https://kathmandupost.com/money/2026/05/29/wagle-set-to-unveil-large-deficit-budget-above-fiscal-ceiling`

Kathmandu Post reported before presentation that the Resource Estimation Committee's original NPR 1.89 trillion ceiling had been revised on Wednesday, at the Finance Minister's request, to around NPR 2.15 trillion. The same article described the expected spending plan as roughly NPR 2.1–2.2 trillion.

The final NPR 2.12434 trillion outlay is therefore:

- materially above the earlier NPR 1.89 trillion planning envelope;
- below the reported revised ceiling of about NPR 2.15 trillion; and
- within the latest reported NPR 2.1–2.2 trillion pre-event range.

**Analytical decision:** `NO_CLEAR_SURPRISE` for headline budget size. V preserves the benchmark sequence instead of selecting the stale early ceiling to create an artificial upside surprise.

## First market observation

### NEPSE — first trading day after the budget

Source: `https://myrepublica.nagariknetwork.com/news/nepse-welcomes-budget-202627-on-negative-note-index-plunges-2672-points-29-72.html`

Republica reported that on the first trading day after the budget, NEPSE fell 26.72 points and closed at 2,755.37. It also reports the market opened at 2,782.10.

V uses `CHANGE_AND_ENDPOINT` rather than reconstructing its own pre-event baseline:

- change: -26.72 index points;
- endpoint: 2,755.37;
- `before_value = null`;
- `independently_reconstructed = false`.

The reporting date and market-session chronology may be used for analytical evidence, but they do not resolve the canonical event's source-native Gregorian mapping.

## Capital-market policy context

Source: `https://kathmandupost.com/money/2026/05/31/capital-market-reforms-draw-mixed-response-as-investors-flag-tax-inequities`

Kathmandu Post documented mixed reactions to the capital-market package. It reported that treating securities capital-gains tax as final was welcomed, while higher CGT rates and the absence of a portfolio loss-offset mechanism attracted criticism. The article also described weak corporate performance and hesitant investor demand as pre-existing constraints.

**Analytical decision:** the first post-budget NEPSE fall is a market observation, not proof that the budget as a whole caused the move. The review uses `TEMPORAL_COINCIDENCE_ONLY` and `NOT_A_CAUSAL_CLAIM`; specific tax provisions, pre-existing corporate weakness and market structure remain alternatives/context.

## Observed implementation follow-through

### Financial Comptroller General Office — daily receipts and payments status

Source: `https://old.fcgo.gov.np/daily-budgetary-analysis`

The official FCGO daily status page reported, as of 2083-05-18 / 3 September 2026:

- total expenditure from Treasury: 5.79% of annual budget;
- recurrent expenditure: 5.69%;
- capital expenditure: 1.19%;
- financing: 10.78%.

The page explicitly states that the figures are unprocessed and subject to change after reconciliation, and that direct-payment expenditure is only partially included.

V treats this as an **observed second-order implementation signal**, not an evaluation of success or failure. No annual-execution conclusion is drawn from an early, unreconciled snapshot.

## Why the other eligible anchors remain held

### Bank of Canada 2 September

Valid completed decision, but the reviewed population already contains several monetary-policy decision/process specimens. Selecting it now would add less contract pressure and risks becoming backlog completion by convenience.

### BWC Working Group session 8

Strong future candidate for treaty-process analysis and explicit null-market response. It remains held because V first repairs a concrete temporal-projection defect exposed by Nepal.

### WOAH General Session 93

Strong future candidate for animal-health standards, trade and One Health transmission. It also remains valid for later controlled expansion.

## V design consequences

1. Analysis schema advances from v0.2 to v0.3 with an explicit temporal-context preservation policy.
2. Public canonical Analysis context carries source-native and unresolved-conversion fields without inference.
3. Browser rendering displays source-native canonical dates directly and states when authoritative Gregorian conversion is unresolved.
4. One Nepal post-event review and seven analytical evidence records are appended.
5. Review/evidence datasets advance to v0.5 and review checkpoint advances to canonical v0.30/681.
6. Canonical registry, source registry, change ledger, biosecurity overlay, monitor configuration and calendar outputs remain byte-identical to post-U main.
7. The remaining unreviewed completed frontier is BoC, BWC and WOAH; V does not claim analytical completeness.
