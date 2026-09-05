# WORLD SIGNALS — South Korea local-election historical anchor AG research v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `3ebd01e1f6f3ba2b09343f238f3ac72262484391`  
**Architecture position:** upstream Canonical Registry historical-anchor repair; no Analysis write

## Why AG exists

After AF added the completed Australian tropical-cyclone seasonal risk window, a fresh exact-base reconnaissance found three canonical categories with forward coverage but no completed anchor:

- `CLIMATE_ENVIRONMENT` — 10 occurrences / 10 series / 7 institutions / 3 sources / 0 completed;
- `CORPORATE_FINANCIAL_MARKET_STRUCTURE` — 17 / 5 / 5 / 5 / 0 completed;
- `ELECTIONS_GOVERNANCE` — 26 / 12 / 12 / 14 / 0 completed.

The same probe found no past-starting non-terminal record in any of these categories. They are genuine historical-anchor gaps rather than another stale-lifecycle repair.

AG does not fill gaps FIFO. Candidate selection considers marginal architecture/analysis pressure, authoritative completion evidence, source quality, ontology cost, international balance and the risk of distorting the sample with mechanically repetitive events.

## Candidate comparison

### South Korea — 9th Nationwide Simultaneous Local Elections — selected

The 3 June 2026 South Korean nationwide local elections add a completed democratic electoral-process specimen in East Asia. They require a new historical series and a new official National Election Commission source identity, but **no taxonomy extension**:

- the repository already uses category `ELECTIONS_GOVERNANCE`;
- South Africa's future 2026 local-government election already establishes subcategory `local_government_election`;
- election-process occurrences already use event type `ELECTION_MILESTONE`;
- election day is already represented as a source-local `CIVIL_DATE` with `DAY` precision rather than as a synthetic polling-hours timestamp.

This is therefore controlled source/series expansion rather than ontology invention.

The specimen is also deliberately different from the completed East Asian anchors already present, which are Japanese sovereign-financing and household-statistics occurrences. Its value is political/institutional process diversity, not a regional quota.

### UNFCCC June Climate Meetings (SB64), Bonn — strong next candidate, deferred

UNFCCC first-party material records SB64 in Bonn from **8–18 June 2026** and states on 18 June that the meetings officially closed. This is a materially cleaner climate candidate than COP30 because the event window and closure are directly evidenced without the same conference-closing ambiguity.

However, the existing UNFCCC source `WSSRC-CLIM-001` is specifically the COP31 Antalya page with `Europe/Istanbul` source scope. SB64 would require a new subsidiary-bodies series and a new Bonn-specific source identity. Its taxonomy (`ENVIRONMENTAL_GOVERNANCE_EVENT`) is already available, but its institutional-meeting contract is closer to several completed non-market governance specimens already in the Analysis population.

SB64 remains a strong candidate after AG, particularly because `CLIMATE_ENVIRONMENT` will still lack a completed anchor.

### Corporate / market structure — deferred

The live category consists largely of futures-expiry/reconstitution mechanics plus later T+1 settlement transitions. Historical ASX/CME/index-review backfills would be easy to source, but choosing them merely to close the gap would risk over-weighting mechanical calendar events without adding equivalent analytical diversity.

This category remains important, especially for later work on liquidity, passive flows, settlement infrastructure and market microstructure. AG does not treat its deferral as evidence of low intrinsic importance.

## First-party South Korean election evidence

### Election date and legal/administrative schedule

National Election Commission — English election calendar:  
`https://www.nec.go.kr/site/eng/02/10203000000002020070611.jsp`

The NEC describes nationwide simultaneous local elections as a four-year cycle and lists the next election as **3 June 2026**. The generic English page still labels the date provisional, so AG does not rely on that page alone for final date certainty.

National Election Commission — event-specific detailed schedule notice:  
`https://www.nec.go.kr/site/nec/ex/bbs/View.do?bcIdx=294445&cbIdx=1084`

The NEC notice is titled `2026. 6. 3.(수) 실시 제9회 전국동시지방선거 사무일정` and was posted 4 August 2025. It provides the detailed administrative schedule for the **9th Nationwide Simultaneous Local Elections to be held on Wednesday 3 June 2026**.

National Election Commission — event-specific schedule card:  
`https://shipvote.nec.go.kr/site/vt/ex/bbs/View.do?bcIdx=298999&cbIdx=1147`

The NEC records candidate registration on 14–15 May, election-period commencement on 21 May, early voting on 29–30 May, and election-day voting on **3 June 2026 from 06:00 to 18:00**.

Those hours are **not** promoted into the canonical occurrence. The canonical object is the election-day civil-date milestone, matching existing WORLD SIGNALS election semantics. Early voting is a linked process phase, not a reason to stretch the canonical election-day occurrence backwards to 29 May.

### Post-event completion evidence

National Election Commission Policy & Pledge portal:  
`https://policy.nec.go.kr/plc/main/initUMAMain.do`

The current first-party NEC portal exposes `당선인공약` (winner pledges) for the **9th Nationwide Simultaneous Local Elections** and links users to pledges of winners from past elections. This is competent post-event evidence that the election occurred and produced winning candidates.

AG uses that current first-party post-event state to establish lifecycle `COMPLETED`. Completion is **not** inferred merely because 3 June has passed.

The nationwide local election comprises many offices and contests. The existence of winners must not be transformed into a synthetic single national winner, nationwide vote-share result or partisan mandate.

## Canonical temporal contract

Proposed historical occurrence:

- occurrence: `WSO-EL-KR-LGE-20260603`
- series: `WSER-EL-KR-LGE`
- name: `South Korea — 9th Nationwide Simultaneous Local Elections`
- category: `ELECTIONS_GOVERNANCE`
- subcategory: `local_government_election`
- event type: `ELECTION_MILESTONE`
- institution: `National Election Commission of the Republic of Korea`
- jurisdiction: `South Korea`
- region: `East Asia`
- intrinsic importance: `HIGH`
- expected market sensitivity: `MEDIUM`
- lifecycle: `COMPLETED`
- certainty: `CONFIRMED`
- timing type: `CIVIL_DATE`
- source-local date: `2026-06-03`
- source timezone: `Asia/Seoul`
- precision: `DAY`
- all-day semantics: `true`
- UTC: `null`.

A civil election date is not converted into a midnight UTC instant. The NEC polling hours remain supporting schedule detail rather than canonical start/end clock time.

## Election-process semantic guardrail

**Election-day milestone ≠ early-voting window ≠ individual local race ≠ result/certification milestone ≠ government formation ≠ policy implementation ≠ observed market response ≠ causal attribution.**

AG admits one national electoral-process occurrence because the NEC itself administers the event as the 9th Nationwide Simultaneous Local Elections. It does not create child occurrences for each mayoral, gubernatorial, council or education-superintendent contest.

If individual contests later become analytically material, they require separate stable identities and competent result evidence rather than being retrofitted into this anchor.

## Source-governance decision

New source identity: `WSSRC-EL-KR-001`.

The source represents the NEC's official event-specific schedule and post-event result/winner surfaces for the 9th Nationwide Simultaneous Local Elections. The authoritative schedule notice is the primary canonical date surface; the current NEC Policy & Pledge portal provides completion verification.

National Election Commission copyright policy:  
`https://www.nec.go.kr/site/nec/07/10702030000002020040802.jsp`

The NEC states that works for which it owns the full copyright may be freely used without separate permission when opened under the applicable public-work framework, but users must check for the relevant KOGL marking and provide source attribution. Material without a KOGL marking requires prior coordination with the responsible department.

The event-specific schedule notice itself carries a KOGL attribution / non-commercial / no-derivatives notice. AG therefore separates factual provenance from content-reuse and automation permission:

- factual election metadata may support the curated canonical registry;
- no protected page content is republished beyond minimal factual metadata;
- public accessibility and official status do not create a blanket crawler licence;
- production automation is not enabled by this tranche.

Frozen governance classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`.

## Expected post-state

If the reviewed AG transaction is admitted:

- canonical registry: v0.35 / 685 → **v0.36 / 686**
- source registry: v1.76 / 240 → **v1.77 / 241**
- change ledger: v0.22 / 57 → **v0.23 / 58**
- biosecurity overlay: v0.10 @ v0.35/685 → **v0.11 @ v0.36/686**, semantic content unchanged
- Analysis schema: **v0.3 unchanged**
- Analysis reviews: **v0.8 / 12 unchanged**
- Analysis evidence: **v0.8 / 44 unchanged**
- completed canonical Analysis population: 18 → **19**
- reviewed post-event population: **12 unchanged**.

After AG, `ELECTIONS_GOVERNANCE` and `ELECTION_MILESTONE` should be represented among completed canonical anchors/types. That does not make the election sample representative and does not create an obligation to exhaust the remaining two category gaps immediately.

PR #40 remains untouched. Manual merge only.
