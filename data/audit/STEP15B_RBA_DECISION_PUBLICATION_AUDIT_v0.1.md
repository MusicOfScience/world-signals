# Step 15B — “The Bank Has Spoken” audit

**Result: T3 and T4 proven for one bounded live run; candidate remains
`REVIEW_PENDING`.** This is a candidate-only tranche. The schedule monitor
remains unchanged and no production, downstream, or public state was modified.

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

The initial Step 15B attempt is retained as historical context: it failed to
capture linked-page metadata and generated no candidate. In the single
Step 15B.1 corrective run, the committed read-only probe completed one robots,
one RSS and one linked-page request. RSS returned `200 text/xml`, 2,093 bytes;
the linked release returned `200 text/html; charset=UTF-8`, exactly 27,651
bytes, at the requested and resolved URL, with no redirect. Their transport
SHA-256 values are retained in the audit JSON and candidate artifact. The probe
detected the result at `2026-09-29T11:17:08.765213Z` and generated
`WSOUTCAND-AU-RBA-MPB-20260929-001`, status `REVIEW_PENDING`, fingerprint
`a42a8c260d1a9e1e0d2f22b5a3d3e8ce1188f4f3a260a07235224d01ff571d81`.

The candidate binds to `WSO-d2a7c4e4416b505b` and records target `4.60%`,
`INCREASE`, `+25` basis points, unanimity `true`, date `2026-09-29`, and
`ISSUER_STATED_RATIONALE`. Full response payload copies were not persisted; the
probe retained exact byte lengths and transport hashes while parsing them in
memory. No second request was made. The semantic fingerprint was rechecked
from the emitted semantic content; byte-for-byte offline reparsing of retained
payload files is not claimed.

The offline parser and candidate builder are exercised against source-shaped
RSS/HTML fixtures, including the 11 August unchanged decision. The live probe
now proves the actual T3→T4 candidate path once. The proposed route, exact
match rules, request budget and human review questions are in
`data/audit/STEP15B_RBA_DECISION_PUBLICATION_ROUTE_REVIEW_PENDING.json`.

No Canonical completion, Live observation, Analysis, Forecast resolution,
Outcome, public projection, or monitor activation occurred. The November RBA
Forecast remains frozen and unchanged; a later public UX tranche should make
its 26 September vintage visible if an intervening governed decision changes
the starting rate.
