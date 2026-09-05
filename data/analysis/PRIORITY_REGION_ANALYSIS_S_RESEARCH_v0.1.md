# WORLD SIGNALS — Priority-region Analysis S research v0.1

**Research date:** 2026-09-06  
**Base main:** `a7ba439673fa2c468f2c9c4ef28904fb25c688a7`  
**Base canonical:** v0.29 / 678  
**Base Analysis:** schema v0.2; reviews v0.2 / 2; evidence v0.2 / 5

## Purpose

Stress-test the Analysis layer against the four priority geographic regions unlocked by historical-anchor tranche R:

- Africa;
- South Asia;
- Southeast Asia;
- Latin America.

This is a **sample population** exercise, not a claim of regional analytical coverage. One reviewed packet per region is sufficient only to test the contract across different institutional and evidentiary conditions.

The research standard is deliberately asymmetric: an event is not required to produce a discrete market move. `what_moved` may remain empty where the reviewed evidence does not support a defensible movement assertion. WORLD SIGNALS must be able to conclude `NO_CLEAR_SURPRISE`, `NOT_ESTABLISHED` and `NOT_A_CAUSAL_CLAIM` without treating those outcomes as analytical failures.

## Admission rule

A candidate review may enter S only if:

1. it binds to one of the four canonical R occurrences in lifecycle `COMPLETED`;
2. a primary official source supports the outcome;
3. a defensible contemporaneous pre-event expectation exists, or the packet explicitly records that an expectation benchmark is not established;
4. any market movement promoted in `what_moved` is source-reported with a stated measurement window and precision;
5. no missing market baseline is algebraically reconstructed;
6. movement is not promoted to causality by temporal sequence;
7. important competing drivers are carried as noise/alternatives rather than omitted;
8. canonical/source/monitor/calendar state remains read-only.

## South Asia — India GDP, Q1 FY2026-27

Canonical occurrence: `WSO-HIST-R-IN-GDP-2026Q1`  
Canonical series: `WSER-MAC-IN-GDP`  
Event type: `DATA_RELEASE`

### Official outcome

Press Information Bureau / Ministry of Statistics & Programme Implementation, **“QUARTERLY ESTIMATES OF GROSS DOMESTIC PRODUCT FOR THE FIRST QUARTER (APRIL-JUNE) OF 2026-27”**  
https://www.pib.gov.in/PressReleasePage.aspx?PRID=2304949&lang=1&reg=48

The official release, posted 31 August 2026 at 4:00 PM, states that real GDP grew **7.8% year-on-year** in Q1 FY2026-27 and nominal GDP grew 10.3%.

MoSPI’s own release surface also lists the Q1 press note dated 31 August 2026:  
https://mospi.gov.in/node/31376

### Expectation benchmark

Reuters, **“India smashes growth forecasts as investment surges in April-June”**  
https://www.reuters.com/business/indias-gdp-grows-78-april-june-2026-08-31/

Reuters reports a poll/consensus expectation of **7.1% year-on-year**. The observed data surprise is therefore +0.7 percentage points.

### Market observation and contamination

Reuters, **“RBI intervention, dollar flows push Indian rupee to two-month peak”**, 1 September 2026  
https://www.reuters.com/business/rbi-intervention-dollar-flows-push-indian-rupee-two-month-peak-2026-09-01/

Reuters reports that the rupee ended at **94.9500 INR per USD**, **0.2% stronger** than the previous close. The article explicitly says the move was powered principally by RBI dollar-selling intervention and flow-related dollar supply from foreign banks. It also reports that the previous day’s strong growth data improved sentiment toward the currency.

This is therefore suitable only for a **LOW-confidence `OBSERVED_ASSOCIATION`** between the GDP beat and supportive rupee sentiment. The packet must not describe GDP as the main cause of the move.

Competing/contextual drivers carried into the review:

- RBI intervention;
- foreign-bank dollar supply and fund inflows;
- global bond sell-off;
- higher oil prices;
- renewed US-Iran tensions.

The source reports a change and endpoint, not a pre-event FX level. The movement must use `CHANGE_AND_ENDPOINT`; `before_value` remains null.

## Southeast Asia — Bank Indonesia, 18–19 August 2026

Canonical occurrence: `WSO-HIST-R-ID-BI-202608`  
Canonical series: `WSER-REG-ID-BI`  
Event type: `MONETARY_POLICY_DECISION_PROCESS`

### Official outcome

Bank Indonesia, **“BI-Rate Held at 5.75%: Strengthening Stability, Supporting Economic Growth”**, 19 August 2026  
https://www.bi.go.id/en/publikasi/ruang-media/news-release/Pages/sp_2816226.aspx

The official release states that the 18–19 August Board of Governors Meeting:

- held BI-Rate at **5.75%**;
- held the Deposit Facility rate at **4.75%**;
- held the Lending Facility rate at **6.50%**.

BI explicitly framed the decision around rupiah stability amid heightened global volatility and the Middle East war, inflation remaining within target, and sustainable growth.

### Expectation benchmark

Reuters syndication via Kontan, **“Indonesia Central Bank Holds Rates Steady at 5.75%, as Expected”**, 19 August 2026  
https://english.kontan.co.id/news/indonesia-central-bank-holds-rates-steady-at-575-as-expected

The page identifies Reuters as source and reports that **all but one of 28 economists** polled by Reuters expected BI to hold the benchmark rate at 5.75%.

The headline decision therefore supports `NO_CLEAR_SURPRISE` rather than a directional surprise classification.

### Market movement

The reviewed contemporaneous evidence does **not** establish a clean, discrete post-decision rupiah, rates or equity move with a defensible measurement window. S therefore promotes **no market movement** for this packet.

This null result is analytically intentional. The decision occurred amid substantial global/geopolitical volatility and during an institutional leadership transition following the prior governor’s resignation. Those conditions make a casual same-session market narrative particularly vulnerable to post-hoc attribution.

## Africa — Central Bank of Egypt, 20 August 2026

Canonical occurrence: `WSO-HIST-R-EG-CBE-20260820`  
Canonical series: `WSER-REGJ-EG-CBE-MPC`  
Event type: `MONETARY_POLICY_DECISION`

### Official outcome

Central Bank of Egypt, **“MPC Press Release 20 August 2026”**  
https://www.cbe.org.eg/en/news-publications/news/2026/08/20/15/17/mpc-press-release-20-august-2026

CBE kept:

- overnight deposit rate at **19.00%**;
- overnight lending rate at **20.00%**;
- main-operation rate at **19.50%**;
- discount rate at **19.50%**.

The CBE also reported monthly headline and core inflation of 0.0% in July, below expectations, while retaining upside-risk warnings around regional hostilities and pass-through from fiscal consolidation measures.

### Expectation benchmark

HC Securities & Investment, **“HC expects the MPC to hold interest rates at its 20 August meeting”**, 19 August 2026  
https://www.hc-si.com/hc-expects-the-mpc-to-hold-interest-rates-at-its-20-august-meeting

HC explicitly expected the MPC to keep rates unchanged. Its rationale included accelerated inflation pressure, higher energy costs and regional geopolitical turbulence, while judging Egypt’s external position comparatively resilient.

The observed hold is therefore classified `NO_CLEAR_SURPRISE`; S does not convert one institutional forecast into a synthetic numeric consensus distribution.

### Market movement

No clean discrete post-decision market movement is promoted. Reuters’ immediate outcome report records the unchanged rates but does not establish a sufficiently isolated reaction window. The packet therefore carries `what_moved: []` and `NOT_A_CAUSAL_CLAIM`.

## Latin America — Argentina CPI, July 2026

Canonical occurrence: `WSO-HIST-R-AR-CPI-202607`  
Canonical series: `WSER-REG2-AR-CPI`  
Event type: `OFFICIAL_STATISTICAL_RELEASE`

### Official outcome

INDEC, official consumer-price-index release surface  
https://www.indec.gob.ar/Nivel4/Tema/3/5/31

Historical first-party verification in tranche R recorded the 13 August 2026 July CPI technical report and **2.1% month-on-month** national CPI result. The current public page is a rolling publication surface, so the canonical R capture remains the provenance anchor for occurrence completion; S uses the same first-party surface as analytical outcome evidence without altering canonical provenance.

### Expectation benchmark and context

Reuters, **“Argentina monthly inflation rises in July to 2.1%”**, 13 August 2026  
https://www.reuters.com/world/americas/argentina-monthly-inflation-rises-july-21-2026-08-13/

Reuters reports:

- July CPI: **2.1% m/m**;
- June CPI: 1.9% m/m;
- analyst expectation: **2.0% m/m**;
- year-on-year CPI: 33.8%, up from 33.5%.

The monthly surprise is therefore a modest **UPSIDE +0.1 percentage point**.

Reuters attributes the largest category increases to recreation/culture, especially winter-holiday packages, followed by restaurants/hotels. Those composition/seasonality effects are carried as explanatory context rather than a market-causality claim.

### Market movement

No clean discrete market move is established by the reviewed contemporaneous evidence. `what_moved` remains empty.

## Cross-case result

S deliberately tests four different analytical outcomes:

| Region | Event | Surprise | Market movement promoted? | Connection language |
|---|---|---|---|---|
| South Asia | India GDP | UPSIDE | Yes — rupee change+endpoint | LOW-confidence OBSERVED_ASSOCIATION; intervention/flows are stronger immediate drivers |
| Southeast Asia | BI decision process | NO_CLEAR_SURPRISE | No | NOT_A_CAUSAL_CLAIM |
| Africa | CBE decision | NO_CLEAR_SURPRISE | No | NOT_A_CAUSAL_CLAIM |
| Latin America | Argentina CPI | UPSIDE | No | NOT_A_CAUSAL_CLAIM |

This is a stronger stress test than requiring every event to produce a market story. It demonstrates that WORLD SIGNALS can preserve an information-rich null result.

## Explicit non-actions

S must not:

- modify the canonical registry or schema;
- modify the source registry;
- modify the change ledger or biosecurity overlay;
- modify monitor expectations or monitor operations policy;
- add or infer event times;
- add historical occurrences;
- promote analytical evidence into canonical provenance;
- reconstruct missing market baselines;
- infer market causality from temporal sequence;
- describe one reviewed packet per priority region as analytical completeness;
- enable automatic canonical commit;
- enable Google Calendar writes.
