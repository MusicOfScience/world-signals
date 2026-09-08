# WORLD SIGNALS — BT research note

## Purpose

Select the next production-monitor tranche after BS without treating the remaining South Asia production-route gap as a quota. The governing question is whether an existing authoritative schedule source can remain held while a distinct, explicitly published first-party machine interface provides bounded review-only publication monitoring.

Exact BT base: `2b74c10905760c98c75b3598df96441f99841b00` (post-BS main).

## Pressure context

After BS, South Asia remained the only WORLD SIGNALS region with no configured production-monitor route. That is pressure evidence, not a requirement to activate a South Asian source. India MoSPI had already been investigated and remained correctly held: its current calendar surfaces disagree, its conventional robots endpoint did not establish policy, and no documented release-calendar machine interface had been identified. BT therefore did not mechanically retry MoSPI.

## Candidate comparison

### Reserve Bank of India

RBI publishes an official RSS page which expressly presents RSS as a way to receive automatic site updates. That page links a Press Releases RSS endpoint at `https://rbi.org.in/pressreleases_rss.xml`.

The first BT resolver failed closed because the documentation page contains two anchors labelled `Press Releases`: one normal press-release page and one RSS link. No endpoint inference was made. The revised resolver selected only the documented HTTPS RBI-hosted `/pressreleases_rss.xml` target.

Successful RBI read-only diagnostic:

- run `34217974010`
- job `102034145142`
- documentation: HTTP 200 HTML
- RSS: HTTP 200 `text/xml`
- 10 rolling items
- every item had a link and `pubDate`
- two requests total
- zero repository writes

The feed was operationally sound but broad: current items included state-government-securities auction results, banking directions, reverse-repo operations and money-market operations. More importantly, WORLD SIGNALS' two remaining 2026 RBI Canonical records are multi-day MPC meeting windows, not separately modelled decision-publication occurrences. A broad press feed could therefore be made useful only with a more inferential classifier and careful meeting-window semantics. RBI remains a valid future readiness candidate, but it is not the cleanest BT activation.

### Central Bank of Sri Lanka

CBSL's existing `WSSRC-REGJ-002` remains authoritative for the 2026 Monetary Policy Board advance release calendar. It explicitly distinguishes MPB meeting dates from public monetary-policy announcement dates. Its existing rights/automation hold remains unchanged.

CBSL separately publishes an official `RSS Feeds` page containing a dedicated `Monetary Policy Review` feed. This is a source-role split rather than a clearance of the held schedule page.

Successful CBSL read-only diagnostics:

- feed-contract run `34218166410`, job `102034765821`
- item-metadata run `34218262645`, job `102035077150`
- documentation: HTTP 200 HTML
- MPR RSS: HTTP 200 `application/rss+xml; charset=utf-8`
- 10 rolling items
- exactly two requests per diagnostic (documentation + RSS)
- zero item-link requests
- zero repository writes

The feed is deliberately minimal. Every item contained only:

- `title`
- `link`
- `source`

There is no `pubDate`, `guid`, namespaced date or publication clock. BT therefore must not invent a publication timestamp.

However, each official linked PDF filename carries a civil date and review identity. Examples observed in the live feed were:

- `press_20260128_Monetary_Policy_Review_No_1_2026_...pdf`
- `press_20260325_Monetary_Policy_Review_No_2_2026_...pdf`
- `press_20260526_Monetary_Policy_Review_No_3_2026_...pdf`
- `press_20260722_Monetary_Policy_Review_No_4_2026_...pdf`

CBSL's authoritative 2026 advance-release calendar independently gives the corresponding announcement dates as 28 January, 25 March, 26 May and 22 July. It gives the remaining two announcements as:

- Review 5: meeting 29 September 2026; announcement 30 September 2026
- Review 6: meeting 19 November 2026; announcement 20 November 2026

The public Monetary Policy tracker also identifies those future occurrences as `2026/05` and `2026/06` and preserves the meeting/announcement distinction.

## BT selection

CBSL is selected over RBI for BT because the machine interface is both first-party and topic-specific, while the Canonical events are already the public announcement occurrences represented by that feed family.

The production matching contract is intentionally stricter than simple title matching:

1. one request to the dedicated MPR RSS feed;
2. no automatic request to RSS documentation, schedule HTML, article pages or linked PDFs;
3. title must structurally identify `Monetary Policy Review - No. N of YYYY`;
4. official CBSL PDF link filename must structurally identify the same review number and year and contain `press_YYYYMMDD_...`;
5. review number, year and filename civil date must exactly equal one explicitly configured Canonical occurrence mapping;
6. a positive match creates a review candidate only;
7. duplicate, inconsistent or ambiguous identity fails closed;
8. feed absence has no cancellation, delay, completion, certainty or schedule semantics.

The filename date is identity metadata from the official feed link. It is not a clock time and does not authorize a Canonical precision upgrade. No automatic `COMPLETED` is permitted.

## Rights and automation separation

CBSL's website states `All Rights Reserved`. BT therefore does not claim a broad content-reuse or redistribution licence.

The machine-access conclusion is narrower: CBSL itself publishes an RSS Feeds page and a dedicated Monetary Policy Review RSS endpoint. WORLD SIGNALS may make a bounded request to that expressly supplied machine interface for internal review-oriented metadata monitoring. This does not imply permission to crawl the held schedule source, automatically fetch linked PDFs, republish PDF/article content or clear other CBSL endpoints.

Thus:

- content/reuse rights: conservative; minimal factual metadata only;
- RSS automated endpoint access: cleared for this specific published feed;
- schedule-page automated access: still held;
- technical reachability: separately validated by the read-only GitHub Actions diagnostics.

## Governed outcome proposed

BT should add:

- monitor-only source `WSSRC-REGJ-007`;
- route `CBSL_MONETARY_POLICY_RSS`;
- exactly two existing Canonical occurrence links (`WSO-REG-J-0006`, `WSO-REG-J-0007`).

Expected governed state:

- Canonical Registry: `v0.41 / 689` unchanged;
- Sources: `v1.92 / 250` → `v1.93 / 251`;
- Monitor expectations: `v0.17 / 15` → `v0.18 / 16`;
- Change Ledger unchanged;
- Live Intelligence unchanged;
- Analysis unchanged;
- automatic Canonical commit OFF;
- Google Calendar writes OFF.

If implementation or preflight cannot preserve these constraints, BT should remain a readiness tranche rather than force activation.
