# BX — China NBS native Latest Releases RSS research v0.1

Reference date: 2026-09-09  
Frozen base: `29b71bea42610992ad073b1583be64ced7e5de81`

## Decision

BX selects a **new monitor-only native RSS source** for the National Bureau of Statistics of China (NBS), while leaving the existing Canonical release-calendar source `WSSRC-MAC-007` unchanged.

This is a source-role decomposition, not a retroactive clearance of the annual release-calendar endpoint.

- `WSSRC-MAC-007`: remains Canonical forward release-date/clock authority for 36 already-modelled NBS occurrences; its existing endpoint-review/automation status is preserved byte-for-byte by the transaction.
- `WSSRC-MAC-026`: proposed new native `最新发布` RSS monitor identity; publication sentinel only, zero Canonical dependencies.
- route: `CHINA_NBS_LATEST_RELEASES_RSS`.

## Why NBS emerged from the post-BW audit

Read-only pressure audit `34254051956` / `102155253630` found no already-cleared but unrouted Canonical-dependent sources. The leading unresolved sources therefore all required a genuine source-role, endpoint, or rights decision rather than quota filling.

NBS `WSSRC-MAC-007` carries 36 Canonical dependencies spanning CPI, PPI, PMI, National Economic Performance and five component activity releases. It is therefore material, but dependency count alone was not sufficient for selection.

## Existing Canonical schedule source remains held for automated calendar retrieval

`WSSRC-MAC-007` is the NBS annual regular press-release calendar:

`https://www.stats.gov.cn/english/PressRelease/ReleaseCalendar/`

Existing governance correctly separates its factual/provenance value from automated endpoint permission:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `automated_retrieval_permission = NOT_EXPRESSLY_GRANTED_REVIEW_REQUIRED`
- `monitoring_readiness_status = ENDPOINT_REVIEW_REQUIRED`

BX does **not** alter those fields and does not make automatic requests to that schedule page.

## Official RSS machine interface

NBS publishes a Chinese RSS subscription page:

`https://www.stats.gov.cn/wzgl/rss/202302/t20230217_1912859.html`

It states that the RSS service is provided so subscribers can rapidly learn the latest NBS statistical information and can **immediately and automatically obtain** relevant information. It identifies the native Latest Releases feed:

`https://www.stats.gov.cn/sj/zxfb/rss.xml`

This is materially different from inferring crawler permission from a general website page: NBS itself publishes a machine-oriented subscription interface and describes automatic acquisition as its purpose.

The English RSS subscription page similarly describes automatic acquisition, but its feed was not selected for production because the English translation surface can lag the native Chinese release and its whole RSS document was malformed during BX diagnostics.

## Content/reuse rights remain separate from machine access

NBS Terms of Service:

`https://www.stats.gov.cn/english/nbs/200701/t20070104_59236.html`

The terms permit download/use of statistical data and reasonable good-faith reprint/quotation of website material for news/free-public-information purposes with prominent attribution, subject to stated exclusions and restrictions.

BX therefore records two distinct propositions:

1. **machine access**: the native RSS endpoint is an expressly offered automatic subscription interface;
2. **content/reuse**: use remains subject to the NBS terms and attribution conditions.

The monitor stores/uses only minimal factual RSS metadata needed for identity and provenance. It does not republish article bodies and does not assert an unrestricted downstream redistribution licence.

This is an operational governance classification for WORLD SIGNALS, not a legal opinion.

## Diagnostics

### Pressure audit

Run `34254051956`, job `102155253630`: success; read-only; repository byte-clean.

### English RSS contract diagnostic

Run `34254262267`, job `102155970779`:

- official documentation page: HTTP 200;
- English RSS: HTTP 200, `text/xml`, 5,631,432 bytes;
- strict whole-document XML parse failed closed with a mismatched closing tag.

No production parser was weakened to accept the malformed document.

### English RSS structure diagnostic

Run `34254529792`, job `102156858693`: success.

- 500 `<item>` opens and 500 closes;
- 500 complete item fragments;
- 500/500 item fragments parsed independently;
- zero fragment failures;
- every item had the same child-field contract.

This showed that the defect was in the enclosing document structure, not individual items. That made a fragment parser technically conceivable, but technical recoverability did not establish that the English surface was the best semantic source.

### English RSS semantic diagnostic

Run `34254713440`, job `102157479852`: success.

The English titles expose regular series/reference-period identities for CPI, PPI, PMI and activity releases. However, the feed is a translation/publication surface that can post after the native Chinese release. BX therefore rejects it as the production publication sentinel rather than allowing convenient regexes to obscure the lag.

### Native Chinese RSS diagnostic

Run `34254908666`, job `102158115941`: success.

Single request to:

`https://www.stats.gov.cn/sj/zxfb/rss.xml`

Observed:

- HTTP 200;
- `text/xml`;
- 4,496,148 bytes;
- SHA-256 `b15a457fffcba22c65104d35e1c2dfa9021c6c8ec1b47034c153a152c3db12e7`;
- strict whole-document XML parse succeeded;
- exactly 500 items in the live snapshot;
- 500/500 item fragments parse;
- zero item-fragment failures;
- one stable item child contract:
  `title, channel, link, source, pubTime, pubDate, description, content, docId, hitCount`.

Historical native items demonstrate deterministic identities for the configured series. Examples include:

- CPI: `2026年7月份居民消费价格同比上涨0.5%`;
- PPI: `2026年7月份工业生产者出厂价格同比上涨3.5%`;
- PMI: `2026年8月中国采购经理指数运行情况`;
- industrial value added: `2026年7月份规模以上工业增加值增长4.5%`;
- energy: `2026年7月份能源生产情况`;
- fixed-asset investment: `2026年1—7月份全国固定资产投资基本情况`;
- real-estate activity: `2026年1—7月份全国房地产市场基本情况`;
- retail sales: `2026年1—7月份社会消费品零售总额增长1.2%`;
- National Economic Performance uses variable prose but a bounded period prefix plus `国民经济` (for example `1—7月份国民经济...`, monthly forms, and quarter/half-year forms).

## Identity contract

Production mapping is not fuzzy-title similarity.

Each configured Canonical occurrence has an exact tuple:

`(series_key, reference_year, reference_month)`

The parser classifies only bounded native-title forms for:

- `CPI`
- `PPI`
- `PMI`
- `NEP`
- `IP`
- `ENERGY`
- `FAI`
- `REALESTATE`
- `RETAIL`

For NEP titles that do not print a year, the year is taken from the RSS publication metadata **for identity matching only**. This does not make RSS publication time/date Canonical event-time authority.

A relevant item that maps ambiguously or duplicates a configured identity fails closed. Unrecognised items remain outside configured scope observations rather than being coerced into a series.

## Publication metadata is not Canonical timing authority

The feed contains `pubTime` and `pubDate`. Historical target items often align closely with the NBS scheduled release time, but BX deliberately does not promote that empirical alignment into an authority claim.

The RSS fields are publication metadata only. They may support an exact publication-evidence review candidate. They may **not** automatically:

- alter `start_local` or `start_utc`;
- upgrade time precision;
- reschedule an occurrence;
- mark an occurrence completed;
- change certainty;
- imply cancellation, delay, or completion from absence.

Forward date/time authority remains `WSSRC-MAC-007` and its already-recorded Canonical provenance.

## Network boundary

Production route budget: exactly one native RSS request per run.

Automatic follow-ups are prohibited:

- no annual release-calendar request;
- no English RSS request;
- no article-link request;
- no NBS data API request;
- no PDF request;
- no news/search route discovery.

The 4.5 MB live feed is large, so cadence remains daily rather than aggressive polling. The endpoint is treated as a finite rolling feed; absence of a configured future identity carries no event-state meaning.

## Expected governed transition

If all later gates pass:

- Canonical Registry: v0.41 / 689 — unchanged;
- Sources: v1.96 / 252 → v1.97 / 253;
- Monitor expectations: v0.21 / 19 → v0.22 / 20;
- Change Ledger — unchanged;
- Biosecurity — unchanged;
- Live Intelligence — unchanged;
- Analysis — unchanged;
- automatic Canonical commit — OFF;
- Google Calendar writes — OFF.

The architecture, not East Asia route count, is the reason for activation.
