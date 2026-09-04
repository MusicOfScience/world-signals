# WORLD SIGNALS — P1-E source-governance research v0.1

**Research date:** 2026-09-04  
**Base checkpoint:** `fbd95ede5a02daebfa6271e101a2e006ae9ca4ac`  
**Source registry:** v1.56 / 223  
**Canonical registry:** v0.20 / 669  
**Monitor expectations:** v0.7

## Selection method

P1-E is a bounded six-source tranche selected from the measured post-P1-D P1 queue using canonical dependency, active horizon, source-scope integrity, regional breadth, domain diversity and governance-information value. It is not a mechanical top-N pass.

`WSSRC-CB-009` Swiss National Bank remains excluded despite its 18 canonical dependencies because the registered decisions/history URL does not directly support the forward assessment schedule. `WSSRC-EL-BR-001` Brazil TSE remains excluded pending provenance-scope repair.

Selected cohort:

| Source | Institution / surface | Dependencies | Jurisdiction / scope |
|---|---|---:|---|
| `WSSRC-CB-004` | ECB monetary-policy decisions/accounts publication surface | 11 | Euro area |
| `WSSRC-CB-005` | Bank of England upcoming MPC dates | 11 | United Kingdom |
| `WSSRC-MAC-025` | Japan Customs / Ministry of Finance trade-statistics release calendar | 8 | Japan |
| `WSSRC-MAC-011` | Australian Bureau of Statistics Consumer Price Index release surface | 6 | Australia |
| `WSSRC-CLIM-003` | Convention on Biological Diversity COP official site | 4 | Global |
| `WSSRC-REGJ-005` | Central Bank of Egypt MPC schedule | 3 | Egypt |

Total bounded dependency coverage: **43 canonical dependencies**.

## Source-specific findings

### `WSSRC-CB-004` — European Central Bank

Authoritative publication surface: `https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html`  
Rights evidence: `https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html`

The ECB publication surface directly supports monetary-policy decisions and linked monetary-policy accounts. The current ECB decisions page states that decisions are published at **14:15 CET** on the Governing Council monetary-policy meeting day. The accounts surface states that accounts are normally published about four weeks later and currently advertises the next account release separately. These are distinct occurrences and must remain distinct in the canonical model.

ECB website information obtained directly from the site may generally be used freely subject to source citation, accuracy and modification conditions, with exceptions such as authored papers. Those reuse terms do not expressly grant unrestricted automated website retrieval.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

### `WSSRC-CB-005` — Bank of England

Authoritative schedule: `https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates`  
Rights evidence: `https://www.bankofengland.co.uk/legal`

The current schedule distinguishes **2026 confirmed dates** from **2027 provisional dates**. That status must be ingested verbatim; provisional future dates must not be silently promoted to confirmed.

The Bank's general website legal terms allow Resources to be downloaded, displayed or printed for personal use or internal organisational non-commercial use unless more specific terms apply. Further reuse requires authorisation; the separately licensed statistical Database does not convert the general MPC schedule page into an open-reuse or automated-access source.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-MAC-025` — Japan Customs / Ministry of Finance

Authoritative calendar: `https://www.customs.go.jp/toukei/calendar/calend_e.htm`  
Rights evidence: `https://www.customs.go.jp/copyright_e.htm`

The official calendar explicitly says its dates are provisional and may change with notice. It also distinguishes publication stages and times: monthly provisional data at **08:50 JST** and detailed/revised/fixed stages at **09:30 JST**, with some later items marked TBD. WORLD SIGNALS must preserve those stage labels, provisional status and source-native JST times rather than collapsing them into a single generic trade release.

Japan Customs states that Ministry of Finance website content is subject to Public Data License 1.0 unless otherwise indicated. The licence supports factual reuse but does not itself specify crawler frequency or production polling behaviour. Existing parser/pilot evidence justifies a bounded automated-pilot verification mode only.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

### `WSSRC-MAC-011` — Australian Bureau of Statistics CPI

Authoritative product page: `https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia`  
Monitoring route already registered: `https://www.abs.gov.au/release-calendar/future-releases`  
Rights evidence: `https://www.abs.gov.au/website-privacy-copyright-and-disclaimer`

The current CPI page supplies future reference months, release dates and explicit **11:30am** local publication times, with AEST/AEDT changing according to the actual release date. Native timezone semantics must therefore be preserved; Melbourne/Sydney display conversion must not replace the source's Australia/Sydney canonical timezone.

ABS states that general website material is CC BY 4.0 subject to listed exclusions. The licence clears factual reuse but does not independently authorise unrestricted polling. Existing `abs-release-calendar-0.1` pilot evidence supports an automated-pilot verification mode with reviewed commits only.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `AUTOMATED_PILOT`

### `WSSRC-CLIM-003` — Convention on Biological Diversity COP

Authoritative event surface: `https://www.cbd.int/cop`  
Copyright notice: `https://www.cbd.int/copyright`  
General terms: `https://www.cbd.int/terms`

The current COP page identifies **COP 17 in Yerevan, Armenia, 19–30 October 2026**. The page gives a date range, not synthetic daily clock times; canonical precision must remain event-local/date-range unless a more specific official source supplies times.

CBD's legal regime is mixed. Its copyright page says official texts, data and documents are public domain with source acknowledgement and no content change. Its broader website Terms of Use, however, permit site Materials for personal non-commercial use and prohibit resale, redistribution and derivative compilation absent more specific permission. The COP webpage itself is a general site/event surface, so the narrower public-domain statement for official texts/data/documents is not stretched into blanket reuse or automation permission.

**Frozen classification:**
- `canonical_provenance_use`: `MANUAL_INFORMATIONAL_REFERENCE_ONLY`
- `automated_monitoring_use`: `PROHIBITED_OR_RIGHTS_HOLD`
- `verification_mode`: `RIGHTS_HELD_MANUAL_ONLY`

### `WSSRC-REGJ-005` — Central Bank of Egypt

Authoritative schedule: `https://www.cbe.org.eg/en/monetary-policy/mpc-meetings-schedule?verify=false`  
Rights evidence: `https://www.cbe.org.eg/en/disclaimer`

The CBE schedule is authoritative for MPC meeting/decision dates. The currently retrievable schedule surface supplies dates without a publication clock time, so WORLD SIGNALS must preserve date-only precision rather than infer a conventional announcement hour.

CBE's current disclaimer permits use of information obtained directly from the website subject to accurate reproduction, source citation and disclosure of user transformations. That is sufficient for curated factual provenance. It does not separately clear unrestricted automated retrieval.

**Frozen classification:**
- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

## Held-source controls

P1-E must leave both held records byte-identical and must not add modern governance fields to them:

- `WSSRC-EL-BR-001` — Brazil TSE; preserve the canonical `2027-01-05` presidential inauguration as constitutionally grounded.
- `WSSRC-CB-009` — Swiss National Bank; preserve the registered decisions/history URL until the forward-schedule provenance relationship is repaired.

## Transaction boundary

This research freezes a **candidate governance plan only**. It does not authorise a source-registry write by itself.

Any P1-E transaction must:

1. start from canonical v0.20 / 669, source v1.56 / 223 and monitor expectations v0.7;
2. change exactly the six selected source records and the source-registry version only;
3. advance source registry to v1.57 / 223;
4. preserve every non-P1-E source field;
5. preserve Brazil/TSE and SNB holds byte-identically;
6. preserve canonical and monitor files byte-identically;
7. leave automatic canonical commit false and Google Calendar writes false;
8. default to read-only simulation and require a separate explicit environment gate for apply.
