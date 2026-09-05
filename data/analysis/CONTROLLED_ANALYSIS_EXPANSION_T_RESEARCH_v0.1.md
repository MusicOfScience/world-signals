# WORLD SIGNALS — Controlled Analysis Expansion T research v0.1

**Base main:** `33826d046cc7b966cf8e77fe4fbb7debb6a50278`  
**Canonical checkpoint:** v0.29 / 678 occurrences  
**Analysis pre-state:** reviews v0.3 / 6; evidence v0.3 / 14  
**Reference date:** 2026-09-06

## Purpose

Tranche S moved the analytical layer to `READY_FOR_CONTROLLED_EXPANSION`. T does not interpret that state as permission to populate every remaining completed occurrence. It selects only unreviewed completed anchors that add material domain or analytical-contract pressure.

A read-only registry probe on the exact post-PR #48 main found three unreviewed `COMPLETED` anchors:

1. `WSO-ddb70f8ff05a58fb` — Bank of Canada rate decision — North America — `DECISION`;
2. `WSO-COM-A-0013` — EIA Weekly Petroleum Status Report — Cross-regional / Global — `INFORMATION_RELEASE`;
3. `WSO-TECH-A-0002` — EU Chips Act first statutory evaluation/review report due — Europe — `TECHNOLOGY_POLICY_MILESTONE`.

T admits the EIA and EU Chips Act records only. The Bank of Canada occurrence is valid but intentionally left unreviewed because RBNZ, Bank Indonesia and the Central Bank of Egypt already exercise monetary-policy decision analysis. Closing a backlog is not itself an analytical objective.

## Specimen 1 — EIA Weekly Petroleum Status Report, 2 September 2026

Canonical occurrence: `WSO-COM-A-0013`.

### Primary official outcome evidence

U.S. Energy Information Administration — Weekly Petroleum Status Report / weekly stocks data:

- https://www.eia.gov/petroleum/supply/weekly/index.php
- https://www.eia.gov/dnav/pet/pet_stoc_wstk_dcu_nus_w.htm

The official tables carry a 2 September 2026 release date for data through 28 August. Commercial crude stocks moved from 428.910 million barrels on 21 August to 424.460 million on 28 August, a 4.450 million-barrel draw. U.S. distillate stocks moved from 103.391 million to 104.187 million barrels, a 0.796 million-barrel build.

### Expectations and market observation

Reuters, 2 September 2026, distributed via BOE Report:

https://boereport.com/2026/09/02/us-crude-stocks-fall-on-strong-refining-activity-and-exports-eia-says/

Reuters reported a poll expectation for a 1.1 million-barrel crude draw and a 1.3 million-barrel distillate draw. The actual release was therefore internally mixed: crude drew much more than expected, while distillates built instead of drawing. Reuters also reported that oil prices were up slightly after the report, with Brent up $0.68 to $95.33 and WTI up $0.35 to $90.57 at 11:01 ET.

### Competing context

Reuters, 1 September 2026:

https://www.reuters.com/business/energy/oil-prices-rise-latest-fighting-resurrects-middle-east-supply-disruption-risks-2026-09-01/

Oil had surged more than $4 per barrel the preceding session as renewed US-Iran fighting and Strait of Hormuz disruption risk dominated the market. T therefore treats the post-WPSR price move as a LOW-confidence observed association, not a clean inventory causal experiment.

The 1 September geopolitical-market report is stored as a **separate analytical evidence record** from the 2 September inventory/expectations report. This prevents a true contextual claim from riding on the wrong source lineage.

### Analytical treatment

- surprise: `MIXED`;
- market observations: Brent and WTI `CHANGE_AND_ENDPOINT`, source-reported, no synthetic pre-value;
- connection: `TRANSMISSION_CHANNEL` / `OBSERVED_ASSOCIATION` / LOW;
- alternatives: geopolitical supply risk, mixed product-stock details and pre-existing oil-market momentum;
- second-order effects: `NOT_ESTABLISHED`.

## Specimen 2 — EU Chips Act first evaluation/review

Canonical occurrence: `WSO-TECH-A-0002`.

This occurrence is a statutory deadline object. Its canonical `start_local` remains 20 September 2026, but that is the legal latest date — not an asserted publication date. The canonical record separately carries:

- `completion_verified_by_date = 2026-06-03`;
- `deadline_completion_relation = COMPLETED_BEFORE_DEADLINE`;
- `deadline_is_actual_publication_time = false`.

The change ledger explicitly records `LIFECYCLE_COMPLETED_BEFORE_STATUTORY_DEADLINE`.

### Legal benchmark

Regulation (EU) 2023/1781, Article 40:

https://eur-lex.europa.eu/eli/reg/2023/1781/oj/eng

Article 40 requires the Commission to submit the first evaluation/review report to Parliament and Council **by 20 September 2026** and make it public.

### Prior official timetable

European Commission annual plan on evaluations and fitness checks:

https://commission.europa.eu/document/download/05d3777d-5d73-456d-bf56-38caa77d53c8_en?filename=2025-CWP_0.pdf

The plan listed the Evaluation of the Chips Act with an indicative adoption time of **Q1 2026**. `Indicative` must remain indicative; it is not an exact promised publication date.

### Completion evidence

European Commission / EUR-Lex, 3 June 2026:

- SWD(2026) 504 final — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52026SC0504
- COM(2026) 504 final — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2026:504:FIN

The impact-assessment package includes the Evaluation of the Chips Act as an annex. The Commission proposal states that, in accordance with Article 40, the first evaluation/review report had been submitted; it summarises the evaluation and uses it as part of the evidence base for Chips Act 2.0.

### Analytical treatment

The timing result has two distinct benchmarks:

- the indicative Q1 2026 Commission planning window was not met;
- the statutory 20 September 2026 latest date was comfortably met.

T therefore uses `MIXED` with qualitative comparisons rather than calling early statutory compliance an unqualified positive surprise.

No market move is promoted (`what_moved: []`). This is deliberate: the event is intrinsically important industrial/technology policy even if no discrete asset-price response can be isolated or is analytically necessary.

The explicit documentary relationship between the evaluation and the Chips Act 2.0 proposal is represented as `POLICY_RESPONSE_CONTEXT` with `NOT_A_CAUSAL_CLAIM`. The evaluation is one input among impact assessment, consultation, geopolitical, industrial and technological considerations.

## Why Bank of Canada is held back

The 2 September Bank of Canada decision is a legitimate completed canonical occurrence. Official and Reuters evidence is adequate for a review: the Bank held at 2.25%, the hold was expected, guidance was interpreted as more hawkish, and Canadian rates/currency repriced.

T nevertheless does not admit it because the current reviewed set already contains several central-bank decision/process cases. Adding another would improve completion percentage while adding less domain diversity than EIA or EU semiconductor policy.

This hold is not a negative judgement on the event's importance and does not change canonical state.

## Proposed post-state

If both specimens validate:

- canonical: v0.29 / 678 — unchanged;
- Analysis reviews: v0.4 / 8;
- Analysis evidence: v0.4 / **21**;
- eligible completed anchors: 9;
- reviewed anchors: 8;
- reviewed event-type diversity: 7;
- one eligible unreviewed anchor remains: Bank of Canada;
- broad state remains `READY_FOR_CONTROLLED_EXPANSION`.

No canonical, source, monitor, change-ledger, calendar or biosecurity mutation is authorised by T.
