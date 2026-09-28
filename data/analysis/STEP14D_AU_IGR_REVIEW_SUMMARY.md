# Step 14D — Australian IGR official projection / assumption audit

Status: **REVIEW_PENDING / CANDIDATE ONLY / INTERNAL_ONLY**.
Write targets: `[]`. Public projection permitted: `false`.
No production Analysis admission, source activation or downstream promotion.

## Reconciliation and identity

Starting main: `e98d54efaedb5a46c13e9417a12e6d3880e0ccb1`.
PR #183 was verified merged/closed at that SHA (2026-09-28T15:59:54Z).
Exact-merge Validate, coverage audit and Pages runs succeeded: `36447796853`,
`36447796876`, `36447796859`. Fresh branch
`codex/igr-projection-assumption-audit` was checked out before any content write.

Canonical occurrence `WSO-FIS-AU-IGR-20260921`, series `WSER-FIS-AU-IGR`, is the
completed **2026 Intergenerational Report**, `INFORMATION_RELEASE` in
`FISCAL_SOVEREIGN_FINANCE`. Publication is the civil date 2026-09-21, not an
invented UTC release instant. The 9 September announcement and repository
discovery at 2026-09-28T14:17:45Z remain unchanged.

`WSSRC-FIS-030` is Australian Treasury technical publication provenance;
`WSSRC-FIS-031` is Treasury Ministers announcement/framing provenance. Both
remain `MANUAL_ONLY_RIGHTS_HOLD`, `PRODUCTION_AUTOMATION_HOLD`, with no monitor
endpoints. This one-off research creates no continuing retrieval permission.

## Contract decision and inspectable package

The native Analysis v0.8 spine validates a publication-only DRAFT POST_EVENT
candidate with empty actuals and benchmarks. It does **not** validate projection
row semantics. Its public projector copies review fields rather than applying
an extension-field allowlist. Admission now would therefore be premature.

Retain an optional `official_projection_review` **contract-extension candidate**,
not a production schema change. The Analysis candidate links four separately
sealed parts rather than embedding a new production observation store:

- `STEP14D_AU_IGR_ANALYSIS_CANDIDATE_REVIEW_PENDING.json`
- `STEP14D_AU_IGR_OFFICIAL_PROJECTION_INVENTORY_REVIEW_PENDING.json`
- `STEP14D_AU_IGR_ASSUMPTION_AUDIT_REVIEW_PENDING.json`
- `STEP14D_AU_IGR_EVIDENCE_MANIFEST_REVIEW_PENDING.json`
- `STEP14D_AU_IGR_CONTRACT_EXTENSION_REVIEW_PENDING.json`

Analysis ID: `WSAN-AU-IGR-20260921-001`. Its factual claim is publication of the
seventh IGR; future values are never `what_happened.actuals`. Surprise and
second-order effects are `NOT_ESTABLISHED`; market movement is `[]`;
connections are `POLICY_RESPONSE_CONTEXT / NOT_A_CAUSAL_CLAIM`. Alternatives
distinguish methodological change from realised savings, cyclicality from
permanent productivity failure, and delayed births from completed-cohort decline.

The reusable candidate contract requires framework, outputs, assumptions,
sensitivities, assumption audit, prior baseline and limitations. `issuer_rationale`
keeps assumption rows usable beyond Treasury. Controlled epistemic classes are
PUBLICATION_FACT, OBSERVED_EVIDENCE, MODEL_ASSUMPTION, OFFICIAL_PROJECTION,
SENSITIVITY_CASE, POLICY_CLAIM and PRIOR_OFFICIAL_PROJECTION. This is not a new
Forecast contract.

## Source manifest and extraction

One-off primary sources: [2026 report bundle](https://treasury.gov.au/publication/2026-intergenerational-report),
[2023 prior report](https://treasury.gov.au/publication/2023-intergenerational-report),
[original 2002 report](https://treasury.gov.au/sites/default/files/2019-03/2002-IGR-report.pdf).
Publication/retrieval times remain separate. Retrieval timestamp
`2026-09-28T16:25:00Z` is an explicitly recorded upper bound after downloads
completed, not a source publication or retrospective system-knowledge timestamp.

| Asset | SHA-256 of retrieved bytes |
|---|---|
| 2026 main PDF | `888662a1b4d49c92e927fc1e591613288e847be581cceafcd510d2098427a1a4` |
| 2026 factsheet PDF | `9bf693f781796e7450d5e5dc59cbcf1e63fd519a0af262ebdf7caed3eb1dfbfd` |
| 2026 chart ZIP | `c4b6362c9cdae2ba24fc6b268a866b38dc8dd5111e5030bb184cc05c028e6ac9` |
| 2023 main PDF | `a8036065cd2dbb7530fb5fd9f7c2cbdabff603e45ed6eab6b025c03b2b84eb69` |
| 2002 original PDF | `eb50b9c6a260364e99bff156850a6a298660ff8580db354540319e6e5513b63f` |
| Treasury Ministers release | `df8285aa0d3386390959a289d9d44deacb605f271502281efe3f8a5ab661c55b` |
| ABS Births 2024 | `9e59cc3e018b73c0eab781b62a97d5320caa5134d63695e5faccb9e363b8385e` |
| ABS Population March 2026 | `bdccf060a436720a38c000f47ccf548d5755edcd6d0778bef88cd6989138ea0c` |
| ABS Labour Force August 2026 | `b475c926bf9e692d081e5e337309553b8267924e148abeeeaf9ab54aa62fe558` |
| PC September productivity update | `a79fa289242036a8baaa80e877bae9cd13203fa627eb814bea89745cee573619` |

Exact URLs, content types, roles, byte counts, vintages and 14 workbook-member
hashes are in the JSON manifest. PDFs/ZIP/HTML are not committed. PDF extraction
was checked against rendered summary/sensitivity tables; chart data was read
without editing the workbooks. For transformed comparisons: based on
Commonwealth of Australia data.

Treasury main/factsheet/charts are one institutional family; 2023/2002 are
model-evolution references, not independent confirmations. Ministerial reform
attribution remains POLICY_CLAIM and cannot override technical extraction.

Independent current-context audit evidence is bounded to
[ABS births](https://www.abs.gov.au/statistics/people/population/births-australia/2024),
[ABS population](https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/mar-2026),
[ABS labour force](https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia/aug-2026)
and [PC productivity](https://www.pc.gov.au/ongoing/productivity-insights/update-september-2026/).
Registered-birth TFR 1.481 is not cohort fertility; annual NOM 292,100 is not a
long-run policy convention; trend participation 67.0% is not annual structural
participation; whole-economy productivity −0.2% over the year to June is not a
40-year falsification. PC derives its statistics from ABS: two institutions do
not create two independent statistical confirmations. The PC page's hours-growth
prose/graphic discrepancy (2.3%/2.4%) is retained, not silently resolved.

## Projection inventory

25 outputs, 15 model assumptions, eight sensitivity cases, five observed-context
rows, six transition classifications. Terminal outputs are conditional 2065–66
values unless a different horizon is explicit. Selected exact Treasury examples:

| Metric | Official projection |
|---|---|
| Population / working-age population | 39.3m / 24.3m |
| Dependency ratio | 40.2 aged 65+ per 100 aged 15–64 |
| Period life expectancy, male / female | 86.1 / 89.5 years |
| Real GDP growth / real GDP per person | 1.6% / $157,300 in report real-price convention |
| Real GNI per person | $149,500 in report real-price convention |
| Participation, age 15+ | 64.7% |
| Average weekly hours per employed person | 30.6 hours |
| Underlying cash balance / gross debt / net debt | −1.8% / 27.4% / 18.1% GDP |
| Receipts / payments / interest | 25.9% / 27.7% / 1.2% GDP |
| Health / aged care / Commonwealth NDIS | 6.2% / 2.3% / 1.5% GDP |
| Defence / Age and Service Pensions / super concessions | 2.5% / 1.8% / 2.7% GDP |

Exact row locators: A2.1–A2.3 pp297–299, hours p177, receipts p214, interest
p223, super concessions p246. Economy-size language remains a bounded “more
than twice” statement, not an invented multiplier. Employment is not inferred
from labour-force size. Real-dollar levels are not independently rebased.

Fertility 1.34, NOM 235,000/year, productivity 1.2% growth and inflation 2.5%
are **inputs**, not observed outcomes. The 24.2%-GDP tax cap from 2032–33 is
a maintained policy convention involving future bracket-creep offsets, not a
legislated perpetual limit. Assumption types populated: demographic, migration,
participation, productivity, inflation, interest-rate, fiscal-policy, health-cost,
care-cost, AI-structural, energy-transition and other-model assumptions.

## Ten-axis standing audit

Every one of the 15 assumptions has all ten qualitative axes, source locators
and limitations. No assumption/model quality score or aggregate Treasury verdict.

1. Historical plausibility: retain original assumptions and methods, not later
   revisions masquerading as original expectations.
2. Current trajectory: use bounded observed series with period/definition caveats;
   explicitly unresolved where no independent panel was extracted.
3. Structural break: consider changed technology, cohorts, markets and institutions
   without assigning unsupported probabilities.
4. Implementation dependency: separate laws, delivery, funding and future policy
   maintenance from announcements or model premises.
5. Circularity/endogeneity: identify documented fiscal/debt feedback; do not claim
   every plausible behavioural feedback is actually modelled.
6. Sensitivity: preserve Treasury shocks, units, combined-input cases and horizons;
   no invented elasticity or unauthorised combination of shocks.
7. Downside alternative: documented lower cases, or explicitly unquantified
   mechanisms where no credible numeric stress is supplied.
8. Upside alternative: documented higher cases, not guaranteed benefits.
9. Signposts: comparable future observations that inform the premise, not new
   admitted Scenario signposts.
10. Revision conditions: sustained material divergence, revised methods or enacted
    policy changes; one cyclical release is not a long-run falsifier.

Specific candidate findings:

- **Productivity:** 1.2% convergence is not established by the current −0.2%
  measurement. ±0.4ppt sensitivity gives $136,600/$181,000 GDP per person and
  55.9%/2.4% gross debt. Capital deepening, services measurement and diffusion
  matter; sustained underlying divergence prompts review.
- **Demography:** cohort/period fertility and longevity are distinct; AGA's reduced
  mortality gains are a method revision. No new independent mortality panel.
- **Migration:** technical 235,000 remains unchanged from 2023. Short-term annual
  flows above it do not establish a permanent regime. Visa mix and absorption
  capacity are signposts; joint population sensitivities are not migration-only.
- **Labour:** age/cohort participation persistence needs care, flexibility and
  health support. Headline participation alone cannot establish delivered hours.
- **AI:** productivity, task/labour, complementary capital and fiscal channels are
  separate. No central additive AI coefficient was established. Stylised 1.5–2.0%
  upside productivity is conditional. The fiscal 0.1ppt-growth illustration has
  a decade-end horizon, not a general 40-year elasticity.
- **Energy:** investment/delivery, fuel-excise erosion and selected physical damage
  matter. −3.6%/−1.2% crop-yield cases in 2066 are not total GDP/climate damages.
  Independent AEMO delivery evidence was not extracted; success remains unresolved.
- **Fiscal/revenue:** tax ceiling and yield convergence are closures, not empirical
  validation. Debt and interest explicitly feed back into fiscal aggregation;
  better projected balances cannot independently corroborate their own inputs.
- **Health/care:** adjusted cost trends differ from demographics. Aged-care/NDIS
  model changes and reform delivery are not realised savings. Retirement modelling
  uses a 2019–20 base and imputed assets; pension/concession outcomes are coupled.
- **Geopolitical fragmentation:** qualitative trade/security context, not an
  extracted numerical fragmentation coefficient. Industrial transformation mixes
  sector projections/context; intergenerational equity is descriptive/policy
  context, not a numerical aggregate grade.

Nine substantive Analysis falsifiers cover productivity, fertility, migration,
participation, AI, energy, health, NDIS and tax premises. Detailed downstream and
upstream alternatives, signposts and revision tests remain in the audit JSON.

## Comparison and bounded backtest

Five 2023/2026 model comparisons align to **2062–63**, using checked original
2023 tables and exact 2026 chart cells. Rounded revisions:

| Metric | 2023 | 2026, same horizon | Difference |
|---|---:|---:|---:|
| Population, millions | 40.5 | 38.6 | −1.9 |
| Participation 15+, % | 63.8 | 65.3 | +1.5ppt |
| Underlying cash balance, % GDP | −2.6 | −1.4 | +1.2ppt |
| Gross debt, % GDP | 32.1 | 24.9 | −7.2ppt |
| Payments, % GDP | 28.6 | 27.3 | −1.3ppt |

Methods, evidence and policy conventions changed; differences are not clean
causal estimates or pre-release surprises. Terminal real GDP/person $131,815
(2023, 2062–63) versus $157,300 (2026, 2065–66) is NOT_DIRECTLY_COMPARABLE:
horizon and price conventions differ. No subtraction is retained.

Differences above are arithmetic on rounded workbook cells, not unrounded model
estimates. In particular, the report prose describes the participation upgrade
as 1.4ppt while subtraction of the retained rounded cells gives 1.5ppt. Do not
substitute either presentation silently or infer an additional model effect.

Three earlier variables inspected, **two qualified comparisons**, one exclusion:

- Population: original 2002 Table3 projects 23.2m for 2022; 2023 TableA6.1 reports
  26.0m for its 2021–22 comparison. +2.8m is explicitly SOURCE_REPORTED_COMPARISON,
  not a newly reconstructed current ABS-vintage error.
- Productivity: 2023 A6.1 reports the original 20-year average projection 1.8%
  versus realised 1.2%, −0.6ppt. The original 2002 long-run post-transition rule
  is about 1.75%; it must not be confused with the reconstructed rounded window
  average. This is a qualified source-reported comparison, not an independent
  model rerun.
- Participation: 60.2% versus 66.0% retained for inspection, but original point is
  chart-only and averaging alignment has not been independently reconstructed.
  NOT_DIRECTLY_COMPARABLE; `error: null`.

No claim of bias, manipulation, negligence or bad faith follows from a miss.
The 2002 landing-page/report-cover date discrepancy is disclosed in the manifest.
Independent original-chart/ABS-vintage reconstruction is a **DEFER** recommendation,
not a hidden claim of completed full backtesting.

## Dependency map and future-use boundaries

Eleven candidate edges: six MODEL_DEFINED, three SENSITIVITY_SUPPORTED and two
ASSUMED_MECHANISM. No unsupported external-evidence causal edge is inserted.
The vocabulary also permits EXTERNAL_EVIDENCE_SUPPORTED/HYPOTHESISED but neither
is populated just to exercise a label. Debt → interest → debt is explicitly
documented; no automatic transitive inference or confidence uplift.

Four future dimension-use mappings are retained: macro/financial conditions,
trade/capital/energy/food flows, technology/infrastructure, climate physical risk.
All have `current_state_claim: false`. No generic dependencies/chokepoints or
political-stability assessment is inferred from broad report framing. Mapping is
not component admission; model dependency is not a governed Relationship.

Production Analysis/evidence registries, Canonical, sources, Monitor, Live,
Signals, World State (including both climate components), Relationships, Risks,
Scenarios, Forecasts, Outcomes and Evaluation remain immutable inputs. Public
Brief, Outlook, Analysis, Research and web source files remain unchanged.
World State baseline: five components / three snapshots / three admissions /
zero actors. No new evidence store, model vendor dependency or monitoring parser.
Runtime model/version/reasoning metadata is UNAVAILABLE to this repository
procedure; Codex/procedure identity is retained. Model output is not corroboration.

## Integrity and reproduction

Asset manifest SHA-256:
`0fc62cbaf2311aeb7f9bb8d5b884287890159265de39c37fdb956a2cd3245bb9`.
Semantic package fingerprint:
`023bb1e0a7bdb9de0c67ab4c4d5203ab0e8d685679e7e75d60dbe1e99ed20da3`.
Before/after protected input fingerprint:
`6fad2f464bb22831842fd8b382eb499eb0cf6af415e26270a7672fe7943b8721`.
Individual part fingerprints and exact governed-object pins are in the JSONs.

Run `python3 scripts/validate_official_projection_candidate.py` offline. It checks
candidate seals, links, epistemic invariants, native DRAFT validation, exact
Canonical/source objects, source holds and before/after read nonmutation. It does
not fetch assets, regenerate values, admit records or write files. Historical
whole-file hashes document this tranche, not permanent unrelated-population
ceilings; later drift is reported separately from exact selected-object mismatch.
Source correctness/interpretation still requires human review, not just hash
validation. Online byte changes require explicit reconciliation, never silent
pin refresh. Re-extraction requires the same pinned assets; incidental HTML
changes and missing original point precision are genuine limitations.

Focused tests exercise deterministic seals, locators/units/horizons, ten audit
axes, wrong vintages/arithmetic, projection-as-actual rejection, source-family
limits, unknown provenance, no scores, no implicit acceptance, no production or
public promotion, selected-object tamper failure and read-only mutation proof.
Full exact-head validation evidence belongs in the PR handoff, not a guessed
hosted result inside this review-pending record.

## Separate human disposition questions (none decided)

| Part | Question / recommended next action |
|---|---|
| Analysis | Review publication-only spine; DEFER production admission until native extension validation and publication allowlist are adopted. |
| Projection inventory | Review exact units/locators/horizons and classifications; eligible for candidate acceptance, not Forecast conversion. |
| Assumption audit | Review each qualitative premise/axis independently; accept structure only after that review, with unresolved trajectory coverage retained. |
| Historical backtest | DEFER independent backtest acceptance pending original point/window and observed-vintage reconstruction; qualified specimens can be reviewed separately. |
| Dependency map | Review conditional model structure; no causal Relationship admission or automatic edge promotion. |

ACCEPT / DEFER / REJECT must be explicit and separable. No decision has been
recorded. Recommended next intelligence boundary is this human review plus a
bounded native Analysis extension/public-private contract decision, not World
State population, Scenario/Forecast conversion or Treasury automation activation.
