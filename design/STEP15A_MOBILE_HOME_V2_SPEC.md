# Step 15A — mobile home v2 design specification

**Status:** non-public design prototype; no production UI or public projection change.

## Reader task

In the first one or two ordinary phone viewports, a reader should be able to answer:

1. What just happened, or what is awaiting confirmation?
2. What happens next?
3. What does WORLD SIGNALS forecast?
4. Where is the latest full analysis?
5. How fresh is this public edition?

The home is an editorial front page, not the publication concatenated vertically. Apply **progressive disclosure, not progressive accumulation**.

## Information hierarchy

`WORLD SIGNALS → freshness → NOW → NEXT → OUTLOOK → LATEST ANALYSIS → EXPLORE`

- **NOW:** one compact occurrence/result. Before an admitted result, say that confirmation is pending. A fixture result must be labelled as a prototype fixture. Never expose a private candidate.
- **NEXT:** one exact-date governed occurrence, one-sentence time, and `Full Calendar →`.
- **OUTLOOK:** four compact pilot Forecast rows. Preserve target/value, scheduled issuer date, and `Unresolved`; link to `See forecasts →`. Exact resolution rule, full distribution and cutoff remain in Outlook.
- **LATEST ANALYSIS:** one public headline and short abstract, with `Read analysis →`. Full reviews stay in Analysis.
- **EXPLORE:** direct Calendar, Analysis and Research destinations; no vague “More” affordance.

Remove the standalone home Resolution Clock because it duplicates Outlook resolution timing. Remove the full 30-day horizon and multiple long Analysis entries from the home; keep both in their destination views.

## Event/result epistemics

Use separate source fields for device time and the public-edition freshness timestamp. If the edition timestamp is absent, state that freshness cannot be verified; never synthesize “updated now” from `Date.now()` or an HTTP cache header. A passed scheduled time is only `AWAITING_CONFIRMATION`. A detected-but-unreviewed candidate remains internal. A public confirmed result requires an admitted fact and explicit public eligibility.

Suggested compact RBA fixture states:

- `PRE_EVENT`: “RBA decision · Due 2:30 pm AEST”.
- `EVENT_TIME_PASSED_AWAITING_CONFIRMATION`: “Decision time passed · Awaiting confirmed outcome”.
- `CONFIRMED_OUTCOME`: fixture-only “RBA raised cash rate to 4.60% · +25 bp · 29 Sep”.
- `CONFIRMED_OUTCOME_WITH_ANALYSIS`: same fixture plus a clear `Read analysis →` affordance, also marked as illustrative.

These are prototype fixtures, not production facts. Source rationale is not rendered as WORLD SIGNALS analysis.

## Freshness and client update target

The current public data contract has no generated-edition timestamp, source-review timestamp or bundle fingerprint. HTTP `Last-Modified`/ETag/Cache-Control are transport metadata, not governed intelligence freshness. A future build should provide an edition ID, source commit, public bundle hash and actual build/deploy timestamp, while explicitly distinguishing build time from last evidence review.

Future client behavior may check on `pageshow`, focus and visibility regain and perform a bounded edition check only while visible (candidate cadence: at most every 10 minutes). If the edition changes, fetch public derived projections with revalidation and update the page. This is a design proposal; Step 15A adds no production polling.

## Visual and interaction requirements

- 390 px and 430 px phone widths: single-column flow, no horizontal scrolling, legible 16 px body text, useful line length, touch targets at least 44 px high.
- Desktop: restrained editorial width with whitespace; no stretched dashboard cards.
- Use warm archival paper, ink and one muted accent; fine rules and typographic hierarchy, not an admin-tile grid.
- State selector is labelled and keyboard operable. Headings use a semantic hierarchy. Links name destinations. Focus is visible. Respect reduced-motion preferences; no animation is needed.
- Forecast rows preserve probability/value and unresolved status without implying resolution or evaluation.
- Do not rank events by importance. “NOW” and “NEXT” use an explicit eligible event and chronological selection only.

## Human-task heuristic

Review at 390 × 844, 430 × 932 and desktop. For all four states, check:

- “What just happened?” answered or honestly identified as awaiting confirmation within about 5 seconds;
- “What happens next?” visible within about 5 seconds;
- four current Forecast scans visible within about 10 seconds;
- latest Analysis destination plainly linked within about 10 seconds;
- local device time and public data freshness visibly separate immediately.

This is a design heuristic, not user research. Do not claim participant testing.

### Step 15A heuristic result

By content and semantic inspection, the prototype provides an obvious response
to all five tasks: the NOW state is first; NEXT is one event; Outlook has four
compact values; the latest Analysis has a direct link; and local time is
visually separate from the explicit absence of a public-edition timestamp. The
awaiting state says confirmation is pending and explicitly rejects elapsed-time
inference. These are design-review judgments, not timed user observations.

**Visual capture:** `VISUAL_CAPTURE_UNAVAILABLE`. The in-app browser rejected
the local prototype URL under its security policy, which also disallows attempts
to route around that restriction. Therefore no rendered screenshot or claim of
visual inspection is made. The 390 px, 430 px and desktop layouts have only
structural/CSS rules available for later visual verification.

## Non-public fixture prototype

`prototypes/step15a-mobile-home/` contains the four states, compact Forecast scan, single next Calendar event and one Analysis preview. It is excluded from the public build because the builder copies an explicit allowlist from `web/`; no prototype file is referenced by production HTML or generated data.
