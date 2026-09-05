# WORLD SIGNALS — Cross-domain historical anchors U research v0.1

**Base main:** `16f4d441c18a3dee9da5fcdf432606de4da8e310`  
**Reference date:** 2026-09-06  
**Canonical pre-state:** v0.29 / 678  
**Analysis pre-state:** reviews v0.4 / 8; evidence v0.4 / 21; 9 completed canonical anchors

## Purpose

Analysis T deliberately left the Bank of Canada 2 September 2026 decision unreviewed. After T, a direct readiness probe established that the Analysis population gate is not hiding a larger market-data-eligible population: it counts every canonical occurrence whose lifecycle is `COMPLETED`. There are genuinely only nine completed canonical anchors.

The next useful pressure therefore belongs upstream. U adds a small number of authoritative historical occurrences to **existing canonical series**, without changing Analysis, inventing a new taxonomy, or treating backlog closure as an objective.

The selected anchors exercise three materially under-tested domains:

1. biological-security / arms-control treaty governance;
2. animal-health standards governance with trade and food-system transmission;
3. a national fiscal process expressed in a source-native civil calendar with no authoritative Gregorian conversion.

Existing-series reuse is a risk-control device, not a selection principle by itself. The research frontier still includes elections/governance and multilateral trade cases that require dedicated series/process modelling rather than being squeezed into U for convenience.

## Anchor 1 — BWC Working Group, eighth session

**Proposed occurrence:** `WSO-BWC-WG-2026-S08`  
**Existing series:** `WSER-INT-BWC-WG-STRENGTHENING`  
**Natural category:** `INTERNATIONAL_INSTITUTIONS` / biological-security arms control

### Official evidence

UNODA official eighth-session page:

https://meetings.unoda.org/bwc-/biological-weapons-convention-working-group-on-the-strengthening-of-the-convention-eighth-session-2026

It gives **9–13 February 2026**, Geneva, Tempus Building, Palais des Nations, and split programme sessions 10:00–13:00 and 15:00–18:00.

UNODA official 2026 BWC past-meetings archive:

https://meetings.unoda.org/meetings/past?f%5B0%5D=meeting_content_organ%3ABiological+Weapons+Convention&f%5B1%5D=meeting_content_organ_type%3ATreaties+and+Other+Instruments&f%5B2%5D=meeting_content_year%3A2026

The archive classifies the eighth session as a **Past Meeting** and gives the same 9–13 February date range. This supplies completion evidence; elapsed time does not.

Official eighth-session documents:

https://meetings.unoda.org/meeting/79376/documents

The document surface contains revised draft final-report and procedural-report documents dated through 13 February 2026. These support meeting completion/documentary outcome context but are not converted into a claim that every substantive negotiating question was resolved.

### Source-governance decision

Do **not** reuse `WSSRC-INT-032` as the occurrence source. That source is explicitly scoped to the tenth-session page and its evidence role says so. U adds `WSSRC-INT-034`, an official UNODA historical BWC meeting-archive source, under the same conservative UN web-rights classification and manual-only monitoring posture.

### Timing decision

The occurrence remains a five-day `MULTI_DAY_LOCAL` object at DAY_RANGE precision. Split daily programme hours are not promoted into a continuous event timestamp. No synthetic UTC boundary is created for an all-day/day-range governance object.

## Anchor 2 — WOAH 93rd General Session

**Proposed occurrence:** `WSO-WOAH-GS-093`  
**Existing series:** `WSER-AGF-WOAH-GENERAL-SESSION`  
**Natural category:** `AGRICULTURE_FOOD` / animal-health standards governance

### Official evidence

WOAH official event page:

https://www.woah.org/en/event/93rd-general-session-of-the-world-assembly-of-delegates/

The page states that the 93rd General Session **took place 18–22 May 2026 in Paris**. It also records the institutional functions of the session, including adoption of international standards and administrative/technical resolutions.

WOAH 93rd General Session final report:

https://www.woah.org/app/uploads/2026/06/93gs-2026-final-report-en.pdf

The existing source `WSSRC-INT-033` already points to this final report because that report also established the 94th General Session dates. It is therefore competent evidence for the historical 93rd occurrence as well; no new WOAH source object is needed.

### Taxonomy decision

WOAH remains `AGRICULTURE_FOOD`, not `HEALTH_BIOSECURITY`. Its One Health, zoonotic-risk and food-security relationships remain analytical/cross-domain connections. U does not improve a health-category metric by damaging the primary ontology.

### Timing decision

Preserve the 18–22 May civil-date range in `Europe/Paris`; do not fabricate a continuous clock-time span or UTC start/end. The event page's displayed daily hours are not necessary to represent the General Session as a multi-day governance occurrence.

## Anchor 3 — Nepal Federal Budget 2083/84 presentation

**Proposed occurrence:** `WSO-FIS-NP-BUDGET-2083`  
**Existing series:** `WSER-FIS-NP-FEDERAL-BUDGET`  
**Natural category:** `FISCAL_SOVEREIGN_FINANCE` / national budget

### Existing legal authority

`WSSRC-FIS-026` — Nepal Law Commission / Constitution Article 119(3) — is the canonical recurring-rule authority. It establishes presentation on the fifteenth day of Jestha each year.

### Official completion/publication evidence

Nepal Ministry of Finance budget archive:

https://mof.gov.np/category/budget-speech/

Specific FY2083/84 budget statement:

https://mof.gov.np/content/1741/budget-statement-for-the-financial-year-2083-84/

The Ministry records the FY2083/84 budget statement on **15 Jestha 2083**. The archive also exposes a website publication-time field; U does **not** equate that CMS timestamp with the constitutional presentation time.

### Calendar decision

This is deliberately the strongest temporal-contract stress specimen in U.

The historical occurrence is `COMPLETED` because competent first-party evidence establishes the budget statement on 15 Jestha 2083. It preserves:

- `native_calendar_system = BIKRAM_SAMBAT_NEPAL`;
- `native_calendar_year = 2083`;
- `native_calendar_month = JESTHA`;
- `native_calendar_day = 15`;
- `source_native_date_label = 15 Jestha 2083`;
- `gregorian_resolution_status = UNRESOLVED_AUTHORITATIVE_CONVERSION`.

`start_local`, `end_local`, `start_utc` and `end_utc` remain null. U does not use a third-party calendar converter merely because a Gregorian event window would be convenient for later market analysis.

`WSSRC-FIS-027` remains a supporting publication/completion source; it is not promoted into legal-date authority and its canonical dependency count remains zero under the repository's existing source-dependency convention.

## Deliberate non-selections

### Bank of Canada, 2 September 2026

Still eligible and still held for Analysis. Its evidence quality is not the problem; marginal analytical-contract value is.

### Colombia 2026 presidential election

High-value future tranche candidate. Official electoral evidence is available, but WORLD SIGNALS models an election as a stable process with distinct polling, runoff, declaration/certification and assumption milestones. Adding Colombia properly requires a dedicated election-process admission rather than a one-row historical shortcut.

### WTO MC14, Yaoundé

High-value trade/institutional candidate. The completed ministerial produced decisions while leaving material work unresolved and sent issues back to Geneva. It deserves a dedicated WTO ministerial series/interaction treatment rather than opportunistic insertion into an unrelated existing series.

### World Health Assembly 79

Analytically rich because the Assembly completed while PABS-annex negotiations continued. However the current scheduled human-health governance footprint is already WHO-heavy; BWC and WOAH add more marginal institutional/system diversity in this tranche.

## Proposed U post-state

If validation succeeds:

- canonical registry: v0.30 / **681**;
- source registry: v1.72 / **237**;
- change ledger: v0.17 / **51**;
- biosecurity overlay: v0.5 at canonical v0.30 / 681, semantic memberships unchanged;
- Analysis reviews: v0.4 / 8 — unchanged;
- Analysis evidence: v0.4 / 21 — unchanged;
- completed canonical anchors: **12**;
- reviewed completed anchors: **8**;
- broad Analysis readiness: `READY_FOR_CONTROLLED_EXPANSION`.

The unreviewed completed population would then contain four occurrences: the previously held Bank of Canada decision plus the three U anchors. A later Analysis tranche must select among them by analytical pressure, not by FIFO/backlog completion.

## Hard mutation boundary

U may mutate only:

- canonical registry: append three historical occurrences + version/checkpoint metadata;
- source registry: append one BWC archival source, increment the primary dependency counts of `WSSRC-INT-033` and `WSSRC-FIS-026`, and advance registry version/reference date;
- change ledger: append three historical-admission changes + version/reference date;
- biosecurity overlay: version + canonical checkpoint only;
- U research/plan/audit/script/tests.

No canonical schema, monitor configuration, Analysis registry/schema, calendar write, live-intelligence object or automatic canonical commit is authorised.
