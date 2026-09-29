# Step 15B — RBA decision-publication route candidate

Status: `REVIEW_PENDING`; candidate only. The artifact is retained under
`data/audit/`, not `data/monitor/`, because the current protected-input
validator fingerprints that entire production directory. No production
source or monitor route is allocated or activated.

The proposed source identity is separate from `WSSRC-CB-002`. That source and
`RBA_MPB_CALENDAR` are schedule-specific: they retain the
`RBA_MPB_AUTHORITATIVE_SCHEDULE_CHANGE_SENTINEL` role,
`NO_COMPLETION_INFERENCE`, and `automatic_commit_allowed: false`. The existing
`WSSRC-FIN-001` RBA FSR RSS source is a separate publication precedent, not
blanket authority for this media-release feed.

The RBA RSS directory says its Media Releases feed includes Monetary Policy
Decision statements. The RSS Q&A describes feed-reader/software use and notes
WAF protection. Robots policy does not disallow `/rss/` or `/media-releases/`.
The current endpoint responded `200 text/xml` and contained the exact 29
September 2026 decision item linked to the official release. These facts make
the endpoint a credible candidate for a bounded machine-consumption route;
they do not complete WORLD SIGNALS' endpoint-specific source-governance review
or constitute legal advice.

The candidate request design is limited to a robots check, a decision-window
feed check, and no more than one official linked-page request after unique
classification and matching. No archive crawl, guessed URL, broad RBA news
monitoring, automatic Canonical completion, or downstream promotion is
permitted. HTTP 403/429, WAF response, source unavailability, malformed feed,
or an unexpected title is source-health/review-only—not evidence about the
event.

The Step 15B feed check found the exact RSS item at `2026-09-29T14:30:00+10:00`.
The one permitted linked-page request did not yield locally captured response
metadata because the shell body-processing command used unavailable `python`.
It was not retried. Although the official RBA indexed page independently
confirms the result, no transport hash or successful parser-bound page capture
was retained. Accordingly, **no real result candidate was generated**. The
offline parser/candidate builder is tested with source-shaped fixtures, but
that does not substitute for a successful real T3→T4 run.

Human review must separately decide endpoint rights/operations, route cadence,
the exact Canonical match, the extracted result, any Canonical lifecycle
transaction, any bounded Live fact, and public eligibility. Public eligibility
is not authorised here.
