# WORLD SIGNALS — Priority-region historical anchors R audit v0.1

**Research date:** 2026-09-06  
**Base main:** `a8bfb87bb7e889381ba67ab83c5f32218e6c2bd2`  
**Base canonical:** v0.28 / 674 occurrences  
**Base source registry:** v1.70 / 233 sources  
**Base change ledger:** v0.15 / 44 reviewed changes  
**Base biosecurity overlay:** v0.3 @ canonical v0.28 / 674

## Why this tranche exists

Analysis diversity stress-test Q found that the canonical registry contained only five `COMPLETED` occurrences eligible for reviewed post-event analysis. Africa, South Asia, Southeast Asia and Latin America each had zero completed canonical anchors. Q correctly blocked broad analytical population rather than inventing historical events or treating elapsed dates as completion.

R repairs that **upstream canonical historical-anchor gap**. It does not add Analysis reviews.

The scope is deliberately one completed historical occurrence per priority region, chosen from already-canonical series. This avoids inventing new taxonomy merely to satisfy the readiness audit and avoids a four-central-bank monoculture by using two statistical-release families and two monetary-policy families.

## Governing method

The Charter requires lifecycle history and provenance to remain auditable. R therefore separates:

1. **schedule/timing provenance** — the already-governed source that defines the recurring series and scheduled occurrence timing; and
2. **completion/outcome provenance** — a competent first-party post-event publication that proves the occurrence actually happened.

A scheduled date is not treated as proof of completion. A past date is not treated as proof of completion. Each R anchor is admitted as `COMPLETED` only because an authoritative post-event source positively verifies the occurrence.

The existing ABS GDP and RBNZ completed records already demonstrate this separation: their stable canonical source/series identity remains intact while a distinct reviewed completion assertion is recorded in lifecycle/change history.

## Candidate selection

### South Asia — India GDP, Q1 FY2026-27

Existing canonical series: `WSER-MAC-IN-GDP`  
Existing schedule source: `WSSRC-MAC-017` — MoSPI Advance Release Calendar 2026-27  
Proposed occurrence: `WSO-HIST-R-IN-GDP-2026Q1`

First-party evidence:

- MoSPI official site lists **“Press Note On Quarterly estimates of Gross Domestic Product for the first quarter (April-June) of 2026-27”** with publication date **31 August 2026**:  
  `https://www.mospi.gov.in/node/31376`
- MoSPI's current site also states: **“MOSPI is releasing Q1 Estimates of GDP for FY 2026-27 on 31st August, 2026 at 4:00 PM.”**
- MoSPI Advance Release Calendar 2026-27 provides the scheduled release date:  
  `https://www.mospi.gov.in/uploads/documents/releaseCalender/1779709510470-ADVANCE%20RELEASE%20CALENDAR%202026-27%20Updated%2025.05.2026.pdf`

R therefore admits 31 August 2026 at 16:00 Asia/Kolkata / 10:30 UTC. The 16:00 time is **occurrence-specific first-party evidence** and is not converted into a series-wide publication-time rule.

A new outcome-source record is warranted because `WSSRC-MAC-017` is specifically the advance release calendar. Proposed outcome source: `WSSRC-MAC-028`.

### Southeast Asia — Bank Indonesia, August 2026 Board of Governors Meeting

Existing canonical series: `WSER-REG-ID-BI`  
Existing schedule source: `WSSRC-REG-004` — 2026 monthly Board of Governors schedule  
Proposed occurrence: `WSO-HIST-R-ID-BI-202608`

First-party outcome evidence:

Bank Indonesia press release, **19 August 2026**:  
`https://www.bi.go.id/en/publikasi/ruang-media/news-release/Pages/sp_2816226.aspx`

The release states that the **18–19 August 2026** Board of Governors Meeting decided to hold BI-Rate at **5.75%**, with Deposit Facility at 4.75% and Lending Facility at 6.50%.

The canonical occurrence remains the two-day decision process. R does **not** create a duplicate same-day “decision announcement” occurrence and does not use the press-page clock timestamp as the canonical event time.

A new outcome-source record is warranted because `WSSRC-REG-004` is the schedule surface and remains under a rights/automation hold. Proposed outcome source: `WSSRC-REG-012`, also manual-only under the same rights discipline. Official status and public accessibility do not create production-crawling permission.

### Africa — Central Bank of Egypt MPC, 20 August 2026

Existing canonical series: `WSER-REGJ-EG-CBE-MPC`  
Existing source: `WSSRC-REGJ-005`  
Proposed occurrence: `WSO-HIST-R-EG-CBE-20260820`

First-party outcome evidence:

Central Bank of Egypt, **“MPC Press Release 20 August 2026”**:  
`https://www.cbe.org.eg/en/news-publications/news/2026/08/20/15/17/mpc-press-release-20-august-2026`

The CBE states that the MPC kept the overnight deposit rate at **19.00%**, overnight lending rate at **20.00%**, main-operation rate at **19.50%**, and discount rate at **19.50%**.

No separate outcome-source record is required here. `WSSRC-REGJ-005` already explicitly governs the 2026 MPC schedule **and links to completed decision releases**. The source provides a date but no authoritative decision clock time, so the historical occurrence remains a civil date with no synthetic UTC timestamp.

### Latin America — Argentina CPI, July 2026

Existing canonical series: `WSER-REG2-AR-CPI`  
Existing schedule source: `WSSRC-REG2-006` — INDEC second-half 2026 dissemination calendar  
Proposed occurrence: `WSO-HIST-R-AR-CPI-202607`

First-party outcome evidence:

INDEC official CPI page:  
`https://www.indec.gob.ar/Nivel4/Tema/3/5/31`

The page records **13/08/2026 — Índice de precios al consumidor** and states that the national CPI for **July 2026** rose **2.1% month-on-month**.

The second-half 2026 dissemination calendar independently establishes the scheduled publication date:  
`https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_2sem2026.pdf`

No clock time is inferred. A new outcome-source record is warranted because `WSSRC-REG2-006` is the dissemination-calendar surface. Proposed outcome source: `WSSRC-REG2-008`.

## Source-role design

R retains the existing schedule source as each historical occurrence's canonical `source_id`, preserving the same recurring series/timing authority used by future occurrences.

Where the post-event publication is a materially different endpoint, R adds a narrowly scoped supporting completion source with `canonical_dependency_count = 0` and links it as completion/outcome provenance. It does **not** replace the series schedule source.

New source records:

- `WSSRC-MAC-028` — MoSPI GDP press-note publication / completed-release verification;
- `WSSRC-REG-012` — Bank Indonesia monetary-policy decision press releases / completed-meeting verification;
- `WSSRC-REG2-008` — INDEC CPI technical reports / completed-release verification.

CBE uses existing `WSSRC-REGJ-005` because that governed source already covers completed decision releases.

The four existing schedule-source canonical dependency counts must each increase by one because each gains one new primary canonical occurrence:

- `WSSRC-MAC-017`: 17 → 18;
- `WSSRC-REG-004`: 4 → 5;
- `WSSRC-REGJ-005`: 3 → 4;
- `WSSRC-REG2-006`: 4 → 5.

## Lifecycle and assertion design

Each anchor receives two distinct stable assertion identities:

- a schedule assertion tying the occurrence timing to the existing governed schedule source;
- a completion assertion tying `COMPLETED` status to the first-party outcome publication.

The canonical occurrence keeps the schedule source as `source_id` and `primary_source_assertion_id`. The completion assertion is recorded in status history and the change ledger, and becomes `last_successful_assertion_id` because it is the latest authoritative verification for the admitted historical occurrence.

R does not manufacture an earlier WORLD SIGNALS `PLANNED` lifecycle state. These events were not previously canonical. Status history begins with the audited historical admission as `COMPLETED`, while the plan/audit separately records the schedule evidence that establishes timing.

Change-ledger entries use `HISTORICAL_OCCURRENCE_ADMISSION`, with `old_values.canonical_presence = false` and `new_values.canonical_presence = true`. This is an admission transaction, not a claim that an existing canonical occurrence changed from `PLANNED` to `COMPLETED` inside WORLD SIGNALS.

## Expected post-state

If simulation passes exactly:

- canonical v0.28 / 674 → **v0.29 / 678**;
- source registry v1.70 / 233 → **v1.71 / 236**;
- change ledger v0.15 / 44 → **v0.16 / 48**;
- biosecurity overlay v0.3 @ v0.28/674 → **v0.4 @ v0.29/678**, checkpoint-only;
- canonical schema remains **v0.52**;
- monitor expectations and operations policy remain unchanged;
- automatic canonical commit remains OFF;
- Google Calendar writes remain OFF.

Analysis population readiness should then move from:

`BLOCKED_NO_PRIORITY_REGION_COMPLETED_ANCHOR`

to:

`BLOCKED_PRIORITY_REGION_REVIEW_GAP`

because each priority region will have one completed canonical anchor but none of those four anchors will yet have a reviewed Analysis packet. This is the intended result. R unlocks honest analytical sampling; it does not declare analytical coverage complete.

## Explicit non-goals

R does not:

- add four Analysis reviews;
- create new event series;
- create duplicate decision-announcement occurrences for multi-day central-bank processes;
- infer completion from elapsed time;
- infer publication clock times for BI, CBE or INDEC;
- treat public web access as automated-retrieval permission;
- alter monitor expectations;
- alter Calendar write gates;
- alter biosecurity memberships;
- claim the four anchors make WORLD SIGNALS geographically complete.
