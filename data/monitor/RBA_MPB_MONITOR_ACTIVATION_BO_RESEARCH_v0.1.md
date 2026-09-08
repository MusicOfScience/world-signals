# WORLD SIGNALS — RBA MPB monitor activation research BO v0.1

**Exact base:** `3a6869a054372e5df135067df77fb9bdc772367e`  
**Mode:** bounded daily read-only Source/Change Monitor activation; no Canonical write authority.

## Why RBA wins this tranche

Post-BN, Africa remains a genuine production-monitor gap because the Kenya Law endpoint demonstrated variable GitHub Actions reachability and unresolved unattended-access permission. BO therefore does not force an African route for geographic appearance.

Among mature readiness candidates, the Reserve Bank of Australia Monetary Policy Board has the stronger current operational footing. Its schedule/parser contract was already built in BJ, its current official schedule surfaces are live and internally cross-checkable, most RBA website content is published under CC BY 4.0 subject to stated exclusions, and the RBA publishes a robots policy for `User-agent: *` that does not disallow `/schedules-events/`.

The robots signal is treated as an operational machine-access policy, not as blanket legal permission. BO clearance is deliberately narrow: at most three requests per daily run, limited to robots.txt and the two already reviewed schedule surfaces.

## Official surfaces

- MPB topic calendar: `https://www.rba.gov.au/schedules-events/calendar/?topics=monetary-policy-board`
- Board meeting schedules: `https://www.rba.gov.au/schedules-events/board-meeting-schedules.html`
- crawler policy: `https://www.rba.gov.au/robots.txt`
- content/reuse policy: `https://www.rba.gov.au/copyright/`

The topic calendar separately exposes meeting windows, decision statements, Governor media conferences and minutes. The Board schedule independently exposes meeting windows. BO preserves that separation.

## Read-only diagnostic

GitHub Actions run `34196933651`, job `101966639103`, on 8 September 2026:

- exact post-BN ancestry: PASS;
- topic calendar: HTTP 200;
- Board schedule: HTTP 200;
- robots.txt: HTTP 200;
- `/schedules-events/` not disallowed for `User-agent: *`;
- topic calendar / Board schedule alignment: PASS;
- parsed topic-calendar events: 31;
- parsed Board meeting windows: 16;
- topic-calendar semantic schedule hash: `c7be2be9424706b936f5f1b9557947366cb90d0043373e39d5ad3c4b863831dc`;
- existing RBA MPB adapter regression: PASS;
- repository mutation: none.

The diagnostic is evidence of current technical and operational suitability, not evidence that HTTP 200 alone grants permission.

## Canonical scope and the 33/44 distinction

The RBA MPB family contains **44 Canonical occurrences** from the 28–29 September 2026 meeting through December 2027:

- 11 meeting windows;
- 11 monetary-policy decisions;
- 11 media conferences;
- 11 minutes releases.

`WSSRC-CB-002` has 33 Canonical dependencies: meeting windows, decisions and media conferences. The 11 minutes occurrences retain `WSSRC-CB-013` as their Canonical source identity. The topic calendar may provide monitoring evidence about those minutes, but BO must not rewrite their Canonical provenance.

This distinction is material. A monitor source is evidence used by the Source/Change Monitor; it is not automatically the Canonical source of every occurrence it can observe.

## Temporal semantics

The RBA publishes the relevant times in its local Australian eastern time context. WORLD SIGNALS keeps `Australia/Sydney` as the source-native IANA timezone and preserves published AEST/AEDT labels as evidence.

Meeting windows are civil-date ranges. Decision statements, media conferences and minutes are exact local times where explicitly published. BO never manufactures a meeting start clock.

The user-supplied historical heuristic that the final advertised meeting day is normally decision day remains useful interpretation context only. BO does not use that heuristic to create or alter an occurrence because the RBA currently publishes the decision and media-conference entries explicitly.

## Monitor semantics

Board schedules are primary monitoring evidence for meeting windows. The topic calendar meeting-window entries are cross-validation evidence, avoiding duplicate comparisons.

The topic calendar is primary monitoring evidence for decision, media-conference and minutes timing. Matching is limited to the explicit 44-ID allow-list, the expected series kind and the nearest civil date inside a 14-day bound. A tied identity is not guessed.

A positive observed date/time difference creates a review candidate only. It cannot directly mutate Canonical.

Absence has no event-state semantics. The topic calendar is rolling and need not expose every future Canonical occurrence already scheduled through 2027. A missing current-page item therefore cannot imply cancellation, delay, completion or loss of certainty.

Elapsed time likewise cannot imply completion.

## Runtime policy

Each daily run first requests robots.txt. If `/schedules-events/` becomes disallowed for the general crawler policy, BO must fail closed and skip the two schedule requests. That condition is source-health/governance evidence only and does not change any event.

If robots remains compatible, the run may request exactly the MPB topic calendar and Board schedule. This caps BO at three small requests per daily run and avoids broad RBA crawling.

## Governed target

BO may advance:

- Source Registry `v1.87 / 247` → `v1.88 / 247`, changing only `WSSRC-CB-002` operational monitoring metadata;
- Monitor expectations `v0.12 / 10` → `v0.13 / 11`, appending one review-only `RBA_MPB_CALENDAR` route;
- runtime wiring required to execute and smoke-test that route.

BO may not change Canonical, Change Ledger, biosecurity overlay, Live Intelligence datasets or Analysis datasets. Automatic Canonical commit and Google Calendar writes remain disabled.

## Geographic interpretation

This activation strengthens Oceania/Pacific production monitoring and the Australian monetary-policy layer. It does **not** solve the still-important Africa production-monitor gap exposed by BN. That gap remains an architectural pressure for later work rather than a quota to satisfy with a weak endpoint.
