# WORLD SIGNALS — prospective Forecast pilot admission audit

**Admission transaction:** `WS-FP-ADMISSION-20260926-001`
**Admitted at:** `2026-09-26T17:00:12Z`
**Information cutoff:** `2026-09-26T17:00:00Z`
**Reviewer:** `project-owner`
**Production Forecast series admitted:** 4
**Outcomes:** 0
**Evaluation:** `NO_SAMPLE`, 0 records

This is the first bounded production Forecast population. It is prospective:
each target remained unresolved at the frozen cutoff and has a future primary
resolution window. The admission transaction records the pre-state and
post-state semantic hashes and the permanent denominator obligation. No
historical Forecasts were backfilled, and no upstream Signal, Relationship,
Risk/Regime or Scenario was manufactured.

| Series | Type | Target and resolution | Primary source | Decision |
| --- | --- | --- | --- | --- |
| `WS-FP-BOC-20261028` | Numeric point | Bank of Canada overnight-rate target, first official 28 October release | [Bank of Canada policy-rate schedule](https://www.bankofcanada.ca/core-functions/monetary-policy/key-interest-rate/) | Admitted |
| `WS-FP-FED-20261028` | Categorical | Federal-funds target-range direction, first official 28 October FOMC statement | [Federal Reserve FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) | Admitted |
| `WS-FP-ECB-20261029` | Categorical | Joint direction of the three key ECB rates, first official 29 October decision release | [ECB Governing Council calendar](https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html) | Admitted |
| `WS-FP-RBA-20261103` | Numeric point | RBA cash-rate target, first official 3 November decision release | [RBA board schedules](https://www.rba.gov.au/schedules-events/board-meeting-schedules.html) | Admitted |

The 29 September 2026 RBA decision was rejected for this first batch because
it was too close to the cutoff and therefore left insufficient room to prove a
clean prospective information boundary. Bank of Japan and RBNZ candidates were
not admitted because the repository source contracts retain timing or rights
holds that make this pilot less mechanically resolvable. Political, election,
conflict-casualty and other contested targets were excluded by policy.

Estimates use transparent persistence baselines from the latest official
policy state, with bounded analyst adjustments represented only by the explicit
categorical distributions. No external consensus was copied as an independent
WORLD SIGNALS forecast. Provenance records a hybrid human-reviewed process;
there is no established automated WORLD SIGNALS forecasting model.

Admitted Forecast substantive fields are frozen. A later analytical estimate
must be a new issuance; an administrative correction cannot change its
probability/value, target, resolution rule, horizon or information cutoff.
No Outcome or score may be created until the primary resolution rule is due
and the governed Outcome layer records what happened.
