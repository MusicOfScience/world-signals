# WORLD SIGNALS — post-CO pressure audit / CP selection v0.1

**Status:** READ-ONLY SELECTION EVIDENCE — NO CP POPULATION AUTHORISED  
**Reference date:** 2026-09-10  
**CO base:** merged post-CN `main` `b2b9e85933dd1c5924af1228f47427d6b38bf967`  
**Post-CO coverage run:** `34467313601`  
**Coverage artifact:** `10148053040`  
**Coverage artifact digest:** `sha256:9d040c2cdca7cae94a1f9fa5db2cfc9f50449f71bb8a2e9473fa9ce7f6e567be`

## Mechanical post-CO state

The read-only cross-layer audit reports:

- Canonical Registry `v0.42`: 689 occurrences / 203 unique series;
- Monitor expectations `v0.28`: 26 adapters / 217 explicitly scoped occurrences / 48 series;
- Live Intelligence `v0.11`: 10 observations / 3 Canonical-linked observations;
- Analysis `v0.18`: 22 reviews / 1 production Live input / 1 production revision;
- completed linked Live observations with an existing unused Analysis target: **0**;
- completed linked Live observations without an Analysis review: **1** — the PIF partner-framework outcome;
- linked non-completed observations: **1** — BARMM pre-election context for the planned 14 September occurrence;
- unlinked Live observations: 7, including the new Canada counter-tariff implementation row;
- Canonical regions with no Live observation: **Europe only**;
- Canonical categories with no configured Monitor scope: `CLIMATE_ENVIRONMENT`, `HEALTH_BIOSECURITY`;
- Canonical categories with no Analysis review: `CORPORATE_FINANCIAL_MARKET_STRUCTURE`.

These remain prompts, not quotas or automatic queues.

## Qualitative pressure comparison

### Candidate A — ECB 10 September 2026 monetary-policy decision — SELECTED CONDITIONALLY

Primary official evidence reviewed:

- ECB weekly schedule: `https://www.ecb.europa.eu/press/calendars/weekly/html/index.en.html`
- ECB Governing Council meeting schedule: `https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html`
- ECB press-conference page for 10 September 2026: `https://www.ecb.europa.eu/press/press_conference/html/index.en.html`

The ECB schedules publication of the monetary-policy decisions for 14:15 on 10 September, followed by the press conference at 14:45 and macroeconomic projections later the same afternoon. The existing Canonical family already contains the ECB monetary-policy decision series; CP must identity-probe the exact 10 September occurrence after CO merges rather than invent a new occurrence.

Why this is stronger than simple geographic zero-filling:

1. the decision is independently systemically important;
2. it is a scheduled institutional outcome with first-party publication infrastructure and an existing Canonical family;
3. it would exercise a controlled monetary-policy `OUTCOME_OF` Live linkage rather than another unlinked news observation;
4. it provides a useful future bridge candidate only if a separately justified same-anchor Analysis review later exists and policy permits another production Live input — CP itself must not manufacture that bridge;
5. Europe being the final zero-Live region is corroborating coverage context, not the selection rule.

**Critical timing condition:** at this pressure-review point the 10 September outcome had not yet been published. CP is therefore selected only for **fresh post-merge preflight**. No pre-event result, rate decision, rationale, projection value, surprise or market response may be written in advance.

### Candidate B — EU Oil Coordination Group 8 September supply-security assessment — DEFERRED

Primary official evidence:

- European Commission DG Energy, 8 September 2026: `https://energy.ec.europa.eu/news/oil-coordination-group-no-immediate-security-oil-supply-concerns-eu-2026-09-08_en`

The Commission reports no immediate EU oil-supply problem while noting Middle East instability and significant price volatility. This is a real cross-domain Europe/energy/geopolitics signal, but it would be another unlinked institutional-context observation and adds less contract novelty than a clean scheduled ECB outcome. It remains a valid future candidate, not discarded evidence.

### Candidate C — PIF Analysis / second Live→Analysis bridge — DEFERRED

The post-CO frontier still has no completed linked observation with an existing unused Analysis target. PIF remains completed-linked without an Analysis review. Creating a PIF review solely to manufacture a second bridge candidate would invert the evidence-first architecture. The one production Live-input slot remains occupied by Japan FIES under the current controlled bridge contract.

### Candidate D — corporate / financial market-structure Analysis zero — DEFERRED

`CORPORATE_FINANCIAL_MARKET_STRUCTURE` remains the only Canonical category without an Analysis review, but previous audits correctly rejected filling this histogram zero with a weak expiry/reconstitution specimen. No new evidence in CO makes quota completion an analytical objective.

## CP selection

**CP is selected conditionally as a bounded ECB 10 September monetary-policy Live-outcome design after CO merges.**

This is selection evidence only. CP must start fresh from the exact then-current `main` and must abort, defer or redesign if any of the following fail:

1. the official ECB monetary-policy decision has actually been published;
2. the exact 10 September Canonical occurrence and stable series identity can be resolved without creating a duplicate;
3. the source-native timing and publication semantics can be preserved without inventing timezone precision;
4. the Live claim can remain factual and bounded to the decision/outcome actually published;
5. any expectation, surprise, market movement, causal interpretation or second-order effect remains outside Live unless separately supported in Analysis;
6. no automatic Monitor→Live, Live→Analysis, Canonical write, Calendar write or public projection gate is opened;
7. OPEC CE quarantine remains untouched.

If the official decision is not yet available when CP begins, **do not create a pre-event outcome row**. Defer CP or return to pressure selection instead.

## Human merge-handoff safety

`HANDOFF_PROTOCOL.md` is part of the CO closeout. A future handoff must state exactly `MERGE NOW — PR #N` or `DO NOT MERGE — PR #N`; no PR URL may be supplied while the state is `DO NOT MERGE`. The user performs merges; the assistant does not.
