# WORLD SIGNALS — BS research note

## Purpose

Select the next production-monitor tranche after BR using the post-BR governed state, with explicit pressure against regional concentration and without weakening source/automation governance.

Exact baseline: `22a5c0a922d3a126bf268acb61a68abe1bfe5075`.

## Regional pressure audit

Read-only audit `34212793713` / job `102017467282` found:

- South Asia: 29 Canonical occurrences, 0 configured production-monitor routes.
- Southeast Asia: 19 Canonical occurrences, 0 configured production-monitor routes.
- Africa: 19 Canonical occurrences, 1 route.
- Latin America: 21 Canonical occurrences, 1 route.
- Oceania / Pacific: 119 Canonical occurrences, 2 routes.

South Asia therefore remained the largest clear production-monitor gap.

## MoSPI first-pass candidate — held, not activated

`WSSRC-MAC-017` (India Ministry of Statistics and Programme Implementation) has 18 South Asia Canonical dependencies and remains a valuable authoritative schedule source.

Current authoritative surfaces include the FY2026-27 Advance Release Calendar PDF and MoSPI calendar/announcement pages. The source remains suitable for curated Canonical provenance, but BS did not establish a sufficiently clean automated access contract:

1. `https://www.mospi.gov.in/robots.txt` returned HTTP 200 with `text/html` and a React application shell, not a valid robots policy. This must not be interpreted as permission.
2. Public calendar surfaces were inconsistent: the announcement route rendered releases while `/release-calendar` and `/advance-release-calendar` rendered no releases during research.
3. The React bundle exposed a generic first-party `/api/` base, but no documented release-calendar API was established. BS did not probe guessed API paths.
4. The updated ARC PDF was transport-retrievable, but successful PDF transport does not itself establish an automated retrieval permission model.

Read-only MoSPI diagnostic: run `34213065847`, job `102018354714`.

Decision: preserve `WSSRC-MAC-017` as an endpoint-review hold. South Asia remains a priority for future source-method work rather than being forced into production to satisfy a coverage target.

## BSP selection

The next candidate was Bangko Sentral ng Pilipinas (BSP), whose existing schedule source `WSSRC-REGJ-003` has two remaining 2026 Canonical dependencies:

- `WSO-REG-J-0008` — monetary policy stance decision — 22 October 2026.
- `WSO-REG-J-0009` — monetary policy stance decision — 17 December 2026.

Both are date-only `Asia/Manila` Canonical occurrences. The existing notes state that the official Monetary Board calendar and advance-release schedule align the policy meeting with the monetary-policy stance release date. No unsupported clock is present or added.

### Existing schedule source

`WSSRC-REGJ-003` predates several modern governance fields. It already records:

- official BSP monetary-policy calendar authority;
- two Canonical dependencies;
- curated factual reuse with attribution;
- `PENDING_ENDPOINT_OPERATIONAL_REVIEW` for automated retrieval;
- `ENDPOINT_REVIEW_REQUIRED` monitoring readiness;
- HTML/PDF source type;
- `UNKNOWN_NOT_LIVE_POLLED` runtime health.

Missing fields (`canonical_provenance_use`, `automated_monitoring_use`, `verification_mode`, `monitoring_activation_status`) are a schema-era gap, not evidence of automation clearance. BS backfills them conservatively while preserving the schedule-source hold.

## Official BSP RSS machine interface

BSP publishes an official RSS page:

`https://www.bsp.gov.ph/SitePages/RSS.aspx`

The page explicitly describes RSS feeds as fetching updates automatically and describes RSS as structured information usable by applications. That is machine-interface intent materially stronger than public-page fetchability alone.

The public page publishes a SharePoint template expression for the **Media Releases** feed. A quote-aware deterministic parser resolves only BSP-published variants of that expression to:

`https://www.bsp.gov.ph/_layouts/15/listfeed.aspx?List=9b0a2117-49d8-4e96-80ba-8651a0e3e17a&View=8c968884-887d-4d63-8c00-ba05ea3c2d93`

The resolver validates:

- HTTPS;
- exact `www.bsp.gov.ph` host;
- exact `/_layouts/15/listfeed.aspx` path;
- only `List` and `View` query keys;
- UUID-shaped List and View identifiers.

It does not construct or search arbitrary SharePoint list endpoints.

## Read-only live diagnostic

Successful diagnostic:

- run `34213769016`
- job `102020585149`
- official RSS documentation HTTP 200
- Media Releases RSS HTTP 200
- Content-Type `text/xml; charset=utf-8`
- 30 RSS items retained at observation time
- one feed request
- repository read-only

Observed feed SHA-256:

`715c610524b3e7339e5f649cdb74536d11a06b056af6ed85716ab9843b78b013`

The feed contained a real 27 August 2026 monetary-policy stance release:

`Monetary Board raises target RRP Rate by 25 basis points`

Its body begins with the structurally strong statement that, at its monetary policy meeting that day, the Monetary Board decided to change the Target Reverse Repurchase rate. This historical item is outside the two-occurrence BS allow-list and therefore becomes classifier evidence only, not a Canonical proposition.

The broad keyword scan also found false positives: bank-lending releases, discount-window rates, business sentiment and credit-rating commentary can mention monetary policy. Therefore BS deliberately rejects generic keyword matching.

## Production classification contract

A feed item qualifies as a BSP monetary-policy stance publication only when both are true:

1. the title begins `Monetary Board ` (case-insensitive); and
2. normalized body text contains `At its monetary policy meeting today, the Monetary Board decided` (case-insensitive).

For a qualifying item:

- preserve the RSS `pubDate` as publication evidence;
- normalize it to UTC for evidence storage;
- convert the same instant to `Asia/Manila` and derive the publication civil date;
- match only if that civil date exactly equals one of the two configured Canonical occurrence dates;
- if exactly one occurrence matches and is not already `COMPLETED`, create a review candidate;
- if the occurrence is already `COMPLETED`, record corroboration only;
- if the item is historical/outside configured scope, record observation only;
- if identity is ambiguous, fail closed;
- finite-feed absence has no schedule, lifecycle, cancellation or certainty semantics.

The RSS publication timestamp is **not** the event clock. The route cannot create or upgrade Canonical time precision.

## Source-role separation

`WSSRC-REGJ-003` remains the Canonical forward-schedule authority. Its HTML/PDF automation state remains held.

BS creates `WSSRC-REGJ-006` as a separate machine source for the official BSP Media Releases RSS feed. It has zero Canonical dependencies and is monitor-only.

The production route performs exactly one official RSS request per daily run. It does not follow item links and does not fetch the BSP schedule HTML/PDF automatically.

## Non-authorities preserved

The BS route has no authority to:

- change a Canonical scheduled date;
- set or infer an event clock;
- mark an occurrence `COMPLETED` automatically;
- change certainty;
- infer cancellation or delay from RSS absence;
- promote evidence automatically into Live Intelligence or Analysis;
- write Google Calendar;
- commit Canonical changes automatically.

## Expected governed state after BS

- Canonical: `v0.41 / 689` unchanged.
- Sources: `v1.91 / 249` → `v1.92 / 250`.
- Monitor expectations: `v0.16 / 14` → `v0.17 / 15`.
- Southeast Asia gains its first configured production-monitor route.
- South Asia remains a documented priority gap with MoSPI held pending a defensible machine-access route.
- Change Ledger, biosecurity overlay, Live Intelligence and Analysis remain unchanged.
- automatic Canonical commit remains OFF.
- Google Calendar writes remain OFF.
