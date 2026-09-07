# BL — Japan household-spending Statistics Dashboard API monitor research

**Review date:** 2026-09-08  
**Exact post-BK base:** `3952ec1f5a6022fec43210103f7a7244442e3201`

## Pressure being tested

After BK, WORLD SIGNALS has nine configured production monitor routes but still has no production route anchored in East Asia. The purpose of BL is not to increase the route count mechanically. It is to test whether an already-canonical Japanese macro series has an official machine interface with sufficiently explicit access terms and deterministic data identity to support a genuinely governed review-only monitor.

The candidate chosen is the Statistics Bureau of Japan's Family Income and Expenditure Survey household-spending series, `WSER-MAC-JP-HHSPEND`. The canonical schedule source remains `WSSRC-MAC-024` and currently supplies eight source-native civil-date occurrences from 4 September 2026 through 6 April 2027.

## Why the existing schedule source is not being repurposed

`WSSRC-MAC-024` is an official Statistics Bureau release-schedule surface and remains a valid canonical provenance source. Its current automation classification is `ENDPOINT_REVIEW_REQUIRED`. BL does not reinterpret that HTML schedule as machine-permitted merely because it is publicly reachable.

Instead, BL applies the established WORLD SIGNALS source-decomposition rule: materially different endpoint roles and access conditions receive distinct source identities. This mirrors the Colombia `WSSRC-REG4-001` / `WSSRC-REG4-002` split, where canonical/manual legal authority and a reuse-cleared machine sentinel remain separate.

The proposed new machine source is therefore `WSSRC-MAC-030`. It will have **zero canonical dependencies**. Canonical schedule truth continues to point to `WSSRC-MAC-024`; manual/statistical-result verification continues to use the official result surface `WSSRC-MAC-029`.

## Official Statistics Dashboard WebAPI

The Statistics Dashboard operated by the Statistics Bureau, Ministry of Internal Affairs and Communications publishes an official REST WebAPI. Its English API documentation says that the data displayed on its chart/data pages are also published through the WebAPI in machine-readable formats including XML, JSON and CSV. It expressly states that no registration is required and anyone can use the API, subject to the Site Policy.

The Japanese API guidance additionally states that users must not conduct short-period mass access that interferes with operation of the API, network or system. BL treats this as an operational constraint, not as permission for unconstrained crawling. The production design makes one narrow bounded `getData` request per monitor run for one indicator and eight monthly reference periods.

Official surfaces reviewed:

- `https://dashboard.e-stat.go.jp/en/static/api`
- `https://dashboard.e-stat.go.jp/static/api`
- `https://dashboard.e-stat.go.jp/en/static/sitePolicy`
- `https://dashboard.e-stat.go.jp/static/sitePolicy`

## Deterministic household-spending identity

Read-only probe run **34168995455** resolved the official indicator metadata. The exact monitored indicator is:

- indicator code: `0704010101000010000`
- label: **Consumption expenditures for two-or-more-person households**
- survey: **Family Income and Expenditure Survey**
- statistical table code: `00200561`
- cycle: `1` — monthly
- regional rank: `2` — Japan
- region code: `00000` — nationwide
- original/seasonal selector: `1` — original series
- source timezone: `Asia/Tokyo`

These dimensions are part of the parser contract. A response row carrying a different indicator, statistical table, region, cadence or seasonal-adjustment identity fails closed rather than being treated as the same series.

## Reference-period mapping

The API uses monthly time codes of the form `YYYYMM00`. The eight existing canonical release occurrences map to the following reference periods:

| Canonical occurrence | Canonical release date | Reference period code |
| --- | --- | --- |
| `WSO-MAC-B-0041` | 2026-09-04 | `20260700` |
| `WSO-MAC-B-0042` | 2026-10-09 | `20260800` |
| `WSO-MAC-B-0043` | 2026-11-10 | `20260900` |
| `WSO-MAC-B-0044` | 2026-12-08 | `20261000` |
| `WSO-MAC-B-0045` | 2027-01-08 | `20261100` |
| `WSO-MAC-B-0046` | 2027-02-05 | `20261200` |
| `WSO-MAC-B-0047` | 2027-03-09 | `20270100` |
| `WSO-MAC-B-0048` | 2027-04-06 | `20270200` |

The mapping is explicit configuration. The monitor does not derive a release date by adding a lag to the reference month.

## Live data-availability negative control

Read-only probe run **34169141999** tested the exact `getData` route on 8 September 2026.

For July 2026 (`20260700`), the API returned an actual `DATA_OBJ.VALUE` row:

- value: `301245`
- `@isProvisional`: `0`
- indicator: `0704010101000010000`
- stat: `00200561`
- region: `00000`
- cycle: `1`
- original-series selector: `1`

For August 2026 (`20260800`), the API returned HTTP 200 but **no `DATA_OBJ.VALUE` row**. This is the expected state before the canonical 9 October 2026 release.

An important parser hazard was identified: the API echoes the requested `Time`/`TimeFrom`/`TimeTo` parameter inside the response. Therefore the literal string `20260800` may be present even when no August data object exists. BL only treats a validated `STATISTICAL_DATA.DATA_INF.DATA_OBJ.VALUE` object as data availability. Raw token presence is never sufficient.

## Monitor semantics

BL monitors **data availability**, not the release calendar.

For a completed canonical occurrence:

- matching API data present → observation only;
- matching API data absent → source-health observation only; never revert completion.

For a planned canonical occurrence:

- matching API data absent → observation only; no cancellation, delay or date-change inference;
- matching API data present before the canonical release civil date → review candidate for unexpected/early data availability, with **no schedule change inferred**;
- matching API data present on or after the canonical release civil date → completion-review candidate requiring manual official result verification before lifecycle can change.

The API never supplies canonical release clock time, and BL never fabricates one. All eight canonical occurrences remain `DAY` precision in `Asia/Tokyo`. API values do not change certainty status. API outcome data is not automatically promoted into Live Intelligence or Analysis.

## Operational discipline

The proposed production route is `JAPAN_HHSPEND_STATISTICS_DASHBOARD_API` using new machine source `WSSRC-MAC-030`. One bounded query covers `20260700` through `20270200`; the monitor parser then compares returned reference-period rows against the eight explicit canonical occurrence mappings.

All propositions remain review-only. Automatic Canonical commit remains off. Google Calendar writes remain off. Any source failure is source health only.

## Expected structural effect

If the transaction passes its read-only materialised preflight and controlled mutation audit:

- Canonical remains v0.41 / 689;
- Sources advance v1.84 / 246 → **v1.85 / 247** solely by adding `WSSRC-MAC-030`;
- Monitor expectations advance v0.11 / 9 → **v0.12 / 10**;
- Change Ledger, biosecurity overlay, Live Intelligence and Analysis remain byte-semantically unchanged;
- the production monitor cohort gains its first East Asia machine route without weakening source governance.

This does **not** authorize Japan MOF JGB, RBA MPB, RBNZ, Kenya Law or any other held route.
