# WORLD SIGNALS — Analysis population readiness Q audit v0.1

**Base main:** `444d0345446ce3852bca90f488ae187581163ace`  
**Base canonical:** v0.28 / 674 occurrences  
**Base source registry:** v1.70 / 233 sources  
**Base monitor expectations:** v0.8 / 7 configured live routes  
**Reference date:** 2026-09-06

## Purpose

Analysis Foundation P established an executable analytical contract with one completed Australian GDP release. Q stress-tests that contract before broader population.

The Charter requires WORLD SIGNALS to distinguish what happened, what was expected, what surprised, what moved, what appears connected, what may be noise, alternative explanations, second-order effects and falsifiers. It also requires genuinely international coverage rather than allowing US/European or market-data availability to shape the system by default.

Q therefore asks two separate questions:

1. Can the P contract handle a materially different completed event type without forcing it into a macro-data-release template?
2. Does the current canonical registry contain enough completed anchors to support geographically diverse post-event analysis honestly?

This is an audit-and-stress-test tranche, not bulk analytical population.

## Canonical anchor discovery

Temporary read-only registry probes were run from the exact post-PR #45 main checkpoint.

### Probe 1 — completed non-data-release events

Run `33971975178` searched 2026 completed non-data-release occurrences across Africa, South Asia, Southeast Asia, Latin America, East Asia, Oceania / Pacific and cross-regional/global coverage.

It returned only two qualifying records:

- `WSO-8df73c7804d45880` — Reserve Bank of New Zealand OCR decision, 2 September 2026;
- `WSO-COM-A-0013` — US EIA Weekly Petroleum Status Report, cross-regional/global oil-market information release.

The RBNZ occurrence is a useful event-type stress specimen because it is a canonical `DECISION`, not a `DATA_RELEASE`.

### Probe 2 — completed Global South data releases

Run `33972025326` searched completed 2026 data releases across the project’s Global South focus regions and jurisdictions, including India, Indonesia, Brazil, South Africa, Mexico, Nigeria, Kenya, Vietnam, the Philippines, Malaysia, Thailand, Argentina, Colombia and Chile.

Result: **zero candidates**.

The workflow intentionally exited non-zero because the probe was written to fail when no candidate existed. The failure therefore records absence; it is not a repository or validation failure.

### Probe 3 — elapsed Global South records still marked PLANNED

Run `33972061870` tested an alternative explanation: perhaps suitable events existed but lifecycle maintenance had lagged, leaving past-dated 2026 occurrences as `PLANNED`.

Result: **zero candidates**.

That rules out a simple stale-lifecycle explanation for the searched scope. Q therefore treats the problem as a canonical historical-anchor/population gap, not as permission to infer `COMPLETED` from elapsed time.

## Population-readiness contract

Analysis schema v0.2 introduces an explicit readiness policy:

- reviewed post-event analysis requires canonical lifecycle `COMPLETED`;
- elapsed clock time never implies completion;
- a missing historical anchor never authorises a synthetic canonical occurrence;
- Africa, South Asia, Southeast Asia and Latin America are explicit geographic stress regions;
- at least two reviewed event types are required before broad population can be considered, but meeting the event-type target does not override geographic anchor gaps.

The readiness calculation is descriptive only. It has no canonical-population authority.

## Exact readiness state at Q

Full validation run `33972620952` built the public analytical projection and printed the readiness object from the live 674-record canonical checkpoint.

### Eligible completed canonical anchors

**5 occurrences total**:

By region:

- Oceania / Pacific: 2
- North America: 1
- Europe: 1
- Cross-regional / Global: 1

By event type:

- `DECISION`: 2
- `DATA_RELEASE`: 1
- `INFORMATION_RELEASE`: 1
- `TECHNOLOGY_POLICY_MILESTONE`: 1

### Reviewed sample coverage after Q

**2 reviewed samples**:

- `WSO-MAC-A-0025` — Australian Bureau of Statistics GDP release — `DATA_RELEASE`;
- `WSO-8df73c7804d45880` — Reserve Bank of New Zealand OCR decision — `DECISION`.

Reviewed event-type diversity is therefore **2**, meeting the schema’s minimum event-type stress target.

Both reviewed samples are still in Oceania / Pacific. This is not geographically diverse analytical coverage.

### Priority-region anchor state

At this checkpoint:

- Africa: 0 completed anchors — `NO_COMPLETED_CANONICAL_ANCHOR`
- South Asia: 0 — `NO_COMPLETED_CANONICAL_ANCHOR`
- Southeast Asia: 0 — `NO_COMPLETED_CANONICAL_ANCHOR`
- Latin America: 0 — `NO_COMPLETED_CANONICAL_ANCHOR`

The resulting broad-population state is:

**`BLOCKED_NO_PRIORITY_REGION_COMPLETED_ANCHOR`**

This is an upstream canonical-population constraint. It must not be repaired inside Analysis by manufacturing historical events or silently promoting elapsed occurrences to completed state.

## RBNZ decision stress specimen

Canonical anchor:

- occurrence: `WSO-8df73c7804d45880`
- series: `WS.CB.RBNZ.OCR_DECISION`
- institution: Reserve Bank of New Zealand
- event type: `DECISION`
- lifecycle: `COMPLETED`
- release: `2026-09-02T14:00:00` New Zealand local time / `2026-09-02T02:00:00Z`

### Analytical evidence

Q adds three analytical-evidence records, all with `canonical_provenance_effect = NONE`:

1. Reserve Bank of New Zealand — **“OCR increased by 25 basis points to 2.75%”**  
   https://www.rbnz.govt.nz/news-and-events/news/2026/09/ocr-increased-by-25-basis-points-to-2-75

   Used as primary official outcome evidence for the consensus 25-basis-point increase to 2.75 percent and the Committee’s statement that the future OCR path was not pre-determined.

2. The Business Times — **“New Zealand central bank raises rates by 25 bps, flags gradual tightening path”**  
   https://www.businesstimes.com.sg/companies-markets/banking-finance/new-zealand-central-bank-raises-rates-25-bps-flags-gradual-tightening-path

   Used only for the reported pre-decision Reuters poll benchmark: 27 of 31 economists expected a 25-basis-point increase to 2.75 percent.

3. Reuters, syndicated by Business Recorder — **“NZ dollar skids as RBNZ flags gradual hikes, Aussie supported”**  
   https://www.brecorder.com/news/amp/40437554

   Used as analytical evidence for the market-pricing comparison, reported short-rate and FX response, and competing global bond/oil context. The syndication page is not treated as canonical RBNZ provenance.

### What happened

The RBNZ increased the OCR by 25 basis points to 2.75 percent by consensus.

### What was expected

The headline move was widely expected: the cited Reuters poll had 27 of 31 economists forecasting the 25-basis-point increase.

### What surprised

The packet is classified `MIXED` rather than forcing a headline numeric surprise.

- headline policy action: matched consensus;
- forward path: Reuters reported the RBNZ path as more gradual and limited than market pricing, with an OCR projection of 2.81 percent by December 2026 and 3.15 percent at end-2027 versus market pricing for a faster path and a peak around 3.5 percent.

Q therefore adds a controlled `QUALITATIVE` comparison type. Guidance/path surprise and headline decision surprise remain distinct dimensions.

### What moved

Reuters reported:

- New Zealand two-year swaps down 3 basis points to 3.7001 percent;
- New Zealand dollar down 0.7 percent to US$0.5893.

The source reports a change and an endpoint, not a defensible exact pre-value. Q therefore introduces `CHANGE_AND_ENDPOINT` with `SOURCE_REPORTED_CHANGE_AND_ENDPOINT` precision.

`before_value` remains `null` for both movements. The validator rejects inserting a synthetic pre-value unless an independently reconstructed exact series is used.

### What appears connected

- interaction type: `TRANSMISSION_CHANNEL`
- causal status: `OBSERVED_ASSOCIATION`
- confidence: `MEDIUM`

The short-rate and FX response is directionally consistent with a less aggressive forward OCR path than markets had priced. This remains an observed association, not an exclusive causal claim.

### What may be noise / alternatives

Reuters simultaneously reported a global bond sell-off associated with renewed Gulf fighting, higher oil prices and inflation concerns. Longer New Zealand yields were rising in that global move.

The packet therefore refuses to treat the full New Zealand rates session as a clean RBNZ-only experiment. It also notes that the New Zealand dollar had already weakened overnight, so the same-session currency decline cannot be assigned wholly to the decision without higher-frequency reconstruction.

### Second-order effects

`NOT_ESTABLISHED`.

The forward OCR path is guidance, not proof of later mortgage, growth, political or capital-flow outcomes.

## Contract repairs exposed by the stress test

Q generalises three assumptions inherited from the first GDP specimen:

1. **Surprise is not necessarily a single number.** A decision may match consensus while guidance, path, composition or language is surprising.
2. **Source-reported market movements need not contain a pre-value.** `CHANGE_AND_ENDPOINT` preserves what the source actually reports instead of algebraically manufacturing a baseline.
3. **The browser must be event-generic.** Review headings now come from canonical context; the public surface no longer hard-codes Australian GDP.

The public projection also attaches a read-only canonical context object to each review and publishes the readiness audit alongside the reviewed packets.

## Validation

Full Q branch validation run `33972620952`: **SUCCESS**.

- protected upstream state identity: PASS;
- canonical validator: PASS for 674 occurrences;
- analytical validator: PASS for 2 reviews / 5 evidence records;
- full repository suite: **385 tests PASS, 14 skipped**;
- Python compile checks: PASS;
- all browser JavaScript syntax checks: PASS;
- static build: PASS for 674 events / 7 monitor routes / 233 governed sources / 2 analytical reviews;
- generated Q analytical projection assertions: PASS;
- readiness output: `BLOCKED_NO_PRIORITY_REGION_COMPLETED_ANCHOR`.

An earlier full-gate run `33972543879` reached successful protected-state and analytical validation but stopped on one test-helper naming collision (`self.canonical` dict versus a helper named `canonical`). That defect was confined to the new regression test; it was repaired before the successful full rerun.

## Protected state

Q does not modify:

- `data/canonical/registry.json`
- `data/canonical/schema.json`
- `data/sources/registry.json`
- `data/monitor/expectations.json`
- `data/monitor/operations_policy.json`
- `data/changes/ledger.json`
- `data/coverage/biosecurity_overlay.json`

Canonical remains v0.28 / 674. Sources remain v1.70 / 233. Monitor expectations remain v0.8 / 7 routes.

Automatic canonical commit remains OFF. Google Calendar writes remain OFF.

## Next architectural implication

Q does **not** recommend bulk-populating more Oceania/North America/Europe analysis simply because those anchors are available.

The next analytical expansion should follow a controlled upstream historical-anchor tranche for at least one priority region, using authoritative occurrence evidence and normal canonical provenance/change discipline. Only after that canonical work should a Global South analytical specimen be admitted.
