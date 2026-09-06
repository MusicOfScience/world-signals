# WORLD SIGNALS — South Korea local-election Analysis AN research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `d9dc06da84608f74297f94c426ab77706d9223e0`  
**Canonical target:** `WSO-EL-KR-LGE-20260603`  
**Layer:** Analysis only; upstream canonical/source/change state remains authoritative and protected

## Research question

How should WORLD SIGNALS analyse South Korea's 3 June 2026 nationwide simultaneous local elections without:

- inventing a single national winner or mandate from many local contests;
- turning broad pre-election political expectations into a synthetic seat forecast;
- using a post-vote exit poll as a pre-event benchmark;
- conflating election results with the separate ballot-paper administration failure;
- treating ballot shortages, protests or rerun demands as proof of fraud or automatic legal invalidity; or
- manufacturing an election-specific market response?

## Canonical object already established upstream

AG admitted the historical occurrence using stable identity and first-party completion evidence:

- occurrence: `WSO-EL-KR-LGE-20260603`;
- series: `WSER-EL-KR-LGE`;
- category: `ELECTIONS_GOVERNANCE`;
- subcategory: `local_government_election`;
- event type: `ELECTION_MILESTONE`;
- institution: National Election Commission of the Republic of Korea;
- jurisdiction / region: South Korea / East Asia;
- lifecycle: `COMPLETED`;
- timing: `CIVIL_DATE`, `2026-06-03`, `Asia/Seoul`, `DAY` precision, all-day semantics;
- `start_utc = null`, `end_utc = null`.

AN does not reopen that canonical decision. Polling hours, early voting or analytical reporting chronology may not supply a synthetic canonical clock time.

## First-party election completion anchor

National Election Commission Policy & Pledge portal:

- https://policy.nec.go.kr/plc/main/initUMAMain.do

The current NEC surface exposes elected-candidate/winner material for the 9th Nationwide Simultaneous Local Elections. It is competent first-party evidence that the election produced elected candidates. It does not convert the many contests into a single national partisan result.

The event-specific NEC schedule used upstream remains:

- https://www.nec.go.kr/site/nec/ex/bbs/View.do?bcIdx=294445&cbIdx=1084

AN cites the current winner portal only as official process/outcome context. Canonical provenance remains governed upstream; Analysis evidence has `canonical_provenance_effect = NONE`.

## Distributed election result

Reuters, 3/4 June 2026:

- https://www.reuters.com/world/asia-pacific/south-korea-ruling-party-sweeps-most-seats-local-elections-faces-losing-seoul-2026-06-03/

Reuters reports that President Lee Jae Myung's ruling Democratic Party won **12 of 16** major mayoral/provincial contests, while the opposition People Power Party won four. The PPP retained Seoul under incumbent Oh Se-hoon; the DP won Busan.

Yonhap corroboration, 4 June 2026:

- https://en.yna.co.kr/view/AEN20260602008360315

Yonhap likewise reports a 12–4 split across the 16 major mayoral/gubernatorial posts, DP victory in Busan and PPP retention of Seoul.

### Analytical interpretation

The 12–4 figure is an aggregate for one important contest class. It is not:

- a single nationwide vote tally;
- a national popular-vote result;
- the complete set of offices elected that day;
- a unitary legal outcome; or
- by itself evidence of a national policy mandate.

The canonical event is broader than those 16 contests. Local council, local executive, education and concurrent by-election outcomes remain distinct result objects inside or alongside the nationwide process.

## What was reasonably expected before voting

Reuters, 8 May 2026:

- https://www.reuters.com/world/asia-pacific/south-korea-heads-local-elections-under-shadow-disgraced-former-president-2026-05-08/

The report establishes a strong **directional** pre-election environment:

- the PPP controlled 12 of the 16 major local governments going into the election;
- analysts cited by Reuters expected the conservatives to suffer a severe/landslide defeat;
- late-April Gallup Korea party support was reported at DP 46% versus PPP 21%;
- President Lee's approval was reported at 64%;
- the political context included continuing fallout from former president Yoon Suk Yeol's martial-law attempt and conservative internal division.

This is defensible expectation context, but not an exact forecast that the DP would win 12 of 16, win Busan, lose Seoul, or achieve any specified distribution across individual contests.

AN therefore uses `OTHER_DEFENSIBLE_EXPECTATION` rather than pretending the political-environment evidence is a seat-by-seat consensus forecast.

## Exit poll is not a pre-event benchmark

Reuters, 3 June 2026:

- https://www.reuters.com/world/asia-pacific/south-koreans-vote-local-elections-seen-gauge-president-lees-first-year-2026-06-03/

The joint broadcasters' exit poll projected the DP ahead in 11 of 16 major mayoral/provincial contests and projected a DP victory in Seoul, with several races too close to call.

The final result differed in important detail, including PPP retention of Seoul and a final 12–4 major-contest split. But the exit poll was available **after voting**, not before the event. It therefore belongs in observation/noise context. It must not be promoted into `what_was_expected` as though market participants or voters possessed it ex ante.

## Ballot-paper administration failure

The later NEC accounting requires three distinct quantities.

Yonhap, reporting the NEC's 8 June findings:

- https://www.yna.co.kr/view/AKR20260608178651001

The NEC said:

- supplemental ballot papers were sent to **140 of 14,288** polling stations because shortages were expected;
- the supplemental papers were actually used at **91** polling stations;
- voting was temporarily interrupted and later resumed at **26** polling stations.

The NEC also established an external fact-finding committee to investigate ballot printing/allocation, supply management, polling-station operation, initial response and reporting systems.

These are election-administration facts. AN does not transform them into a claim that 91 results were invalid, that fraud occurred, or that the partisan result was caused by shortages.

## Observed institutional consequences

Reuters, 4 June 2026:

- https://www.reuters.com/world/asia-pacific/shortage-ballot-papers-sparks-protests-south-koreas-local-elections-2026-06-04/

Reuters documents immediate voter anger, extended voting at affected sites, protests around ballot boxes and calls for revotes. The NEC apologised and announced investigation while stating that the incidents did not themselves constitute grounds for delaying the election or holding a rerun.

Reuters, 12 June 2026:

- https://www.reuters.com/world/asia-pacific/how-south-koreas-ballot-shortage-spurred-turnout-thousands-defend-democracy-2026-06-12/

Reuters documents sustained protests, public-confidence damage, the resignation of NEC chief Rho Tae-ak and President Lee's investigation/reform response. It also records that the shortages were especially contentious in conservative-leaning areas and that claims of election fraud circulated. Those allegations are not adopted as factual findings by AN.

Reuters, 19 June 2026:

- https://www.reuters.com/world/asia-pacific/south-koreas-lee-calls-overhaul-election-management-after-flawed-vote-2026-06-19/

President Lee called for a major overhaul of election management and a thorough fact-finding process, including possible legal or constitutional reform if political agreement existed.

### Causal classification

The evidence directly connects the ballot-supply failure with protest, investigation, leadership consequences and reform pressure. AN can therefore treat the administration failure as an observed institutional trigger/context for those consequences.

However:

- this is not a causal estimate of partisan vote outcomes;
- the ballot shortages occurred unevenly across locations;
- other long-running controversies over the NEC and South Korean election administration predated 3 June;
- political actors had strategic incentives in how they framed the failure;
- legal validity of any individual contest requires competent legal/electoral determination.

`OBSERVED_ASSOCIATION` with explicit alternatives is therefore preferable to `CAUSAL_SUPPORT_STRONG`.

## Surprise decision

AN should use `what_surprised.status = NOT_ESTABLISHED`.

Reason:

- the broad direction — substantial DP gains and conservative losses — was anticipated;
- the final map contained meaningful details that diverged from the post-vote exit poll, especially Seoul;
- but the reviewed **pre-election** evidence does not establish an exact seat/distribution forecast suitable for classifying the overall result as UPSIDE, DOWNSIDE or MIXED surprise.

A result can be politically consequential and contain locally surprising races without WORLD SIGNALS inventing an aggregate forecast error.

## Market-response decision

AN should use `what_moved = []`.

The canonical event's intrinsic importance and expected market sensitivity do not compel an observed market row. South Korean equities, KRW, rates and regional markets were exposed to contemporaneous macroeconomic, geopolitical and policy drivers. Without event-specific defensible evidence, a market response would be manufactured rather than observed.

No `EXACT_TIMESTAMP_SERIES` data are required or populated.

## Proposed second-order classification

`second_order_effects.status = OBSERVED` is warranted **for election-administration consequences**, not for the partisan result.

Observed consequences include:

- protests and rerun demands;
- NEC leadership and senior-management consequences;
- formal investigation/fact-finding;
- pressure for legal/institutional overhaul;
- measurable deterioration in public confidence and a changed political debate about election administration.

The analytical summary must name the causal object accurately: these are consequences associated with the ballot-paper administration failure around the election, not consequences of 'the DP winning 12 of 16'.

## Alternatives and noise that must remain visible

- Seoul's PPP retention can reflect local incumbent/housing dynamics rather than contradicting the nationwide directional expectation.
- Busan and other reversals may reflect local candidates and regional political conditions as well as national party sentiment.
- The martial-law legacy, President Lee's approval, economic conditions, housing concerns and conservative party fragmentation all shaped the pre-election environment.
- Post-election protest mobilisation may reflect both the genuine administrative failure and pre-existing mistrust/conspiracy narratives around election administration.
- Calls for a nationwide rerun are political/legal demands, not proof that such a remedy is legally available or justified.
- A post-vote exit-poll miss in an individual race is not an ex ante surprise benchmark.
- No same-session market move should be reverse-engineered into an election reaction.

## Falsification / revision conditions

AN should be revised if:

1. the NEC issues corrected official results that materially alter the 12–4 major-contest aggregate or named Seoul/Busan outcomes;
2. a competent pre-election source is found with a defensible contest-by-contest or aggregate forecast against which the final distribution can be measured;
3. a court, NEC or other competent authority legally invalidates or reruns affected contests, requiring the outcome description to distinguish original reported result from later legal disposition;
4. the NEC's final investigation materially revises the 140 / 91 / 26 administration figures;
5. later evidence shows that the institutional-response chain was principally driven by a separate pre-existing NEC controversy rather than the June ballot-supply failure, requiring causal language to be narrowed;
6. credible event-window market evidence establishes a specific, separately identifiable election-result response; or
7. upstream canonical evidence changes the stable occurrence's lifecycle or timing semantics.

## Architecture decision

Existing Analysis schema v0.4 is sufficient. AN should be a controlled Analysis population tranche only.

Protected from AN mutation:

- Canonical Registry and canonical schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- monitor expectations and operations policy;
- Analysis schema;
- Calendar / Google Calendar.

The expected production mutation is one reviewed Analysis packet plus its Analysis-only evidence rows, with exact market-series population remaining zero.