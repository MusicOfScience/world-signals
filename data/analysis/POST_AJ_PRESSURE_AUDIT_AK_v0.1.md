# WORLD SIGNALS — Post-AJ pressure audit AK v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `53e98457b70aa0dda4da490d5fe3210ce333ecae`  
**Architecture position:** Analysis methodology audit  
**Mutation policy:** read-only selection audit; no canonical, source, ledger, overlay, monitor, Calendar, Analysis-review or Analysis-evidence mutation

## Verified post-AJ checkpoint

- Canonical registry: **v0.37 / 687**
- Source registry: **v1.78 / 242**
- Change ledger: **v0.24 / 59**
- Biosecurity overlay: **v0.12 @ canonical v0.37 / 687**
- Analysis schema: **v0.3**
- Analysis reviews: **v0.10 / 14**
- Analysis evidence: **v0.10 / 54**
- completed Analysis-eligible occurrences: **20**
- reviewed occurrences: **14**
- reviewed event-type diversity: **12**
- market-movement rows: **10**
- independently reconstructed market rows: **0**
- `EXACT_TIMESTAMP_SERIES` rows: **0**
- completed-but-unreviewed frontier: **6**

The evidence count is 54, not the approximate 53 carried in the thread handoff. AJ added four evidence rows.

## Remaining population pressure

The only canonical category represented in the registry but absent from the completed-anchor population is `CORPORATE_FINANCIAL_MARKET_STRUCTURE`. That remains a real upstream gap, but it is not a quota. Existing forward market-structure coverage is mechanically concentrated; backfilling an expiry solely to make the category-gap histogram reach zero would add less semantic value than the stronger methodology pressure described below.

All canonical regions represented by the registry now have at least one completed Analysis-eligible anchor. The six completed-but-unreviewed occurrences are:

| Occurrence | Category / event type | Marginal sample value |
| --- | --- | --- |
| `WSO-FIN-B-0004` | FINANCIAL_STABILITY_REGULATION / FINANCIAL_STABILITY_REPORT | new category, event type and institution; exact canonical release time also stresses event-time versus market-measurement precision |
| `WSO-CLIM-UNFCCC-SB64-202606` | CLIMATE_ENVIRONMENT / ENVIRONMENTAL_GOVERNANCE_EVENT | new category, event type and institution |
| `WSO-EL-KR-LGE-20260603` | ELECTIONS_GOVERNANCE / ELECTION_MILESTONE | new category, event type and institution |
| `WSO-HEALTH-WHA-079` | HEALTH_BIOSECURITY / HEALTH_GOVERNANCE_EVENT | new category, event type and institution |
| `WSO-TRD-EU-RU-SANC-20260625` | TRADE_SANCTIONS_INDUSTRIAL_POLICY / SANCTIONS_PROCESS | new category, event type and institution |
| `WSO-MAC-B-0041` | MACROECONOMIC_RELEASE / DATA_RELEASE | mainly institution novelty; repeats an already exercised macro/data-release contract |

Among individual Analysis specimens, the **RBA Financial Stability Review — March 2026** has the highest marginal value because it adds taxonomy and institution novelty while carrying an exact canonical release timestamp. It remains a strong next specimen after the methodology issue is repaired.

## Exact-market-measurement pressure

The live Analysis schema v0.3 contains `EXACT_TIMESTAMP_SERIES` as a permitted `measurement_precision` value, but the live validator has no dedicated exact-series branch. An exact-series row is currently subject only to the generic movement rules: valid movement type, representation and precision enum; non-empty measurement window and evidence references; and an explicit `independently_reconstructed` boolean.

The validator does **not** currently require an exact-series row to establish:

- an independently sourced market series identity;
- an IANA market/source timezone;
- a series granularity or sampling basis;
- explicit before/after observation timestamps;
- an event anchor copied from canonical state;
- ordering of observations around that anchor;
- a market-observation evidence row from a primary/exchange or market-data provider;
- a reviewed data-use/reuse basis; or
- permission for the exact observations to enter the public Analysis projection.

This is a material contract gap. The enum can currently imply more precision than the structure proves.

## External rights/source reconnaissance

Authoritative exchange material confirms that high-frequency data can exist without being freely ingestible or redistributable.

- CME Group offers historical trades, top-of-book, market depth and market-by-order datasets through DataMine and says historical data is purchased/licensed rather than simply scraped from a public page: https://www.cmegroup.com/market-data/real-time-and-historical-data.html
- CME explicitly describes internal non-display use for research and analysis as a licensing use case, and separately licenses distribution: https://www.cmegroup.com/market-data/license-data.html
- CME's policy centre distinguishes non-display use, historical licensing and distribution permissions: https://www.cmegroup.com/market-data/license-data/market-data-policy-education-center.html
- ASX states that historical data covering every ASX market is a data product and points users to licensing/access routes: https://www.asx.com.au/connectivity-and-data/information-services/price-data
- ASX MarketSource is tick-by-tick, and direct ITCH access can carry nanosecond timestamps; direct and vendor access are explicit service arrangements: https://www.asx.com.au/connectivity-and-data/information-services/price-data/how-to-access-asx-price-data

Therefore **data existence != access authority != reuse authority != public redistribution authority**. WORLD SIGNALS must preserve that separation before it ingests any exact market series.

## Selection

### Selected next tranche: exact-market-measurement contract

The methodology tranche has greater marginal architectural value than consuming another completed review now because:

1. the weakness is live: ten market-response rows already exist, even though none claims exact-series precision;
2. the first exact-series row has not yet been populated, so the contract can be repaired without migrating production exact data;
3. two recent specimens have already demonstrated that exact canonical event timing does not establish exact market-measurement precision;
4. exchange data availability is explicitly entangled with licensing and redistribution permissions; and
5. the completed Analysis frontier remains broad enough that one methodology tranche does not strand an urgent unique specimen.

### Intended AK contract

Upgrade Analysis schema **v0.3 → v0.4** without adding any market observation. `EXACT_TIMESTAMP_SERIES` will remain at **0**.

For an exact-series movement, require all of the following:

- `movement_representation == PRE_POST_VALUES`;
- `independently_reconstructed == true`;
- existing canonical occurrence has an exact `start_utc` anchor;
- `event_anchor_utc` exactly equals that canonical `start_utc` rather than independently resolving or replacing it;
- explicit UTC `before_observation_utc` and `after_observation_utc` with `before < anchor <= after`;
- non-empty `market_series_id`;
- valid IANA `market_timezone`;
- non-empty `series_granularity`;
- controlled `data_use_basis`;
- `public_projection_permitted == true` for any exact observations stored in the public Analysis dataset;
- at least one referenced `MARKET_OBSERVATION` evidence row whose evidence class is `PRIMARY_OFFICIAL` or `MARKET_DATA_PROVIDER`.

Non-exact source-reported rows remain valid and are not upgraded merely because their canonical event has an exact timestamp.

## Guardrails

- Canonical event time **does not** confer market-series precision.
- Exact market observations may **not** backfill or resolve missing canonical timing.
- A newswire description of an intraday move is **not** an independently reconstructed exact series.
- A licensed internal dataset is **not** automatically permitted in a public projection.
- `EXACT_TIMESTAMP_SERIES == 0` is an acceptable post-state; the objective is a defensible contract, not filling the enum.
- The RBA FSR, SB64, WHA79, South Korean local elections and EU sanctions renewal remain legitimate later specimens; none is compulsory backlog.
- The market-structure category gap remains open unless a genuinely useful historical anchor is independently justified.
