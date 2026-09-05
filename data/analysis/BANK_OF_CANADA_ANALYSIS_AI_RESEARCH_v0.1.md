# WORLD SIGNALS — Bank of Canada Analysis AI research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `b12058d260a8139c893feb52ad864258044e83b2` (merged PR #63)

## Why this specimen now

The post-AH read-only pressure audit finds 20 completed Analysis-eligible canonical occurrences and 12 reviewed post-event specimens. There are no completed-anchor regional gaps. The only canonical category still lacking any completed anchor is `CORPORATE_FINANCIAL_MARKET_STRUCTURE`, but mechanically backfilling that category would prioritise histogram completion over marginal analytical pressure.

The reviewed Analysis sample has one remaining regional omission: **North America**. The completed Bank of Canada 2 September 2026 decision is the strongest specimen for that gap because it also tests an exact canonical release time, an expected headline policy decision, a materially more hawkish communication/path signal, and market reaction observed under heavy global/geopolitical contamination.

The RBA March 2026 Financial Stability Review ranks highly on taxonomy novelty and also has an exact canonical release time. It remains a strong later non-market/financial-stability specimen. AI chooses Bank of Canada because it repairs the reviewed North America gap while testing a different distinction: **headline decision surprise versus communication/path surprise**.

Queue exhaustion is not the objective. The other completed occurrences remain eligible.

## Canonical target

- occurrence: `WSO-ddb70f8ff05a58fb`
- series: `WS.CB.BOC.POLICY_RATE_ANNOUNCEMENT`
- canonical name: `Bank of Canada policy interest rate announcement — 2026-09-02`
- institution: Bank of Canada
- region: North America
- category: `MONETARY_FINANCIAL_POLICY`
- event type: `DECISION`
- lifecycle: `COMPLETED`
- native release: `2026-09-02T09:45:00`, `America/Toronto`
- UTC release: `2026-09-02T13:45:00Z`
- precision: `MINUTE`

The exact canonical timestamp is already upstream truth. AI does not alter it.

## First-party outcome and guidance

### Bank of Canada decision release

https://www.bankofcanada.ca/2026/09/fad-press-release-2026-09-02/

The Bank held the target for the overnight rate at **2.25%**, with Bank Rate at **2.5%** and the deposit rate at **2.20%**. It described continuing Middle East conflict, high energy prices, new US tariffs and Canadian counter-measures as material uncertainties.

### Official event timing

https://www.bankofcanada.ca/2026/09/interest-rate-announcement-september-2-2026/

The Bank's event page states that the interest-rate announcement was scheduled for **09:45 ET** and that the press conference was expected around **10:30 ET**. These are distinct information moments. AI analyses the canonical 09:45 decision occurrence and treats later press-conference remarks as subsequent information within the same policy communication episode, not as though they were part of the 09:45 payload.

### Opening statement

https://www.bankofcanada.ca/2026/09/opening-statement-2026-09-02/

Governor Tiff Macklem said recent Canadian data had evolved broadly in line with the July forecast and explained the decision to maintain the policy rate at 2.25%. He also said upside risks to inflation had increased because of persistent high energy prices and potential tariff pass-through, while trade uncertainty increased risks to growth. The Bank remained prepared to adjust policy as needed.

## What was expected

Reuters poll, 28 August 2026:
https://www.reuters.com/world/americas/bank-canada-hold-rates-another-year-wait-more-stability-trade-2026-08-28/

All **35 economists** in the Reuters poll expected the Bank to hold the overnight rate at 2.25% on 2 September, in line with market pricing. The poll's median path expected the rate to remain at 2.25% through at least the third quarter of 2027, with a rise to 2.50% only in the fourth quarter of 2027.

This establishes two different expectation objects:

1. **headline decision expectation:** hold at 2.25%;
2. **policy-path expectation:** a long hold, with the median economist path not anticipating a hike until late 2027.

AI must not collapse these into one synthetic surprise number.

## What surprised

Reuters decision coverage, 2 September 2026:
https://www.reuters.com/world/americas/bank-canada-set-hold-rates-strong-growth-collides-with-trade-risks-2026-09-02/

The headline hold matched consensus. Reuters nevertheless characterised the communication as more hawkish: the Bank dropped earlier language that the current policy rate was appropriate to balance risks, and Macklem said policymakers could need multiple hikes if inflation remained too high. Markets subsequently priced hikes beginning in December, potentially continuing into 2027.

The appropriate Analysis classification is therefore **`MIXED`**:

- no headline decision surprise;
- a qualitatively hawkish communication/path surprise relative to the pre-event expectation of an extended hold.

This is exactly the distinction protected by Analysis schema v0.3: a headline action may match consensus while guidance/path information surprises.

## Market observations

### Canadian dollar

Reuters, 2 September 2026:
https://www.reuters.com/business/canadian-dollar-rebounds-nearly-three-week-low-boc-inflation-concerns-2026-09-02/

Reuters reported that the Canadian dollar strengthened **0.4%** against the US dollar to **C$1.3840 per US$1** after earlier touching C$1.3939, as investors increased expectations of future Bank of Canada rate hikes after the Bank emphasised greater upside inflation risks.

This is useful event-linked market evidence, but it is **not** an independently reconstructed 09:44/09:46 time series. The correct precision is `SOURCE_REPORTED_CHANGE_AND_ENDPOINT`, not `EXACT_TIMESTAMP_SERIES`.

### Rates / policy pricing

Reuters' decision coverage says Canadian government bond yields edged higher after the remarks and markets moved to price rate increases beginning in December. The available reviewed evidence does not provide a clean independent pre/post yield series at the canonical 09:45 timestamp. Any rate-path movement is therefore represented qualitatively or as source-reported repricing, not reconstructed tick data.

### Equity market

Reuters reported the S&P/TSX Composite closed up 0.7% on 2 September, with financial and mining shares leading the rebound. The hold may have been supportive, but the day's equity move was broad and materially exposed to sector and global drivers. AI does **not** use the TSX close as a clean Bank-of-Canada reaction measure.

## Pre-event contamination and alternatives

Reuters, 1 September 2026:
https://www.reuters.com/business/canadian-dollar-weakens-ahead-boc-rate-decision-10-year-yield-hits-2-year-high-2026-09-01/

The Canadian dollar had weakened 0.4% to C$1.3905 per US dollar on the day before the decision, while Canada's 10-year yield reached a two-year high amid a broader global bond sell-off. This matters because the 2 September reaction occurred against an already volatile global rates backdrop.

Additional alternative/common drivers include:

- broad US-dollar moves;
- global sovereign-bond repricing;
- Middle East conflict and elevated oil prices;
- Canadian-US tariff escalation;
- stronger-than-expected Canadian Q2 growth already incorporated into the pre-event information set.

## Exact-timestamp measurement finding

The canonical decision is exact to the minute: **09:45 ET / 13:45Z**.

That does **not** entitle Analysis to label a market observation `EXACT_TIMESTAMP_SERIES`.

The Bank of Canada's public exchange-rate and money-market series reviewed for AI are daily/through-day observations rather than a clean event-time series. Reuters provides event-linked market reporting but not an independently reconstructable exact pre/post timestamp pair in the reviewed material.

Therefore AI intentionally leaves the existing Analysis measurement gap unresolved:

- canonical timestamp precision: exact minute;
- market-measurement precision: source-reported change/endpoint or qualitative;
- `EXACT_TIMESTAMP_SERIES`: still zero after AI.

This is a methodological result, not a missing-data field to be guessed.

## Causal discipline

AI may support an **observed association** between the more hawkish communication and contemporaneous CAD/rate-path repricing because multiple Reuters reports explicitly describe investors raising hike bets after the Bank's inflation-risk communication.

It must not escalate that into a clean causal estimate. The event sat inside a globally volatile rates, FX, energy and geopolitical session. The analysis therefore requires explicit alternatives and falsifiers.

## Selection conclusion

Select the Bank of Canada 2 September 2026 decision for AI.

The specimen adds:

- first reviewed North America occurrence;
- first reviewed Bank of Canada occurrence;
- explicit headline-versus-guidance surprise decomposition;
- exact canonical time versus non-exact market-measurement separation;
- market reaction with contamination rather than post-hoc monocausality.

Do not create a market-structure historical anchor merely because that category is now the last completed-anchor gap. Reassess it after AI.
