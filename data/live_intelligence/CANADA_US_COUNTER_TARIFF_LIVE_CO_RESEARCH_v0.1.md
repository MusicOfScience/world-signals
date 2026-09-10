# WORLD SIGNALS — Canada counter-tariff Live CO research v0.1

**Status:** RESEARCH FROZEN / DESIGN ONLY / NO GOVERNED WRITE  
**Reference date:** 2026-09-10  
**Exact post-CN base main:** `b2b9e85933dd1c5924af1228f47427d6b38bf967`  
**Branch:** `feature/post-cn-canada-us-trade-live-co`

## Selection pressure

The post-CN cross-layer audit leaves Europe and North America as regions with Canonical series but no Live observation. Those are qualitative prompts only, not quotas. CO does **not** select Canada merely to remove a North America zero.

Canada's 8 September 2026 counter-tariff implementation is selected because it is a current, primary-source-verifiable trade-policy action with material cross-domain relevance: trade policy, industrial exposure, bilateral political-economic tension and import-cost transmission. It also exercises a useful Live distinction between a policy **implementation** and a later sovereign response by another government.

The U.S. 8 September proclamations are not folded into the same observation. They are distinct U.S. sovereign acts with their own effective dates and remain separately reviewable future Live candidates.

## Canonical identity probe

The exact post-CN Canonical Registry remains v0.42 / 689 occurrences. Identity-aware review found Canadian Bank of Canada and sovereign-financing occurrences but no Canonical occurrence representing the 8 September 2026 Canadian counter-tariff implementation. Literal search also found no existing `counter-tariff` occurrence.

CO therefore must **not create a Canonical occurrence** simply because the countermeasure had a previously announced effective date. The Live observation will carry zero Canonical links.

## Primary official evidence

### 1. Department of Finance Canada — tariff scope and effective date

Title: `List of products from the United States subject to counter-tariffs effective September 8, 2026`  
URL: `https://www.canada.ca/en/department-finance/news/2026/08/list-of-products-from-the-united-states-subject-to-counter-tariffs-effective-september-8-2026.html`

The Government of Canada archived-news index records this backgrounder on **2026-08-25**. The page states that:

- Canada will impose counter-tariffs of **15%, 25% and 50%**;
- covered products correspond to goods targeted by U.S. Section 338 and Section 232 tariffs, with individual rates based on the matching U.S. rate;
- the counter-tariffs apply to products covering **$27.6 billion** in imports from the United States;
- affected sectors include steel, dairy, appliances, agricultural equipment, pulp and paper, and electronics;
- the measures are effective as of **12:01 a.m. on 2026-09-08**;
- the list was updated as of 2026-08-26.

The reviewed Finance page does **not** establish an IANA timezone for the displayed `12:01 a.m.` effective clock time. CO therefore preserves the real-world event at `CIVIL_DATE` precision rather than fabricating an exact UTC timestamp.

### 2. Canada Border Services Agency — operative border application

Title: `Customs Notice 26-23: United States Surtax Order (2026)`  
URL: `https://www.cbsa.gc.ca/publications/cn-ad/cn26-23-eng.html`

The notice is dated **Ottawa, 2026-09-07** and states that:

- the United States Surtax Order (2026) applies to certain U.S.-origin goods **effective 2026-09-08**;
- applicable surtaxes are 15%, 25% or 50% of value for duty according to the Order;
- the CBSA administers the Order;
- the measure applies to commercial and casual imports subject to the listed rules and exceptions.

A separate current CBSA traveller page states that **as of 2026-09-08** the Government of Canada has imposed counter-tariffs of 15%, 25% or 50% on certain U.S.-origin goods. This is useful post-effective-date corroboration, but CO does not need a third production evidence row merely to increase evidence count.

### 3. Order in Council — legal instrument context

Order-in-Council P.C. **2026-0785**, dated **2026-09-04**, makes the `United States Surtax Order (2026)` under the Customs Tariff. Its coming-into-force clause states 2026-09-08, unless registration occurs after that date, in which case registration controls.

CO does not rely on that conditional clause alone to assert implementation. The CBSA's operative 7 September notice and current post-effective-date guidance establish application from 8 September for the bounded Live claim.

The Order-in-Council is retained in research as legal context and is not required as an additional Live evidence row.

## U.S. response deliberately separated

The White House issued multiple proclamations on **2026-09-08** responding to Canada's retaliation. The White House fact sheet describes five Section 338 proclamations; separate proclamations impose or modify U.S. restrictions, with some import bans taking effect on **2026-09-29**.

These are not evidence for the proposition that *Canada implemented its counter-tariffs*. They are a separate sovereign development. CO therefore does not:

- combine Canadian and U.S. actions into one observation;
- describe a bilateral sequence as a single event identity;
- create a `CONFLICTING_REPORTS` state merely because the governments characterize the dispute differently;
- choose which government's legal/political characterization is correct;
- create a manual story identity before a story-grouping pressure audit demonstrates that it is needed.

## CO Live design

One production observation:

- observation ID: `WSLI-TRD-CAN-US-SURTAX-20260908-001`;
- type: `POLICY_DEVELOPMENT`;
- verification: `PRIMARY_CONFIRMED`;
- jurisdiction: Canada;
- region: North America;
- domain tags: `TRADE`, `ECONOMICS`, `GEOPOLITICS`;
- Canonical links: 0;
- event time: `CIVIL_DATE` 2026-09-08;
- revision/correction target: none;
- story ID: none.

Two primary-official Live evidence rows:

1. Department of Finance Canada backgrounder, publication date 2026-08-25;
2. CBSA Customs Notice 26-23, publication date 2026-09-07.

Target governed Live state:

- schema/data version: `0.11`;
- observations: **10**;
- evidence rows: **14**;
- Canonical-linked observations: **3**.

## Claim boundary

CO may state that Canada implemented/applied 15%, 25% and 50% counter-tariffs on listed U.S.-origin goods from 8 September 2026 and that the Department of Finance describes the covered import value as $27.6 billion.

CO must not state or imply that:

- all $27.6 billion of imports face a single 50% rate;
- the source-established `12:01 a.m.` is an exact UTC timestamp;
- the counter-tariffs caused a quantified price, inflation, trade-flow, currency, equity or market movement;
- the White House's 8 September response is part of the Canadian sovereign act;
- either government's characterization of discrimination, retaliation, fairness or legality is an independent WORLD SIGNALS conclusion;
- a Canonical occurrence, Monitor route, Analysis review or public feed is created by this Live evidence.

## Protected boundary

CO must leave unchanged:

- Canonical Registry and schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- Monitor expectations and operations policy;
- Analysis schema, reviews and evidence registry;
- OPEC quarantine document and quarantine regression test.

Automatic Canonical commit, Google Calendar write, automatic Live ingestion and public Live projection remain closed.
