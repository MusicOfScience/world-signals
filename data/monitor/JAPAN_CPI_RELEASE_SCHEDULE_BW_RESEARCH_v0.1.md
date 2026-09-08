# WORLD SIGNALS — BW Japan CPI release-schedule research v0.1

Reference date: 2026-09-09  
Exact post-BV base: `b277939bc6c540d0986f298a832c7d63a29a2d19`

## Decision

BW selects the existing Statistics Bureau of Japan CPI schedule source `WSSRC-MAC-014` for a bounded, review-only **civil-date drift monitor** over seven already-modelled national CPI occurrences (`WSO-MAC-A-0050` through `0056`).

This is not a coverage-quota choice. The post-BV pressure audit still identifies South Asia as the deepest regional monitoring gap, but the leading South Asian candidates remain held for endpoint, parser or rights reasons. BW therefore does not override governance controls merely to improve regional counts. Japan CPI is selected because source rights, machine access, source identity and event semantics all support a narrow production route now.

## Authoritative source stack

### 1. National CPI release schedule — civil dates

Statistics Bureau of Japan, **Schedule of Release**  
Registered WORLD SIGNALS endpoint: `https://www.stat.go.jp/english/data/cpi/1582.htm`

The page states `Last Update : 23 January 2026` and publishes separate Japan and Ku-area of Tokyo columns. The national Japan rows relevant to the frozen BW scope are:

| CPI reference period | Visible Japan release date | Canonical occurrence |
|---|---|---|
| August 2026 | September 18, 2026 | `WSO-MAC-A-0050` |
| September 2026 | October 23, 2026 | `WSO-MAC-A-0051` |
| October 2026 | November 20, 2026 | `WSO-MAC-A-0052` |
| November 2026 | December 18, 2026 | `WSO-MAC-A-0053` |
| December 2026 | January 22, 2027 | `WSO-MAC-A-0054` |
| January 2027 | February 19, 2027 | `WSO-MAC-A-0055` |
| February 2027 | March 19, 2027 | `WSO-MAC-A-0056` |

The table also contains Tokyo preliminary CPI columns. Those are structurally visible to the parser but are **outside BW's Canonical scope** and do not trigger automatic follow-up or new event creation.

### 2. CPI publication rule — clock provenance

Statistics Bureau of Japan, **Q&A about the Consumer Price Index (Answers)**  
`https://www.stat.go.jp/english/data/cpi/1585.htm`

Question C-1 states that the preceding month's national CPI is released at **08:30 Japan time** on the Friday of the week including the 19th. This is the separate official provenance for the existing Canonical 08:30 JST clock.

Architectural consequence: the release-schedule monitor may compare the **civil date only**. It has no authority to validate, infer, upgrade or mutate `08:30`, `start_utc`, `time_precision`, `time_basis` or `timing_type`. Those fields remain governed by the separate official publication rule and existing Canonical provenance.

### 3. Content reuse terms

Statistics Bureau of Japan, **Information for use of this Website**  
`https://www.stat.go.jp/english/info/riyou.html`

The Statistics Bureau states that its website content is available under terms based on Public Data License 1.0; content may be used, copied, transmitted, translated or modified subject to conditions, including source citation and edited-content disclosure, and commercial use is permitted. It separately notes that numerical data and simple tables are not subject to copyright.

WORLD SIGNALS does **not** treat these content-use terms as machine-access permission. Machine access was reviewed separately through the live endpoint/robots diagnostics below.

## Machine-access and endpoint evidence

### Post-BV pressure audit

Run `34240072579`, job `102107667084` — SUCCESS, repository-read-only.

The audit confirmed that South Asia remained the largest route-coverage gap, but its high-value candidates retained genuine holds. Japan macro release schedules ranked among the strongest endpoint-review candidates after those controls were respected.

### Hardened Statistics Bureau endpoint diagnostic

Run `34240941533`, job `102110625804` — SUCCESS, repository-read-only.

Contract exercised:

- one request to `https://www.stat.go.jp/robots.txt`;
- one request to the official CPI schedule surface;
- total request budget: 2;
- zero linked-page, Tokyo-CPI, e-Stat/API, data-release, PDF, news or search follow-ups.

Observed result:

- `robots.txt`: HTTP 200, valid robots syntax, schedule path allowed;
- CPI schedule: HTTP 200 HTML;
- seven configured national-CPI survey/release pairs resolved exactly once;
- zero repository mutation;
- no clock, lifecycle, certainty or direct-write authority.

An earlier diagnostic failed safely because it assumed the August row would repeat the year in its first table cell. Raw evidence showed the live table labels that row simply `August`. The parser was then hardened to actual table-cell structure and explicit/carry-forward year anchors rather than loosening the match with a broad regex.

### Exact registered-endpoint check

Run `34241227432`, job `102111604587` — SUCCESS, repository-read-only.

The registry already identifies `https://www.stat.go.jp/english/data/cpi/1582.htm`. The Statistics Bureau also serves an `.html` alias, but BW does not migrate provenance merely because an alias works. The exact registered `.htm` endpoint returned HTTP 200 directly, was allowed by the live robots policy, and yielded all seven unique national-CPI pairs with the same two-request/no-follow-up contract.

### Source/Canonical contract inspection

Run `34241042301`, job `102110970929` — SUCCESS, repository-read-only.

The inspection confirmed:

- `WSSRC-MAC-014` is the sole existing CPI schedule source identity;
- exactly seven Canonical dependencies exist;
- no monitor route currently uses this source;
- the source is already cleared for curated factual Canonical provenance under Government of Japan open-use terms;
- its automation state was still `ENDPOINT_REVIEW_REQUIRED` / `PENDING_ENDPOINT_OPERATIONAL_REVIEW` before BW;
- the seven Canonical rows retain minute precision and explicit 08:30 JST timestamps, with notes recording that the date comes from the schedule while the clock comes from the separate publication rule.

## Parser contract

The permanent adapter must parse the **Japan** pair of columns from table rows, not free text.

For national survey-period identity:

1. a first-column value `Month, YYYY` establishes a survey-year anchor;
2. subsequent bare month names inherit that survey year until a new explicit year anchor appears;
3. the second column is the national release-date label;
4. an explicit release year is used when present;
5. otherwise the release year is derived from the survey year and calendar order: a release month earlier than the survey month crosses into the next year; otherwise it remains in the survey year;
6. duplicate national survey-period identities fail closed;
7. malformed or ambiguous date labels fail closed.

The parser does not read the Tokyo columns as national evidence and does not synthesize a time of day.

## Runtime comparison contract

Configured scope is exactly `WSO-MAC-A-0050` through `0056`.

- Exact observed civil-date match → observation only.
- Different observed civil date for the same configured reference period → review candidate for the same stable occurrence ID.
- Missing configured reference-period row → review candidate only for a non-completed occurrence, plus an absence observation.
- Missing row is **not** cancellation, completion, delay or certainty evidence.
- A completed occurrence receives corroboration observation only.
- Additional historical or future national CPI rows outside configured scope are observations, not automatic Canonical additions.
- Duplicate configured identities or structural ambiguity fail closed.
- No automatic Canonical commit.
- No Google Calendar write.
- No automatic Live Intelligence or Analysis promotion.
- No clock, lifecycle or certainty mutation.

## Source identity and governance update

BW reuses `WSSRC-MAC-014`. Creating a second machine source would falsely split provenance because Canonical date authority and monitoring both inspect the same first-party schedule.

The source count therefore remains 252. Only automation/readiness metadata may advance. Rights, licence, canonical provenance, institution, jurisdiction, source timezone, authoritative URL, dependency count and the separate clock-rule note remain unchanged.

The proposed production parser version is `jp-stat-cpi-0.2`, reflecting the hardened table-cell/year-anchor contract tested against the live page.

## Historical P1-F checkpoint

P1-F remains historical truth: on its 2026-09-04 governance snapshot, `WSSRC-MAC-014` was correctly classified as `ENDPOINT_REVIEW_REQUIRED` with `AUTOMATED_PILOT` verification.

If the current P1-F regression test blocks the later BW operational promotion, it may be made descendant-safe **only** for `WSSRC-MAC-014`, and only when the exact `JAPAN_CPI_RELEASE_SCHEDULE` route exists with BW's bounded/no-write gates. The P1-F plan file and every other P1-F source classification remain frozen.

## Expected governed post-state

- Canonical Registry: v0.41 / 689 — unchanged.
- Sources: v1.95 / 252 → v1.96 / 252.
- Monitor expectations: v0.20 / 18 → v0.21 / 19.
- Change Ledger: unchanged.
- Biosecurity: unchanged.
- Live Intelligence: unchanged.
- Analysis: unchanged.
- Automatic Canonical commit: OFF.
- Google Calendar writes: OFF.
