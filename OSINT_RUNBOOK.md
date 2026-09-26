# OSINT Observation & Signal Engine v1

## Purpose

The OSINT engine is a local-first, read-only candidate generator. It helps
answer “what consequential factual development may deserve review?” without
turning retrieval into Canonical truth or a governed analytical Signal.

```text
MONITOR (did a governed surface change?)
  != OSINT CANDIDATE ENGINE (what factual development may deserve review?)
  != LIVE INTELLIGENCE (reviewed immutable Observation)
  != SIGNAL (reviewed analytical inference)
```

## Running one pass

From the repository root:

```bash
python scripts/validate_osint_engine.py
python scripts/run_osint_engine.py --once
```

The engine has no implicit daemon. A local scheduler may invoke `--once` at
the cadences recorded in `data/osint/source_cohort.json`. Runtime output is
written to `.world-signals-runtime/osint/`, which is intentionally ignored by
Git and is not a governed data store. A run records route attempts, HTTP state,
content type, payload hash, source publication timestamps, native IDs, parser
versions, candidate evidence, clustering and review-queue reasons.

## V1 cohort and rights boundary

The cohort contains eight first-party RSS/JSON machine routes covering monetary
policy, macroeconomic releases, sovereign/fiscal publication metadata,
institutional meetings and one bounded public policy API. It was selected from
the Source Registry only where automated monitoring use is explicitly cleared
and the route's retrieval/ingestion fields are not held. `ACTIVE`, official
authority or machine readability alone is not permission. Held, manual-only,
calendar-only, paid/licensed and arbitrary newswire/social routes remain gated.
OPEC quarantine is not touched.

The runner makes at most one request per selected route per pass. It does not
crawl linked pages, follow a calendar into a different endpoint, or republish
source article bodies. Source-native publication time, any effective/occurrence
time, and local retrieval time remain distinct. Unknown times are left unknown.

## Candidate and review boundary

Observation Candidates have stable candidate identities, source lineage,
ultimate-provider fields, timestamps, payload hashes, domain labels and an
explicit candidate state such as `NEW`, `POSSIBLE_CORRECTION` or `CONFLICT`.
Same-provider documents, mirrors and repeated routes are deduplicated while
their route lineage is retained. Independent ultimate providers remain
separate, but source count is never treated as corroboration without review.

Story clusters are operational groupings, not facts. Signal Candidates explain
why a pattern was nominated and expose qualitative persistence/corroboration
states. They do not establish direction, materiality, confidence, causation,
Risk/Regime state or a forecast. Review priority is a work-order label, not a
truth score.

The following actions are closed:

- automatic Canonical mutation;
- automatic promotion to governed Observation or Signal;
- automatic Relationship, Risk, Scenario or Forecast changes;
- mutation of the four 26 September 2026-cutoff Forecast issuances;
- public candidate projection;
- automatic Outcome or Evaluation writes.

A later reviewed OSINT promotion tranche must preserve candidate hashes,
lineage and review decisions in a separate governed transaction. Retrieval
failure, parser failure, an empty feed or a permission hold is source health,
not evidence that an event was cancelled or that nothing happened.

## First reviewed promotion tranche

OSINT v0.13 completed the first bounded end-to-end path. One Federal Reserve
FOMC decision candidate was retrieved successfully from the authorised
`osint-fed-monetary-rss` route, checked against the exact first-party statement,
and admitted as `WSLI-OSINT-FED-FOMC-20260916-001`. The promotion is recorded in
`data/live_intelligence/osint_promotion_transaction_v1.json` with the candidate
ID, RSS payload hash, route, parser/adapter versions, reviewer decision and
pre/post Live-state fingerprints.

The tranche limit is four new observations; only one passed review. The Japan
MOF meeting candidate was not admitted because the authorised route supplied
publication metadata while the page content needed for a fuller factual
observation was outside that route's cleared automated-ingestion scope. No
source permission was broadened. Automatic promotion, Signal promotion and
public observation projection remain closed.

For a later prospective update, retain the existing Forecast issuance, freeze
a new cutoff and create a distinct reviewed issuance only when new evidence
materially changes the estimate. Do not attach post-cutoff OSINT to the four
26 September 2026 Forecast issuances.

## First reviewed Signal disposition

The first OSINT bootstrap run produced 701 Observation Candidates, 605 story
clusters and five Signal Candidates. This was primarily feed-history/bootstrap
discovery: 510 candidates had no publication timestamp and 55 were older than
90 days at audit time. The candidates were therefore treated as review aids,
not as evidence of current-world change.

The route split was China NBS 500, Japan MOF 100, European Council 50, SARB
25, Federal Reserve 15, CBSL 10 and GOV.UK 1; BSP returned source-specific
HTTP 403. Publication-age buckets were 16 within 7 days, 71 within 8–30 days,
49 within 31–90 days, 55 older than 90 days and 510 unknown. Story clustering
left 571 singleton clusters, with only a small tail of multi-item clusters.
The run therefore behaved as bootstrap/history discovery mixed with recent
material, not as a clean current-change detector. The audit did not rewrite
runtime history or treat the BSP 403 as evidence of a world-state change.

None of the five machine Signal Candidates was admitted. The Japan MOF and
European Council proposals were retained for later review as one-provider
history/archive material; the China NBS proposal lacked governed support and
time-qualified persistence; the mixed monetary-policy proposal lacked one
bounded proposition and baseline; and the broad cross-domain proposal was
analysis rather than a Signal. These dispositions are retained in
`data/signals/signal_admission_transaction_v1.json`.

One independently reviewed Signal was admitted from the governed Live store,
not from raw candidates: `WSSIG-HEALTH-COD-BVD-BURDEN-202609-001`. It compares
two dated WHO snapshots of the DRC Bundibugyo outbreak. The records share WHO
ultimate origin, so corroboration is explicitly `PARTIAL`, confidence is
`LOW`, and no causal, risk, scenario or forecast claim is made. Signal
population remains closed by default, the public projection remains closed,
and downstream analytical populations remain empty.

## Current coverage gaps

V1 does not provide real-time market prices/yield curves/OIS, credit stress,
freight/shipping/AIS, maritime security, oil/LNG physical flows, sanctions,
corporate filings, cyber/security advisories, defence/security notices,
reputable newswire or climate/hazard observation coverage. These require
separate rights, endpoint and semantic review. Newswire should later be used
primarily for rapid discovery and corroboration/pointers to primary sources,
not silently treated as ultimate truth.
