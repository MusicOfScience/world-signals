# WORLD SIGNALS — CA USDA NASS Agricultural Statistics Board iCalendar research v0.1

**Reference date:** 2026-09-09  
**Exact post-BZ base:** `07c558c8811795f0aed40e73bd386cc70344191e`

## Decision

CA selects the USDA National Agricultural Statistics Service (NASS) **2026 Agricultural Statistics Board iCalendar** as a bounded, read-only schedule-change sentinel for the five already-modelled forward NASS Crop Production and Grain Stocks occurrences.

The existing source identity `WSSRC-COM-005` is reused in place. This is deliberate: that source already represents the Agricultural Statistics Board calendar, already lists `PDF + ICS` as the machine-readable form, and already carries the five Canonical dependencies. Creating a second machine-source identity would duplicate provenance rather than separate genuinely different source roles.

Proposed route: `USDA_NASS_ASB_ICAL`.

## Why this emerged after BZ

The post-BZ source-aware pressure audit (`34306324400` / `102323665121`) found continued weak production-monitor coverage outside the best-developed macro routes. The audit did **not** turn its regional/category counts into quotas. In particular, a low explicit-route score for North America was not treated as justification to add another US source automatically, while South Asia, Africa and Southeast Asia candidates remained constrained by genuine rights or endpoint holds.

NASS nevertheless survived the selection test for reasons independent of geography:

- it opens a food/agriculture information-catalyst route rather than another central-bank route;
- five high-sensitivity forward Canonical releases already depend on the source;
- the institution explicitly publishes a purpose-built iCalendar schedule;
- NASS explicitly addresses automated retrieval and prohibits excessive rather than all automated access;
- the current route passed a one-request production-shaped diagnostic;
- content reuse is already governed as public-domain factual metadata with NASS acknowledgement requested.

OPEC remained quarantined and was not retried. MoSPI, CBE, Bank of Thailand, Bank Negara Malaysia and other held families were not promoted merely to fill measured gaps.

## Existing Canonical/source authority

Existing source: `WSSRC-COM-005`  
Institution: USDA NASS  
Authoritative calendar family: `https://www.nass.usda.gov/Publications/Calendar/`

At the frozen CA base the source has:

- five Canonical dependencies;
- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`;
- `licence_review_status = CLEARED_PUBLIC_DOMAIN_GENERAL_NASS_INFORMATION`;
- `machine_readable_available = PDF + ICS`;
- `automated_retrieval_permission = PENDING_ENDPOINT_OPERATIONAL_REVIEW`;
- `monitoring_readiness_status = ENDPOINT_REVIEW_REQUIRED`;
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`.

Those last three fields correctly described the earlier state: machine readability alone was not treated as automation permission. CA changes them only after source-specific policy review plus live endpoint validation.

The five exact Canonical dependencies are:

| Occurrence | Series | Current source-native datetime |
|---|---|---|
| `WSO-COM-A-0030` | Crop Production | 2026-09-11 12:00 America/New_York |
| `WSO-COM-A-0032` | Crop Production | 2026-10-09 12:00 America/New_York |
| `WSO-COM-A-0034` | Crop Production | 2026-11-10 12:00 America/New_York |
| `WSO-COM-A-0036` | Crop Production | 2026-12-10 12:00 America/New_York |
| `WSO-COM-A-0037` | Grain Stocks | 2026-09-30 12:00 America/New_York |

All five are exact local datetimes with minute precision and have existing UTC conversions. CA does not alter any of them.

## First-party iCalendar machine interface

NASS's Publications pages explicitly state that the 2026 Agricultural Statistics Board calendar is available in PDF, printer-friendly and **iCalendar** formats:

`https://www.nass.usda.gov/Publications/`

The advertised machine document is:

`https://www.nass.usda.gov/Publications/Calendar/2026/NassReleases2026.ics`

CA treats this as the monitoring endpoint. It does not crawl report pages or use search discovery during a production monitor run.

## Automated-access policy

NASS's Security Statement explicitly discusses automated retrieval programs. It prohibits **excessive** robot activity, including multiple accesses per second that degrade service, and reserves the right to block robots that do not contain contact information for the owner.

Policy source:

`https://www.nass.usda.gov/About_NASS/Security_Statement/index.php`

CA therefore uses:

- one iCalendar request per run;
- the shared WORLD SIGNALS User-Agent containing the repository URL as contact/owner route;
- zero calendar-HTML requests;
- zero report follow-ups;
- zero search/discovery requests.

No claim is made that public-domain content alone grants crawler permission. The automation classification rests on the combination of the explicitly offered iCalendar interface and NASS's explicit non-excessive robot policy.

## Reuse / provenance

NASS's Citation Request page states that most information on the NASS site is public domain and that public-domain information may be freely downloaded and reproduced, while requesting appropriate USDA-NASS acknowledgement:

`https://www.nass.usda.gov/Data_and_Statistics/Citation_Request/`

CA preserves the existing source's factual-metadata provenance and redistribution posture. It does not republish the calendar body.

## Live one-request diagnostic

Run `34306617952`, job `102324539796` — **SUCCESS**, read-only.

The run first froze the exact post-BZ base and inspected the existing source plus its five Canonical dependencies. It then made exactly one external request to the advertised iCalendar endpoint using a WORLD SIGNALS User-Agent with the repository URL.

Observed snapshot:

- HTTP 200;
- `text/calendar`;
- 120,961 bytes;
- 567 VEVENTs in the observed file;
- SHA-256 `23ceabbd75ca89c98ff42859997abef67fe444e2829945747cbadc1788175a9a`;
- five configured target events present.

Neither the body hash nor 567-event count is a permanent production invariant.

The configured current feed identities are:

| UID | Canonical occurrence | Summary | Floating DTSTART |
|---|---|---|---|
| `a763c1f5-aef0-435a-a183-2f8191f08d99` | `WSO-COM-A-0030` | Crop Production | `20260911T120000` |
| `7172110f-8719-4672-9026-f708df320e71` | `WSO-COM-A-0032` | Crop Production | `20261009T120000` |
| `cf36624c-7ddb-4293-ad32-c52b78d0e299` | `WSO-COM-A-0034` | Crop Production | `20261110T120000` |
| `49647b19-c690-45dc-a48f-54d12ea99307` | `WSO-COM-A-0036` | Crop Production | `20261210T120000` |
| `4b58e729-3b3b-4f2a-a86e-2ee17637ad46` | `WSO-COM-A-0037` | Grain Stocks | `20260930T120000` |

## Floating time is not silently timezone-aware

The live ICS `DTSTART` values are floating datetimes: they carry neither `Z` nor `TZID`. CA therefore refuses to treat the ICS syntax alone as timezone authority.

The timezone interpretation is separately grounded in NASS's first-party **Reports by Date** pages. For September, October, November and December 2026, the configured Crop Production and Grain Stocks releases are explicitly displayed at **12:00 pm ET**. The existing Canonical source timezone is `America/New_York`.

CA therefore permits the parser/comparator to interpret these specific floating schedule values in `America/New_York` only under an explicit governed timezone contract. If the route or Canonical timezone drifts, it fails closed.

This matters across daylight-saving boundaries: September and October map to UTC-4; November and December map to UTC-5. The adapter uses the IANA timezone rather than a fixed offset.

The HTML pages are policy/timezone corroboration only. Production monitoring makes **no HTML request**.

## DTSTART versus other ICS fields

For the configured events the live VEVENT field set includes `UID`, `SUMMARY`, `DESCRIPTION`, `DTSTART`, `DTEND`, `DTSTAMP` and `SEQUENCE`.

Only configured `UID`, exact `SUMMARY`, and governed `DTSTART` participate in event schedule comparison.

CA explicitly does **not** promote:

- the five-minute ICS `DTEND` into event duration or Canonical end time;
- `DTSTAMP` into event time;
- `SEQUENCE` into lifecycle/certainty state;
- `DESCRIPTION` into clock or event-state authority.

## Identity limits

The current feed gives each configured event a UUID UID. CA uses that UID as a configured monitoring identity but does not overclaim that NASS guarantees UID persistence under every rescheduling mechanism.

If a date change preserves the UID, the same stable Canonical occurrence receives a datetime-change review candidate.

If NASS replaces an event with a new UID and removes the configured UID, the route produces a **missing-UID review**. It does not guess that a different same-title event is the same occurrence.

An unconfigured future `Crop Production` or `Grain Stocks` event may be surfaced as observation-only evidence after the CA review floor, but it cannot create a Canonical occurrence automatically.

## Comparator semantics

### Exact configured UID + current datetime

Emit `NASS_ASB_ICAL_DATETIME_MATCH_OBSERVATION`. No review candidate.

### Same configured UID + changed datetime

Create `NASS_ASB_ICAL_DATETIME_CHANGE_REVIEW` against the **current Canonical** local datetime and UTC timestamp. No direct mutation.

### Configured UID missing

If the Canonical occurrence is not `COMPLETED`, create `NASS_ASB_ICAL_CONFIGURED_UID_MISSING_REVIEW`.

Absence is not cancellation, completion, postponement or certainty change.

If the Canonical occurrence is already `COMPLETED`, absence is corroborative/source-health observation only.

### Structural drift

Duplicate UIDs, malformed ICS, target summary drift, invalid floating datetimes, unexpected timezone parameters or Canonical timing-shape drift fail closed as source-health evidence rather than guessed schedule changes.

## Authority boundary

The route has no authority over:

- automatic Canonical datetime writes;
- lifecycle;
- certainty;
- Canonical name;
- automatic creation of new NASS occurrences;
- report-page retrieval;
- Live Intelligence or Analysis promotion;
- automatic commits.

The monitor is a change sentinel and review generator, not a second Canonical database.

## Request boundary

Per production monitor run:

- iCalendar requests: 1;
- robots requests: 0;
- calendar HTML requests: 0;
- report follow-ups: 0;
- search/discovery requests: 0;
- total external request budget: 1.

## Expected governed post-state

If all offline, materialised and live gates pass:

- Canonical Registry: v0.41 / 689 — unchanged;
- Sources: v1.99 / 255 → v2.00 / 255;
- Monitor expectations: v0.24 / 22 → v0.25 / 23;
- only `WSSRC-COM-005` changes in the source registry;
- Change Ledger unchanged;
- biosecurity unchanged;
- Live Intelligence unchanged;
- Analysis unchanged;
- automatic Canonical commit OFF;
- Google Calendar write OFF.
