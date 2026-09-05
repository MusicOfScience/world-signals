# WORLD SIGNALS — Core monitor expansion O research v0.1

**Research date:** 2026-09-05  
**Base main:** `03b6255cdc121062816b39073e3c88dd049db29c`  
**Base canonical registry:** v0.28 / 674  
**Base source registry:** v1.69 / 233  
**Base live monitor expectations:** v0.7 / 6 adapters  
**Canonical mutation authorised:** **NO**

## Decision

Promote the UK Office for National Statistics release calendar as the seventh read-only live monitor route, while placing Eurostat's release-calendar automation route on an explicit endpoint-identity hold.

This is deliberately asymmetric. Both sources have prior automated-monitoring clearance, but only ONS currently has a verified production transport identity that can be exercised without broad HTML crawling or invented endpoint semantics.

## ONS — live route approved for review-only monitoring

Source: `WSSRC-MAC-006` — Office for National Statistics.

Prior governance already records:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`;
- `automated_monitoring_use = CLEARED`;
- `verification_mode = AUTOMATED_PILOT`;
- official release-calendar/feed routes;
- controlled failure-injection evidence;
- 19 canonical dependencies.

Current ONS terms state that most website content is available under the Open Government Licence and that ONS makes website content available through feeds for other websites and applications. The official release calendar exposes RSS and calendar links.

### Live transport verification

The official upcoming RSS route resolves successfully as `application/rss+xml`:

`https://www.ons.gov.uk/releasecalendar?highlight=true&limit=100&page=1&release-type=type-upcoming&rss=&sort=date-newest`

The route is paginated. Research run `33969711355` fetched four pages and terminated on the short fourth page:

- page 1: 100 items;
- page 2: 100 items;
- page 3: 100 items;
- page 4: 43 items;
- total upcoming feed items: 343.

The adapter must therefore paginate to exhaustion inside a hard safety bound. Reaching the bound without a short page is a source-health failure, not evidence about any event.

### RSS semantic boundary

Observed RSS 2.0 item fields are:

- `title`;
- `link`;
- `guid`;
- `pubDate`;
- `description`.

`pubDate` carries a timezone and can be normalised to UTC. For example, the ONS July 2026 monthly GDP release appears as `Fri, 11 Sep 2026 06:00:00 +0000`, corresponding to the canonical 07:00 Europe/London publication time.

The RSS feed does **not** carry the online release calendar's `Confirmed` / `Provisional` label. The live route therefore has no authority to change canonical certainty status from RSS alone.

### Exact canonical identity verification

The 19 existing ONS canonical occurrences were matched using explicit per-occurrence feed titles, not fuzzy search. Research run `33969711355` returned exactly one current RSS item for every tracked occurrence and exact UTC agreement for all 19.

Tracked families:

- UK consumer price inflation — five occurrences;
- UK Labour Market — five occurrences;
- quarterly GDP — three occurrences;
- monthly GDP — two occurrences;
- Index of Production — two occurrences;
- UK Trade — two occurrences.

The route must retain these exact identities in monitor expectations. A missing or multiply-matched title is a **source-match review condition**, never an event cancellation/completion inference.

### Change policy

Positive exact RSS identity + changed datetime:

1. generate a review candidate;
2. preserve automatic canonical commit = false;
3. require verification against the official ONS HTML release calendar or item page, including Confirmed/Provisional status;
4. only a later reviewed transaction may update canonical timing.

No change:

- record a no-change observation.

Tracked title absent or renamed:

- generate source-match review evidence;
- event-state inference = none.

Occurrence already elapsed:

- do not presence-check against the upcoming-only feed;
- do not infer completion/cancellation from absence.

Source fetch/parse/pagination failure:

- mark source health degraded;
- canonical action = none.

## Eurostat — permission remains cleared, endpoint identity held

Source: `WSSRC-MAC-005` — Eurostat.

Prior governance correctly established that Eurostat explicitly offers an internet-calendar subscription which automatically receives release-calendar updates. Automated-monitoring permission remains `CLEARED`, bounded to the official subscription/feed mechanism.

However, the source registry currently labels this URL as an ICS endpoint:

`https://ec.europa.eu/eurostat/en/news/release-calendar`

Current verification shows that URL resolves as ordinary HTML, not `text/calendar`. Eurostat's current subscription instructions state that users can generate/copy a `.ics` calendar URL, but this research pass did not recover a stable authoritative generated feed URL suitable for a production adapter.

Therefore this transaction must **not**:

- pretend the HTML release calendar is ICS;
- silently replace the intended subscription route with HTML scraping;
- downgrade the previously established reuse/automation permission finding merely because endpoint discovery is incomplete.

Instead:

- repair the misclassified endpoint to an HTML subscription/release-calendar landing route;
- make it non-preferred for automated monitoring;
- set an explicit generated-ICS-endpoint rediscovery hold;
- keep `automated_monitoring_use = CLEARED` as a permission fact;
- do not add Eurostat to live monitor expectations.

This preserves the separation between **permission** and **operational endpoint readiness**.

## Bias note

ONS is a UK/European source and does not improve geographic coverage. It is selected because it is the strongest currently verified monitor-readiness candidate: explicit feed permission, a real official RSS transport, 19 existing canonical dependencies, prior fault-containment work, and a live 19/19 identity/no-change baseline.

This should not become a new Western-default population rule. The next monitor-research cohort should prefer Australia/Asia/Pacific or Global South routes when governance and endpoint maturity are comparable.

## Invariants

This work must leave unchanged:

- canonical registry v0.28 / 674 and its bytes;
- canonical schema;
- change ledger;
- biosecurity overlay;
- Google Calendar write policy;
- automatic canonical commit policy.

The live monitor remains a Source/Change Monitor layer producing observations and review candidates only.
