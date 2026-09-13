# WORLD SIGNALS — monitor health repair CU plan v0.1

Date: 13 September 2026 (Australia/Melbourne)

## Governed base

- `main`: `5bb0ee475afb818a8cc358cb243f56f0ea252886`
- predecessor: merged PR #128, cross-domain risk overlay CT
- branch: `codex/monitor-health-repair-cu`

## Trigger evidence

Local production run `LOCAL-00000003-20260913T121630Z` observed all 26 configured adapters, with 24 healthy and two degraded:

1. `INDEC_CPI_CALENDAR` found no configured national CPI identity in `Septiembre-2026` after the governed 10 September release date. Direct inspection showed the official route remained structurally healthy and continued to expose later September releases. The route is a rolling future calendar, so disappearance after the release date is not a source failure and has no completion, delay, cancellation or certainty semantics.
2. `NZ_ELECTION_TIMETABLE_CHANGE_RSS` returned HTTP 200 with `text/html` and an Imperva/Incapsula access-denial document instead of the advertised RSS feed. That response is source-access health only and contains no election timetable evidence.

## Bounded change

- Permit a configured INDEC month route to contain no CPI row only after that occurrence's governed release date has passed in `America/Argentina/Buenos_Aires`.
- Continue to fail closed when a future configured CPI row is absent, duplicated, malformed, off-month or otherwise structurally inconsistent.
- Record a past rolling-window absence as a non-event observation and do not generate a change candidate from that absence.
- Classify the observed Elections NZ perimeter-security response explicitly while retaining degraded health and all existing no-write/no-inference controls.
- Keep live and smoke execution paths aligned.

## Boundaries

- No Canonical, source-registry, expectation, change-history, Live Intelligence or Analysis mutation.
- No lifecycle, date, clock, certainty, probability, impact or causal inference.
- No attempt to evade Elections NZ perimeter security, disguise the WORLD SIGNALS user agent, follow feed-item links or fetch the held timetable HTML route.
- OPEC quarantine remains dormant and unchanged.
- The owner performs any merge under `HANDOFF_PROTOCOL.md`.

## Gate

- focused parser/comparator and monitor policy tests;
- full ordinary validation suite at exact committed head;
- exact-head governed local operations run against all configured endpoints;
- Canonical byte guard, protected-path diff, structural diff and residue checks;
- hosted CI when runnable, otherwise the owner-authorised exact-head local fallback.
