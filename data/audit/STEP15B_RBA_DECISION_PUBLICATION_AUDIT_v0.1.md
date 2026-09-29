# Step 15B — “The Bank Has Spoken” audit

**Result: T3 observed; real T4 candidate generation not proven.** This is a
candidate-only tranche. The schedule monitor remains unchanged and no
production, downstream, or public state was modified.

The existing `RBA_MPB_CALENDAR` route is correctly a schedule-change sentinel
over the approved schedule surfaces. Its role remains
`RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL`; elapsed time is
`NO_COMPLETION_INFERENCE`; automatic commit is false. It is not a decision
publication detector and is not defective for failing to extract a result.

The RBA RSS directory identifies its Media Releases feed as including Monetary
Policy Decision statements. Its RSS Q&A describes the format as suitable for
automated software/feed-reader use and warns that the feeds are protected by
WAF controls. The live feed returned `200 text/xml` and contained the exact
29 September item, publication time `2026-09-29T14:30:00+10:00`, and linked
official release. Current robots rules do not disallow `/rss/` or
`/media-releases/`. The RBA copyright terms separately discuss content reuse;
they do not replace endpoint-specific automated-retrieval governance. A new
source identity is therefore recommended, but remains `REVIEW_REQUIRED` and
unallocated in production.

The exact official release is independently visible in the RBA's indexed
publication result: cash rate target `4.60%`, increase `25` basis points, and a
unanimous decision. Rationale remains issuer-attributed. The single direct
linked-page request was not captured correctly by the local output pipeline
(`python` was unavailable); status, content type, resolved URL and page
transport hash were not retained. It was not retried. Because the candidate
builder requires both transport hashes and a validated linked response, **no
real result candidate is retained**. This is a deliberate fail-closed outcome,
not a claim that the feed lacked the item or that the RBA source failed.

The offline parser and candidate builder are exercised against source-shaped
RSS/HTML fixtures, including the 11 August unchanged decision. Those tests
prove the bounded code path, not the live T3→T4 transaction. The proposed
route, exact match rules, request budget and human review questions are in
`data/monitor/STEP15B_RBA_DECISION_PUBLICATION_ROUTE_REVIEW_PENDING.json`.

No Canonical completion, Live observation, Analysis, Forecast resolution,
Outcome, public projection, or monitor activation occurred. The November RBA
Forecast remains frozen and unchanged; a later public UX tranche should make
its 26 September vintage visible if an intervening governed decision changes
the starting rate.
