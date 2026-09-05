# WORLD SIGNALS — Cross-domain Analysis V research v0.1

**Base main:** `1bfa947d1fbd86e945349991778944094a78e5ed`  
**Canonical checkpoint:** v0.30 / 681 occurrences  
**Analysis pre-state:** reviews v0.4 / 8; evidence v0.4 / 21  
**Reference date:** 2026-09-06

## Purpose

Historical-anchor tranche U deliberately expanded the completed-event frontier without immediately reviewing every newly eligible occurrence. V now stress-tests the Analysis contract against three materially different completed anchors:

1. biological-security treaty negotiations;
2. animal-health standards governance with trade and food-system transmission;
3. a national fiscal-process occurrence whose exact date exists only in the competent jurisdiction's native civil calendar.

The Bank of Canada 2 September decision remains eligible but unreviewed. V does not treat backlog closure as an analytical objective.

## Pre-state discovery

A read-only probe on exact post-PR #50 main confirmed:

- canonical registry: v0.30 / 681;
- Analysis reviews: v0.4 / 8;
- Analysis evidence: v0.4 / 21;
- 12 canonical occurrences have lifecycle `COMPLETED`;
- 8 are reviewed;
- the three U anchors plus the Bank of Canada decision are the unreviewed completed frontier.

The probe also exposed a public-projection gap. `public_analysis_projection()` currently emits only Gregorian/local start fields in its canonical context. A source-native date such as Nepal's `15 Jestha 2083` would therefore appear in Analysis with null Gregorian/local timing and without its actual canonical temporal semantics. V treats that as a read-only projection defect, not as permission to convert the date.

## Specimen 1 — BWC Working Group, eighth session

Canonical occurrence: `WSO-BWC-WG-2026-S08`  
Series: `WSER-INT-BWC-WG-STRENGTHENING`  
Event type: `TREATY_WORKING_GROUP_SESSION`  
Canonical category: `INTERNATIONAL_INSTITUTIONS`

### Pre-session benchmark

Official BWC/UNODA revised draft working material before the session restated the Ninth Review Conference mandate: the Working Group is to identify, examine and develop measures, including possible legally binding measures, and make recommendations to strengthen and institutionalise the Convention.

Source:

- `BWC/WG/8/CRP.1/Rev.2`, 7 February 2026
- https://docs-library.unoda.org/Biological_Weapons_Convention_-Working_Group_on_the_strengthening_of_the_ConventionEighth_session_%282026%29/BWC_WG_8_CRP1_Rev1_2.pdf

The document is a negotiating draft. Coloured/revised text and material carried from earlier sessions are not equivalent to a final substantive agreement.

### Post-session outcome evidence

Official procedural material records that the eighth session met 9–13 February 2026, held ten meetings and continued substantive work under the strengthening mandate. A further revision was issued at the tenth meeting **without prejudice to future discussions**. The procedural report itself was adopted by consensus.

Source:

- `BWC/WG/8/CRP.2`, 13 February 2026
- https://docs-library.unoda.org/Biological_Weapons_Convention_-Working_Group_on_the_strengthening_of_the_ConventionEighth_session_%282026%29/BWC_WG_8_CRP_2.pdf

### Analytical treatment

- `what_was_expected`: official institutional mandate, not a market forecast;
- surprise: `NOT_ESTABLISHED` — there is no defensible ex-ante benchmark for how much substantive convergence the eighth session should have achieved;
- `what_moved: []` — no asset-price reaction is required for a high-importance treaty-governance event;
- connection: `STRUCTURAL_DEPENDENCY` / `NOT_A_CAUSAL_CLAIM` / HIGH — the session is structurally part of the mandated multi-session strengthening process;
- noise guard: revised negotiating text is not promoted into a final substantive consensus outcome;
- second-order effects: `NOT_ESTABLISHED` — later treaty outcomes remain contingent on subsequent sessions, states' positions and eventual Review Conference decisions.

## Specimen 2 — WOAH 93rd General Session

Canonical occurrence: `WSO-WOAH-GS-093`  
Series: `WSER-AGF-WOAH-GENERAL-SESSION`  
Event type: `GOVERNANCE_ASSEMBLY_SESSION`  
Canonical category: `AGRICULTURE_FOOD`

### Pre-session benchmark

WOAH's provisional programme set out an adoption agenda rather than an asset-market expectation. It scheduled presentation/adoption of the 8th Strategic Plan and consideration/adoption of international standards and resolutions across the Terrestrial and Aquatic Codes and Manuals.

Source:

- WOAH 93rd General Session provisional programme, version 24 April 2026
- https://www.woah.org/app/uploads/2026/03/gs93-wd-adm-01-programme-en.pdf

### Official outcomes

WOAH's official General Session material reports that the 18–22 May Assembly adopted 35 resolutions and 51 international standards, alongside official disease-status/control-programme decisions. On 20 May the Assembly adopted WOAH's 8th Strategic Plan for 2027–2031.

Sources:

- https://www.woah.org/en/event/93rd-general-session-of-the-world-assembly-of-delegates/
- https://www.woah.org/en/woah-8th-strategic-plan-adopted-for-2027-2031/

### Analytical treatment

- surprise: `NO_CLEAR_SURPRISE` — the broad adoption agenda occurred, but no defensible pre-event forecast established an expected count of resolutions or standards;
- exact realised counts are facts, not automatically an `UPSIDE` surprise;
- `what_moved: []` — institutional importance does not require a discrete market response;
- connection: `STRUCTURAL_DEPENDENCY` / `NOT_A_CAUSAL_CLAIM` / HIGH — the World Assembly is the formal governance locus for these standards and strategic decisions;
- canonical category remains `AGRICULTURE_FOOD`; One Health, biosecurity and zoonotic-risk relevance remain cross-domain analytical context rather than a category rewrite;
- second-order status: `PLAUSIBLE_WATCH_ITEM` — the Strategic Plan takes effect from 2027 and implementation depends on subsequent roadmaps, monitoring, member adoption, capacity and resources. Those prospective effects are not yet observed outcomes.

## Specimen 3 — Nepal Federal Budget 2083/84 presentation

Canonical occurrence: `WSO-FIS-NP-BUDGET-2083`  
Series: `WSER-FIS-NP-FEDERAL-BUDGET`  
Event type: `FISCAL_POLICY_PROCESS`  
Canonical timing: `SOURCE_NATIVE_CALENDAR_DATE`

### Legal expectation

Article 119(3) of Nepal's Constitution requires the Finance Minister to present annual revenue and expenditure estimates to the Federal Parliament on the fifteenth day of Jestha every year.

Source:

- Nepal Law Commission, Constitution of Nepal, Article 119
- https://lawcommission.gov.np/content/13437/nepal-s-constitution/

The legal rule establishes a source-native recurring date. It does not, for this occurrence, provide an authoritative Gregorian conversion or clock time.

### Official outcome

Nepal's Ministry of Finance publishes the Budget Statement for FY2083/84 with the source-native date `15 Jestha 2083`.

Source:

- https://mof.gov.np/content/1741/budget-statement-for-the-financial-year-2083-84/

A CMS publication clock exposed by the Ministry site is not the constitutional presentation time and is not promoted into canonical or analytical event timing.

### Later fiscal-cycle observation

The Ministry of Finance's official Appropriation Act archive lists the Appropriation Act 2083 on `7 Saun 2083`.

Source:

- https://mof.gov.np/category/allocation-act/?page=1

This is retained as an observed later legal/fiscal-cycle development. It does not prove that the presentation alone caused enactment and it does not reconstruct omitted parliamentary milestones.

### Analytical treatment

- expectation benchmark: the constitutional recurring rule, represented as `OTHER_DEFENSIBLE_EXPECTATION` rather than market consensus;
- surprise: `NO_CLEAR_SURPRISE` — the observed source-native date matches the legal recurring rule;
- `what_moved: []` — no market series is manufactured;
- connection: `LEGAL_OR_OPERATIONAL_DEPENDENCY` / `NOT_A_CAUSAL_CLAIM` / HIGH;
- noise guards: no third-party Gregorian conversion, no CMS-clock substitution, no duplicate event inferred from later English-language files;
- second-order status: `OBSERVED` for the later Appropriation Act listing, while explicitly withholding causal attribution and any synthetic process reconstruction.

## Public Analysis temporal projection repair

V should extend only the read-only Analysis canonical context so it preserves temporal semantics already present upstream. The generic projection should expose:

- `timing_type`;
- `time_precision`;
- `start_local` / `end_local`;
- `start_utc` / `end_utc`;
- `source_timezone`;
- `source_native_date_label`;
- `native_calendar_system` / year / month / day;
- `gregorian_resolution_status`;
- `publication_time_semantics`.

The Analysis UI should then display source-native dates as source-native dates and multi-day ranges as ranges. It must never derive a Gregorian date from Nepal's native date.

## Proposed post-state

If the three packets and projection repair validate:

- canonical: v0.30 / 681 — unchanged;
- Analysis schema: v0.2 — unchanged;
- Analysis reviews: v0.5 / 11;
- Analysis evidence: v0.5 / 29;
- Analysis canonical checkpoint: v0.30 / 681;
- eligible completed occurrences: 12;
- reviewed occurrences: 11;
- reviewed event-type diversity: 10;
- remaining eligible unreviewed occurrence: Bank of Canada `WSO-ddb70f8ff05a58fb` only;
- broad state remains `READY_FOR_CONTROLLED_EXPANSION`.

No canonical, source, monitor, change-ledger, biosecurity or calendar mutation is authorised by V. Automatic canonical commit remains OFF and Google Calendar writes remain OFF.
