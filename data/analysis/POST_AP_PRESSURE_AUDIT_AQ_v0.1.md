# WORLD SIGNALS — post-AP pressure audit AQ v0.1

**Reference date:** 2026-09-06  
**Exact base:** `c7381ff684e6aeb8c458cdf5eb1740ef6a8a8e3b` (post-PR #71 `main`)  
**Layer:** Analysis selection / read-only pressure audit  
**Population write authorised by this audit alone:** **NO**

## Live post-AP state

- canonical registry `v0.37 / 687`;
- source registry `v1.78 / 242`;
- change ledger `v0.24 / 59`;
- biosecurity overlay `v0.12`, checkpoint `v0.37 / 687`;
- monitor expectations `v0.9`;
- Analysis schema `v0.4`;
- Analysis reviews `v0.14 / 18`;
- Analysis evidence `v0.14 / 79`;
- eligible completed occurrences `20`;
- reviewed occurrences `18`;
- reviewed event-type diversity `16`;
- production `EXACT_TIMESTAMP_SERIES` rows `0`;
- broad population state `READY_FOR_CONTROLLED_EXPANSION`.

The remaining completed/unreviewed choice set is exactly:

1. `WSO-TRD-EU-RU-SANC-20260625` — EU economic sanctions on Russia, 25 June 2026 renewal — `TRADE_SANCTIONS_INDUSTRIAL_POLICY / SANCTIONS_PROCESS`;
2. `WSO-MAC-B-0041` — Japan Family Income and Expenditure Survey, July 2026 — `MACROECONOMIC_RELEASE / DATA_RELEASE`.

This is a choice set, not a queue. Completing it is not a population objective.

## Wider architecture pressure

The audit rechecks the long-standing upstream `CORPORATE_FINANCIAL_MARKET_STRUCTURE` completed-anchor gap rather than assuming one of the two remaining Analysis specimens must be selected.

That gap remains real but is not a stale lifecycle defect. Existing forward holdings are concentrated in ASX/CME expiry mechanics, Russell reconstitution steps and later UK/EU T+1 transitions. Prior exact-base reconnaissance found no past-starting non-terminal market-structure occurrence that could be repaired simply by correcting lifecycle state. A historical ASX/CME/MSCI/index-rebalance admission would therefore be a deliberate backfill.

That backfill remains feasible, but choosing a mechanical expiry solely to erase the final category zero would optimise the histogram rather than marginal analytical value. Market structure stays explicitly open for a future contract-driven selection.

## Candidate research

### EU economic sanctions on Russia — 25 June 2026 renewal

The Council of the European Union states that on 25 June 2026 it renewed the sectoral economic sanctions concerning Russia's destabilising actions in Ukraine for a further **12 months, until 31 July 2027**.

Primary Council source:
- https://www.consilium.europa.eu/en/press/press-releases/2026/06/25/russia-s-war-of-aggression-against-ukraine-council-extends-economic-sanctions-for-another-year/

The binding legal act is Council Decision (CFSP) 2026/1437. It amended Article 9(1) of Decision 2014/512/CFSP so that the measures apply until 31 July 2027, and states that the decision enters into force the day following publication in the Official Journal.

Primary legal source:
- https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026D1437

The legal adoption must be separated from the political agreement that preceded it. Reuters reported on 18 June 2026 that EU leaders had agreed to renew the sanctions for another 12 months, the first full-year renewal after previous six-month rollovers. That public political agreement is a defensible pre-adoption expectation for the direction and horizon of the later legal act, but it is not itself the binding Council decision and is not a market-consensus forecast.

Pre-adoption reporting:
- https://www.reuters.com/world/europe/eu-leaders-agree-renew-russia-sanctions-12-months-2026-06-18/

The European Council's published 18 June conclusions separately document the policy context: increasing pressure on Russia, reducing energy revenues, curbing the shadow fleet, constraining the banking system, strengthening enforcement and calling for swift adoption of a further sanctions package.

Primary context:
- https://www.consilium.europa.eu/en/press/press-releases/2026/06/18/european-council-conclusions-on-ukraine-and-security-and-defence-18-june-2026/

The annual renewal did not freeze the sanctions regime. On 23 July 2026 the Council adopted a 21st sanctions package with new individual/entity designations and additional measures affecting energy, finance, crypto and the shadow fleet. This later action is evidence that legal continuity through July 2027 coexists with later amendment and calibration. It is not evidence that the June renewal caused the July package.

Primary later-policy context:
- https://www.consilium.europa.eu/en/press/press-releases/2026/07/23/21st-package-of-sanctions-eu-hits-russian-energy-financial-services-and-crypto-hard/

No defensible event-specific market response has been established. Reuters reported large oil-price moves on 24 June in the context of changing expectations about Strait of Hormuz crude flows and Iran-related supply risk. That is a strong contemporaneous alternative driver and argues against narrating same-period oil movement as a reaction to the 25 June EU legal renewal.

Market-context reference:
- https://www.reuters.com/business/energy/oil-prices-extend-decline-expectations-smoother-crude-flows-via-hormuz-2026-06-24/

### Japan household spending — held

The July 2026 Japanese household-spending release remains analytically valid. Official data showed real consumption expenditure for two-or-more-person households down 3.6% year on year and up 0.5% month on month seasonally adjusted; Reuters had reported expectations of a 1.6% year-on-year decline and 2.6% month-on-month rise.

This supplies a clean negative macro surprise, but the repository already exercises multiple `DATA_RELEASE` specimens and explicit surprise/market-contamination contracts. Its marginal novelty is therefore lower than the sanctions/legal-continuity object.

References:
- https://www.stat.go.jp/english/data/kakei/156.htm
- https://www.reuters.com/world/asia-pacific/japan-year-on-year-household-spending-drops-8-straight-months-2026-09-03/

## Comparative pressure test

| Candidate | New reviewed category/type | Main new analytical boundary | Evidence quality | Marginal value |
| --- | --- | --- | --- | --- |
| EU sanctions renewal | `TRADE_SANCTIONS_INDUSTRIAL_POLICY / SANCTIONS_PROCESS` | political agreement → binding legal adoption → in-force horizon → later amendment/calibration → future renewal boundary | strong Council/EUR-Lex + Reuters prior reporting | **highest** |
| Japan household spending | no new category/type | clean macro surprise and household-demand signal | strong official data + Reuters expectation | medium |
| historical market structure backfill | would repair final upstream completed-anchor category gap | rule-derived expiry/reconstitution mechanics | feasible but source/rights dependent | real gap, lower current marginal value |

## Selection

AQ selects **`WSO-TRD-EU-RU-SANC-20260625` — EU economic sanctions on Russia, 25 June 2026 renewal decision**.

The selection is not European quota filling and is not FIFO completion. It creates the strongest untested Analysis object:

1. **political agreement is not binding legal adoption**;
2. **legal adoption is not press-release publication time**;
3. **a novel 12-month renewal cadence is not automatically a surprise when publicly agreed a week earlier**;
4. **renewal to 31 July 2027 is not the same event as the 31 July 2027 renewal/expiry boundary**;
5. **renewal does not imply the sanctions framework is frozen until 2027**;
6. **later sanctions amendments are not effects caused by the renewal merely because they occur under the same framework**;
7. **same-period oil, FX, rates or equity movement must not be attributed to the renewal without event-specific evidence**;
8. **expiry or renewal boundary does not imply automatic termination**.

## Schema decision

No Analysis schema migration is justified.

Schema `v0.4` can already represent:
- `NOT_ESTABLISHED` surprise;
- `OTHER_DEFENSIBLE_EXPECTATION` for pre-adoption political agreement;
- empty market response;
- `LEGAL_OR_OPERATIONAL_DEPENDENCY` with `NOT_A_CAUSAL_CLAIM`;
- `PLAUSIBLE_WATCH_ITEM` second-order institutional effects;
- alternatives, noise tests and falsifiers.

The pressure is legal/institutional classification discipline, not missing schema capacity.

## Descendant-test pressure

AP's frozen historical post-state remains exact at `v0.14 / 18 reviews / 79 evidence / 16 event types`.

AP is now one generation behind AQ. Its live descendant assertions must therefore permit legitimate later growth while retaining the exact historical AP checkpoint and exactly one `HEALTH_GOVERNANCE_EVENT` contribution. AQ may narrow-repair only the live descendant count/version/evidence ceilings; AP's plan, payload and exact prestate transform remain frozen.

## AQ authorised boundary

A subsequent reviewed AQ plan may add one EU-sanctions Analysis review and its Analysis-only evidence if exact-prestate, source, legal and regression gates pass.

AQ must not mutate:
- Canonical Registry or schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- monitor expectations or operations policy;
- Analysis schema;
- Calendar / Google Calendar.

No auto-merge. No queue-exhaustion claim. Japan household spending remains held as a legitimate future specimen.