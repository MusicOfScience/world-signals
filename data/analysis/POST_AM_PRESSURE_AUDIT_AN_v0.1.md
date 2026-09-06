# WORLD SIGNALS — Post-AM pressure audit AN v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `d9dc06da84608f74297f94c426ab77706d9223e0`  
**Architecture position:** Analysis selection/methodology audit  
**Mutation policy:** read-only selection audit; no canonical, source, ledger, overlay, monitor, Calendar, Analysis-review or Analysis-evidence mutation

## Verified post-AM checkpoint

- Canonical registry: **v0.37 / 687**
- Source registry: **v1.78 / 242**
- Change ledger: **v0.24 / 59**
- Biosecurity overlay: **v0.12 @ canonical v0.37 / 687**
- Monitor expectations: **v0.9**
- Analysis schema: **v0.4**
- Analysis reviews: **v0.11 / 15**
- Analysis evidence: **v0.11 / 59**
- completed Analysis-eligible occurrences: **20**
- reviewed occurrences: **15**
- reviewed event-type diversity: **13**
- production `EXACT_TIMESTAMP_SERIES` rows: **0**
- completed-but-unreviewed frontier: **5**

## Remaining choice set

| Occurrence | Category / event type | Marginal value after AM |
| --- | --- | --- |
| `WSO-EL-KR-LGE-20260603` | ELECTIONS_GOVERNANCE / ELECTION_MILESTONE | first reviewed election milestone; East Asian political-process coverage; tests aggregation, expectation and election-administration boundaries |
| `WSO-CLIM-UNFCCC-SB64-202606` | CLIMATE_ENVIRONMENT / ENVIRONMENTAL_GOVERNANCE_EVENT | first reviewed climate-governance type; strong global specimen, but overlaps the non-market institutional-process contract already exercised by W |
| `WSO-HEALTH-WHA-079` | HEALTH_BIOSECURITY / HEALTH_GOVERNANCE_EVENT | first reviewed health-governance type; strong first-party outcomes, but also substantially overlaps W's institutional-process semantics and remains WHO-concentrated |
| `WSO-TRD-EU-RU-SANC-20260625` | TRADE_SANCTIONS_INDUSTRIAL_POLICY / SANCTIONS_PROCESS | clean legal-policy act and novel type, but another European specimen and lower geographic corrective value |
| `WSO-MAC-B-0041` | MACROECONOMIC_RELEASE / DATA_RELEASE | useful Japanese institutional novelty but repeats a well-exercised macro/data-release contract |

The set remains a **choice set, not a backlog**. Nothing in this audit creates a requirement to exhaust it in order or to fill taxonomy histograms mechanically.

## Schema-pressure check

The four institutionally novel remaining specimens are compound objects rather than single-number releases. This raised a legitimate question: does the Analysis schema's single top-level `what_surprised.status` force multidimensional outcomes into a synthetic average?

Current evidence does not justify another schema migration. The existing Bank of Canada reviewed specimen already demonstrates that `MIXED` can be decomposed into explicit comparison rows: a headline decision may match expectations while a guidance/path dimension surprises. The validator requires a comparison basis for directional/MIXED classifications, while `NOT_ESTABLISHED` remains valid when no defensible benchmark exists.

Therefore AN keeps Analysis schema **v0.4**. A future schema change should require demonstrated representational failure, not merely the existence of compound events.

## Selection — South Korea, 3 June 2026 local elections

AN selects `WSO-EL-KR-LGE-20260603`, the **9th Nationwide Simultaneous Local Elections** administered by the National Election Commission of the Republic of Korea.

This specimen has the highest marginal value after AM because it tests three analytical boundaries not yet exercised together:

1. **Aggregation boundary.** The canonical occurrence is a nationwide simultaneous electoral process containing many mayoral, gubernatorial, council, education and related contests. It is not a plebiscite and must not be converted into a synthetic single national winner, vote share or mandate.
2. **Expectation boundary.** Pre-election polling and analyst commentary clearly pointed to severe pressure on the conservative People Power Party, but they do not constitute a defensible forecast of an exact 12-of-16 mayoral/provincial result. A post-vote exit poll is observation context, not a pre-event benchmark.
3. **Institutional-consequence boundary.** Ballot-paper shortages during the election subsequently produced protests, leadership consequences, investigation and reform pressure. Those effects are analytically connected to election administration, not evidence that the reported electoral winners were automatically invalid or that an election-management failure caused the partisan result.

The selection also adds an East Asian political-process specimen rather than defaulting to another European or North American institutional event.

## Current external evidence reconnaissance

### Authoritative election identity and administration

National Election Commission material establishes the 3 June 2026 election date and nationwide simultaneous-local-election process. The existing canonical AG anchor already preserves the event as a source-local civil date in `Asia/Seoul`, day precision, with no synthetic UTC instant and no promotion of polling hours or early voting into the canonical occurrence.

Existing canonical source family:
- National Election Commission election calendar and event-specific schedule material;
- canonical occurrence `WSO-EL-KR-LGE-20260603`;
- canonical series `WSER-EL-KR-LGE`;
- source `WSSRC-EL-KR-001`.

### Results

Reuters (3/4 June 2026) reports that the ruling Democratic Party won **12 of 16** major mayoral/provincial contests, while the People Power Party won four, including incumbent Oh Se-hoon's retention of Seoul; the Democratic Party won Busan.

- https://www.reuters.com/world/asia-pacific/south-korea-ruling-party-sweeps-most-seats-local-elections-faces-losing-seoul-2026-06-03/
- corroboration: https://en.yna.co.kr/view/AEN20260602008360315

This is a defensible aggregate description of one contest class. It is **not** a single national election result and does not subsume the many other local offices elected on the same day.

### Pre-election expectation context

Reuters on 8 May reported that analysts expected a severe conservative defeat; the PPP entered the election controlling 12 of 16 major local governments, while late-April Gallup Korea party support was reported at DP 46% versus PPP 21%, with President Lee at 64%.

- https://www.reuters.com/world/asia-pacific/south-korea-heads-local-elections-under-shadow-disgraced-former-president-2026-05-08/

That establishes directional political context, not an exact seat forecast. AN must not infer that 12 DP victories were the consensus number.

The joint broadcasters' exit poll after voting projected the DP ahead in 11 of 16 major races and projected a DP Seoul win. Because the exit poll is post-voting observation, it must not be used as the event's pre-election expectation benchmark.

- https://www.reuters.com/world/asia-pacific/south-koreans-vote-local-elections-seen-gauge-president-lees-first-year-2026-06-03/

### Ballot-paper shortage and observed institutional consequences

The National Election Commission later reported that additional ballots were actually used at **91 polling stations**, and voting was temporarily suspended then resumed at **26**. It established an investigation into ballot supply and election management.

- NEC material surfaced through the official NEC document viewer and subsequent NEC-reported figures;
- Yonhap report reproducing the NEC's 8 June findings: https://www.yna.co.kr/view/AKR20260608178651001

Reuters documents the subsequent chain:
- shortages and immediate protests: https://www.reuters.com/world/asia-pacific/shortage-ballot-papers-sparks-protests-south-koreas-local-elections-2026-06-04/
- sustained protests, NEC-chief resignation and public-confidence effects: https://www.reuters.com/world/asia-pacific/how-south-koreas-ballot-shortage-spurred-turnout-thousands-defend-democracy-2026-06-12/
- election-management reform demand: https://www.reuters.com/world/asia-pacific/south-koreas-lee-calls-overhaul-election-management-after-flawed-vote-2026-06-19/

These sources establish observed political/institutional consequences of the administrative failure. They do **not** establish that the partisan result was caused by the shortages, that fraud occurred, or that the nationwide election was legally void.

## Intended Analysis classification

Unless a controlled preflight identifies a stronger upstream defect, AN should use:

- `what_happened`: describe the distributed electoral outcome and separately the material election-administration failure;
- `what_was_expected`: directional pre-election political context only, using `OTHER_DEFENSIBLE_EXPECTATION`, not a fabricated seat consensus;
- `what_surprised.status = NOT_ESTABLISHED`: the broad DP gain was anticipated directionally, but no defensible pre-event exact distribution benchmark has been established;
- `what_moved = []`: no market response is required or manufactured;
- `what_appears_connected`: the ballot-shortage administration failure is connected to subsequent protest/institutional-response dynamics, while partisan election outcomes remain causally separate;
- `second_order_effects.status = OBSERVED`: protests, NEC leadership consequences, investigations and reform pressure occurred after the administrative failure;
- explicit alternatives, noise tests and falsifiers.

## Temporal and causal guardrails

- `CIVIL_DATE` election day **does not** acquire a midnight UTC event timestamp.
- Poll opening/closing hours **do not** replace the canonical day-level occurrence.
- Early voting **does not** convert the election-day occurrence into a multi-day window.
- Nationwide simultaneous elections **do not** imply a synthetic single national winner or mandate.
- Party-support polling **does not** imply an exact mayoral/provincial seat forecast.
- A post-vote exit poll **is not** a pre-event expectation benchmark.
- Ballot shortages **do not** establish fraud.
- Ballot shortages **do not** by themselves invalidate reported winners.
- Protest, resignation, investigation and reform pressure may be consequences of election administration without being consequences of the DP's 12-of-16 result.
- No market observation is required to make the election analytically consequential.
- Exact market-series population remains optional and **0 is valid**.
- Canonical, source, ledger, overlay, monitor and Calendar layers remain protected from AN Analysis writes.
- The remaining four completed/unreviewed occurrences stay legitimate later choices rather than compulsory backlog.
- No auto-merge.

## Decision

**Selected next tranche: South Korea local-election Analysis AN**, contingent on an exact-base read-only preflight confirming that the canonical occurrence, Analysis schema and protected upstream layers remain internally consistent at post-#68 `main`.