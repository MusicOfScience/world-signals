# WORLD SIGNALS — Post-AA pressure audit AB v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `c4b499436db54f6dc3ebbe045cfda2fba7f730dd`  
**Canonical:** v0.31 / 681  
**Analysis:** schema v0.3; reviews v0.8 / 12; evidence v0.8 / 44

## Purpose

AB is a read-only post-AA pressure audit. It asks what AA actually repaired, what material gaps remain, and whether the two completed-but-unreviewed occurrences are genuinely the best next work. It is not a quota engine and does not mutate canonical, source, monitor, Analysis or Calendar data.

## What AA repaired

- East Asia completed-anchor gap repaired: **True**
- East Asia now represented in reviewed Analysis sample: **True**
- `FISCAL_FINANCING_EVENT` now reviewed: **True**
- reviewed completed occurrences: **12 / 14**
- reviewed event-type diversity: **11**

## What remains material

- completed-anchor region gaps: none
- completed-anchor category gaps: CLIMATE_ENVIRONMENT, CORPORATE_FINANCIAL_MARKET_STRUCTURE, ELECTIONS_GOVERNANCE, FINANCIAL_STABILITY_REGULATION, HEALTH_BIOSECURITY, PHYSICAL_CLIMATE_RISK, TRADE_SANCTIONS_INDUSTRIAL_POLICY
- completed-anchor event-type gaps: ELECTION_MILESTONE, ENVIRONMENTAL_GOVERNANCE_EVENT, FINANCIAL_STABILITY_POLICY_EVENT, FINANCIAL_STABILITY_REPORT, FISCAL_PROCESS, HEALTH_GOVERNANCE_EVENT, INDUSTRIAL_TRADE_POLICY_PROCESS, INFORMATION_CATALYST_MEETING, INSTITUTIONAL_MEETING, LEADERSHIP_TRANSITION_PROCESS, LEGISLATIVE_FISCAL_POLICY_SESSION, LEGISLATIVE_SESSION_OPENING, MARKET_STRUCTURE_EVENT, MEETING, MONETARY_POLICY_REFERENCE_RATE_PUBLICATION, PHYSICAL_RISK_WINDOW, POLITICAL_CONSULTATIVE_SESSION, POLITICAL_DECISION_PROCESS, PRESS_CONFERENCE, PRODUCER_POLICY_MEETING, PRUDENTIAL_STANDARD_EFFECTIVE_DATE, PUBLICATION, SANCTIONS_PROCESS, SCIENTIFIC_ASSESSMENT_RELEASE, SECTORAL_MINISTERIAL_MEETING, SYSTEMIC_TAX_REFORM_IMPLEMENTATION_BOUNDARY, TRADE_POLICY_PROCESS
- exact-timestamp market rows: **0**
- source-reported/session-level market rows: **8**

The absence of exact-timestamp market evidence remains a measurement gap, not permission to manufacture event times or reconstruct market data from incomplete reporting.

## Remaining completed frontier

- `WSO-ddb70f8ff05a58fb` — Bank of Canada policy interest rate announcement — 2026-09-02 — North America / MONETARY_FINANCIAL_POLICY / DECISION; new region=True, category=False, event type=False, institution=True
- `WSO-MAC-B-0041` — Japan Family Income and Expenditure Survey — July 2026 — East Asia / MACROECONOMIC_RELEASE / DATA_RELEASE; new region=False, category=False, event type=False, institution=True

### Frontier interpretation

Bank of Canada has greater marginal sample novelty than Japan household spending because North America still lacks a reviewed specimen. But neither frontier item repairs a missing completed category or event type. Household spending is particularly duplicative: East Asia is now reviewed, and `MACROECONOMIC_RELEASE` / `DATA_RELEASE` are already well exercised.

## Evidence diagnostics

- referenced evidence rows: **44**
- primary-official share: **61.4%**
- largest single provider: **Reuters** — 10 rows / 22.7%

Provider concentration remains descriptive only; it is not a source-quality quota.

## Selection recommendation

1. **First compare upstream historical anchors in still-missing completed categories/event types.** Prefer an existing canonical series with strong first-party post-event evidence over inventing new history.
2. **Keep Bank of Canada live as the strongest frontier candidate.** Promote it only if research can add distinct value — especially defensible high-frequency market measurement or a North America-specific analytical pressure test.
3. **De-prioritise Japan household spending for now.** It is valid but low marginal diversity after AA.
4. Re-audit again before any broad/full-population move. Queue exhaustion is not a research objective.

AB therefore recommends **upstream category/event-type reconnaissance before the next Analysis write**.
