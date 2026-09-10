# WORLD SIGNALS — post-CM pressure audit / CN selection v0.1

**Status:** READ-ONLY PRESSURE INTERPRETATION / CN SELECTED FOR FRESH POST-MERGE DESIGN  
**Reference date:** 2026-09-10  
**Exact CM base main:** `1e4a6bbc8670fc36a452740401461f28e313c031`  
**CM branch at selection:** descendant of guarded materialisation `aafaa2fb3ffe3acce54e587cb69b5d95bd9d9972`

## CM result

CM hardens the Live Intelligence correction/retraction/conflict grammar without changing production population:

- Live v0.9;
- 8 observations;
- 11 evidence rows;
- 3 Canonical-linked observations;
- no production `CONFLICTING_REPORTS`, `CORRECTED` or `RETRACTED` row;
- automatic ingestion and public Live projection remain closed.

The guarded transaction passed 1,276 historical tests with 68 historical-prestate skips. Ordinary PR validation also passed on the permanent CM state.

## Post-CM cross-layer audit

Read-only coverage run `34441643238` confirms the expected no-population result:

- Canonical: 689 occurrences / 203 series;
- Monitor: 26 adapters / 217 explicitly scoped occurrences / 48 series;
- Live: 8 observations / 3 Canonical-linked;
- Analysis: 22 reviews / 1 production Live input / 1 production revision;
- completed linked Live observations with an existing unused Analysis target: 0;
- completed linked Live observations without an Analysis review: 1 — PIF;
- linked observations whose Canonical target is not completed: 1 — BARMM pre-election context;
- unlinked Live observations: 5;
- zero-Live regional prompts: Europe, Latin America, North America;
- Monitor category prompts: `CLIMATE_ENVIRONMENT`, `HEALTH_BIOSECURITY`;
- Analysis category prompt: `CORPORATE_FINANCIAL_MARKET_STRUCTURE`.

Coverage artifact: `world-signals-coverage-audit-34441643238`  
Artifact digest: `sha256:d8c5c58e3e0c3160c1f8699db655586800ad1b5af247c6cad485aee3726dc38f`.

These remain prompts, not queues or quotas.

## Fresh candidate comparison

### Selected — Brazil fuel-price policy intervention, 9 September 2026

Primary first-party source:

- Ministério da Fazenda, `Governo Federal adota novas medidas para combustíveis após novos aumentos do petróleo`;
- URL: `https://www.gov.br/fazenda/pt-br/assuntos/noticias/2026/setembro/governo-federal-adota-novas-medidas-para-combustiveis-apos-novos-aumentos-do-petroleo/`;
- source page displays publication `09/09/2026 18h47` but does not, in the reviewed rendering, explicitly state an IANA timezone;
- the article says the Federal Government adopted/signed two measures on 9 September in response to persistent international oil-price volatility and fuel-supply restrictions associated by the government with geopolitical conflict;
- one measure reduces federal PIS/Pasep and Cofins on gasoline and hydrated ethanol for the stated 10 September–9 October period;
- the other authorises an adjustable economic subsidy for road diesel, initially R$1.00/litre according to the ministry announcement;
- the government describes the measures as temporary cushioning against the external oil/fuel shock.

This is a stronger Live-pressure candidate than a regional zero alone because it combines:

- unscheduled fiscal/tax policy;
- commodity-price and fuel-supply transmission;
- explicit government-stated geopolitical-shock context;
- domestic inflation/affordability implications without requiring WORLD SIGNALS to claim those effects have already occurred;
- Latin American / Global South representation in a current Live population that currently has no Latin America observation.

The regional broadening is a benefit, not the reason for selection.

### Legal-status caveat — mandatory fresh CN recheck

At the time of this post-CM review, the Finance Ministry announcement is cleaner than the available indexed legal-instrument set for the newly announced package. Related Presidency/Planalto records around 8–9 September include extraordinary-credit measures supporting the fuel-policy response, but the reviewed search did not yet yield a clean, complete final legal-instrument pair corresponding to every substantive term in the 9 September ministry announcement.

CN therefore must **not** pre-write `in force`, final legal numbering or a source-native exact publication timestamp from inference.

After CM is merged, CN must freshly recheck:

1. Presidency / Planalto legal texts;
2. Diário Oficial publication where retrievable;
3. Finance Ministry article for corrections or updates;
4. whether the announced measures were published, amended, delayed or superseded;
5. exact legal effective dates and numbers before any stronger status wording is used.

If that recheck remains incomplete, a Live row may describe only the first-party **announced/adopted/signed policy development** actually supported by the ministry source, not a stronger legal-effect claim.

### Deferred — Canada–United States tariff escalation

Current official evidence is also high-value:

- Department of Finance Canada states counter-tariffs of 15%, 25% and 50% on C$27.6bn of U.S. imports took effect at 00:01 on 8 September 2026;
- U.S. White House material records responsive Section 338 product restrictions on the same date.

This is a legitimate future Live candidate in `TRADE` / `ECONOMICS` / `GEOPOLITICS`. It is not selected immediately because:

- its implementation date was announced in advance and may interact with existing/future Canonical trade-policy identity work;
- it would pull the next specimen toward the already structurally dominant North American/US policy sphere;
- Brazil offers greater marginal cross-domain and international-diversity value while remaining independently important.

Deferral is not a judgment that the Canada–U.S. development is less economically consequential.

### Deferred — EU Oil Coordination Group, 8 September 2026

European Commission first-party evidence says the group found no immediate EU oil-supply problem while geopolitical uncertainty continued to drive substantial crude/product price volatility and could tighten markets later.

This is useful Live context, but it is principally a current risk assessment rather than a newly adopted policy action. Brazil supplies a cleaner policy-development specimen with stronger cross-domain novelty.

### Not selected — PIF Analysis / second Live→Analysis bridge

PIF remains one completed linked Live observation without an Analysis review. There is still no unused completed same-anchor Analysis target. Creating a PIF review merely to manufacture a second bridge candidate would reverse the evidence-first architecture.

### Not selected — `CORPORATE_FINANCIAL_MARKET_STRUCTURE` Analysis zero

Prior audits repeatedly established that the easy completed candidates are largely expiry/reconstitution mechanics. Backfilling one merely to erase the last Analysis-category zero remains histogram optimisation rather than analytical need.

### Not selected — Monitor zero categories

`CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` have no configured Monitor scope, but existing relevant source families include rights/manual-only constraints. Zero configured scope does not grant automation permission.

## CN selection

**CN — Brazil fuel-policy Live broadening** is selected for fresh design **only after CM merges**.

Expected design direction, subject to the mandatory fresh legal-status/source recheck:

- architecture layer: `LIVE_INTELLIGENCE`;
- likely observation type: `POLICY_DEVELOPMENT`;
- likely verification state: `PRIMARY_CONFIRMED` if the official ministry source remains uncorrected and sufficient for the bounded claim;
- jurisdiction: Brazil;
- region: Latin America;
- likely domain tags: `ECONOMICS`, `COMMODITIES`, with `GEOPOLITICS` only where the source's stated external-conflict context is retained factually rather than converted into WORLD SIGNALS causal attribution;
- likely Canonical links: none unless a fresh identity-aware search finds an existing scheduled occurrence that genuinely represents this unscheduled intervention;
- event time: no finer than `CIVIL_DATE` 2026-09-09 unless a competent source establishes more precise real-world event timing;
- publication time: do not promote the displayed `18h47` to exact UTC unless the source timezone is competently established;
- no market movement claim unless independently evidenced and rights-cleared;
- no claim that consumer prices fell, inflation changed, supply improved or geopolitical conflict caused a quantified domestic effect merely because the government announced cushioning measures.

## Protected boundary for CN design

A future CN tranche must not:

- create a Canonical occurrence simply because the Live policy development is unscheduled;
- infer legal effectiveness from announcement language;
- manufacture exact source/event UTC timing;
- create a Brazil Monitor route or automation permission from public accessibility;
- automatically populate Analysis;
- claim observed market or inflation effects without separate evidence;
- weaken the newly established CM correction/conflict contract;
- touch OPEC CE quarantine.

If fresh post-merge evidence materially changes the Brazilian package, CN must revise or abandon the candidate rather than force this selection through.
