# WORLD SIGNALS — BU INDEC CPI calendar monitor research v0.1

Reference date: 2026-09-08  
Exact post-BT main: `17e6130267c9d7911d12ac6f685c90228fec9e1e`

## Pressure finding

The post-BT monitor-coverage audit (`34221221467` / `102044536376`) found no wholly unmonitored geographic region, but substantial concentration remains. Latin America has 11 Canonical series and only one configured monitor occurrence/series; Africa has 11 series and two monitored occurrences; South Asia has nine series and two; Southeast Asia has 11 series and two. Seven Canonical categories still have zero configured monitor scope. These are diagnostic prompts, not quotas.

The existing readiness candidate list is not a neutral priority queue: it over-represents sources already carrying particular governance/readiness labels and therefore under-represents several Global South institutional sources. BU does not select a source by candidate-list rank or by geographic quota.

## Why INDEC

INDEC's national CPI series (`WSER-REG2-AR-CPI`) already has four remaining 2026 planned Canonical occurrences sourced to the official second-half dissemination-calendar PDF (`WSSRC-REG2-006`):

- `WSO-REG-B-0008` — August 2026 CPI, planned release 2026-09-10;
- `WSO-REG-B-0009` — September 2026 CPI, planned release 2026-10-13;
- `WSO-REG-B-0010` — October 2026 CPI, planned release 2026-11-12;
- `WSO-REG-B-0011` — November 2026 CPI, planned release 2026-12-15.

A fifth same-series occurrence, `WSO-HIST-R-AR-CPI-202607`, is a completed historical analytical anchor and is not included in the BU production allow-list.

INDEC states that its advance dissemination calendar announces release dates 12 months ahead and supports user searches by day, month and report. Its dissemination policy states that official public statistical dissemination is objective, impartial and simultaneous and fixes 16:00 UTC−03:00 for statistics in the calendar. INDEC also issued a 2 January 2026 notice changing several previously announced 2026 release dates, including September CPI to 13 October, demonstrating that forward schedule changes are real rather than hypothetical.

Primary official references:

- calendar: `https://www.indec.gob.ar/indec/web/Calendario-Fecha-0`
- transparency/calendar description: `https://www.indec.gob.ar/indec/web/Institucional-Indec-Transparencia`
- FAQ: `https://www.indec.gob.ar/indec/web/Institucional-Indec-PreguntasFrecuentes`
- 2026 change notice: `https://www.indec.gob.ar/indec/web/Institucional-GacetillaCompleta-517`
- dissemination policy: `https://www.indec.gob.ar/ftp/cuadros/publicaciones/politica_difusion_indec.pdf`
- second-half 2026 PDF already used by Canonical: `https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_2sem2026.pdf`

## Machine-interface discovery

BU used read-only GitHub Actions diagnostics with exact post-BT ancestry and no repository writes.

1. `34221438614` / `102045235833`: INDEC `robots.txt` returned HTTP 200 with `User-agent: *` and an empty `Disallow:`. The public calendar returned HTTP 200 and referenced first-party calendar JavaScript. Robots compatibility is operational crawler-policy evidence, not blanket legal permission.
2. `34221529512` / `102045530088`: first-party scripts exposed `/Calendario/FiltrosCalendario/dia/`, `/mes/` and `/buscar/` route families.
3. `34221689211` / `102046057336`: `CalendarioFull.js` showed that the public UI itself uses jQuery `.load()` GET requests to `/Calendario/FiltrosCalendario/mes/{month}/{variant}` and analogous day/search routes.
4. `34221959307` / `102046924867`: one deterministic request to `/Calendario/FiltrosCalendario/mes/Septiembre-2026/0` returned HTTP 200 and the September release schedule, including national CPI for August 2026 on 10 September at `16:00hs`.
5. `34222409320` / `102048394411`: a deliberately literal raw-HTML title assertion failed because accented characters are HTML-entity encoded. This is retained as fail-closed parser evidence.
6. `34222469393` / `102048588503`: entity-normalised inspection passed. The first-party response contains both the visible CPI row (`16:00hs`) and an embedded Google Calendar template URL whose query metadata independently represents the exact CPI title, `20260910T160000/20260910T163000`, and `ctz=America/Argentina/Buenos_Aires`. BU does not request Google; the URL is parsed only as metadata embedded in INDEC's own response.

The search/autocomplete shortcut was not adopted. Its values are not supplied by the static JavaScript itself, so BU refuses to discover a one-request search contract by parameter experimentation. Four deterministic month endpoints are preferable to one opaque shortcut.

## Rights and automation separation

`WSSRC-REG2-006` already records INDEC's Creative Commons factual-content/reuse posture while retaining `ENDPOINT_REVIEW_REQUIRED` for automated calendar retrieval. BU does not reinterpret that old PDF source as broadly automation-cleared.

Instead BU separates the machine interface:

- `WSSRC-REG2-006` remains the Canonical forward-schedule authority based on the official dissemination-calendar source and is preserved unchanged;
- proposed `WSSRC-REG2-009` represents only the public interactive calendar month-route interface used by INDEC's own browser UI.

Narrow machine-access basis: public first-party UI invocation + explicit robots compatibility + bounded low-rate GET requests. This is not a general crawl permission and does not confer unrelated endpoint access.

Content/reuse basis remains separate: INDEC states that website material is generally Creative Commons unless specifically indicated, with attribution/modification conditions. WORLD SIGNALS stores and emits only minimal factual schedule metadata, not copied page content.

Operational classifications are internal governance judgements, not legal opinions.

## Temporal discipline

The interactive calendar provides materially richer precision than the current Canonical CPI rows: 16:00 in `America/Argentina/Buenos_Aires`, consistent with INDEC's published 16:00 UTC−03:00 dissemination policy.

BU **does not mutate Canonical timing**. Current occurrences remain date-only. A matching live row may generate a `CLOCK_ENRICHMENT_REVIEW_CANDIDATE`; only a later explicit reviewed Canonical transaction may add a clock and UTC timestamp.

Date drift, time drift, disappearance or ambiguous duplicate rows are review evidence only. Absence is never cancellation, delay, completion or certainty change. Elapsed time is never completion evidence. The post-event CPI technical-report source `WSSRC-REG2-008` is not automatically fetched and is not folded into this schedule monitor.

## Proposed BU boundary

- new monitor-only machine source: `WSSRC-REG2-009`;
- route: `INDEC_CPI_CALENDAR`;
- exact allow-list: four remaining 2026 planned CPI occurrences only;
- deterministic month routes: September, October, November, December 2026;
- maximum four calendar-fragment requests plus one robots check per monitor run;
- no search-route probing, no PDF follow-up, no CPI technical-report follow-up, no Google request;
- review-only schedule/clock evidence;
- no Canonical, lifecycle, certainty, Live Intelligence, Analysis or Google Calendar automatic write authority.
