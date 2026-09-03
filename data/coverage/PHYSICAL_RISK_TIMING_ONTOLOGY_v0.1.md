# WORLD SIGNALS — Physical-risk timing ontology implementation v0.1

**Reference date:** 2026-09-04  
**Canonical checkpoint:** v0.19 / 668 occurrences  
**Canonical schema:** v0.50  
**Schema migration commit:** `c1548af6ce4adc0c400fe850f6fde125179a41f8`  
**Canonical population authorised by this implementation record:** **NO**

## Why this tranche exists

The physical-risk coverage audit found that the strongest missing international tropical-cyclone sources do not all express seasonal timing as exact civil-day ranges.

In particular:

- Fiji Meteorological Service / RSMC Nadi uses regional **November–April** wording;
- IMD / RSMC New Delhi describes two North Indian Ocean cyclone seasons: **April–June and October–December**.

The prior canonical timing model could represent exact date ranges and expected day-bounded windows, but it had no safe source-native representation for these month-bounded patterns. Using `date_earliest` / `date_latest` would have required manufacturing first/last civil days that the regional source did not assert.

This tranche therefore extends temporal representation **before** any new physical-risk events are admitted.

## New timing types

### `MONTH_BOUNDED_SEASON_WINDOW`

Use when one authoritative seasonal-risk phase has named start/end months but no authoritative day boundary.

Required model:

`season_window_model = MONTH_BOUNDED_SINGLE_PHASE`

Example shape:

```json
{
  "timing_type": "MONTH_BOUNDED_SEASON_WINDOW",
  "season_window_model": "MONTH_BOUNDED_SINGLE_PHASE",
  "time_precision": "MONTH",
  "time_status": "NOT_APPLICABLE",
  "time_basis": "NOT_APPLICABLE",
  "start_local": null,
  "end_local": null,
  "start_utc": null,
  "end_utc": null,
  "date_earliest": null,
  "date_latest": null,
  "publication_datetime": null,
  "source_native_window_label": "November–April",
  "season_phases": [
    {
      "phase_id": "PHASE_1",
      "start_month": "2026-11",
      "end_month": "2027-04",
      "boundary_precision": "MONTH",
      "source_label": "November–April"
    }
  ]
}
```

### `MULTI_PHASE_SEASON_WINDOW`

Use when one stable seasonal-risk family has two or more authoritative non-contiguous month-bounded phases.

Required model:

`season_window_model = MONTH_BOUNDED_MULTI_PHASE`

Example shape:

```json
{
  "timing_type": "MULTI_PHASE_SEASON_WINDOW",
  "season_window_model": "MONTH_BOUNDED_MULTI_PHASE",
  "time_precision": "MONTH",
  "source_native_window_label": "April–June and October–December",
  "season_phases": [
    {
      "phase_id": "PHASE_1",
      "start_month": "2027-04",
      "end_month": "2027-06",
      "boundary_precision": "MONTH",
      "source_label": "April–June"
    },
    {
      "phase_id": "PHASE_2",
      "start_month": "2027-10",
      "end_month": "2027-12",
      "boundary_precision": "MONTH",
      "source_label": "October–December"
    }
  ]
}
```

## Canonical invariants

The executable validator now enforces all of the following:

1. month tokens are year-qualified `YYYY-MM` values;
2. a single-phase model has exactly one phase;
3. a multi-phase model has at least two phases;
4. every phase has a unique `phase_id`;
5. every phase has `boundary_precision = MONTH` and a source-native label;
6. phase end cannot precede phase start;
7. phases must be ordered and may not overlap;
8. adjacent phases are rejected under `MULTI_PHASE_SEASON_WINDOW` because they are temporally continuous and should be represented as one phase;
9. `time_precision = MONTH` is mandatory;
10. clock-time semantics are prohibited (`time_status` / `time_basis` must be absent or `NOT_APPLICABLE`);
11. `start_local`, `end_local`, UTC timestamps, `date_earliest`, `date_latest` and `publication_datetime` must remain empty;
12. `source_native_window_label` is mandatory.

These rules deliberately make it harder to turn coarse source precision into false calendar precision.

## Browser / Calendar projection semantics

The static web projection now carries:

- `season_window_model`;
- `source_native_window_label`;
- `season_phases[]`.

Month-bounded seasons are **not exact-day events**:

- `eventDateKey()` explicitly returns no day key for them;
- they therefore never appear as an arbitrary chip on a calendar day;
- the calendar windows rail tests overlap at `YYYY-MM` precision against individual phases;
- visible timing uses the source-native wording;
- detail/index views state that no day boundary is asserted.

The browser may derive an internal first-month sort proxy for ordering and future filtering. That proxy is a presentation convenience only. It is never displayed, exported or written back as canonical timing.

## Test evidence

The first read-only architecture preflight was GitHub Actions run `33780453409`.

It established in memory:

- schema v0.49 → v0.50;
- canonical v0.19 / 668 unchanged;
- nine temporal ontology tests PASS;
- canonical registry validation PASS;
- source-of-truth working tree unchanged after dry-run.

The one-shot schema migration run `33780566202` then required:

- fresh fail-closed preflight;
- temporal tests PASS;
- canonical validation PASS;
- exact schema v0.50 postconditions;
- protected hashes for canonical registry, live-monitor expectations and monitor operations policy unchanged;
- changed-file set exactly `data/canonical/schema.json`.

The write-capable workflow was removed immediately after the reviewed commit. The read-only preflight workflow was also retired after completion.

CI was subsequently strengthened with `node --check web/app.js`; Python tests, JavaScript syntax validation and static-site build all pass against canonical v0.19 / 668.

## What this schema does **not** imply

Schema capability is not event-admission evidence.

This tranche does **not**:

- add Fiji/RSMC Nadi occurrences;
- add IMD/RSMC New Delhi occurrences;
- interpret a month-boundary as the first or last civil day of that month;
- make a seasonal outlook the same object as the season it describes;
- grant automated retrieval/reuse permission for Fiji Met or IMD sources;
- promote either source into the scheduled live-monitor cohort;
- authorise Google Calendar writes;
- change the automatic canonical-commit gate.

## Next gate

Before any bounded physical-risk population transaction:

1. re-verify current authoritative Fiji Met / RSMC Nadi evidence and exact regional wording;
2. re-verify current authoritative IMD / RSMC New Delhi evidence and exact two-phase wording;
3. separately re-audit source rights / automated-monitoring permission;
4. determine annual occurrence horizon without generating dates beyond authoritative evidence;
5. run stable-identity/source-ID preflight;
6. populate only the smallest defensible corrective tranche;
7. re-audit coverage after population rather than assuming success from row count.
