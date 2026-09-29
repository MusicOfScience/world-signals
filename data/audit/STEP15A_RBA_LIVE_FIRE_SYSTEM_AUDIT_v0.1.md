# Step 15A — RBA live-fire systems audit

**Status:** diagnostic/design only. The audit did not admit an outcome, alter a production layer, activate monitoring, or change the public site.

## Finding

WORLD SIGNALS correctly moved its device-clock-based **NEXT ON THE CALENDAR** lane past the elapsed RBA decision. That is calendar chronology, not outcome detection. The configured `RBA_MPB_CALENDAR` route is a schedule-change sentinel: it checked the RBA robots policy, Monetary Policy Board topic calendar and Board schedule, and returned `RBA_MPB_CALENDAR_EVENT_NO_CHANGE` for the 29 September decision. It does not inspect decision publications or extract rate/unanimity facts.

The event was present in Canonical as `WSO-d2a7c4e4416b505b`, series `WS.CB.RBA.MONETARY_POLICY_DECISION`, scheduled for 29 September 2026 at 14:30 AEST (`2026-09-29T04:30:00Z`). At 19:13 AEST the reader-facing next event was Australia CPI on 30 September at 11:30 AEST. The event's scheduled time passing did not establish completion.

The official RBA release, [Media Release 2026-27](https://www.rba.gov.au/media-releases/2026/mr-26-27.html), states that the Board raised the cash rate target by 25 basis points to 4.60 per cent and that the decision was unanimous. Its accompanying explanation is retained as issuer-stated rationale, not independent WORLD SIGNALS causal analysis.

**Classification: `OUTCOME_DETECTION_COVERAGE_GAP`.** The first missing system boundary is T3, detection of an official decision publication. The existing schedule sentinel is not broken; it is not an outcome publication sentinel or result extractor.

## Three kinds of dynamism

### Clock dynamism

`web/briefing.js` calls `load()` once. `nextCalendarEvent()` selects the earliest eligible event whose parsed time is `>= Date.now()`, breaking ties by occurrence ID. Deterministic fixture results:

| Melbourne time | Selected event | Meaning |
|---|---|---|
| 14:29 | RBA decision | It is the next eligible occurrence. |
| 14:30 | RBA decision | Boundary is inclusive (`>=`). |
| 14:31 | RBA press conference | Decision left the next lane; no completion was inferred. |
| 19:13 | Australia CPI, 30 Sep 11:30 | Both RBA schedule items had elapsed; chronology only. |

An open page does not rerun this calculation as time passes. The Brief has no interval, timer, visibility, pageshow or focus refresh hook. The displayed Melbourne reference clock is also populated by the app's initial `renderProductBrief()` call, not a ticking clock. This is a `CLIENT_CLOCK_REEVALUATION_GAP`, separate from the outcome-detection gap.

### Public-data refresh

The Brief fetches `briefing.json`, `outlook.json`, `events.json` and `analysis.json` once at module load. It has no public-version check and no automatic re-fetch on focus/visibility. A newly deployed edition can therefore remain absent from an already-open document until it is reloaded or replaced. The current app has no service worker. Browser/CDN cache policy is not a substitute for application refresh logic.

Read-only HEAD requests to the deployed public status, events and Brief resources returned `Cache-Control: max-age=600` and ETags. The public status response also exposed HTTP `Last-Modified: 2026-09-28T22:33:08Z`. That header describes a served static artifact; it is not a governed application claim that intelligence sources were checked or reviewed at that time. No `generated_at`, build edition ID or public-data bundle fingerprint is present in the public data contract.

**Future freshness contract:** publish an edition identifier tied to the public dataset bundle fingerprint, source commit, and a genuine build/deployment timestamp. Label device time as **Your time** and the generated edition as **Public data rebuilt**. Do not label build time as source-review time. A future client can refresh on `pageshow`, focus and visibility regain, plus a bounded visible-tab edition check (proposed no more often than every 10 minutes); re-fetch derived data only when the edition changes. Exact cadence remains a service-policy decision, not a Step 15A implementation.

## RBA schedule monitor and bounded live run

The production configuration identifies `RBA_MPB_CALENDAR` as `RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL`, configured `DAILY`, with a three-request budget and sequence:

1. RBA `robots.txt`;
2. official MPB topic calendar;
3. official Board meeting schedule.

Its contract says `elapsed_time_policy: NO_COMPLETION_INFERENCE` and `automatic_commit_allowed: false`. The configured run rechecks robots before fetching schedule paths; it does not treat a missing schedule item as cancellation, delay, completion or certainty change. The GitHub live-monitor workflow is manual-dispatch only; its comments say routine monitoring uses a guarded local scheduler. The actual local scheduler interval was not inspected.

At 2026-09-29 09:34 UTC, I invoked only the already-configured RBA fetch/parse/alignment and candidate-comparison functions, avoiding the all-source runner and its artifact writes. Results: robots 200 and schedule path allowed; topic calendar 200 (55 parsed events); Board schedule 200 (16 windows); no schedule drift for the target occurrence; zero review candidates. The run did not fetch the decision release, observe 4.60%, or observe unanimity. No repository or governed state was written.

The RBA first-party release confirms the outcome. The official RSS landing page advertises a Media Releases feed that includes Monetary Policy Decision statements, and the linked feed endpoint is `https://www.rba.gov.au/rss/rss-cb-media-releases.xml`. RBA's robots rules observed in the monitor run do not disallow `/rss/`; its general reuse terms describe most material as CC BY 4.0 but impose special Cash Rate conditions and attribution/non-endorsement requirements. Existing `WSSRC-CB-002` automation authority is narrowly cleared for `/schedules-events/` schedule paths, not this RSS route. Therefore the feed is a promising **candidate** source, not permission to activate a new route. Feed schema, retention, update behavior and operational rights still need a specific preflight/review. Do not guess release serial URLs.

## Event-resolution chain

| Boundary | Audit result |
|---|---|
| T0 Canonical scheduled occurrence | Implemented; target remains `PLANNED`. |
| T1 scheduled time arrives | Device-clock chronology only; no governed transition. |
| T2 official publication | External RBA release exists. |
| T3 WORLD SIGNALS detects publication | Missing for the current route. |
| T4 result review candidate | Not available; no publication/result candidate produced. |
| T5 human/governed review | Existing review/admission patterns exist, but were not entered for this event. |
| T6 Canonical completion admitted | Not performed; must remain an explicit governed action. |
| T7 result fact/observation admitted | Missing for this event; no Live observation created. |
| T8 public projection regenerated | Existing static builder supports manual rebuild after governed input changes. |
| T9 Pages deployed | Existing main/deployment workflow; no outcome was admitted to trigger this chain. |
| T10 open client sees new edition | No edition check or re-fetch; reload required. |
| T11 reader sees confirmed outcome | No governed outcome projection exists for this occurrence. |

No source-publication availability timestamp, actual local scheduler interval, review latency, admission-to-build latency or per-event deployment latency is available. These remain `UNKNOWN`, not implied SLAs. The RBA schedule announces a 14:30 AEST release; that is its scheduled publication time, not an independently verified delivery-latency measurement.

## Target event state and public “NOW” source

Recommended projected states are:

- `UPCOMING` — scheduled occurrence is still future.
- `AWAITING_CONFIRMATION` — scheduled time passed, but no governed result exists.
- `SOURCE_CHECK_UNAVAILABLE` — only when a current governed check explicitly reports source failure; never infer this from missing data.
- `DETECTED_REVIEW_PENDING` — internal-only candidate state.
- `CONFIRMED_OUTCOME` — admitted result fact with separate public eligibility.
- `ANALYSIS_AVAILABLE` — a public Analysis is explicitly linked and published.

Elapsed time can only move the reader from upcoming to awaiting confirmation. A parser result is not a public fact.

For “NOW”, use the existing reviewed/admitted Live Intelligence observation as the factual substrate, explicitly linked to the Canonical occurrence. Canonical may separately record governed completion. A small allowlisted public event-resolution projection can join those existing layers after publication eligibility is granted. Do not use Forecast Outcome as a generic event-result store; do not require Analysis for a simple result fact; do not introduce a duplicate outcome database. When multiple eligible events exist, use explicit publication eligibility, then chronology and occurrence ID as neutral deterministic tie-breaks. No importance or newsworthiness score.

## Candidate next RBA tranche

If a first-party audit confirms the RSS behavior and source-governance review clears that endpoint, implement one `RBA_MPB_DECISION_PUBLICATION_SENTINEL` candidate route. It should match an official decision-statement item to an explicit allowlisted Canonical occurrence by title family and publication date, verify the linked release, extract only the decision, prior/new rate, basis-point change and unanimity, and produce a review-only candidate. It must have bounded request counts, explicit duplicate/update handling, no broad search, no inferred completion from feed absence, no automatic Canonical/Live/Analysis mutation, and no activation until rights/operations approval. Prove that one route end-to-end before considering another central bank.

The official RBA RSS landing page explicitly recommends feeds for software/feed-reader use. Current robots policy does not disallow `/rss/`, but the existing monitored permission covers only `/schedules-events/`; endpoint semantics, feed retention, rights scope and operational failure behavior need a separate decision. This is a route-review recommendation, not an activated monitor.

## Mobile home finding

The supplied iOS capture shows progressive accumulation: Brief, all Forecast cards, Resolution Clock, multiple long Analysis reviews, NOW/NEXT, then the full 30-day horizon (105 occurrences). The material can be useful while still making the opening task too long. The non-public prototype is at `prototypes/step15a-mobile-home/` and uses explicit fixture-only event results.

Its editorial spine is:

1. **NOW** — one compact scheduled/pending/result item;
2. **NEXT** — one next governed Calendar event and a clear Calendar link;
3. **OUTLOOK** — four compact monetary-policy forecasts, with unresolved status and target semantics;
4. **LATEST ANALYSIS** — one headline/short abstract and a direct Analysis link;
5. **EXPLORE** — Calendar, Analysis and Research destinations.

The homepage omits the standalone Resolution Clock and full event horizon. The Outlook destination owns exact cutoff, full distribution and resolution rules; Analysis owns the full review. The prototype is intentionally excluded from `scripts/build_site.py`'s explicit web-file copy list.

## Architecture comparison

| Option | Safety/latency | Complexity/operations | Finding |
|---|---|---|---|
| A. Static site, manual review and deploy | High epistemic safety; latency depends on operator availability. | Lowest complexity and operating burden; clear audit trail. | Safe interim path, but cannot reliably answer an elapsed event promptly. |
| B. Bounded publication sentinel → review candidate → human approval → automated build/deploy | Preserves human admission; bounded polling latency after endpoint and rights approval. | Moderate; requires endpoint review, durable candidate/review audit, failure handling and guarded build trigger. | Best next architecture once the single RBA route is separately cleared. |
| C. Near-real-time runtime public data service | Lowest potential reader latency but a parser/service failure can directly affect public facts. | Highest complexity, availability, security and on-call burden; least aligned with current local-first/static governance. | Not justified now. |

Recommend a staged Option B, keeping Option A as the fail-safe. The Step 15A evidence identifies the missing publication-detection boundary; it does not authorize implementation or activation.

## Mutation and publication boundary

The audit ran read-only source requests and deterministic fixtures only. Canonical, source registry, monitor expectations, Live Intelligence, Analysis, Signals, World State, Relationships, Forecasts, Scenarios, Risks and Outcomes were not changed. No new route, retrieval job, observation, Analysis, Forecast resolution or public artifact was created. The prototype and audit files are not part of the public-site build.
