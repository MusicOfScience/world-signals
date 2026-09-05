# WORLD SIGNALS — Analytical layer foundation P audit v0.1

**Base main:** `f81ce2440d6e3acce2a84c902cd8215e898a002c`  
**Base canonical:** v0.28 / 674 occurrences  
**Base source registry:** v1.70 / 233 sources  
**Base monitor expectations:** v0.8 / 7 configured live routes  
**Reference date:** 2026-09-06

## Purpose

This tranche establishes the first executable WORLD SIGNALS **Analysis** layer while preserving the architectural boundary:

`Canonical Registry → Calendar → Source/Change Monitor → Live Intelligence → Analysis`

It does not populate a large analytical corpus. It defines and tests the contract using one reviewed sample linked to one existing canonical occurrence.

## Why analysis now

After monitor expansion O, the seven configured routes were healthy in the post-merge run and no immediately adjacent high-value source could be promoted honestly without further endpoint/governance work. The next useful architectural step was therefore to make the Charter's analytical discipline executable rather than adding a nominal eighth adapter or filling coverage counts for appearance.

## Fail-closed specimen selection

The first design idea was to use the August 2026 RBA monetary-policy decision because the project already models the distinction between the multi-day Monetary Policy Board meeting window, the decision release and the Governor's press conference.

That idea was rejected after registry introspection.

Temporary read-only introspection run `33970972329` showed that the canonical `WS.CB.RBA.MONETARY_POLICY_DECISION` series currently begins with the 29 September 2026 decision. The 11 August 2026 decision is therefore not an existing canonical occurrence. Creating an analytical review around it would have violated referential integrity even though the real-world event occurred.

A second temporary read-only introspection run, `33971044768`, examined canonical occurrences around 1–5 September 2026. It identified the completed Australian National Accounts release as a suitable specimen:

- occurrence: `WSO-MAC-A-0025`
- series: `WSER-MAC-AU-GDP`
- institution: Australian Bureau of Statistics
- event type: `DATA_RELEASE`
- lifecycle: `COMPLETED`
- local release: `2026-09-02T11:30:00`
- UTC release: `2026-09-02T01:30:00Z`
- canonical source: `WSSRC-MAC-013`
- intrinsic importance: HIGH
- expected market sensitivity: HIGH

The analytical layer binds to that exact occurrence and repeats selected canonical identity fields only so the validator can detect drift or a wrong link.

## Analytical evidence is not canonical provenance

A separate `ANALYTICAL_EVIDENCE_REGISTRY` is introduced under `data/analysis/`.

This is deliberate. Sources that establish what an event *is*, when it occurs, or its canonical state have a different provenance role from sources used to establish a consensus benchmark, an observed market response or a competing explanation.

The sample uses:

1. Australian Bureau of Statistics, **“Australian economy grew 0.4% in the June quarter”**, 2 September 2026, as primary official outcome evidence. It supports real GDP growth of 0.4% quarter-on-quarter and 2.1% year-on-year and the ABS characterisation of subdued growth / cautious households.
2. Reuters reporting syndicated by RTÉ, **“Australia economy slows in Q2 but not by enough to fend off another rate hike”**, 2 September 2026, as analytical evidence for the contemporaneous market forecasts, reported RBA policy-probability repricing and competing global oil/geopolitical rates context.

Both evidence records set `canonical_provenance_effect = NONE`. They do not change `data/sources/registry.json`, the canonical occurrence's `source_id`, or any monitoring permission.

## Sample analytical findings

### What happened

ABS reported real GDP growth of **0.4% q/q** and **2.1% y/y** in the June quarter of 2026.

### What was expected

Reuters reported contemporaneous market forecasts of **0.3% q/q** and **1.8% y/y**.

### What surprised

The sample therefore classifies the release as a modest **UPSIDE** data surprise:

- q/q: +0.1 percentage point versus the cited forecast;
- y/y: +0.3 percentage point versus the cited forecast.

The surprise is defined from actual-versus-benchmark comparison, never from the subsequent market move.

### What moved

Reuters reported the market-implied probability of an RBA September 2026 rate increase moving from **48% to 57%** after the release, a +9 percentage-point repricing.

WORLD SIGNALS records this as `SOURCE_REPORTED_PRE_POST`. It is explicitly **not independently reconstructed** from a timestamped market-data series in this tranche.

### What appears connected

The sample uses:

- interaction type: `TRANSMISSION_CHANNEL`
- causal status: `OBSERVED_ASSOCIATION`
- confidence: `MEDIUM`

The upside GDP surprise and near-term RBA repricing are analytically consistent with a growth-to-policy-expectations channel. This is not promoted to an exclusive causal claim.

### What may be noise / alternatives

The same Reuters report described renewed US–Iran fighting, higher oil prices and inflation concerns as pushing Australian ten-year yields higher. That is preserved as a competing global driver rather than discarded to make the domestic GDP story cleaner.

The packet also allows that the GDP release may have reinforced a pre-existing RBA repricing path rather than creating it from zero.

### Second-order effects

`NOT_ESTABLISHED`.

The observed policy-probability repricing is treated as the immediate response; it is not proof that the RBA will subsequently change policy.

### Falsifiers

The sample weakens its own interpretation if later evidence shows that:

- the relevant repricing materially preceded the GDP release;
- the repricing rapidly reverses without new Australian information while global rates continue in the same direction; or
- stronger contemporaneous evidence identifies another catalyst as the principal driver.

## Executable guardrails

`src/world_signals/analysis.py` and `scripts/validate_analysis.py` enforce, among other things:

- every review resolves to an existing canonical occurrence;
- selected repeated canonical identity fields match the live canonical object;
- analytical evidence cannot claim canonical provenance effect;
- expected and actual observations remain separate;
- a directional surprise requires an explicit comparison basis;
- every market movement requires evidence, a measurement window and precision class;
- interaction type, causal status and confidence use controlled vocabularies;
- any connection stronger than `NOT_A_CAUSAL_CLAIM` requires alternative explanations;
- stronger causal language requires multiple evidence references;
- evidence references must resolve;
- `NOT_ESTABLISHED`, `NO_CLEAR_SURPRISE` and `NOT_A_CAUSAL_CLAIM` remain valid analytical outcomes;
- canonical mutation and Google Calendar writes remain prohibited.

## Public projection

The static site gains a read-only Analysis view. It exposes the nine review questions, connection grade, alternatives, falsifiers and analytical evidence links.

The browser reads only `data/analysis.json`. It has no canonical/source/monitor write path. The source module is bundled into `docs/app.js` by the existing static build pattern; `web/index.html` does not acquire analysis-specific markup.

## Protected state

This tranche must not modify:

- `data/canonical/registry.json`
- `data/canonical/schema.json`
- `data/sources/registry.json`
- `data/monitor/expectations.json`
- `data/monitor/operations_policy.json`
- `data/changes/ledger.json`
- `data/coverage/biosecurity_overlay.json`

Automatic canonical commit remains OFF. Google Calendar writes remain OFF.

## Population discipline

One Australian sample is a contract test, not a global analytical corpus and not a preferred geography for future analysis. Before broad population, the same model should be challenged against materially different event types and regions — including non-Western and Global South cases — so the schema is not accidentally shaped around central-bank/macro-market conventions.
